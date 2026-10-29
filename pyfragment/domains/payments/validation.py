from __future__ import annotations

from pyfragment.enums import PaymentMethod
from pyfragment.exceptions import ConfigurationError


def validate_payment_method(payment_method: PaymentMethod) -> None:
    if payment_method not in PaymentMethod:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method, supported=", ".join(m.value for m in PaymentMethod)
            )
        )
