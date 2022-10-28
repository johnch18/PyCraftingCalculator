#!/usr/bin/python3


__all__ = ["ISerializable"]

from abc import ABC, abstractmethod
from typing import ClassVar, TypeVar


class ISerializable(ABC):
    """
    Guarantees serializable behavior in strings, JSON, and XML
    """

    def __str__(self) -> str:
        return self.to_string()

    @abstractmethod
    def to_string(self) -> str:
        """
        Serializes to a string
        :return:
        """

    T: ClassVar[TypeVar] = TypeVar("T", bound="ISerializable")

    @classmethod
    @abstractmethod
    def from_string(cls: T, source: str) -> T:
        """
        Deserializes from a string
        :param source:  string to use
        :return: Object
        """


def main():
    pass


if __name__ == "__main__":
    main()
