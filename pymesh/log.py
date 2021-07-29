"""
Log class for pymesh
"""

try:
    from rich import print as rprint
    from rich.text import Text
    # from rich.console import Console
except ImportError:
    def rprint(obj):
        print(obj)
    def Text(*obj, style=None):
        return "".join(obj)

import datetime

class Logger:
    log_out_all = []
    log_err_all = []
    timestamp = "." + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    default_out_style = "bold green"
    # console = Console()

    # glyph_head = '❯❯'
    glyph_head = '❯'
    glyph_tail = '❯'
    glyph_end = ''
    # glyph_end  = '❮❮'
    # glyph_head  = '❮❮'
    # glyph_tail = ' '
    # glyph_end = '❯❯'
    indent_factor = 1

    # glyph_head = ''
    # glyph_tail = ' '
    # glyph_end = ''

    # gleft = ''

    # glyph_head = '|-->'
    # glyph_tail = ' '
    # glyph_head = 'INFO:'
    # glyph_tail = ''
    # glyph_head = '->>'
    # glyph_tail = '->>'


    def __init__(self, level=0):
        self.level = level

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
        prepend = "".join([Logger.glyph_tail]*self.level*Logger.indent_factor) + Logger.glyph_head + ' '
        msg = "INFO" + prepend + " ".join(message) + ' ' + Logger.glyph_end
        Logger.log_out_all.append(msg)
        rprint(Text(msg, style=style or Logger.default_out_style))

    def err(self, *message):
        """
        Write to stderr
        """
        msg = " ".join(message)
        Logger.log_err_all.append('ERROR: ' + msg)
        rprint(Text("ERROR: " + msg, style="bold red"))

    def warn(self, *message):
        """
        Write to stderr
        """
        msg = " ".join(message)
        Logger.log_err_all.append('WARN: ' + msg)
        rprint(Text("WARN: " + msg, style="bold yellow"))

    def note(self, *message):
        """
        Write to stderr
        """
        msg = " ".join(message)
        Logger.log_err_all.append('NOTE: ' + msg)
        rprint(Text("NOTE: " + msg, style="bold magenta"))

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
