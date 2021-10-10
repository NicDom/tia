"""Module for Invoices."""
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypedDict
from typing import Union

import datetime

from pydantic import Field
from tabulate import tabulate  # type: ignore

from tia.balances import AccountingItem
from tia.basemodels import TiaConfigBaseModel
from tia.basemodels import TiaItemModel
from tia.basemodels import TiaSheetModel
from tia.client import Client
from tia.company import Company


class InvDict(TypedDict):
    """TypedDict for `Invoice`."""

    config: "InvoiceConfiguration"
    invoicenumber: str
    client: Client
    company: Company
    items: Union["InvoiceItem", List["InvoiceItem"]]


MetaTuple = Tuple[str, float, float, datetime.date, Optional[datetime.date]]


class InvoiceMetadata(TiaItemModel):
    """The class representing the `metadata` of an invoice.

    Args:
        invoicenumber (str): The invoicenumber of the invoice.
        total (float): The total (subtotal + tax) of the invoice. Needs to be greater
            than 0.
        tax (float): The tax of the invoice. Needs to be greater or equal to 0 and less
        due_to (datetime.date): The date to which the invoice needs to be settled.
            than 1/2 of the total (otherwise vat would be grater than 100 %%).
        payed_on (datetime.date, optional): Date the invoice was settled.
            Defaults to None.
    """

    invoicenumber: str
    value: float = Field(..., gt=0)
    vat: float = Field(0, ge=0, lt=100)
    due_to: datetime.date
    payed_on: Optional[datetime.date] = None

    @property
    def subtotal(self) -> float:
        """Subtotal of the invoice stored in this `InvoiceMetadata`."""
        return self.value

    @classmethod
    def __headers__(cls) -> List[str]:
        """__headers__ for representing a `TypedList` of `InvoiceMetadata`."""
        return ["invoicenumber", "total", "tax", "due_to", "payed_on"]

    @property
    def __values__(self) -> List[Any]:
        """__values__ for representing a `TypedList` of `InvoiceMetadata`."""
        return [getattr(self, attr) for attr in InvoiceMetadata.__headers__()]


class InvoiceConfiguration(TiaConfigBaseModel):
    """Dataclass that contains the default configurations for a new invoice.

    Args:
        language (str, optional): The default language of the assistant an of a new
            invoice. Defaults to "english".
        date (datetime.date, optional): The default date for a new invoice.
            Defaults to datetime.date.today().
        vat (float, optional): The default VAT for a new invoice. Defaults to 0.
        deadline (datetime.timedelta, optional): The default time period in days given
            to the client to settle an invoice. Defaults to 30.
        paymentterms (str, optional): The default paymentterms of a new invoice.
            Defaults to None.
        invoicestyle (str, optional): The default style of a new invoice. Defaults to
            "classic".
        curencyshort (str, optional): The default currency symbol for a new invoice.
            Defaults to "€".
        currencylong (str, optional): The code of the currency according to ISO 4217.
            Defaults to "EUR".
    """

    # language: str = "english"
    date: datetime.date = datetime.date.today()
    vat: float = Field(default=0, ge=0, lt=100)
    deadline: datetime.timedelta = datetime.timedelta(days=30)
    paymentterms: str = ""
    invoicestyle: str = "classic"
    currency_symbol: str = "€"  # todo check if known currency
    currency_code: str = "EUR"


class InvoiceItem(TiaItemModel):
    """Class to represent an invoice item.

    Args:
        service (str): The service
        qty (float): The quantity of the service (e.g. hours, units, etc.).
            Needs to be greater than 0.
        unit_price (float): The price of one unit. Needs to be greater than 0.
        vat (float, optional): The vat for the item. Needs to be greater or equal
            to 0 and less than 100 if given. Defaults to None.
        description (str): A more detailed description of the item.
    """

    service: str
    qty: float = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    vat: float = Field(default=99.99, ge=0, lt=100)
    description: Optional[str] = ""

    @property
    def subtotal(self) -> float:
        """The subtotal of the invoice item.

        Getter only. Setter is not defined.

        Returns:
            float: The subtotal = qty * unit_price of the item.
        """
        return self.qty * self.unit_price


class Invoice(TiaSheetModel[InvoiceItem]):
    """Subclass of `TiaSheetModel` representing an invoice.

    Make sure that `invoicenumber` is unique and increasing.

    Args:
        config (InvoiceConfiguration): The configuration of the invoice. See docstring
            of `InvoiceConfiguration` for more information.
        invoicenumber (str): The invoicenumber of the invoice. Make sure it is unique
            and increasing.
        client (Client): The client of the invoice.
        company (Company): The company of the invoice.
        items (List[InvoiceItem]): The items of the invoice. Defaults to [].
    """

    invoicenumber: str
    config: InvoiceConfiguration
    company: Company
    client: Client
    items: List[InvoiceItem] = []
    payed_on: Optional[datetime.date] = None

    def check(self, v: InvoiceItem) -> InvoiceItem:
        """Validates added items.

        Overrides `TypedList.check`. Checks that `v` is an instance of
        `InvoiceItem` and sets items VAT to invoices VAT, if items VAT is None.

        Args:
            v (InvoiceItem): [description]

        Returns:
            InvoiceItem: [description]
        """
        v = super().check(v)
        if v.vat == 99.99:
            v.vat = self.config.vat
        return v

    @property
    def due_to(self) -> datetime.date:
        """Getter (no setter defined) to get the due date of the invoice.

        Returns:
            datetime.date: The due date of the invoice.
        """
        return self.config.date + self.config.deadline

    @property
    def meta(self) -> InvoiceMetadata:
        """Returns the 'metadata' of the invoice as an instance of type InvoiceMetadata.

        Metadata consists of:
        The invoicenumber, the total, the due date, the taxes and the day the
        invoice was settled (None if not settled).

        Returns:
            InvoiceMetadata: The metadata.
        """
        return InvoiceMetadata(
            invoicenumber=self.invoicenumber,
            value=self.total,
            due_to=self.due_to,
            vat=self.tax / self.subtotal * 100,
            payed_on=self.payed_on,
        )

    @property
    def ca_item(self) -> Optional[AccountingItem]:
        """Returns an `AccountingItem` object for the invoice.

        The `AccountingItem` input is given by:
        description = Invoice no. `invoicenumber`
        value = `total` of the invoice
        vat = `tax` / `subtotal` * 100 (mean of the items vats in %%)
        currency = currency of the invoice
        date = date the invoice was settled

        if the invoice wasn't settled the function returns `None`

        Returns:
            Union[AccountingItem, None]: AccountingItem for the invoice, if the invoice
                was settled, else None.
        """
        if self.payed_on is not None:
            return AccountingItem(
                description=f"Invoice no. {self.invoicenumber}",
                value=self.total,
                vat=self.tax / self.subtotal * 100,
                currency=self.config.currency_symbol,
                date=self.payed_on,
            )
        else:
            return None

    @property
    def company_and_client_str(self) -> str:
        """String representation of client and company innformation.

        Returns:
            str: String representation of client and company.
        """
        company_and_client_headers = ["From", "Prepared For"]
        company_and_client_information = zip(
            [self.company.__str__()], [self.client.__str__()]
        )
        return str(
            tabulate(company_and_client_information, headers=company_and_client_headers)
        )

    @property
    def items_str(self) -> str:
        """String representation of the invoiceitems.

        Returns:
            str: The string representation of the invoiceitems.
        """
        return self.__str__()

    @property
    def invoice_str(self) -> str:
        """The string representation of the invoice.

        Returns:
            str: The string representation.
        """
        return f"{self.company_and_client_str}\n\nInvoiceItems:\n\n{self.__str__()}"
