#!/usr/bin/python3.11


"""
crafting_calculator.py
Charles Johnson (johnch18@isu.edu)
10/27/2022
"""

__all__ = []

from inventory import Inventory
from recipe import Recipe
from recipe_mapper import RecipeMapper


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
