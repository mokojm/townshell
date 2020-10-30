# ----- Structure of TownShell -----
# Town_table initialize logging and contains the commands availables for users
# Town_waiter is the core for handling commands passed by user, manage files and interact with the module Town_cooker and Town_shortcuts
# Town_cooker contains all functions that actually modify Townscaper saved files
# Town_shortcuts handles all functions necessary for keyboard shortcuts
# The configuration like the path where Townscaper files are saved are in townshell.cfg

import logging
import sys
from cmd import Cmd
from os import environ, mkdir
from os.path import exists

from Town_waiter import *

# Logging objects
# Main logger
if exists('log') is False: mkdir('log')
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
- listfiles <option> ==> List the Townscaper saved files available
- level <file> -height:<n> ==> Modify the height of your structure according to <n>
- paint <file> -color:<n> ==> Modify the color of your structure according to <n>
- colors ==> Print colors and their corresponding digits
- undo <file> ==> Undo the last change for the targeted file
- redo <file> ==> Redo the last change for the targeted file
See help <cmd> to get more information about a specific command
Type help or ? to list all commands.\n"""

    intro = "\nWelcome to TownShell !\n" + main_command
    prompt = "T> "
    file = None
    completekey='tab'

    def preloop(self):
        """Initialize the data
        - Fetch the directory of Townscaper saved files
        - List all saved files if found
        - Update backup of saved files"""
        job = init_townshell()

        # Job to be executed
        if isinstance(job, list):
            self.cmdqueue.extend(job)

    def postloop(self):
        """End of the loop, keyboard shortcuts are stopped"""
        stop_shortcuts()

    def precmd(self, line):
        """Log the command passed and checks that scapedir is defined"""
        root.info("cmd : %s", line)

        # A few checks are made
        # - if cmd is load_path no check is done
        # - if the path to saved files is not well defined in townshell.cfg
        # - if cmd modify the file (level, paint, ...) a check on last modified file is done
        if check_stuff(line):
            return line
        else:
            # An empty line is returned if the check is not successful
            return ""

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
        """level <file> -height:<n> -max_height:<n> - min_height:<n> -plain:<0/1> -color:<n> -color_filter:<n> -new_file:<file> ==> Modify the height of your structure according to <n>
        <file> : [optional] Name of the file to be modified. Can be a path. Can be a chain of characters, the first file corresponding is used
        height (h): [mandatory] The height that will be added to the selected structure. Can be negative, the height of the structure will be decreased
        max_height (maxh): [optional] The maximum height for all building in the structure.
        min_height (minh): [optional] The minimum height for all building in the structure.
        plain (p): [optional] If 0 or not filled, the space below the elevated building stays empty. If 1, the created spaces are filled
        color (c): [optional] color (between 1 and 14) that will be applied to the newly created blocks. If not filled, the potential new blocks will take the color of the first colored one above them (or the default color if no blocks above them).
        color_filter (cf): [optional] Only the blocks having this color (between 1 and 14) will be affected by this command
        new_file (nf): [optional] Instead of updating the original file, a new one is created. Can be anything"""
        parsed_args = parse(arg)
        level_town(parsed_args)

    def do_paint(self, arg):
        """paint <file> -color:<multi> -color_filter:<n> -height:<multi> -new_file:<file> ==> Modify the color of your structure according to <n>
        <file> : [optional] Name of the file to be modified. Can be a path. Can be a chain of characters, the first file corresponding is used
        color (c): [mandatory] The color (between 1 and 14) that will be applied to the selected blocks. Can be 'r' for random color. Can be (n,m,p) for random choice between n,m and p
        color_filter (cf): [optional] Only the blocks with that color will be modified
        height (h): [optional] Can be a positive integer. Only the blocks at that height will be affected. Can be (n,m,p) only the blocks at these height will be affected. Can be ((n,m),(p,q)). Only the blocks between height n and m, and between p and q will be affected
        new_file (nf): [optional] Instead of updating the original file, a new one is created. Can be anything"""
        parsed_args = parse(arg)
        paint_town(parsed_args)

    def do_backup(self, arg):
        """backup <file> ==> Create a copy of all Townscaper saved files in directory 'backup'. Erase the previous ones
        <file> : [optional] Name of the file to be modified. Can be a path. Can be a chain of characters
        You can use 'backup -all' or 'backup -a' to apply backup operation to all saved files from Townscaper
        If no target file, the last file modified by Townshell is used"""
        parsed_args = parse(arg)
        backup(pprint=True, args=parsed_args)

    def do_restore(self, arg):
        """restore <file> ==> Restore a file or all Townscaper saved files to their last backup state
        <file> : [optional] Name of the file to be modified. Can be a path. Can be a chain of characters, the first file corresponding is used
        You can use 'restore -all' or 'restore -a' to apply restore operation to all saved files from Townscaper
        If no target file, the last file modified by Townshell is used"""
        parsed_args = parse(arg)
        restore(parsed_args)

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
        """Undo the last change for the targeted file
        If no target file, the last modified file is used"""
        parsed_args = parse(arg)
        undo(parsed_args)

    def do_redo(self, arg):
        """Redo the last change for the targeted file
        If no target file, the last modified file is used"""
        parsed_args = parse(arg)
        redo(parsed_args)

    # def do_copy(self, arg):
    # """Copy all voxels or a group of voxels to a chosen height"""

    # def do_mix(self, arg):
    #     """Mix the voxels of several files"""

    # def do_select(self, arg):
    #     """Save a group of voxels according to height or color and attribute a number"""

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
