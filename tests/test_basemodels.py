"""Tests basemodels."""
from typing import Any
from typing import List

import pytest
from faker import Faker  # type: ignore
from pydantic import ValidationError

from tia.basemodels import TiaBaseModel
from tia.basemodels import TiaConfigBaseModel
from tia.basemodels import TiaItemModel
from tia.basemodels import TypedList


class Person(TiaItemModel):
    """Example class."""

    first_name: str
    last_name: str


def test_tia_item_model(some_person: Person) -> None:
    """It has dunder methods relevant for TypedList."""
    assert Person.__headers__() == ["ID", "first_name", "last_name"]
    assert some_person.__values__ == some_person.values
    assert some_person.__values__ == [value for value in some_person.dict().values()]
    assert Person.__format_values__(some_person) == some_person.__values__


def test_typed_list_init(faker: Faker, some_person: Person) -> None:
    """It uses the right type for typechecks and behaves like a `list`."""
    person = some_person
    city = TypedList[Person](items=person)
    other_person = Person(first_name=faker.first_name(), last_name=faker.last_name())
    city.append(other_person)
    assert city.item_type == Person
    assert person in city
    assert TypedList[int]().item_type == int  # type: ignore[type-var]
    assert len(city) == 2
    city.remove(person)
    assert person not in city
    city[0] = person
    assert city[0] == person
    assert other_person not in city
    assert city.__eq__(person) == NotImplemented


def test_typed_list_type_check(some_person: Person) -> None:
    """It checks the type before assignment, inserting, etc.

    Args:
        some_person (Person): Some `Person`.
    """
    person = some_person
    with pytest.raises(ValidationError):
        TypedList[Person](items=1)
    with pytest.raises(ValidationError):
        TypedList[Person](items=[1])
    city = TypedList[Person](items=person)
    with pytest.raises(TypeError) as excinfo:
        city.append(1)  # type: ignore[arg-type]
    assert str(Person) in str(excinfo) and str(int) in str(excinfo)


def test_typed_list_equal(some_person: Person) -> None:
    """It can be compared to `list`."""
    assert TypedList[Person](items=some_person) == [some_person]
    assert TypedList[Person](items=some_person) != [some_person, some_person]
    assert TypedList[Person](items=some_person) != [1]


def test_typed_list_properties(faker: Faker, some_person: Person) -> None:
    """It has dataframe and table properties."""
    person = some_person
    city = TypedList[Person](items=person)
    other_person = Person(first_name=faker.first_name(), last_name=faker.last_name())
    city.append(other_person)
    assert city.dataframe == [item.values for item in city]
    assert city.headers == Person.__headers__()
    assert city.table == [city.headers] + list(
        map(city.item_type.__format_values__, city.items)
    )
    int_list = TypedList[int](items=[1, 2, 3])  # type: ignore[type-var]
    assert int_list.dataframe == int_list.items
    assert int_list.table == str(int_list.items)


def test_typed_list_inheritance(some_person: Person) -> None:
    """Inheritance from `TypedList` does not break type check."""

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
    person_list.append(some_person)
    assert some_person in person_list
    assert len(person_list) == 1
    person_list.remove(some_person)
    assert some_person not in person_list


def test_typed_list_str(some_person: Person) -> None:
    """String representation is different, if items are `TiaItemModel`.

    Args:
        some_person (Person): Some `Person`.
    """
    int_list = TypedList[int](items=[1, 2, 3])  # type: ignore[type-var]
    city = TypedList[Person]()
    assert str(int_list) == str(int_list.items)
    assert str(city) == str([])
    city.append(some_person)
    assert all([value in str(city) for value in some_person.values])


def test_tiaconfigbasemodel() -> None:
    """Raises when `language` is not supported."""

    class SomeConfig(TiaConfigBaseModel):
        """Some config."""

    some_config = SomeConfig(language="english")
    assert some_config.language == "english"
    with pytest.raises(ValidationError) as excinfo:
        some_config.language = "invalid"
    assert "Language 'invalid' is not supported." in str(excinfo)


def test_typed_list_json(fake_filesystem: Any, some_person: Person) -> None:
    """It can be saved as json and loaded from json.

    Args:
        some_person (Person): Some `Person`.
        fake_filesystem (Any): `pyfakefs.fake_filesystem.FakeFilesystem()`.
    """

    class City(TypedList[Person]):
        """A list of persons."""

        name: str = "CityTown"
        items: List[Person] = [some_person, some_person]

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
    assert country == Country.parse_file("some.json")
