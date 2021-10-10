"""Testssuite of the invoices-module."""
from typing import Any
from typing import Dict
from typing import List
from typing import Union

import datetime

import pytest

# from faker import Faker
from pydantic import ValidationError

from tia.balances import AccountingItem
from tia.basemodels import TypedList

# from tia.balances import AccountingItem
from tia.client import Client
from tia.company import Company

# from tia.exceptions import TaxValueError
# from tia.exceptions import UnknownInvoiceItemError
# from tia.invoices import Invoice
# from tia.invoices import InvoiceConfiguration
from tia.invoices import Invoice
from tia.invoices import InvoiceConfiguration
from tia.invoices import InvoiceItem
from tia.invoices import InvoiceMetadata

# import json
# import pathlib


# from tabulate import tabulate


# from tia.invoices import InvoiceMetadata

# fake = Faker()

ItemDict = Dict[str, Union[str, float]]
MetaDict = Dict[str, Union[str, float, datetime.date]]


@pytest.fixture
def inv_metadata_1() -> MetaDict:
    """Returns a dict for some `InvoiceMetadata`."""
    return {
        "invoicenumber": "order",
        "value": 6.223030212187535,
        "due_to": datetime.date(2021, 9, 1),
        "vat": 2.0,
        "payed_on": datetime.date(2021, 9, 10),
    }


@pytest.fixture
def inv_config_1() -> Dict[str, Any]:
    """Returns a dict for some `InvoiceConfiguration`."""
    return {
        "language": "english",
        "date": datetime.date(2021, 9, 13),
        "vat": 4.0,
        "deadline": datetime.timedelta(days=10),
        "paymentterms": "my",
        "invoicestyle": "classic",
        "currency_symbol": "$",
        "currency_code": "GMD",
    }


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


# #################################
# #     TESTING InvoiceItem
# #################################


def test_invoiceitem_vat_default(full_invoiceitem: Dict[str, Any]) -> None:
    """Default value for `vat` in InvoiceItem is None."""
    full_invoiceitem.pop("vat")
    item = InvoiceItem(**full_invoiceitem)
    assert item.vat == 99.99


def test_invoiceitem_qty_le_zero_fail(full_invoiceitem: Dict[str, Any]) -> None:
    """It raises `ValidationError`, if `qty` is less than zero."""
    full_invoiceitem["qty"] = 0
    with pytest.raises(ValidationError) as excinfo:
        InvoiceItem(**full_invoiceitem)
    assert "qty" in str(excinfo.value) and "ensure this value is greater than 0" in str(
        excinfo.value
    )


def test_invoiceitem_unit_price_le_zero_fail(full_invoiceitem: Dict[str, Any]) -> None:
    """IT raises `ValidationError`, if `unit_price` is less than zero."""
    full_invoiceitem["unit_price"] *= -1
    with pytest.raises(ValidationError) as excinfo:
        InvoiceItem(**full_invoiceitem)
    assert "unit_price" in str(
        excinfo.value
    ) and "ensure this value is greater than 0" in str(excinfo.value)


def test_invoiceitem_validate_assignment_fail(full_invoiceitem: Dict[str, Any]) -> None:
    """It raises ValidationError on invalid assignments."""
    item = InvoiceItem(**full_invoiceitem)
    with pytest.raises(ValidationError) as excinfo:
        item.vat = 101
    assert "vat" in str(excinfo.value) and "ensure this value is less than 100" in str(
        excinfo.value
    )


def test_invoiceitem_properties(full_invoiceitem: Dict[str, Any]) -> None:
    """Tests properties of InvoiceItem.

    Args:
        full_invoiceitem (Dict[str, Any]): Data for an InvoiceItem
    """
    item = InvoiceItem(**full_invoiceitem)
    assert item.subtotal == item.qty * item.unit_price
    assert item.values == [value for value in item.dict().values()]
    with pytest.raises(ValueError):
        item.subtotal = 1  # type: ignore[misc]
    assert item.subtotal == item.qty * item.unit_price


# #################################
# #     TESTING InvoiceMetadata
# #################################


def test_invoicemetadata_init(inv_metadata_1: MetaDict) -> None:
    """It sets the attributes to the given values."""
    meta = InvoiceMetadata(**inv_metadata_1)
    assert meta.payed_on == inv_metadata_1["payed_on"]
    assert meta.dict() == inv_metadata_1


def test_invoicemetadata_init_not_payed(inv_metadata_1: MetaDict) -> None:
    """Default value for `payed_on` is None."""
    inv_metadata_1.pop("payed_on")
    meta = InvoiceMetadata(**inv_metadata_1)
    assert meta.payed_on is None


def test_invoicemetadata_properties(inv_metadata_1: MetaDict) -> None:
    """Subtotal == `value`."""
    meta = InvoiceMetadata(**inv_metadata_1)
    assert meta.subtotal == meta.value


def test_invoicemetadata_typedlist_related(inv_metadata_1: MetaDict) -> None:
    """`__headers__` and `__values__` are defined as expected."""
    meta = InvoiceMetadata(**inv_metadata_1)
    assert InvoiceMetadata.__headers__() == [
        "invoicenumber",
        "total",
        "tax",
        "due_to",
        "payed_on",
    ]
    assert meta.__values__ != [value for value in meta.dict().values()]
    assert meta.__values__ == [
        getattr(meta, attr) for attr in InvoiceMetadata.__headers__()
    ]


# #################################
# #   TESTING InvoiceConfiguration
# #################################


def test_invoiceconfiguration_init(inv_config_1: Dict[str, Any]) -> None:
    """It creates an instance of InvoiceConfiguration."""
    config = InvoiceConfiguration(**inv_config_1)
    assert config.language == inv_config_1["language"]
    assert config.dict() == inv_config_1


def test_invoiceconfiguration_init_default() -> None:
    """It sets the correct default values."""
    config = InvoiceConfiguration()
    expected = [
        datetime.date.today(),
        0,
        datetime.timedelta(30),
        "",
        "classic",
        "€",
        "EUR",
    ]
    assert all([value in config.dict().values() for value in expected])


# #################################
# #     TESTING Invoice
# #################################


def test_invoice_init(full_invoice_data: Dict[str, Any]) -> None:
    """It creates an instance of `Invoice`."""
    invoice = Invoice(**full_invoice_data)
    assert invoice.dict() == full_invoice_data
    assert issubclass(Invoice, TypedList)


def test_invoice_init_given_no_items(empty_invoice_data: Dict[str, Any]) -> None:
    """Default value for items is []."""
    invoice = Invoice(**empty_invoice_data)
    assert invoice.items == []


def test_invoice_add_item(
    empty_invoice_data: Dict[str, Any], full_invoiceitem: Dict[str, Any]
) -> None:
    """It adds an item to the invoice."""
    invoice = Invoice(**empty_invoice_data)
    new_item = InvoiceItem(**full_invoiceitem)
    invoice.add_item(new_item)
    assert new_item in invoice.items


def test_invoice_add_item_vat_is_none(
    empty_invoice_data: Dict[str, Any], full_invoiceitem: Dict[str, Any]
) -> None:
    """It sets `item.vat` to `config.vat` if the former was omitted."""
    full_invoiceitem.pop("vat")
    invoice = Invoice(**empty_invoice_data)
    new_item = InvoiceItem(**full_invoiceitem)
    invoice.add_item(new_item)
    assert invoice.items[-1].vat == invoice.config.vat


# def test_invoice_valid_dict_add_item(empty_invoice_data: Dict[str, Any],
# full_invoiceitem: Dict[str, Any]) -> None:
#     """It adds an item to the invoice, given a dict."""
#     invoice = Invoice(**empty_invoice_data)
#     new_item = InvoiceItem(**full_invoiceitem)
#     invoice.add_item(full_invoiceitem)
#     assert new_item in invoice.items


def test_invoice_edit_item(
    empty_invoice_data: Dict[str, Any],
    full_invoiceitem: Dict[str, Any],
    other_invoiceitem: Dict[str, Any],
) -> None:
    """It sets an existing invoiceitem to another."""
    old_item = InvoiceItem(**full_invoiceitem)
    invoice = Invoice(**empty_invoice_data)
    invoice.add_item(old_item)
    new_item = InvoiceItem(**other_invoiceitem)
    invoice.edit_item(old_item=old_item, new_item=new_item)
    assert new_item in invoice.items and len(invoice.items) == 1


def test_invoice_valid_dict_edit_item(
    empty_invoice_data: Dict[str, Any],
    full_invoiceitem: Dict[str, Any],
    other_invoiceitem: Dict[str, Any],
) -> None:
    """It sets the values of an invoiceitem to the ones given by a dict."""
    old_item = InvoiceItem(**full_invoiceitem)
    invoice = Invoice(**empty_invoice_data)
    invoice.add_item(old_item)
    new_item = InvoiceItem(**other_invoiceitem)
    invoice.edit_item(old_item=old_item, new_item=other_invoiceitem)
    assert new_item in invoice.items and len(invoice.items) == 1


def test_invoice_properties(some_invoice: Invoice) -> None:
    """It has `due_to`, `meta` and `ca_item` properties.

    Args:
        some_invoice (Invoice): Some `Invoice`.
    """
    invoice = some_invoice
    assert invoice.due_to == invoice.config.date + invoice.config.deadline
    assert invoice.meta == InvoiceMetadata(
        invoicenumber=invoice.invoicenumber,
        value=invoice.total,
        due_to=invoice.due_to,
        vat=invoice.tax / invoice.subtotal * 100,
        payed_on=invoice.payed_on,
    )
    assert invoice.ca_item == AccountingItem(
        description=f"Invoice no. {invoice.invoicenumber}",
        value=invoice.total,
        vat=invoice.tax / invoice.subtotal * 100,
        currency=invoice.config.currency_symbol,
        date=invoice.payed_on,
    )
    invoice.payed_on = None
    assert invoice.ca_item is None


def test_invoice_str_representation(some_invoice: Invoice) -> None:
    """Properties for string representations are defined."""
    invoice = some_invoice
    representations = [
        invoice.items_str,
        invoice.company_and_client_str,
        invoice.invoice_str,
    ]
    assert all([isinstance(representation, str) for representation in representations])
    assert invoice.items_str == invoice.__str__()


def test_invoice_save_and_load(fake_filesystem: Any, some_invoice: Invoice) -> None:
    """It can be saved to json files and created by data given in json files."""
    filename = "invoice.json"
    with open(filename, "w") as f:
        f.write(some_invoice.json())
    with open(filename, "r") as f:
        invoice = Invoice.parse_raw(f.read())
    assert invoice.dict() == some_invoice.dict()
    assert Invoice.from_file(filename).dict() == some_invoice.dict()
