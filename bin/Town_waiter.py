import json
import xml.etree.ElementTree as ET
from ast import literal_eval as make_tuple
from datetime import datetime
from getpass import getuser  # Used in find_scapedir
from glob import glob
from logging import getLogger
from os import mkdir, remove, scandir  # Used in list_scapefiles
from os.path import basename  # Used in find_scapedir and list_scapefiles
from os.path import dirname, exists, getmtime, isdir, join, splitext
from shutil import copy2, get_terminal_size, move
from threading import Event, Thread

from Town_cooker import *
from Town_shortcuts import shortcut

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

# Last modified Townscaper saved file path
global last_modified
last_modified = ""

# Directory where all Townscaper saved files are
scapedir = ""

# Return the path of the last modified Townscaper saved file
def get_last_modified():
    global last_modified
    return last_modified


# Update the last modified townscaper saved file path
def set_last_modified(path):
    global last_modified
    last_modified = path


# Print the colors a pretty way
def print_colors():

    for digit, color in ALLCOLORS.items():
        print("{} ==> {}".format(digit, color))

# Fetch the log level from 'townshell.cfg'
def get_loglevel():

    loglevel = read_cfg('loglevel')
    if loglevel not in ("INFO", "WARNING", "DEBUG", "ERROR"):
        print("Invalid log level found in 'townshell.cfg'. INFO will be used")
        return "INFO"
    else:
        return loglevel

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
            stream.error("Copy of %s failed", src)
            return

    # Case the file exists already in destination and rename = erase = False
    elif exists(dst):
        root.error("%s already exists in %s, no file copied", src, dst)
        stream.error("%s already exists in %s, no file copied", src, dst)
        return

    # Copy
    try:
        copy2(src, dst)
        root.debug("Successful copy from %s to %s", src, dst)

    except PermissionError:
        root.exception("Copy of %s in %s not allowed", src, dst)
        stream.error(
            "Copy of %s in %s not allowed, the file was copied. check 'town.log' for more details",
            src,
            dst,
        )
        if erase:
            move(temp, dst)

    except:
        root.exception("Error during copy of %s in %s", src, dst)
        stream.error(
            "Error during copy of %s in %s. Check 'town.log' for more details", src, dst
        )
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
            stream.error(toprint)
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
        stream.error(toprint)

    # Final return
    root.info("%s successfully updated", TOWNSHELL_PATH)
    root.debug("Written :\n{}".format(cfg))
    return True


# Checks a bunch of things and modify if unappropriate
# line: command about to be executed
# - if cmd is load_path no check is done
# - if the path to saved files is not well defined in townshell.cfg
# - if cmd modify the file (level, paint, ...) a check on last modified file is done
def check_stuff(line):

    # Commands that will always work
    if any([line.startswith(it) for it in ("loadpath", 'color', 'shortcuts', 'EOF', 'exit', '?', 'help')]):
        return True

    # Scapedir stuff
    global scapedir
    if exists(scapedir) is False:

        scapedir = read_cfg("scapedir")
        if exists(scapedir) is False:
            stream.warning(
                "Townscaper saved files directory is not defined. See 'help loadpath' to update it"
            )
            return False

    # Last_modified stuff
    # Command that require that check : level, paint, undo, redo, backup, restore
    if (
        line.startswith("level -")
        or line.startswith("paint -")
        or line in ("undo", "redo", "backup", "restore")
    ):

        global last_modified
        new_last_modified = max(list_scapefiles(), key=getmtime)
        if new_last_modified != last_modified:

            # Check in townshell.cfg to know whether there is a control or not
            if read_cfg("user_approval") in (True, None):
                pursue = input(
                    """The last modified file changed. The new one is : {}
                    Do you want to continue ? (y/n) :""".format(
                        basename(new_last_modified)
                    )
                )
                if pursue.lower() not in ("y", "1", "o"):
                    root.debug("User did not want to continue (pursue : '%s' )", pursue)
                    return False
                else:
                    root.info(
                        "Last modified change approved. New file : %s",
                        new_last_modified,
                    )
                    last_modified = new_last_modified

            # Bypass controls
            else:
                root.debug("User approval bypassed")
                last_modified = new_last_modified

    # Everything is fine
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
        stream.warning("No Townscaper saved files were found")
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


# Create a backup copy of every saved files from townscaper
# pprint: If True, the updated files are printed
# args: cmd dictionary when backup is used from Cmd
def backup(pprint=False, args=None):

    # Dealing with args
    if args == {}:
        char = get_last_modified()
        if char == "":
            return

    elif args is None:
        char = ""

    elif "input1" in args and args["input1"] in ("-a", "-all"):
        char = ""

    elif "input1" in args:
        char = args["input1"]

    # Listing of all saved files
    scapefiles = list_scapefiles(char)

    # Case list_scapefiles failed
    if scapefiles is None:
        return

    # Listing of backup files
    backupfiles = {}
    with scandir(BACKUPTOWN) as backupdir:
        for file in backupdir:
            backupfiles[file.name] = {"path": file.path, "date": getmtime(file.path)}

    # Compare of scapefiles and backupfiles
    one_failure = False  # At least one operation failed
    one_change = False  # At least one file was updated or newly backup
    for file in scapefiles:

        name = basename(file)
        # Case the file is already in BACKUPTOWN, the update time is checked, if the file is newer, it's updated
        if name in backupfiles and getmtime(file) > backupfiles[name]["date"]:
            res = copyc(file, backupfiles[name]["path"], erase=True)
            if res and pprint:
                stream.info("Successful update backup of %s", name)
            if res:
                root.debug("Successful update backup of %s", name)
                one_change = True
            else:
                one_failure = True

        # Case the file is already in BACKUPTOWN but the mtime is the same or newer, nothing is done
        elif name in backupfiles:
            pass

        # Case the file does not exists in BACKUPTOWN
        else:
            res = copyc(file, BACKUPTOWN)
            if res and pprint:
                stream.info("Successful new backup of %s", name)
            if res:
                root.info("Successful new backup of %s", name)
                one_change = True
            else:
                one_failure = True

    # Final print
    if pprint and one_change is False and one_failure is False:
        stream.info("No new backup or update")
        root.info("No new backup or update")


# Restore a file or all Townscaper saved files to their last backup state
# args: Dictionary containing the args. Expected ones are '-all' or chain of characters or a path
def restore(args):

    # No args mean last_modified is used
    if args == {}:
        char = get_last_modified()
        if char == "":
            return
    else:
        # Checking the provided args : only the first arg is analyzed actually
        iter_args = iter(args.items())
        key, char = next(iter_args)

    # Case it's path
    if exists(char):
        file_to_restore = char

    # Case it's all
    elif char in ("-a", "-all"):
        files = list_scapefiles()
        for file in files:
            restore({"input1": file})

    # Other case, it's a chain of characters
    else:

        # Pick the first file found
        candidates = list_scapefiles(char)
        if candidates == []:
            stream.error("No corresponding file")
            root.warning("No file found for %s", char)
            return
        else:
            file_to_restore = candidates[0]
            stream.info("File to be restored : %s", file_to_restore)
            root.info("File to be restored : %s", file_to_restore)

    # Checking that the file exists in BACKUPTOWN and that the file has been modified
    backup_file = join(BACKUPTOWN, basename(file_to_restore))
    if exists(backup_file) and getmtime(file_to_restore) == getmtime(backup_file):
        stream.warning("No restore since the file are the same")
        root.warning(
            "No restore since the last modification date of both files are the same"
        )

    elif exists(backup_file) and getmtime(file_to_restore) != getmtime(backup_file):
        copyc(backup_file, file_to_restore, erase=True)
        stream.info("Successful restore of %s", basename(file_to_restore))

    else:
        stream.error("No backup found for %s", basename(file_to_restore))
        root.warning("No backup found for %s", basename(file_to_restore))


# Initialize Townshell
# - Fetch the directory of Townscaper saved files
# - List all saved files if found
# - Update backup of saved files
def init_townshell():

    global scapedir

    # Print Title
    print(TITLE)

    #Checks that the directories necessary for TownShell to work are built
    if exists(dirname(BACKUPTOWN)) is False:
        mkdir(dirname(BACKUPTOWN))

    if exists(TEMP) is False:
        mkdir(TEMP)

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

    # Start keyboard shortcuts
    start_shortcuts()

    # Print keyboard shortcuts
    print_shortcuts()

    # Checks townshell.cfg to find the directory where Townscaper saved files are
    scapedir = read_cfg("scapedir")

    # Checks that scapedir (the directory where Townscaper saved files are stored is filled) is OK
    if isinstance(scapedir, str) and exists(scapedir):
        stream.info("Townscaper saved files are in %s", scapedir)

    else:

        # Case where the value in townshell.cfg does not exist
        if isinstance(scapedir, str) and not exists(scapedir):
            root.warning("scapedir path in townshell.cfg does not exist")

        # Search for scapedir
        # Search through find_scapedir
        scapedir = find_scapedir()

        # Case where the path was not found the user is asked to provide it
        if scapedir == "":
            scapedir = input(
                """Townscaper saved files directory was not found.
            Drag and drop the directory to the command line or copy-paste the path of the directory
            Path : """
            )

            if scapedir.startswith('"'):
                scapedir = scapedir[1:-1]

            # Case where the provided path is not correct
            if exists(scapedir) is False:
                stream.error(
                    """%s does not exist.
                Only keyboard features will be available. Please use command 'loadpath' to provide Townscaper saved files directory""", scapedir
                )
                return False

        # Case the path is correct
        update_cfg("scapedir", scapedir)
        stream.info("Townscaper saved files are in %s", scapedir)

    # Printing of Townscaper saved files
    print_scapefiles(max_amount=5)

    # Initialize last_modified
    candidates = list_scapefiles()
    if candidates is None:
        pass
    else:
        last_modified = max(candidates, key=getmtime)
        set_last_modified(last_modified)

    # Update of backup files
    if exists(BACKUPTOWN) is False:
        mkdir(BACKUPTOWN)
    backup()

    # Look for a job to be read and executed
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
    new_file = None
    for key, arg in iter_args:

        # File to modify (char)
        if key == "input1":
            char = arg

        # Height
        if key in ("height", "h") and (
            arg.isnumeric() or (arg.startswith("-") and arg[1:].isnumeric())
        ):
            height = int(arg)

        # Coord
        elif key == "coord":
            coord = make_tuple(arg)

        # Max_height
        elif key in ("max_height", "maxh") and arg.isnumeric():
            if int(arg) > 255:
                stream.warning("Maximum height cannot exceed 255")
                root.warning("Invalid max height : %s", arg)
            else:
                max_height = int(arg)

        # Min_height
        elif key in ("min_height", "minh") and arg.isnumeric():
            if int(arg) > max_height:
                stream.warning("Minimum height cannot be superior to maximum height")
                root.warning("Invalid min height : %s", arg)
            else:
                min_height = int(arg)

        # Plain
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

        # New_file : to choose whether the previous file is erased or a new_file is made
        elif key in ("new_file", "nf"):
            # Checking the syntax of the new_file
            if exists(arg):
                new_file = arg

            # To be handled after
            elif arg == "":
                new_file = "to_be_created"

            # The directory of the saved files is fetched to check that the potential file does not exist yet
            else:

                # Case where the name is valid
                if arg.startswith("Town") and arg.endswith(".scape"):
                    name = arg

                # Case where the name is not valid, it's completed
                else:
                    name = "Town" + arg + ".scape"

                # Checking that the file does not exist in scapedir. If it exists it will be replaced with a new one
                if exists(join(scapedir, name)):
                    stream.warning(
                        "The name %s for the new file exists already, a new one will be used",
                        name,
                    )
                    root.warning(
                        "The name %s for the new file exists already, a new one will be used",
                        name,
                    )
                    new_file = "to_be_created"
                else:
                    new_file = join(scapedir, name)

        # New_file bis
        elif key.startswith("option") and arg in ("new_file", "nf"):
            new_file = "to_be_created"

    # Checking that 'char' as been provided last_modified is used otherwise
    if char is None:
        char = get_last_modified()

    # Checking that height has been filled
    if height is None:
        stream.error("No valid height was found")
        root.warning("No valid height was found")
        return

    # Dealing with new_file to be created
    if new_file == "to_be_created":

        # The name of the file is created using the current timestamp
        suffix = datetime.now().strftime("%Y%m%d%H%M%S")
        name = "Town" + suffix + ".scape"
        new_file = join(scapedir, name)

        root.info("The file will be saved to %s", new_file)
        stream.info("The file will be saved to %s", new_file)

    # Fetching the path of the file to be modified
    file_path = list_scapefiles(char)

    if file_path is None:
        return
    # Several files were found
    elif len(file_path) > 1:
        root.warning(
            "Several files were found : {}".format(
                [basename(file) for file in file_path]
            )
        )
        stream.warning(
            """Several files were found : {}
            Please try again with more characters""".format(
                [basename(file) for file in file_path]
            )
        )
        return
    # One file
    else:
        file_path = file_path[0]

    # Dictionary parsing the file
    corvox, rawfile = load(file_path)

    # Saving the raw data in version for undo/redo
    store_version(file_path, rawfile)

    # Leveling of appropriate data
    corvox = level(
        corvox, height, coord, max_height, min_height, plain, color, color_filter
    )

    # Saving the new file
    new_save = save(corvox, file_path, new_file)

    # Versioning
    if new_file is None:
        store_version(file_path, new_save)

    # Last_modified updated
    if new_file is None:
        set_last_modified(file_path)
    else:
        set_last_modified(new_file)

    # Print the new created file
    print_scapefiles(max_amount=1)


# Do all operations to level the town as required
# - Checks the args provided
# - Find the file spotted
# - Load the file using function load
# - Paint it as required using function paint
# - Save it using function save
def paint_town(args):

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
    new_file = None

    for key, arg in iter_args:

        # File to modify (char)
        if key == "input1":
            char = arg

        # Color
        if key in ("color", "c"):

            # color is between 0 and 14
            if arg.isnumeric() and 0 <= int(arg) <= 14:
                color = int(arg)
            # Invalid color digit
            elif arg.isnumeric():
                stream.error("Color needs to be between 0 and 14 included")
                root.warning("Color %s is not a valid one", arg)
                return
            # Random color
            elif arg.lower() in ("r", "random"):
                color = "random"

            # Color is a tuple like (color1, color2, color3)
            elif "," in arg:
                color = make_tuple(arg)

        # Old color
        elif key in ("color_filter", "cf"):

            # old color needs to be between 0 and 14
            if arg.isnumeric() and 0 <= int(arg) <= 14:
                color_filter = int(arg)

            # Invalid color digit
            elif arg.isnumeric():
                stream.error("Old color needs to be between 0 and 14 included")
                root.warning("Old color %s is not a valid one", arg)

        # Height
        elif key in ("height", "h"):
            if arg.isnumeric():
                height = int(arg)
            elif "," in arg:
                height = make_tuple(arg)

        ###
        # Column, coord and Details are not implemented yet
        ###

        # New_file : to choose whether the previous file is erased or a new_file is made
        elif key in ("new_file", "nf"):
            # Checking the syntax of the new_file
            if exists(arg):
                new_file = arg

            # To be handled after
            elif arg == "":
                new_file = "to_be_created"

            # The directory of the saved files is fetched to check that the potential file does not exist yet
            else:

                # Case where the name is valid
                if arg.startswith("Town") and arg.endswith(".scape"):
                    name = arg

                # Case where the name is not valid, it's completed
                else:
                    name = "Town" + arg + ".scape"

                # Checking that the file does not exist in scapedir. If it exists it will be replaced with a new one
                if exists(join(scapedir, name)):
                    stream.warning(
                        "The name %s for the new file exists already, a new one will be used",
                        name,
                    )
                    root.warning(
                        "The name %s for the new file exists already, a new one will be used",
                        name,
                    )
                    new_file = "to_be_created"
                else:
                    new_file = join(scapedir, name)

    # Checking that 'char' as been provided last_modified is used otherwise
    if char is None:
        char = get_last_modified()

    # Color is mandatory
    if color is None:
        return

    # Dealing with new_file to be created
    if new_file == "to_be_created":

        # The name of the file is created using the current timestamp
        suffix = datetime.now().strftime("%Y%m%d%H%M%S")
        name = "Town" + suffix + ".scape"
        new_file = join(scapedir, name)

        root.info("The file will be saved to %s", new_file)
        stream.info("The file will be saved to %s", new_file)

    # Fetching the path of the file to be modified
    file_path = list_scapefiles(char)

    if file_path is None:
        return
    # Several files were found
    elif len(file_path) > 1:
        root.warning(
            "Several files were found : {}".format(
                [basename(file) for file in file_path]
            )
        )
        stream.warning(
            """Several files were found : {}
            Please try again with more characters""".format(
                [basename(file) for file in file_path]
            )
        )
        return
    # One file
    else:
        file_path = file_path[0]

    # Dictionary parsing the file
    corvox, rawfile = load(file_path)

    # Saving the raw data in version for undo/redo
    store_version(file_path, rawfile)

    # Leveling of appropriate data
    corvox = paint(corvox, color, color_filter, height, column, coord, details)

    # Saving the new file
    new_save = save(corvox, file_path, new_file)

    # Versioning
    if new_file is None:
        store_version(file_path, new_save)

    # Last modified updated
    if new_file is None:
        set_last_modified(file_path)
    else:
        set_last_modified(new_file)

    # Print the new created file
    print_scapefiles(max_amount=1)


# Handle the storage of the versions, update a key or create a new one
# path: path of the file the content will be saved
# raw: file content
def store_version(path, raw):

    global version

    # Check that path is in versions or not
    if path in version:
        version[path]["previous"].append(version[path]["current"])
        version[path]["current"] = raw
        version[path]["future"] = []

    # A new key is added to version.
    else:
        version[path] = {"previous": [], "current": raw, "future": []}


# Fetch the content of the previous version of the spoted file and save it
def undo(args):

    global versions

    # No args mean last_modified is used
    if args == {}:
        char = get_last_modified()
        if char == "":
            return
    else:
        # Checking the provided args : only the first arg is analyzed actually
        iter_args = iter(args.items())
        key, char = next(iter_args)

    # Fetching the path of the file to be modified
    file_path = list_scapefiles(char)

    if file_path is None:
        return
    # Several files were found
    elif len(file_path) > 1:
        root.warning(
            "Several files were found : {}".format(
                [basename(file) for file in file_path]
            )
        )
        stream.warning(
            """Several files were found : {}
    Please try again with more characters""".format(
                [basename(file) for file in file_path]
            )
        )
        return
    # One file
    else:
        file_path = file_path[0]

    # Checks that the file exists in versions dictionary
    if file_path in version and version[file_path]["previous"] != []:

        version[file_path]["future"].append(version[file_path]["current"])
        version[file_path]["current"] = version[file_path]["previous"].pop()

        # The file is written back to its previous state
        # (Handling of the stats of the file to be done in the future)
        with open(file_path, "w") as file:
            file.write(version[file_path]["current"])

        stream.info("Undo success for %s", basename(file_path))
        root.info("Undo success for %s", basename(file_path))

    # No corresponding files
    else:
        stream.warning("No older version for %s", basename(file_path))
        root.info("No file found in versions for %s", file_path)


# Fetch the future version of the file (equivalent to Ctrl+Y)
def redo(args):

    global versions

    # No args mean last_modified is used
    if args == {}:
        char = get_last_modified()
        if char == "":
            return
    else:
        # Checking the provided args : only the first arg is analyzed actually
        iter_args = iter(args.items())
        key, char = next(iter_args)

    # Fetching the path of the file to be modified
    file_path = list_scapefiles(char)

    if file_path is None:
        return
    # Several files were found
    elif len(file_path) > 1:
        root.warning(
            "Several files were found : {}".format(
                [basename(file) for file in file_path]
            )
        )
        stream.warning(
            """Several files were found : {}
    Please try again with more characters""".format(
                [basename(file) for file in file_path]
            )
        )
        return
    # One file
    else:
        file_path = file_path[0]

    # Checks that the file exists in versions dictionary
    if file_path in version and version[file_path]["future"] != []:

        version[file_path]["previous"].append(version[file_path]["current"])
        version[file_path]["current"] = version[file_path]["future"].pop()

        # The file is written back to its previous state
        # (Handling of the stats of the file to be done in the future)
        with open(file_path, "w") as file:
            file.write(version[file_path]["current"])

        stream.info("Redo success for %s", basename(file_path))
        root.info("Redo success for %s", basename(file_path))

    # No corresponding files
    else:
        stream.warning("No newer version for %s", basename(file_path))
        root.info("No newer file in version for %s", file_path)

# Print the current keyboard shortcuts
def print_shortcuts():

    #Print whether keyboard shortcuts are active or not
    if active_shortcuts:
        print("Keyboard shortcuts : ON")
    else:
        print("Keyboard shortcuts : OFF")

    #Fetch shortcuts
    shortcuts = read_cfg('shortcuts')
    if shortcuts is None: return
    shortcuts = iter(shortcuts.items())

    # First shortcuts
    info_printed = False
    for key, value in shortcuts:

        if key.startswith('custom') and info_printed is False:
            print("\nTo get precise amount of clicks, enter quickly a few digits, then use the custom shortcuts below :")
            info_printed = True

        if key == 'pause':
            print("\nIntervals between clicks (s) : {}".format(value))

        else:
            print("'{}' ==> '{}'".format(key, value))

    # How to modify shortcuts
    print("Shortcuts and intervals can be modified in 'townshell.cfg'")


# Class of Thread to have shortcuts handled in another thread
class ShortcutThread(Thread):
    def __init__(self, event):  # event = objet Event
        Thread.__init__(self)
        self.event = event
        self.daemon = True

    def run(self):
        # Fetch the keyboard shortcuts settings from townshell.cfg
        shortcut(self.event, read_cfg("shortcuts"))

# Start a thread activating the keyboard shortcuts
def start_shortcuts():

    # Event that determine whether keyboard shortcuts should be active or not
    global stopnow
    global active_shortcuts

    # Checking that another thread is not executed already
    if active_shortcuts:
        stream.warning("Keyboard shortcuts are already activated")
        return

    # Initialize the event that control whether shortcuts are active or not
    stopnow = Event()
    stopnow.clear()

    # Main program
    new_thread = ShortcutThread(stopnow)
    new_thread.start()
    active_shortcuts = True
    stream.info("Keyboard shortcuts are now active")
    root.info("Keyboard shortcuts are now active")


# Stop the thread handling the shortcuts
def stop_shortcuts():

    global stopnow
    global active_shortcuts

    # Checking that another thread is not executed already
    if active_shortcuts is False:
        stream.warning("No shortcuts activated")
        return

    # The event is activated and shortcuts is stopped
    stopnow.set()
    active_shortcuts = False
    stream.info("Keyboard shortcuts have been deactivated")
    root.info("Keyboard shortcuts have been deactivated")
