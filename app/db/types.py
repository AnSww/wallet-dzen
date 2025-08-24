from enum import Enum


class Role(str, Enum):
    user = "user"
    admin = "admin"


class AccountType(str, Enum):
    cash = "cash"
    card = "card"
    deposit = "deposit"


class CategoryKind(str, Enum):
    expense = "expense"
    income = "income"


class Direction(str, Enum):
    incoming = "in"
    outgoing = "out"
