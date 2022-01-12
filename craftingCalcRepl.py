#!/usr/bin/python3
import sys

import craftingCalc
import repl


class IncorrectArgumentException(craftingCalc.CraftingCalcException):
    pass


class AddRecipeCommand(repl.Command):

    @staticmethod
    def action(rpl: "RecipeRepl", *_, **__):
        recipe = craftingCalc.Recipe([], [])
        for e, i in enumerate(_):
            ingredient = RecipeRepl.parse_ingredient(i)
            recipe.add_output(ingredient)
            ingredient.component.set_recipe(recipe)
        try:
            rpl.println("Please enter ingredients, or press Ctrl+C or type :exit to exit")
            while True:
                r = rpl.prompt("\t> ")
                if r == ":exit":
                    break
                ing = RecipeRepl.parse_ingredient(r)
                recipe.add_input(ing)
        except KeyboardInterrupt:
            rpl.println("")
        finally:
            rpl.recipeBook.add_recipe(recipe)

    keyword = "add"
    help_msg = """Usage: add [*{outputName:amount}]
    Adds a recipe with given outputs and inputs prescribed by the user through dialogue.
    """


class ListRecipeCommand(repl.Command):

    @staticmethod
    def action(rpl, *_, **__):
        if len(_) > 0:
            r = set()
            for item in _:
                item = craftingCalc.Component(item)
                for recipe in rpl.recipeBook:
                    if item in recipe.inputs or item in recipe.outputs:
                        r.add(recipe)
            for recipe in r:
                rpl.println(recipe)
        else:
            for recipe in rpl.recipeBook:
                rpl.println(recipe)

    keyword = "list"
    help_msg = """Usage: list [*items/fluids]
    Lists the recipes stored, or lists all recipes involving the items/fluids.
    """


class SaveCommand(repl.Command):

    @staticmethod
    def action(rpl, *_, **__):
        if len(_) <= 0:
            raise IncorrectArgumentException("Missing argument 'fileName'")
        else:
            fileName = _[0]
            rpl.recipeBook.dump_to_file(fileName)
            rpl.println(f"Successfully saved to '{fileName}'")

    keyword = "save"
    help_msg = """Usage: save fileName
    Saves the recipes to a file.
    """


class TreeCommand(repl.Command):

    @staticmethod
    def action(rpl, *_, **__):
        if len(_) <= 0:
            raise IncorrectArgumentException("Missing argument item/fluid")
        ingredient = RecipeRepl.parse_ingredient(_[0])
        tree = ingredient.get_tree()
        TreeCommand.display_tree(rpl, tree)

    @staticmethod
    def display_tree(rpl, tree: dict, depth=0):
        o = tree["output"]
        rpl.println(f"{'  '*depth}|-- {o}")
        for i in tree["inputs"]:
            TreeCommand.display_tree(rpl, i, depth+1)

    keyword = "tree"
    help_msg = """Usage: tree item/fluid
    Prints the crafting tree of the item.
    """


class CostCommand(repl.Command):

    @staticmethod
    def action(rpl, *_, **__):
        if len(_) <= 0:
            raise IncorrectArgumentException("Missing argument item/fluid")
        ingredient = RecipeRepl.parse_ingredient(_[0])
        cost = ingredient.recipe.cost(ingredient)
        for itemName in sorted(cost.keys()):
            rpl.println(f"{cost[itemName]}")

    keyword = "cost"
    help_msg = """Usage: cost item/fluid
    Displays the net cost of a craft in terms of base components"""


class ItemsCommand(repl.Command):

    @staticmethod
    def action(rpl, *_, **__):
        reg = craftingCalc.Component.COMPONENT_REGISTRY
        for item in sorted(reg.keys()):
            print(reg[item].recipe)

    keyword = "__items"
    help_msg = """"""


class RecipeRepl(repl.Repl):
    RECIPE_COMMANDS = [AddRecipeCommand, ListRecipeCommand, SaveCommand, TreeCommand, ItemsCommand, CostCommand]

    def __init__(self, fileName=None, old=False):
        super().__init__()
        if old:
            self.recipeBook = craftingCalc.RecipeBook()
            self.recipeBook.load_from_file_old(fileName)
        else:
            self.recipeBook = craftingCalc.RecipeBook(fileName)
        self.load_recipe_commands()
        self.println("The default format for an ingredient is [ITEM/FLUIDNAME]:AMOUNT")
        self.println("Use liters for fluids.")
        self.println("Enter help for help or exit for exit.")

    @staticmethod
    def parse_ingredient(ingredient: str) -> craftingCalc.Ingredient:
        split = ingredient.split(":")
        if len(split) <= 1:
            amount = 1
        else:
            amount = int(split.pop())
        itemName = split.pop(0)
        return craftingCalc.Ingredient(craftingCalc.Component(itemName), amount)

    def on_exit(self):
        if self.recipeBook.dirty:
            self.unsaved_changes_dialog()
        super().on_exit()

    def load_recipe_commands(self):
        for command in RecipeRepl.RECIPE_COMMANDS:
            self.commands[command.keyword] = command

    def unsaved_changes_dialog(self):
        self.println("\nYou have unsaved changed, would you like to save them? [y/n]")
        answer = self.prompt().lower()
        if answer == "y":
            self.save_dialog()
        self.println("")

    def save_dialog(self):
        fileName = self.prompt("Please enter a file to save to: ")
        try:
            self.recipeBook.dump_to_file(fileName)
        except Exception as e:
            self.printerr(e)
        else:
            self.println("File successfully saved")


def main():
    old = "-o" in sys.argv
    if len(sys.argv) > 1:
        rpl = RecipeRepl(sys.argv[1], old=old)
    else:
        rpl = RecipeRepl(old=old)
    rpl.repl()


if __name__ == "__main__":
    main()
    