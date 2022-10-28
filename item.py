#!/usr/bin/python3


__all__ = ["Item"]

import re
from dataclasses import dataclass, field
from typing import ClassVar, TypeVar

from utility.iserializable import ISerializable
from utility.misc import snake_to_canonical


@dataclass(unsafe_hash=True, order=True)
class Item(ISerializable):
    """
    An object which has an id, a name, and metadata
    """

    name: str  # name must be snakecase
    metadata: int = 0  # metadata >= 0
    proper_name: str = field(default=None, hash=False, compare=False)  # Fancy

    metadata_any: bool = field(default=False, hash=False)

    regex: ClassVar[str] = r"<(\w\w*):?([\d*]*)?>"  # Regex pattern for item

    @property
    def canonical_name(self) -> str:
        """
        Gets human-readable name from name, unless proper_name is set
        :return: Human-readable name
        """
        if self.proper_name is not None:
            return self.proper_name
        return snake_to_canonical(self.name)

    def to_string(self) -> str:
        """
        Serializes to string
        :return: String representation
        """
        return f"<{self.name}:{self.metadata if not self.metadata_any else '*'}>"

    T: ClassVar[TypeVar] = TypeVar("T", bound="Item")

    @classmethod
    def from_string(cls: T, item_string: str) -> T:
        """
        String factory for Item
        :param item_string: String to parse
        :return: The item
        """
        item_name: str
        metadata_string: str
        # Get match
        matches = re.findall(cls.regex, item_string)[0]
        # print(item_string, cls.regex, matches)
        item_name, metadata_string = matches
        # Check metadata
        if not metadata_string:
            metadata_string = "0"
        metadata: int
        if metadata_string == "*":
            metadata = 0
            metadata_any = True
        else:
            metadata = int(metadata_string)
            metadata_any = False
        return cls(item_name, metadata, metadata_any=metadata_any)


def main():
    pass


if __name__ == "__main__":
    main()
