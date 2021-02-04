import json
import sys
import xml.etree.ElementTree as ET
from ast import literal_eval as make_tuple
from ctypes import windll
from datetime import datetime
from getpass import getuser
from glob import glob
from logging import getLogger
from os import mkdir, remove, scandir
from os.path import (abspath, basename, dirname, exists, getmtime, isdir, join,
                     splitext)
from random import choice
from shutil import copy2, get_terminal_size, move
from threading import Event, Thread
from time import sleep

import pyperclip
from bin.Town_clipper import *
from bin.Town_cooker import *
from bin.Town_shortcuts import shortcut
from keyboard import add_hotkey

# Logging options
root = getLogger("Town.waiter")
stream = getLogger("TownStream.waiter")

# Title
TITLE = r"""
 _____                   ____  _          _ _
|_   _|____      ___ __ / ___|| |__   ___| | |
  | |/ _ \ \ /\ / / '_ \\___ \| '_ \ / _ \ | |
  | | (_) \ V  V /| | | |___) | | | |  __/ | |
  |_|\___/ \_/\_/ |_| |_|____/|_| |_|\___|_|_|
  """

# All available colors
ALLCOLORS = {
    0: "red",
    1: "orange",
    2: "yellow",
    3: "yellow_green",
    4: "light_green",
    5: "grass_green",
    6: "green",
    7: "green_blue",
    8: "blue",
    9: "deep_blue",
    10: "purple",
    11: "mauve",
    12: "beige",
    13: "brown_gray",
    14: "white",
}

# To handle .exe treatment
BUNDLE_DIR = getattr(sys, "_MEIPASS", abspath(dirname(__file__)))


def exePath(mypath):
    if exists(mypath):
        return mypath
    elif exists(abspath(join(BUNDLE_DIR, mypath))):
        return abspath(join(BUNDLE_DIR, mypath))
    else:
        return mypath


# The configuration file
TOWNSHELL_PATH = "townshell.cfg"

# Directory of backup
BACKUPTOWN = "backup\\" + datetime.now().strftime("%Y%m%d%H%M%S")

# Directory for temporary storage
TEMP = "temp"

# Timestamp format
TIMESTAMP_FORMAT = "%Y/%m/%d %H:%M:%S"

# Boolean to know whether Keyboard shortcuts are active or not
global active_shortcuts
active_shortcuts = False

# Dictionary for undo and redo
global version
version = {}

# Dictionary of stored clips
global clipHistory
clipHistory = {"previous": [], "current": "", "future": []}

# Directory where all Townscaper saved files are
scapedir = ""

# Print the colors a pretty way
def print_colors():

    for digit, color in ALLCOLORS.items():
        print("{} ==> {}".format(digit, color))


# Fetch the log level from 'townshell.cfg'
def get_loglevel():

    # Checks that townshell.cfg exists
    if exists(TOWNSHELL_PATH) is False:
        myTownshell = copyc(exePath(r"tmp_townshell.cfg"), TOWNSHELL_PATH)
        if myTownshell is None:
            return "INFO"

    loglevel = read_cfg("loglevel")
    if loglevel not in ("INFO", "WARNING", "DEBUG", "ERROR"):
        print("Invalid log level found in 'townshell.cfg'. INFO will be used")

        return "INFO"
    else:
        return loglevel


# Copy a corvox dictionnary so that it's fully independent from the original one
def dictCopy(corvox):
    return {key: dictvalues.copy() for key, dictvalues in corvox.items()}


# Customized copy2 to handle logging constraints
# rename: If True the copy will be renamed in destination if any file with the same name is found
# erase: If True and the file exists in the destination it's erased by the new file
# Note that rename has higher priority than erase so rename=True and erase=True is useless
def copyc(src, dst, rename=False, erase=False):

    # Conversion for comfort
    if isdir(dst):
        dst = join(dst, basename(src))

    # Case the file exists already in destination and rename = True
    if exists(dst) and rename:
        root.warning("%s already exists in %s and will be renamed", src, dst)

        # The renaming is done by adding the current timestamp to basename of the file
        suffix = datetime.now().strftime("%Y%m%d%H%M%S")
        base_src, ext = splitext(basename(src))
        dst = join(dirname(dst), base_src + suffix + ext)

    # Case the file exists already in destination and erase = True
    elif exists(dst) and erase:
        root.warning("%s already exists in %s and will be updated", src, dst)

        # The previous file is stored in TEMP
        try:
            temp = move(dst, TEMP)
        except:
            root.exception("Backup of %s failed, %s will not be copied", dst, src)

            return

    # Case the file exists already in destination and rename = erase = False
    elif exists(dst):
        root.error("%s already exists in %s, no file copied", src, dst)

        return

    # Copy
    try:
        copy2(src, dst)
        root.debug("Successful copy from %s to %s", src, dst)

    except PermissionError:
        root.exception("Copy of %s in %s not allowed", src, dst)

        if erase:
            move(temp, dst)

    except:
        root.exception("Error during copy of %s in %s", src, dst)

        if erase:
            move(temp, dst)

    # When everything is fine
    else:
        # Erase = True
        if erase:
            remove(temp)
            root.debug("Sucessful cleaning of %s", temp)

        # Return
        return dst

    # Erase = True
    if erase:
        move(temp, dst)
        root.debug("Successful rollback on %s", temp)

    # Return failure
    return


# Read TOWNSHELL_PATH and send back the dictionary associated or the value associated with the key given as input
# key: key in townshell.cfg if exists the value is returned
def read_cfg(key=None):

    # Checks that the configuration file exists
    if exists(TOWNSHELL_PATH) is False:
        root.error("{} does not exist.".format(TOWNSHELL_PATH))
        return

    # Reads the configuration file and store the value in a dictionary
    try:
        cfg = json.load(open(TOWNSHELL_PATH))
        root.debug("Output read :\n{}".format(cfg))
    except:
        root.exception("Invalid format for {}".format(TOWNSHELL_PATH))
        return

    # Checks the key, if 'all' the whole dictionary is provided. If None or does not exists, the dictionary is returned
    if key == "all":
        return cfg
    elif key is None or key not in cfg:
        return
    else:
        return cfg[key]


# Update townshell.cfg.
# key: name of the field to update in config file
# value: new value for the spotted key
def update_cfg(key, value):

    # Read of the configuration file to fetch the dictionary cfg
    cfg = read_cfg("all")
    if cfg is None:
        return

    # Checks the format of the value depending on the key
    # Path of the .scape save files, the value must be an existing path
    if key == "scapedir":

        # Path with spaces, when drag and drop might have this look
        if value.startswith('"'):
            value = value[1:-1]

        if exists(value) is False:
            toprint = "'{}' does not exist. Directory of scape saved files not updated".format(
                value
            )
            root.warning(toprint)

            return

        else:
            cfg[key] = value
            global scapedir
            scapedir = value
            root.debug("'{}' is a valid path".format(value))

    # Update of the config file
    try:
        json.dump(cfg, open(TOWNSHELL_PATH, "w"), indent=1)
    except:
        toprint("Error on saving the updated {}".format(TOWNSHELL_PATH))
        root.error(toprint)

    # Final return
    root.info("%s successfully updated", TOWNSHELL_PATH)
    root.debug("Written :\n{}".format(cfg))
    return True


# Identify the directory where all maps are stored by Townscaper
# Return the path if it does exist or None
def find_scapedir():

    # Fetching the current user
    current_user = getuser()

    # Identifying the potential Townscaper save directory
    scapedir = join(
        r"C:\Users", current_user, r"AppData\LocalLow\Oskar Stalberg\Townscaper\Saves"
    )

    # Checking that the directory exists and return
    if exists(scapedir):
        root.info("Townscaper directory is : %s", scapedir)
        return scapedir
    else:
        root.warning("Townscaper directory not found")
        return ""


# Find the saved file that contains the characters given as input
# char: chain of characters
# extended: If True, the amount of corners and voxels are returned too,
def list_scapefiles(char="", extended=False):

    # Case it's obvious
    if exists(char) and extended is False:
        root.debug("%s returned directly", char)
        return [char]

    elif exists(char):
        char = basename(char)

    # Gathering the files
    if char.endswith(".scape"):
        candidates = glob(join(scapedir, "*" + char + "*"))
    else:
        candidates = glob(join(scapedir, "*" + char + "*.scape"))

    # Case nothing found
    if candidates == []:
        root.warning("No Townscaper saved files were found")
        return

    # Other cases

    # Extended extraction
    if extended:
        scapefiles = {}
        for path in candidates:
            # Parsing XML
            tree = ET.parse(path)
            loot = tree.getroot()
            # Amount of corners : coordinates with at list one case filled
            corners = loot.find("corners")
            amount_corners = len(corners.findall("C"))
            # Amount of voxels
            voxels = loot.find("voxels")
            amount_voxels = len(voxels.findall("V"))

            # Adding the data to dictionnary
            scapefiles[basename(path)] = {
                "path": path,
                "date": getmtime(path),
                "corners": amount_corners,
                "voxels": amount_voxels,
            }
        # Return for extended version
        root.debug("{} files returned with extended True".format(len(scapefiles)))
        return scapefiles

    else:
        # Return
        root.debug("{} files returned with extended False".format(len(candidates)))
        return candidates


# Print the townscaper saved files highlighting key information
# max_amount: Number of files to be displayed at most, if None, there are no limits
# args: cmd dictionary when print_scapefiles is used from Cmd
def print_scapefiles(max_amount=5, args=None):

    # Fill the end the input string with spaces according to a given length,
    # if the string is bigger, it's truncated and ended with '...'
    # Convert other type to str
    def fill(string, length):

        # Convert
        if not isinstance(string, str):
            string = str(string)

        # Fill
        if len(string) > length:
            return string[: length - 3] + "..."

        elif len(string) < length:
            return string + " " * (length - len(string))

        else:
            return string

    ####
    # if full print : all columns are printed. Otherwise only file name and modification date are published
    full_print = True

    # Dealing with args
    # No args means default settings are used otherwise the options are taken in charge
    if args == {} or args is None:
        pass
    elif "input1" in args and args["input1"] in ("-a", "-all"):
        max_amount = None

    # Gather all saved files in a dictionary
    scapefiles = list_scapefiles(extended=True)

    # Case list_scapefiles failed
    if scapefiles is None:
        return

    # Saving the length of list_scapefiles, useful for print outs
    len_scapefiles = len(scapefiles)

    # Fetch the max amount of characters for every column
    max_len_name = max([len(name) for name in scapefiles])
    max_len_corners = max(
        [len(str(data["corners"])) for data in scapefiles.values()] + [len("corners")]
    )
    max_len_voxels = max(
        [len(str(data["voxels"])) for data in scapefiles.values()] + [len("voxels")]
    )

    # Size of the column for dates
    len_date_column = len(datetime.now().strftime(TIMESTAMP_FORMAT))

    # Between each column there are 4 spaces
    SPACES = "  |  "
    len_SPACES = len(SPACES)

    # Length of the full print
    full_len = (
        max_len_name
        + len_SPACES
        + len_date_column
        + len_SPACES
        + max_len_corners
        + len_SPACES
        + max_len_voxels
    )
    # Fetch the terminal size
    max_columns = get_terminal_size(fallback=(80, 24))[0]
    # Compare the length of the full print to the terminal size
    if full_len < max_columns:
        len_name_column = max_len_name
        len_corners_column = max_len_corners
        len_voxels_column = max_len_voxels

    else:
        # If the lenght of the files is too much for the terminal, the size of the field for File name is reduced
        # Half of the terminal size is booked for the File name
        len_name_column = round(max_columns / 2)

        # Check that other field together do not take too much place. If it's too much full print is set to false
        part_len = (
            len_SPACES
            + len_date_column
            + len_SPACES
            + max_len_corners
            + len_SPACES
            + max_len_voxels
        )
        if part_len > max_columns / 2:
            full_print = False
            full_len = len_name_column + len_SPACES + len_date_column

        # Full print stay True
        else:
            len_corners_column = max_len_corners
            len_voxels_column = max_len_voxels
            full_len = (
                len_name_column
                + len_SPACES
                + len_date_column
                + len_SPACES
                + len_corners_column
                + len_SPACES
                + len_voxels_column
            )

    # Handling of max_amount and Sort the files, default key is modification date
    if max_amount is None:
        scapefiles = sorted(
            scapefiles.items(), key=lambda x: x[1]["date"], reverse=True
        )
    else:
        scapefiles = sorted(
            scapefiles.items(), key=lambda x: x[1]["date"], reverse=True
        )[:max_amount]

    # Print of the header
    if full_print:
        print(
            "{0}{1}{2}{1}{3}{1}{4}".format(
                fill("File Name", len_name_column),
                SPACES,
                fill("Last update", len_date_column),
                fill("Corners", len_corners_column),
                fill("Voxels", len_voxels_column),
            )
        )

    else:
        print(
            "{0}{1}{2}".format(
                fill("File Name", len_name_column),
                SPACES,
                fill("Last update", len_date_column),
            )
        )

    # Line break
    print("-" * full_len)

    # Iteration on the dictionary items
    for i, (name, file_data) in enumerate(scapefiles):

        # Format of the date
        date_last_update = datetime.fromtimestamp(file_data["date"])
        date_last_update = date_last_update.strftime(TIMESTAMP_FORMAT)

        if full_print is False:
            print(
                "{}{}{}".format(fill(name, len_name_column), SPACES, date_last_update)
            )
            continue

        # Corners and voxels
        amount_corners = file_data["corners"]
        amount_voxels = file_data["voxels"]

        # Print-out for full_print = True
        print(
            "{0}{1}{2}{1}{3}{1}{4}".format(
                fill(name, len_name_column),
                SPACES,
                date_last_update,
                fill(amount_corners, len_corners_column),
                fill(amount_voxels, len_voxels_column),
            )
        )

    # Line break
    print("-" * full_len)

    # Sum up of the file displayed
    if max_amount is None:
        nb_files_displayed = len_scapefiles
    else:
        nb_files_displayed = max_amount
    print(
        "{} saved file(s) // {} file(s) displayed".format(
            len_scapefiles, nb_files_displayed
        )
    )

    # Line break
    print("-" * full_len)

    # Return
    return True


# Initialize Townshell
def init_townshell():

    global scapedir
    global mypid

    # Print Title (deprecated)

    # Fetch the pid of TownShell
    mypid = windll.user32.GetForegroundWindow()

    # Checks for logs
    if exists("log") is False:
        mkdir("log")

    # Archiving of the previous log
    with open("log\\town.log") as logfile:
        with open("log\\town_old.log", "a") as old_logfile:
            old_logfile.write(logfile.read())

    with open("log\\town.log", "w") as logfile:
        logfile.write("")

    # Start of new logging
    root.info("TownShell started")

    # Start clipboard watch
    clipboard_thread = ClipboardThread()
    clipboard_thread.start()

    # Start keyboard shortcuts
    start_shortcuts()

    # Print keyboard shortcuts (deprecated)
    # print_shortcuts()

    # Checks townshell.cfg to find the directory where Townscaper saved files are
    scapedir = read_cfg("scapedir")

    # Checks that scapedir (the directory where Townscaper saved files are stored is filled) is OK
    if isinstance(scapedir, str) and exists(scapedir):
        pass

    else:

        # Case where the value in townshell.cfg does not exist
        if isinstance(scapedir, str) and not exists(scapedir):
            root.warning("scapedir path in townshell.cfg does not exist")

        # Search for scapedir
        # Search through find_scapedir
        scapedir = find_scapedir()

        # Case where the path was not found the user is asked to provide it
        if scapedir == "":
            root.warning("Townscaper saved files directory was not found")
            # scapedir = input(
            #     """Townscaper saved files directory was not found.
            # Drag and drop the directory to the command line or copy-paste the path of the directory
            # Path : """
            # )

            # if scapedir.startswith('"'):
            #     scapedir = scapedir[1:-1]

            # # Case where the provided path is not correct
            # if exists(scapedir) is False:
            #     root.error(
            #         """%s does not exist.
            #     'listfiles' will not work. Please use command 'loadpath' to provide Townscaper saved files directory""",
            #         scapedir,
            #     )
            #     return False

        # Case the path is correct
        update_cfg("scapedir", scapedir)

    # Look for a job to be read and executed (unsafe not checked for a while)
    job_path = read_cfg("job")
    if isinstance(job_path, str) and exists(job_path):
        with open(job_path) as job_file:
            return job_file.read().splitlines()


# Do all operations to level the town as required
# - Checks the args provided
# - Find the file spotted
# - Load the file using function load
# - Level it as required using function level
# - Save it using function save
def level_town(args):

    root.debug(f"Input settings : {args}")

    # Checking the provided args
    # args is a dictionary so we'll analyze each arg one by one
    iter_args = iter(args.items())

    # Then the other args are analyzed
    # Expected input
    char = None  # chain of character of the file to be modified
    height = None
    coord = None
    max_height = 255
    min_height = -1
    plain = False
    color = None
    color_filter = None
    for key, arg in iter_args:

        # File to modify (char)
        if key == "input1":
            char = arg

        # Height
        if key in ("height", "h") and isinstance(arg, int):
            height = arg

        elif key in ("height", "h") and (
            arg.isnumeric() or (arg.startswith("-") and arg[1:].isnumeric())
        ):
            height = int(arg)

        # Coord
        elif key == "coord":
            coord = make_tuple(arg)

        # Max_height
        elif key in ("max_height", "maxh") and isinstance(arg, int):
            max_height = arg

        elif key in ("max_height", "maxh") and arg.isnumeric():
            if int(arg) > 255:
                root.warning(
                    "Invalid max height : %s ; Maximum height cannot exceed 255", arg
                )
            else:
                max_height = int(arg)

        # Min_height
        elif key in ("min_height", "minh") and isinstance(arg, int):
            min_height = arg

        elif key in ("min_height", "minh") and arg.isnumeric():
            if int(arg) > max_height:

                root.warning(
                    "Invalid min height : %s ; Minimum height cannot be superior to maximum height",
                    arg,
                )
            else:
                min_height = int(arg)

        # Plain
        elif key in ("plain", "p") and isinstance(arg, bool):
            plain = arg
        elif key in ("plain", "p"):
            if (arg.isnumeric() and int(arg) > 0) or (arg == "True"):
                plain = True

        # Color
        elif key in ("color", "c"):
            if arg.isnumeric():
                color = int(arg)

        # color_filter
        elif key in ("color_filter", "cf"):
            if arg.isnumeric():
                color_filter = int(arg)

    # Checking that height has been filled
    if height is None:

        root.warning("No valid height was found")
        return

    # PREVIOUSLY: Checking that 'char' has been provided last_modified is used otherwise
    # 2020/11/15 : lastClip is used instead of last_modified if 'char' was not provided
    if char is None and lastClip is None:

        root.info("No valid clip from Townscaper")
        return
    elif char is None:
        char = lastClip

    # Checks if 'char' is a clip
    elif isClip(char) is False:
        return

    storeClip(char)

    # Corvox from clip
    corvox = clipToCorvox(char)
    if corvox is None:
        return

    # Leveling of appropriate data
    root.debug("Input right before leveling : {}".format([height, coord, max_height, min_height, plain, color, color_filter]))
    corvox = level(
        corvox, height, coord, max_height, min_height, plain, color, color_filter
    )

    # Copy to clipboard
    new_clip = corvoxToClip(corvox)

    # Store the new clip
    storeClip(new_clip)

    # Success
    return True


# Do all operations to level the town as required
# - Checks the args provided
# - Paint it as required using function paint
def paint_town(args):

    root.debug(f"Input settings : {args}")

    # Checking the provided args
    # args is a dictionary so we'll analyze each arg one by one
    iter_args = iter(args.items())

    # Then the other args are analyzed
    # Expected input
    char = None  # chain of character of the file to be modified
    color = None
    color_filter = None
    height = None
    column = None
    coord = ()
    details = None

    for key, arg in iter_args:

        # File to modify (char)
        if key == "input1":
            char = arg

        # Color
        if key in ("color", "c"):

            # color is already a tuple
            if isinstance(arg, tuple):
                color = tuple(c for c in arg if c in ALLCOLORS)
            # color is between 0 and 14
            elif arg.isnumeric() and 0 <= int(arg) <= 14:
                color = int(arg)
            # Invalid color digit
            elif arg.isnumeric():
                root.warning(
                    "Color %s is not a valid one ; Color needs to be between 0 and 14 included",
                    arg,
                )
                return
            # Random color
            elif arg.lower() in ("r", "random"):
                color = "random"

            # Color is a tuple like (color1, color2, color3)
            elif "," in arg:
                color = make_tuple(arg)

        # Old color
        elif key in ("color_filter", "cf"):

            if arg == ():
                pass
            # old color is already a tuple
            elif isinstance(arg, tuple):
                color_filter = tuple(c for c in arg if c in ALLCOLORS)
            # old color needs to be between 0 and 14
            elif arg.isnumeric() and 0 <= int(arg) <= 14:
                color_filter = int(arg)

            # Invalid color digit
            elif arg.isnumeric():

                root.warning("Old color %s is not a valid one", arg)

        # Height
        elif key in ("height", "h"):
            if arg is None:
                pass
            elif isinstance(arg, (int, tuple)):
                height = arg
            elif arg.isnumeric():
                height = int(arg)
            elif "," in arg:
                height = make_tuple(arg)

        ###
        # Column, coord and Details are not implemented yet
        ###

    if char is None and lastClip == "":

        root.info("No valid clip from Townscaper")
        return
    elif char is None:
        char = lastClip

    # Checks if 'char' is a clip
    elif isClip(char) is False:
        return

    # The clip saved for undo/redo
    storeClip(char)

    # Corvox from clip
    corvox = clipToCorvox(char)
    if corvox is None:
        return

    # Painting of appropriate data
    root.debug(f"Settings : color :{color}, cf: {color_filter}, height: {height}")
    corvox = paint(corvox, color, color_filter, height, column, coord, details)

    # Copy to clipboard
    new_clip = corvoxToClip(corvox)

    # Store the new clip
    storeClip(new_clip)

    # Success
    return True


# Do all operations to merge the args provided
def merge_town(args):

    root.debug(f"Input settings : {args}")

    toMerge = []
    for i, arg in enumerate(args.values()):

        # Checks that it's an actual clip
        if isClip(arg) is False:
            root.debug(f"Invalid clip : {arg}")
            root.warning("Invalid clip, no merge done")
            return

        # Converts the clip and add it to toMerge
        else:
            toMerge.append(clipToCorvox(arg))

            # The first clip is stored for undo/redo
            if i == 0:
                storeClip(arg)

    # Merging of dict
    corvox = merge(*toMerge)

    # Copy to clipboard
    new_clip = corvoxToClip(corvox)

    # Store the new clip
    storeClip(new_clip)

    # Success
    return True


# Copy a structure to another height a given amount of time
# Shortly, it's the combination of level and merge
def replicate_town(args):

    root.debug(f"Input settings : {args}")

    # Checking the provided args
    # args is a dictionary so we'll analyze each arg one by one
    iter_args = iter(args.items())

    # Then the other args are analyzed
    # Expected input
    char = None  # chain of character of the file to be modified
    copyAmount = 1
    height = None
    max_height = 255
    min_height = -1
    coord = None
    plain = False
    color = None
    color_filter = None
    for key, arg in iter_args:

        # File to modify (char)
        if key == "input1":
            char = arg

        # Amount of copy
        if key in ("copy", "c") and isinstance(arg, int):
            copyAmount = arg
        elif (
            key in ("copy", "c")
            and isinstance(arg, str)
            and (arg.isnumeric() or (arg.startswith("-") and arg[1:].isnumeric()))
        ):
            copyAmount = int(arg)

        # Height
        elif key in ("height", "h") and isinstance(arg, int):
            height = arg

        elif key in ("height", "h") and (
            arg.isnumeric() or (arg.startswith("-") and arg[1:].isnumeric())
        ):
            height = int(arg)

        # Coord
        elif key == "coord":
            coord = make_tuple(arg)

        # Plain
        elif key in ("plain", "p") and isinstance(arg, bool):
            plain = arg
        elif key in ("plain", "p"):
            if (arg.isnumeric() and int(arg) > 0) or (arg == "True"):
                plain = True

        # Color
        elif key in ("color", "c"):
            if arg.lower() in ("r", "random"):
                color = "random"

            elif arg.isnumeric():
                color = int(arg)

        # color_filter
        elif key in ("color_filter", "cf"):
            if arg.isnumeric():
                color_filter = int(arg)

    # Checking that height has been filled
    if height is None:

        root.warning("No valid height was found")
        return

    # PREVIOUSLY: Checking that 'char' has been provided last_modified is used otherwise
    # 2020/11/15 : lastClip is used instead of last_modified if 'char' was not provided
    if char is None and lastClip is None:

        root.info("No valid clip from Townscaper")
        return
    elif char is None:
        char = lastClip

    # Checks if 'char' is a clip
    elif isClip(char) is False:
        return

    storeClip(char)

    # Corvox from clip
    initCorvox = clipToCorvox(char)

    if initCorvox is None:
        return

    toLevel = dictCopy(initCorvox)
    toMerge = [initCorvox]
    thisHeight = 0
    for i in range(copyAmount):

        # The height used for this copy
        thisHeight += height
        if thisHeight > 255:
            break

        # color choice if random has been selected
        thisColor = choice(ALLCOLORS) if color == "random" else color

        # Leveling of appropriate data
        corvox = level(
            toLevel,
            height,
            coord,
            max_height,
            min_height,
            plain,
            thisColor,
            color_filter,
        )

        # Adding the dictionnary to toMerge
        toMerge.append(dictCopy(corvox))
        # root.debug(toMerge)

    # Merge of all dictionnary : if plain is True, the last becomes the first
    if plain:
        toMerge.reverse()

    finalCorvox = merge(*toMerge)

    # Copy to clipboard
    new_clip = corvoxToClip(finalCorvox)

    # Store the new clip
    storeClip(new_clip)

    # Success
    return True


# Do all operations for using dig function
def dig_town(args):

    root.debug(f"Input settings : {args}")

    # Checking the provided args
    # args is a dictionary so we'll analyze each arg one by one
    iter_args = iter(args.items())

    # Then the other args are analyzed
    # Expected input
    char = None  # chain of character of the file to be modified
    color_filter = None
    height = None
    percent = 1

    for key, arg in iter_args:

        # File to modify (char)
        if key == "input1":
            char = arg

        # Percent
        if key in ("percent", "p"):

            if isinstance(arg, (int, float)) and arg <= 100:
                percent = arg / 100
            else:
                root.warning(f"Invalid percent value {percent}")
                return

        # Old color
        elif key in ("color_filter", "cf"):

            if arg == ():
                pass
            # old color is already a tuple
            elif isinstance(arg, tuple):
                color_filter = tuple(c for c in arg if c in ALLCOLORS)
            # old color needs to be between 0 and 14
            elif arg.isnumeric() and 0 <= int(arg) <= 14:
                color_filter = int(arg)

            # Invalid color digit
            elif arg.isnumeric():

                root.warning("Old color %s is not a valid one", arg)

        # Height
        elif key in ("height", "h"):
            if arg is None:
                pass
            elif isinstance(arg, (int, tuple)):
                height = arg
            elif arg.isnumeric():
                height = int(arg)
            elif "," in arg:
                height = make_tuple(arg)

    if char is None and lastClip == "":

        root.info("No valid clip from Townscaper")
        return
    elif char is None:
        char = lastClip

    # Checks if 'char' is a clip
    elif isClip(char) is False:
        return

    # The clip saved for undo/redo
    storeClip(char)

    # Corvox from clip
    corvox = clipToCorvox(char)
    if corvox is None:
        return

    # Digging of appropriate data
    corvox = dig(corvox, color_filter, percent, height)

    # Copy to clipboard
    new_clip = corvoxToClip(corvox)

    # Store the new clip
    storeClip(new_clip)

    # Success
    return True


# Store the clip
def storeClip(clip):
    global clipHistory

    # Duplicate from the current clip are bypassed
    if clip == clipHistory["current"]:
        return
    else:
        clipHistory["previous"].append(clipHistory["current"])
        clipHistory["current"] = clip
        clipHistory["future"] = []


# Fetch the lastclip
def undoClip():

    global clipHistory

    if clipHistory["previous"] != []:

        clipHistory["future"].append(clipHistory["current"])
        clipHistory["current"] = clipHistory["previous"].pop()

        # To clipboard
        pyperclip.copy(clipHistory["current"])

        # Success
        return True

    # No corresponding files
    else:
        root.info(f"No older clip")


# Fetch the last future clip (Yes I don't know how to say it)
def redoClip():

    global clipHistory

    if clipHistory["future"] != []:

        clipHistory["previous"].append(clipHistory["current"])
        clipHistory["current"] = clipHistory["future"].pop()

        # To clipboard
        pyperclip.copy(clipHistory["current"])

        # Success
        return True

    # No corresponding files
    else:
        root.info(f"No newer clip")


# Print the current keyboard shortcuts
def print_shortcuts():

    output = ""

    # Print whether keyboard shortcuts are active or not
    if active_shortcuts:
        output += "Keyboard shortcuts : ON\n"
    else:
        output += "Keyboard shortcuts : OFF\n"

    # Fetch shortcuts
    shortcuts = read_cfg("shortcuts")
    if shortcuts is None:
        return
    shortcuts = iter(shortcuts.items())

    # Shorcut to open TownShell
    output += "Press '²' to open TownShell from Townscaper\n"

    # First shortcuts
    info_printed = False
    for key, value in shortcuts:

        if key.startswith("custom") and info_printed is False:
            output += "\nTo get precise amount of clicks, enter quickly a few digits, then use the custom shortcuts below :\n"
            info_printed = True

        if key == "pause":
            output += f"\nIntervals between clicks (s) : {value}\n"

        else:
            output += f"'{key}' ==> '{value}'\n"

    # How to modify shortcuts
    output += "Shortcuts and intervals can be modified in 'townshell.cfg'\n"

    # Output is directly printed by default but can be returned
    return output


# Class of Thread to have shortcuts handled in another thread
class ShortcutThread(Thread):
    def __init__(self, event):  # event = objet Event
        Thread.__init__(self)
        self.event = event
        self.daemon = True

    def run(self):
        global mypid

        # Hotkeys
        myShortcuts = read_cfg("shortcuts")
        add_hotkey(myShortcuts["undo_command"], undoClip, args=[], suppress=True)
        add_hotkey(myShortcuts["redo_command"], redoClip, args=[], suppress=True)

        # Fetch the keyboard shortcuts settings from townshell.cfg
        shortcut(self.event, myShortcuts, mypid)


# Start a thread activating the keyboard shortcuts
def start_shortcuts():

    # Event that determine whether keyboard shortcuts should be active or not
    global stopnow
    global active_shortcuts

    # Checking that another thread is not executed already
    if active_shortcuts:
        root.warning("Keyboard shortcuts are already activated")
        return

    # Initialize the event that control whether shortcuts are active or not
    stopnow = Event()
    stopnow.clear()

    # Main program
    new_thread = ShortcutThread(stopnow)
    new_thread.start()
    active_shortcuts = True

    root.info("Keyboard shortcuts are now active")

    # Success
    return True


# Stop the thread handling the shortcuts
def stop_shortcuts():

    global stopnow
    global active_shortcuts

    # Checking that another thread is not executed already
    if active_shortcuts is False:
        root.warning("No shortcuts activated")
        return

    # The event is activated and shortcuts is stopped
    stopnow.set()
    active_shortcuts = False

    root.info("Keyboard shortcuts have been deactivated")

    # Success
    return True


# Return True if the provided string is a clip
# Only bits and dense are checked assuming that it's enough to check
def isClip(clip):

    try:
        bits = clipToBits(clip)
        if bits and bitsToDense(bits):
            return True
        else:
            return False

    except:
        root.exception("Error in isclip but let's keep working")
        return False


# Thread that checks whether TownShell is the active application and checks the content of the clipboard
# NOTE : The implementation could change the "Groups" features are implemented (TODO)
class ClipboardThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True

    def run(self):

        global mypid
        global lastClip
        lastClip = None
        prev_clip = ""

        while True:
            # Fetch the foreground application
            cur_foreground = windll.user32.GetForegroundWindow()

            if mypid == cur_foreground:

                # The clipboard is checked
                clip = pyperclip.paste()

                # Check that it's a valid clip from Townscaper
                if clip and prev_clip != clip and isClip(clip):

                    lastClip = clip

            # Wait between loops
            prev_clip = clip
            sleep(0.5)


# Transform a dictionary corvox to string and copy it to clipboard
def corvoxToClip(corvox):

    dense = sparseToDense(corvoxToSparse(corvox))
    bits = denseToBits(dense) if dense else None
    clip = bitsToClip(bits) if bits else None

    if clip:
        pyperclip.copy(clip)
        root.info("Corvox copied on clipboard")

        return clip
    else:

        root.error(
            "Copy for 'Load from Clipboard' failed. Set DEBUG on 'loglevel' in 'townshell.cfg' and try again for more information"
        )
        return


# Transform a clipboard content of Townscaper into a corvox dictionary
def clipToCorvox(clip):

    bits = clipToBits(clip)
    dense = bitsToDense(bits) if bits else None
    sparse = denseToSparse(dense) if dense else None
    corvox = sparseToCorvox(sparse) if sparse else None

    if corvox:
        return corvox
    else:

        root.error(
            "Invalid clipboard content. Set DEBUG on 'loglevel' in 'townshell.cfg' and try again for more information"
        )
        return
