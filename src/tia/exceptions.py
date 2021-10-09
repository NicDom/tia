"""Exceptions for TIA."""
from typing import Optional


class TaxValueError(ValueError):  # pragma: no cover
    """Custom error that occurs when the tax value can't be correct."""

    def __init__(
        self,
        value: Optional[float] = 0,
        msg: Optional[str] = "The value for tax is not correct.",
        *args: object,
    ) -> None:
        """__init__ for `TaxValueError`.

        Args:
            value (float, optional): The value of the tax.
            msg (str, optional): The error message.
                Defaults to "The value for tax is not correct.".
            *args (object): An object.
        """
        self.value = value
        self.message = msg
        super().__init__(self.value, self.message, *args)


class UnknownInvoiceItemError(IndexError):  # pragma: no cover
    """Custom error that occurs, when an `InvoiceItem` not part of `Invoice.items`."""

    def __init__(self, item: object, invoicenumber: str, *args: object) -> None:
        """__init__ of UnknownInvoiceItemError.

        Args:
            item (object): The `InvoiceItem` that is none of the `Invoice`.
            invoicenumber (str): The invoicenumber of the invoice.
            *args (object): object
        """
        self.message = (
            f"The item {item!r} is not an item of the invoice {invoicenumber}"
        )
        super().__init__(self.message, *args)


class CompanyAccountDataMissingError(ValueError):
    """Risen when `companybic` or `companybank` are missing at validation."""

    def __init__(
        self,
        # value: str = "1",
        message: Optional[str] = "Companybic or Companybank are missing.",
        *args: object,
    ) -> None:
        """__init__ of `CompanyAccountDataMissingError`.

        Args:
            message (str, optional): The error message.
                Defaults to "Companybic or Companybank are missing.".
            *args (object): Object.
        """
        # self.value = value
        self.message = message
        super().__init__(message, *args)
