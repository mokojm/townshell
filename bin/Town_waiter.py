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
from os.path import abspath, basename, dirname, exists, getmtime, isdir, join, splitext
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
    0: {"name": "red", "coord": (0.925, 0.267, 0.267)},
    1: {"name": "orange", "coord": (0.953, 0.553, 0.357)},
    2: {"name": "yellow", "coord": (0.953, 0.839, 0.400)},
    3: {"name": "yellow_green", "coord": (0.851, 0.914, 0.463)},
    4: {"name": "light_green", "coord": (0.675, 0.765, 0.486)},
    5: {"name": "grass_green", "coord": (0.518, 0.839, 0.384)},
    6: {"name": "green", "coord": (0.271, 0.812, 0.439)},
    7: {"name": "green_blue", "coord": (0.286, 0.784, 0.647)},
    8: {"name": "blue", "coord": (0.286, 0.729, 0.812)},
    9: {"name": "deep_blue", "coord": (0.325, 0.604, 1)},
    10: {"name": "purple", "coord": (0.447, 0.475, 0.812)},
    11: {"name": "mauve", "coord": (0.725, 0.341, 0.459)},
    12: {"name": "beige", "coord": (0.812, 0.667, 0.549)},
    13: {"name": "brown_gray", "coord": (0.698, 0.643, 0.616)},
    14: {"name": "white", "coord": (0.871, 0.871, 0.871)},
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
# def print_colors():

#     for digit, color in ALLCOLORS.items():
#         print("{} ==> {}".format(digit, color))


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
    dictComp = {}  # New arguments
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
            if arg == tuple():
                color_filter = None
            elif isinstance(arg, tuple):
                color_filter = arg
            elif arg.isnumeric():
                color_filter = int(arg)

        # Other arguments
        else:
            dictComp[key] = arg

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
        corvox,
        height,
        coord,
        max_height,
        min_height,
        plain,
        color,
        color_filter,
        **dictComp,
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
    alternate = False

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

        # Alternate
        elif key == "alternate":
            alternate = arg

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
    corvox = paint(
        corvox, color, color_filter, height, column, coord, details, alternate
    )

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
    op = "+"  # Operator for merging
    for i, (name, arg) in enumerate(args.items()):

        # Operator
        if name == "op":
            op = arg
            continue

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
    corvox = merge(op, *toMerge)

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
    maxhf = None
    corner = False

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

        # Corner
        elif key == "corner":
            corner = arg

        # Max height filter
        elif key == "maxhf":
            maxhf = arg

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
    corvox = dig(corvox, color_filter, percent, height, corner, maxhf)

    # Copy to clipboard
    new_clip = corvoxToClip(corvox)

    # Store the new clip
    storeClip(new_clip)

    # Success
    return True


# Fetch all available template for 'Write' and return a dictionary of name vs path
def fetch_templates():

    templatePaths = {}
    with scandir(exePath("templates")) as it:
        for entry in it:
            base, ext = splitext(entry.name)
            if ext == ".txt":
                templatePaths[base] = entry.path

    feedback = read_cfg("write_templates")
    if feedback == []:
        pass
    elif feedback and isinstance(feedback, list):
        for entry in feedback:
            if isdir(entry):
                with scandir(entry) as it:
                    for file in it:
                        base, ext = splitext(file.name)
                        if ext == ".txt":
                            templatePaths[base] = file.path
            else:
                base, ext = splitext(entry)
                if ext == ".txt":
                    templatePaths[basename(base)] = entry
    else:
        root.warning(f"Wrong format : {feedback}")

    return templatePaths


# Write the words in Townscaper
def write_town(**kwargs):

    # Args input
    root.debug(f"Input : {kwargs}")

    # Colors and Background deal
    if kwargs.get("color") == tuple():
        del kwargs["color"]
    if kwargs.get("background") == tuple():
        del kwargs["background"]

    wallpath = kwargs.get("wallpath")
    advanced = kwargs.get("advanced")

    # wallpath = r"temp\TownU7m8kmT0Wu0m2b5A.scape" #temporary
    if wallpath:
        # Determining whether it's .scape file or .txt and how the corvox dictionnary is acquired
        if wallpath.endswith(".scape"):
            corvox, full_content = load(wallpath)
        else:
            with open(wallpath) as file:
                corvox = clipToCorvox(file.read())

        kwargs["corvox"] = corvox

    # Advanced contains additional data
    if advanced and advanced != "":
        try:
            answer = json.loads(advanced)
            root.debug("Output read :\n{}".format(answer))
        except:
            root.exception("Invalid format for Advanced : {}".format(advanced))
            return "'Advanced' format error"

        # Input dictionary is updated with advanced content before wallwrite is called
        kwargs.update(answer)
        root.debug(f"Input after advanced : {kwargs}")

    # Get Template
    getTemplate = kwargs.get("template")  # Option to fetch the template clip
    if getTemplate:
        corvoxToClip(corvox)
        return True

    # # temp
    # font = Figlet(font="6x10")
    # # text = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    # text = "Help\n!!!"
    # dictLetter = {}
    # LINE_LENGTH = 30
    # SPACE_LEN = 4
    # INTERLINE = 2
    # # letter = 'w'
    # root.debug(f"{font.renderText(text)}")
    # # exit(0)

    corvox = wallwrite(**kwargs)

    # Copy to clipboard
    new_clip = corvoxToClip(corvox)

    return True


# Return information about the lastClip
def info_town(filters=None):

    corvox = clipToCorvox(lastClip) if lastClip and isClip(lastClip) else None
    if corvox:
        stats = info(corvox, filters)
        stats["timestamp"] = datetime.now().strftime(TIMESTAMP_FORMAT)
        return stats
    else:
        return "No valid clip", datetime.now().strftime(TIMESTAMP_FORMAT)


# Perform all operations for flipping the town
# copy: "None" the town is just flipped, "Ground" a copy is flipped, leveled and merged with original, "Head" a copy is flipped and the original is leveled
def flip_town(**kwargs):

    root.debug(f"Input : {kwargs}")

    copyMode = kwargs.get("copy")
    copyMode = None if copyMode == "None" else copyMode

    color = kwargs.get("color", 14)
    color = 14 if color == "" else int(color)

    color_filter = kwargs.get("color_filter")
    color_filter = None if color_filter == () else color_filter

    if lastClip is None or isClip(lastClip) is False:
        return
    else:
        char = lastClip

    # The clip saved for undo/redo
    storeClip(char)

    # Corvox from clip
    corvox = clipToCorvox(char)

    if corvox is None:
        return

    # Copy mode
    if copyMode:
        copyCorvox = dictCopy(corvox)
        copyStats = info(corvox)
        if copyStats:
            maxH = copyStats["max_height"]
        else:
            return

    if copyMode == "Ground":
        copyCorvox = level(copyCorvox, maxH, color=color, color_filter=color_filter)

    # Flipping of appropriate data
    corvox = flip(corvox, color, color_filter)

    if copyMode == "Head":
        corvox = level(corvox, maxH, color=color, color_filter=color_filter)

    # Final merging for copyMode
    if copyMode:
        corvox = merge("+", copyCorvox, corvox)

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
        denses = bitsToDense(bits)
        sparses = denseToSparse(denses)
        if bits and denses and sparses:
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

    # Fetch 'townshell.cfg' input for Capture and add Manager objects
    initDict = {
        "bitrate": read_cfg("bitrate"),
        "dirname": read_cfg("dirname"),
        "preset": read_cfg("preset"),
        "loglevel": read_cfg("loglevel"),
        "queue": queue,
        "cqueue": myManager.Queue(),  # Queue objects for communication between process
        "mqueue": myManager.Queue(),  # Queue objects for communication between process
        "synchro": myManager.Event(),  # To allow showcase and capture to start at the same time
    }
    # Initialize the Process

    captureProcess = Process(target=ProcessForCapture, daemon=True, kwargs=initDict)
    captureProcess.start()

    return (
        captureProcess,
        initDict.get("cqueue"),
        initDict.get("mqueue"),
        initDict.get("synchro"),
        myManager,
    )


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


# Fetch from a json the template for town spot
def loadTempTown(path):

    # Checks that the configuration file exists
    if exists(path) is False:
        root.error("{} does not exist.".format(path))
        return

    # Reads the configuration file and store the value in a dictionary
    try:
        dictTown = json.load(open(path))
        root.debug("Output read :\n{}".format(dictTown))
    except:
        root.exception("Invalid format for {}".format(path))
        return

    # Dealing with pictures
    picture = dictTown["picture"]
    dictTown["picture"] = exePath(picture) if exists(exePath(picture)) else ""

    # Return
    return dictTown


# Gather all town spots and return a dictionary name vs dict
def getSpots():
    dictSpots = {}
    with scandir(exePath("spots")) as it:
        for entry in it:
            base, ext = splitext(entry.name)
            if ext == ".json":
                spot = loadTempTown(entry.path)
                if spot:
                    dictSpots[spot["name"]] = spot
                else:
                    root.debug(f"Bad file : {entry.path}")

    # Sorting results
    dictSpots = dict(sorted(dictSpots.items()))

    return dictSpots


# Utility class
class Utility(object):
    def __init__(self):

        self.captureQueue = None  # To send to capture process
        self.mainQueue = None  # To receive from capture process
        self.synchro = None  # For capture and showcase
        self.manager = None

        self.prev_clip = None  # For clipInfo
        self.clipInfo = None

        self.dictSpots = None  # For load

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

        # Load requirement
        self.dictSpots = getSpots()

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
    def write(self, **kwargs):
        return write_town(**kwargs)

    # Fetch templates
    def fetch_templates(self):
        return fetch_templates()

    # Flip
    def flip(self, **kwargs):
        return flip_town(**kwargs)

    # Infos
    def info(self, _, **kwargs):

        global lastClip

        if lastClip != self.prev_clip:
            self.clipInfo = info_town()
            self.prev_clip = lastClip

        return self.clipInfo
