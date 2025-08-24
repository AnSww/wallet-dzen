from enum import Enum

class Role(str, Enum):
    user = "user"
    admin = "admin"

class AccountType(str, Enum):
    cash = "cash"
    card = "card"
    deposit = "deposit"