"""conftest of TIA."""
from typing import Any
from typing import Dict
from typing import List

import pathlib

import pytest

from tia.balances import AccountingConfiguration
from tia.balances import AccountingItem
from tia.balances import CashAccounting
from tia.client import Client
from tia.company import Company
from tia.invoices import Invoice
from tia.invoices import InvoiceConfiguration
from tia.invoices import InvoiceItem

DIR_NAMES = ["parent_dir", "pdf_parent_dir", "pdf_invoice_dir", "pdf_eur_dir"]


@pytest.fixture(scope="session", autouse=True)
def faker_seed():
    """Default `faker` seed."""
    return 12345


@pytest.fixture(scope="session", autouse=True)
def random_seed():
    """Default `random` seed."""
    return 12345


@pytest.fixture
def some_person(faker) -> Dict[str, Any]:
    """Returns dict for some `Person`."""
    return {
        "first_name": faker.first_name(),
        "last_name": faker.last_name(),
        "salary": 1000,
        "currency": "€",
        "date_of_birth": faker.date_object(),
    }


@pytest.fixture
def second_person(faker) -> Dict[str, Any]:
    """Returns dict for some `Person`."""
    return {
        "first_name": faker.first_name(),
        "last_name": faker.last_name(),
        "salary": 1000,
        "currency": "€",
        "date_of_birth": faker.date_object(),
    }


@pytest.fixture
def full_invoiceitem(faker):
    """Returns a dict for an `InvoiceItem`."""
    full_item_dict = {
        "service": "Some Material",
        "qty": 5.0,
        "unit_price": 12.3,
        "vat": 19.0,
        "description": faker.sentence(nb_words=5),
    }
    return full_item_dict


@pytest.fixture
def other_invoiceitem(faker):
    """Returns a dict for an `InvoiceItem` with `vat` = 0."""
    full_item_dict = {
        "service": faker.sentence(nb_words=2),
        "qty": 1.0,
        "unit_price": 1.0,
        "vat": 0.0,
        "description": faker.sentence(nb_words=5),
    }
    return full_item_dict


@pytest.fixture
def acc_item_default() -> Dict[str, Any]:
    """Returns default dict for an `AccountingItem`."""
    return {
        "description": "Clear movement lay end.",
        "subtotal": 0.721918685087275,
    }


@pytest.fixture
def acc_item_1(faker) -> Dict[str, Any]:
    """Returns a dict for an `AccountingItem`."""
    return {
        "description": faker.sentence(nb_words=5),
        "value": 0.7,
        "currency": "€",
        "vat": 3.5,
        "date": faker.date_object(),
    }


@pytest.fixture
def acc_item_2(faker) -> Dict[str, Any]:
    """Returns a dict for an `AccountingItem`."""
    return {
        "description": faker.sentence(nb_words=5),
        "value": 10.1,
        "currency": "€",
        "vat": 4,
        "date": faker.date_object(),
    }


@pytest.fixture
def some_client():
    """Returns a dict for a `Client`."""
    client_option_1 = {
        "ref": "cost",
        "name": "Kristen Walker",
        "street": "3363 Hannah Plain",
        "plz": "89620",
        "city": "Port Peter",
        "country": "United States",
        "email": "system@hotmail.com",
        "invoicemail": "page@hotmail.com",
        "remindermail": "speech@hotmail.com",
    }
    return client_option_1


@pytest.fixture
def company_data():
    """Returns a dict for some `Company` (`account_validation=True`)."""
    company_option_1 = {
        "companyname": "Craig, Smith and Ford",
        "companystreet": "8429 Jones Street",
        "companyplz": "71974",
        "companycity": "Valerieshire",
        "companycountry": "United States",
        "companylogo": "choice",
        "companyphone": "001-044-850-0363",
        "companyemail": "increase@hotmail.com",
        "validate_account_information": True,
        "companytaxnumber": "368-04-6085",
        "companyiban": "DE89370400440532013000",
        "companybic": "cost",
        "companybank": "fight",
    }
    return company_option_1


@pytest.fixture
def list_of_invoiceitems(
    full_invoiceitem: Dict[str, Any], other_invoiceitem: Dict[str, Any]
) -> List[InvoiceItem]:
    """Returns a list of invoiceitems.

    Args:
        full_invoiceitem (Dict[str, Any]): [description]
        other_invoiceitem (Dict[str, Any]): [description]

    Returns:
        List[InvoiceItem]: A list of `InvoiceItems`.
    """
    return [InvoiceItem(**full_invoiceitem), InvoiceItem(**other_invoiceitem)]


@pytest.fixture
def full_invoice_data(
    some_client: Dict[str, Any],
    company_data: Dict[str, Any],
    list_of_invoiceitems: List[InvoiceItem],
    faker: Any,
) -> Dict[str, Any]:
    """Returns data for an `Invoice`.

    Args:
        some_client (Dict[str, Any]): Data for some `Client`
        company_data (Dict[str, Any]): Data for some 'Company'
        list_of_invoiceitems (List[InvoiceItem]): List of `InvoiceItem`
        faker (Any): faker object

    Returns:
        Dict[str, Any]: Data for an `Invoice`.
    """
    return {
        "invoicenumber": "2021001",
        "config": InvoiceConfiguration(),
        "client": Client(**some_client),
        "company": Company(**company_data),
        "items": list_of_invoiceitems,
        "payed_on": faker.date_object(),
    }


@pytest.fixture
def empty_invoice_data(full_invoice_data: Dict[str, Any]) -> Dict[str, Any]:
    """Returns data for an `Invoice` without items.

    Args:
        full_invoice_data (Dict[str, Any]): Data for an invoice with items.

    Returns:
        Dict[str, Any]: Data for an empty `Invoice`.
    """
    full_invoice_data.pop("items")
    return full_invoice_data


@pytest.fixture
def some_invoice(full_invoice_data: Dict[str, Any]) -> Invoice:
    """Returns some `Invoice`."""
    return Invoice(**full_invoice_data)


@pytest.fixture
def ca_items(
    acc_item_1: Dict[str, Any], acc_item_2: Dict[str, Any]
) -> List[AccountingItem]:
    """List of some `AccountingItems`.

    Args:
        acc_item_1 (Dict[str, Any]): Dict for some`AccountingItem`
        acc_item_2 (Dict[str, Any]): Dict for some `AccountingItem`

    Returns:
        List[AccountingItem]: List of `AccountingItem`.
    """
    return [AccountingItem(**acc_item_1), AccountingItem(**acc_item_2)]


@pytest.fixture
def empty_ca(acc_config: AccountingConfiguration) -> CashAccounting:
    """`CashAccounting` without any items.

    Args:
        acc_config (AccountingConfiguration): The configuration.

    Returns:
        CashAccounting: An empty `CashAccounting`.
    """
    return CashAccounting(
        config=acc_config,
    )


@pytest.fixture
def some_ca(
    acc_config: AccountingConfiguration, ca_items: List[AccountingItem]
) -> CashAccounting:
    """Some `CashAccounting` with items.

    Args:
        acc_config (AccountingConfiguration): The configuration.
        ca_items (List[AccountingItem]): Some CA items.

    Returns:
        CashAccounting: The CA.
    """
    return CashAccounting(config=acc_config, items=ca_items)


@pytest.fixture
def fake_filesystem(fs):  # pylint:disable=invalid-name
    """Provide a longer name acceptable to pylint for use in tests."""
    yield fs


@pytest.fixture
def tia_dirs():
    """Returns fake dirs for TIA instantiation."""
    _fake_paths = [
        pathlib.Path("/path"),
        pathlib.Path("/path/parent_dir"),
        pathlib.Path("/not_real/Invoice"),
        pathlib.Path("/some_location/EUR"),
    ]
    _keys = DIR_NAMES.copy()
    fake_dirs = dict(zip(_keys, _fake_paths))
    return fake_dirs
