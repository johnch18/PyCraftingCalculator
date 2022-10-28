#!/usr/bin/python3.11


__all__ = []

import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import ClassVar, TypeVar, Callable, Generic

K = TypeVar("K", bound="KeyCollection")
V = TypeVar("V", bound="KeyCollection")


class KeyCollection(Generic[K, V], dict):
    """
    A collection of type V stored in a hash table calculated with a callable
    type (V) -> K
    """

    def __init__(self, key_func: Callable[[V], K], *args: V):
        super().__init__()
        self.key_func = key_func
        self.add_elements(*args)

    def __repr__(self) -> str:
        el_string = ", ".join(repr(self[key]) for key in sorted(self.keys()))
        return f"{type(self).__name__}({el_string})"

    def add_element(self, elem: V):
        """
        Adds an element to the collection
        :param elem: The element to add
        """
        self[self.key_func(elem)] = elem

    def add_elements(self, *elems: V):
        """
        Adds multiple elements
        :param elems: elements to add
        """
        for e in elems:
            self.add_element(e)

    def contains_element(self, elem: V) -> bool:
        return self.key_func(elem) in self


def snake_to_canonical(snake: str) -> str:
    """
    Converts a snake-case name to a canonical name.
    e.g. 'foo_bar_baz' -> 'Foo Bar Baz'
    :param snake: snake-case name
    :return: Canonical name
    """
    return " ".join(s.capitalize() for s in snake.split("_"))


class ISerializable(ABC):
    """
    Guarantees serializable behavior in strings, JSON, and XML
    """

    @abstractmethod
    def to_string(self) -> str:
        """
        Serializes to a string
        :return:
        """

    T: ClassVar[TypeVar] = TypeVar("T", bound="ISerializable")

    @classmethod
    @abstractmethod
    def from_string(cls: T, source: str) -> T:
        """
        Deserializes from a string
        :param source:  string to use
        :return: Object
        """


@dataclass(unsafe_hash=True, order=True)
class Item(ISerializable):
    """
    An object which has an id, a name, and metadata
    """

    name: str  # name must be snakecase
    metadata: int = 0  # metadata >= 0
    proper_name: str = None  # Overrides canonical_name

    regex: ClassVar[str] = r"<(\w\w*):?(\d*)?>"  # Regex pattern for item

    # strings

    @property
    def canonical_name(self) -> str:
        """
        Gets human-readable name from name, unless proper_name is set
        :return: Human-readable name
        """
        if self.proper_name is not None:
            return self.proper_name
        return snake_to_canonical(self.name)

    T: ClassVar[TypeVar] = TypeVar("T", bound="Item")

    def to_string(self) -> str:
        """
        Serializes to string
        :return: String representation
        """
        return f"<{self.name}:{self.metadata}>"

    @classmethod
    def from_string(cls: T, item_string: str) -> T:
        """
        String factory for Item
        :param item_string: String to parse
        :return: The item
        """
        item_name: str
        metadata_string: str
        # Get match
        matches = re.findall(cls.regex, item_string)[0]
        # matches = re.matchall(cls.regex, item_string)
        item_name, metadata_string = matches
        # Check metadata
        if not metadata_string:
            metadata_string = "0"
        metadata: int = int(metadata_string)
        return cls(item_name, metadata)


@dataclass(unsafe_hash=True, order=True)
class ItemStack(ISerializable):
    """
    A group of items of a given type with cardinality and an associated
    percentage
    """

    item: Item  # The item
    amount: int = 1  # The amount of the item
    chance: float = 1.0  # The odds of the stack being produced/consumed

    regex: ClassVar[str] = r"(<[a-zA-Z]\w*:?\d*>):?(\d*)?:?(\d*\.\d*)?"

    T: ClassVar[TypeVar] = TypeVar("T", bound="ItemStack")

    @classmethod
    def from_string(cls: T, item_stack_string: str) -> T:
        """
        String factory for ItemStack
        :param item_stack_string: string to parse
        :return: ItemStack parsed
        """
        item_name: str
        amount_string: str
        chance_string: str
        # Match using regex
        matches = re.match(cls.regex, item_stack_string)
        item_string, amount_string, chance_string = matches.groups()
        # Correct improper values
        if not amount_string:
            amount_string = "1"
        if not chance_string:
            chance_string = "1.0"
        # Convert values
        item: Item = Item.from_string(item_string)
        amount: int = int(amount_string)
        chance: float = float(chance_string)
        return cls(item, amount, chance)

    def to_string(self) -> str:
        """
        Serializes ItemStack to string
        :return: Serialization
        """
        return f"{self.item.to_string()}:{self.amount}:{self.chance}"


@dataclass(unsafe_hash=True, order=True)
class Recipe(ISerializable):
    """
    A mapping of ItemStack inputs to outputs
    """

    input_item_stacks: KeyCollection[int, ItemStack]
    output_item_stacks: KeyCollection[int, ItemStack]

    T: ClassVar[TypeVar] = TypeVar("T", bound="Recipe")

    @classmethod
    def from_string(cls: T, recipe_string: str) -> T:
        """
        String factory for recipe
        :param recipe_string: The recipe string to parse
        :return: Completed recipe
        """
        input_string: str
        output_string: str
        input_string, output_string = recipe_string.split("->")
        # Get rid of spaces
        input_string = input_string.strip()
        output_string = output_string.strip()
        # Separate out ingredients
        input_strings = input_string.split("+")
        output_strings = output_string.split("+")
        # Convert to ItemStacks
        input_list = map(
            lambda s: ItemStack.from_string(s.strip()),
            input_strings
        )
        output_list = map(
            lambda s: ItemStack.from_string(s.strip()),
            output_strings
        )
        return cls(
            KeyCollection(lambda x: x.__hash__(), *input_list),
            KeyCollection(lambda x: x.__hash__(), *output_list)
        )

    def to_string(self) -> str:
        inputs = " + ".join(item_stack.to_string() for item_stack in
                            self.input_item_stacks.values())
        outputs = " + ".join(item_stack.to_string() for item_stack in
                             self.output_item_stacks.values())
        return f"{inputs} -> {outputs}"


class RecipeTable:
    """
    Stores the mappings of Recipes and Items
    """

    def __init__(self):
        self.table: dict[Item, list[Recipe]] = defaultdict(lambda: list())


def main():
    test: Recipe = Recipe.from_string("<wood_log:0> -> <wood_plank:0>:4:1.0")
    print(test.to_string())


if __name__ == "__main__":
    main()
