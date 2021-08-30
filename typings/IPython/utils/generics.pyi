"""
This type stub file was generated by pyright.
"""

from functools import singledispatch

"""Generic functions for extending IPython.
"""
@singledispatch
def inspect_object(obj): # -> NoReturn:
    """Called when you do obj?"""
    ...

@singledispatch
def complete_object(obj, prev_completions): # -> NoReturn:
    """Custom completer dispatching for python objects.

    Parameters
    ----------
    obj : object
        The object to complete.
    prev_completions : list
        List of attributes discovered so far.

    This should return the list of attributes in obj. If you only wish to
    add to the attributes already discovered normally, return
    own_attrs + prev_completions.
    """
    ...
