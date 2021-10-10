"""printer: Module for creating output files."""
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import datetime
import enum
import os
import pathlib
from string import Template

from babel.dates import format_date  # type: ignore[import]
from pydantic.types import DirectoryPath
from pydantic.types import FilePath

from tia.balances import CashAccounting
from tia.basemodels import BS_BASENAME
from tia.basemodels import INVOICE_BASENAME
from tia.basemodels import TiaBaseModel
from tia.invoices import Invoice
from tia.invoices import InvoiceConfiguration
from tia.utils import delete_file

PARENT_DIR = pathlib.Path.home() / ".tia"
TEMPLATE_DIR = pathlib.Path(__file__).resolve().parent
TEX_TEMPLATE_INV = "invoice_template.tex"
TEX_TEMPLATE_BS = "EUR_template.tex"


class PMode(enum.Enum):
    """Class representing the modes of the printer."""

    latex = "tex"
    txt = "txt"


class TemplateDirs(enum.Enum):
    """Class returning the template directories."""

    invoice = TEMPLATE_DIR / "templates"
    balance_sheet = TEMPLATE_DIR / "templates"

    def __str__(self) -> str:  # pragma: no cover
        """__str__ of TemplateDirs.

        Returns:
            str: The value.
        """
        return str(self.value)


class Printer(TiaBaseModel):
    """Class for generating the output files of TIA.

    Creates outputs for `CashAccounting` and `Invoice`.

    Args:
        pdf_invoice_dir (DirectoryPath): Directory, where invoice pdf is put.
        pdf_eur_dir (DirectoryPath): Directory the cash accounting pdf is put.
        mode (PMode, optional): File format for output. Defaults to PMode.latex.
    """

    pdf_invoice_dir: DirectoryPath
    pdf_eur_dir: DirectoryPath
    mode: PMode = PMode.latex

    # class Config:
    #     arbitrary_types_allowed = True

    ################################
    #    Print CashAccounting
    ################################

    def _bs_row_to_tex(self, row: Union[str, List[str]]) -> str:
        """Tex content for a row of the CashAccounting.

        Args:
            row (List[str]): The row.

        Returns:
            str: The texfile content for the row.
        """
        return " & ".join(row)

    def bs_items_tex(self, bs: CashAccounting) -> str:
        """Tex format for all items of the CashAccounting.

        Args:
            bs (CashAccounting): The balance sheet.

        Returns:
            str: The tex content for all balance sheet items.
        """
        return (
            " \\\\\n\t\t\\hline\n\t\t".join(
                self._bs_row_to_tex(row) for row in bs.table
            )
            + "\\\\"
        )

    def bs_tex(
        self, bs: CashAccounting, template_filename: str = TEX_TEMPLATE_BS
    ) -> str:
        """The full tex content of the CashAccounting.

        Output depends on the given template via `template_filename`.
        Replacement is done via `string.Template`.

        Args:
            bs (CashAccounting): The balance sheet.
            template_filename (str): Filename of the template to use.
                Defaults to TEX_TEMPLATE_BS.

        Returns:
            str: The content for the texfile for the given CashAccounting.
        """
        template_path = TemplateDirs.balance_sheet.value / template_filename
        with open(template_path) as f:
            template = f.read()
        content = Template(template).safe_substitute(items=self.bs_items_tex(bs))
        return content

    def bs_pdf(
        self,
        bs: CashAccounting,
        pdf_dir: DirectoryPath,
        template_filename: str = TEX_TEMPLATE_BS,
        year: Optional[int] = datetime.date.today().year,
    ) -> pathlib.Path:
        """Creates the pdf file for the CashAccounting at returns its path.

        Deletes all temporary files. Directory for the pdf is determined by pdf_dir.
        PDF is created via latexmk.

        Args:
            bs (CashAccounting): The CashAccounting.
            pdf_dir (DirectoryPath): The directory the pdf is put.
            template_filename (str): Filename for the template to be used.
                Defaults to TEX_TEMPLATE_BS.
            year (int, optional): Year the balance sheet refers to.
                Defaults to datetime.date.today().year.

        Returns:
            str: Path of the created pdf.
        """
        name = f"{BS_BASENAME}{year}"
        path = pathlib.Path(__file__).resolve().parent
        with open(path / f"{name}.tex", "wb") as f:
            f.write(self.bs_tex(bs, template_filename).encode("utf-8"))
            aux_dir = PARENT_DIR / ".aux_files" / f"{name}"
            command = " ".join(
                [
                    "latexmk",
                    "--pdf",
                    str(f.name),
                    f"--outdir={pdf_dir}",
                    f"--auxdir={aux_dir}",
                ]
            )
            filepath = f.name
        import subprocess  # noqa: S404

        subprocess.check_call(command)  # noqa: S603
        self.delete_aux_files(pdf_dir)
        os.remove(filepath)
        return pathlib.Path(pdf_dir) / f"{name}.pdf"

    ################################
    #    Print Invoice
    ################################

    def invoiceitems_tex(self, invoice: Invoice) -> str:
        """Tex content for all items of the invoice.

        Args:
            invoice (Invoice): The invoice.

        Returns:
            str: The tex content for all invoiceitems.
        """
        result = ""
        for item in invoice.items:
            values = item.values
            result += (
                "\\invoiceitem" + "".join([f"{{{value}}}" for value in values]) + "\n"
            )
        return result

    def _invoice_substitution_dict(self, invoice: Invoice) -> Dict[str, str]:
        config: InvoiceConfiguration = invoice.config
        client_data = invoice.client.dict(by_alias=True)
        company_data = invoice.company.dict(by_alias=True)
        date = format_date(config.date, format="short", locale="en")
        res = {
            **client_data,
            **company_data,
            "items": self.invoiceitems_tex(invoice),
            "invdate": f"\\SetDate[{date}]",
            "invoicenumber": invoice.invoicenumber,
            **invoice.config.dict(exclude={"client", "company"}),
        }
        # format datetime.timedelta for latex
        res["deadline"] = str(invoice.config.deadline.days)
        return res

    def invoice_tex(
        self, invoice: Invoice, template_filename: str = TEX_TEMPLATE_INV
    ) -> str:
        """Tex content corresponding to `invoice`.

        Output depends on the used template. Replacement is done via `string.Template`.

        Args:
            invoice (Invoice): The invoice.
            template_filename (str): Filename of the template to be used.
                Defaults to TEX_TEMPLATE_INV.

        Returns:
            str: The tex content.
        """
        template_path: FilePath = TemplateDirs.invoice.value / template_filename
        # if not template_path.is_file():
        #     raise (ValueError(f"The template {template_path} does not exist."))
        with open(template_path) as f:
            template = f.read()
        content = Template(template).safe_substitute(
            self._invoice_substitution_dict(invoice)
        )
        return content.replace("$", r"\$")

    def invoice_pdf(
        self,
        invoice: Invoice,
        pdf_dir: DirectoryPath,
        template_filename: str = TEX_TEMPLATE_INV,
    ) -> pathlib.Path:
        """Creates the pdf file for the invoice at returns its path.

        Deletes all temporary files. Directory for the pdf is determined by `pdf_dir`.
        PDF is created via `latexmk`.

        Args:
            invoice (Invoice): The invoice.
            pdf_dir (DirectoryPath): The directory the pdf is put.
            template_filename (str): Filename for the template to be used.
                Defaults to TEX_TEMPLATE_INV.

        Returns:
            str: Path of the created pdf.
        """
        name = f"{INVOICE_BASENAME}{invoice.invoicenumber}"
        path = pathlib.Path(__file__).resolve().parent / "templates"
        with open(path / f"{name}.tex", "wb") as f:
            f.write(self.invoice_tex(invoice, template_filename).encode("utf-8"))
            aux_dir = PARENT_DIR / ".aux_files" / f"{name}"
            command = " ".join(
                [
                    "latexmk",
                    "--pdf",
                    "--cd",
                    str(f.name),
                    f"--outdir={pdf_dir}",
                    f"--auxdir={aux_dir}",
                ]
            )
            filepath = f.name
        import subprocess  # noqa: S404

        subprocess.check_call(command)  # noqa: S603
        self.delete_aux_files(pdf_dir)
        os.remove(filepath)
        return pathlib.Path(pdf_dir) / f"{name}.pdf"

    def delete_aux_files(self, dir: DirectoryPath) -> None:
        """Deletes the aux files in `dir`.

        Args:
            dir (DirectoryPath): The directory we want to remove the aux-files from.
        """
        dir = pathlib.Path(dir)
        files = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
        for file in files:
            if ".pdf" not in file:
                delete_file(dir / file)
