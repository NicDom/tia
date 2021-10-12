"""Testsuite for backend module."""
from typing import Any
from typing import Callable
from typing import Dict
from typing import List

import datetime
import itertools
import pathlib

import orjson
import pytest
from pydantic import ValidationError

from tia.backend import TIA
from tia.backend import TiaProfile
from tia.balances import AccountingConfiguration
from tia.balances import AccountingItem
from tia.basemodels import DIR_NAMES
from tia.client import Client
from tia.company import Company
from tia.exceptions import TIANoInvoiceOpenedError
from tia.invoices import Invoice
from tia.invoices import InvoiceConfiguration
from tia.invoices import InvoiceItem
from tia.utils import create_directory

tia_parent_dir = pathlib.Path.home() / ".tia"


#############################
#         FIXTURES
#############################


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
def some_invoice(full_invoice_data: Dict[str, Any]) -> Invoice:
    """Returns some `Invoice`."""
    return Invoice(**full_invoice_data)


@pytest.fixture
def profile_default(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """Dict to create the default `TiaProfile`."""
    return {
        "company": Company(**company_data),
        "default_invoice_config": InvoiceConfiguration(),
        "default_accounting_config": AccountingConfiguration(),
    }


@pytest.fixture
def profile_with_fake_dirs(
    profile_default: Dict[str, Any]
) -> Callable[..., TiaProfile]:
    """Returns inner."""

    def inner(fake_dirs: Dict[str, pathlib.Path]) -> TiaProfile:
        """Creates fake directories and appends them to `profile_default`.

        Creates fake directories with paths given in `fake_dirs.values()` and
        returns a copy of `profile_default` updated `fake_dirs`.

        Args:
            fake_dirs (Dict[str, DirectoryPath]): A dictionary containing the
                directories and the keys for updating the copy of `profile_default`.

        Returns:
            TiaProfile: An instance of `TiaProfile` with `fake_dirs`
        """
        result = {**profile_default}
        for key, value in fake_dirs.items():
            result[key] = create_directory(value)
        return TiaProfile(**result)

    return inner


@pytest.fixture
def client(some_client: Dict[str, Any]) -> Client:
    """Returns an instance of `Client`."""
    return Client(**some_client)


@pytest.fixture
def invoiceitem(full_invoiceitem: Dict[str, Any]) -> InvoiceItem:
    """Returns an instance of an `InvoiceItem`."""
    return InvoiceItem(**full_invoiceitem)


@pytest.fixture
def second_invoiceitem(other_invoiceitem: Dict[str, Any]) -> InvoiceItem:
    """Returns an instance of an `InvoiceItem`."""
    return InvoiceItem(**other_invoiceitem)


@pytest.fixture
def acc_item(acc_item_1: Dict[str, Any]) -> AccountingItem:
    """Returns an instance of an `AccountingItem`."""
    return AccountingItem(**acc_item_1)


@pytest.fixture
def tia(
    fake_filesystem: Any,
    profile_with_fake_dirs: Callable[..., TiaProfile],
    tia_dirs: Dict[str, pathlib.Path],
) -> TIA:
    """Returns instance of `TIA`."""
    return TIA(profile=profile_with_fake_dirs(tia_dirs))


#################################
#  Test TiaProfile
#################################


def test_profile_init_default(profile_default: Dict[str, Any]) -> None:
    """It creates an instance and builds the default dir structure."""
    profile = TiaProfile(**profile_default)
    parent_dir = tia_parent_dir / profile.company.name
    pdf_parent_dir = parent_dir / "Balances"
    assertions = [
        profile.parent_dir == parent_dir,
        profile.pdf_parent_dir == parent_dir / "Balances",
        profile.pdf_invoice_dir == pdf_parent_dir / "Invoices",
        profile.pdf_eur_dir == pdf_parent_dir / "EUR",
        profile.open_pdf,
        profile.auto_remind,
        profile.__config__.validate_assignment,
    ]
    assert all(assertions)


def test_profile_init_default_and_pdf_parent(
    fake_filesystem: Any, profile_with_fake_dirs: Callable[..., TiaProfile]
) -> None:
    """It builds the pdf dirs relative to `pdf_parent`."""
    fake_path = pathlib.Path("/not_real")
    fake_dirs = {"pdf_parent_dir": fake_path}
    profile = profile_with_fake_dirs(fake_dirs=fake_dirs)
    pdf_parent_dir = fake_path
    assert profile.pdf_parent_dir == pdf_parent_dir
    assert profile.pdf_invoice_dir == pdf_parent_dir / "Invoices"
    assert profile.pdf_eur_dir == pdf_parent_dir / "EUR"


def test_profile_init_default_and_pdf_subdirs(
    fake_filesystem: Any, profile_with_fake_dirs: Callable[..., Any]
) -> None:
    """It does not build a pdf dir structure, if pdf dirs are given."""
    fake_paths = [pathlib.Path("/not_real/Invoice"), pathlib.Path("/some_location/EUR")]
    fake_dirs = {DIR_NAMES[2]: fake_paths[0], DIR_NAMES[3]: fake_paths[1]}
    for fake_path in fake_paths:
        fake_filesystem.create_dir(fake_path)
    profile = profile_with_fake_dirs(fake_dirs=fake_dirs)
    assertions = [
        profile.pdf_invoice_dir == fake_paths[0],
        profile.pdf_invoice_dir == fake_paths[1],
    ]
    assertions = [getattr(profile, key) == value for key, value in fake_dirs.items()]
    assert all(assertions)


def test_profile_init_default_and_pdf_dirs(
    fake_filesystem: Any, profile_with_fake_dirs: Callable[..., Dict[str, Any]]
) -> None:
    """It does not build a pdf dir structure, if pdf dirs are given."""
    fake_paths = [
        pathlib.Path("/path/parent_dir"),
        pathlib.Path("/not_real/Invoice"),
        pathlib.Path("/some_location/EUR"),
    ]
    keys = DIR_NAMES.copy()
    del keys[0]
    fake_dirs = {key: value for key in keys for value in fake_paths}

    # get all combinations of fake_dirs of len <= len(fake_dirs)
    key_iter_combs = [
        itertools.combinations(fake_dirs, i) for i in range(1, len(fake_dirs) + 1)
    ]
    key_combs = []
    for comb in key_iter_combs:
        key_combs += [[key for key in row] for row in comb]
    value_combs = [[fake_dirs[key] for key in row] for row in key_combs]
    fake_dir_combs = [
        # {key: value for key in key_combs[i] for value in value_combs[i]}
        dict(zip(key_combs[i], value_combs[i]))
        for i in range(len(key_combs))
    ]
    # getting combinations done, combinations stored in fake_dir_combs

    for fake_path in fake_paths:
        fake_filesystem.create_dir(fake_path)
    for fake_dirs in fake_dir_combs:
        profile = profile_with_fake_dirs(fake_dirs=fake_dirs)
        assertions = [
            getattr(profile, key) == value for key, value in fake_dirs.items()
        ]
        assert all(assertions)


def test_profile_init_invalid_language(profile_default: Dict[str, Any]) -> None:
    """It raises `ValidationError`, if language is not supported."""
    profile_default["language"] = "invalid"
    with pytest.raises(ValidationError) as excinfo:
        TiaProfile(**profile_default)
    assert "'invalid' is not supported" in str(excinfo)


##################################
#           Test Tia
##################################


def test_tia_init(fake_filesystem: Any, tia: TIA) -> None:
    """It creates an instance of `TIA`."""
    bs_language = tia.cash_acc.config.language
    tia_language = tia.profile.default_accounting_config.language
    assert tia.cash_acc.items == []
    assert bs_language == tia_language
    assert tia.year == datetime.date.today().year


def test_tia_new_invoice(fake_filesystem: Any, tia: TIA, some_client: Client) -> None:
    """It creates a new invoice and saves it.

    Invoice client an be given in three ways:
    1. As a `Client`
    2. As a filepath
    3. Omitted or None (if only client exists for the profile, that one is taken then)
    """
    # create file with client data
    client_filepath = tia.client_dir / "cl.json"
    with open(client_filepath, "wb") as f:
        f.write(orjson.dumps(some_client))

    # create new invoice with client = None
    invoice = tia.new_invoice()

    # tia.invoice should be equal to invoice
    assert tia.invoice == invoice

    # create expected invoice
    # the client should be now the single client found in client dir
    invoicenumber = str(datetime.date.today().year) + "001"
    config = tia.profile.default_invoice_config
    client = Client.from_file(client_filepath)
    company = tia.profile.company
    expect = Invoice(
        invoicenumber=invoicenumber, config=config, client=client, company=company
    )

    assert expect == invoice

    # check if invoice was properly saved
    # with open(tia.invoice_filename(invoicenumber), "r") as f:
    #     data = orjson.loads(f.read())
    # assert data["invoicenumber"] == invoicenumber
    expect = Invoice.from_file(tia.invoice_filename(invoicenumber))
    assert invoice == expect
    assert invoice == tia.invoices[0]
    assert invoice in tia.invoices

    # now give `client` as filepath to `new_invoice`
    invoice = tia.new_invoice(client=client_filepath)
    invoicenumber = str(datetime.date.today().year) + "002"
    expect = Invoice.from_file(tia.invoice_filename(invoicenumber))
    assert expect == invoice
    assert invoice.invoicenumber == invoicenumber
    # there should be two invoices now
    assert len(tia.invoices) == 2

    # now give `client` as `Client`
    invoice = tia.new_invoice(client=client)
    invoicenumber = str(datetime.date.today().year) + "003"
    expect = Invoice.from_file(tia.invoice_filename(invoicenumber))
    assert expect == invoice
    assert invoice.invoicenumber == invoicenumber


def test_tia_new_invoice_exception(fake_filesystem: Any, tia: TIA) -> None:
    """It raises, if no client for the new invoice could be determined."""
    with pytest.raises(ValueError):
        tia.new_invoice()


def test_tia_delete_invoice(fake_filesystem: Any, tia: TIA, client: Client) -> None:
    """It deletes an existing invoice."""
    # delete given invoice
    invoice = tia.new_invoice(client=client)
    assert invoice in tia.invoices
    tia.delete_invoice(invoice)
    assert invoice not in tia.invoices

    # delete according to invoicenumber
    invoice = tia.new_invoice(client=client)
    assert invoice in tia.invoices
    tia.delete_invoice(invoice.invoicenumber)
    assert invoice not in tia.invoices

    # default for `delete_invoice` is the last created invoice
    invoice = tia.new_invoice(client=client)
    tia.delete_invoice()
    assert invoice not in tia.invoices

    # it adjusts the invoicenumbers of other invoices on deletion
    for _ in range(3):
        tia.new_invoice(client=client)
    invnum = str(datetime.date.today().year) + "002"
    assert tia.invoices[-1].invoicenumber == str(datetime.date.today().year) + "003"
    tia.delete_invoice(invnum)
    # invoicenumber of last invoice should now be invum
    assert tia.invoices[-1].invoicenumber == invnum


def test_tia_delete_invoice_exception(
    fake_filesystem: Any, tia: TIA, some_invoice: Invoice
) -> None:
    """It raises `ValueError` on `delete_invoice`, if the invoice does not exist."""
    with pytest.raises(ValueError):
        tia.delete_invoice(some_invoice)


def test_tia_add_item(
    fake_filesystem: Any,
    tia: TIA,
    invoiceitem: InvoiceItem,
    client: Client,
    acc_item: AccountingItem,
) -> None:
    """It adds an item to the opened invoice or cash accounting."""
    tia.new_invoice(client=client)
    # if item is an invoiceitem add it to the opened invoice
    tia.add_item(item=invoiceitem)
    assert invoiceitem in tia.invoice  # type: ignore[operator]
    # if item is an accouting item, add it to the cash accounting
    tia.add_item(item=acc_item)
    assert acc_item in tia.cash_acc


def test_tia_add_item_exceptions(
    fake_filesystem: Any, tia: TIA, invoiceitem: InvoiceItem
) -> None:
    """It raises, if no invoice was opened, when adding an item."""
    with pytest.raises(TIANoInvoiceOpenedError):
        tia.add_item(invoiceitem)


def test_tia_delete_item_exceptions(
    fake_filesystem: Any, tia: TIA, invoiceitem: InvoiceItem
) -> None:
    """It raises, if no invoice was opened, when deleting an item."""
    with pytest.raises(TIANoInvoiceOpenedError):
        tia.delete_item(invoiceitem)


def test_tia_save_invoice_exceptions(fake_filesystem: Any, tia: TIA) -> None:
    """It raises, if invoice is None, when saving an invoice."""
    with pytest.raises(TIANoInvoiceOpenedError):
        tia.save_invoice(None)


def test_tia_edit_item(
    fake_filesystem: Any,
    tia: TIA,
    invoiceitem: InvoiceItem,
    other_invoiceitem: Dict[str, Any],
    acc_item: AccountingItem,
    acc_item_2: Dict[str, Any],
    client: Client,
) -> None:
    """It edits an item depending on the item type.

    Depending on old_item type and new_item type it looks for old_item inside of
    tia.invoice or tia.cash_acc.
    """
    ###################
    # edit invoice item
    ###################

    invoice = tia.new_invoice(client=client)
    tia.add_item(item=invoiceitem)
    new_item = InvoiceItem(**other_invoiceitem)
    # edit giving another `InvoiceItem`
    tia.edit_item(old_item=invoiceitem, new_item=new_item)
    assert new_item in invoice
    assert invoiceitem not in tia.invoice  # type: ignore[operator]

    # clean up the invoice
    tia.delete_item(item=new_item)
    tia.add_item(invoiceitem)
    assert new_item not in tia.invoice  # type: ignore[operator]
    # edit giving a valid `Dict`
    tia.edit_item(old_item=invoiceitem, new_item=other_invoiceitem)
    assert new_item in invoice

    ####################
    # edit cash_acc item
    ####################

    tia.add_item(acc_item)
    new_acc_item = AccountingItem(**acc_item_2)
    # edit giving another `InvoiceItem`
    tia.edit_item(old_item=acc_item, new_item=new_acc_item)
    assert new_acc_item in tia.cash_acc

    # clean up the cash_acc
    tia.delete_item(item=new_acc_item)
    tia.add_item(acc_item)
    assert new_acc_item not in tia.cash_acc
    # edit giving a valid `Dict`
    tia.edit_item(old_item=acc_item, new_item=acc_item_2)
    assert new_acc_item in tia.cash_acc


def test_tia_edit_item_exception_type_match(
    fake_filesystem: Any,
    tia: TIA,
    invoiceitem: InvoiceItem,
    acc_item: AccountingItem,
    client: Client,
) -> None:
    """It raises, the types of old_item and new_item don't match."""
    tia.new_invoice(client=client)
    with pytest.raises(ValueError):
        tia.edit_item(invoiceitem, acc_item)
    with pytest.raises(ValueError):
        tia.edit_item(acc_item, invoiceitem)


def test_tia_edit_item_exception_no_invoice_opened(
    fake_filesystem: Any,
    tia: TIA,
    invoiceitem: InvoiceItem,
    acc_item: AccountingItem,
) -> None:
    """It raises, if no invoice is opened."""
    with pytest.raises(TIANoInvoiceOpenedError) as excinfo:
        tia.edit_item(invoiceitem, acc_item)
    assert "No invoice is opened." in str(excinfo)


def test_tia_open_invoice(fake_filesystem: Any, tia: TIA, client: Client) -> None:
    """It opens an existing invoice and makes it `tia.invoice`."""
    invoice = tia.new_invoice(client=client)
    tia.new_invoice(client=client)
    opened_invoice = tia.open_invoice(invoice)
    assert opened_invoice == invoice
    assert opened_invoice.invoicenumber == str(datetime.date.today().year) + "001"


def test_tia_open_invoice_exceptions(
    fake_filesystem: Any, tia: TIA, some_invoice: Invoice
) -> None:
    """It raises if the invoice does not exist."""
    with pytest.raises(ValueError):
        tia.open_invoice(some_invoice)
    with pytest.raises(ValueError):
        tia.open_invoice("invalid")


def test_tia_get_invoice_exception(
    fake_filesystem: Any, tia: TIA, some_invoice: Invoice
) -> None:
    """It raises, if no invoice could be determined."""
    with pytest.raises(ValueError):
        tia.get_invoice(some_invoice)
    with pytest.raises(ValueError):
        tia.get_invoice("invalid_invoice_name")


def test_tia_meta_list(fake_filesystem: Any, tia: TIA, client: Client) -> None:
    """It returns metadata for the known invoices."""
    assert tia.invoices_meta_list == []
    inv_1 = tia.new_invoice(client=client)
    inv_2 = tia.new_invoice(client=client)
    assert tia.invoices_meta_list == [inv_1.meta, inv_2.meta]


def test_tia_printer(fake_filesystem: Any, tia: TIA) -> None:
    """It creates an instance of `Printer` with the right dirs."""
    assert tia.printer.pdf_invoice_dir == tia.profile.pdf_invoice_dir
    assert tia.printer.pdf_eur_dir == tia.profile.pdf_eur_dir


def test_tia_clients(fake_filesystem: Any, tia: TIA) -> None:
    """It returns `clients` as a `TypedList`."""
    assert hasattr(tia.clients, "table")
