from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Expense:
    day: date
    category: str
    amount: float
    note: str = ""
