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

import inspect
from abc import ABC
from collections.abc import MutableSequence

import orjson
import pydantic
from pydantic import BaseConfig
from pydantic import BaseModel
from pydantic import Extra
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

ItemType = TypeVar("ItemType")


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
    return orjson.dumps(obj, default=default).decode()


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

    class Config(TiaBaseConfig):
        """The Config of `TiaBaseModel`."""


class TiaGenericModel(GenericModel):
    """Baseclass for GenericModels in TIA."""

    class Config(TiaBaseConfig):
        """Config for `TiaGenericModel`.

        Subclass of `TiaBaseConfig`.
        """


class TiaItemModel(TiaBaseModel):
    """Baseclass for items in TIA.

    Subclass of `TiaBaseModel`.
    """

    @classmethod
    def __format_values__(cls, row: "TiaItemModel") -> List[str]:
        """String formatting rule for the individual attributes of the class.

        Used for displaying as part of a TypedList.

        Args:
            row (TiaItemModel): An `TiaItemModel`.

        Returns:
            List[str]: Formatted strings for the several items.
        """
        return [str(entry) if entry != 0 else "" for entry in row.__values__]

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

    def check(self, v: ItemType) -> ItemType:
        """Validates `v`.

        Args:
            v (ItemType): The item to validate.

        Returns:
            ItemType: `v`

        Raises:
            TypeError: if `v` is no instance of `ItemType`.
        """
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
        try:
            return [self.headers] + list(
                map(self.item_type.__format_values__, self.items)  # type: ignore
            )
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
