"""Testsuite for company."""
from typing import Any
from typing import Dict

import pytest
from pydantic.error_wrappers import ValidationError
from tabulate import tabulate  # type: ignore

from tia.company import Company

# The correct BIC and bankname for the given IBAN (DE89 3704 0044 0532 0130 00) -> None:
correct_bic_and_bank_to_iban: Dict[str, str] = {
    "companybic": "COBADEFFXXX",
    "companybank": "CommerzBk TF MZ 1, Mainz",
}


def test_company_init_validate_account_true(company_data: Dict[str, Any]) -> None:
    """It validates the IBAN and sets via `schwifty` a valid BIC and bankname."""
    company = Company(**company_data)
    company_data_after_account_validation = company_data.copy()
    company_data_after_account_validation.update(correct_bic_and_bank_to_iban)
    assert company.dict(by_alias=True) == company_data_after_account_validation


def test_company_init_no_bic_and_bank_validate_account_true(
    company_data: Dict[str, Any]
) -> None:
    """It validates the IBAN and sets via `schwifty` a valid BIC and bankname.

    BIC and bank information are optional.
    """
    company_data.pop("companybic")
    company_data.pop("companybank")
    # Following line is only to make sure the following lines are not longer than 88
    # chars
    company = Company(**company_data)
    company_data_after_account_validation = company_data.copy()
    company_data_after_account_validation.update(correct_bic_and_bank_to_iban)
    assert company.dict(by_alias=True) == company_data_after_account_validation
    bic = correct_bic_and_bank_to_iban["companybic"]
    copy = company_data.copy()
    copy["companybic"] = bic
    company = Company(**copy)
    assert company.dict(by_alias=True) == company_data_after_account_validation


def test_company_init_invalid_iban_validate_account_true(
    company_data: Dict[str, Any]
) -> None:
    """It raises when the given IBAN is invalid."""
    company_data["companyiban"] = "DE89 3704 0044 0532 0130"
    with pytest.raises(ValidationError) as excinfo:
        Company(**company_data)
    info = str(excinfo)
    assert "Invalid IBAN length" in info


def test_company_init_no_bic_validate_account_false(
    company_data: Dict[str, Any]
) -> None:
    """It raises when BIC is missing and account validation is false."""
    company_data["validate_account_information"] = False
    company_data.pop("companybic")
    with pytest.raises(ValidationError) as excinfo:
        Company(**company_data)
    info = str(excinfo).lower()
    assert all(["bic" in info or "bank" in info, "missing" in info])


def test_company_init_ambiguous_data_given(company_data: Dict[str, Any]) -> None:
    """It raises when an attribute appears by its name and its alias."""
    company_data = company_data.copy()
    company_data["bic"] = "another_bic"
    with pytest.raises(ValidationError) as excinfo:
        Company(**company_data)
    info = str(excinfo)
    assert "companybic" in info and "bic" in info


def test_company_init_no_bank_to_iban_existing(company_data: Dict[str, Any]) -> None:
    """It raises when it couldn't determine the bank using the IBAN."""
    company_data.pop("companybic")
    company_data.pop("companybank")
    company_data["companyiban"] = "GB51RPOQ40801609753513"
    with pytest.raises(ValidationError) as excinfo:
        Company(**company_data)
    assert "missing" in str(excinfo)


def test_company_init_no_bic_no_bank_validate_account_false(
    company_data: Dict[str, Any]
) -> None:
    """It raises when BIC or bankname is missing and account validation is false."""
    company_data.pop("companybic")
    company_data.pop("companybank")
    company_data["validate_account_information"] = False
    with pytest.raises(ValidationError) as excinfo:
        Company(**company_data)
    info = str(excinfo).lower()
    assert all(["bic" in info, "missing" in info])
    copy = company_data.copy()
    copy["bic"] = "bic"
    with pytest.raises(ValidationError) as excinfo:
        Company(**copy)
    info = str(excinfo).lower()
    print(info)
    assert all(["bank" in info, "missing" in info])


def test_company_init_bic_and_bank_given_validate_account_false(
    company_data: Dict[str, Any]
) -> None:
    """It does not get BIC and bankname from the IBAN when no account validation."""
    company_data["validate_account_information"] = False
    company = Company(**company_data)
    assert company.dict(by_alias=True) == company_data


def test_company_string_representations(company_data: Dict[str, Any]) -> None:
    """It prints all information in a human readable way."""
    company = Company(**company_data)
    company_data_after_account_validation = company_data.copy()
    company_data_after_account_validation.update(correct_bic_and_bank_to_iban)
    assert (
        company.address
        == f"{company.street}\n{company.plz}, {company.city}\n{company.country}"
    )
    assert company.contact_information == f"☏: {company.phone}\n✉: {company.email}"
    assert (
        company.bank_account_information
        == f"IBAN: {company.iban}\nBIC: {company.bic}\nBank: {company.bank}"
    )
    assert company.compact == [
        [company.name],
        [company.address],
        [company.contact_information],
        [company.bank_account_information],
        [company.taxnumber],
    ]
    assert str(company) == tabulate(company.compact)
