"""
Log class for pymesh
"""

from rich import print as rprint
from rich.console import Console
from rich.theme import Theme

import datetime

class Logger:
    log_out_all = []
    log_err_all = []
    timestamp = "." + datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    # default_out_style = Style.parse("bold green")
    # default_out_tag_style = Style.parse("bold black on green")

    custom_theme = Theme({
        "info" : 'bold green',
        "note": "bold magenta",
        "warn": "bold yellow",
        "error": "bold red"
    })
    console = Console(theme = custom_theme)

    def __init__(self, level=0):
        self.level = level

    def rule(self):
        pass

    def print(self, *message):
        """
        Default print (without Text wrapper) to be able to print dicts and other stuff
        """
        Logger.log_out_all.extend([str(i) for i in message])
        rprint(*message)

    def out(self, *message, style=None):
        """
        Write to stdout
        """
        Logger.log_out_all.append(" ".join(['INFO:' + "".join([' ']*self.level), *message]))
        Logger.console.print('INFO    :' + "".join([' ']*self.level), *message, style=style or 'info')

    def err(self, *message):
        """
        Write to "stderr"
        """
        Logger.log_out_all.append(" ".join(['ERROR:', *message]))
        Logger.console.print('ERROR:', *message, style='error')

    def warn(self, *message):
        """
        Write to stderr
        """
        Logger.log_out_all.append(" ".join(['WARN:', *message]))
        Logger.console.print('WARN:', *message, style='warn')

    def note(self, *message):
        """
        Write to stderr
        """
        Logger.log_out_all.append(" ".join(['NOTE:', *message]))
        Logger.console.print('NOTE:', *message, style='note')

    def die(self, *message, exception=RuntimeError):
        """
        Write to stderr, and die
        """
        self.err(*message)
        raise(exception)

    def write(self, fname, timestamp=False):
        """
        write to files
        """
        ts = Logger.timestamp if timestamp else ''
        with open(fname + ts + '.stdout.log', 'w') as outfile:
            outfile.write("\n".join(self.log_out_all))
        with open(fname + ts + '.stderr.log', 'w') as errfile:
            errfile.write("\n".join(self.log_err_all))
