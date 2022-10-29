#!/usr/bin/python3


__all__ = ["CraftingTableRecipe"]

from collections import defaultdict
from dataclasses import dataclass, field

from inventory import Inventory
from item import Item
from item_stack import ItemStack
from recipe.recipe import Recipe


@dataclass(unsafe_hash=True, order=True)
class CraftingTableRecipe(Recipe):
    pattern: tuple[str, str, str] = field(default=("___", "___", "___"))
    mirrored: bool = field(default=False)

    def __init__(self, output: ItemStack, pattern: tuple[str, str, str], enabled: bool = True, priority: int = 0, mirrored=False, **codex):
        self.pattern = pattern
        self.mirrored = mirrored
        inputs = CraftingTableRecipe.process_inputs(pattern, codex)
        super().__init__(input_item_stacks=inputs, output_item_stacks=[output], enabled=enabled, priority=priority)

    def repr_pattern(self) -> str:
        """
        Shows the pattern as a string
        :return: ^
        """
        return "\n".join("")

    @classmethod
    def process_inputs(cls, pattern: tuple[str, str, str], codex: dict[str, Item]) -> Inventory:
        """
        Encodes the recipe into an inventory
        :param pattern: The crafting grid pattern
        :param codex: Corresponding
        :return:
        """
        result = defaultdict(lambda: 0)
        # Iterate through pattern, count
        for row in pattern:
            for char in row:
                v = codex.get(char, None)
                if v:
                    result[v] += 1
        # Assemble Inventory
        final = Inventory()
        for item, amount in result.items():
            final.add_item_stack(ItemStack(item, amount))
        return final


def main():
    pass


if __name__ == "__main__":
    main()
