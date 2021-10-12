"""Tests printer."""
from typing import Any
from typing import Dict
from typing import List

import pathlib
import shutil

import pytest
from pydantic import ValidationError
from pyfakefs import fake_filesystem  # type: ignore[import]

from tia.balances import AccountingConfiguration
from tia.balances import AccountingItem
from tia.balances import CashAccounting
from tia.client import Client
from tia.company import Company
from tia.invoices import Invoice
from tia.invoices import InvoiceConfiguration
from tia.invoices import InvoiceItem
from tia.printer import TEX_TEMPLATE_BS
from tia.printer import TEX_TEMPLATE_INV
from tia.printer import Printer
from tia.printer import TemplateDirs
from tia.utils import create_directory

inv_dir = pathlib.Path("/invoices")
eur_dir = pathlib.Path("/eur")


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
def acc_config() -> AccountingConfiguration:
    """Some `AccountingConfiguration`.

    Returns:
        AccountingConfiguration: Some `AccountingConfiguration`.
    """
    return AccountingConfiguration()


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
def cash_acc(some_ca: CashAccounting) -> CashAccounting:
    """Returns instance of `CashAccounting` with items."""
    return some_ca


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
def some_invoice(full_invoice_data: Dict[str, Any]) -> Invoice:
    """Returns some `Invoice`."""
    return Invoice(**full_invoice_data)


def test_printer_init(fake_filesystem: fake_filesystem.FakeFilesystem) -> None:
    """It creates an instance."""
    inv_dir = pathlib.Path("/invoices")
    eur_dir = pathlib.Path("/eur")
    fake_filesystem.create_dir(inv_dir)
    fake_filesystem.create_dir(eur_dir)
    printer = Printer(pdf_invoice_dir=inv_dir, pdf_eur_dir=eur_dir)
    assert printer.pdf_invoice_dir == inv_dir
    assert printer.mode.value == "tex"


def test_printer_invalid_mode(fake_filesystem: fake_filesystem.FakeFilesystem) -> None:
    """It raises, if mode is invalid."""
    fake_filesystem.create_dir(inv_dir)
    fake_filesystem.create_dir(eur_dir)
    with pytest.raises(ValidationError):
        Printer(pdf_invoice_dir=inv_dir, pdf_eur_dir=eur_dir, mode="invalid")


def test_printer_ca_items_tex(
    fake_filesystem: fake_filesystem.FakeFilesystem, cash_acc: CashAccounting
) -> None:
    """Creates latex table with the content of the balance sheet."""
    template_dir = TemplateDirs.balance_sheet.value
    fake_filesystem.create_dir(inv_dir)
    fake_filesystem.create_dir(eur_dir)
    fake_filesystem.create_dir(template_dir)
    template_path = template_dir / TEX_TEMPLATE_BS
    with open(template_path, "w") as f:
        f.write("$items")
    printer = Printer(pdf_invoice_dir=inv_dir, pdf_eur_dir=eur_dir)
    tex = printer.ca_items_tex(cash_acc)
    assert all([entry in tex for entry in sum((row for row in cash_acc.table), [])])
    assert "&" in tex and "\\hline" in tex


def test_printer_ca_pdf(cash_acc: CashAccounting) -> None:
    """It creates a pdf file for a balance sheet."""
    eur_dir = pathlib.Path.home() / ".tia" / "pdfs"
    inv_dir = eur_dir
    create_directory(eur_dir)
    printer = Printer(pdf_invoice_dir=inv_dir, pdf_eur_dir=eur_dir)
    assert isinstance(printer.ca_tex(cash_acc), str)
    # pdf: pathlib.Path = printer.ca_pdf(cash_acc=cash_acc, pdf_dir=eur_dir)
    # assert pdf.is_file()
    # shutil.rmtree(eur_dir)


def test_printer_invoiceitems_tex(
    fake_filesystem: fake_filesystem.FakeFilesystem, some_invoice: Invoice
) -> None:
    """Creates latex table with the content of the balance sheet."""
    invoice = some_invoice
    inv_dir = pathlib.Path("/invoices")
    eur_dir = pathlib.Path("/eur")
    template_dir = TemplateDirs.invoice.value
    fake_filesystem.create_dir(inv_dir)
    fake_filesystem.create_dir(eur_dir)
    fake_filesystem.create_dir(template_dir)
    template_path = template_dir / TEX_TEMPLATE_INV
    printer = Printer(pdf_invoice_dir=inv_dir, pdf_eur_dir=eur_dir)
    with open(template_path, "w") as f:
        f.write("$items")
    tex = printer.invoiceitems_tex(invoice)
    # print(tex)
    # print([entry for entry in sum([row for row in cash_acc.table], [])])
    assert all(
        [
            str(entry) in tex
            for entry in sum((item.values for item in invoice.items), [])
        ]
    )
    subst_dict = printer._invoice_substitution_dict(invoice)
    with open(template_path, "a") as f:
        for key in subst_dict:
            f.write(f"${key}")
    tex = printer.invoice_tex(invoice=invoice)
    assert all(
        [
            str(value) in tex
            for value in subst_dict.values()
            if not isinstance(value, bool)
        ]
    )


def test_printer_invoice_pdf(some_invoice: Invoice) -> None:
    """It creates a pdf file for a balance sheet."""
    eur_dir = pathlib.Path.home() / ".tia" / "pdfs"
    inv_dir = eur_dir
    create_directory(eur_dir)
    printer = Printer(pdf_invoice_dir=inv_dir, pdf_eur_dir=eur_dir)
    assert isinstance(printer.invoice_tex(some_invoice), str)
    # pdf: pathlib.Path = printer.invoice_pdf(invoice=some_invoice, pdf_dir=eur_dir)
    # assert pdf.is_file()
    shutil.rmtree(eur_dir)
