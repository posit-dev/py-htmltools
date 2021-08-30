"""
This type stub file was generated by pyright.
"""

from IPython.utils.decorators import undoc

"""
IO related utilities.
"""
@undoc
class IOStream:
    def __init__(self, stream, fallback=...) -> None:
        ...
    
    def __repr__(self): # -> str:
        ...
    
    def write(self, data): # -> None:
        ...
    
    def writelines(self, lines): # -> None:
        ...
    
    @property
    def closed(self):
        ...
    
    def close(self): # -> None:
        ...
    


devnull = ...
class Tee:
    """A class to duplicate an output stream to stdout/err.

    This works in a manner very similar to the Unix 'tee' command.

    When the object is closed or deleted, it closes the original file given to
    it for duplication.
    """
    def __init__(self, file_or_name, mode=..., channel=...) -> None:
        """Construct a new Tee object.

        Parameters
        ----------
        file_or_name : filename or open filehandle (writable)
          File that will be duplicated

        mode : optional, valid mode for open().
          If a filename was give, open with this mode.

        channel : str, one of ['stdout', 'stderr']
        """
        ...
    
    def close(self): # -> None:
        """Close the file and restore the channel."""
        ...
    
    def write(self, data): # -> None:
        """Write data to both channels."""
        ...
    
    def flush(self): # -> None:
        """Flush both channels."""
        ...
    
    def __del__(self): # -> None:
        ...
    


def ask_yes_no(prompt, default=..., interrupt=...): # -> bool:
    """Asks a question and returns a boolean (y/n) answer.

    If default is given (one of 'y','n'), it is used if the user input is
    empty. If interrupt is given (one of 'y','n'), it is used if the user
    presses Ctrl-C. Otherwise the question is repeated until an answer is
    given.

    An EOF is treated as the default answer.  If there is no default, an
    exception is raised to prevent infinite loops.

    Valid answers are: y/yes/n/no (match is not case sensitive)."""
    ...

def temp_pyfile(src, ext=...):
    """Make a temporary python file, return filename and filehandle.

    Parameters
    ----------
    src : string or list of strings (no need for ending newlines if list)
      Source code to be written to the file.

    ext : optional, string
      Extension for the generated file.

    Returns
    -------
    (filename, open filehandle)
      It is the caller's responsibility to close the open file and unlink it.
    """
    ...

@undoc
def atomic_writing(*args, **kwargs): # -> _GeneratorContextManager[TextIOWrapper | FileIO]:
    """DEPRECATED: moved to notebook.services.contents.fileio"""
    ...

@undoc
def raw_print(*args, **kw): # -> None:
    """DEPRECATED: Raw print to sys.__stdout__, otherwise identical interface to print()."""
    ...

@undoc
def raw_print_err(*args, **kw): # -> None:
    """DEPRECATED: Raw print to sys.__stderr__, otherwise identical interface to print()."""
    ...

rprint = ...
rprinte = ...
@undoc
def unicode_std_stream(stream=...): # -> Any | StreamWriter:
    """DEPRECATED, moved to nbconvert.utils.io"""
    ...
