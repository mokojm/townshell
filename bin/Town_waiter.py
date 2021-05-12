import json
import logging
import logging.handlers
import re
import sys
import xml.etree.ElementTree as ET
from ast import literal_eval as make_tuple
from ctypes import windll
from datetime import datetime
from getpass import getuser
from glob import glob
from logging import getLogger
from multiprocessing import Manager, Process, Queue
from os import environ, mkdir, remove, scandir
from os.path import (abspath, basename, dirname, exists, getmtime, isdir, join,
                     splitext)
from queue import Empty
from random import choice
from shutil import copy2, get_terminal_size, move
from threading import Event, Thread
from time import sleep, time

import pyperclip
from bin.Town_capture import *
from bin.Town_clipper import *
from bin.Town_cooker import *
from bin.Town_logger import *
from bin.Town_shortcuts import getTownscaperPid, setForeground, shortcut
from bin.Town_tools import *
from keyboard import add_hotkey, is_pressed

# Logging options
global root  # Will be initialized par initLogging
# root = getLogger("Town.waiter")
# stream = getLogger("TownStream.waiter") #to be deleted

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


# Initialize logging
# Since there are multiple processes started by Townshell, a QueueHandler is used to gather log messages and a listener will write all informations in that queue to a FileHandler
def initLogging():

    # Logger in this module
    global root
    global queue
    global listener

    # Logging objects
    if exists("log") is False:
        mkdir("log")

    # Archiving of the previous log
    if exists("log\\town.log"):
        with open("log\\town.log", encoding="utf-8") as logfile:
            with open("log\\town_old.log", "a", encoding="utf-8") as old_logfile:
                old_logfile.write(logfile.read())

    with open("log\\town.log", "w") as logfile:
        logfile.write("")

    # Fetch log level
    loglevel = get_loglevel()

    # Start the listener
    queue = Queue(-1)
    listener = Process(target=listenerProcess, args=(queue, listenerConfigurer))
    listener.start()

    # Initialize the worker for Town_waiter, cooker, shortcuts, clipper and table
    workerConfigurer(queue)
    root = getLogger("Town.waiter")


# Stop the listener and wait for him to finish processing
def endLogging():

    global queue
    global listener
    queue.put_nowait(None)
    listener.join()


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

    # Initialize capture module

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
    root.debug(
        "Input right before leveling : {}".format(
            [height, coord, max_height, min_height, plain, color, color_filter]
        )
    )
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


# Write the words in Townscaper
def write_town(args=None):

    from pyfiglet import Figlet

    wallpath = r"temp\TownU7m8kmT0Wu0m2b5A.scape"

    # temp
    font = Figlet(font="6x10")
    # text = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    text = "Help\n!!!"
    dictLetter = {}
    LINE_LENGTH = 30
    SPACE_LEN = 4
    INTERLINE = 2
    # letter = 'w'
    root.debug(f"{font.renderText(text)}")
    # exit(0)
    def prepare_text(text, font, INTERLINE, SPACE_LEN, LINE_LENGTH):

        # Strip unecessary spaces over and below letters
        def finilize_line(dico, linenb, align="left"):
            root.debug(dico)

            minStart = 1000
            minEnd = 1000
            minCursor = LINE_LENGTH
            maxCursor = 0

            # Determine minimum empty space over and below letter for a given line
            for line in dico.values():
                for word in line.values():
                    for letter in word.values():
                        if (
                            "line" not in letter
                            or "empty_start" not in letter
                            or "empty_end" not in letter
                            or letter["line"] != linenb
                        ):
                            continue
                        else:
                            minStart = min(letter["empty_start"], minStart)
                            minEnd = min(letter["empty_end"], minEnd)

                            minCursor = min(minCursor, letter["cursor"])
                            maxCursor = max(
                                maxCursor, letter["cursor"] + len(letter["content"][0])
                            )

            root.debug((minStart, minEnd))

            # Strip common useless spaces over and below letters for a given line
            midCursor = round(
                (LINE_LENGTH - (maxCursor - minCursor)) / 2
            )  # cursor if align == 'mid'
            rCursor = LINE_LENGTH - (
                maxCursor - minCursor
            )  # cursor if align == 'right'
            for line in dico.values():
                for word in line.values():
                    for letter in word.values():
                        if "line" not in letter or letter["line"] != linenb:
                            continue
                        else:
                            letter["content"] = (
                                letter["content"][minStart:-minEnd]
                                if minEnd > 0
                                else letter["content"][minStart:]
                            )
                            lenLetter = len(letter["content"][0])
                            letter["cursor"] += (
                                midCursor
                                if align == "mid"
                                else rCursor
                                if align == "right"
                                else 0
                            )

            root.debug("fin")
            root.debug(
                f"line_lengh, maxCursor, mincursor : {(LINE_LENGTH, maxCursor, minCursor)}"
            )
            root.debug(dico)

            return minStart, minEnd

        # Modify the cursor and line number for letter in dictionnary according to new initial position
        def re_configure(dictWord, line, posi=0):
            root.debug(dictWord)
            pos = posi
            for letter in dictWord.values():
                if "line" not in letter:
                    continue
                else:
                    lenLetter = len(letter["content"][0])
                    letter.update({"line": line, "cursor": pos})
                    pos += lenLetter + INTERLETTER

            return pos

        ################################

        # LINE_LENGTH = 50
        MAX_HEIGHT = 255
        INTERLINE = 3
        INTERWORD = 4
        INTERLETTER = 1

        wordWrap = True
        align = "mid"  # left by default, or mid, or right
        cursor = 0
        height = 1
        curLine = 1
        heightLine = 1

        myDict = {(i, line): {} for i, line in enumerate(text.splitlines())}
        lineVsHeight = {}  # Height associated with Lines
        lineVsHeight[curLine] = height

        ## Dealing with each line
        for c1, (i, line) in enumerate(myDict):

            if c1 != 0:
                minS, minE = finilize_line(myDict, curLine, align)
                heightLine = heightLine - minS - minE
                height += heightLine + INTERLINE
                curLine += 1
                cursor = 0

            heightLine = 1

            if height > MAX_HEIGHT:
                break

            myDict[(i, line)] = {(j, word): {} for j, word in enumerate(line.split())}

            lineDict = myDict[(i, line)]

            ## Dealing with each word
            for c2, (j, word) in enumerate(lineDict):

                wordWrapTriggered = True if cursor == 0 else False

                if c2 != 0:
                    cursor += INTERWORD

                lineDict[(j, word)] = {(k, letter): {} for k, letter in enumerate(word)}

                wordDict = lineDict[(j, word)]

                ## Dealing with each letter
                for c3, (k, letter) in enumerate(wordDict):

                    if c3 != 0:
                        cursor += INTERLETTER

                    wordDict[(k, letter)] = {"cursor": cursor}

                    # Render the letter and identify and delete unecessary spaces
                    renderLines = font.renderText(letter).splitlines()

                    # Delete empty lines
                    spaceStart = spaceEnd = len(renderLines[0])
                    oneCharFound = False
                    emptyLineStart = emptyLineEnd = 0
                    for line in renderLines.copy():

                        emptyLineBool = True if line == " " * len(line) else False
                        emptyLineStart += (
                            1 if emptyLineBool and oneCharFound == False else 0
                        )
                        emptyLineEnd = (
                            emptyLineEnd + 1 if emptyLineBool and oneCharFound else 0
                        )

                        # Looking for starting and ending spaces
                        matchStart = re.search(r"\A(\s+)\S+", line)
                        matchEnd = re.search(r"\S+(\s+)\Z", line)
                        spaceStart = min(
                            spaceStart,
                            len(matchStart[1])
                            if matchStart is not None
                            else len(line)
                            if emptyLineBool
                            else 0,
                        )
                        spaceEnd = min(
                            spaceEnd,
                            len(matchEnd[1])
                            if matchEnd is not None
                            else len(line)
                            if emptyLineBool
                            else 0,
                        )

                        if matchStart is not None or matchEnd is not None:
                            oneCharFound = True

                    # Deleting spaces at the end and begining
                    root.debug(f"s,e : {spaceStart, spaceEnd}")
                    renderLines = (
                        list(map(lambda x: x[spaceStart:-spaceEnd], renderLines))
                        if spaceEnd != 0
                        else list(map(lambda x: x[spaceStart:], renderLines))
                    )

                    cursor += len(renderLines[0])
                    heightLine = max(len(renderLines), heightLine)

                    # Dealing with length of line
                    if cursor > LINE_LENGTH:

                        if wordWrap and wordWrapTriggered is False:
                            nextLineCursor = re_configure(wordDict, curLine + 1)
                            wordWrapTriggered = True
                        else:
                            nextLineCursor = 0

                        minS, minE = finilize_line(myDict, curLine, align)
                        heightLine = heightLine - minS - minE
                        lineVsHeight[curLine] = height
                        height += heightLine + INTERLINE
                        if height > MAX_HEIGHT:
                            wordOK = True
                            break
                        else:
                            heightLine = len(renderLines)
                            cursor = nextLineCursor
                            curLine += 1
                            wordDict[(k, letter)] = {"cursor": cursor}
                            cursor += len(renderLines[0])

                    # Adding to dictionnary
                    wordDict[(k, letter)].update(
                        {
                            "content": renderLines,
                            "line": curLine,
                            "empty_start": emptyLineStart,
                            "empty_end": emptyLineEnd,
                        }
                    )
                    lineVsHeight[curLine] = height
                    root.debug(f"letter {letter}, {wordDict[(k, letter)]}")
                    root.debug(f"lineVsHeight : {lineVsHeight}")

        # Last operations
        minS, minE = finilize_line(myDict, curLine, align)
        heightLine = heightLine - minS - minE
        lineVsHeight[curLine] = height
        heightTot = height + heightLine

        root.debug(f"myDict : {myDict}")
        root.debug(f"lineVsHeight : {lineVsHeight}")
        # Creation of map of characters
        finalDict = {}
        for (i, line), lineDict in myDict.items():
            for (j, word), wordDict in lineDict.items():
                for (k, letter), letterDict in wordDict.items():
                    heightLetter = len(letterDict["content"])
                    for m, line in enumerate(letterDict["content"]):
                        for n, char in enumerate(line):
                            x = letterDict["cursor"] + n
                            y = heightTot - lineVsHeight[letterDict["line"]] - m
                            finalDict[(letter, x, y)] = 1 if char not in (" ",) else 0

        root.debug(f"finalDict : {finalDict}")
        return finalDict

    def wallwrite(
        wallpath,
        text,
        color=10,
        plain=False,
        background=14,
        centered=False,
        flying=False,
        line_length=None,
        max_height=None,
    ):

        # Fetching wallpath
        dico_corvox, full_content = load(wallpath)

        # Maximum line length
        max_line_length = len(dico_corvox)
        if line_length is None or line_length > max_line_length:
            line_length = max_line_length
            print()

        # Prepare the text
        dictext2 = prepare_text(text, font, INTERLINE, SPACE_LEN, line_length)
        dictext = {(x, y): value for (l, x, y), value in dictext2.items()}
        length_text = max([x for x, y in dictext])
        height_text = max([y for x, y in dictext])

        # Determine the start of the writing
        # Get the max length of prepared words
        startl = 0
        endl = startl + length_text
        starth = 1
        endh = starth + height_text

        if centered:
            startl = round(max_line_length / 2 - length_text / 2)
            endl = round(max_line_length / 2 + length_text / 2)

        max_height = (
            endh + 1
        )  # +1 is here to have at least one line over the words when plain=True
        if flying:
            if max_height is None or max_height < height_text:
                max_height = height_text * 2

            starth = round(max_height / 2 - height_text / 2)
            endh = round(max_height / 2 + height_text / 2)

        # Browse dico_corvox
        # A copy of dico_corvox is iterated
        # Warning! count_and_voxels even it's a copy will point the actual item of dico_corvox
        dico_corvox_copy = dico_corvox.copy()
        for l, ((x, y), count_and_voxels) in enumerate(dico_corvox_copy.items()):

            cur_voxels = count_and_voxels["voxels"]
            new_voxels = {}
            if l < startl or l > endl:
                pass

            else:
                for h in range(max_height):
                    # color choice
                    if color == "random":
                        t = choice([co for co in ALLCOLORS if co != background])
                    else:
                        t = color

                    if h == 0 and plain:
                        new_voxels[h] = 15

                    elif h > endh and plain is False:
                        break

                    elif h < starth and plain is False:
                        pass

                    elif (l - startl, h - starth) in dictext and dictext[
                        (l - startl, h - starth)
                    ]:
                        if color == "empty":
                            pass
                        else:
                            new_voxels[h] = t

                    elif plain:
                        if background == "random":
                            new_voxels[h] = choice(
                                [co for co in ALLCOLORS if co != color]
                            )
                        else:
                            new_voxels[h] = background

            # "Count" adjustment according to the amount of voxels
            dico_corvox[(x, y)]["count"] = len(new_voxels)
            dico_corvox[(x, y)]["voxels"] = new_voxels

        # Return
        return dico_corvox

    corvox = wallwrite(wallpath, text, plain=False, color=0)

    # Copy to clipboard
    new_clip = corvoxToClip(corvox)


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
    output += "Press 'tab' to open TownShell from Townscaper\n"

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


def processCmd(myCapture, mainQueue, synchro, command, value):
    """Function designed to handle communication between main process and capture process"""
    root.debug(f"Input : {(command, value)}")
    # Dealing with received command
    if command == "FPS":
        myCapture.target_fps = value
    elif command == "Dirname":
        myCapture.dirname = value
    elif command == "Region":
        myCapture.region = value
    elif command == "Start Recorder":
        myCapture.start_recorder()
    elif command == "Capture":
        duration = value

        # We wait for showcase to release the Lock
        synchro.wait()
        sleep(0.04)

        # Lock acquired by showcase, capture can start
        duration = (
            3 * duration
        )  # Not very clean but the purpose is to have enough time for showcase to send the end signal
        start = time()
        count = 0
        while "capture ongoing":

            if time() - start > duration:
                break

            elif not synchro.is_set():  # Showcase will set it False when it's finished
                break

            else:
                myCapture.shotoqueue()
                count += 1

        # FPS
        fps = round(count / (time() - start))

    elif command == "Window size":
        mainQueue.put(("Window size", myCapture.size))

    # Dealing with Capture and Force Stop
    if command in ("Capture",):
        myCapture.stop_recorder()

        while myCapture.is_recording:  # Waiting time
            sleep(0.1)
        mainQueue.put(("End Record", fps))


def ProcessForCapture(cqueue, mqueue, queue, synchro, **kwargs):
    """Process handling capture instance creation and keeping alive"""

    # Initialize logging worker
    workerConfigurer(queue)
    root = getLogger("Town.waiter")

    # Main Capture Process
    try:
        with TownCapture(**kwargs) as myCapture:
            root.debug("Towncapture module started")
            while True:

                infos = cqueue.get()
                root.debug(f"Infos received : {infos}")

                if isinstance(infos, tuple) and isinstance(infos[0], tuple):
                    for command, value in infos:
                        processCmd(myCapture, mqueue, synchro, command, value)
                elif isinstance(infos, tuple):
                    command, value = infos
                    processCmd(myCapture, mqueue, synchro, command, value)
                else:
                    continue
    except:
        root.exception(
            "An error occured in Capture process. Restart TownShell to try using Capture again or activate 'DEBUG' in 'townshell.cfg' to raise a ticket to the dev for investigation puposes"
        )


# Initialize capture object
def initTownCapture():

    global queue  # for logging
    
    myManager = Manager()
  
    #Fetch 'townshell.cfg' input for Capture and add Manager objects
    initDict = {
    'bitrate': read_cfg('bitrate'),
    'dirname': read_cfg('dirname'),
    'preset': read_cfg('preset'),
    'loglevel': read_cfg('loglevel'),
    'queue': queue,
    'cqueue': myManager.Queue(),  # Queue objects for communication between process
    'mqueue': myManager.Queue(),     # Queue objects for communication between process
    'synchro': myManager.Event(),       # To allow showcase and capture to start at the same time
    } 
    # Initialize the Process
    
    captureProcess = Process(
        target=ProcessForCapture,
        daemon=True,
        kwargs=initDict
    )
    captureProcess.start()

    return captureProcess, initDict.get('cqueue'), initDict.get('mqueue'), initDict.get('synchro'), myManager


# Short function to get window size used by Townscaper
def getTownRegion(cqueue, mqueue):
    cqueue.put(("Window size", ""))

    # Waiting for the answer
    try:
        answer = mqueue.get(timeout=3)
        if isinstance(answer, tuple) and answer[0] == "Window size":
            return answer[1]
        else:
            root.debug(f"Unexpected answer : {answer}")
            return

    except Empty:
        root.debug("Nothing returned")
        return


# Given an Event will set it to False if RAM exceed limit % usage
def monitorRAM(limit, event, ramIssue):
    event.wait()  # Monitoring is waiting for showcase to start working to monitor RAM
    while event.is_set():
        if virtual_memory().percent > limit:
            ramIssue.set()
            event.clear()
        sleep(0.5)


# Main function for capturing pictures from Townscaper
# def doCapture(capturePipe, dirname, fps, button, start, pixels, duration, angle, rythm, region=None, dryrun=False) #previous declaration
def doCapture(**kwargs):

    cqueue, mqueue = kwargs["cqueue"], kwargs["mqueue"]
    dryrun = kwargs["dryrun"]

    # Checking there is a Townscaper application running
    if not getTownscaperPid():
        return "No Townscaper application found"

    # Get the window size of Townscaper
    windowSize = getTownRegion(cqueue, mqueue)
    root.debug(f"WindowSize : {windowSize}")
    kwargs["region"] = kwargs.get(
        "region", windowSize
    )  # Region contains either a setting from the user or Townscaper window size
    root.debug(f"kwargs : {kwargs}")

    # Region cannot be None
    if kwargs["region"] is None:
        return "No valid region were found"

    # Checks that it's showcasable
    decision = isShowcasable(kwargs["pixels"], kwargs["duration"])
    root.debug(f"isShowcasable: {decision}")
    if decision is True:
        pass
    else:
        return decision

    # Fetch the RAM limit and starts ram monitoring
    if dryrun is False:
        ramIssue = Event()
        ramLimit = read_cfg("ram_limit")
        ramLimit = ramLimit if ramLimit else 93
        curRAM = virtual_memory().percent
        if curRAM > ramLimit:
            return f"Not enough RAM, missing percents : {round(curRAM - ramLimit)} %"
        Thread(target=monitorRAM, args=(ramLimit, kwargs["synchro"], ramIssue)).start()

    # Send the parameters first
    if dryrun is False:
        if kwargs["region"]:
            cqueue.put(
                (
                    ("FPS", kwargs["fps"]),
                    ("Dirname", kwargs["dirname"]),
                    ("Region", kwargs["region"]),
                    ("Start Recorder", ""),
                    ("Capture", kwargs["duration"]),
                )
            )
        else:
            cqueue.put(
                (
                    ("FPS", target_fps),
                    ("Dirname", kwargs["dirname"]),
                    ("Start Recorder", ""),
                    ("Capture", kwargs["duration"]),
                )
            )

    # set Townscaper foreground
    setForeground()

    # Starts showcase mouse if pixels != 0
    if kwargs["pixels"] == 0:
        kwargs["synchro"].set()
        answer = "Let's take a break :)"
        sleep(kwargs["duration"])
    else:
        answer = showcase(**kwargs)

    kwargs["synchro"].clear()

    # set Townshell back foreground
    setForeground()

    if dryrun is False:
        try:
            answer = mqueue.get(timeout=kwargs["duration"] * 3)
            if isinstance(answer, tuple) and answer[0] == "End Record":
                if ramIssue.is_set():
                    return f"maximum RAM reached, FPS : {answer[1]}"
                else:
                    return answer[1]  # Actual FPS is returned

        except Empty:
            return "Rendering was either too long or an error occured"
    else:
        return answer


# Utility class
class Utility(object):
    def __init__(self):

        self.captureQueue = None  # To send to capture process
        self.mainQueue = None  # To receive from capture process
        self.synchro = None  # For capture and showcase
        self.manager = None

        self.init_core()
        self.shortcuts = print_shortcuts()

    # Shortcuts management
    def activate_shortcuts(self):
        out = start_shortcuts()
        self.shortcuts = print_shortcuts()
        return out

    def deactivate_shortcuts(self):
        out = stop_shortcuts()
        self.shortcuts = print_shortcuts()
        return out

    def get_shortcuts(self):
        return self.shortcuts

    # Call level_town from Town_waiter
    def level(self, settings):

        return level_town(settings)

    # Call merge_town from Town_waiter
    def merge(self, settings):

        return merge_town(settings)

    # Call dig_town from Town_waiter
    def dig(self, settings):

        return dig_town(settings)

    # Call replicate_town from Town_waiter
    def replicate(self, settings):

        return replicate_town(settings)

    # Call paint_town from Town_waiter
    def paint(self, settings):

        return paint_town(settings)

    # Call isClip fron Town_waiter
    def isclip(self, clip):
        return isClip(clip)

    # Initiate TownShell core
    def init_core(self):

        # Part working with clip (level, paint, ...)
        init_townshell()
        # Capture part
        (
            _,
            self.captureQueue,
            self.mainQueue,
            self.synchro,
            self.manager,
        ) = initTownCapture()

    # Terminate TownShell core
    def end_core(self, issue=False):

        # (temporary) stop logging
        endLogging()

    # Capture
    def capture(self, **kwargs):
        return doCapture(**kwargs)

    # Showcasable
    def isShowcasable(self, *args):
        return isShowcasable(*args)

    # Undo
    def undo(self):
        return undoClip()

    # Redo
    def redo(self):
        return redoClip()

    # Write
    def write(self, settings):
        return write_town()
