"""
This type stub file was generated by pyright.
"""

"""Posix-specific implementation of process utilities.

This file is only meant to be imported by process.py, not by end-users.
"""
class ProcessHandler:
    """Execute subprocesses under the control of pexpect.
    """
    read_timeout = ...
    terminate_timeout = ...
    logfile = ...
    _sh = ...
    @property
    def sh(self): # -> str:
        ...
    
    def __init__(self, logfile=..., read_timeout=..., terminate_timeout=...) -> None:
        """Arguments are used for pexpect calls."""
        ...
    
    def getoutput(self, cmd): # -> bytes | str | None:
        """Run a command and return its stdout/stderr as a string.

        Parameters
        ----------
        cmd : str
          A command to be executed in the system shell.

        Returns
        -------
        output : str
          A string containing the combination of stdout and stderr from the
        subprocess, in whatever order the subprocess originally wrote to its
        file descriptors (so the order of the information in this string is the
        correct order as would be seen if running the command in a terminal).
        """
        ...
    
    def getoutput_pexpect(self, cmd): # -> bytes | str | None:
        """Run a command and return its stdout/stderr as a string.

        Parameters
        ----------
        cmd : str
          A command to be executed in the system shell.

        Returns
        -------
        output : str
          A string containing the combination of stdout and stderr from the
        subprocess, in whatever order the subprocess originally wrote to its
        file descriptors (so the order of the information in this string is the
        correct order as would be seen if running the command in a terminal).
        """
        ...
    
    def system(self, cmd): # -> int:
        """Execute a command in a subshell.

        Parameters
        ----------
        cmd : str
          A command to be executed in the system shell.

        Returns
        -------
        int : child's exitstatus
        """
        ...
    


system = ...
def check_pid(pid): # -> bool:
    ...

