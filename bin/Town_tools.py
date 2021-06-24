import json
import sys
from datetime import datetime
from logging import getLogger
from os import remove
from os.path import abspath, basename, dirname, exists, isdir, join, splitext
from shutil import copy2, move

from psutil import virtual_memory

# The configuration file
TOWNSHELL_PATH = "townshell.cfg"

# To handle .exe treatment
BUNDLE_DIR = getattr(sys, "_MEIPASS", abspath(dirname(__file__)))

# Directory of backup
BACKUPTOWN = "backup\\" + datetime.now().strftime("%Y%m%d%H%M%S")

# Directory for temporary storage
TEMP = "temp"

# Timestamp format
TIMESTAMP_FORMAT = "%Y/%m/%d %H:%M:%S"

# Logging
root = getLogger("Town.tools")

# Look for the given path in exe directory and current dir
def exePath(mypath):
    if exists(mypath):
        return mypath
    elif exists(abspath(join(BUNDLE_DIR, mypath))):
        return abspath(join(BUNDLE_DIR, mypath))
    else:
        return mypath

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
            root.warning("'{}' does not exist. Directory of scape saved files not updated".format(
                value
            ))

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
        root.error("Error on saving the updated {}".format(TOWNSHELL_PATH))

    # Final return
    root.info("%s successfully updated", TOWNSHELL_PATH)
    root.debug("Written :\n{}".format(cfg))
    return True
