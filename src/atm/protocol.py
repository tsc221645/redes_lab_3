from __future__ import annotations

from typing import Any


ATM_REQUEST = "ATM_REQUEST"
ATM_RESPONSE = "ATM_RESPONSE"

AUTH = "AUTH"
BALANCE = "BALANCE"
WITHDRAW = "WITHDRAW"


def make_auth_request(card: str, pin: str) -> dict[str, Any]:
    return {
        "type": ATM_REQUEST,
        "operation": AUTH,
        "card": card,
        "pin": pin,
    }


def make_balance_request(card: str) -> dict[str, Any]:
    return {
        "type": ATM_REQUEST,
        "operation": BALANCE,
        "card": card,
    }


def make_withdraw_request(card: str, amount: float) -> dict[str, Any]:
    return {
        "type": ATM_REQUEST,
        "operation": WITHDRAW,
        "card": card,
        "amount": amount,
    }


def make_response(
    operation: str,
    success: bool,
    message: str,
    **extra: Any,
) -> dict[str, Any]:
    response = {
        "type": ATM_RESPONSE,
        "operation": operation,
        "success": success,
        "message": message,
    }

    response.update(extra)
    return response


def validate_request(request: Any) -> bool:
    if not isinstance(request, dict):
        return False

    if request.get("type") != ATM_REQUEST:
        return False

    operation = request.get("operation")

    if operation == AUTH:
        return (
            isinstance(request.get("card"), str)
            and isinstance(request.get("pin"), str)
        )

    if operation == BALANCE:
        return isinstance(request.get("card"), str)

    if operation == WITHDRAW:
        return (
            isinstance(request.get("card"), str)
            and isinstance(request.get("amount"), (int, float))
            and not isinstance(request.get("amount"), bool)
            and request.get("amount") > 0
        )

    return False