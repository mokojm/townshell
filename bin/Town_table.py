# ----- Structure of TownShell -----
# Town_table initialize logging and contains the commands availables for users
# Town_waiter is the core for handling commands passed by user, manage files and interact with the module Town_cooker, Town_clipper and Town_shortcuts
# Town_cooker contains all functions that actually modify Townscaper saved files
# Town_clipper contains all functions that transform Townscaper clip to corners/voxels directories
# Town_shortcuts handles all functions necessary for keyboard shortcuts
# The configuration like the path where Townscaper files are saved are in townshell.cfg

import logging
import sys
from cmd import Cmd
from os import environ, mkdir
from os.path import exists
from time import sleep

try:
    from bin.Town_waiter import *
except ModuleNotFoundError:
    sys.path.append(".")
    from bin.Town_waiter import *

# Logging objects
# Main logger
handler = logging.FileHandler(environ.get("LOGFILE", "log\\town.log"))
formatter = logging.Formatter(
    "{asctime} : [{name}:{funcName}] {levelname} :{message}", style="{"
)
handler.setFormatter(formatter)
root = logging.getLogger("Town")
root.setLevel(environ.get("LOGLEVEL", get_loglevel()))
root.addHandler(handler)

# Stream logger
streamhandler = logging.StreamHandler(sys.stdout)
streamformatter = logging.Formatter("{asctime} : {levelname} :{message}", style="{")
streamhandler.setFormatter(streamformatter)
stream = logging.getLogger("TownStream")
stream.setLevel(environ.get("LOGLEVEL", "INFO"))
stream.addHandler(streamhandler)

# Main class for shell interpreter designed for Townscaper improvements
class TownShell(Cmd):

    main_command = """Main commands :
- level -height:<n> ==> Modify the height of your structure according to <n>
- paint -color:<n> ==> Modify the color of your structure according to <n>
- colors ==> Print colors and their corresponding digits
- undo ==> Undo the last change
- redo ==> Redo the last change
See help <cmd> to get more information about a specific command
Type help or ? to list all commands.\n"""

    intro = "\nWelcome to TownShell !\n" + main_command
    prompt = "T> "
    file = None
    completekey = "tab"

    def preloop(self):
        """Initialize the data
        - Fetch the directory of Townscaper saved files
        - Start Shortcuts"""
        job = init_townshell()

        # Job to be executed
        if isinstance(job, list):
            self.cmdqueue.extend(job)

    def postloop(self):
        """End of the loop, keyboard shortcuts are stopped"""
        stop_shortcuts()
        sleep(1)

    def precmd(self, line):
        """Log the command passed and checks that scapedir is defined"""
        root.info("cmd : %s", line)
        return line

    def emptyline(self):
        """In Case of empty line nothing is done"""
        return

    def postcmd(self, stop, line):
        """Print a line break for log to be easy to read"""
        root.info("************************************")
        return stop

    def default(self, line):
        stream.warning("Unknown command")
        root.warning("Unknown command : %s", line)
        print(self.main_command)

    # ----- Commands -----
    def do_loadpath(self, arg):
        """loadpath <directory> ==> Override the path where Townscaper saved files are searched and saved
        <directory> : usually looks like 'C:\\Users\\<username>\\AppData\\LocalLow\\Oskar Stalberg\\Townscaper\\Saves'
        Drag and drop the directory in the screen or copy/paste the path of the directory"""
        output = update_cfg("scapedir", arg)

        # Success
        if output:
            stream.info("Path to Townscaper saved files updated")

    def do_listfiles(self, arg):
        """listfiles <option> ==> List the 5 most recent Townscaper saved files
        <option> : [optional] Can be '-a' or '-all' to see all Townscaper saved files"""
        parsed_args = parse(arg)
        print_scapefiles(args=parsed_args)

    # Alias for listfiles
    do_ls = do_listfiles
    do_dir = do_listfiles

    def do_colors(self, arg):
        """Print colors and their corresponding digits"""
        print_colors()

    def do_level(self, arg):
        """level -height:<n> -max_height:<n> - min_height:<n> -plain:<0/1> -color:<n> -color_filter:<n> <clip> ==> Modify the height of your structure according to <n>
        height (h): [mandatory] The height that will be added to the selected structure. Can be negative, the height of the structure will be decreased
        max_height (maxh): [optional] The maximum height for all building in the structure.
        min_height (minh): [optional] The minimum height for all building in the structure.
        plain (p): [optional] If 0 or not filled, the space below the elevated building stays empty. If 1, the created spaces are filled
        color (c): [optional] color (between 1 and 14) that will be applied to the newly created blocks. If not filled, the potential new blocks will take the color of the first colored one above them (or the default color if no blocks above them).
        color_filter (cf): [optional] Only the blocks having this color (between 1 and 14) will be affected by this command
        <clip> : [optional] Clip from Townscaper to be modified"""
        parsed_args = parse(arg)
        level_town(parsed_args)

    def do_paint(self, arg):
        """paint -color:<multi> -color_filter:<n> -height:<multi> <clip> ==> Modify the color of your structure according to <n>
        color (c): [mandatory] The color (between 1 and 14) that will be applied to the selected blocks. Can be 'r' for random color. Can be (n,m,p) for random choice between n,m and p
        color_filter (cf): [optional] Only the blocks with that color will be modified
        height (h): [optional] Can be a positive integer. Only the blocks at that height will be affected. Can be (n,m,p) only the blocks at these height will be affected. Can be ((n,m),(p,q)). Only the blocks between height n and m, and between p and q will be affected
        <clip> : [optional] Clip from Townscaper to be modified"""
        parsed_args = parse(arg)
        paint_town(parsed_args)

    def do_shortcuts(self, arg):
        """Print the current keyboard shortcuts"""
        print_shortcuts()

    def do_start_shortcuts(self, arg):
        """Activate the shortcuts on keyboard to play Townscaper more efficiently"""
        start_shortcuts()

    def do_stop_shortcuts(self, arg):
        """Deactivate the shortcuts on keyboard"""
        stop_shortcuts()

    def do_undo(self, arg):
        """Copy to clipboard to the previous clip"""
        undoClip()

    def do_redo(self, arg):
        """Put back to clipboard the clip before 'undo'"""
        redoClip()

    # def do_copy(self, arg):
    # """Copy all voxels or a group of voxels to a chosen height"""

    # def do_mix(self, arg):
    #     """Mix the voxels of several files"""

    # def do_randtown(self, arg):
    #     """Create a random town according to a set of criterias"""

    def do_exit(self, arg):
        """Exit the TownShell loop"""
        root.info("TownShell execution ended")
        stream.info("Bye (^_^)/ ")
        return True

    # do_EOF : same with do_exit
    do_EOF = do_exit

    # ----- Extra Commands -----
    def do_record(self, arg):
        "Save future commands to filename:  RECORD rose.cmd"
        self.file = open(arg, "w")

    def do_stop(self, arg):
        "Stop the recording of commands"
        self.close()

    def do_playback(self, arg):
        "Playback commands from a file:  PLAYBACK rose.cmd"

        with open(arg) as f:
            self.cmdqueue.extend(f.read().splitlines())

    def close(self):
        if self.file:
            self.file.close()
            self.file = None


def parse(arg):
    """Parse the arguments given return a dictionnary or a string containing the organized parts
    Ex : "-height:8 -color:r" ==> {'height':8, 'color':r}"""

    root.debug("Initial arg : {}".format(arg))
    # Args are separated by spaces
    args = arg.split()

    # One arg only : arg is returned directly expect if it's already an option
    if len(args) == 1 and not (args[0].startswith("-") and ":" in args[0]):
        return {"input1": arg}
    else:
        i = 1  # counter for arg with no "-"
        o = 1  # counter for arg with '-' but no ':'
        parsed_args = {}
        add_to_path = None

        # Iteration over the args
        for j, arg in enumerate(args):

            # The arg is a path starting with '"'
            if arg.startswith('"'):
                add_to_path = "input" + str(i)
                key, value = "input" + str(i), arg[1:]
                i += 1

            # The arg is the end of the previous path
            elif arg.endswith('"'):
                parsed_args[add_to_path] += " " + arg[:-1]
                add_to_path = None

            # The arg is the next part of the path
            elif add_to_path is not None:
                parsed_args[add_to_path] += " " + arg

            # The arg starts with "-" and is not an option
            elif arg.startswith("-") and ":" in arg:
                key, value = arg[1:].split(":")
                key = key.lower()

            # The arg is an option
            elif arg.startswith("-"):
                key, value = "option" + str(o), arg[1:]
                o += 1

            # The arg is another kind of input
            else:
                key, value = "input" + str(i), arg
                i += 1

            # Add to dictionary
            parsed_args[key] = value

        # Return
        root.debug("Parsed args : {}".format(parsed_args))
        return parsed_args


if __name__ == "__main__":

    # Main loop
    try:
        townshell = TownShell()
        townshell.cmdloop()
    except KeyboardInterrupt:
        root.warning("TownShell ended with Ctrl+C")
        stream.warning("TownShell interrupted (-_-)")
        townshell.postloop()
    except:
        root.exception("TownShell ended with an error")
        stream.fatal("TownShell Fatal Error system (T_T)")
        townshell.postloop()
        exit(-1)
