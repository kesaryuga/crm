from __future__ import annotations

import ast
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

TWO = Decimal("0.01")

_ALLOWED_FUNCS = {"abs", "min", "max", "round", "float", "int", "Decimal"}
_ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.USub,
    ast.UAdd,
    ast.Mod,
    ast.Call,
    ast.Compare,
    ast.IfExp,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
)


class FormulaError(ValueError):
    pass


def _to_dec(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise FormulaError(f"Нечисловое значение: {value!r}") from exc


def _eval(node: ast.AST, ctx: dict[str, Decimal]) -> Decimal | bool:
    if not isinstance(node, _ALLOWED_NODES):
        raise FormulaError(f"Запрещённый синтаксис: {type(node).__name__}")
    if isinstance(node, ast.Constant):
        return _to_dec(node.value)
    if isinstance(node, ast.Name):
        if node.id not in ctx:
            raise FormulaError(f"Неизвестная переменная: {node.id}")
        return ctx[node.id]
    if isinstance(node, ast.UnaryOp):
        val = _eval(node.operand, ctx)
        if isinstance(node.op, ast.USub):
            return -_to_dec(val)
        return _to_dec(val)
    if isinstance(node, ast.BinOp):
        left = _to_dec(_eval(node.left, ctx))
        right = _to_dec(_eval(node.right, ctx))
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise FormulaError("Деление на ноль")
            return left / right
        if isinstance(node.op, ast.Pow):
            return left ** right
        if isinstance(node.op, ast.Mod):
            if right == 0:
                raise FormulaError("Деление на ноль")
            return left % right
        raise FormulaError("Запрещённая операция")
    if isinstance(node, ast.Compare):
        left = _to_dec(_eval(node.left, ctx))
        right = _to_dec(_eval(node.comparators[0], ctx))
        op = node.ops[0]
        if isinstance(op, ast.Eq):
            return left == right
        if isinstance(op, ast.NotEq):
            return left != right
        if isinstance(op, ast.Lt):
            return left < right
        if isinstance(op, ast.LtE):
            return left <= right
        if isinstance(op, ast.Gt):
            return left > right
        if isinstance(op, ast.GtE):
            return left >= right
        raise FormulaError("Запрещённое сравнение")
    if isinstance(node, ast.IfExp):
        cond = _eval(node.test, ctx)
        return _eval(node.body if cond else node.orelse, ctx)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCS:
            raise FormulaError("Функция не в белом списке")
        args = [_to_dec(_eval(a, ctx)) for a in node.args]
        fn = node.func.id
        if fn == "abs":
            return abs(args[0])
        if fn == "min":
            return min(args)
        if fn == "max":
            return max(args)
        if fn == "round":
            return args[0].quantize(TWO, rounding=ROUND_HALF_UP)
        if fn == "float":
            return args[0]
        if fn == "int":
            return Decimal(int(args[0]))
        if fn == "Decimal":
            return args[0]
        raise FormulaError("Функция не реализована")
    raise FormulaError("Недопустимое выражение")


def eval_formula(expr: str, variables: dict[str, Any]) -> Decimal:
    """Безопасная формула: только арифметика и белый список функций."""
    clean = expr.strip()
    if not clean:
        raise FormulaError("Пустая формула")
    if "__" in clean or ";" in clean or "import" in clean:
        raise FormulaError("Запрещённый фрагмент в формуле")
    ctx = {k: _to_dec(v) for k, v in variables.items() if v is not None}
    try:
        tree = ast.parse(clean, mode="eval")
    except SyntaxError as exc:
        raise FormulaError(f"Синтаксис формулы: {exc}") from exc
    result = _eval(tree.body, ctx)
    return _to_dec(result).quantize(TWO, rounding=ROUND_HALF_UP)
