"""Testsuite for balances."""
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

import operator

import pytest
from pydantic import ValidationError

from tia.balances import AccountingConfiguration
from tia.balances import AccountingItem
from tia.balances import CashAccounting

invalid_item_options = {"vat": [-1, 101]}


@pytest.fixture
def check_invalid_assignments() -> Callable[
    [Any, Dict[str, List[Any]], Optional[List[str]]], Any
]:
    """Returns callable that checks invalid assignments.

    Checks, if all combinations of invalid assignments given by `assignments`
    raise an error.
    """

    def inner(
        obj: Any, assignments: Dict[str, List[Any]], strings: Optional[List[str]] = None
    ) -> None:
        """Checks if invalid assignments for `obj` raise an error.

        Args:
            obj (Any): The object we want to test.
            assignments (Dict[str, List[Any]]): A dictionary of assignments to check.
                The keys are the attribute names.
                The values are lists, whose entries are the values we assign the
                attributes to.
            strings (Optional[List[str]], optional): Optional strings,
                whose appearance in the exception info is checked. Defaults to None.
        """
        for key, value_list in assignments.items():
            for value in value_list:
                with pytest.raises(ValidationError) as excinfo:
                    setattr(obj, key, value)
                if strings is not None:
                    assertions = [string in str(excinfo) for string in strings]
                else:
                    assertions = []
                assertions += [key in str(excinfo)]
                assert all(assertions)

    return inner


@pytest.fixture
def acc_config() -> AccountingConfiguration:
    """Some `AccountingConfiguration`.

    Returns:
        AccountingConfiguration: Some `AccountingConfiguration`.
    """
    return AccountingConfiguration()


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


######################################
#    AccountingConfiguration
######################################


def test_balance_config_init() -> None:
    """It properly creates an instance."""
    cash_acc_config = AccountingConfiguration(language="english")
    assert cash_acc_config.language == "english"


def test_balance_config_init_language_invalid() -> None:
    """It raises, if language is not supported."""
    with pytest.raises(ValidationError) as excinfo:
        AccountingConfiguration(language="invalid")
    assert "'invalid' is not supported" in str(excinfo)


######################################
#    AccountingItem
######################################


def test_item_init(acc_item_1: Dict[str, Any]) -> None:
    """It properly creates an instance.

    Properties are defined and work as expected.

    Args:
        acc_item_1 (Dict[str, Any]): Dict for some `AccountingItem`.
    """
    item = AccountingItem(**acc_item_1)
    assert item.dict() == acc_item_1
    assert item.subtotal == 0.7
    assert item.tax == item.subtotal * item.vat / 100
    assert item.total == item.subtotal + item.tax


def test_item_init_invalid_input_fail(acc_item_default: Dict[str, Any]) -> None:
    """It raises `ValidationError`, if input is invalid.

    Args:
        acc_item_default (Dict[str, Any]): [description]
    """
    item_data = acc_item_default.copy()
    for key in invalid_item_options:
        for value in invalid_item_options[key]:
            item_data[key] = value
            with pytest.raises(ValidationError) as excinfo:
                AccountingItem(**item_data)
            assert key in str(excinfo)


def test_item_init_invalid_assignment_fail(
    check_invalid_assignments: Callable[..., Any], acc_item_1: Dict[str, Any]
) -> None:
    """It raises on invalid assignment.

    `vat` is only valid if: 0 <= `vat` < 100

    Args:
        check_invalid_assignments (Callable[..., Any]): Checks, if all combinations
            of invalid assignments given by `assignments` raise an error.
        acc_item_1 (Dict[str, Any]): Dict for some `AccountingItem`.
    """
    item = AccountingItem(**acc_item_1)
    check_invalid_assignments(obj=item, assignments=invalid_item_options)


def test_item_typedlist_related_attributes(acc_item_1: Dict[str, Any]) -> None:
    """`__headers__` and `__values__` are properly defined.

    __headers__ give common first line for cash accounting.
    __values__ corresponds to the usual line of a cash accounting.

    Args:
        acc_item_1 (Dict[str, Any]): Dict for some `AccountingItem`.
    """
    item = AccountingItem(**acc_item_1)
    assert AccountingItem.__headers__() == [
        "Receipt No.",
        "Date",
        "Transaction",
        "Revenue(Net)",
        "Revenue(VAT)",
        "Revenue(Total)",
        "Expenditure(Net)",
        "Expenditure(VAT)",
        "Expenditure(Total)",
        "VAT Paid",
        "VAT Debt",
    ]
    assert item.__values__ == [
        item.date,
        item.description,
        item.subtotal,
        item.tax,
        item.subtotal + item.tax,
        *[0 for _ in range(4)],
        item.tax,
    ]
    item.value = -item.value
    assert item.__values__ == [
        item.date,
        item.description,
        *[0 for _ in range(3)],
        -item.subtotal,
        -item.tax,
        -item.tax - item.subtotal,
        0,
        item.tax,
    ]


######################################
#    CashAccounting
######################################


def test_cash_acc_init(some_ca: CashAccounting, ca_items: List[AccountingItem]) -> None:
    """It properly creates an instance with all properties as desired.

    Args:
        some_ca (CashAccounting): `CashAccounting` with items.
        ca_items (List[AccountingItem]): List of `AccountingItems`.
    """
    cash_acc = some_ca
    assert cash_acc.items == ca_items
    assert cash_acc == ca_items
    assert cash_acc.Config.validate_assignment
    # testing properties
    assert cash_acc.subtotals == (
        sum(item.subtotal for item in cash_acc.items if item.subtotal >= 0),
        sum(item.subtotal for item in cash_acc.items if item.subtotal < 0),
    )
    assert cash_acc.taxes == (
        sum(item.tax for item in cash_acc.items if item.tax >= 0),
        sum(item.tax for item in cash_acc.items if item.tax < 0),
    )
    assert cash_acc.totals == tuple(
        subtotal + tax for subtotal, tax in zip(cash_acc.subtotals, cash_acc.taxes)
    )
    assert cash_acc.total == sum(cash_acc.totals)
    assert cash_acc.subtotal == sum(cash_acc.subtotals)
    assert cash_acc.tax == sum(cash_acc.taxes)
    assert cash_acc.sorted.items == sorted(
        cash_acc.items, key=operator.attrgetter("date")
    )
    assert cash_acc.sorted == cash_acc == cash_acc.sorted.sorted


def test_cash_acc_add(empty_ca: CashAccounting, acc_item_1: Dict[str, Any]) -> None:
    """It adds an item to CashAccounting.

    Args:
        empty_ca (CashAccounting): `CashAccounting` without items.
        acc_item_1 (Dict[str, Any]): Dict for some `AccountingItem`.
    """
    cash_acc = empty_ca
    item = AccountingItem(**acc_item_1)
    cash_acc.add_item(item=item)
    assert item in cash_acc
    cash_acc.remove(item)
    assert item not in cash_acc
    cash_acc.append(item)
    assert item in cash_acc
    cash_acc.remove(item)


def test_cash_acc_edit(
    empty_ca: CashAccounting, ca_items: List[AccountingItem]
) -> None:
    """It edits existing items.

    Args:
        empty_ca (CashAccounting): `CashAccounting` without items.
        ca_items (List[AccountingItem]): List of `AccountingItems`.
    """
    cash_acc = empty_ca
    old_item = ca_items[0]
    new_item = ca_items[1]
    cash_acc.add_item(old_item)
    cash_acc.edit_item(old_item=old_item, new_item=new_item)
    assert new_item in cash_acc.items
    assert old_item not in cash_acc.items


def test_cash_acc_edit_dict(
    empty_ca: CashAccounting, acc_item_1: Dict[str, Any], acc_item_2: Dict[str, Any]
) -> None:
    """It updates an existing item with respect to a valid dict.

    Args:
        empty_ca (CashAccounting): `CashAccounting` without items.
        acc_item_1 (Dict[str, Any]): Dict for some `AccountingItem`.
        acc_item_2 (Dict[str, Any]): Dict for some `AccountingItem`.
    """
    cash_acc = empty_ca
    old_item = AccountingItem(**acc_item_2)
    copy_old_item = AccountingItem(**acc_item_2)
    new_item = AccountingItem(**acc_item_1)
    cash_acc.add_item(old_item)
    cash_acc.edit_item(old_item=old_item, new_item=acc_item_1)
    assert new_item in cash_acc.items
    assert copy_old_item not in cash_acc.items
    assert new_item in cash_acc
    assert copy_old_item not in cash_acc


def test_cash_acc_edit_invalid_input(
    empty_ca: CashAccounting, acc_item_1: Dict[str, Any], acc_item_2: Dict[str, Any]
) -> None:
    """It raises if `old_item` for `edit_item` does not exist or has wrong type.

    Args:
        empty_ca (CashAccounting): `CashAccounting` without items.
        acc_item_1 (Dict[str, Any]): Dict for some `AccountingItem`.
        acc_item_2 (Dict[str, Any]): Dict for some `AccountingItem`.
    """
    cash_acc = empty_ca
    old_item = AccountingItem(**acc_item_1)
    new_item = AccountingItem(**acc_item_2)
    cash_acc.append(old_item)
    invalid_item = "invalid"
    with pytest.raises(ValueError):
        cash_acc.edit_item(old_item=new_item, new_item=old_item)
        cash_acc.edit_item(old_item=invalid_item, new_item=new_item)  # type: ignore # noqa: B950
    # with pytest.raises(ValueError) as excinfo:
    #     cash_acc.edit_item(old_item=old_item, new_item=invalid_item)
    # assert f"{invalid_item}" in str(
    #     excinfo
    # ) and f"{cash_acc.item_type.__name__}" in str(excinfo)


def test_cash_acc_delete(some_ca: CashAccounting, acc_item_1: Dict[str, Any]) -> None:
    """It deletes an existing `AccountingItem`.

    Args:
        some_ca (CashAccounting): `CashAccounting` with items.
        acc_item_1 (Dict[str, Any]): Dict for some `AccountingItem`.
    """
    cash_acc = some_ca
    item = AccountingItem(**acc_item_1)
    cash_acc.delete_item(item=item)
    assert item not in cash_acc.items
    assert item not in cash_acc


def test_cash_acc_subtotal(some_ca: CashAccounting) -> None:
    """It returns the right subtotal.

    Args:
        some_ca (CashAccounting): `CashAccounting` with items.
    """
    cash_acc = some_ca
    expected = sum(item.subtotal for item in cash_acc.items)
    actual = cash_acc.subtotal
    assert actual == expected


def test_cash_acc_tax(some_ca: CashAccounting) -> None:
    """It returns the proper tax.

    Args:
        some_ca (CashAccounting): `CashAccounting` with items.
    """
    cash_acc = some_ca
    expected = sum(item.subtotal * item.vat / 100 for item in cash_acc.items)
    actual = cash_acc.tax
    assert actual == expected


def test_cash_acc_total(some_ca: CashAccounting) -> None:
    """It returns the proper total.

    Args:
        some_ca (CashAccounting): `CashAccounting` with items.
    """
    cash_acc = some_ca
    expected = cash_acc.subtotal + cash_acc.tax
    actual = cash_acc.total
    assert actual == expected


def test_cash_acc_delete_not_in_list(
    empty_ca: CashAccounting, acc_item_1: Dict[str, Any]
) -> None:
    """It raises on delete, if the item is none of the `CashAccounting`.

    Args:
        empty_ca (CashAccounting): `CashAccounting` without items.
        acc_item_1 (Dict[str, Any]): Dict for some `AccountingItem`.
    """
    cash_acc = empty_ca
    item = AccountingItem(**acc_item_1)
    with pytest.raises(ValueError):
        cash_acc.delete_item(item=item)


# ###############################################
# #
# #                EXCEPTION ONES
# #
# ###############################################


# def test_cash_acc_add_invalid_inputtype() -> None:
#     cash_acc = CashAccounting(**cash_acc_data)
#     item = "invalid"
#     with pytest.raises(ValidationError) -> None:
#         cash_acc.add_item(item=item)


# def test_cash_acc_delete_invalid_inputtype() -> None:
#     cash_acc = CashAccounting(**cash_acc_data)
#     item = "invalid"
#     with pytest.raises(ValidationError) -> None:
#         cash_acc.delete_item(item=item)


# def test_cash_acc_edit_invalid_inputtype() -> None:
#     cash_acc = CashAccounting(**cash_acc_data)
#     old_item = AccountingItem(**cash_acc_item_data_2)
#     new_item = "invalid"
#     with pytest.raises(ValidationError) -> None:
#         cash_acc.edit_item(old_item=old_item, new_item=new_item)


# def test_cash_acc_edit_invalid_dict() -> None:
#     cash_acc = CashAccounting(**cash_acc_data)
#     old_item = AccountingItem(**cash_acc_item_data_2)
#     new_item = {"vat": 101}
#     with pytest.raises(ValidationError) -> None:
#         cash_acc.edit_item(old_item=old_item, new_item=new_item)
#     new_item = {"non_existent": 101}
#     with pytest.raises(ValueError) -> None:
#         cash_acc.edit_item(old_item=old_item, new_item=new_item)


# def test_cash_acc_edit_not_in_list() -> None:
#     cash_acc = CashAccounting(**cash_acc_data)
#     old_item = AccountingItem(**acc_item_1)
#     new_item = AccountingItem(**cash_acc_item_data_2)
#     with pytest.raises(ValueError) -> None:
#         cash_acc.edit_item(old_item=old_item, new_item=new_item)
