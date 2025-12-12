from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import ast

from playwright.sync_api import (
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    expect,
    sync_playwright,
)


# === модели отчёта ===
@dataclass
class LocatorIssue:
    """Проблема с конкретным локатором/действием в файле автотеста."""

    file: str
    selector: str
    message: str
    step: Optional[str] = None
    line: Optional[int] = None


@dataclass
class UiLocatorsReport:
    """Результат проверки всех автотестов в директории."""

    ok_files: List[str]
    issues: List[LocatorIssue]


class UiLocatorsChecker:
    """
    Сценарная проверка локаторов Playwright в сгенерированных UI-автотестах.

    """

    # Методы, которые считаем "фабриками локаторов" на Page/Locator:
    _LOCATOR_FACTORIES = {
        # page.*
        "locator",
        "get_by_role",
        "get_by_text",
        "get_by_label",
        "get_by_placeholder",
        "get_by_test_id",
        # locator.*
        "locator",
        "get_by_role",
        "get_by_text",
        "get_by_label",
        "get_by_placeholder",
        "get_by_test_id",
        "filter",
        "nth",
    }

    # Методы действий на Page:
    _PAGE_ACTIONS = {
        "goto",
        "wait_for_selector",
        "wait_for_load_state",
        "wait_for_timeout",
        "reload",
        "go_back",
        "go_forward",
        "set_viewport_size",
    }

    # Методы действий на Locator:
    _LOCATOR_ACTIONS = {
        "click",
        "fill",
        "type",
        "press",
        "check",
        "uncheck",
        "select_option",
        "hover",
        "focus",
        "scroll_into_view_if_needed",
        "set_input_files",
        "wait_for",
    }

    _LOCATOR_PROPERTIES = {"first", "last"}

    def __init__(
        self,
        base_url: str,
        timeout_ms: int = 60_000,
        locator_wait_ms: int = 7_000,
        validate_only_in_assert: bool = True,
        headless: bool = True,
        artifacts_dir: Path | str | None = None,
        abort_on_arrange_act_error: bool = True,
        optional_action_timeout_ms: int = 1_000,  # для действий внутри try/except pass
    ) -> None:
        self.base_url = base_url
        self.timeout_ms = timeout_ms
        self.locator_wait_ms = locator_wait_ms
        self.validate_only_in_assert = validate_only_in_assert
        self.headless = headless
        self.artifacts_dir = Path(artifacts_dir) if artifacts_dir else None
        self.abort_on_arrange_act_error = abort_on_arrange_act_error
        self.optional_action_timeout_ms = optional_action_timeout_ms

    # =========================
    # Public API
    # =========================
    def analyze_dir(self, tests_dir: Path | str) -> UiLocatorsReport:
        tests_path = Path(tests_dir)
        ok_files: List[str] = []
        issues: List[LocatorIssue] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()

            for file in sorted(tests_path.glob("test_ui_*.py")):
                page = context.new_page()
                self._prepare_page(page)

                try:
                    # Стартовое состояние (на случай, если в тесте нет goto)
                    page.goto(self.base_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                    try:
                        page.wait_for_load_state("networkidle", timeout=10_000)
                    except Exception:
                        pass
                except Exception as e:
                    issues.append(
                        LocatorIssue(
                            file=file.name,
                            selector="page.goto(BASE_URL)",
                            message=f"Не удалось открыть BASE_URL: {e}",
                        )
                    )
                    page.close()
                    continue

                file_issues = self._check_file_scenario(page, file)
                if file_issues:
                    issues.extend(file_issues)
                else:
                    ok_files.append(file.name)

                page.close()

            context.close()
            browser.close()

        return UiLocatorsReport(ok_files=ok_files, issues=issues)

    # =========================
    # Page helpers
    # =========================
    def _prepare_page(self, page: Page) -> None:
        page.set_default_navigation_timeout(self.timeout_ms)
        page.set_default_timeout(max(10_000, min(20_000, self.locator_wait_ms * 3)))

    def _dump_artifacts(self, page: Page, file_name: str, note: str = "") -> None:
        if not self.artifacts_dir:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = self.artifacts_dir / file_name.replace(".py", "") / ts
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            page.screenshot(path=str(out_dir / "page.png"), full_page=True)
        except Exception:
            pass

        try:
            (out_dir / "page.html").write_text(page.content(), encoding="utf-8")
        except Exception:
            pass

        try:
            (out_dir / "meta.txt").write_text(f"url={page.url}\nnote={note}\n", encoding="utf-8")
        except Exception:
            pass

    # =========================
    # Scenario per file
    # =========================
    def _check_file_scenario(self, page: Page, file_path: Path) -> List[LocatorIssue]:
        source = file_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return [
                LocatorIssue(
                    file=file_path.name,
                    selector="(parse)",
                    message=f"SyntaxError при парсинге файла: {e}",
                )
            ]

        test_funcs = self._find_test_functions(tree)
        if not test_funcs:
            return []

        env: Dict[str, Any] = {
            "page": page,
            "CALC_URL": self.base_url,  # подменяем константу из тестов
        }

        issues: List[LocatorIssue] = []
        for fn in test_funcs:
            issues.extend(self._run_test_function_safely(fn, source, env, file_path.name))
        return issues

    def _find_test_functions(self, tree: ast.AST) -> List[ast.FunctionDef]:
        funcs: List[ast.FunctionDef] = []
        for node in tree.body:  # type: ignore[attr-defined]
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                funcs.append(node)
        return funcs


    def _run_test_function_safely(
        self,
        fn: ast.FunctionDef,
        source: str,
        env: Dict[str, Any],
        file_name: str,
    ) -> List[LocatorIssue]:
        issues: List[LocatorIssue] = []

        phase: Optional[str] = None
        current_step: Optional[str] = None
        aborted = False
        artifact_dumped = False

        def maybe_abort(e: Exception) -> None:
            nonlocal aborted, artifact_dumped
            if self.abort_on_arrange_act_error and phase in {"arrange", "act"}:
                aborted = True
                if not artifact_dumped:
                    self._dump_artifacts(env["page"], file_name, note=f"abort in {phase}: {e}")
                    artifact_dumped = True

        def record_issue(stmt: ast.AST, msg: str) -> None:
            nonlocal artifact_dumped
            issues.append(
                LocatorIssue(
                    file=file_name,
                    selector=self._src(stmt, source) or stmt.__class__.__name__,
                    message=msg,
                    step=current_step,
                    line=getattr(stmt, "lineno", None),
                )
            )
            if not artifact_dumped:
                self._dump_artifacts(env["page"], file_name, note=msg)
                artifact_dumped = True

        def run_block(stmts: List[ast.stmt], *, in_soft_try: bool) -> None:
            nonlocal phase, current_step, aborted
            for stmt in stmts:
                if aborted:
                    return

                # with allure.step(...)
                if isinstance(stmt, ast.With):
                    step_title = self._extract_allure_step_title(stmt, source)
                    prev_step = current_step
                    prev_phase = phase
                    if step_title is not None:
                        current_step = step_title
                        phase = self._phase_from_step_title(step_title) or phase
                    run_block(stmt.body, in_soft_try=in_soft_try)
                    current_step = prev_step
                    phase = prev_phase
                    continue

                # try: ... except: ... finally: ...
                if isinstance(stmt, ast.Try):
                    is_soft = self._is_soft_try(stmt)
                    try:
                        run_block(stmt.body, in_soft_try=in_soft_try or is_soft)
                    except Exception as e:
                        if is_soft:
                            for h in stmt.handlers:
                                run_block(h.body, in_soft_try=True)
                        else:
                            for h in stmt.handlers:
                                run_block(h.body, in_soft_try=in_soft_try)
                            record_issue(stmt, f"Ошибка в try-блоке: {e}")
                            maybe_abort(e)
                    finally:
                        run_block(stmt.finalbody, in_soft_try=in_soft_try)
                    continue

                try:
                    self._execute_stmt(
                        stmt,
                        source,
                        env,
                        file_name,
                        phase,
                        current_step,
                        issues,
                        in_soft_try=in_soft_try,
                    )
                except Exception as e:
                    if in_soft_try:
                        continue
                    record_issue(stmt, f"Ошибка при выполнении шага сценария: {e}")
                    maybe_abort(e)

        run_block(fn.body, in_soft_try=False)
        return issues

    def _is_soft_try(self, try_node: ast.Try) -> bool:

        if not try_node.handlers:
            return False
        for h in try_node.handlers:
            if h.type is None:
                pass
            elif isinstance(h.type, ast.Name) and h.type.id in {"Exception", "BaseException"}:
                pass
            else:
                return False

            body = h.body or []
            if len(body) == 0:
                continue
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                continue
            return False
        return True

    def _execute_stmt(
        self,
        stmt: ast.stmt,
        source: str,
        env: Dict[str, Any],
        file_name: str,
        phase: Optional[str],
        step: Optional[str],
        issues: List[LocatorIssue],
        *,
        in_soft_try: bool,
    ) -> None:
        # var = <expr>
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            var_name = stmt.targets[0].id
            value = self._eval_expr(
                stmt.value, source, env, file_name, phase, step, issues, in_soft_try=in_soft_try
            )
            env[var_name] = value
            return

        if isinstance(stmt, ast.Expr):
            _ = self._eval_expr(
                stmt.value, source, env, file_name, phase, step, issues, in_soft_try=in_soft_try
            )
            return

        if isinstance(stmt, (ast.Pass, ast.Return)):
            return

        return

    def _eval_expr(
        self,
        node: ast.AST,
        source: str,
        env: Dict[str, Any],
        file_name: str,
        phase: Optional[str],
        step: Optional[str],
        issues: List[LocatorIssue],
        *,
        in_soft_try: bool,
    ) -> Any:
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            if node.id in env:
                return env[node.id]
            if node.id in {"True", "False", "None"}:
                return {"True": True, "False": False, "None": None}[node.id]
            return None

        if isinstance(node, ast.Attribute):
            base = self._eval_expr(
                node.value, source, env, file_name, phase, step, issues, in_soft_try=in_soft_try
            )
            if isinstance(base, Locator) and node.attr in self._LOCATOR_PROPERTIES:
                return getattr(base, node.attr)
            return getattr(base, node.attr, None)

        if isinstance(node, ast.Call):
            # expect(locator).to_be_*(...)
            if self._is_expect_chain(node):
                self._handle_expect_chain(
                    node, source, env, file_name, phase, step, issues, in_soft_try=in_soft_try
                )
                return None

            return self._handle_call(
                node, source, env, file_name, phase, step, issues, in_soft_try=in_soft_try
            )

        return None

    def _handle_call(
        self,
        call: ast.Call,
        source: str,
        env: Dict[str, Any],
        file_name: str,
        phase: Optional[str],
        step: Optional[str],
        issues: List[LocatorIssue],
        *,
        in_soft_try: bool,
    ) -> Any:
        func_obj, method_name, owner_obj = self._resolve_callable(
            call.func, source, env, file_name, phase, step, issues, in_soft_try=in_soft_try
        )
        if func_obj is None or method_name is None:
            return None

        args = [
            self._eval_expr(a, source, env, file_name, phase, step, issues, in_soft_try=in_soft_try)
            for a in call.args
        ]
        kwargs = {
            kw.arg: self._eval_expr(kw.value, source, env, file_name, phase, step, issues, in_soft_try=in_soft_try)
            for kw in call.keywords
            if kw.arg
        }

        # page actions
        if owner_obj is env.get("page") and method_name in self._PAGE_ACTIONS:
            if method_name == "goto":
                kwargs.setdefault("timeout", self.timeout_ms)
                kwargs.setdefault("wait_until", "domcontentloaded")
            return func_obj(*args, **kwargs)

        # locator factories
        if method_name in self._LOCATOR_FACTORIES:
            result = func_obj(*args, **kwargs)
            if isinstance(result, Locator):
                should_validate = not self.validate_only_in_assert or (phase == "assert")
                if should_validate:
                    self._validate_locator(
                        result,
                        self._src(call, source) or method_name,
                        file_name,
                        step,
                        getattr(call, "lineno", None),
                        issues,
                    )
            return result

        # locator actions
        if isinstance(owner_obj, Locator) and method_name in self._LOCATOR_ACTIONS:
            if method_name == "click":
                if in_soft_try:
                    self._optional_click(owner_obj, kwargs)
                    return None

                # обязательный click: trial + реальный click
                self._trial_click(
                    owner_obj,
                    self._src(call, source) or "locator.click()",
                    file_name,
                    step,
                    getattr(call, "lineno", None),
                    issues,
                    kwargs,
                )
                kwargs.setdefault("timeout", self.locator_wait_ms)
                try:
                    owner_obj.scroll_into_view_if_needed()
                except Exception:
                    pass
                return func_obj(*args, **kwargs)

            if in_soft_try and method_name in {"fill", "type", "press", "check", "uncheck", "select_option", "hover"}:
                kwargs.setdefault("timeout", self.optional_action_timeout_ms)
            return func_obj(*args, **kwargs)

        return None

    def _optional_click(self, locator: Locator, original_kwargs: Dict[str, Any]) -> None:
        """
        клик: короткий таймаут, без issue, без падения.
        Нужен для cookie/баннеров/попапов, которые могут не появляться.
        """
        kwargs = dict(original_kwargs)
        kwargs.setdefault("timeout", self.optional_action_timeout_ms)
        try:
            locator.first.click(**kwargs)
        except Exception:
            return

    def _resolve_callable(
        self,
        func: ast.AST,
        source: str,
        env: Dict[str, Any],
        file_name: str,
        phase: Optional[str],
        step: Optional[str],
        issues: List[LocatorIssue],
        *,
        in_soft_try: bool,
    ) -> Tuple[Optional[Any], Optional[str], Optional[Any]]:
        # page.method(...) или var.method(...)
        if isinstance(func, ast.Attribute):
            owner = self._eval_expr(
                func.value, source, env, file_name, phase, step, issues, in_soft_try=in_soft_try
            )
            if owner is None:
                return None, None, None
            method = func.attr
            target = getattr(owner, method, None)
            if target is None:
                return None, None, None
            return target, method, owner

        if isinstance(func, ast.Name):
            target = env.get(func.id)
            return target, func.id, None

        return None, None, None

    # =========================
    # expect(...) chain handling
    # =========================
    def _is_expect_chain(self, call: ast.Call) -> bool:
        # expect(X).to_be_visible(...)
        if not isinstance(call.func, ast.Attribute):
            return False
        inner = call.func.value
        if not isinstance(inner, ast.Call):
            return False
        if not isinstance(inner.func, ast.Name) or inner.func.id != "expect":
            return False
        return True

    def _handle_expect_chain(
        self,
        call: ast.Call,
        source: str,
        env: Dict[str, Any],
        file_name: str,
        phase: Optional[str],
        step: Optional[str],
        issues: List[LocatorIssue],
        *,
        in_soft_try: bool,
    ) -> None:
        inner: ast.Call = call.func.value  # type: ignore[assignment]
        if not inner.args:
            return

        locator_expr = inner.args[0]
        locator_obj = self._eval_expr(
            locator_expr, source, env, file_name, phase, step, issues, in_soft_try=in_soft_try
        )
        if not isinstance(locator_obj, Locator):
            return

        if self.validate_only_in_assert and phase != "assert":
            return

        try:
            assertion_method = call.func.attr  # type: ignore[attr-defined]
            exp = expect(locator_obj)
            method = getattr(exp, assertion_method)
            args = [
                self._eval_expr(a, source, env, file_name, phase, step, issues, in_soft_try=in_soft_try)
                for a in call.args
            ]
            kwargs = {
                kw.arg: self._eval_expr(
                    kw.value, source, env, file_name, phase, step, issues, in_soft_try=in_soft_try
                )
                for kw in call.keywords
                if kw.arg
            }
            kwargs.setdefault("timeout", self.locator_wait_ms)
            method(*args, **kwargs)
        except Exception as e:
            issues.append(
                LocatorIssue(
                    file=file_name,
                    selector=self._src(call, source) or "expect(...)",
                    message=f"expect-assertion failed: {e}",
                    step=step,
                    line=getattr(call, "lineno", None),
                )
            )

    # =========================
    # Validation helpers
    # =========================
    def _validate_locator(
        self,
        locator: Locator,
        selector_text: str,
        file_name: str,
        step: Optional[str],
        line: Optional[int],
        issues: List[LocatorIssue],
    ) -> None:
        try:
            locator.first.wait_for(state="attached", timeout=self.locator_wait_ms)
            cnt = locator.count()
            if cnt == 0:
                issues.append(
                    LocatorIssue(
                        file=file_name,
                        selector=selector_text,
                        message="Локатор не нашёл ни одного элемента на странице (count==0)",
                        step=step,
                        line=line,
                    )
                )
            elif cnt > 1:
                issues.append(
                    LocatorIssue(
                        file=file_name,
                        selector=selector_text,
                        message=(
                            f"Локатор не уникален (strict-mode risk): найдено {cnt} элементов. "
                            "Сузьте область/уточните селектор или используйте .first/.nth()."
                        ),
                        step=step,
                        line=line,
                    )
                )
        except PlaywrightTimeoutError:
            issues.append(
                LocatorIssue(
                    file=file_name,
                    selector=selector_text,
                    message=f"Локатор не появился на странице за {self.locator_wait_ms} ms (wait_for attached таймаут)",
                    step=step,
                    line=line,
                )
            )
        except Exception as e:
            issues.append(
                LocatorIssue(
                    file=file_name,
                    selector=selector_text,
                    message=f"Ошибка при проверке локатора: {e}",
                    step=step,
                    line=line,
                )
            )

    def _trial_click(
        self,
        locator: Locator,
        selector_text: str,
        file_name: str,
        step: Optional[str],
        line: Optional[int],
        issues: List[LocatorIssue],
        original_kwargs: Dict[str, Any],
    ) -> None:
        trial_kwargs = dict(original_kwargs)
        trial_kwargs.setdefault("trial", True)
        trial_kwargs.setdefault("timeout", self.locator_wait_ms)
        try:
            locator.first.click(**trial_kwargs)
        except Exception as e:
            issues.append(
                LocatorIssue(
                    file=file_name,
                    selector=selector_text,
                    message=f"Click trial failed (кликабельность не подтверждена): {e}",
                    step=step,
                    line=line,
                )
            )

    # =========================
    # Step / Phase helpers
    # =========================
    def _extract_allure_step_title(self, with_node: ast.With, source: str) -> Optional[str]:
        # with allure.step("..."):
        if not with_node.items:
            return None
        ctx = with_node.items[0].context_expr
        if not isinstance(ctx, ast.Call):
            return None
        if not isinstance(ctx.func, ast.Attribute):
            return None
        if ctx.func.attr != "step":
            return None
        if not isinstance(ctx.func.value, ast.Name) or ctx.func.value.id != "allure":
            return None
        if not ctx.args:
            return None
        arg0 = ctx.args[0]
        if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
            return arg0.value
        return None

    def _phase_from_step_title(self, title: str) -> Optional[str]:
        t = title.strip().lower()
        if t.startswith("arrange"):
            return "arrange"
        if t.startswith("act"):
            return "act"
        if t.startswith("assert"):
            return "assert"
        return None

    # =========================
    # Source helpers
    # =========================
    def _src(self, node: ast.AST, source: str) -> Optional[str]:
        try:
            seg = ast.get_source_segment(source, node)
            if seg:
                return " ".join(seg.strip().split())
        except Exception:
            pass
        return None
