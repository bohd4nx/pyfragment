from __future__ import annotations

from pyfragment.enums import SUPPORTED_PAYMENT_METHODS, PaymentMethod
from pyfragment.exceptions import ConfigurationError


def validate_payment_method(payment_method: PaymentMethod) -> None:
    if payment_method not in SUPPORTED_PAYMENT_METHODS:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(m.value for m in SUPPORTED_PAYMENT_METHODS)),
            )
        )
