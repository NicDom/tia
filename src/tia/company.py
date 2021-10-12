"""Company module for TIA."""
from typing import Dict
from typing import List
from typing import Optional
from typing import TypedDict
from typing import Union

import pydantic
from pydantic.types import DirectoryPath
from pydantic.types import FilePath
from tabulate import tabulate  # type: ignore

from tia.basemodels import CompanyAndClientABCBaseModel
from tia.exceptions import CompanyAccountDataMissingError

ValuesDict = Dict[str, Union[bool, Optional[str]]]


class CompanyDict(TypedDict):
    """TypedDict for `Company`."""

    name: str
    street: str
    plz: str
    city: str
    country: str
    logo: Union[str, DirectoryPath]
    phone: str
    email: str
    validate_account_information: bool
    iban: str
    bank: Optional[str]
    bic: Optional[str]
    taxnumber: str


def company_alias_generator(string: str) -> str:
    """The alias_generator function for Company class.

    Generates the aliases for the classes variables.
    Aliases are given by: "company" + `variable_name` except for
    `validate_account_information`

    Args:
        string (str): The variable name/ dictionary key of the class.

    Returns:
        str: "company" + the given string

    Example:
        >>> assert company_alias_generator("name") == "companyname"
    """
    return "company" + string if "validate_account_information" != string else string


class Company(CompanyAndClientABCBaseModel):
    """Dataclass that contains company information.

    Args:
        name (str): The name of the company.
        street (str): The street of the address of the company.
        plz (str): The company's PLZ.
        city (str): The company's city.
        country (str): The company's country.
        logo (Union[str, DirectoryPath]): The path to the company logo.
        phone (str): The phone number of the company.
        email (str): The company's email-address.
        validate_account_information (bool): If set to True, will check if the
            bank-account information are valid. Will also determine 'companybank' and
            'companybic' from `iban` if IBAN is valid.
        iban (str): The company IBAN.
        bank (Optional[str]): The company bank. May be determined from IBAN.
        bic (Optional[str]): The company bic. May be determinded from IBAN.
        taxnumber (str): The company tax number/ tax-ID.
    """

    # name: str
    # street: str
    # plz: str
    # city: str
    # country: str
    # email :str
    logo: Union[str, FilePath]
    phone: str
    validate_account_information: bool  # Optional[bool]?
    taxnumber: str
    iban: str
    bic: Optional[str] = None
    bank: Optional[str] = None

    class Config:
        """Config for Company.

        Adds the proper `alias_generator` to the base config
        `CompanyAndClientABCBaseModel.Config`.
        """

        alias_generator = company_alias_generator

    # @property
    # def address(self) -> str:
    #     """String representation of the full company address.

    #     Full address is given by:
    #     `street`
    #     `plz`, `city`
    #     `country`

    #     Getter only. Setter is not defined.

    #     Returns:
    #         str: String representation of the full company address.
    #     """
    #     return f"{self.street}\n{self.plz}, {self.city}\n{self.country}"

    @property
    def contact_information(self) -> str:
        """String representation of the company contact information.

        Contact information are given by:
        `phone`
        `email`

        Getter only. Setter is not defined.

        Returns:
            str: String representation of the contact information.
        """
        return f"☏: {self.phone}\n✉: {self.email}"

    @property
    def bank_account_information(self) -> str:
        """String representation of the company bank account information.

        Account information are given by:
        `iban`
        `bic`
        `bank`

        Getter only. Setter is not defined.

        Returns:
            str: String representation of the bank account information.
        """
        return f"IBAN: {self.iban}\nBIC: {self.bic}\nBank: {self.bank}"

    @property
    def compact(self) -> List[List[str]]:
        """The company data string representations as a list.

        Used whenever it is convenient to have the class information
        string representations in a list.

        Returns:
            List[List[str]]: The company data.
        """
        return [
            [self.name],
            [self.address],
            [self.contact_information],
            [self.bank_account_information],
            [self.taxnumber],
        ]

    def __str__(self) -> str:
        """The string representation of the class.

        Gives the class in a human readable format, using tabulate.tabulate and
        `self.compact`.

        Returns:
            str: The company information in one table.
        """
        return str(tabulate(self.compact))

    # Method `bic_and_bank_given_if_no_account_validation` is not necessary as other
    # validator of this class `check_validity_iban_and_get_bic_and_bank_name` can do the
    # same. As this approach seems to be more convenient for possible future features I
    # kept it anyhow

    @pydantic.root_validator(pre=True)
    @classmethod
    def bic_and_bank_given_if_no_account_validation(
        cls, values: ValuesDict
    ) -> CompanyDict:
        """Checks if BIC and Bank are given.

        If `validate_account_information` is false, checks whether BIC and Bank are
        given. Raises `CompanyAccountDataMissingError` if one of them is missing. Check
        can also be made in  other validator of this class:
        `check_validity_iban_and_get_bic_and_bank_name`.

        Args:
            values (ValuesDict): The dictionary given to the class.

        Returns:
            CompanyDict: The validated dictionary.
        """
        prepped_values = cls._prepare_values(values)
        if not prepped_values["validate_account_information"]:
            cls._raise_error_if_bic_or_bank_is_not_given(prepped_values)
        else:
            prepped_values = cls._set_and_validate_account_information(prepped_values)
        return prepped_values

    @classmethod
    def _prepare_values(cls, values: ValuesDict) -> CompanyDict:
        """Private method that prepares `values` for further validation.

        Checks if the keys in the dictionary are aliases of Company attributes.
        If check is True, changes the key to the corresponding attribute name
        of Company.
        Sets missing account information to None.

        Args:
            values (ValuesDict): The dict given to Company at instantiation.

        Returns:
            CompanyDict: The for further validation prepared dictionary `values`.

        Raises:
            ValueError: If the alias of an class attribute and the attributename appear
                as a key in the dictionary `values`.
        """
        copy = values.copy()
        for key in values:
            if "company" in key:
                key_short = key.split("company")[1]
                if key_short in values:
                    raise (
                        ValueError(f"Giving '{key}' and '{key_short}' is ambiguous.")
                    )
                else:
                    copy[key_short] = copy.pop(key)
        if "bic" not in copy:
            copy["bic"] = None
        if "bank" not in copy:
            copy["bank"] = None
        return copy  # type: ignore[return-value]

    @classmethod
    def _raise_error_if_bic_or_bank_is_not_given(cls, values: CompanyDict) -> None:
        """Raises a `CompanyAccountDataMissingError` if bic or bank is missing.

        Only called if `validate_account_information` is False.

        Args:
            values (CompanyDict): The dict given to Company at instantiation.

        Raises:
            CompanyAccountDataMissingError: If `validate_account_information` is False
                and `bic` or `bank`  are missing.
        """
        if not values["bic"]:
            raise (CompanyAccountDataMissingError(message="Company BIC is missing."))
        if not values["bank"]:
            raise (CompanyAccountDataMissingError(message="Company Bank is missing."))

    @classmethod
    def _set_and_validate_account_information(cls, values: CompanyDict) -> CompanyDict:
        """Sets and validates the bank account information.

        Only called, if `validate_acount_information` is True. Validates the IBAN and
        retrieves BIC and bank information from that IBAN.
        All done using the `schwifty`-package. Sets missing information to None,
        thereby preparing the raise of a `CompanyAccountDataMissingError` in
        `validate_completeness_of_account_information`

        Args:
            values (CompanyDict): The dict given to Company

        Returns:
            CompanyDict: The validated dict.
        """
        from schwifty import iban as iban_module

        iban = iban_module.IBAN(values["iban"])
        bic = iban.bic
        try:
            bank = bic.bank_short_names[0]  # type: ignore[union-attr]
        except AttributeError:
            bank = None
        values["bic"] = str(bic) or values["bic"]
        values["bank"] = bank or values["bank"]
        return values

    @pydantic.validator("iban", "bic", "bank")
    @classmethod
    def validate_completeness_of_account_information(cls, v: str) -> str:
        """Checks if IBAN, BIC or bankname is missing.

        Args:
            v (str): The respective account information (iban, bic or bankname).

        Returns:
            str: The respective information if it is not `None`.

        Raises:
            CompanyAccountDataMissingError: If any of `iban`, `bic` or `bank` is
                missing.
        """
        if v is None:
            raise (CompanyAccountDataMissingError())
        return v
