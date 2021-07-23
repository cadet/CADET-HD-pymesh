"""
Log class for pymesh
"""

try:
    from rich import print as rprint
    from rich.text import Text
except ImportError:
    def rprint(obj):
        print(obj)
    def Text(*obj, style=None):
        return "".join(obj)

import datetime

class Logger:
    logout = []
    logerr = []
    timestamp = "." + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    glyph_head = '|-->'
    glyph_tail = ' '

    def __init__(self, level=0):
        self.level = level

    def print(self, *message):
        """
        Default print (without Text wrapper) to be able to print dicts and other stuff
        """
        Logger.logout.extend([str(i) for i in message])
        rprint(*message)

    def out(self, *message, style=None):
        """
        Write to stdout
        """
        prepend = "".join([Logger.glyph_tail]*self.level*2) + Logger.glyph_head + ' '
        msg = prepend + " ".join(message)
        Logger.logout.append(msg)
        rprint(Text(msg, style=style))

    def err(self, *message):
        """
        Write to stderr
        """
        msg = " ".join(message)
        Logger.logerr.append('ERROR: ' + msg)
        rprint(Text("ERROR: " + msg, style="bold red"))

    def warn(self, *message):
        """
        Write to stderr
        """
        msg = " ".join(message)
        Logger.logerr.append('WARN: ' + msg)
        rprint(Text("WARN: " + msg, style="bold yellow"))

    def note(self, *message):
        """
        Write to stderr
        """
        msg = " ".join(message)
        Logger.logerr.append('NOTE: ' + msg)
        rprint(Text("NOTE: " + msg, style="bold magenta"))

    def die(self, *message, exception=RuntimeError):
        """
        Write to stderr, and die
        """
        self.err(*message)
        raise(exception)

    def write(self, fname):
        """
        write to files
        """
        with open(fname + Logger.timestamp + '.stdout.log', 'w') as outfile:
            outfile.write("\n".join(self.logout))
        with open(fname + Logger.timestamp + '.stderr.log', 'w') as errfile:
            errfile.write("\n".join(self.logerr))
