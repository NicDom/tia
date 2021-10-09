"""Module for the balance sheet."""
from typing import Any
from typing import List
from typing import Tuple
from typing import Union

import datetime
import operator

from pydantic import Field

from tia.basemodels import TiaConfigBaseModel
from tia.basemodels import TiaItemModel
from tia.basemodels import TiaSheetModel

BSTableRow = Tuple[
    str, str, str, float, float, float, float, float, float, float, float
]


class AccountingItem(TiaItemModel):
    """Dataclass representing an item of some accounting.

    Args:
        description (str): The description or label of the item.
        value (float): The amount of the item, e.g. 1000, if you
            received 1000 €.
        currency (str, optional): The currency the value is given in.
        vat (float, optional): The VAT in %% for the item.
        date: The date you made/received the payment (CashAccounting) or the date you
            are about to make/receive the payment (Accrual Accounting)
    """

    description: str
    value: float
    currency: str = "€"
    vat: float = Field(default=19, ge=0, lt=100)
    date: datetime.date = datetime.date.today()

    @property
    def subtotal(self) -> float:
        """Subtotal of the `AccountingItem`."""
        return self.value

    @property
    def total(self) -> float:
        """Total of the `AccountingItem`."""
        return super().total

    @property
    def tax(self) -> float:
        """Tax of the `AccountingItem`."""
        return super().tax

    @classmethod
    def __headers__(cls) -> List[str]:
        """__header__-method of `BalanceSheetItem`.

        Returns the header for a table representation of a `TypedList` of
        `BalanceSheetItems`.
        """
        return [
            "Receipt No.",
            "Date",
            "Transaction",
            "Revenue(Net)",
            "Revenue(VAT)",
            "Revenue(Total)",
            "Expenditure(Net)",
            "Expenditure(VAT)",
            "Expenditure(Total)",
            "VAT Paid",
            "VAT Debt",
        ]

    @property
    def __values__(self) -> List[Any]:
        """__values__-method of `BalanceSheetItem`.

        Returns the values for table and representation of a
        `TypedList` of `BalanceSheetItem`.

        Returns:
            BSTableRow: A row for the `TypedList` table.
        """
        if self.subtotal >= 0:
            return [
                self.date,
                self.description,
                self.subtotal,
                self.tax,
                self.subtotal + self.tax,
                *[0 for _ in range(4)],
                self.tax,
            ]
        else:
            return [
                self.date,
                self.description,
                *[0 for _ in range(3)],
                -self.subtotal,
                -self.tax,
                -self.tax - self.subtotal,
                0,
                self.tax,
            ]


class AccountingConfiguration(TiaConfigBaseModel):
    """Dataclass having the configuration of the Accounting."""

    # language: str = "english"


class CashAccounting(TiaSheetModel[AccountingItem]):
    """The class for the balance sheet.

    Subclass of `TiaSheetModel`.

    Attributes:
        config (AccountingConfiguration): The configuration of the `CashAccounting`.
        items List[AccountingItem]: The items of the `CashAccounting`.
    """

    config: AccountingConfiguration
    items: List[AccountingItem] = []

    @property
    def subtotals(self) -> Tuple[float, float]:
        """Getter of subtotal. Setter is not defined.

        Returns:
            Tuple[float, float]: The subtotals (revenues, expenditures)
                of the cash accounting.
        """
        return (
            sum(item.subtotal for item in self.items if item.subtotal >= 0),
            sum(item.subtotal for item in self.items if item.subtotal < 0),
        )

    @property
    def taxes(self) -> Tuple[float, float]:
        """Getter of taxes. Setter is not defined.

        Returns:
            Tuple[float, float]: The taxes (revenues, expenditures) contained
                in the cash accounting.
        """
        return (
            sum(item.tax for item in self.items if item.tax >= 0),
            sum(item.tax for item in self.items if item.tax < 0),
        )

    @property
    def totals(self) -> Union[Tuple[float, float], Tuple[float, ...]]:
        """Getter of total. Setter is not defined.

        Returns:
            Union[Tuple[float, float], Tuple[float, ...]]: The total = subtotal + tax
                of the cash accounting.
        """
        return tuple(
            subtotal + tax for subtotal, tax in zip(self.subtotals, self.taxes)
        )

    @property
    def sorted(self) -> "CashAccounting":
        """Sorts the items by `date` attribute.

        Returns:
            CashAccounting: The sorted `CashAccounting` `self`.
        """
        self.items = sorted(self.items, key=operator.attrgetter("date"))
        return self
