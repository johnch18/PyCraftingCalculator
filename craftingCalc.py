#!/usr/bin/python3
"""
Second version of PyCraftingCalculator
By johnch18 on 12/30/21
"""


import json
import math
from typing import Dict, Optional, List, Tuple


MAX_DEPTH = 1000
VERSION = "1.0.0"
VERSION_STR = "version"
RECIPE_STR = "recipes"
INP_STR = "inputs"
OUT_STR = "outputs"
EN_STR = "enabled"
ING_STR = "ingredient"
FLUID_STR = "fluid"


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


class RecipeDepthException(CraftingCalcException):
    pass


class Component:
    COMPONENT_REGISTRY: Dict[str, "Component"] = dict()

    def __new__(cls, name: str, recipe: Optional["Recipe"] = None):
        if name.strip() == "":
            raise ValueError("Cannot have empty name")
        if name not in Component.COMPONENT_REGISTRY:
            newComponent = super(Component, cls).__new__(cls)
            Component.COMPONENT_REGISTRY[name] = newComponent
            return newComponent
        else:
            c = Component.COMPONENT_REGISTRY[name]
            if c.recipe is not None and recipe is not None:
                raise DuplicateRecipeException("Cannot have duplicate recipe.")
            c.set_recipe(recipe)
            return c

    def __init__(self, name: str, recipe: Optional["Recipe"] = None):
        self.name = name
        if not hasattr(self, "recipe"):
            self.recipe: Optional[Recipe] = None
        self.set_recipe(recipe)

    def __eq__(self, other: "Component"):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Component<{self.name}>"

    def set_recipe(self, recipe: Optional["Recipe"]):
        if recipe is None:
            return
        self.recipe = recipe


class Ingredient:
    def __init__(self, comp: Component, amount: int = 1, enabled: bool = True, isFluid: bool = False):
        self.component = comp
        self.amount = amount
        self.enabled = enabled
        self.isFluid = isFluid

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

    def __str__(self):
        return f"{self.component.name}:{self.amount}"

    def same_type(self, other: "Ingredient") -> bool:
        return self.component == other.component

    def is_component(self, comp: Component) -> bool:
        return self.component == comp

    @classmethod
    def load_from_json(cls, d: dict) -> "Ingredient":
        name, amt = d[ING_STR].split(":")
        enabled = d.get(EN_STR, True)
        isFluid = d.get(FLUID_STR, False)
        return Ingredient(Component(name), int(amt), enabled=enabled, isFluid=isFluid)

    def dump_to_json(self) -> dict:
        d = {ING_STR: f"{self.component.name}:{self.amount}", EN_STR: self.enabled, FLUID_STR: self.isFluid}
        return d

    def get_tree(self, factor: int = 1, depth: int = 0) -> dict:
        if depth > MAX_DEPTH:
            raise RecipeDepthException("Recipe exceeded maximum depth")
        ing = self * factor
        result = {"output": ing, "inputs": []}
        if ing.recipe is None:
            return result
        crafts = self.recipe.get_num_crafts(ing)
        for inp in self.recipe.inputs:
            result["inputs"].append(inp.get_tree(crafts, depth+1))
        return result

    @property
    def recipe(self) -> Optional["Recipe"]:
        return self.component.recipe

    @property
    def name(self) -> str:
        return self.component.name


class Recipe:
    def __init__(self, inputs: List[Ingredient], outputs: List[Ingredient], enabled: bool = True):
        self.inputs = inputs
        self.outputs = outputs
        self.enabled = enabled
        self.validate()

    def __repr__(self):
        return f"{' + '.join(str(s) for s in self.outputs)} <- {' + '.join(str(s) for s in self.inputs)}"

    def __hash__(self):
        h = 0
        for i in self.inputs:
            h += hash(i)
        for o in self.outputs:
            h += hash(o)
        return h

    def requires(self, comp: Component) -> bool:
        Q = self.inputs[:]
        dirty = False
        while len(Q) > 0:
            inp = Q.pop(0)
            print(inp)
            if inp.is_component(comp) and dirty:
                return True
            Q.extend(inp.component.recipe.inputs)
            dirty = True
        return False

    def validate(self):
        for i in self.inputs:
            if i.component.recipe is not None:
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
    def load_from_json(cls, js: dict) -> "Recipe":
        inp = js[INP_STR]
        out = js[OUT_STR]
        enabled = js[EN_STR]
        r = Recipe([], [], enabled)
        for _ in inp:
            i = Ingredient.load_from_json(_)
            r.add_input(i)
        for _ in out:
            o = Ingredient.load_from_json(_)
            o.component.set_recipe(r)
            r.add_output(o)
        return r

    def dump_to_json(self) -> dict:
        result = {INP_STR:[], OUT_STR:[], EN_STR: self.enabled}
        for inp in self.inputs:
            result[INP_STR].append(inp.dump_to_json())
        for out in self.outputs:
            result[OUT_STR].append(out.dump_to_json())
        return result

    def cost(self, ing: Ingredient) -> Dict[str, Ingredient]:
        result = dict()
        crafts = self.get_num_crafts(ing)
        for inp in self.inputs:
            if inp.recipe is None:
                if inp.name in result:
                    result[inp.name] += inp * crafts
                else:
                    result[inp.name] = inp * crafts
                continue
            cost = inp.recipe.cost(inp * crafts)
            for name, ingredient in cost.items():
                if name in result:
                    result[name] += ingredient
                else:
                    result[name] = ingredient
        return result

    def get_num_crafts(self, ingredient: Ingredient) -> int:
        requestedNumberOfCrafts = ingredient.amount
        for i in self.outputs:
            if i.same_type(ingredient):
                target = i
                break
        else:
            raise Exception("Something went wrong")
        yieldPerCraft = target.amount
        factor = math.ceil(requestedNumberOfCrafts / yieldPerCraft)
        return factor


class RecipeBook:
    def __init__(self, fileName: Optional[str] = None):
        self.recipes: List[Recipe] = list()
        self.dirty = False
        if fileName is not None:
            self.load_from_file(fileName)

    def __iter__(self):
        return iter(self.recipes)

    def load_from_file(self, fileName: str):
        with open(fileName, "r") as file:
            js = json.load(file)
            v = js[VERSION_STR]
            if v != VERSION:
                raise CompatibilityException("Cannot reconcile version {v} with {VERSION}, please contact author")
            for recipe in js[RECIPE_STR]:
                self.recipes.append(Recipe.load_from_json(recipe))

    def dump_to_file(self, fileName: str):
        with open(fileName, "w") as file:
            d = {VERSION_STR: VERSION, RECIPE_STR: []}
            for recipe in self.recipes:
                d[RECIPE_STR].append(recipe.dump_to_json())
            json.dump(d, file)
        self.dirty = False

    def add_recipe(self, recipe: Recipe):
        self.recipes.append(recipe)
        self.dirty = True


def main():
    pass


if __name__ == "__main__":
    main()
