#!/usr/bin/python3

"""
Made by johnch18 on 12/27/21
GPL license bitches, don't be a dick
"""


import json
import math
import os
import sys
from typing import List, Union, Dict, Optional, Tuple

VERSION = 1.0


class CalcError(Exception):
    """
    Base Error Class for this Program
    """
    pass


class InvalidArithmeticError(CalcError):
    """
    Indicates some kind of arithmetic error, such as adding or multiplying incompatible objects
    """
    pass


class RecursiveRecipeError(CalcError):
    """
    Indicates a recipe is recursive. Hopefully will implement a way to calculate them some day.
    """
    pass


class RecursionDepthError(CalcError):
    """
    Indicates that too many steps have been found in the recipe.
    Triggered by 1000 for now, which should cover 99.99% of cases.
    """
    pass


class DuplicateRecipeError(CalcError):
    """
    Indicates that a duplicate recipe has been added. Unsure how to implement multiple recipes per item or if I should
    have a dialogue for this kind of thing.
    TODO: Make dialogue for duplicate recipe
    """
    pass


class Item:
    """
    Stores the name of an item and its recipe. Each item of the same name is a singleton.
    """
    registry: Dict[str, "Item"] = {}  # Stores Item instances

    def __new__(cls, name: str, recipe: Optional["Recipe"] = None) -> "Item":
        """
        Overloads the base __new__ functionality to verify that multiple items aren't being used. Overwrites recipe if
        it hasn't been set, raises an error otherwise.
        :param name: The item name
        :param recipe: The recipe, is typically None
        :return: Returns either an existing instance or creates a new one
        """
        if name in Item.registry:
            if recipe is not None and Item.registry[name].recipe is not None:
                raise DuplicateRecipeError("Attempted to add a recipe for an existing item")
            Item.registry[name].set_recipe(recipe)
            return Item.registry[name]
        else:
            newItem = super(Item, cls).__new__(cls)
            Item.registry[name] = newItem
            return newItem

    def __init__(self, name: str, recipe: Optional["Recipe"] = None):
        """
        Creates an Item with name and recipe.
        :param name: The item name
        :param recipe: The item recipe
        """
        self.name = name
        if not hasattr(self, "recipe"):
            self.recipe = None
        self.set_recipe(recipe)

    def __eq__(self, other: "Item") -> bool:
        """
        Allows comparison of Item instances
        :param other: The other Item object
        :return: Returns whether or not they are the same
        """
        return self.name == other.name

    def __hash__(self):
        """
        Hashes the item based on name and recipe
        :return: A hash
        """
        return hash(hash(self.name) + hash(self.recipe))

    def __repr__(self) -> str:
        """
        Gets a string representation of the Item
        :return: The name
        """
        return repr(self.name)

    def requires(self, item: "Item") -> bool:
        """
        Checks if an item is in the crafting tree of this item
        :param item:
        :return:
        """
        # This should be self-evident
        if item == self:
            return True
        # If it has no recipe this is obviously false
        if self.recipe is None:
            return False
        # Check itself
        for ing in self.recipe.inputs:
            if ing == item:
                return True
        # DFS
        for ing in self.recipe.inputs:
            i = ing.item
            if i.requires(item):
                return True
        return False

    def repr_tree(self, amt=1, depth=0) -> str:
        """
        Returns a string representation of the crafting tree
        TODO: Fix the amount calculations
        :param amt: Number to craft
        :param depth: How many steps the current craft is
        :return: Returns the string repr of the tree
        """
        s = str()
        # Get the number of crafts needed
        numRecipes = math.ceil(amt * (1/self.recipe.output.amount))
        # DEBUG
        # print(self.name, self.recipe.output.amount, amt, self.recipe.output.amount, numRecipes)
        # Print yourself
        s += "  " * depth + "-- " + repr(self.recipe.output * numRecipes) + "\n"
        for inp in self.recipe.inputs:
            # Check if recipe exists
            if inp.recipe is None:
                # If not, just print the item
                s += "  " * (depth + 1) + "-- " + repr(inp * numRecipes) + "\n"
                continue
            else:
                # If it does, print the tree of this item
                i = inp.recipe.output
                s += i.item.repr_tree(amt=numRecipes*i.amount, depth=depth + 1)
        return s

    def set_recipe(self, recipe: Optional["Recipe"]):
        if recipe is not None:
            self.recipe = recipe


class Ingredient:
    """
    Stores an item and how much of it exists
    Use liters for fluids, e.g. 1 bucket of water would be 1000 Water
    """
    MAX_DEPTH = 1000  # Maximum amount of crafting steps allowed

    def __init__(self, item: Item, amount: int):
        """
        Initializes Ingredient
        :param item: The item
        :param amount: The amount of it
        """
        self.item = item
        self.amount = amount

    def __hash__(self):
        """
        Hashes the Ingredient
        :return: The hash
        """
        return hash(self.item)

    def __eq__(self, other: "Ingredient") -> bool:
        """
        Checks equality between two ingredients based on the item
        :param other: The other ingredient
        :return: Whether they're the same
        """
        return self.is_same_type_as(other)

    def __repr__(self) -> str:
        """
        Returns the string representation of the ingredient
        :return: ^
        """
        return f"{self.amount} {repr(self.item)}"

    def __add__(self, other: Union[int, "Ingredient"]) -> "Ingredient":
        """
        Adds two ingredients or an ingredient with an int.
        Raises an error if they're not the same item, can't add apples and oranges.
        :param other: The integer or Ingredient to add
        :return: The resulting ingredient
        """
        if type(other) == int:
            return Ingredient(self.item, self.amount + other)
        if type(other) == Ingredient:
            if self == other:
                return Ingredient(self.item, self.amount + other.amount)
            raise InvalidArithmeticError(f"Attempted to add {self.item} with {other.item}")
        raise InvalidArithmeticError(f"Attempted to add an object of type {type(other)}")

    def __mul__(self, amount: int) -> "Ingredient":
        """
        Multiplies an ingredient's amount by an integer.
        :param amount: The amount to multiply by
        :return: The new ingredient
        """
        return Ingredient(self.item, self.amount * amount)

    @property
    def recipe(self) -> "Recipe":
        """
        :return: The ingredient's recipe
        """
        return self.item.recipe

    def is_same_type_as(self, other: "Ingredient") -> bool:
        """
        :param other: Other ingredient
        :return: Whether or not they are of the same type
        """
        return self.item == other.item

    def get_net_cost(self, number=1, depth=0) -> dict:
        """
        Recursively gathers all ingredients in the recipe
        :param number: Number of items to craft
        :param depth: Number of iterations
        :return: The net crafting cost
        """
        result = dict()
        # Check that we're not too deep
        if depth > Ingredient.MAX_DEPTH:
            raise RecursionDepthError(f"Maximum depth ({Ingredient.MAX_DEPTH} steps) reached")
        # Check if recipe exists, if not return self
        if self.recipe is None:
            return {self.item: Ingredient(self.item, 1)}
        # Iterate through inputs and calculate their costs
        for inp in self.recipe.inputs:
            amount = math.ceil(number / inp.amount)
            # Add costs to self
            for item, ingredient in inp.get_net_cost(amount, depth + 1):
                # No key errors for you
                if item not in result:
                    result[item] = 0
                result[item] += ingredient
        return result


class Recipe:
    """
    Stores an output ingredient and a list of input ingredients
    TODO: Add multiple outputs
    """
    def __init__(self, output: Ingredient, inputs: Optional[List[Ingredient]] = None):
        """
        Initializes Recipe with input and outputs
        :param output: Output ingredient
        :param inputs: Input ingredients
        """
        # Python doesn't like mutable arguments
        if inputs is None:
            inputs = list()
        self.output: Ingredient = output
        self.inputs: List[Ingredient] = list()
        # Use the method to add inputs you beast!
        for i in inputs:
            self.add_ingredient(i)

    def __repr__(self) -> str:
        """
        :return: The string representation of the Recipe
        """
        return f"{repr(self.output)}" + " <- " + " + ".join(repr(i) for i in self.inputs)

    def add_ingredient(self, ingredient: Ingredient):
        """
        Adds an input to the recipe
        :param ingredient: Ingredient to add
        :return: Nada amigo
        """
        # Verify ingredient isn't already present, add if so
        for index, inp in enumerate(self.inputs):
            if inp == ingredient:
                self.inputs[index] += ingredient
                break
        # Append ingredient
        else:
            self.inputs.append(ingredient)

    @classmethod
    def load_from_dict(cls, item, recipeDict) -> "Recipe":
        """
        Reads a recipe from a dictionary
        :param item: The item name
        :param recipeDict: The 'recipe'
        :return: The recipe
        """
        # Create output ingredient
        outputItem = Item(item)
        amount = recipeDict["amt"]
        result = Recipe(Ingredient(outputItem, amount))
        # Add output ingredients
        for ingredient in recipeDict["ing"]:
            i = Item(ingredient["name"])
            ing = Ingredient(i, ingredient["amt"])
            result.add_ingredient(ing)
        return result

    def dump_to_dict(self) -> dict:
        """
        :return: Dict representation of the recipe
        """
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
    """
    Stores a collection of recipes
    """
    def __init__(self):
        """
        C'mon, really?
        """
        self.items: List[Item] = list()

    def load_from_file(self, fileName: str):
        """
        :param fileName:The file to load
        :return:
        """
        with open(fileName, "r") as file:
            jsonFile = json.load(file)
            self.load_from_dict(jsonFile)

    def load_from_dict(self, d: dict):
        """
        :param d: The dictionary to load. You aren't too bright, are ya?
        Sorry. I've been writing docs for like 40 minutes
        :return:
        """
        for item, recipe in d.items():
            r = Recipe.load_from_dict(item, recipe)
            self.items.append(Item(item, r))

    def save_to_file(self, fileName: str):
        """
        Saves recipe book to a file
        :param fileName: The file
        :return:
        """
        with open(fileName, "w") as file:
            recipes = self.save_to_dict()
            json.dump(recipes, file)

    def save_to_dict(self):
        """
        Exports recipe book to a dict
        :return:
        """
        result = dict()
        for item in self.items:
            result[item.name] = item.recipe.dump_to_dict()
        return result


class Repl:
    """
    Shitty REPL implementation to allow testing and basic usage. I hate it. I want it gone. I need to make an actual lib
    for this shit. More than anything I need a GUI but Tkinter gives me cancer
    """
    HELP_MSG = "Valid commands are:\nexit - Kills the shell\nhelp - Lists commands\nadd - Adds Recipe\nremove - " \
               "Deletes Recipe\nsave - Saves Recipes to file\nload - Loads Recipes from file\nlist - Prints all " \
               "recipes\nprint - Prints the recipe for an item\ntree - Prints the Crafting Tree for a Recipe"
    # Just what's printed when you beg the gods for help

    def __init__(self, fileName: Optional[str] = None):
        """
        Just initializes some stuff, nothing fancy
        """
        self.recipes = RecipeBook()
        self.running = True
        self.prompt_str = ">>>"
        self.saved = False
        if fileName is not None:
            self.load(fileName)

    def repl(self):
        """
        Executes the REPL
        :return:
        """
        print(f"Welcome to CraftingCalculator {VERSION}\nType 'help' to see available commands\nPress Ctrl+C or type "
              f"'exit' to exit")
        # Catch KeyboardInterrupts
        try:
            while self.running:
                inp = self.prompt()
                self.process_command(inp)
        except KeyboardInterrupt as _:
            pass
        # Check if recipes have been saved
        if not self.saved:
            answer = input("\nYou have unsaved changes, would you like to before exiting? [y/n] ").strip().lower()
            if answer == "y":
                self.save_dialogue()
            # Maybe do something else? IDK
            else:
                pass

    def process_command(self, inp):
        """
        Runs commands
        :param inp: Input string
        :return:
        """
        # Get rid of WS
        com = inp.strip()
        # Ignore empty strings
        if com == "":
            return
        if com == "exit":
            self.running = False
        if com == "help":
            print(Repl.HELP_MSG)
        if com == "add":
            self.add_dialogue()
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

    def add_dialogue(self):
        """
        The add command, adds a recipe to the book
        :return:
        """
        print("Enter the name of the item you would like\nto add followed by the amount produced by the "
              "recipe.\nUse liters for fluids, no spaces in the name.")
        # Get item and number of it
        item, amount = self.get_ingredient()
        # Ignore if error'd
        if item is None:
            return
        # I hate this shit so much, what a horrible design pattern.
        item = Item(item)
        item = Item(item.name, Recipe(Ingredient(item, amount)))
        print("\nPress Ctrl+C to exit")
        print("\t", self.recipes.items)
        try:
            # Add ingredients from user input
            while True:
                print("Enter the ingredients one at a time in the same format")
                inp, amount = self.get_ingredient()
                if inp is None:
                    continue
                i = Item(inp)
                ing = Ingredient(i, amount)
                item.recipe.add_ingredient(ing)
        # Catch those pesky KeyboardInterrupts
        except KeyboardInterrupt:
            pass
        print()
        self.recipes.items.append(item)
        self.saved = False

    def get_ingredient(self) -> Tuple[Optional[str], Optional[int]]:
        """
        Gets an ingredient from the command line
        :return: The ingredient in string, int form
        """
        try:
            s = self.prompt().split()
            # print(s)
            itemName, amount = s
            amount = int(amount)
            return itemName, amount
        # Ignore errors with unpacking the tuple or getting the int
        except ValueError as _:
            # print(e)
            print("Invalid input")
            return None, None
        # This should never be triggered but idk
        except CalcError as e:
            print(e)
            print("Got weird error, contact dev")
            return None, None

    def prompt(self) -> str:
        """
        Literally just a wrapper for input
        :return: The result
        """
        try:
            return input(f"{self.prompt_str} ")
        except EOFError:
            return ""

    def save_dialogue(self):
        """
        A dialogue to interface with save
        :return:
        """
        print("Enter a file to save to.")
        fileName = self.prompt()
        try:
            self.save(fileName)
            print("Save successful")
        except Exception as e:
            print(e)
            print("Something went wrong")

    def save(self, fileName: str):
        """
        Saves the recipe book
        :param fileName: Where to save it
        :return:
        """
        self.recipes.save_to_file(fileName)
        self.saved = True

    def load_dialogue(self):
        """
        CLI wrapper for load
        :return:
        """
        print("Enter a file to load")
        fileName = self.prompt()
        try:
            self.load(fileName)
            print(f"Loaded from {os.path.abspath(fileName)}")
        except Exception as e:
            print(e)
            print("Something went wrong")

    def load(self, fileName: str):
        """
        Loads a recipe book from a file
        :param fileName: The file to load from
        :return:
        """
        self.recipes.load_from_file(fileName)
        self.saved = False

    def remove_dialogue(self):
        """
        Dialogue for removing a recipe
        :return:
        """
        print("Enter the item you wish to delete")
        item = self.prompt()
        if self.remove(item):
            print("Removed recipe")
        else:
            print("No such recipe found.")

    def remove(self, item: str):
        """
        Removes a recipe from the book
        TODO: Migrate to RecipeBook
        :param item:
        :return:
        """
        # Iterate through recipes until you find it, return True if not
        for index, i in enumerate(self.recipes.items):
            if i.name == item:
                # Delete that shit
                del self.recipes.items[index].recipe
                self.recipes.items.pop(index)
                break
        else:
            return True
        return False

    def print_dialogue(self):
        """
        Prints the recipe of an item
        :return:
        """
        print("Enter the desired item to display")
        item = self.prompt()
        # Print recipe, print an error if nothing is there
        for i in self.recipes.items:
            if i.name == item:
                print(i)
                for n in i.recipe.inputs:
                    print(f"-- {n}")
                break
        else:
            print(f"{item} does not have a crafting recipe")

    def tree_dialogue(self):
        """
        Prints the crafting tree of a recipe
        TODO: Fix arithmetic on this
        :return:
        """
        print("Enter the desired item and amount to display")
        item, amount = self.get_ingredient()
        if item is None:
            print("Invalid item")
            return
        for i in self.recipes.items:
            if i.name == item:
                print(i.repr_tree(amt=amount, depth=0))
                break
        else:
            print("No such item has a recipe")


def main():
    """
    Main method bois
    :return:
    """
    argv = sys.argv
    argc = len(argv)
    if argc > 1:
        repl = Repl(argv[1])
    else:
        repl = Repl()
    repl.repl()


if __name__ == "__main__":
    main()
