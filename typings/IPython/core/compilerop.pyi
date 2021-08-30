"""
This type stub file was generated by pyright.
"""

import codeop
from contextlib import contextmanager

"""Compiler tools with improved interactive support.

Provides compilation machinery similar to codeop, but with caching support so
we can provide interactive tracebacks.

Authors
-------
* Robert Kern
* Fernando Perez
* Thomas Kluyver
"""
PyCF_MASK = ...
def code_name(code, number=...): # -> str:
    """ Compute a (probably) unique name for code for caching.

    This now expects code to be unicode.
    """
    ...

class CachingCompiler(codeop.Compile):
    """A compiler that caches code compiled from interactive statements.
    """
    def __init__(self) -> None:
        ...
    
    def ast_parse(self, source, filename=..., symbol=...): # -> Any:
        """Parse code to an AST with the current compiler flags active.

        Arguments are exactly the same as ast.parse (in the standard library),
        and are passed to the built-in compile function."""
        ...
    
    def reset_compiler_flags(self): # -> None:
        """Reset compiler flags to default state."""
        ...
    
    @property
    def compiler_flags(self): # -> int:
        """Flags currently active in the compilation process.
        """
        ...
    
    def get_code_name(self, raw_code, transformed_code, number): # -> str:
        """Compute filename given the code, and the cell number.

        Parameters
        ----------
        raw_code : str
          The raw cell code.
        transformed_code : str
          The executable Python source code to cache and compile.
        number : int
          A number which forms part of the code's name. Used for the execution
          counter.

        Returns
        -------
        The computed filename.
        """
        ...
    
    def cache(self, transformed_code, number=..., raw_code=...): # -> str:
        """Make a name for a block of code, and cache the code.

        Parameters
        ----------
        transformed_code : str
          The executable Python source code to cache and compile.
        number : int
          A number which forms part of the code's name. Used for the execution
          counter.
        raw_code : str
          The raw code before transformation, if None, set to `transformed_code`.

        Returns
        -------
        The name of the cached code (as a string). Pass this as the filename
        argument to compilation, so that tracebacks are correctly hooked up.
        """
        ...
    
    @contextmanager
    def extra_flags(self, flags): # -> Generator[None, None, None]:
        ...
    


def check_linecache_ipython(*args): # -> None:
    """Call linecache.checkcache() safely protecting our cached values.
    """
    ...
