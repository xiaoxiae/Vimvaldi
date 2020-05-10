"""A module for working with command."""
from dataclasses import dataclass


@dataclass
class Command:
    """The default command class that is inherited by all other command classes."""



class GeneralCommand(Command):
    """Other commands that didn't really fit anywhere else."""

class ToggleFocusCommand(GeneralCommand):
    """A command to toggle focus from the status line to the main window."""

@dataclass
class QuitCommand(GeneralCommand):
    """A command to quit. A nicer version of terminate."""
    forced: bool = False  # q!

@dataclass
class SaveCommand(GeneralCommand):
    """A command to save."""
    path: str = None
    forced: bool = False  # w!


class ComponentCommand(Command):
    """A class for component commands."""

class PopComponentCommand(ComponentCommand):
    """Pop a component from the component stack."""

@dataclass
class PushComponentCommand(ComponentCommand):
    """Push a component onto the component stack."""
    component: str



class StatusLineCommand(Command):
    """A class for status line commands."""

@dataclass
class SetStatusLineTextCommand(StatusLineCommand):
    """Set the status line to the given text."""
    text: str
    position: int

@dataclass
class SetStatusLineStateCommand(StatusLineCommand):
    """Set the status line state."""
    state: int

class ClearStatusLineCommand(StatusLineCommand):
    """Clears the contents of the status line."""



class EditorCommand(Command):
    """Commands that concern the note editor."""


@dataclass
class InsertCommand(EditorCommand):
    """The command that gets passed to the editor to deal with."""
    text: str
