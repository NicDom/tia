"""basemodels for TIA."""
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generic
from typing import Iterator
from typing import List
from typing import SupportsIndex
from typing import Type
from typing import TypeVar
from typing import Union
from typing import no_type_check

import datetime
import inspect
import pathlib
from abc import ABC
from abc import abstractmethod
from collections.abc import MutableSequence

import orjson
import pydantic
from babel.dates import format_date  # type: ignore[import]
from pydantic import BaseConfig
from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field
from pydantic.generics import GenericModel
from pydantic.json import pydantic_encoder
from tabulate import tabulate  # type: ignore

__all__ = [
    "TiaBaseConfig",
    "TiaBaseModel",
    "TiaConfigBaseModel",
    "TiaGenericModel",
    "TiaItemModel",
    "CompanyAndClientABCBaseModel",
    "TypedList",
]


DIR_NAMES = ["parent_dir", "pdf_parent_dir", "pdf_invoice_dir", "pdf_eur_dir"]
INVOICE_BASENAME = "invoice_"
BS_BASENAME = "EUR_"

SUPPORTED_LANGUAGES = ["english", "german"]

ObjType = TypeVar("ObjType", bound=BaseModel)

ItemType = TypeVar("ItemType")

ItemTType = TypeVar("ItemTType", bound="TiaItemModel")


class PatchedModel(BaseModel):  # pragma: no cover
    @no_type_check
    def __setattr__(self, name, value):
        """To be able to use properties with setters."""
        try:
            super().__setattr__(name, value)
        except ValueError as e:
            setters = inspect.getmembers(
                self.__class__,
                predicate=lambda x: isinstance(x, property) and x.fset is not None,
            )
            for setter_name, _ in setters:
                if setter_name == name:
                    object.__setattr__(self, name, value)
                    break
                else:
                    raise e


def orjson_dumps(
    obj: Dict[str, Any], *, default: Callable[..., Any] = pydantic_encoder
) -> str:
    """Default `json_dumps` for TIA.

    Args:
        obj (BaseModel): The object to 'dump'.
        default (Callable[..., Any], optional): The default encoder. Defaults to
            pydantic_encoder.

    Returns:
        str: The json formatted string of the object.
    """
    return orjson.dumps(obj, default=default).decode("utf-8")


class TiaBaseConfig(BaseConfig):
    """The base Config class of classes of TIA.

    Its values are:
    `validate_assignment` = True
    `extra` = Extra.forbid
    `allow_population_by_field_name` = True
    """

    validate_assignment = True
    extra = Extra.forbid
    allow_population_by_field_name = True
    json_loads = orjson.loads
    json_dumps = orjson_dumps


class TiaBaseModel(BaseModel):
    """The basic root class.

    It is a subclass of `pydantic.BaseModel`
    Config is given by `TiaBaseConfig`. Its values are:
    `validate_assignment` = True
    `extra` = Extra.forbid
    `allow_population_by_field_name` = True
    """

    @classmethod
    def from_file(cls: Type[ObjType], filepath: Union[str, pathlib.Path]) -> ObjType:
        """Same as `BaseModel.parse_file`, due to issue with unicode symbols."""
        with open(filepath, "r") as f:
            return cls.parse_raw(f.read())

    class Config(TiaBaseConfig):
        """The Config of `TiaBaseModel`."""


class TiaGenericModel(GenericModel):
    """Baseclass for GenericModels in TIA."""

    class Config(TiaBaseConfig):
        """Config for `TiaGenericModel`.

        Subclass of `TiaBaseConfig`.
        """


class TiaItemModel(TiaBaseModel, ABC):
    """Baseclass for items in TIA.

    Subclass of `TiaBaseModel`.
    """

    vat: float = Field(19, lt=100, ge=0)

    @property
    @abstractmethod
    def subtotal(self) -> float:
        """The subtotal of the item.

        Getter only. Setter is not defined.

        Returns:
            float: The subtotal of the item.
        """

    @property
    # @abstractmethod
    def total(self) -> float:
        """The total of the item.

        Getter only. Setter is not defined.

        Returns:
            float: The total = subtotal + tax of the item.
        """
        return self.subtotal + self.tax

    @property
    # @abstractmethod
    def tax(self) -> float:
        """The tax of the item.

        Getter only. Setter is not defined.

        Returns:
            float: The tax of the item.
        """
        return self.subtotal * self.vat / 100

    def _format_value(self, value: Any) -> str:
        """Private method for string formatting `__values__`.

        Used in `__values_str__` to create list containing the desired string
        formation of the elements of `__values__`.

        Args:
            value (Any): Value, whose string representation we want to create.

        Returns:
            str: String format of `value`.
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, float) or isinstance(value, int):
            try:
                return str(value) + self.currency if value != 0 else ""  # type: ignore # noqa: B950
            except (AttributeError):  # pragma: no cover
                return str(value) if value != 0 else ""
        elif isinstance(value, datetime.date):
            return str(format_date(value, format="short", locale="en"))
        else:
            return str(value)

    @property
    def __values_str__(self) -> List[str]:
        """String format for __values__.

        Used for displaying as part of a TypedList.

        Returns:
            List[str]: Formatted strings for the several items.
        """
        return list(map(self._format_value, self.__values__))

    @property
    def __values__(self) -> List[Any]:
        """List of values of the 'item'.

        Required for `dataframe`-property of `TypedList`.

        Returns:
            List[Any]: List containing the values of the 'item'.
        """
        return [value for value in self.dict().values()]

    @property
    def values(self) -> List[Any]:
        """Returns the values of the `TiaItemModel`.

        Returns by default the same as `__values__`.

        Returns:
            List[Any]: List containing the values of the item.
        """
        return self.__values__

    def update(self, dictionary: Dict[str, Any]) -> "TiaItemModel":
        """Updates the item with the given `dictionary`.

        Args:
            dictionary (Dict[str, Any]): Dictionary containing update information for
                the item. Keys need to be names of existing attributes of the object
                `self`, `values` need to be valid values fot the attributes.

        Returns:
            TiaItemModel: Updated `self`.

        Raises:
            AttributeError: if `key` is no attribute of `self`.
        """
        for key, value in dictionary.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise (AttributeError(f"{key} is no attribute of {type(self)}."))
        return self

    @classmethod
    def __headers__(cls) -> List[str]:
        """Headers for a table representing a List of `TiaItemModel` s.

        Used by `TypedList`.

        Returns:
            List[str]: Headers for table in `TypedList`. Default are the attribute
                names of the `TiaItemModel`.
        """
        return ["ID"] + [key for key in cls.__annotations__.keys()]


class TypedList(TiaGenericModel, Generic[ItemType], MutableSequence[ItemType]):
    """GenericModel representing a typechecked list.

    Args:
        items (List[ItemType]): The items of the list.
        _tablefmt (str): Format of the table in string representation.
    """

    items: List[ItemType] = []
    _tablefmt: str = "fancy_grid"

    @pydantic.validator("items", pre=True)
    @classmethod
    def make_list(cls, v: Union[ItemType, List[ItemType]]) -> List[ItemType]:
        """Makes `items` a list, items is no list.

        Args:
            v (Union[ItemType, List[ItemType]]): `self.items`.

        Returns:
            List[ItemType]: `self.items` as a list.
        """
        if not isinstance(v, list):
            v = [v]
        return v

    def __iter__(self) -> Iterator[ItemType]:  # type: ignore[override]
        """Iterator for `TypedList`.

        Iterates through `self.items`.
        """
        return iter(self.items)

    def check(self, v: Any) -> ItemType:
        """Validates `v`.

        Args:
            v (Any): The item to validate.

        Returns:
            ItemType: `v`

        Raises:
            TypeError: if `v` is no instance of `ItemType`.
        """
        # if isinstance(v, dict):
        #     v = self.item_type(**v)
        if not isinstance(v, self.item_type):
            raise (
                TypeError(
                    f"{v}:\nNeeds to be any of type: {self.item_type}"
                    + f" but is of type {type(v)}."
                )
            )
        return v

    def __eq__(self, other: object) -> Any:
        """__eq__ of `TypedList`.

        `TypedList` is equal to another subclass of `list`, if all elements are equal.

        Args:
            other (object): The other list or `TypedList`.

        Returns:
            Any: `NotImplemented` if other is no instance of `list`. If other is
                instance of `list`: `True`, if all elements of the objects are equal,
                else `False`.
        """
        if not isinstance(other, list):
            return NotImplemented
        if len(self) != len(other):
            return False
        return all(
            sum(
                [
                    [
                        self.__getitem__(i) == other.__getitem__(i)
                        for i in range(len(obj))
                    ]
                    for obj in [self, other]
                ],
                [],
            )
        )

    def __len__(self) -> int:
        """The length of the `TypedList`.

        Returns:
            int: The length of `items`.
        """
        return len(self.items)

    def __getitem__(  # type: ignore[override]
        self, idx: Union[int, slice]
    ) -> Union[ItemType, List[ItemType]]:
        """Returns the list item at position `index`.

        Args:
            idx (Union[int, slice]): The index/position of the item
                or slice of the list.

        Returns:
            ItemType: The list item at positions `idx`.
        """
        return self.items[idx]

    def __delitem__(self, idx: Union[int, slice]) -> None:
        """Deletes the item at position `index`.

        Args:
            idx (Union[int, slice]): The index of the item/slice of the list you want to
                delete.
        """
        del self.items[idx]

    def __setitem__(  # type: ignore[override]
        self, index: SupportsIndex, value: ItemType
    ) -> None:
        """Sets the value of listitem at `index` to `value`.

        Args:
            index (SupportsIndex): [description]
            value (ItemType): [description]
        """
        self.check(value)
        self.items[index] = value

    def insert(self, index: int, value: ItemType) -> None:
        """Inserts the item `value` at position `index`.

        Args:
            index (int): The index to insert at.
            value (ItemType): The value to insert.
        """
        self.check(value)
        self.items.insert(index, value)

    @property
    def item_type(self) -> Type[ItemType]:
        """The allowed type for list items.

        Returns:
            ItemType: The allowed type for list items.
        """
        # try:
        return self.__annotations__["items"].__args__[0]  # type: ignore
        # except KeyError:
        #     return self.__orig_bases__[0].__annotations__["items"].__args__[0]

    @property
    def dataframe(self) -> Union[List[ItemType], List[List[Any]]]:
        """Returns of dataframe for the `TypedList`.

        Entries are determined by `__values__` of the allowed itemtype.

        Returns:
            List[List[Any]]: Dataframe for the `TypedList`.
        """
        try:
            return [[value for value in item.__values__] for item in self.items]  # type: ignore # noqa: B950
        except AttributeError:
            return self.items

    @property
    def headers(self) -> List[str]:
        """Headers for displaying the `TypedList` in a table.

        Headers are determined by `__headers__` of the allowed itemtype.

        Returns:
            List[str]: Headers for a table displaying the class.
        """
        try:
            return self.item_type.__headers__()  # type: ignore
        except AttributeError:
            return []

    @property
    def table(self) -> Union[str, List[List[str]]]:
        """Table representation of the `TypedList`.

        Requires `__format_values__` of `item_type`.

        Returns:
            List[List[Any]]: Table representation of the class.
        """
        if len(self.items) == 0:
            return []
        try:
            return [self.headers] + [item.__values_str__ for item in self.items]  # type: ignore[attr-defined] # noqa: B950
        except AttributeError:
            return str(self.items)

    def __str__(self) -> str:
        """String representation of `TypedList`.

        If item

        Returns:
            str: String representation.
        """
        if len(self.items) == 0:
            return f"{[]}"
        elif self.table == str(self.items):
            return str(self.items)
        else:
            return str(
                tabulate(
                    self.table,
                    headers="firstrow",
                    showindex=range(1, len(self.table)),
                    tablefmt=self._tablefmt,
                )
            )


class TiaConfigBaseModel(BaseModel, ABC):
    """The BaseModel for Configurations/Profiles.

    Subclasses of `ConfigBaseModel` are: InvoiceConfiguration,
    TiaProfile and BalanceSheetsConfiguration.

    Args:
        language (str): The language of the configuration. It must be one a
        supported one.
    """

    language: str = "english"

    @pydantic.validator("language", always=True)
    @classmethod
    def valid_language(cls, v: str) -> str:
        """Checks if `language` is a supported one.

        Args:
            v (str): The language.

        Returns:
            str: The language, if it is supported.

        Raises:
            ValueError: If language is not supported.
        """
        if v not in SUPPORTED_LANGUAGES:
            raise (ValueError(f"Language '{v}' is not supported."))
        return v

    class Config(TiaBaseConfig):
        """The Config of `ConfigBaseModel`."""


class CompanyAndClientABCBaseModel(BaseModel, ABC):
    """The BaseModel for Company and Client.

    Args:
        name (str): The name of the client/company.
        street (str): The street-address of the client/company.
        plz (str): The postcode of the client's/company's location.
        city (str): The city in which the client/company is located.
        country (str): The country in which the client/company sits.
        email (str): The email-address for the client/company.
    """

    name: str
    street: str
    plz: str
    city: str
    country: str
    email: str

    class Config:
        """Configuration for CompanyAndClientABCBaseModel."""

        validate_assignment = True
        extra = "forbid"
        allow_population_by_field_name = True


class TiaSheetModel(TypedList[ItemTType], Generic[ItemTType]):
    """Dataclass for the balance sheet/invoice."""

    @property
    def subtotal(self) -> float:
        """The subtotal of the balance sheet/invoice.

        Setter is not defined.

        Returns:
            float: The subtotal of the balance sheet/invoice (revenue + expenditures)
        """
        return sum(item.subtotal for item in self.items)

    @property
    def tax(self) -> float:
        """The tax of the balance sheet/invoice.

        Setter is not defined.

        Returns:
            float: The tax (revenue + expenditures)
        """
        return sum(item.subtotal * item.vat / 100 for item in self.items)

    @property
    def total(self) -> float:
        """The total of the balance sheet/invoice.

        Setter is not defined.

        Returns:
            float: The total (revenue + expenditures)
        """
        return self.subtotal + self.tax

    # @pydantic.validator("items", check_fields=False)
    # @classmethod
    # def make_items_a_list(
    #     cls, v: Optional[Union[ItemTType, List[ItemTType]]]
    # ) -> List[ItemTType]:
    #     """Makes items a list, if not isinstance(items, ItemTType).

    #     Args:
    #         v (Optional[Union[ItemTType, List[ItemTType]]]): The items

    #     Returns:
    #         List[ItemTType]: `items` if isinstance(items, ItemTTypes),
    #             `[items]` else.
    #     """
    #     return v if isinstance(v, list) else [] if v is None else [v]

    def add_item(self, item: ItemTType) -> None:
        """Adds an item to the balance sheets.

        Raises ValidationError, if `item` is no instance of
        `ItemTType`.

        Args:
            item (ItemTType): The item to add to the sheet.
        """
        self.append(item)

    def edit_item(
        self,
        old_item: ItemTType,
        new_item: Union[Dict[str, Union[str, float, datetime.date]], ItemTType],
    ) -> None:
        """Adds an item to the balance sheet/invoice.

        Args:
            old_item (ItemTType): The item we want to edit.
            new_item (Union[Dict[str, Union[str, float, datetime.date]], ItemTType]): Is
                either a dictionary containing new values for for updating `old_item`,
                or a "TiaModelItem" that replaces the old item.

        Raises:
            ValueError: if `new_item` is no dict or of type `ItemTType`.
        """
        index = self.items.index(old_item)
        if isinstance(new_item, self.item_type):
            self.items[index] = self.check(new_item)
        elif isinstance(new_item, dict):
            self.check(self.items[index].update(new_item))
        else:  # pragma: no cover
            raise (
                ValueError(
                    f"{new_item} needs to be a dict or a(n) {self.item_type.__name__}."
                )
            )

    def delete_item(self, item: ItemTType) -> None:
        """Deletes an item.

        Deletes the given item, if it is one of `self.items`.

        Args:
            item (ItemTType): The item to be deleted.
        """
        self.remove(item)
