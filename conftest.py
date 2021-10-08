"""conftest of TIA."""
from typing import Dict

import pathlib

import pytest

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
def some_person(faker) -> Dict[str, str]:
    """Returns dict some `Person`."""
    return {"first_name": faker.first_name(), "last_name": faker.last_name()}


@pytest.fixture
def full_invoiceitem(faker):
    """Returns a dict for an `InvoiceItem`."""
    full_item_dict = {
        "service": "Some Material",
        "qty": 5,
        "unit_price": 12.3,
        "vat": 19,
        "description": faker.sentence(nb_words=5),
    }
    return full_item_dict


@pytest.fixture
def other_invoiceitem(faker):
    """Returns a dict for an `InvoiceItem` with `vat` = 0."""
    full_item_dict = {
        "service": faker.sentence(nb_words=2),
        "qty": 1,
        "unit_price": 1,
        "vat": 0,
        "description": faker.sentence(nb_words=5),
    }
    return full_item_dict


@pytest.fixture
def some_client():
    """Returns a dict for a `Client`."""
    client_option_1 = {
        "clientref": "cost",
        "clientname": "Kristen Walker",
        "clientstreet": "3363 Hannah Plain",
        "clientplz": "89620",
        "clientcity": "Port Peter",
        "clientcountry": "United States",
        "clientemail": "system@hotmail.com",
        "clientinvoicemail": "page@hotmail.com",
        "clientremindermail": "speech@hotmail.com",
    }
    return client_option_1


@pytest.fixture
def some_client_no_invoicemail():
    """Returns a dict for some `Client` without an `invoicemail`."""
    client_data = {
        "clientref": "cost",
        "clientname": "Kristen Walker",
        "clientstreet": "3363 Hannah Plain",
        "clientplz": "89620",
        "clientcity": "Port Peter",
        "clientcountry": "United States",
        "clientemail": "system@hotmail.com",
        "clientremindermail": "speech@hotmail.com",
    }
    return client_data


@pytest.fixture
def some_client_no_remindermail():
    """Returns a dict for some `Client` without an `remindermail`."""
    client_data = {
        "clientref": "cost",
        "clientname": "Kristen Walker",
        "clientstreet": "3363 Hannah Plain",
        "clientplz": "89620",
        "clientcity": "Port Peter",
        "clientcountry": "United States",
        "clientemail": "system@hotmail.com",
        "clientinvoicemail": "page@hotmail.com",
    }
    return client_data


@pytest.fixture
def some_client_only_mail():
    """Returns a dict for some `Client` without `invoicemail` or `remindermail`."""
    client_data = {
        "clientref": "cost",
        "clientname": "Kristen Walker",
        "clientstreet": "3363 Hannah Plain",
        "clientplz": "89620",
        "clientcity": "Port Peter",
        "clientcountry": "United States",
        "clientemail": "system@hotmail.com",
    }
    return client_data


@pytest.fixture
def some_company_validate_account():
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
