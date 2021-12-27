#!/usr/bin/python3
import json
import math
import os
from typing import List, Union, Dict, Optional

VERSION = 1.0


class CalcError(Exception):
    pass


class InvalidArithmeticError(CalcError):
    pass


class RecursiveRecipeError(CalcError):
    pass


class RecursionDepthError(CalcError):
    pass


class DuplicateRecipeError(CalcError):
    pass


class Item:
    registry: Dict[str, "Item"] = {}

    def __new__(cls, name: str, recipe: Optional["Recipe"] = None):
        if name in Item.registry:
            if recipe is not None and Item.registry[name].recipe is not None:
                raise DuplicateRecipeError("Attempted to add a recipe for an existing item")
            Item.registry[name].recipe = recipe
            return Item.registry[name]
        else:
            newItem = super(Item, cls).__new__(cls)
            Item.registry[name] = newItem
            return newItem

    def __init__(self, name: str, recipe: Optional["Recipe"] = None):
        self.name = name
        self.recipe = recipe

    def __eq__(self, other: "Item"):
        return self.name == other.name

    def __hash__(self):
        return hash(hash(self.name) + hash(self.recipe))

    def __repr__(self):
        return self.name

    def requires(self, item: "Item"):
        if self.recipe is None:
            return False
        for ing in self.recipe.inputs:
            if ing == item:
                return True
        for ing in self.recipe.inputs:
            i = ing.item
            if i.requires(item):
                return True
        return False

    def repr_tree(self, amt=1, depth=0):
        s = str()
        mult = self.recipe.output.amount * math.ceil(1 / amt)
        s += "  " * depth + "-- " + repr(self.recipe.output * mult) + "\n"
        for inp in self.recipe.inputs:
            if inp.recipe is None:
                s += "  " * (depth + 1) + "-- " + repr(inp) + "\n"
                continue
            i = inp.recipe.output
            s += i.item.repr_tree(amt=i.amount * mult, depth=depth + 1)
        return s


class Ingredient:
    MAX_DEPTH = 1000

    def __init__(self, item: Item, amount: int):
        self.item = item
        self.amount = amount

    def __hash__(self):
        return hash(self.item)

    def __eq__(self, other: "Ingredient"):
        return self.is_same_type_as(other)

    def __repr__(self):
        return f"{self.amount} {repr(self.item)}"

    def __add__(self, other: Union[int, "Ingredient"]) -> "Ingredient":
        if type(other) == int:
            return Ingredient(self.item, self.amount + other)
        if type(other) == Ingredient:
            if self == other:
                return Ingredient(self.item, self.amount + other.amount)
            raise InvalidArithmeticError(f"Attempted to add {self.item} with {other.item}")
        raise InvalidArithmeticError(f"Attempted to add an object of type {type(other)}")

    def __mul__(self, amount: int) -> "Ingredient":
        return Ingredient(self.item, self.amount * amount)

    @property
    def recipe(self):
        return self.item.recipe

    def is_same_type_as(self, other: "Ingredient"):
        return self.item == other.item

    def get_net_cost(self, number=1, depth=0):
        result = dict()
        if depth > Ingredient.MAX_DEPTH:
            raise RecursionDepthError(f"Maximum depth ({Ingredient.MAX_DEPTH} steps) reached")
        if self.recipe is None:
            return {self.item: Ingredient(self.item, 1)}
        for inp in self.recipe.inputs:
            amount = math.ceil(number / inp.amount)
            for item, ingredient in inp.get_net_cost(amount, depth + 1):
                result[item] += ingredient
        return result


class Recipe:
    def __init__(self, output: Ingredient, inputs=None):
        if inputs is None:
            inputs = []
        self.output: Ingredient = output
        self.inputs: List[Ingredient] = list()
        for i in inputs:
            self.add_ingredient(i)

    def __repr__(self):
        return f"{repr(self.output)}" + " <- " + " + ".join(repr(i) for i in self.inputs)

    def add_ingredient(self, ingredient: Ingredient):
        for index, inp in enumerate(self.inputs):
            if inp == ingredient:
                self.inputs[index] += ingredient
        else:
            self.inputs.append(ingredient)

    @classmethod
    def load_from_dict(cls, item, recipeDict):
        outputItem = Item(item)
        amount = recipeDict["amt"]
        result = Recipe(Ingredient(outputItem, amount))
        for ingredient in recipeDict["ing"]:
            i = Item(ingredient["name"])
            ing = Ingredient(i, ingredient["amt"])
            result.add_ingredient(ing)
        return result

    def dump_to_dict(self):
        result = dict()
        result["amt"] = self.output.amount
        ingredients = list()
        for ing in self.inputs:
            d = dict()
            d["name"] = ing.item.name
            d["amt"] = ing.amount
            ingredients.append(d)
        result["ing"] = ingredients
        # print(result)
        return result


class RecipeBook:
    def __init__(self):
        self.items: List[Item] = list()

    def load_from_file(self, fileName: str):
        with open(fileName, "r") as file:
            jsonFile = json.load(file)
            self.load_from_dict(jsonFile)

    def load_from_dict(self, d: dict):
        for item, recipe in d.items():
            r = Recipe.load_from_dict(item, recipe)
            self.items.append(Item(item, r))

    def save_to_file(self, fileName: str):
        with open(fileName, "w") as file:
            recipes = self.save_to_dict()
            json.dump(recipes, file)

    def save_to_dict(self):
        result = dict()
        for item in self.items:
            result[item.name] = item.recipe.dump_to_dict()
        return result


class Repl:
    HELP_MSG = "Valid commands are:\nexit - Kills the shell\nhelp - Lists commands\nadd - Adds Recipe\nremove - " \
               "Deletes Recipe\nsave - Saves Recipes to file\nload - Loads Recipes from file\nlist - Prints all " \
               "recipes\nprint - Prints the recipe for an item\ntree - Prints the Crafting Tree for a recipe"

    def __init__(self):
        self.recipes = RecipeBook()
        self.running = True
        self.prompt_str = ">>>"
        self.saved = False

    def repl(self):
        print(f"Welcome to CraftingCalculator {VERSION}\nType 'help' to see available commands\nPress Ctrl+C or type "
              f"'exit' to exit")
        try:
            while self.running:
                inp = self.prompt()
                self.process_command(inp)
        except KeyboardInterrupt as e:
            pass
        if not self.saved:
            answer = input("\nYou have unsaved changes, would you like to before exiting? [y/n] ").strip().lower()
            if answer == "y":
                self.save_dialogue()
            else:
                pass

    def process_command(self, inp):
        com = inp.strip()
        if com == "":
            return
        if com == "exit":
            self.running = False
        if com == "help":
            print(Repl.HELP_MSG)
        if com == "add":
            self.add_command()
        if com == "list":
            for item in self.recipes.items:
                print(item.recipe)
        if com == "save":
            self.save_dialogue()
        if com == "load":
            self.load_dialogue()
        if com == "remove":
            self.remove_dialogue()
        if com == "print":
            self.print_dialogue()
        if com == "tree":
            self.tree_dialogue()

    def add_command(self):
        print("Enter the name of the item you would like\nto add followed by the amount produced by the "
              "recipe.\nUse liters for fluids, no spaces in the name.")
        item, amount = self.get_ingredient()
        if item is None:
            return
        item = Item(item)
        item = Item(item.name, Recipe(Ingredient(item, amount)))
        print("\nPress Ctrl+C to exit")
        try:
            while True:
                print("Enter the ingredients one at a time in the same format")
                inp, amount = self.get_ingredient()
                if inp is None:
                    continue
                i = Item(inp, None)
                ing = Ingredient(i, amount)
                item.recipe.add_ingredient(ing)
        except KeyboardInterrupt:
            pass
        print()
        self.recipes.items.append(item)
        self.saved = False

    def get_ingredient(self):
        try:
            s = self.prompt().split()
            # print(s)
            itemName, amount = s
            amount = int(amount)
            return itemName, amount
        except ValueError as e:
            # print(e)
            print("Invalid input")
            return None, None
        except CalcError as e:
            # print(e)
            print("Got weird error, contact dev")
            return None, None

    def prompt(self):
        return input(f"{self.prompt_str} ")

    def save_dialogue(self):
        print("Enter a file to save to.")
        fileName = self.prompt()
        self.save(fileName)
        print("Save successful")

    def save(self, fileName):
        self.recipes.save_to_file(fileName)
        self.saved = True

    def load_dialogue(self):
        print("Enter a file to load")
        fileName = self.prompt()
        self.load(fileName)
        print(f"Loaded from {os.path.abspath(fileName)}")

    def load(self, fileName):
        self.recipes.load_from_file(fileName)
        self.saved = False

    def remove_dialogue(self):
        print("Enter the item you wish to delete")
        item = self.prompt()
        if self.remove(item):
            print("Removed recipe")
        else:
            print("No such recipe found.")

    def remove(self, item):
        for index, i in enumerate(self.recipes.items):
            print(i.name, item)
            if i.name == item:
                del self.recipes.items[index].recipe
                print(self.recipes.items)
                self.recipes.items.pop(index)
                print(self.recipes.items)
                break
        else:
            return True
        return False

    def print_dialogue(self):
        print("Enter the desired item to display")
        item = self.prompt()
        for i in self.recipes.items:
            if i.name == item:
                r = i.recipe
                print(i)
                for n in i.recipe.inputs:
                    print(f"-- {n}")
                break
        else:
            print(f"{item} does not have a crafting recipe")

    def tree_dialogue(self):
        print("Enter the desired item to display")
        item = self.prompt()
        for i in self.recipes.items:
            if i.name == item:
                print(i.repr_tree(depth=0))
                break
        else:
            print("No such item has a recipe")


def main():
    repl = Repl()
    repl.repl()


if __name__ == "__main__":
    main()
