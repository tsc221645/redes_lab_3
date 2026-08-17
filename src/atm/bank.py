from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Account:
    card: str
    pin: str
    balance: float


class Bank:
    def __init__(self) -> None:
        self.accounts: dict[str, Account] = {
            "123456789": Account(
                card="123456789",
                pin="1234",
                balance=5000.00,
            ),
            "987654321": Account(
                card="987654321",
                pin="4321",
                balance=2500.00,
            ),
        }

    def verify_credentials(self, card: str, pin: str) -> bool:
        account = self.accounts.get(card)

        if account is None:
            return False

        return account.pin == pin

    def get_balance(self, card: str) -> float | None:
        account = self.accounts.get(card)

        if account is None:
            return None

        return account.balance

    def withdraw(
        self,
        card: str,
        amount: float,
    ) -> tuple[bool, str, float | None]:

        account = self.accounts.get(card)

        if account is None:
            return False, "Tarjeta no encontrada.", None

        if amount <= 0:
            return False, "El monto debe ser mayor que cero.", account.balance

        if amount > account.balance:
            return False, "Fondos insuficientes.", account.balance

        account.balance -= amount

        return (
            True,
            "Retiro realizado correctamente.",
            account.balance,
        )