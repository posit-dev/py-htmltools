"""
This type stub file was generated by pyright.
"""

import sys
from typing import Callable
from prompt_toolkit.filters import Condition
from IPython.utils.decorators import undoc

"""
Module to define and register Terminal IPython shortcuts with
:mod:`prompt_toolkit`
"""
@undoc
@Condition
def cursor_in_leading_ws(): # -> bool:
    ...

def create_ipython_shortcuts(shell): # -> KeyBindings:
    """Set up the prompt_toolkit keyboard shortcuts for IPython"""
    ...

def reformat_text_before_cursor(buffer, document, shell): # -> None:
    ...

def newline_or_execute_outer(shell): # -> (event: Unknown) -> None:
    ...

def previous_history_or_previous_completion(event): # -> None:
    """
    Control-P in vi edit mode on readline is history next, unlike default prompt toolkit.

    If completer is open this still select previous completion.
    """
    ...

def next_history_or_next_completion(event): # -> None:
    """
    Control-N in vi edit mode on readline is history previous, unlike default prompt toolkit.

    If completer is open this still select next completion.
    """
    ...

def dismiss_completion(event): # -> None:
    ...

def reset_buffer(event): # -> None:
    ...

def reset_search_buffer(event): # -> None:
    ...

def suspend_to_bg(event): # -> None:
    ...

def force_exit(event): # -> NoReturn:
    """
    Force exit (with a non-zero return value)
    """
    ...

def indent_buffer(event): # -> None:
    ...

@undoc
def newline_with_copy_margin(event): # -> None:
    """
    DEPRECATED since IPython 6.0

    See :any:`newline_autoindent_outer` for a replacement.

    Preserve margin and cursor position when using
    Control-O to insert a newline in EMACS mode
    """
    ...

def newline_autoindent_outer(inputsplitter) -> Callable[..., None]:
    """
    Return a function suitable for inserting a indented newline after the cursor.

    Fancier version of deprecated ``newline_with_copy_margin`` which should
    compute the correct indentation of the inserted line. That is to say, indent
    by 4 extra space after a function definition, class definition, context
    manager... And dedent by 4 space after ``pass``, ``return``, ``raise ...``.
    """
    ...

def open_input_in_editor(event): # -> None:
    ...

if sys.platform == 'win32':
    ...
