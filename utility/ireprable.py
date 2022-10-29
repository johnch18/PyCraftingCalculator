#!/usr/bin/python3


__all__ = ["IReprable"]

from abc import ABC, abstractmethod


class IReprable(ABC):
    @abstractmethod
    def fancy_string(self) -> str:
        """
        A nicely formatted string representation of the object
        :return:
        """


def main():
    pass


if __name__ == "__main__":
    main()
