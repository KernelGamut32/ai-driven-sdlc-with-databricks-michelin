"""Business rules in plain Python.

No Spark and no third-party package: these functions run anywhere, and the local tests exercise
them in milliseconds. The Spark transformation (o2i.transform) has the same rules as column
expressions. The parity check proves on the fixture that both agree.

Money is decimal.Decimal, never float. Rounding is half up, which is the rounding of Spark's round().
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

CENT = Decimal("0.01")


# ---- R2: status ----------------------------------------------------------------------------------

def normalize_status(raw: Optional[str]) -> Optional[str]:
    """Comparison form of a delivered status: trimmed and upper case. The raw value is never rewritten."""
    if raw is None:
        return None
    return raw.strip().upper()


def classify_status(raw: Optional[str]) -> str:
    """Return POSTED, NOT_POSTED (draft or cancelled), or UNEXPECTED (any other value, or no value)."""
    status = normalize_status(raw)
    if status == "POSTED":
        return "POSTED"
    if status in ("DRAFT", "CANCELLED"):
        return "NOT_POSTED"
    return "UNEXPECTED"


# ---- the derived amounts -------------------------------------------------------------------------

def _as_decimal(value, name: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return Decimal(value)
    raise TypeError(f"{name} must be a Decimal, not {type(value).__name__}: money is never a float")


def round_half_up(value: Decimal) -> Decimal:
    """Round to two decimals, half away from zero: 0.165 becomes 0.17, and -0.165 becomes -0.17."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def tax_amount(net_amount: Decimal, tax_rate: Optional[Decimal]) -> Decimal:
    """Tax of one line, rounded half up. No tax rate means that no tax applies: the result is 0.00."""
    raise NotImplementedError("Lab 2: write this helper as the plain-Python twin of the Spark expression")


def gross_amount(net_amount: Decimal, tax_rate: Optional[Decimal]) -> Decimal:
    """Net amount plus tax. A credit stays negative: -3.00 at 5.5 percent is -3.17."""
    raise NotImplementedError("Lab 2: write this helper as the plain-Python twin of the Spark expression")
