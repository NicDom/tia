"""Tests basemodels."""
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from datetime import date

import pytest
from babel.dates import format_date  # type: ignore

# from faker import Faker  # type: ignore
from pydantic import ValidationError

from tia.basemodels import TiaBaseModel
from tia.basemodels import TiaConfigBaseModel
from tia.basemodels import TiaItemModel
from tia.basemodels import TypedList
from tia.utils import file2class


class Person(TiaItemModel):
    """Example class."""

    first_name: str
    last_name: str
    salary: float
    date_of_birth: date
    currency: str = "€"
    sibling: Optional["Person"] = None

    @property
    def subtotal(self) -> float:
        """The parent subtotal."""
        return self.salary

    @property
    def total(self) -> float:
        """The  parent total."""
        return super().total

    @property
    def tax(self) -> float:
        """The parent tax."""
        return super().tax


Person.update_forward_refs()


def test_tia_item_model(some_person: Dict[str, Any]) -> None:
    """It has dunder methods relevant for TypedList."""
    person = Person(**some_person)
    attr_names = [key for key in person.dict()]
    attr_names.remove("vat")
    assert Person.__headers__() == ["ID"] + attr_names
    assert person.__values__ == person.values
    assert person.__values__ == [value for value in person.dict().values()]
    actual = person._format_value(person.date_of_birth)
    expected = format_date(person.date_of_birth, format="short", locale="en")
    assert actual == expected
    actual = person._format_value(person.salary)
    expected = str(person.salary) + person.currency
    assert actual == expected
    assert person.__values_str__ == [
        person._format_value(value) for value in person.__values__
    ]
    assert person.subtotal == 1000
    assert person.tax == 190
    assert person.total == 1190
    person.update({"first_name": "updated"})
    assert person.first_name == "updated"
    with pytest.raises(AttributeError):
        person.update({"no_attr": "value"})


def test_typed_list_init(
    faker: Any, some_person: Dict[str, Any], second_person: Dict[str, Any]
) -> None:
    """It uses the right type for typechecks and behaves like a `list`."""
    person = Person(**some_person)
    city = TypedList[Person](items=person)
    other_person = Person(**second_person)
    city.append(other_person)
    assert city.item_type == Person
    assert person in city
    assert TypedList[int]().item_type == int
    assert len(city) == 2
    city.remove(person)
    assert person not in city
    city[0] = person
    assert city[0] == person
    assert other_person not in city
    assert city.__eq__(person) == NotImplemented


def test_typed_list_type_check(some_person: Dict[str, Any]) -> None:
    """It checks the type before assignment, inserting, etc.

    Args:
        some_person (Person): Some `Person`.
    """
    person = Person(**some_person)
    with pytest.raises(ValidationError):
        TypedList[Person](items=1)
    with pytest.raises(ValidationError):
        TypedList[Person](items=[1])
    city = TypedList[Person](items=person)
    with pytest.raises(TypeError) as excinfo:
        city.append(1)  # type: ignore[arg-type]
    assert str(Person) in str(excinfo) and str(int) in str(excinfo)


def test_typed_list_equal(some_person: Dict[str, Any]) -> None:
    """It can be compared to `list`."""
    person = Person(**some_person)
    assert TypedList[Person](items=some_person) == [person]
    assert TypedList[Person](items=some_person) != [some_person, some_person]
    assert TypedList[Person](items=some_person) != [1]


def test_typed_list_properties(
    faker: Any, some_person: Dict[str, Any], second_person: Dict[str, Any]
) -> None:
    """It has dataframe and table properties."""
    person = Person(**some_person)
    city = TypedList[Person](items=person)
    other_person = Person(**second_person)
    city.append(other_person)
    assert city.dataframe == [item.values for item in city]
    assert city.headers == Person.__headers__()
    assert city.table == [city.headers] + [item.__values_str__ for item in city.items]
    int_list = TypedList[int](items=[1, 2, 3])
    assert int_list.dataframe == int_list.items
    assert int_list.table == str(int_list.items)


def test_typed_list_inheritance(some_person: Dict[str, Any]) -> None:
    """Inheritance from `TypedList` does not break type check."""
    person = Person(**some_person)

    class PersonList(TypedList[Person]):
        """A list of persons."""

    assert PersonList().item_type == Person

    class InfoPersonList(TypedList[Person]):
        """A list of persons."""

        home_town: str = ""
        # when inheriting with further arguments, we have to implement `items` manually
        items: List[Person] = []

    person_list = InfoPersonList()
    assert person_list.item_type == Person
    person_list.append(person)
    assert person in person_list
    assert len(person_list) == 1
    person_list.remove(person)
    assert person not in person_list


def test_typed_list_str(some_person: Dict[str, Any]) -> None:
    """String representation is different, if items are `TiaItemModel`.

    Args:
        some_person (Person): Some `Person`.
    """
    person = Person(**some_person)
    int_list = TypedList[int](items=[1, 2, 3])
    city = TypedList[Person]()
    assert str(int_list) == str(int_list.items)
    assert str(city) == str([])
    assert city.table == []
    city.append(person)
    assert all([person._format_value(value) in str(city) for value in person.values])


def test_tiaconfigbasemodel() -> None:
    """Raises when `language` is not supported."""

    class SomeConfig(TiaConfigBaseModel):
        """Some config."""

    some_config = SomeConfig(language="english")
    assert some_config.language == "english"
    with pytest.raises(ValidationError) as excinfo:
        some_config.language = "invalid"
    assert "Language 'invalid' is not supported." in str(excinfo)


def test_typed_list_json(fake_filesystem: Any, some_person: Dict[str, Any]) -> None:
    """It can be saved as json and loaded from json.

    Args:
        some_person (Person): Some `Person`.
        fake_filesystem (Any): `pyfakefs.fake_filesystem.FakeFilesystem()`.
    """
    person = Person(**some_person)

    class City(TypedList[Person]):
        """A list of persons."""

        name: str = "CityTown"
        items: List[Person] = [person, person]

    class Country(TiaBaseModel):
        cities: City = City()

    # some_path = pathlib.Path("some/")
    country = Country()
    with open("some.json", "w") as f:
        f.write(country.json())
    with open("some.json", "r") as f:
        expected = Country.parse_raw(f.read())
    print(country.json())
    print(expected)
    assert expected == country
    assert country == file2class(Country, "some.json")
    assert country == Country.from_file("some.json")
