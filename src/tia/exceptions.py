"""Exceptions for TIA."""
from typing import Optional


class TIANoInvoiceOpenedError(ValueError):  # pargma: no cover
    """Custom error that occurs, when no invoice is opened.

    Adding, editing and deleting items are always by TIA performed on `self.invoice`.
    If `self.invoice` is `None`, when performing one of these tasks, this error is
    raised.
    """

    def __init__(self, message: str = "No invoice is opened."):
        """__init__ of `TiaNoInvoiceOpenedError`.

        Args:
            message (str): message that gets displayed.
        """
        self.message = message
        super().__init__(self.message)


# class UnknownInvoiceItemError(IndexError):  # pragma: no cover
#     """Custom error that occurs, when an `InvoiceItem` not part of `Invoice.items`."""

#     def __init__(self, item: object, invoicenumber: str, *args: object) -> None:
#         """__init__ of UnknownInvoiceItemError.

#         Args:
#             item (object): The `InvoiceItem` that is none of the `Invoice`.
#             invoicenumber (str): The invoicenumber of the invoice.
#             *args (object): object
#         """
#         self.message = (
#             f"The item {item!r} is not an item of the invoice {invoicenumber}"
#         )
#         super().__init__(self.message, *args)


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
