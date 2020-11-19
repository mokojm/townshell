import xml.etree.ElementTree as ET
from logging import getLogger
from math import atan2, degrees, dist
from random import choice
from re import DOTALL, search

# Logging options
root = getLogger("Town.cooker")
stream = getLogger("TownStream.cooker")

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
ALLCOLORS = [i for i in range(15)]


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
    stream.info("%s created", file_path)

    # Return
    return new_save


# Fonction complétant superposant deux dictionnaires corners voxels
def mix(dico_one, dico_two):

    # On parcourt le second à la recherche d'éléments présents dans le premier
    for key, values in dico_two.items():
        if key in dico_one:
            # La valeur du nouveau dico écrase la précédente
            dico_one[key] = values

    # Return
    return dico_one


# Modify the level of a structure or a part of the structure based on criterias (color, coordonates). Height of each voxel is modified and new voxels may be added. Therefore the count of corners will be affected. The coordonates of corners are not affected. Return a new dictionary
# dico_corvox: dictionary containing the original structure
# height: amount to be added to each voxel. If negative, the amount is substrated
# coord: only the coordonate (x,y) spoted will affected
# max_height: define the maximum height that can be reached by voxels.
# min_height: define the minimum height that voxels can have
# plain: If False scafolding of empty space will appear below the leveled structure. If True, the empty space created will be filled by voxels according to the chosen 'color'.
# color: color applied to new voxels or voxels that were on the ocean floor (color=15)
# color_filter: only voxels with the selected color will have their height modified. The leveled voxels can take place of another voxel
# default_color: color taken by a case when no color is defined and there are no case over to copy the color
def level(
    dico_corvox,
    height,
    coord=None,
    max_height=255,
    min_height=-1,
    plain=False,
    color=None,
    color_filter=None,
    default_color=14,
):

    # Color is None
    if color is None:
        pass
    # Invalid colors lead to default color choice
    elif color > 14 or color < 0:
        root.warning("Color {} is invalid. Color 13 will be used".format(color))
        stream.warning("Color {} is invalid. Color 13 will be used".format(color))
        color = None

    # Max height limit
    if max_height > 255:
        max_height = 255

    # A copy of dico_corvox is iterated
    # Warning! count_and_voxels even it's a copy will point the actual item of dico_corvox
    dico_corvox_copy = dico_corvox.copy()
    for (x, y), count_and_voxels in dico_corvox_copy.items():

        cur_voxels = count_and_voxels["voxels"]

        # Coord
        if coord is None:
            pass
        else:
            if (x, y) != coord:
                continue

        # Case cur_voxels is empty, meaning that there is nothing on this case, a voxel is created on ocean floor
        if cur_voxels == {}:
            cur_voxels[-1] = 15

        # If color = None : Fetching the color of the closest to the floor or the one on min_height
        if color is None:
            positive_heights = [
                h for h in cur_voxels.keys() if h > 0 and h >= min_height
            ]
            if positive_heights == []:
                new_color = default_color
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
            # If the color of the voxel is not the correct one, it's not modified
            elif t != color_filter:
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


# Paint the spoted voxels (no voxels added). Lots of options to come in the future
# dico_corvox : dictionnaire des éléments présents
# color: color between 0 and 14, can be 'random', can be tuple with several color (ex: (1,2,3)), to have the random colors only among the chosen ones.
# color_filter: None by default, can be between 0 and 14, if not None every voxel having this color will be affected but not others
# height: if None or 0 and column is None and coord is () too, all the voxels are impacted. can be tuple with several heights (ex: (1,2,3)), can be tuple of tuple (ex : ((1,3),(5,7)) meaning put the color from height 1 to 3 and from 5 to 7)
# column: allow accurate choice of the corners impacted depending on the height (ex: '=5' mean that only corners with maximum height = 5 will be impacted), '<', '>', '!=' are accepted, '&' and '||' too, so the following command should be possible (=1||=2)||(>5&<15&!=10) (gonna be such a hell to implement, for now I'll sleep on it)
# coord: if you're aware of the format .scape of Townscaper save files, (x,y) of the file you need to colorize can be indicated, None by default.
# details: None by default, dictionnary allowing accurate colors for appropriate height in one command (ex : {1:((1,2),(5,7)), 10:4, 5:(11,15)}) (to be implemented after since it's not essential)
def paint(
    dico_corvox,
    color=None,
    color_filter=None,
    height=None,
    column=None,
    coord=(),
    details=None,
):

    # Basic control on entry
    if color is None:
        return

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
            # Random
            if color == "random":
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
