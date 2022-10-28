#!/usr/bin/python3


__all__ = ["snake_to_canonical"]


def snake_to_canonical(snake: str) -> str:
    """
    Converts a snake-case name to a canonical name.
    e.g. 'foo_bar_baz' -> 'Foo Bar Baz'
    :param snake: snake-case name
    :return: Canonical name
    """
    return " ".join(s.capitalize() for s in snake.split("_"))


def main():
    pass


if __name__ == "__main__":
    main()
