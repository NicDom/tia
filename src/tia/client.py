"""Module for clients in TIA."""
from typing import List
from typing import Optional
from typing import TypedDict

import pydantic
from tabulate import tabulate  # type: ignore

from tia.basemodels import CompanyAndClientABCBaseModel


class ClientDict(TypedDict):
    """TypedDict for `Client`."""

    name: str
    street: str
    plz: str
    country: str
    email: str
    invoicemail: Optional[str]
    remindermail: Optional[str]


def client_alias_generator(string: str) -> str:
    """The alias_generator function for the Client class.

    Generates the aliases for the classes variables.
    Aliases are given by: "client" + `variable_name`

    Args:
        string (str): The variable name/ dictionary key of the class.

    Returns:
        str: "client" + the given string

    Example:
        >>> assert client_alias_generator("name") == "clientname"
    """
    return "client" + string


class Client(CompanyAndClientABCBaseModel):
    """Dataclass for client data.

    Args:
        ref (str): A referencenumber for the client. Needs to be five (5)
            digit long.
        name (str): The name of the client.
        street (str): The street, where the client is located.
        plz (str): The PLZ of the clients location.
        city (str): The city of the clients location.
        country (str): The country of the clients location.
        email (str): The official mail of the client.
        invoicemail (str, optional): The mail to which invoices needs to be sent. Set to
            mail, if omitted.
        remindermail (str, optional): The mail to which reminder needs to be sent. Set
            to mail, if omitted.
    """

    # name: str
    # street: str
    # plz: str
    # city: str
    # email: str
    ref: str
    country: str
    invoicemail: Optional[str] = None
    remindermail: Optional[str] = None

    class Config:
        """Extra `Config`for `Client`.

        Inherits from `CompanyAndClientABCBaseModel.Config` and adds
        the proper `alias_generator` to it.
        """

        alias_generator = client_alias_generator

    @pydantic.validator("remindermail", "invoicemail", always=True)
    @classmethod
    def are_invoicemail_or_remindermail_given(
        cls, v: Optional[str], values: ClientDict
    ) -> str:
        """Checks if invoicemail and/or remindermail are given.

        Checks if the email-address for invoice correspondence `invoicemail`
        and/or reminder correspondence `remindermail` are given and sets the
        missing ones to `email`.

        Args:
            v (Optional[str]): The value of `invoicemail` or `remindermails`
            values (ClientDict): The dictionary of values of the class.

        Returns:
            str: `v` or `values["email"]`.
        """
        return v or values["email"]

    @property
    def address(self) -> str:
        """Returns the full address of the client as a string.

        The full address is given by:
        `self.street`
        `self.plz`, `self.city`
        `self.country`

        There is no `address.setter`.

        Returns:
            str: The full address as a string.
        """
        return f"{self.street}\n{self.plz}, {self.city}\n{self.country}"

    @property
    def contact_information(self) -> str:
        """Getter for the contact information of the client as string.

        The client information are given by:
        `self.email`
        `self.invoicemail`
        `self.remindermail`

        There is no `contact_information.setter`.

        Returns:
            str: String representation of the contact information.
        """
        return (
            f"\n✉ (official): {self.email}\n✉ (invoice): {self.invoicemail}\n✉"
            f" (reminder): {self.remindermail}"
        )

    @property
    def compact(self) -> List[List[str]]:
        """Gives all client information as a list.

        Returns:
            List[List[str]]: The relevant client information.
        """
        return [
            ["Client_ID: " + self.ref + "\n" + self.name],
            [self.address],
            [self.contact_information],
        ]

    def __str__(self) -> str:
        """String representation of the Client class.

        Uses tabulate to return the client information in a niceley formatted way.

        Returns:
            str: The string representation of Client.
        """
        return str(tabulate(self.compact))
