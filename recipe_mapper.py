#!/usr/bin/python3


__all__ = ["RecipeMapper"]

import math
from collections import defaultdict

from inventory import Inventory
from item import Item
from item_stack import ItemStack
from recipe import Recipe


class RecipeMapper:
    """
    Stores the mappings of Recipes and Items
    """

    def __init__(self):
        # Associates items with recipes that yield them
        self.back_table: defaultdict[Item, set[Recipe]] = defaultdict(set)
        # Associates items with recipes that require them
        self.forward_table: defaultdict[Item, set[Recipe]] = defaultdict(set)
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

    def calculate_cost(self, target: Inventory, cache: Inventory = None) -> tuple[Inventory, Inventory]:
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
                # Queue up inputs
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
    pass


if __name__ == "__main__":
    main()
