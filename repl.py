#!/usr/bin/python3
import _io
import sys
import time
from abc import ABC, abstractmethod
from enum import IntEnum, auto
from typing import Dict, Type


class Command(ABC):
    keyword = None
    help_msg = None

    @staticmethod
    @abstractmethod
    def action(repl, *_, **__):
        pass


class HelpCommand(Command):
    @staticmethod
    def action(repl, *args, **kwargs):
        if len(args) > 0:
            for c in args:
                if c in repl.commands:
                    repl.println(f"{c}:\n{repl.commands[c].help_msg}")
                else:
                    repl.printerr(f"Unable to find command {c}")
        else:
            for c in repl.commands:
                repl.println(c)

    keyword = "help"
    help_msg = """Usage: help [*commands]
    Returns either a list of commands or the help message for that command, like what you're seeing now.
    """


class ExitCommand(Command):

    @staticmethod
    def action(repl, *_, **__):
        repl.running = False

    keyword = "exit"
    help_msg = """"""


class Repl:
    DEFAULT_COMMANDS = [
        HelpCommand, ExitCommand
    ]

    class IOGadget:
        class ColorEnum(IntEnum):
            BLACK = 0
            RED = auto()
            GREEN = auto()
            YELLOW = auto()
            BLUE = auto()
            MAGENTA = auto()
            CYAN = auto()
            WHITE = auto()

            def get_fg(self):
                return 30 + self.value

            def get_bg(self):
                return 40 + self.value

        def __init__(self, istream, ostream, estream):
            self.istream = istream
            self.ostream = ostream
            self.estream = estream

        @staticmethod
        def format_text(text: str, color: ColorEnum = ColorEnum.WHITE, bolded: bool = False, italicized: bool = False,
                        blinking=False):
            bold = ";1" if bolded else ""
            italic = ";3" if italicized else ""
            blink = ";5" if blinking else ""
            s = f"{color.get_fg()}{bold}{italic}{blink}m{str(text)}"
            s = f"\033[{s}\033[0m"
            # print(repr(s))
            return s

        def put(self, text, **fmt):
            self.ostream.write(self.format_text(text, **fmt))
            self.ostream.flush()

        def get(self, prompt=None, **fmt):
            if prompt is not None:
                self.put(prompt, **fmt)
                time.sleep(1)
            return self.istream.readline()

        def err(self, text, fg=ColorEnum.RED, **fmt):
            self.estream.write(self.format_text(text, fg, **fmt))
            self.estream.flush()

    def __init__(self, istream=sys.stdin, ostream=sys.stdout, estream=sys.stderr):
        self.io = Repl.IOGadget(istream, ostream, estream)
        self.running = True
        self.history = []
        self.commands: Dict[str, Type[Command]] = {}
        self.init_commands()

    def repl(self):
        while self.running:
            try:
                self.get_command()
            except KeyboardInterrupt:
                self.on_keyboard_interrupt()
        self.println("")

    def prompt(self, text=">>> ", bolded=True, blinking=False, **fmt):
        v = self.io.get(prompt=text, bolded=bolded, blinking=blinking, **fmt).strip()
        self.history.append(v)
        return v

    def get_command(self):
        text = self.prompt()
        toks = text.split()
        if len(toks) < 1:
            return
        com = toks.pop(0)
        if com not in self.commands:
            self.printerr("Invalid command")
            return
        self.commands[com].action(self, *toks)

    def init_commands(self):
        for com in Repl.DEFAULT_COMMANDS:
            self.commands[com.keyword] = com

    def println(self, text):
        self.io.put(f"{text}\n")

    def printerr(self, err):
        self.io.err(f"{err}\n")

    def on_keyboard_interrupt(self):
        self.running = False


def main():
    test = Repl()
    test.repl()


if __name__ == "__main__":
    main()
