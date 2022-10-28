#!/usr/bin/python3.11


"""
crafting_calculator.py
Charles Johnson (johnch18@isu.edu)
10/27/2022
"""

__all__ = []

import math
import pprint
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import ClassVar, Iterator, Optional, Tuple, Type, TypeVar


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

    def __str__(self) -> str:
        return self.to_string()

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
    proper_name: str = field(default=None, hash=False, compare=False)  # Fancy

    metadata_any: bool = field(default=False, hash=False)

    regex: ClassVar[str] = r"<(\w\w*):?([\d*]*)?>"  # Regex pattern for item

    @property
    def canonical_name(self) -> str:
        """
        Gets human-readable name from name, unless proper_name is set
        :return: Human-readable name
        """
        if self.proper_name is not None:
            return self.proper_name
        return snake_to_canonical(self.name)

    def to_string(self) -> str:
        """
        Serializes to string
        :return: String representation
        """
        return f"<{self.name}:{self.metadata if not self.metadata_any else '*'}>"

    T: ClassVar[TypeVar] = TypeVar("T", bound="Item")

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
        # print(item_string, cls.regex, matches)
        item_name, metadata_string = matches
        # Check metadata
        if not metadata_string:
            metadata_string = "0"
        metadata: int
        if metadata_string == "*":
            metadata = 0
            metadata_any = True
        else:
            metadata = int(metadata_string)
            metadata_any = False
        return cls(item_name, metadata, metadata_any=metadata_any)


@dataclass(unsafe_hash=True, order=True)
class ItemStack(ISerializable):
    """
    A group of items of a given type with cardinality and an associated
    percentage
    """

    item: Item  # The item
    amount: int = field(default=1, hash=False, compare=False)  # Item amount
    chance: float = field(default=1.0, hash=False, compare=False)  # Item chance

    regex: ClassVar[str] = r"(<[a-zA-Z]\w*:?[\d*]*>):?(\d*)?:?(\d*\.\d*)?"

    def __mul__(self, factor: int) -> "ItemStack":
        return ItemStack(self.item, self.amount * factor, self.chance)

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
        items than the factor stack.
        e.g. 32 Iron Ingots is a superstack of 8 Iron Ingots
        :param other: stack to check
        :return: If it's a superstack
        """
        if self.item != other.item:
            return False
        return self.amount >= other.amount

    def fancy_repr(self) -> str:
        """
        Returns a nicely-formatted string representation of the stack
        :return: ^
        """
        amt_str: str = f"{self.amount} x " if self.amount > 1 else ""
        metadata_str: str = f":{self.item.metadata}" if self.item.metadata > 0 else ""
        return f"{amt_str}{self.item.canonical_name}{metadata_str}"


@dataclass(unsafe_hash=True, order=True)
class Recipe(ISerializable):
    """
    A mapping of ItemStack inputs to outputs
    """

    input_item_stacks: "Inventory" # Inputs
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


class RecipeMapper:
    """
    Stores the mappings of Recipes and Items
    """

    def __init__(self):
        # Associates items with recipes that yield them
        self.back_table: defaultdict[Item, set[Recipe]]
        self.back_table = defaultdict(set)
        # Associates items with recipes that require them
        self.forward_table: defaultdict[Item, set[Recipe]]
        self.forward_table = defaultdict(set)
        # Stores recipes outright
        self.recipe_table: set[Recipe] = set()

    def __repr__(self) -> str:
        return repr(self.recipe_table)

    def __str__(self) -> str:
        return str(self.recipe_table)

    def add_recipe(self, recipe: Recipe):
        """
        Adds recipe to table, links it to inputs and outputs
        :param recipe: Recipe to add
        """
        # Link outputs with recipe
        for entry in recipe.output_item_stacks:
            # print(entry, entry.item, recipe, sep=" ==== ")
            self.back_table[entry.item].add(recipe)
        # Link inputs with recipe
        for entry in recipe.input_item_stacks:
            self.forward_table[entry.item].add(recipe)
        # Save Recipe
        # noinspection PyTypeChecker
        self.recipe_table.add(recipe)

    def remove_recipe(self, recipe: Recipe):
        """
        Removes a recipe from the mapping
        :param recipe: Recipe to remove
        """
        # Remove from recipe_table
        self.recipe_table.remove(recipe)
        # Remove from back_table
        for entry in recipe.output_item_stacks:
            self.back_table[entry.item].remove(recipe)
        # Remove from forward_table
        for entry in recipe.input_item_stacks:
            self.forward_table[entry.item].remove(recipe)

    def calculate_cost(self, target: Inventory, cache: Inventory = None) -> Tuple[Inventory, Inventory]:
        """
        Calculates what is needed to craft target_items given initial
        :param target: The items to be crafted
        :param cache: Items provided
        :return: A tuple containing cost and leftover items
        """
        if not cache:
            cache = Inventory()
        cost = Inventory()
        queue: list[ItemStack] = list()
        queue.extend(target.values())
        while queue:
            stack = queue.pop(0)
            item = stack.item
            # Check cache for item
            if item in cache:
                stack.amount -= cache.sub_item_stack(stack)
            # If satisfied, continue
            if stack.amount <= 0:
                continue
            # Check if item has any recipes, if not, add to cost and continue
            if item not in self.back_table.keys():
                cost.add_item_stack(stack)
                continue
            # Get the list of recipes for the item
            recipes: list[Recipe] = sorted(filter(lambda r: r.enabled, self.back_table[item]), key=lambda r: r.priority,
                                           reverse=True)
            max_priority = max(map(lambda r: r.priority, recipes))
            recipes = list(filter(lambda r: r.priority == max_priority, recipes))
            # Ignore if no recipes valid
            if len(recipes) == 0:
                cost.add_item_stack(stack)
                continue
            # Only one recipe found
            elif len(recipes) == 1:
                target_recipe = recipes.pop(0)
                output_stack: ItemStack = target_recipe.get_output_stack(item)
                number_of_crafts = math.ceil(stack.amount / output_stack.effective_amount)
                for i in target_recipe.input_item_stacks:
                    queue.append(i * number_of_crafts)
                for o in target_recipe.output_item_stacks:
                    o *= number_of_crafts
                    if o.item != item:
                        cache.add_item_stack(o)
                    else:
                        excess: int = o.amount - stack.amount
                        if excess > 0:
                            cache.add_item_stack(ItemStack(item, excess))
            # Multiple recipes found
            else:
                # TODO: Handle multiple valid recipes
                raise Exception("Multiple Recipes")
        return cost, cache


def main():
    table = RecipeMapper()
    table.add_recipe(Recipe.from_string("<wood_log> -> <wood_plank>:4"))
    table.add_recipe(Recipe.from_string("<wood_log> -> <wood_plank>:6 + <wood_pulp>:1").set_priority(1))
    table.add_recipe(Recipe.from_string("<wood_plank>:4 -> <crafting_bench>"))
    table.add_recipe(Recipe.from_string("<wood_plank>:2 -> <stick>:4"))
    #
    table.add_recipe(Recipe.from_string("<tiny_nether_star_dust> + <magma_cream> -> <nether_star>"))
    table.add_recipe(Recipe.from_string("<nether_star> -> <tiny_nether_star_dust>:9"))
    #
    cost, leftover = table.calculate_cost(
        Inventory.from_string("<nether_star>:64"),
        Inventory.from_string("<tiny_nether_star_dust>:9")
        )
    print("Cost:")
    for stack in cost:
        print("\t", stack.fancy_repr())
    print("Leftover:")
    for stack in leftover:
        print("\t", stack.fancy_repr())


if __name__ == "__main__":
    main()
