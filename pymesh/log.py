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


class Logger:
    logout = ""
    logerr = ""

    def __init__(self, level=0):
        self.level = level

    def out(self, *message, style=None):
        """
        Write to stdout
        """
        prepend = "".join([' ']*self.level*2) + '|--> '
        msg = prepend + " ".join(message)
        Logger.logout = "".join([Logger.logout, msg, '\n'])
        rprint(Text(msg, style=style))

    def err(self, *message):
        """
        Write to stderr
        """
        msg = " ".join(message)
        Logger.logerr = "".join([Logger.logerr, 'ERROR: ' + msg, '\n'])
        rprint(Text("ERROR: " + msg, style="bold red"))

    def warn(self, *message):
        """
        Write to stderr
        """
        msg = " ".join(message)
        Logger.logerr = "".join([Logger.logerr, 'WARN: ' + msg, '\n'])
        rprint(Text("WARN: " + msg, style="bold yellow"))

    def note(self, *message):
        """
        Write to stderr
        """
        msg = " ".join(message)
        Logger.logerr = "".join([Logger.logerr, 'NOTE: ' + msg, '\n'])
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
        with open(fname + '.stdout.log', 'w') as outfile:
            outfile.write(self.logout)
        with open(fname + '.stderr.log', 'w') as errfile:
            errfile.write(self.logerr)
