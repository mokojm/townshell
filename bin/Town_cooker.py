import xml.etree.ElementTree as ET
from itertools import cycle
from logging import getLogger
from math import atan2, degrees
from random import choice, random
from re import DOTALL, search
from statistics import mean, pvariance

from pyfiglet import Figlet

# Logging options
root = getLogger("Town.cooker")
# stream = getLogger("TownStream.cooker") #to be deleted

# Template of corners and voxels for 'save'
TEMP_CORNER = """
    <C>
      <x>{x}</x>
      <y>{y}</y>
      <count>{count}</count>
    </C>"""

TEMP_VOXEL = """
    <V>
      <t>{t}</t>
      <h>{h}</h>
    </V>"""

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

# Load the data contained in provided .scape file. Returns a dictionnary containing the coordinates of the corners (key), the amount of voxels linked with a corner, a dictionnary of the voxels linked with that corner.
# file_path: path of the .scape file to be loaded
def load(file_path):

    # Opening the file and saving the whole file
    with open(file_path) as file:
        full_content = file.read()

    # Parsing XML
    loot = ET.fromstring(full_content)

    # Corners : coordinates with at list one case filled
    corners = loot.find("corners")

    # Voxels : details about each case present on that corner, (h: height, t:color)
    voxels = loot.find("voxels")

    dico_corvox = {}  # Dictionnary linking the corners to their associated voxels
    list_corners = corners.findall("C")
    list_voxels = voxels.findall("V")

    # Corners and voxels are analyzed simultaneously to link them with one another according to count
    c1 = 0  # corners counter
    v1 = 0  # voxels counter
    limit_corners = len(list_corners)
    limit_voxels = len(list_voxels)
    while True:

        # Limit case, our job is done
        if c1 == limit_corners or v1 == limit_voxels:
            break

        corner = list_corners[c1]
        x = int(corner.find("x").text)
        y = int(corner.find("y").text)
        count = int(corner.find("count").text)  # will be useful to iterate over voxels
        dico_corvox[(x, y)] = {"count": count, "voxels": {}}

        # Iterating voxels
        while True:
            if count == 0:
                break

            voxel = list_voxels[v1]
            height = int(voxel.find("h").text)
            color = int(voxel.find("t").text)
            dico_corvox[(x, y)]["voxels"][height] = color

            count -= 1
            v1 += 1  # Next voxel

        # Next corner
        c1 += 1

    # Return
    root.info("Loading %s done", file_path)
    return dico_corvox, full_content


# Create a saved file using the given dictionary and the original file
# dico_corvox: dictionary containing the structure
# file_path : path to the original file
# new_file: Path of the new file to be created. If None the original file is updated
def save(dico_corvox, file_path, new_file=None):

    # Search corners and voxels groups
    with open(file_path) as file:
        original_save = file.read()

    old_corners = search("<corners>(.+)</corners>", original_save, DOTALL)[1]
    old_voxels = search("<voxels>(.+)</voxels>", original_save, DOTALL)[1]

    # Sort the dictionary to have the corners in the right order
    sorted_corvox = sorted(dico_corvox.items())

    # Building the new groups of corners and voxels
    new_corners = ""
    new_voxels = ""
    for (x, y), count_and_voxels in sorted_corvox:

        # If there are no voxels
        if count_and_voxels["count"] == 0:
            continue

        # Create a corner
        this_corner = TEMP_CORNER.replace("{x}", str(x))
        this_corner = this_corner.replace("{y}", str(y))
        this_corner = this_corner.replace("{count}", str(count_and_voxels["count"]))

        # Add the corner to the group of corners
        new_corners += this_corner

        # Sort the voxels
        sorted_voxels = sorted(count_and_voxels["voxels"].items())

        # Browse voxels
        for h, t in sorted_voxels:

            # Create a voxel
            this_voxel = TEMP_VOXEL.replace("{h}", str(h))
            this_voxel = this_voxel.replace("{t}", str(t))

            # Add the voxel to the group of voxels
            new_voxels += this_voxel

    # Final text
    new_save = original_save.replace(old_corners, new_corners)
    new_save = new_save.replace(old_voxels, new_voxels)

    # Dealing with new_file setting
    if new_file != None:
        file_path = new_file
    with open(file_path, "w") as file:
        file.write(new_save)

    # Log
    root.info("%s created", file_path)

    # Return
    return new_save


# Merge together several dictionnaries corners voxels according to operator 'op'
# "+" : gather all voxels in one dictionary
# "-" : voxels of the first dict that are not in other dict
# "&" : voxels that are common to all dict
# "^" : gather all voxels in one dict except those which are in more than one dict
def merge(op="+", *args):

    dictf = args[0]
    for dicti in args[1:]:

        for key, count_and_voxels in dicti.items():

            if op == "+":
                if key in dictf:
                    dictf[key]["voxels"].update(count_and_voxels["voxels"])
                    dictf[key]["count"] = len(dictf[key]["voxels"])
                else:
                    dictf[key] = count_and_voxels.copy()

            elif op == "-":
                if key in dictf:
                    thisKey = dictf[key]["voxels"].copy()
                    dictf[key]["voxels"] = {
                        h: thisKey[h]
                        for h in set(thisKey) - set(count_and_voxels["voxels"])
                    }
                    dictf[key]["count"] = len(dictf[key]["voxels"])

            elif op == "&":
                if key in dictf:
                    thisKey = dictf[key]["voxels"].copy()
                    dictf[key]["voxels"] = {
                        h: thisKey[h]
                        for h in set(thisKey) & set(count_and_voxels["voxels"])
                    }
                    dictf[key]["count"] = len(dictf[key]["voxels"])

            elif op == "^":
                if key in dictf:
                    thisKey = dictf[key]["voxels"].copy()
                    dictf[key]["voxels"] = {
                        h: thisKey[h]
                        for h in set(thisKey) ^ set(count_and_voxels["voxels"])
                    }
                    dictf[key]["count"] = len(dictf[key]["voxels"])
                else:
                    dictf[key] = count_and_voxels.copy()

        # Intersect specific
        if op == "&":
            for key in dictf.copy():
                if key not in dicti:
                    del dictf[key]

    # Return
    root.debug(f"Dictf:{dictf}")
    return dictf


# Modify the level of a structure or a part of the structure based on criterias (color, coordonates). Height of each voxel is modified and new voxels may be added. Therefore the count of corners will be affected. The coordonates of corners are not affected. Return a new dictionary
# dico_corvox: dictionary containing the original structure
# height: amount to be added to each voxel. If negative, the amount is substrated
# coord: only the coordonate (x,y) spoted will affected
# max_height: define the maximum height that can be reached by voxels.
# min_height: define the minimum height that voxels can have
# plain: If False scafolding of empty space will appear below the leveled structure. If True, the empty space created will be filled by voxels according to the chosen 'color'.
# color: color applied to new voxels or voxels that were on the ocean floor (color=15)
# color_filter: only voxels with the selected color will have their height modified. The leveled voxels can take place of another voxel, (2021/07/06: can be a tuple)
# smart: if true, the color of the lowest voxel will be used to color the new voxels
# height_filter: only the voxels with the specified height will be affected, tuple accepted
# count_vox: only corners having the specified amount of voxels matching previous criterias will triggered
# ground_only: only voxels having only ground level will be modified
def level(
    dico_corvox,
    height,
    coord=None,
    max_height=255,
    min_height=-1,
    plain=False,
    color=14,
    color_filter=None,
    **kwargs,
):

    smart = kwargs.get("smart", True)
    height_filter = kwargs.get("height_filter")
    count_vox = kwargs.get("count_vox")
    ground_only = kwargs.get("ground_only", False)

    # Color is None
    if color is None:
        color = 14
    # Invalid colors lead to default color choice
    elif color > 14 or color < 0:
        root.warning("Color {} is invalid. Color 13 will be used".format(color))
        color = 14

    # Max height limit
    if max_height > 255:
        max_height = 255

    # A copy of dico_corvox is iterated
    # Warning! count_and_voxels even it's a copy will point the actual item of dico_corvox
    dico_corvox_copy = dico_corvox.copy()
    for (x, y), count_and_voxels in dico_corvox_copy.items():

        cur_voxels = count_and_voxels["voxels"]

        countVoxOk = False if count_vox else True  # by default

        # Coord
        if coord is None:
            pass
        else:
            if (x, y) != coord:
                continue

        # Case cur_voxels is empty, meaning that there is nothing on this case, a voxel is created on ocean floor
        if cur_voxels == {}:
            cur_voxels[-1] = 15

        # GroundOnly handling
        if (
            ground_only is None
            or ground_only is False
            or ground_only
            and len(cur_voxels) == 1
            and cur_voxels.get(0)
        ):
            groundOnlyOk = True
        else:
            groundOnlyOk = False

        # Count_vox handling
        if count_vox:
            voxelsOk = 0
            for h, t in cur_voxels.items():
                hfOK = False  # Height filter
                cfOk = False  # Color filter

                # Height filter
                if (
                    isinstance(height_filter, tuple)
                    and height_filter[0] <= h <= height_filter[1]
                ):
                    hfOk = True
                elif height_filter and h == height_filter:
                    hfOk = True
                elif height_filter is None:
                    hfOk = True

                # Color filter
                if isinstance(color_filter, tuple) and t in color_filter:
                    cfOk = True
                elif color_filter and t == color_filter:
                    cfOk = True
                elif color_filter is None:
                    cfOk = True

                voxelsOk += 1 if hfOk and cfOk else 0

            countVoxOk = True if voxelsOk == count_vox else False

        # If color = None : Fetching the color of the closest to the floor or the one on min_height
        if smart:
            positive_heights = [
                h for h in cur_voxels.keys() if h > 0 and h >= min_height
            ]
            if positive_heights == []:
                new_color = color
            else:
                new_color = cur_voxels[min(positive_heights)]
        else:
            new_color = color

        # Iterating voxels and creating the new ones (new_voxels)
        new_voxels = {}
        for h, t in cur_voxels.items():

            # color_filter
            if color_filter is None:
                pass

            # Count_vox and Ground-only handling
            if countVoxOk is False or groundOnlyOk is False:
                root.debug(f"CountVoxOk and ground: {(countVoxOk, groundOnlyOk)}")
                new_voxels[h] = t
                continue

            # Height filter handling
            elif (
                isinstance(height_filter, tuple)
                and (h < height_filter[0] or h > height_filter[1])
            ) or (isinstance(height_filter, int) and h != height_filter):
                new_voxels[h] = t
                root.debug(f"Height filter : {(h,t)}")
                continue

            # When color_filter is a tuple
            elif isinstance(color_filter, tuple) and t not in color_filter:
                new_voxels[h] = t
                continue

            # If the color of the voxel is not the correct one, it's not modified
            elif isinstance(color_filter, int) and t != color_filter:
                new_voxels[h] = t
                continue

            # Define the new height
            new_h = h + height
            if new_h > max_height or new_h < min_height:
                continue

            # Define the new color
            # Case new_h = 0
            if new_h == 0:
                new_t = 15
            # Otherwise
            elif t == 15:
                new_t = new_color
            # Color unchanged
            else:
                new_t = t

            # If the height is positive or zero, a new voxel is created
            if new_h >= 0:
                new_voxels[new_h] = new_t

        # Dealing with plain : filling or not the empty space created
        if plain:
            # Among new voxels smallest height is chosen
            if color_filter is None:
                new_min_h = min(
                    [h for h, t in new_voxels.items() if h > 0 and h >= min_height],
                    default=None,
                )
            else:
                # At least one of the voxels in new_voxels needs to have the proper color_filter
                new_min_h = min(
                    [
                        h
                        for h, t in new_voxels.items()
                        if t == color_filter and h > 0 and h >= min_height
                    ],
                    default=None,
                )
            # Empty spaces are filled starting from the highest to min_height
            if new_min_h:
                for new_h in range(new_min_h - 1, min_height - 1, -1):

                    # h<0
                    if new_h < 0:
                        continue

                    # If new_h is already in new_voxels
                    if new_h in new_voxels:
                        break

                    # h=0
                    elif new_h == 0:
                        new_voxels[new_h] = 15

                    # Otherwise
                    else:
                        new_voxels[new_h] = new_color

        # "Count" adjustment according to the amount of voxels
        dico_corvox[(x, y)]["count"] = len(new_voxels)
        dico_corvox[(x, y)]["voxels"] = new_voxels

    # Return
    root.info("Dictionary leveled")
    return dico_corvox


# Take off some blocks according to some criterias, by default it will clean everything
# dico_corvox: dictionary containing the original structure
# color_filter: only voxels with the selected colors will be taken off
# percent: percentage of voxels that will be taken off
# height: only the voxels with the specified height will be affected, tuple accepted
# corner: dig corners instead of voxels, color_filter and height filter are ignored
# maxhf: max height filter, filter voxels that will be dig depending on the max height of their corner
def dig(
    dico_corvox, color_filter=None, percent=1, height=None, corner=False, maxhf=None
):

    # A copy of dico_corvox is browsed
    # Warning! count_and_voxels even it's a copy will point the actual item of dico_corvox
    dico_corvox_copy = dico_corvox.copy()
    for (x, y), count_and_voxels in dico_corvox_copy.items():

        cur_voxels = count_and_voxels["voxels"]

        # Max height filter
        if maxhf:
            maxhf = maxhf[0]  # because it's a tuple of tuple by default
            thisMaxH = max(cur_voxels)

            # Tuple
            if (
                isinstance(maxhf, tuple)
                and maxhf != ()
                and (thisMaxH < maxhf[0] or thisMaxH > maxhf[1])
            ):
                continue

            # Int
            elif isinstance(maxhf, int) and maxhf != thisMaxH:
                continue

        # Corner setting (other filters except max height filter are ignored)
        if corner is True:
            if random() < percent:
                dico_corvox[(x, y)]["voxels"] = {}
            continue

        # Browse voxels :
        # 1) Each criteria is checked and a boolean is set True. All boolean need to be true for the color to be applied
        # 2) The color is determined
        # 3) The color is applied
        new_voxels = {}
        for h, t in cur_voxels.items():

            # Intialize of validation criterias
            color_filter_OK = False
            height_OK = False
            percent_OK = False

            # Dealing with color_filter
            if color_filter is None:
                color_filter_OK = True

            elif isinstance(color_filter, tuple) and t in color_filter:
                color_filter_OK = True

            elif color_filter in ALLCOLORS and t == color_filter:
                color_filter_OK = True

            # Dealing with height
            if height is None:
                height_OK = True

            else:

                # Height is just an int
                if isinstance(height, int) and h == height:
                    height_OK = True

                # Height is a tuple
                elif (
                    isinstance(height, tuple)
                    and isinstance(height[0], int)
                    and h in height
                ):
                    height_OK = True

                # Height is a tuple of tuple
                elif (
                    isinstance(height, tuple)
                    and isinstance(height[0], tuple)
                    and isinstance(height[0][0], int)
                ):

                    # Analysis height against intervals
                    if any(mini <= h <= maxi for mini, maxi in height):
                        height_OK = True

            # Percent
            if percent == 1 or random() < percent:
                percent_OK = True

            # Conclusion when one of the condition is not fulfilled, color stay the same
            if color_filter_OK and height_OK and percent_OK:
                continue
            else:
                new_voxels[h] = t

        # Update of dico_corvox
        dico_corvox[(x, y)]["voxels"] = new_voxels

    # Return
    return dico_corvox


# Paint the spoted voxels (no voxels added). Lots of options to come in the future
# dico_corvox : dictionnaire des éléments présents
# color: color between 0 and 14, can be 'random', can be tuple with several color (ex: (1,2,3)), to have the random colors only among the chosen ones.
# color_filter: None by default, can be between 0 and 14, if not None every voxel having this color will be affected but not others, can be a tuple now
# height: if None or 0 and column is None and coord is () too, all the voxels are impacted. can be tuple with several heights (ex: (1,2,3)), can be tuple of tuple (ex : ((1,3),(5,7)) meaning put the color from height 1 to 3 and from 5 to 7)
# column: allow accurate choice of the corners impacted depending on the height (ex: '=5' mean that only corners with maximum height = 5 will be impacted), '<', '>', '!=' are accepted, '&' and '||' too, so the following command should be possible (=1||=2)||(>5&<15&!=10) (gonna be such a hell to implement, for now I'll sleep on it)
# coord: if you're aware of the format .scape of Townscaper save files, (x,y) of the file you need to colorize can be indicated, None by default.
# details: None by default, dictionnary allowing accurate colors for appropriate height in one command (ex : {1:((1,2),(5,7)), 10:4, 5:(11,15)}) (to be implemented after since it's not essential)
# alternate: if true and color is tuple, colors will alternate between given values
def paint(
    dico_corvox,
    color=None,
    color_filter=None,
    height=None,
    column=None,
    coord=(),
    details=None,
    alternate=False,
):

    # Basic control on entry
    if color is None:
        return

    # Alternate handling
    if isinstance(color, tuple) and alternate:
        cycleCol = cycle(color)

    elif color == "random" and alternate:
        cycleCol = cycle(ALLCOLORS)
    else:
        cycleCol = None

    # A copy of dico_corvox is browsed
    # Warning! count_and_voxels even it's a copy will point the actual item of dico_corvox
    dico_corvox_copy = dico_corvox.copy()
    for (x, y), count_and_voxels in dico_corvox_copy.items():

        cur_voxels = count_and_voxels["voxels"]

        # Browse voxels :
        # 1) Each criteria is checked and a boolean is set True. All boolean need to be true for the color to be applied
        # 2) The color is determined
        # 3) The color is applied
        new_voxels = {}
        for h, t in cur_voxels.items():

            # h=0 ==> t=15 Always
            if h == 0:
                new_voxels[h] = 15
                continue

            # Intialize of validation criterias
            color_filter_OK = False
            height_OK = False

            # Dealing with color_filter
            if color_filter is None:
                color_filter_OK = True

            elif isinstance(color_filter, tuple) and t in color_filter:
                color_filter_OK = True

            elif color_filter in ALLCOLORS and t == color_filter:
                color_filter_OK = True

            # Dealing with height
            if height is None:
                height_OK = True

            elif height is not None and height != 0:

                # Height is just an int
                if isinstance(height, int) and h == height:
                    height_OK = True

                # Height is a tuple
                elif (
                    isinstance(height, tuple)
                    and isinstance(height[0], int)
                    and h in height
                ):
                    height_OK = True

                # Height is a tuple of tuple
                elif (
                    isinstance(height, tuple)
                    and isinstance(height[0], tuple)
                    and isinstance(height[0][0], int)
                ):

                    # Analysis height against intervals
                    if any(mini <= h <= maxi for mini, maxi in height):
                        height_OK = True

            # Conclusion when one of the condition is not fulfilled, color stay the same
            if not (color_filter_OK and height_OK):
                new_voxels[h] = t
                continue

            # Determine colors
            new_t = t  # (that line is just here prevent any obscure reason that would bring new_t not to be found through following statements)

            # Alternate
            if cycleCol:
                new_t = next(cycleCol)
            # Random
            elif color == "random":
                new_t = choice(ALLCOLORS)
            # Case it's one color
            elif isinstance(color, int) and color in ALLCOLORS:
                new_t = color
            # Case it's a tuple of colors, one of them is randomly chosen
            elif isinstance(color, tuple) and all(c in ALLCOLORS for c in color):
                new_t = choice(color)

            # New color is applied
            new_voxels[h] = new_t

        # Update of dico_corvox
        dico_corvox[(x, y)]["voxels"] = new_voxels

    # Return
    return dico_corvox


# Change a text as input in dictionary of positions for wallwrite using Figlet, supporting a bunch of options
def prepare_text(**kwargs):

    text = kwargs.get("text")
    fontstr = kwargs.get("font", "6x10")
    INTERLINE = kwargs.get("INTERLINE", 2)
    SPACE_LEN = kwargs.get("SPACE_LEN", 4)
    LINE_LENGTH = kwargs.get("LINE_LENGTH", len(kwargs["corvox"]))
    INTERLETTER = kwargs.get("INTERLETTER", 1)
    INTERWORD = kwargs.get("INTERWORD", 4)
    wordWrap = kwargs.get("wordwrap", True)
    align = kwargs.get("align", "middle")  # left by default, or middle, or right

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
        )  # cursor if align == 'middle'
        rCursor = LINE_LENGTH - (maxCursor - minCursor)  # cursor if align == 'right'
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
                            if align == "middle"
                            else rCursor
                            if align == "right"
                            else 0
                        )

        # root.debug("fin")
        # root.debug(
        #     f"line_lengh, maxCursor, mincursor : {(LINE_LENGTH, maxCursor, minCursor)}"
        # )
        # root.debug(dico)

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

    # Font
    font = Figlet(font=fontstr)

    # 28/06/2021: Checking step to strip all characters that pyfiglet does not proceed
    textCopy = text
    for letter in textCopy:
        render = font.renderText(letter)
        if render == "":
            text = text.replace(letter, "")

    MAX_HEIGHT = 255

    cursor = 0
    height = 1
    curLine = 1
    heightLine = 1

    myDict = {(i, line): {} for i, line in enumerate(text.splitlines())}
    lineVsHeight = {}  # Height associated with Lines
    lineVsHeight[curLine] = height
    root.debug(f"initial mydict : {myDict}")

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

                if c3 != 0 and cursor != 0:
                    cursor += INTERLETTER

                wordDict[(k, letter)] = {"cursor": cursor}

                # Render the letter and identify and delete unecessary spaces
                renderLetter = font.renderText(letter)
                renderLines = renderLetter.splitlines()

                # Delete empty lines
                spaceStart = spaceEnd = len(renderLines[0])

                # root.debug(f"letter : {letter}")
                # root.debug(f"text : {renderLetter}")
                # root.debug(f"renderlines : {renderLines}")

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
                    matchStart = search(r"\A(\s+)\S+", line)
                    matchEnd = search(r"\S+(\s+)\Z", line)
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
                # root.debug(f"s,e : {spaceStart, spaceEnd}")
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
                # root.debug(f"letter {letter}, {wordDict[(k, letter)]}")
                # root.debug(f"lineVsHeight : {lineVsHeight}")

    # Last operations
    minS, minE = finilize_line(myDict, curLine, align)
    heightLine = heightLine - minS - minE
    lineVsHeight[curLine] = height
    heightTot = height + heightLine

    # root.debug(f"myDict : {myDict}")
    # root.debug(f"lineVsHeight : {lineVsHeight}")
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
                        finalDict[(x, y)] = (
                            {"line": i, "word": j, "letter": letter, "idl": k}
                            if char not in (" ",)
                            else 0
                        )

    root.debug(f"finalDict : {finalDict}")
    return finalDict


# From a given text, make a Townscaper dictionary, too many options !
def wallwrite(**kwargs):

    # Settings
    dico_corvox = kwargs.get("corvox")

    text = kwargs.get("text", "notext")
    text = "(empty)" if text == "" else text

    color = kwargs.get("color", 10)

    # Plain handling to stay logic
    plain = kwargs.get("plain", False)
    background = kwargs.get("background")
    plain = True if background is not None and background != tuple() else False

    centered = kwargs.get("align", "left")
    line_length = kwargs.get("LINE_LENGTH", len(dico_corvox))
    mode = kwargs.get("mode")
    dictColors = kwargs.get("dict_colors")
    alternate = kwargs.get("alternate")
    crown = kwargs.get("crown")
    reverse_all = kwargs.get("reverse")
    startpos = kwargs.get("start")
    fullstruct = kwargs.get("full")

    # Alternate requirements
    # Alternate does not work with dictColors or if color is not tuple
    if alternate == "background" and isinstance(background, tuple) is False:
        alternate = None
    elif alternate == "text" and isinstance(color, tuple) is False:
        alternate = None
    elif alternate in ("both", "all") and (
        isinstance(background, tuple) is False or isinstance(color, tuple) is False
    ):
        alternate = None
    elif alternate and dictColors:
        alternate = None
    elif alternate == "text":
        cycleText = cycle(color)
    elif alternate == "background":
        cycleBack = cycle(background)
    elif alternate in ("both", "all"):
        cycleText = cycle(color)
        cycleBack = cycle(background)

    # Maximum line length
    max_line_length = len(dico_corvox)
    if line_length is None or line_length > max_line_length:
        line_length = max_line_length

    # Prepare the text
    dictext = prepare_text(**kwargs)
    lx = [x for x, y in dictext]
    length_text = max(lx)
    height_text = max([y for x, y in dictext])

    # Determine the start of the writing
    # Get the max length of prepared words
    startl = 0
    starth = 1

    endl = 9999999 if fullstruct else startl + length_text
    endh = starth + height_text

    centered = True if centered == "middle" else False
    if centered and not fullstruct:
        startl = min(lx)  # round(max_line_length / 2 - length_text / 2)
        endl = max(lx)  # round(max_line_length / 2 - length_text / 2)

    root.debug(f"{(startl, endl)}")

    max_height = (
        endh + 1
    )  # +1 is here to have at least one line over the words when plain=True

    # Browse dico_corvox

    # The dictionary is sorted according to voxels height
    dico_corvox_copy = sorted(
        dico_corvox.items(),
        key=lambda x: max(x[1]["voxels"]),
        reverse=True if reverse_all else False,
    )

    # If startpos is defined then the list is rearranged according to
    # Note that startpos should only be used with circular structure
    if startpos:
        dico_corvox_copy = dico_corvox_copy[startpos:] + dico_corvox_copy[:startpos]

    # Previous value for color according to word, line or letter
    dictMode = {}

    # Main loop
    for l, ((x, y), count_and_voxels) in enumerate(dico_corvox_copy):

        cur_voxels = count_and_voxels["voxels"]
        new_voxels = {}
        if l < startl or l > endl:
            pass

        else:
            for h in range(max_height):

                # color choice (first layer)
                if color == "random":
                    t = (
                        choice([co for co in ALLCOLORS if co not in background])
                        if isinstance(background, tuple)
                        else choice([co for co in ALLCOLORS if co != background])
                    )
                elif isinstance(color, tuple):
                    t = choice(color)
                else:
                    t = color

                if h == 0 and plain:
                    new_voxels[h] = 15

                elif h > endh and plain is False:
                    break

                elif h < starth and plain is False:
                    pass

                elif (l, h - starth) in dictext and dictext[(l, h - starth)]:

                    # Color choice (second layer)
                    if dictColors:
                        t = dictColors.get(dictext[(l, h - starth)]["letter"], t)

                    # Alternate handling
                    elif alternate in ("both", "all", "text") and not mode:
                        t = next(cycleText)
                        if t == "random":
                            t = (
                                choice([co for co in ALLCOLORS if co not in background])
                                if isinstance(background, tuple)
                                else choice(
                                    [co for co in ALLCOLORS if co != background]
                                )
                            )

                    # Mode handling
                    if dictColors is None and mode:
                        data = dictext[(l, h - starth)]
                        if mode in ("1-letter-1-color", "1l1c"):
                            key = data["line"], data["word"], data["idl"]

                        elif mode in ("1-word-1-color", "1w1c"):
                            key = data["line"], data["word"]

                        elif mode in ("1-line-1-color", "1li1c"):
                            key = data["line"]

                        # Applying color
                        if key in dictMode:
                            t = dictMode[key]

                        # Alternate + mode
                        elif alternate in ("both", "all", "text"):
                            t = next(cycleText)
                            if t == "random":
                                t = (
                                    choice(
                                        [co for co in ALLCOLORS if co not in background]
                                    )
                                    if isinstance(background, tuple)
                                    else choice(
                                        [co for co in ALLCOLORS if co != background]
                                    )
                                )
                            dictMode[key] = t
                        else:
                            dictMode[key] = t

                    # Applying the color
                    if t == "empty":
                        pass
                    else:
                        new_voxels[h] = t

                elif plain:
                    # Crown option
                    if crown:
                        listx = [c for c in range(l - crown, l + crown + 1)]
                        listy = [
                            c for c in range(h - starth - crown, h - starth + crown + 1)
                        ]
                        if any(
                            [
                                (a, b) in dictext and dictext[(a, b)]
                                for a in listx
                                for b in listy
                            ]
                        ):
                            pass
                        else:
                            continue

                    # Alternate handling
                    if alternate in ("both", "all", "background"):
                        b = next(cycleBack)
                        if b == "random":
                            b = (
                                choice([co for co in ALLCOLORS if co not in background])
                                if isinstance(background, tuple)
                                else choice(
                                    [co for co in ALLCOLORS if co != background]
                                )
                            )
                        new_voxels[h] = b

                    elif background == "random":
                        new_voxels[h] = choice([co for co in ALLCOLORS if co != t])
                    elif isinstance(background, tuple):
                        b = choice(background)
                        if b != "empty":
                            new_voxels[h] = b
                    else:
                        new_voxels[h] = background

        # "Count" adjustment according to the amount of voxels
        dico_corvox[(x, y)]["count"] = len(new_voxels)
        dico_corvox[(x, y)]["voxels"] = new_voxels

    # Return
    return dico_corvox


# Flip the given structure upside down
def flip(
    dico_corvox,
    color=14,
    color_filter=None,
):

    # Find maximum height in dico_corvox
    maxHeight = max([max(data["voxels"]) for data in dico_corvox.values()])

    # A copy of dico_corvox is browsed
    # Warning! count_and_voxels even it's a copy will point the actual item of dico_corvox
    dico_corvox_copy = dico_corvox.copy()
    for (x, y), count_and_voxels in dico_corvox_copy.items():

        cur_voxels = count_and_voxels["voxels"]

        new_voxels = {}
        for h, t in cur_voxels.items():

            if (
                color_filter is None
                or (isinstance(color_filter, tuple) and t in color_filter)
                or (isinstance(color_filter, int) and t == color_filter)
            ):

                # Determine the new height
                new_h = maxHeight - h

                # new_h=0 ==> t=15 Always
                if new_h == 0:
                    new_voxels[new_h] = 15
                    continue

                # Case the original voxel was on the ground
                elif h == 0:
                    new_voxels[new_h] = color

                # Other cases
                else:
                    # New color is applied
                    new_voxels[new_h] = t

        # Update of dico_corvox
        dico_corvox[(x, y)]["voxels"] = new_voxels

    # Return
    return dico_corvox


# Statistics about the dictionary given
# nb_corners: amount of corners
# nb_voxels: amount of voxels
# max_height: maximum height of the structure
# min_height: minimum height of the structure
# mean_height: average height of the structure
# var_height: variance of the height of the structure
# max_nb_height: maximum amount of different heights in corners
# 1st_height: most used height
# 2nd_height: 2nd most used height
# nb_colors: amount of different colors used in the structure
# mean_color: average color of the structure (rgb)
# var_color: variance of used colors
# mean_col_vs_cor: average amount of different colors used in corners
# max_col_vs_cor: maximum amount of different colors used in corners
# least_color: least used color
# 1st_color: most used color (no ground)
# 2nd_color: 2nd most used color
# ground_only: amount of corners with only ground
# no_ground: amount of corners that don't touch ground
# mean_x, mean_y: center of the structure
# var_x, var_y: variance of coordinates
# filters: list of statistics to be returned among exposed ones over there
def info(dico_corvox, filters=None):

    stats = {
        "timestamp": 0,
        "nb_corners": 0,
        "nb_voxels": 0,
        "max_height": 0,
        "min_height": 0,
        "mean_height": 0,
        "var_height": [],
        "max_nb_height": 0,
        "1st_height": 0,
        "2nd_height": 0,
        "nb_colors": set(),
        "mean_color": [],
        "var_color": [],
        "mean_col_vs_cor": 0,
        "max_col_vs_cor": 0,
        "least_color": 0,
        "1st_color": 0,
        "2nd_color": 0,
        "ground_only": 0,
        "no_ground": 0,
        "mean_x": 0,
        "mean_y": 0,
        "var_x": [],
        "var_y": [],
    }
    color_count = {
        0: 0,
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        10: 0,
        11: 0,
        12: 0,
        13: 0,
        14: 0,
        15: 0,
    }
    height_count = {}

    for (x, y), c_voxels in dico_corvox.items():

        stats["nb_corners"] += 1
        stats["mean_x"] += x
        stats["mean_y"] += y
        stats["var_x"].append(x)
        stats["var_y"].append(y)
        maxh = 0
        minh = 0
        seqColors = set()
        seqHeights = set()

        groundOnlyTrig = False
        noGround = True

        for h, t in c_voxels["voxels"].items():
            stats["nb_voxels"] += 1

            maxh = max(h, maxh)
            minh = min(h, minh)
            seqHeights.add(h)

            if h in height_count:
                height_count[h] += 1
            else:
                height_count[h] = 1

            seqColors.add(t)
            stats["nb_colors"].add(t)
            if t != 15:
                stats["var_color"].append(t)
                stats["mean_color"].append(ALLCOLORS[t]["coord"])

            color_count[t] += 1

            if t == 15:
                groundOnlyTrig = True
                noGround = False
            else:
                groundOnlyTrig = False

        stats["max_height"] = max(stats["max_height"], maxh)
        stats["min_height"] = min(stats["max_height"], minh)
        stats["max_nb_height"] = max(stats["max_nb_height"], len(seqHeights))
        stats["var_height"].append(maxh)
        stats["mean_height"] += maxh

        if groundOnlyTrig:
            stats["ground_only"] += 1

        if noGround:
            stats["no_ground"] += 1

        stats["mean_col_vs_cor"] += len(seqColors)
        stats["max_col_vs_cor"] = max(stats["max_col_vs_cor"], len(seqColors))

    stats["mean_height"] /= stats["nb_corners"]
    stats["var_height"] = pvariance(stats["var_height"], stats["mean_height"])

    height_count = sorted(height_count.items(), key=lambda x: x[1], reverse=True)
    stats["1st_height"] = height_count[0][0]
    stats["2nd_height"] = height_count[1][0] if len(height_count) > 1 else 0

    stats["nb_colors"] = len(stats["nb_colors"])
    tmp = stats["mean_color"]
    stats["mean_color"] = (
        (
            mean([a[0] for a in tmp]),
            mean([a[1] for a in tmp]),
            mean([a[2] for a in tmp]),
        )
        if tmp != []
        else (0, 0, 0)
    )
    stats["var_color"] = (
        pvariance(stats["var_color"]) if stats["var_color"] != [] else 0
    )

    color_count = sorted(color_count.items(), key=lambda x: x[1])
    stats["1st_color"] = color_count[-1][0]
    stats["2nd_color"] = color_count[-2][0]
    stats["least_color"] = color_count[0][0]

    stats["mean_col_vs_cor"] /= stats["nb_corners"]

    stats["mean_x"] /= stats["nb_corners"]
    stats["mean_y"] /= stats["nb_corners"]
    stats["var_x"] = pvariance(stats["var_x"], stats["mean_x"])
    stats["var_y"] = pvariance(stats["var_y"], stats["mean_y"])

    # Handling filters
    if isinstance(filters, list):
        stats = {key: value for key, value in stats.items() if key in filters}

    return stats


# Calculate the angle between three 2 dimensions points, return it in degrees
def cangle(pt1, pt2, pt3):
    x1, y1 = pt1
    x2, y2 = pt2
    x3, y3 = pt3
    a = (x2 - x1, y2 - y1)
    b = (x3 - x1, y3 - y1)
    return degrees(atan2(b[1], b[0]) - atan2(a[1], a[0]))


# Find the borders of a set of points according to a given accuracy. Return the dictonnary given as input with one more tag 'border' with the value 0 if the point is not a border and 1 to infinite depending on the group of borders it's part on.
# dico_corvox: the dictionnary of corners
# accuracy: the maximum distance that will be searched for each point, by default the whole map is included
def find_borders(dico_corvox, accuracy=20):

    list_corvox = list(
        dico_corvox.keys()
    )  # Useful for optimizing analysis of neighbors

    # Looping dico_corvox
    for i, (x0, y0) in enumerate(dico_corvox):

        # Initialize the dictionnary that need to be filled
        borders = {
            (0.0, 45.0): False,
            (45.0, 90.0): False,
            (-45.0, 0.0): False,
            (-90.0, -45.0): False,
            (90.0, 135.0): False,
            (135.0, 180.0): False,
            (-135.0, -90.0): False,
            (-180.0, -135.0): False,
        }

        # Inner looping list_corvox
        before = i - 1
        after = i + 1
        do_after = True
        finished_after = False
        do_before = False
        finished_before = False
        amount_corvox = len(list_corvox)
        while True:

            # Limits cases
            if finished_before and finished_after:
                break

            if after >= amount_corvox:
                do_after = False

            if before < 0:
                do_before = False

            # Condition to analyze the next case or the case before or stop here the loop
            if do_after:
                x1, y1 = list_corvox[after]
                after += 1
                do_after = False
                do_before = True
            elif do_before:
                x1, y1 = list_corvox[before]
                before -= 1
                do_after = True
                do_before = False
            else:
                break

            # Main part of the inner loop
            diffx = x1 - x0
            diffy = y1 - y0
            # Case where the point x1,y1 is too far obviously
            if abs(diffx) > accuracy and x1 > x0:
                finished_after = True
            elif abs(diffx) > accuracy and x1 < x0:
                finished_before = True

            if abs(diffy) > accuracy:
                continue

            # Check which reference point will be used takes into account that angle does not support angle >90°C or < -90°C
            ref_point = (x0 + 1, y0)

            # Angle
            angle1 = round(cangle((x0, y0), ref_point, (x1, y1)), 1)
            print((x0, y0), ref_point, (x1, y1), file=open("borders.txt", "a"))
            print(diffx, angle1, file=open("borders.txt", "a"))

            # Borders loop to find the place of the spotted point
            for (a_min, a_max) in borders:

                if a_min < angle1 <= a_max:
                    borders[(a_min, a_max)] = True
                elif angle1 == -180.0:
                    borders[(135.0, 180.0)] = True

                # Listing condition where the point change the status of the border point
                # if diffx >= 0 and a_min < angle1 <= a_max:
                #     borders[(a_min, a_max)] = True

                # elif diffx < 0 and angle1 < 0 and a_min < angle1 - 90.0 <= a_max:
                #     borders[(a_min, a_max)] = True

                # elif diffx < 0 and angle1 >= 0 and a_min < angle1 + 90.0 <= a_max:
                #     borders[(a_min, a_max)] = True

            # Checks that borders is completed or not, get out of the loop if yes
            if any([filled is False for filled in borders.values()]):
                pass
            else:
                dico_corvox[(x0, y0)]["border"] = 0
                break

        print(borders, file=open("borders.txt", "a"))
        # raise
        # Summarize
        if any([filled is False for filled in borders.values()]):
            dico_corvox[(x0, y0)]["border"] = 1

    # Return
    return dico_corvox


# ANALYSE DE LA GRILLE
# print('',  file=open('borders.txt', 'w'))
# first_one = 'Townk27qIIxorrgF0xNe.scape'
# second_one = 'Town123.scape'
# third_one = 'Town123bis.scape'
# fourth = 'Town125.scape'
# #Analyse matplot
# import matplotlib.pyplot as plt

# dico_s,raw = load(second_one)
# dico_f,raw = load(fourth)
# #dico_f = mix(dico_s, dico_f)
# #dico_s = level(dico_s, -1)
# dico_s = find_borders(dico_s)
# for (x,y),datas in dico_f.items():
#     if datas['count'] == 2 and dico_s[(x,y)]['border']==1:

#         plt.scatter(x,y, c='g')
#     elif datas['count'] == 2:
#         plt.scatter(x,y, c='r')

#     elif datas['count'] == 1 and dico_s[(x,y)]['border']==1:
#         plt.scatter(x,y, c='m')

#         #dico_s = level(dico_s, height=1, coord=(x,y), plain=True)
#     else:
#         plt.scatter(x,y, c='k')
# #save(dico_s, second_one,'Town1210.scape')
# plt.title('Nuage de points avec Matplotlib')
# plt.xlabel('x')
# plt.ylabel('y')

# plt.savefig('ScatterPlot_01.png')
# plt.show()

# exit(0)
