"""
Log class for pymesh
"""

from rich import print as rprint
from rich.text import Text

class Logger:

    def __init__(self):
        self.logout = ""
        self.logerr = ""
        rprint("Logger Initialized")

    def out(self, *message, style=None):
        msg = " ".join(message)
        self.logout = "\n".join([self.logout, msg])
        rprint(Text(msg, style=style))

    def err(self, *message):
        msg = " ".join(message)
        self.logerr = "\n".join([self.logerr, 'ERROR: ' + msg])
        rprint(Text("ERROR: " + msg, style="bold red"))

    def warn(self, *message):
        msg = " ".join(message)
        self.logerr = "\n".join([self.logerr, 'WARN: ' + msg])
        rprint(Text("WARN: " + msg, style="bold yellow"))

    def die(self, *message, exception=RuntimeError):
        self.err(*message)
        raise(exception)
