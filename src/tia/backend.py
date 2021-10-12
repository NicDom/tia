"""The backend-module."""
# from typing import TypedDict
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import datetime
import operator
import os
import pathlib

import pydantic
from pydantic import DirectoryPath
from pydantic import ValidationError
from pydantic import validate_arguments

from tia.balances import AccountingConfiguration
from tia.balances import AccountingItem
from tia.balances import CashAccounting
from tia.basemodels import BS_BASENAME
from tia.basemodels import DIR_NAMES
from tia.basemodels import TiaBaseModel
from tia.basemodels import TiaConfigBaseModel
from tia.basemodels import TypedList
from tia.client import Client
from tia.company import Company
from tia.exceptions import TIANoInvoiceOpenedError
from tia.invoices import Invoice
from tia.invoices import InvoiceConfiguration
from tia.invoices import InvoiceItem
from tia.invoices import InvoiceMetadata
from tia.printer import Printer
from tia.utils import create_directory

# from tabulate import tabulate


# class Dict[str, Any](TypedDict):
#     """TypedDict for `TiaProfile`."""

#     company: Company
#     default_invoice_config: InvoiceConfiguration
#     default_accounting_config: AccountingConfiguration
#     parent_dir: Optional[DirectoryPath]
#     pdf_parent_dir: Optional[DirectoryPath]
#     pdf_invoice_dir: Optional[DirectoryPath]
#     pdf_eur_dir: Optional[DirectoryPath]
#     open_pdf: bool
#     auto_remind: bool


class TiaProfile(TiaConfigBaseModel):
    """Dataclass for the assistants profile.

    Is a subclass from `TiaConfigBaseModel`.

    Args:
        language (str, optional): The default language of the assistant an of a new
            invoice. Given and validated by the parent `TiaConfigBaseModel`.
            Defaults to "english".
        default_invoice_configs (InvoiceConfiguration): Default configurations for a new
            invoice.
        default_accounting_configs (AccountingConfiguration): Default configurations for
            a new cash_acc.
        parent_dir (DirectoryPath, optional): The path for the parent directory in the
            directory tree. Defaults to os.path.dirname(os.path.abspath(__file__)).
        invoice_dir (DirectoryPath, optional): The default directory to store the pdf of
            an invoice. Defaults to None.
        eur_dir (DirectoryPath, optional): The default directory to store the pdf of an
            EUR. Defaults to None.
        open_pdf (bool, optional): True if a pdf should get opened right after it was
            created. False otherwise. Defaults to True.
        auto_remind (bool, optional): If true reminders are send automatically when the
            assistant is started. Defaults to True.
    """

    # language: str = "english"  #  reminder that this parameter is also here
    company: Company

    default_invoice_config: InvoiceConfiguration
    default_accounting_config: AccountingConfiguration
    parent_dir: Optional[DirectoryPath] = None
    pdf_parent_dir: Optional[DirectoryPath] = None
    pdf_invoice_dir: Optional[DirectoryPath] = None
    pdf_eur_dir: Optional[DirectoryPath] = None
    open_pdf: bool = True
    auto_remind: bool = True

    @pydantic.root_validator(pre=True)
    @classmethod
    def build_dir_structure(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Builds the directory structure according to the given input.

        1. Set all missing values of the `root` to `None`.
        2. If `parent_dir` is `None` set it to default value:
            '$HOME/.tia/<company_name>'
        3. Build the pdf directory structure.
            a) If `pdf_parent_dir` is None set it to:
                `parent_dir` / "Balances"
            b) if `pdf_invoice_dir` is None set it to:
                `pdf_parent_dir` / Invoices
            c) if `pdf_eur_dir` is None set it to:
                `pdf_parent_dir` / EUR
        4. Create the several directories

        Args:
            values (Dict[str, Any]): The dictionary given to `Tia` at instantiation.

        Returns:
            Dict[str, Any]: The dict updated with the default values for the
                directories.
        """
        values = cls._set_missing_dirs_to_none(values)
        parent_dir = DIR_NAMES[0]
        company_name = values["company"].name

        if values[parent_dir] is None:
            values[parent_dir] = create_directory(
                pathlib.Path.home() / ".tia" / company_name
            )

        values = cls._build_pdf_folder_structure(values)
        return values

    @classmethod
    def _build_pdf_folder_structure(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Builds the pdf directory structure.

        1. If `pdf_parent_dir` is None set it to:
            `parent_dir` / "Balances"
        2. if `pdf_invoice_dir` is None set it to:
            `pdf_parent_dir` / Invoices
        3. if `pdf_eur_dir` is None set it to:
            `pdf_parent_dir` / EUR
        4. Create the several directories.


        Args:
            values (Dict[str, Any]): Dict given to `Tia` at instantiation.

        Returns:
            Dict[str, Any]: The dict updated with default values for the several
                directories where required.
        """
        parent_dir = DIR_NAMES[0]
        pdf_parent_dir = DIR_NAMES[1]

        if values[pdf_parent_dir] is None:
            values[pdf_parent_dir] = create_directory(values[parent_dir] / "Balances")

        desired_path_dict = {
            DIR_NAMES[2]: "Invoices",  # invoice_dir = DIR_NAMES[2]
            DIR_NAMES[3]: "EUR",  # eur_dir = DIR_NAMES[3]
        }
        keys = desired_path_dict.keys()
        for key in keys:
            if values[key] is None:
                values[key] = create_directory(
                    values[pdf_parent_dir] / desired_path_dict[key]
                )
        return values

    @classmethod
    def _set_missing_dirs_to_none(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Sets the in `values` missing directories to None.

        Args:
            values (Dict[str, Any]): Dict given to `Tia` at instantiation.

        Returns:
            Dict[str, Any]: The dict where missing directories where set to None.
        """
        for dir in DIR_NAMES:
            if dir not in values:
                values[dir] = None
        return values


class TIA(TiaBaseModel):
    """Main class."""

    profile: TiaProfile
    invoice: Optional[Invoice] = None
    year: int = datetime.date.today().year
    # cash_acc: Optional[CashAccounting] = None

    # @pydantic.validator("cash_acc", always=True)
    # @classmethod
    # def cash_acc_default(
    #     cls, v: Optional[CashAccounting], values: Dict[str, Any]
    # ) -> CashAccounting:
    #     return v or CashAccounting(
    #         config=values["profile"].default_accounting_config, items=[]
    #     )

    # def __post_init__(self) -> None:
    #     self.cash_acc = self.cash_acc or CashAccounting(
    #         config=self.profile.default_accounting_config,
    #         items=[]
    #     )

    @property
    def cash_acc(self) -> CashAccounting:
        """The cash accounting of `Tia`.

        Creates `CashAccounting` from `self._ca_filename` and returns it.

        Returns:
            CashAccounting: Cash accounting for the current `year` and `profile`.
        """
        filename = self._ca_filename
        try:
            result = CashAccounting.from_file(filename)
        except (FileNotFoundError, ValueError, ValidationError, TypeError) as e:
            print(e)
            result = CashAccounting(
                config=self.profile.default_accounting_config, items=[]
            )
        print(result.__repr__)
        return result

    @property
    def printer(self) -> Printer:
        """The `Printer` of this instance of `Tia`.

        Returns:
            Printer: The `Printer`.
        """
        return Printer(
            pdf_invoice_dir=self.profile.pdf_invoice_dir,
            pdf_eur_dir=self.profile.pdf_eur_dir,
        )

    @validate_arguments
    def list_files(
        self, dir: DirectoryPath, return_path: bool = True
    ) -> Union[List[pathlib.Path], List[str]]:
        """Lists all files in the given directory `dir`.

        Args: dir (DirectoryPath): The directory, whose files we want to list.
            return_path (bool): If true the full path of the files will be returned,
            else only the filenames. Defaults to `True`.

        Returns: Union[List[pathlib.Path], List[str]]: A list containing the filenames
            of the files in `dir`.
        """
        if return_path:
            return [
                dir / f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))
            ]
        else:
            return [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]

    def get_invoice(self, invoice_or_invoicenumber: Union[str, Invoice]) -> Invoice:
        """Private function that returns an invoice.

        If `invoice_or_invoicenumber` is of type `Invoice` and is in the TIA database,
        it returns `invoice`. Otherwise, the function assumes that `invoice` is an
        invoicenumber and checks, if an invoice with that number exists. If this
        succeeds, it returns the invoice corresponding to the given invoicenumber.

        Args:
            invoice_or_invoicenumber (Union[str, Invoice]): Invoice or invoicenumber.

        Returns:
            Invoice: `invoice`, if it is of type Invoice and if it exists in the tia
                database. The invoice corresponding to the invoicenumber `invoice`, if
                such an invoice exists.

        Raises:
            ValueError: If the invoice is not in the TIA database.
            TypeError: If `invoice_or_invoicenumber` has not a str or an instance of
                Invoice.
        """
        print(invoice_or_invoicenumber)
        if isinstance(invoice_or_invoicenumber, str):
            for filename in self.list_files(self.invoice_dir, return_path=False):
                if invoice_or_invoicenumber in str(filename):
                    invoice = Invoice.from_file(self.invoice_dir / filename)
                    return invoice
            raise (
                ValueError(f"The invoice {invoice_or_invoicenumber} does not exist.")
            )
        elif isinstance(invoice_or_invoicenumber, Invoice):
            invoice = invoice_or_invoicenumber
            for filename in self.list_files(self.invoice_dir):  # pragma: no cover
                if invoice.invoicenumber in str(filename):
                    return invoice
            raise (
                ValueError(f"The invoice {invoice_or_invoicenumber} does not exist.")
            )
        else:  # pragma: no cover
            raise (
                TypeError(
                    "Invoice needs to be str or an Invoice (not"
                    f" {type(invoice_or_invoicenumber).__name__})"
                )
            )

    @property
    def last_invoicenumber(self) -> str:
        """The last used invoicenumber.

        Required as invoicenumbers need to be unique and increasing.
        """
        invoices = self.invoices
        return str(self.year) + "000" if invoices == [] else invoices[-1].invoicenumber

    @property
    def parent_dir(self) -> pathlib.Path:
        """The root dir of TIA."""
        if self.profile.parent_dir is None:  # pragma: no cover
            raise (ValueError("No parent directory is defined."))
        return self.profile.parent_dir

    @property
    def invoice_dir(self) -> pathlib.Path:
        """The directory where the invoices are stored."""
        return create_directory(
            pathlib.Path(self.parent_dir) / ".invoices" / str(self.year)
        )

    @property
    def cash_acc_dir(self) -> pathlib.Path:
        """The directory where the balance sheet is stored."""
        return create_directory(
            pathlib.Path(self.parent_dir) / ".cash_accs" / str(self.year)
        )

    @property
    def client_dir(self) -> pathlib.Path:
        """Creates and returns the directory the clients are stored.

        Getter only, no setter defined.

        Returns:
            pathlib.Path: The directory the clients are stored.
        """
        return create_directory(pathlib.Path(self.parent_dir) / ".clients")

    @property
    def clients(self) -> TypedList[Client]:
        """Getter for all clients in the databas.

        Returns:
            TypedList[Client]: `TypedList` containing all clients in the database.
        """
        clients_list = [
            Client.from_file(file) for file in self.list_files(self.client_dir)
        ]
        return TypedList[Client](items=clients_list)

    @property
    def invoices(self) -> List[Invoice]:
        """Getter for all invoices in the database.

        Returns:
            List[Invoice]: List containing all invoices in the database.
        """
        if self.list_files(self.invoice_dir) == []:
            return []
        invoices_list = [
            Invoice.from_file(file) for file in self.list_files(self.invoice_dir)
        ]
        invoices_list = sorted(invoices_list, key=operator.attrgetter("invoicenumber"))
        return invoices_list

    @property
    def invoices_meta_list(self) -> TypedList[InvoiceMetadata]:
        """Metadata for every invoice of this `profile` in the `year`.

        Returns:
            TypedList[InvoiceMetadata]: Invoice metadata for all invoices.
        """
        meta_list = []
        for invoice in self.invoices:
            meta_list.append(invoice.meta)
        meta_list = sorted(meta_list, key=operator.attrgetter("invoicenumber"))
        return TypedList[InvoiceMetadata](items=meta_list)

    @validate_arguments
    def _load_client(
        self, client: Optional[Union[pathlib.Path, Client]] = None
    ) -> Client:
        """Returns instance of `Client` according to input.

        If `client` is a valid filepath, an instance is created from that file and
        returned.
        If `client` is an instance of `Client` it is returned.
        If `client` is `None`, it is checked if there is only one client known to `Tia`.
        If so, that `Client` is returned.
        Non of above: raise ValueError

        Args:
            client (Optional[Union[pathlib.Path, Client]], optional): Information to
                determine the `Client`. Defaults to None.

        Returns:
            Client: The client for the invoice.

        Raises:
            ValueError: if `client` was `None` and more than one client is in the
                database.
        """
        if isinstance(client, pathlib.Path):
            return Client.from_file(client)
        elif isinstance(client, Client):
            return client
        else:
            if len(self.list_files(self.client_dir)) == 1:
                filename = self.list_files(self.client_dir)[0]
                filepath = self.client_dir / filename
                return Client.from_file(filepath)
            else:
                raise (
                    ValueError(
                        "Client was None. Loading default client is aborted as"
                        f" none/several clients exist.\nClients found:\n {self.clients}"
                    )
                )

    def new_invoice(
        self,
        config: Optional[InvoiceConfiguration] = None,
        client: Optional[Union[pathlib.Path, Client]] = None,
        # company: Optional[Client] = None,
        items: Optional[Union[InvoiceItem, List[InvoiceItem]]] = None,
    ) -> Invoice:
        """Creates a new invoice and returns it.

        Args:
            config (Optional[InvoiceConfiguration], optional):
                The invoice configuration. Defaults to None.
            client (Optional[Client], optional): The client. Defaults to None.
            items (Union[InvoiceItem, List[InvoiceItem]], optional): The invoiceitems.
                Defaults to [].

        Returns:
            Invoice: The created invoice.
        """
        if items is None:  # pragma: no cover
            items = []
        invoicenumber = int(self.last_invoicenumber) + 1
        config = config or self.profile.default_invoice_config
        client = self._load_client(client)
        company = self.profile.company
        invoice = Invoice(
            invoicenumber=invoicenumber,
            config=config,
            client=client,
            company=company,
            items=items,
        )
        self.invoice = invoice
        self.save_invoice(invoice)
        return invoice

    @property
    def _ca_filename(self) -> pathlib.Path:
        """Returns path to the balance sheet.

        Returns:
            pathlib.Path: Path to the balance sheet.
        """
        return self.cash_acc_dir / f"{BS_BASENAME}{self.year}.json"

    def invoice_filename(self, invoice: Union[str, Invoice]) -> pathlib.Path:
        """Returns the filepath under which the invoice is stored.

        `invoice` might be an invoice or its invoicenumber.

        Args:
            invoice (Union[str, Invoice]): The invoice or its invoicenumber.

        Returns:
            pathlib.Path: The filepath to the invoice information.
        """
        invoicenumber = invoice if isinstance(invoice, str) else invoice.invoicenumber
        return self.invoice_dir / f"config_{invoicenumber}.json"

    @validate_arguments
    def open_invoice(self, invoice_or_invoicenumber: Union[str, Invoice]) -> Invoice:
        """Loads the invoice identified by `invoicenumber`.

        Args:
            invoice_or_invoicenumber (Union[str, Invoice]): The identifying
                invoicenumber.

        Returns:
            Invoice: The identifyied invoice.
        """
        self.invoice = self.get_invoice(invoice_or_invoicenumber)
        return self.invoice

    def _delete_files(self, invoicenumber: str) -> None:
        """Deletes all files realted to the invoice determined by `invoicenumber`.

        Args:
            invoicenumber (str): The invoicenumber of the invoice, whose files are
                to be deleted.
        """
        files = [
            self.invoice_dir / file
            for file in self.list_files(self.invoice_dir)
            if invoicenumber in str(file)
        ]
        for file in files:
            os.remove(file)

    def delete_invoice(self, invoice: Optional[Union[str, Invoice]] = None) -> None:
        """Deletes the invoice `invoice` and related data.

        `invoice` may be an invoicenumber or the invoice itself. Adjusts the
        invoicenumbers of the other invoices after deletion.

        Args:
            invoice (Optional[Union[str, Invoice]], optional): The invoice (or its
                invoicenumber) to delete. Defaults to None.
        """
        if invoice is None:
            invoice = self.last_invoicenumber
        invoice = self.get_invoice(invoice)
        self._adjust_invoicenumbers(invoice)
        self._delete_files(self.last_invoicenumber)

    def follow_up_invoice(self, invoice_a: Invoice, invoice_b: Invoice) -> bool:
        """Checks if `invoice_b` was made after `invoice_a`.

        Args:
            invoice_a (Invoice): First invoice for invoicenumber comparison
            invoice_b (Invoice): Second invoice for invoicenumber comparison

        Returns:
            bool: `True`, if `invoice_b` was created after `invoice_a` was created,
                else `False`.
        """
        return int(invoice_b.invoicenumber) > int(invoice_a.invoicenumber)

    def decrement_invoicenumber(self, invoice_b: Invoice) -> None:
        """Reduces the invoicenumber of `invoice_b` by one.

        Args:
            invoice_b (Invoice): The invoice, whose invoicenumber should be
                decremented.
        """
        invoice_b.invoicenumber = str(int(invoice_b.invoicenumber) - 1)
        self.save_invoice(invoice_b)

    def _adjust_invoicenumbers(self, deleted_invoice: Invoice) -> None:
        """Adjusts the invoicenumber according to the deleted invoice.

        Private method called by `delete_invoice` to adjust invoicenumbers on deletion.

        Args:
            deleted_invoice (Invoice): The deleted invoice.
        """
        for invoice in self.invoices:
            if self.follow_up_invoice(invoice_a=deleted_invoice, invoice_b=invoice):
                self.decrement_invoicenumber(invoice)

    def save_invoice(self, invoice: Optional[Invoice]) -> None:
        """Saves the invoice `invoice`.

        Saves the content of `invoice` to `self.invoice_filename`.

        Args:
            invoice (Invoice, optional): The invoice to be saved.

        Raises:
            TIANoInvoiceOpenedError: if `self.invoice` is ´None`.
        """
        if invoice is None:
            raise (TIANoInvoiceOpenedError())
        filename = self.invoice_filename(invoice.invoicenumber)
        with open(filename, "w") as f:
            f.write(invoice.json())

    def save_cash_acc(self, obj: CashAccounting) -> None:
        """Saves the cash accounting `obj`to `self._ca_filename`."""
        # invoice.config.deadline = str(invoice.config.deadline)
        filename = self._ca_filename
        with open(filename, "w") as f:
            f.write(obj.json())

    # # @staticmethod
    # def type_context(func: Callable) -> None:
    #     @wraps(func)
    #     def wrapper(*args, **kwargs) -> None:
    #         _self: "TIA" = args[0]
    #         print("asdfadsdagfdsökjhkj", func.__name__)
    #         if "obj" in kwargs:
    #             obj = kwargs["obj"]
    #         else:
    #             obj = None
    #         if "item" in kwargs:
    #             item = kwargs["item"]
    #         else:
    #             item = kwargs["old_item"]
    #             new_item = kwargs["new_item"]
    #             print(type(item), type(new_item))
    #             if not type(item) == type(new_item) and not
    # isinstance(new_item, dict):
    #                 raise (
    #                     ValueError(
    #                         f"Types of 'old_item' (type: {type(item)}) and 'new_item'"
    #                         f" (type: {type(new_item)}) need to be of
    # the same type, or"
    #                         " 'new_item' needs to be a dictionary."
    #                     )
    #                 )
    #         if obj is None:
    #             obj = _self.cash_acc
    #             if not isinstance(item, AccountingItem):
    #                 raise (
    #                     ValueError(
    #                         "'item' needs to be of type 'AccountingItem' but is of"
    #                         f" type {type(item)}"
    #                     )
    #                 )
    #             save = _self.save_cash_acc
    #         else:
    #             obj = _self._invoice(obj)
    #             if not isinstance(item, InvoiceItem):
    #                 raise (
    #                     ValueError(
    #                         "'item' needs to be of type 'InvoiceItem' but is of type"
    #                         f" {type(item)}"
    #                     )
    #                 )
    #             save = _self.save_invoice
    #         if "obj" in kwargs:
    #             del kwargs["obj"]
    #         getattr(obj, func.__name__)(**kwargs)
    #         save(obj)

    #     return wrapper

    def add_item(self, item: Union[InvoiceItem, AccountingItem]) -> None:
        """Depending on item type: adds 'item' to `cash_acc` or `invoice`.

        Adds item to `self.invoice`, if `item` is an instance of `InvoiceItem`.
        Adds item to `self.cash_acc`. if `item`is an instance of `AccountingItem`.

        Args: item (InvoiceItem): InvoiceItem that we are adding to 'invoice'.

        Raises: TIANoInvoiceOpenedError: if `self.invoice` is `None`. TypeError: if
            `old_item` is neither an instance of `AccountingItem` nor `InvoiceItem`.
        """
        # `self.invoice` needs to be set
        if self.invoice is None:
            raise (TIANoInvoiceOpenedError())
        if isinstance(item, InvoiceItem):
            self.invoice.add_item(item)
            self.save_invoice(self.invoice)
        elif isinstance(item, AccountingItem):
            ca = self.cash_acc
            ca.add_item(item)
            self.save_cash_acc(ca)
        else:  # pragma: no cover
            raise (
                TypeError(
                    "Item needs to be an InvoiceItem or AccountingItem (not"
                    f" {type(item).__name__}"
                )
            )

    # @type_context
    def delete_item(self, item: Union[InvoiceItem, AccountingItem]) -> None:
        """Deletes the InvoiceItem 'item' from the Invoice 'invoice'.

        Deletes item of `self.invoice`, if `item` is an instance of `InvoiceItem`.
        Deletes item of `self.cash_acc`. if `item`is an instance of `AccountingItem`.

        Args:
            item (InvoiceItem): InvoiceItem that gets deleted

        Raises:
            TIANoInvoiceOpenedError: if `self.invoice` is `None`.
            TypeError: if `old_item` is neither an instance of `AccountingItem` nor
                `InvoiceItem`.
        """
        if self.invoice is None:
            raise (TIANoInvoiceOpenedError())
        if isinstance(item, InvoiceItem):
            self.invoice.delete_item(item)
            self.save_invoice(self.invoice)
        elif isinstance(item, AccountingItem):
            ca = self.cash_acc
            ca.delete_item(item)
            self.save_cash_acc(ca)
        else:  # pragma: no cover
            raise (
                TypeError(
                    "Item needs to be an InvoiceItem or AccountingItem (not"
                    f" {type(item).__name__}"
                )
            )

    # @type_context
    def edit_item(
        self,
        old_item: Union[AccountingItem, InvoiceItem],
        new_item: Union[AccountingItem, InvoiceItem, Dict[str, Any]],
    ) -> None:
        """Changes the InvoiceItem 'item' of the Invoice 'invoice' to 'new_item'.

        Edits item in `self.invoice`, if `old_item` is an instance of `InvoiceItem`.
        Edits item in `self.cash_acc`. if `old_item` is an instance of `AccountingItem`.

        Args:
            old_item (InvoiceItem): The `InvoiceItem` we want to edit.
            new_item (Union[InvoiceItem, Dict[str, Any]]):
                The new_item.

        Raises:
            TIANoInvoiceOpenedError: if `self.invoice` is `None`.
            TypeError: if `old_item` is neither an instance of `AccountingItem` nor
                `InvoiceItem`.
            ValueError: If `new_item` is no dict and `new_item` and `old_item` are
                not of the same type.
        """
        if self.invoice is None:
            raise (TIANoInvoiceOpenedError())
        if not isinstance(new_item, dict):
            # if `new_item` is no dict, `old_item` and `new_item` need to have the same
            # type
            if type(new_item) != type(old_item):
                raise (
                    ValueError(
                        "new_item and old_item need to be of the same type (or old_item"
                        " needs to be a valid dict)"
                    )
                )
        if isinstance(old_item, InvoiceItem):
            self.invoice.edit_item(old_item, new_item)  # type: ignore[arg-type]
            self.save_invoice(self.invoice)
        elif isinstance(old_item, AccountingItem):
            ca = self.cash_acc
            ca.edit_item(old_item, new_item)  # type: ignore[arg-type]
            self.save_cash_acc(ca)
        else:  # pragma: no cover
            raise (
                TypeError(
                    "Item needs to be an InvoiceItem or AccountingItem (not"
                    f" {type(old_item).__name__}"
                )
            )
