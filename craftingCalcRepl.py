import craftingCalc
import repl


class RecipeRepl(repl.Repl):
    RECIPE_COMMANDS = []

    def __init__(self, fileName=None):
        super().__init__()
        self.recipeBook = craftingCalc.RecipeBook(fileName)
        self.load_recipe_commands()

    def on_keyboard_interrupt(self):
        if self.recipeBook.dirty:
            self.unsaved_changes_dialog()
        super().on_keyboard_interrupt()

    def load_recipe_commands(self):
        pass

    def unsaved_changes_dialog(self):
        self.println("You have unsaved changed, would you like to save them? [y/n]")
        answer = self.prompt().lower()
        if answer == "y":
            self.save_dialog()
        else:
            return

    def save_dialog(self):
        pass

    