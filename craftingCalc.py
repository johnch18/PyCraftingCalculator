#!/usr/bin/python3
"""
Second version of PyCraftingCalculator
By johnch18 on 12/30/21
"""


import json
from typing import Dict, Optional, List, Tuple

VERSION = "1.0.0"


class CraftingCalcException(Exception):
    pass


class DuplicateRecipeException(CraftingCalcException):
    pass


class IncompatibleIngredientException(CraftingCalcException):
    pass


class RecursiveRecipeException(CraftingCalcException):
    pass

class CompatibilityException(CraftingCalcException):
    pass


class Component:
    COMPONENT_REGISTRY: Dict[str, "Component"] = dict()

    def __new__(cls, name: str, recipe: Optional["Recipe"] = None):
        if name not in Component.COMPONENT_REGISTRY:
            newComponent = Component(name, recipe)
            Component.COMPONENT_REGISTRY[name] = newComponent
            return newComponent
        else:
            c = Component.COMPONENT_REGISTRY[name]
            if c.recipe is None:
                c.recipe = recipe
            elif recipe is not None:
                raise DuplicateRecipeException(f"Attempted to register second recipe for {name}")
            return c

    def __init__(self, name: str, recipe: Optional["Recipe"] = None):
        self.name = name
        self.recipe = recipe

    def __eq__(self, other: "Component"):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Ingredient:
    def __init__(self, comp: Component, amount: int = 1):
        self.component = comp
        self.amount = amount

    def __add__(self, other: Tuple["Ingredient", int]):
        if isinstance(other, int):
            return Ingredient(self.component, self.amount + other)
        elif isinstance(other, Ingredient):
            if not self.same_type(other):
                raise IncompatibleIngredientException(f"Attempted to combine stacks of type {self.component}"
                                                      "and {other.component}")
            return Ingredient(self.component, self.amount + other.amount)
        else:
            raise IncompatibleIngredientException(f"Attempted to add object of type {type(other)} to Ingredient")

    def __mul__(self, scale: int):
        return Ingredient(self.component, self.amount * scale)

    def same_type(self, other: "Ingredient") -> bool:
        return self.component == other.component

    def is_component(self, comp: Component) -> bool:
        return self.component == comp

    @classmethod
    def load_from_json(cls, d: dict) -> "Ingredient":
        name = d["n"]
        amt = d["a"]
        return Ingredient(Component(name), int(amt))

    def dump_to_json(self) -> dict:
        d = dict()
        d["n"] = self.component.name
        d["a"] = self.amount
        return d


class Recipe:
    def __init__(self, inputs: List[Ingredient], outputs: List[Ingredient]):
        self.inputs = inputs
        self.outputs = outputs
        self.validate()

    def requires(self, comp: Component) -> bool:
        Q = self.inputs[:]
        while len(Q) > 0:
            inp = Q.pop(0)
            print(inp)
            if inp.is_component(comp):
                return True
            Q.extend(inp.component.recipe.inputs)
        return False

    def validate(self):
        for i in self.inputs:
            if i.component.recipe.requires(i.component):
                raise RecursiveRecipeException(f"Recipe for {i} requires {i}")

    def add_input(self, ing: Ingredient):
        for e, i in enumerate(self.inputs):
            if i.same_type(ing):
                self.inputs[e] += ing
                break
        else:
            self.inputs.append(ing)
        self.validate()

    def add_output(self, ing: Ingredient):
        for e, i in enumerate(self.outputs):
            if i.same_type(ing):
                self.outputs[e] += ing
                break
        else:
            self.outputs.append(ing)
        self.validate()

    @classmethod
    def load_from_json(cls, js: list) -> "Recipe":
        inp = js[0]
        out = js[1]
        r = Recipe([], [])
        for _ in inp:
            i = Ingredient.load_from_json(_)
            r.add_input(i)
        for _ in out:
            o = Ingredient.load_from_json(_)
            r.add_output(o)
        return r

    def dump_to_json(self) -> list:
        result = [[], []]
        for inp in self.inputs:
            result[0].append(inp.dump_to_json())
        for out in self.outputs:
            result[1].append(out.dump_to_json())
        return result


class RecipeBook:
    def __init__(self, fileName: str = None):
        self.recipes: List[Recipe] = list()
        self.dirty = False
        if fileName is not None:
            self.load_from_file(fileName)

    def load_from_file(self, fileName: str):
        with open(fileName, "r") as file:
            js = json.load(file)
            v = js["v"]
            if v != VERSION:
                raise CompatibilityException("Cannot reconcile version {v} with {VERSION}, please contact author")
            for recipe in js["r"]:
                self.recipes.append(Recipe.load_from_json(recipe))

    def dump_to_file(self, fileName: str):
        with open(fileName, "w") as file:
            d = {"v": VERSION, "r": []}
            for recipe in self.recipes:
                d["r"].append(recipe.dump_to_json())
            json.dump(d, file)
        self.dirty = False


def main():
    pass


if __name__ == "__main__":
    main()
