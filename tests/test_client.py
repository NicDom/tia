"""Test suite for the client module."""
from typing import Dict

import pytest
from pydantic import ValidationError
from tabulate import tabulate  # type: ignore

from tia.client import Client


def test_client_init(some_client: Dict[str, str]) -> None:
    """It creates an instance with the given values.

    Args:
        some_client (Dict[str, str]): Data for an example `Client`.
    """
    client = Client(**some_client)
    assert client.dict() == some_client


def test_client_init_no_invoicemail(some_client: Dict[str, str]) -> None:
    """It sets `invoicemail` to `email`, if no `invoicemail` is given.

    Args:
        some_client (Dict[str, str]): Data for an example client
    """
    some_client.pop("invoicemail")
    client = Client(**some_client)
    assert client.invoicemail == client.email


def test_client_init_no_remindermail(some_client: Dict[str, str]) -> None:
    """It sets `remindermail` to `email`, if no `remindermail` is given.

    Args:
        some_client (Dict[str, str]): Data for an example client
    """
    some_client.pop("remindermail")
    client = Client(**some_client)
    assert client.remindermail == client.email


def test_client_init_extra_forbid(some_client: Dict[str, str]) -> None:
    """It raises if extra fields are given.

    Args:
        some_client (Dict[str, str]): Some `Client` data.
    """
    client_data = some_client.copy()
    client_data["extra_field"] = "not_allowed"
    with pytest.raises(ValidationError) as excinfo:
        Client(**client_data)
    info = str(excinfo)
    assert "extra fields not permitted" in info and "extra_field" in info


def test_client_address(some_client: Dict[str, str]) -> None:
    """It properly returns the clients address."""
    client = Client(**some_client)
    assert (
        client.address
        == f"{client.street}\n{client.plz}, {client.city}\n{client.country}"
    )


def test_client_contact_information(some_client: Dict[str, str]) -> None:
    """It properly returns contact information for the client."""
    client = Client(**some_client)
    assert (
        client.contact_information
        == f"\n✉ (official): {client.email}\n✉ (invoice): {client.invoicemail}\n✉"
        f" (reminder): {client.remindermail}"
    )


def test_client_compact(some_client: Dict[str, str]) -> None:
    """It returns all data to the client in a compact list."""
    client = Client(**some_client)
    assert client.compact == [
        ["Client_ID: " + client.ref + "\n" + client.name],
        [client.address],
        [client.contact_information],
    ]


def test_client__str__(some_client: Dict[str, str]) -> None:
    """It has a human readable string representation."""
    client = Client(**some_client)
    assert client.__str__() == tabulate(client.compact)
