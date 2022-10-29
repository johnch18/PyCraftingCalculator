#!/usr/bin/python3.11


__all__ = []

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, Optional, cast

from item import Item
from recipe import Recipe

# Abstract Nodes
from utility.ireprable import IReprable


@dataclass
class Node(ABC):
    """
    ABC of all nodes, simply points to the trie
    """
    master: "Trie"

    def get_root(self) -> "RootNode":
        """
        Returns the root of the trie
        :return: Root
        """
        return self.master.root

    @abstractmethod
    def get_line_representation(self, depth: int = 0, repr_func: Callable[[Any], str] = repr) -> Iterable[str]:
        """
        Yields different lines of tree string
        :param depth: How many layers down
        :param repr_func: What to run on each value
        :return: Yields lines
        """


@dataclass
class ParentNode(Node, ABC):
    """
    Has children
    """
    children: list["ChildNode"] = field(default_factory=list)

    def __iter__(self) -> Iterator["ChildNode"]:
        """
        Allows iteration through children
        :return: Iterator of children
        """
        yield from self.children

    @property
    def num_children(self) -> int:
        return len(self.children)

    @property
    def first_child(self) -> Optional["ChildNode"]:
        if self.num_children > 0:
            return self.children[0]
        return None

    @property
    def last_child(self) -> Optional["ChildNode"]:
        if self.num_children > 0:
            return self.children[-1]
        return None

    def add_child(self, child: "ChildNode"):
        self.children.append(child)
        child.parent = self


@dataclass
class DoublyLinkedListNode(Node, ABC):
    """
    Node that acts as a doubly linked list node
    """
    prev: "DoublyLinkedListNode" = field(default=None)
    next: "DoublyLinkedListNode" = field(default=None)

    def emplace(self, new_prev: "DoublyLinkedListNode", new_next: "DoublyLinkedListNode"):
        """
        Places this node between two others and links them
        :param new_prev: new previous node
        :param new_next: new next node
        """
        DoublyLinkedListNode.link(new_prev, self)
        DoublyLinkedListNode.link(self, new_next)

    # noinspection PyShadowingBuiltins
    @classmethod
    def link(cls, prev: "DoublyLinkedListNode", next: "DoublyLinkedListNode"):
        """
        Links two nodes
        :param prev: previous
        :param next: next
        """
        prev.next = next
        next.prev = prev

    @property
    def has_prev(self) -> bool:
        """
        Checks if node has previous node
        :return: ^
        """
        return self.prev is not None

    @property
    def has_next(self) -> bool:
        """
        Checks if node has next node
        :return: ^
        """
        return self.next is not None

    @property
    def head(self) -> "DoublyLinkedListNode":
        """
        Gets head of list
        :return: ^
        """
        if self.has_prev:
            return self.prev.head
        return self

    @property
    def tail(self) -> "DoublyLinkedListNode":
        """
        Gets tail of list
        :return: ^
        """
        if self.has_next:
            return self.next.tail
        return self


@dataclass(unsafe_hash=True, order=True)
class ChildNode(Node, ABC):
    """
    A node with a parent
    """
    parent: ParentNode = field(default=None, hash=False)

    @property
    def is_orphan(self) -> bool:
        """
        Whether a node has a parent
        :return: ^
        """
        return self.parent is None


@dataclass
class VertexNode(DoublyLinkedListNode, ChildNode, ABC):
    """
    Combination of Linked List and Tree nodes, think of it like a cross, DLL Node is horizontal, Child Node is vertical.
    DLL and Child Nodes are separated for clarity
    """


# Concrete Nodes


@dataclass
class RootNode(ParentNode):
    """
    Start of the trie, has no properties aside from being a parent
    """

    def to_string(self, repr_func: Callable[[Any], str]) -> str:
        """
        Gets string representation of tree from root
        :param repr_func: Function to call on data
        :return:
        """
        return "\n".join(self.get_line_representation(repr_func=repr_func))

    def get_line_representation(self, depth: int = 0, repr_func: Callable[[Any], str] = repr) -> Iterable[str]:
        for child_index, child in enumerate(self.children):
            lines = child.get_line_representation(depth+1, repr_func)
            for line_index, line in enumerate(lines):
                if child_index < self.num_children - 1 or line_index == 0:
                    yield f"|{line}"
                else:
                    yield f" {line}"
            if child_index < self.num_children - 1:
                yield "|"


@dataclass
class BranchNode(ParentNode, ChildNode):
    """
    Internal node that stores keys in the form of items
    """
    item: Item = field(default=None)

    def get_line_representation(self, depth: int = 0, repr_func: Callable[[Any], str] = repr) -> Iterable[str]:
        spacer = "    "
        yield "----+ " + repr_func(self.item)
        for child_index, child in enumerate(self.children):
            lines = child.get_line_representation(depth + 1, repr_func)
            for line_index, line in enumerate(lines):
                if child_index < self.num_children - 1 or line_index == 0:
                    yield f"{spacer}|{line}"
                else:
                    yield f" {spacer}{line}"


@dataclass
class LeafNode(VertexNode):
    """
    External node that stores values in the form of recipes
    """
    recipe: Recipe = field(default=None, hash=True, compare=True)

    def get_line_representation(self, depth: int = 0, repr_func: Callable[[Any], str] = repr) -> Iterable[str]:
        yield f"---- {repr_func(self.recipe)}"


# Trie


@dataclass
class Trie(ABC):
    """
    Stores a root and performs operations on the data
    """
    root: RootNode

    def __iter__(self) -> Iterator[LeafNode]:
        """
        Iterates through leaves
        :return: ^
        """
        # Find first leaf
        current: Node = self.root
        while isinstance(current, ParentNode):
            current = current.first_child
        # Yield leaves
        current: DoublyLinkedListNode = cast(DoublyLinkedListNode, current)
        while current is not None:
            yield current
            current = current.next


class RecipeTrie(Trie, IReprable):
    """
    Trie with added functionality for recipe manipulation
    """

    def __init__(self, *recipe_list: Recipe):
        self.root = RootNode(self)
        self.add_recipes(recipe_list)

    def __iter__(self) -> Iterator[Recipe]:
        """
        Iterate through recipes
        :return: Iteration of recipes
        """
        yield from (node.recipe for node in super().__iter__())

    def __str__(self) -> str:
        return self.root.to_string(repr_func=str)

    def add_recipe(self, recipe: Recipe) -> LeafNode:
        """
        Adds a recipe to the trie if not there, returns node containing recipe either way
        :param recipe: Recipe to add
        :return: Node containing recipe
        """
        current_node = self.root
        for stack in recipe.input_item_stacks:
            item = stack.item
            for child_node in current_node:
                if isinstance(child_node, BranchNode) and cast(BranchNode, child_node).item == item:
                    current_node = child_node
                    break
            else:
                new_node: BranchNode = BranchNode(master=self, item=item)
                current_node.add_child(new_node)
                current_node = new_node
        new_leaf: LeafNode = LeafNode(master=self, recipe=recipe)
        current_node.add_child(new_leaf)
        return new_leaf

    def add_recipes(self, recipe_list: Iterable[Recipe]):
        """
        Adds a collection of recipes
        :param recipe_list: Recipes to add
        """
        for recipe in recipe_list:
            self.add_recipe(recipe)

    def fancy_string(self) -> str:
        return self.root.to_string(repr_func=lambda i: i.fancy_string())


def main():
    test = RecipeTrie(
        Recipe.from_string("<wood_log> -> <wood_plank>:4"),
        Recipe.from_string("<wood_plank>:2 -> <stick>:4"),
        Recipe.from_string("<wood_plank>:4 -> <crafting_bench>"),
        Recipe.from_string("<wood_plank>:3 + <stick>:2 -> <wood_pickaxe>"),
        Recipe.from_string("<wood_plank>:3 + <stick>:2 -> <wood_axe>"),
        Recipe.from_string("<cobblestone>:3 + <stick>:2 -> <stone_pickaxe>"),
        Recipe.from_string("<obsidian>:4 + <book> + <diamond>:2 -> <enchanting_table>"),
        Recipe.from_string("<iron_ore> -> <crushed_iron_ore>:2 + <stone_dust>:1:0.1111"),
        Recipe.from_string("<wood_plank>:4 + <stick>:4 + <screwdriver>:1:0.0 -> <wood_gear>")
        )
    print(test.fancy_string())


if __name__ == "__main__":
    main()
