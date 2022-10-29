#!/usr/bin/python3


__all__ = ["Recipe"]

from dataclasses import dataclass, field
from typing import ClassVar, TypeVar

from inventory import Inventory
from item import Item
from item_stack import ItemStack
from utility.ireprable import IReprable
from utility.iserializable import ISerializable


@dataclass(unsafe_hash=True, order=True)
class Recipe(ISerializable, IReprable):
    """
    A mapping of ItemStack inputs to outputs
    """

    input_item_stacks: "Inventory"  # Inputs
    output_item_stacks: "Inventory"  # Outputs
    enabled: bool = field(default=True, hash=False, compare=False)  # Active?
    priority: int = field(default=0, hash=False)  # Priority

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
        input_list = map(lambda s: ItemStack.from_string(s.strip()), input_strings)
        output_list = map(lambda s: ItemStack.from_string(s.strip()), output_strings)
        # Populate inventories
        inputs = Inventory()
        outputs = Inventory()
        for i in input_list:
            inputs.add_item_stack(i)
        for o in output_list:
            outputs.add_item_stack(o)
        #
        return cls(inputs, outputs)

    def to_string(self) -> str:
        """
        Serializes Recipe to string
        :return: String
        """
        inputs = " + ".join(item_stack.to_string() for item_stack in self.input_item_stacks)
        outputs = " + ".join(item_stack.to_string() for item_stack in self.output_item_stacks)
        return f"{inputs} -> {outputs}"

    def fancy_string(self) -> str:
        inputs = " + ".join(item_stack.fancy_string() for item_stack in self.input_item_stacks)
        outputs = " + ".join(item_stack.fancy_string() for item_stack in self.output_item_stacks)
        return f"{inputs} -> {outputs}"

    def set_priority(self, priority: int) -> "Recipe":
        """
        Sets recipe priority
        :param priority: New Priority
        :return: self
        """
        self.priority = priority
        return self

    def get_output_stack(self, item: Item) -> ItemStack:
        """
        Gets the output ItemStack corresponding to item
        :param item: Item to search
        :return: ItemStack
        """
        return self.output_item_stacks[item]


def main():
    pass


if __name__ == "__main__":
    main()
