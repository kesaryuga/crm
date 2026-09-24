from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

TWO = Decimal("0.01")


def money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(TWO, rounding=ROUND_HALF_UP)


def line_totals(
    quantity: Decimal,
    unit_price: Decimal,
    discount_type: str | None = None,
    discount_value: Decimal | None = None,
    vat_rate: Decimal | None = None,
) -> tuple[Decimal, Decimal, Decimal]:
    """Return (subtotal, vat_amount, total). Company is not a VAT payer."""
    sub = money(quantity * unit_price)
    if discount_type == "percent" and discount_value is not None:
        sub = money(sub * (Decimal("100") - discount_value) / Decimal("100"))
    elif discount_type == "amount" and discount_value is not None:
        sub = money(sub - discount_value)
    if sub < 0:
        sub = money(0)
    vat = money(sub * (vat_rate or Decimal("0")) / Decimal("100"))
    return sub, vat, money(sub + vat)


def recalculate_contract(
    items_totals: list[tuple[Decimal, Decimal, Decimal]],
) -> tuple[Decimal, Decimal, Decimal]:
    subtotal = money(sum(s for s, _v, _t in items_totals))
    vat_amount = money(sum(v for _s, v, _t in items_totals))
    total = money(sum(t for _s, _v, t in items_totals))
    return subtotal, vat_amount, total


_ONES = [
    "ноль", "один", "два", "три", "четыре", "пять", "шесть",
    "семь", "восемь", "девять", "десять", "одиннадцать", "двенадцать",
    "тринадцать", "четырнадцать", "пятнадцать", "шестнадцать",
    "семнадцать", "восемнадцать", "девятнадцать",
]
_ONES_F = _ONES[:2] + ["две"] + _ONES[3:]
_TENS = [
    "", "", "двадцать", "тридцать", "сорок", "пятьдесят",
    "шестьдесят", "семьдесят", "восемьдесят", "девяносто",
]
_HUNDREDS = [
    "", "сто", "двести", "триста", "четыреста", "пятьсот",
    "шестьсот", "семьсот", "восемьсот", "девятьсот",
]


def _triad(n: int, female: bool) -> str:
    ones = _ONES_F if female else _ONES
    parts = []
    h, rest = divmod(n, 100)
    if h:
        parts.append(_HUNDREDS[h])
    t, o = divmod(rest, 10)
    if t == 1:
        parts.append(_ONES[10 + o])
    else:
        if t:
            parts.append(_TENS[t])
        if o:
            parts.append(ones[o])
    return " ".join(parts)


def _plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def amount_in_words(value: Decimal, currency: str = "BYN") -> str:
    """Сумма прописью без НДС (исполнитель не плательщик НДС)."""
    value = money(value)
    integer = int(value)
    frac = int((value - Decimal(integer)) * 100)
    female = currency in ("BYN", "RUB", "UAH")
    parts = []
    millions, rest = divmod(integer, 1_000_000)
    thousands, units = divmod(rest, 1_000)
    if millions:
        word = _plural(millions, "миллион", "миллиона", "миллионов")
        parts.append(f"{_triad(millions, False)} {word}")
    if thousands:
        word = _plural(thousands, "тысяча", "тысячи", "тысяч")
        parts.append(f"{_triad(thousands, True)} {word}")
    if units or not parts:
        parts.append(_triad(units, female))
    main = _plural(
        integer,
        "белорусский рубль",
        "белорусских рубля",
        "белорусских рублей",
    )
    kop = _plural(frac, "копейка", "копейки", "копеек")
    kop_v = f"{frac:02d}"
    text = f"({' '.join(parts)} {main} {kop_v} {kop} без НДС)"
    return text.replace("  ", " ").strip()
