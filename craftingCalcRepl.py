#!/usr/bin/python3
import sys

import craftingCalc
import repl


class AddRecipeCommand(repl.Command):

    @staticmethod
    def action(rpl: "RecipeRepl", *_, **__):
        recipe = craftingCalc.Recipe([], [])
        for e, i in enumerate(_):
            item, amount = i.split(":")
            itemObject = craftingCalc.Component(item)
            ingredient = craftingCalc.Ingredient(itemObject, int(amount))
            recipe.add_output(ingredient)
        try:
            while True:
                r = rpl.prompt("Please enter an ingredient, or press Cntl+C or type 'exit' to exit > ")
                if r == "exit":
                    break
                itemName, amount = r.split(":")
                item = craftingCalc.Component(itemName)
                ing = craftingCalc.Ingredient(item, int(amount))
                recipe.add_input(ing)
        except KeyboardInterrupt:
            pass
        finally:
            rpl.recipeBook.recipes.append(recipe)

    keyword = "add"
    help_msg = """Usage: add [*{outputName:amount}]
    Adds a recipe with given outputs and inputs prescribed by the user through dialogue.
    """


class RecipeRepl(repl.Repl):
    RECIPE_COMMANDS = [AddRecipeCommand]

    def __init__(self, fileName=None):
        super().__init__()
        self.recipeBook = craftingCalc.RecipeBook(fileName)
        self.load_recipe_commands()
        self.println("The default format for an ingredient is [ITEM/FLUIDNAME]:AMOUNT")

    def on_keyboard_interrupt(self):
        if self.recipeBook.dirty:
            self.unsaved_changes_dialog()
        super().on_keyboard_interrupt()

    def load_recipe_commands(self):
        for command in RecipeRepl.RECIPE_COMMANDS:
            self.commands[command.keyword] = command

    def unsaved_changes_dialog(self):
        self.println("You have unsaved changed, would you like to save them? [y/n]")
        answer = self.prompt().lower()
        if answer == "y":
            self.save_dialog()
        else:
            return

    def save_dialog(self):
        fileName = self.prompt("Please enter a file to save to: ")
        try:
            self.recipeBook.dump_to_file(fileName)
        except Exception as e:
            self.printerr(e)
        else:
            self.println("File successfully saved")


def main():
    if len(sys.argv) > 1:
        rpl = RecipeRepl(sys.argv[0])
    else:
        rpl = RecipeRepl()
    rpl.repl()


if __name__ == "__main__":
    main()
    