#!/usr/bin/python3


__all__ = ["ItemStack"]

import math
import re
from dataclasses import dataclass, field
from typing import ClassVar, Optional, TypeVar

from item import Item
from utility.ireprable import IReprable
from utility.iserializable import ISerializable


@dataclass(unsafe_hash=True, order=True)
class ItemStack(ISerializable, IReprable):
    """
    A group of inputs of a given type with cardinality and an associated
    percentage
    """

    item: Item  # The item
    amount: int = field(default=1, hash=False, compare=False)  # Item amount
    chance: float = field(default=1.0, hash=False, compare=False)  # Item chance
    consumed: bool = field(default=True, hash=False, compare=False)  # If it's consumed

    regex: ClassVar[str] = r"(<[a-zA-Z]\w*:?[\d*]*>):?(\d*)?:?(\d*\.\d*)?"

    def __mul__(self, factor: int) -> "ItemStack":
        return ItemStack(self.item, self.amount * factor, self.chance)

    T: ClassVar[TypeVar] = TypeVar("T", bound="ItemStack")

    @classmethod
    def from_string(cls: T, item_stack_string: str) -> Optional[T]:
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
        if not matches:
            return None
        # print(item_stack_string, cls.regex, matches)
        item_name, amount_string, chance_string = matches.groups()
        # Correct improper values
        if not amount_string:
            amount_string = "1"
        if not chance_string:
            chance_string = "1.0"
        # Convert values
        item: Item = Item.from_string(item_name)
        amount: int = int(amount_string)
        chance: float = float(chance_string)
        return cls(item, amount, chance)

    def to_string(self) -> str:
        """
        Serializes ItemStack to string
        :return: Serialization
        """
        return f"{self.item.to_string()}:{self.amount}:{self.chance}"

    @property
    def effective_amount(self) -> float:
        """
        Get average yield
        :return: Average yield
        """
        return self.amount * self.chance

    @property
    def conservative_amount(self) -> int:
        """
        Get average yield rounded down
        :return: ^
        """
        return math.floor(self.effective_amount)

    @property
    def liberal_amount(self) -> int:
        """
        Get average yield rounded up
        :return: ^
        """
        return math.ceil(self.effective_amount)

    def is_superstack(self, other: "ItemStack") -> bool:
        """
        Checks if this stack is of the same type and has as much or more
        inputs than the factor stack.
        e.g. 32 Iron Ingots is a superstack of 8 Iron Ingots
        :param other: stack to check
        :return: If it's a superstack
        """
        if self.item != other.item:
            return False
        return self.amount >= other.amount

    def fancy_string(self) -> str:
        """
        Returns a nicely-formatted string representation of the stack
        :return: ^
        """
        amt_str: str = f"{self.amount}x " if self.amount > 1 else ""
        percent_str: str
        if self.chance <= 0:
            percent_str = f" (Not Consumed)"
        else:
            percent_str = f" ({self.chance * 100:.2f}%)" if self.chance != 1.0 else ""
        return f"{amt_str}{self.item.fancy_string()}{percent_str}"


def main():
    pass


if __name__ == "__main__":
    main()
