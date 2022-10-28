#!/usr/bin/python3


__all__ = ["Inventory"]

from typing import Iterator, Type

from item import Item
from item_stack import ItemStack
from utility.iserializable import ISerializable


class Inventory(ISerializable, dict[Item, ItemStack]):
    """
    Stores a collection of stacks
    """

    def __hash__(self) -> int:
        result: int = 0
        for item_stack in self:
            result = 31 * result + hash(item_stack)
        return result

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(repr(i) for i in self)})"

    def __str__(self) -> str:
        return f"{{{', '.join(str(i) for i in self)}}}"

    def __iter__(self) -> Iterator[ItemStack]:
        # noinspection PyTypeChecker
        yield from (self[k] for k in sorted(self.keys()))

    def to_string(self) -> str:
        """
        Serializes to string
        :return: The string
        """
        return f"{{{', '.join(i.to_string() for i in self)}}}"

    @classmethod
    def from_string(cls: Type["Inventory"], source: str) -> "Inventory":
        """
        Deserializes from string
        :param source: Source string
        :return: Object
        """
        result = Inventory()
        i_stack_strings = (s.strip() for s in source.split(","))
        for s in i_stack_strings:
            result.add_item_stack(ItemStack.from_string(s))
        return result

    def add_item_stack(self, i_stack: ItemStack) -> int:
        """
        Adds an item stack to inventory
        :param i_stack: Stack to add
        :return: Amount added
        """
        if i_stack.amount <= 0:
            return 0
        if self.contains(i_stack):
            self.get_stack(i_stack).amount += i_stack.amount
        else:
            self[i_stack.item] = i_stack
        return i_stack.amount

    def sub_item_stack(self, i_stack: ItemStack) -> int:
        """
        Removes items from an inventory, as many as it can without making it
        go negative
        :param i_stack: Stack to subtract
        :return: Number subtracted
        """
        if not self.contains(i_stack):
            return 0
        target = self.get_stack(i_stack)
        amt = min(target.amount, i_stack.amount)
        target.amount -= amt
        if self[i_stack.item].amount <= 0:
            self.pop(i_stack.item)
        return amt

    def get_stack(self, i_stack: ItemStack) -> ItemStack:
        """
        Gets matching stack
        :param i_stack: search
        :return: cost
        """
        return self[i_stack.item]

    def contains(self, i_stack: ItemStack) -> bool:
        """
        Checks if stack in inventory
        :param i_stack: target
        :return: cost
        """
        return i_stack.item in self


def main():
    pass


if __name__ == "__main__":
    main()
