# The functions detailed below are all translation from Javascript.
# The original code was done by alvaro-cuesta here https://github.com/alvaro-cuesta/townsclipper
# Thank you very much for it !

# IMPORTANT NOTES:
#
# Input looks like base64url but IT IS NOT! Notice the alphabet's out-of-order "w"
# and the swapped "_" and "-" when compared to RFC 4648 §5.
#
# Townscaper decodes clip strings left-to-right and LSB first (both in BitArray index
# and character bits). This means the "base64" output is reversed.
#
# Later, when reading values, they're read in bit blocks from LSB to MSB. I.e. values
# are read right-to-left (but their bits are still LSB on the right).

from logging import getLogger
from math import ceil, inf, log2
from re import search

# Logging
root = getLogger("Town.clipper")

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvxyzw0123456789_-"
BITS_PER_CHAR = 6


def clipToBits(clip):

    #root.debug(f"clipToBits to do :\n{clip}")
    reversed_clip = list(clip)[::-1]
    bits = []
    for x in reversed_clip:
        value = ALPHABET.find(x)
        if value == -1:
            root.debug(f"Invalid clip string character {x}")
            return
        bits.append("{0:b}".format(value).rjust(BITS_PER_CHAR, "0"))

    #root.debug(f"clipToBits done :\n{''.join(bits)}")
    return "".join(bits)


def bitsToClip(bits):

    if any(bit not in ("0", "1") for bit in bits):
        root.debug("Invalid bits")
        return

    if len(bits) % BITS_PER_CHAR != 0:
        root.debug(
            f"Bit string length {len(bits)} must be a multiple of {BITS_PER_CHAR}"
        )

    clip = []
    for i, b in enumerate(bits):
        charBits = bits[i * BITS_PER_CHAR : (i + 1) * BITS_PER_CHAR]
        if charBits != "":
            clip.append(ALPHABET[int(charBits, 2)])

    #root.debug(f"bitsToClip done :\n{''.join(clip[::-1])}")
    return "".join(clip[::-1])


###
EMPTY_TYPE = -1
GROUND_TYPE = 15
MAX_TYPE_COUNT = 15
MAX_TYPE = 15  # Technically this should be 14 but it works in-game (with glitches)
MAX_HEIGHT = 255
GROUND_HEIGHT = 0
###


class BitReader:
    def __init__(self, bits):
        self.bits = bits
        self.cursor = 0

    def get_remaining(self):
        return len(self.bits) - self.cursor

    def read(self, n, lenient=False):
        if n == 0:
            root.debug("Trying to read zero bytes")
            return

        if self.get_remaining() < n and lenient is False:
            root.debug(
                "Could not read {} bits (only {} remaining) at position {}".format(
                    n, self.get_remaining(), self.cursor
                )
            )

        readBits = self.bits[
            -self.cursor - n : -self.cursor if self.cursor > 0 else None
        ]
        self.cursor += n
        if len(readBits) == 0:
            return 0
        else:
            return int(readBits, 2)


# Given a signed int bit length, get the number to subtract from the raw uint
# to transform it into its signed value.
#
# https:#en.wikipedia.org/wiki/Offset_binary
def getSignOffset(bitLength):
    return 1 << (bitLength - 1)


# Get the max value representable with some bit length.
def getMaxValue(bitLength):
    return (1 << bitLength) - 1


# Get the bit length needed to represent some max value.
def getBitLength(maxValue):
    return ceil(log2(maxValue + 1))


# Get the bit length needed to represent some max value in "offset binary"
# form (see getSignOffset).
def getSignedBitLength(minValue, maxValue):
    if minValue == 0 and maxValue == 0:
        return 0

    unsignedMaxValue = max(
        abs(minValue) if minValue < 0 else minValue + 1,
        abs(maxValue) if maxValue < 0 else maxValue + 1,
    )

    return getBitLength(unsignedMaxValue * 2 - 1)


# Get info for the type list indices. Used in voxel lists to index the types.
def getTypeIndexInfo(typeCount):
    typeIndexBitLength = getBitLength(typeCount + 1)
    typeStopIndex = getMaxValue(typeIndexBitLength)

    return typeIndexBitLength, typeStopIndex


# Constants
BIT_LENGTH_BIT_LENGTH = 5
TYPE_COUNT_BIT_LENGTH = getBitLength(MAX_TYPE_COUNT - 1)
TYPE_BIT_LENGTH = getBitLength(MAX_TYPE)
BOOLEAN_BIT_LENGTH = 1

# Remove zero-padding from a bit string. Assumes no extranous characters.
def removePadding(bits):
    first1Index = bits.find("1")

    if first1Index == -1:
        return ""

    return bits[first1Index:]


def bitsToDense(bits):
    nonBit = search(r"[^01]", bits)

    if nonBit is not None:
        root.debug("Invalid bit character" + nonBit[0])
        return

    if len(bits) % BITS_PER_CHAR != 0:
        root.debug(
            "Bit string length {} must be a multiple of {}".format(
                len(bits), BITS_PER_CHAR
            )
        )
        return

    dense = {}
    bitReader = BitReader(removePadding(bits))

    # Bit lengths
    posBitLength = bitReader.read(BIT_LENGTH_BIT_LENGTH)
    xDeltaBitLength = bitReader.read(BIT_LENGTH_BIT_LENGTH)
    yOffsetBitLength = bitReader.read(BIT_LENGTH_BIT_LENGTH)

    # Initial position (optional)
    if posBitLength > 0:
        signOffset = getSignOffset(posBitLength)

        dense["xInitial"] = bitReader.read(posBitLength) - signOffset
        dense["yInitial"] = bitReader.read(posBitLength) - signOffset
    else:
        dense["xInitial"] = 0
        dense["yInitial"] = 0

    # Types
    typeCount = bitReader.read(TYPE_COUNT_BIT_LENGTH)

    dense["types"] = []
    for i in range(typeCount):
        typee = bitReader.read(TYPE_BIT_LENGTH)

        if typee > MAX_TYPE:
            root.debug(
                "Invalid voxel type {}, max {} near bit {}".format(
                    typee, MAX_TYPE, bitReader.cursor
                )
            )
            return
        dense["types"].append(typee)

    typeIndexBitLength, typeStopIndex = getTypeIndexInfo(typeCount)

    # Corners
    dense["corners"] = []

    xPos = dense["xInitial"]
    isFirst = True
    while bitReader.get_remaining() > 0:
        corner = {}

        # First corner does not have xDelta (0 assumed)
        if isFirst:
            corner["xDelta"] = None
            isFirst = False
        else:
            isMoveX = bool(bitReader.read(BOOLEAN_BIT_LENGTH))

            if isMoveX and xDeltaBitLength > 0:
                corner["xDelta"] = bitReader.read(xDeltaBitLength)
                xPos += corner["xDelta"]
            else:
                corner["xDelta"] = 0

        if yOffsetBitLength > 0:
            corner["yOffset"] = bitReader.read(yOffsetBitLength)
        else:
            corner["yOffset"] = 0

        corner["hasGround"] = bool(bitReader.read(BOOLEAN_BIT_LENGTH))

        # Voxels
        corner["voxels"] = []

        while len(corner["voxels"]) < MAX_HEIGHT:
            # Special case: when reading the last voxel in the last corner, if it is located exactly
            # at MAX_HEIGHT, the next typeStopIndex will be omitted. If we're trying to read a
            # typeIndex that has leading zeroes, given that there's no '1' from typeStopIndex, we
            #  might have removed the leading 0s as if they were padding and `.read` will throw.
            #
            # We could always return implicit zeroes from BitReader but then we'd lose the ability to
            # detect wrong reads.
            typeIndex = bitReader.read(typeIndexBitLength, True)

            if typeIndex == typeStopIndex:
                break

            typeIndexZeroBased = typeIndex - 1

            if typeIndexZeroBased < EMPTY_TYPE or typeIndexZeroBased >= typeCount:
                yPos = dense["yInitial"] + corner["yOffset"]
                root.debug(
                    "Invalid voxel type {}/{} at ({}, {}, {}) near bit {}".format(
                        typeIndexZeroBased,
                        typeCount,
                        xPos,
                        yPos,
                        len(corner["voxels"]) + 1,
                        bitReader.cursor,
                    )
                )
                return

            corner["voxels"].append(typeIndexZeroBased)

        # Only push the corner if it has voxels
        nonEmptyVoxels = [voxel for voxel in corner["voxels"] if voxel != EMPTY_TYPE]

        if corner["hasGround"] or len(nonEmptyVoxels) > 0:
            dense["corners"].append(corner)

    #root.debug(f"bitsToDense done :\n{dense}")
    return dense


# Get the uintN representation of a given value.
def bits(value, bitLength):
    if value < 0:
        root.debug(f"Trying to get bits for negative value {value}")
        return

    maxValue = getMaxValue(bitLength)

    if value > maxValue:
        root.debug(f"Trying to get bits for too large value {value} (max {maxValue})")
        return

    return "{0:b}".format(value).rjust(bitLength, "0")


def denseToBits(dense, pad=True):

    outString = ""

    # Detect bit lengths from values
    posBitLength = getSignedBitLength(
        min(dense["xInitial"], dense["yInitial"]),
        max(dense["xInitial"], dense["yInitial"]),
    )

    maxXDelta = 0
    maxYOffset = 0

    for corner in dense["corners"]:
        maxXDelta = max(
            maxXDelta, corner["xDelta"] if corner["xDelta"] is not None else 0
        )
        maxYOffset = max(maxYOffset, corner["yOffset"])

    xDeltaBitLength = getBitLength(maxXDelta)
    yOffsetBitLength = getBitLength(maxYOffset)

    # Bit lengths
    posBitLengthBits = bits(posBitLength, BIT_LENGTH_BIT_LENGTH)
    xDeltaBitLengthBits = bits(xDeltaBitLength, BIT_LENGTH_BIT_LENGTH)
    yOffsetBitLengthBits = bits(yOffsetBitLength, BIT_LENGTH_BIT_LENGTH)

    outString = (
        yOffsetBitLengthBits + xDeltaBitLengthBits + posBitLengthBits + outString
    )

    # Initial position (optional)
    if posBitLength > 0:
        signOffset = getSignOffset(posBitLength)

        xInitialBits = bits(dense["xInitial"] + signOffset, posBitLength)
        yInitialBits = bits(dense["yInitial"] + signOffset, posBitLength)

        outString = yInitialBits + xInitialBits + outString

    # Types
    if len(dense["types"]) > MAX_TYPE_COUNT:
        root.debug(f"Invalid types.length {dense.types.length}, max {MAX_TYPE_COUNT}")
        return

    typeCountBits = bits(len(dense["types"]), TYPE_COUNT_BIT_LENGTH)
    outString = typeCountBits + outString

    for typee in dense["types"]:
        if typee < 0 or typee > MAX_TYPE:
            root.debug(f"Invalid type {typee}, max {MAX_TYPE}")
            return

        typeBits = bits(typee, TYPE_BIT_LENGTH)
        outString = typeBits + outString

    typeIndexBitLength, typeStopIndex = getTypeIndexInfo(len(dense["types"]))

    # Corners
    cornersWithData = [
        corner
        for i, corner in enumerate(dense["corners"])
        if i == 0 or corner["hasGround"] or len(corner["voxels"]) > 0
    ]

    # Ensure there's at least one (empty) corner
    # Townscaper encodes the empty map as AAAE, but without this we'd output AAAA
    corners = (
        cornersWithData
        if len(cornersWithData) > 0
        else [{"xDelta": None, "hasGround": False, "voxels": []}]
    )
    isFirst = True

    for corner in corners:

        # First corner does not have xDelta (must be null)
        if isFirst:
            if corner["xDelta"] is not None:
                root.debug("xDelta on first corner")
                return

            isFirst = False
        else:
            hasXDeltaBits = bits(1 if corner["xDelta"] else 0, BOOLEAN_BIT_LENGTH)
            outString = hasXDeltaBits + outString

            if corner["xDelta"]:
                xDeltaBits = bits(corner["xDelta"], xDeltaBitLength)
                outString = xDeltaBits + outString

        if yOffsetBitLength > 0:
            yOffsetBits = bits(corner["yOffset"], yOffsetBitLength)
            outString = yOffsetBits + outString

        hasGroundBits = bits(1 if corner["hasGround"] else 0, BOOLEAN_BIT_LENGTH)
        outString = hasGroundBits + outString

        # Voxels
        if len(corner["voxels"]) > MAX_HEIGHT:
            root.debug(f"Too many voxels ({corner.voxels.length}), max {MAX_HEIGHT}")
            return

        for typeIndexZeroBased in corner["voxels"]:
            if typeIndexZeroBased < EMPTY_TYPE or typeIndexZeroBased >= len(
                dense["types"]
            ):
                root.debug(
                    f"Invalid type {typeIndexZeroBased}, min 0, max {len(dense['types'])}"
                )
                return

            typeIndexZeroBasedBits = bits(typeIndexZeroBased + 1, typeIndexBitLength)
            outString = typeIndexZeroBasedBits + outString

        # Omit typeStopIndexBits if we reached the max height
        if len(corner["voxels"]) < MAX_HEIGHT:
            typeStopIndexBits = bits(typeStopIndex, typeIndexBitLength)
            outString = typeStopIndexBits + outString

    # Padding
    if pad:
        paddingLength = (
            BITS_PER_CHAR - (len(outString) % BITS_PER_CHAR)
        ) % BITS_PER_CHAR

        if paddingLength > 0:
            paddingBits = "0" * paddingLength

            outString = paddingBits + outString

    #
    #root.debug(f"denseToBits done :\n{outString}")
    return outString


def denseToSparse(dense):
    if len(dense["types"]) > MAX_TYPE_COUNT:
        root.debug(f"Too many types ({len(dense['types'])}), max {MAX_TYPE_COUNT}")
        return

    if dense["corners"][0]["xDelta"] is not None:
        root.debug(f"First xDelta ({dense['corners'][0]['xDelta']}) is not null")
        return

    sparse = []

    x = dense["xInitial"]

    # Corners
    for denseCorner in dense["corners"]:
        if denseCorner["xDelta"]:
            x += denseCorner["xDelta"]

        y = dense["yInitial"] + (denseCorner["yOffset"] or 0)

        # Voxels
        voxels = {}

        if denseCorner["hasGround"]:
            voxels[GROUND_HEIGHT] = GROUND_TYPE

        if len(denseCorner["voxels"]) > MAX_HEIGHT:
            root.debug(
                f"Too many voxels ({len(denseCorner['voxels'])}), max {MAX_HEIGHT}"
            )
            return

        for h in range(len(denseCorner["voxels"])):
            typee = denseCorner["voxels"][h]

            if typee == EMPTY_TYPE:
                continue

            if not isinstance(typee, int):
                root.debug(f"Invalid voxel typee {typee} at ({x}, {y}, {h + 1})")
                return

            if typee < EMPTY_TYPE or typee >= len(dense["types"]):
                root.debug(
                    f"Invalid voxel typee {typee} at ({x}, {y}, {h + 1}), min {EMPTY_TYPE}, max {len(dense['types']) - 1}"
                )
                return

            voxels[h + (GROUND_HEIGHT + 1)] = dense["types"][typee]

        if len(voxels) > 0:
            sparse.append({"x": x, "y": y, "voxels": voxels})

    #root.debug(f"denseToSparse done :\n{sparse}")
    return sparse


def sparseToDense(sparse):
    dense = {}

    sortedSparseCorners = []
    for sparseCorner in sparse:
        groundVoxel = (
            sparseCorner["voxels"][GROUND_HEIGHT]
            if GROUND_HEIGHT in sparseCorner["voxels"]
            else None
        )

        if groundVoxel != None and groundVoxel != GROUND_TYPE:
            root.debug(
                f"Trying to set voxel typee {sparseCorner['voxels'][0]} on ground, only {GROUND_TYPE} allowed"
            )
            return

        sparseCorner["hasGround"] = groundVoxel == GROUND_TYPE
        sparseCorner["voxels"] = {
            h: t for h, t in sparseCorner["voxels"].items() if t is not None
        }

        if sparseCorner["hasGround"] or len(sparseCorner["voxels"]) > 0:
            sortedSparseCorners.append(sparseCorner)

    sortedSparseCorners.sort(key=lambda a: (a["x"], a["y"]))
    # TODO: Throw here? We shouldn't have two corners with the same coordinates. Merge maybe?

    if len(sortedSparseCorners) == 0:
        return {"xInitial": 0, "yInitial": 0, "types": [], "corners": []}
    # Analyze voxels for yInitial and types
    minY = inf
    types = []

    for sparseCorner in sortedSparseCorners:
        minY = min(minY, sparseCorner["y"])

        for heightString, typee in sparseCorner["voxels"].items():
            if typee is None:
                continue

            height = int(heightString)

            if height > MAX_HEIGHT:
                root.debug(f"Invalid height {height}, max {MAX_HEIGHT}")
                return

            if not isinstance(typee, int):
                root.debug(f"Voxel typee {typee} is not an index")
                return

            if typee < 0 or typee > MAX_TYPE:
                root.debug(f"Invalid voxel typee {type}, min 0, max {MAX_TYPE}")
                return

            if typee not in types and (height != GROUND_HEIGHT or typee != GROUND_TYPE):
                types.append(typee)

    if len(types) > MAX_TYPE_COUNT:
        root.debug(f"Too many types ({types.length}), max {MAX_TYPE_COUNT}")
        return

    dense["xInitial"] = sortedSparseCorners[0]["x"]
    dense["yInitial"] = minY
    types.sort()
    dense["types"] = types

    # Corners
    dense["corners"] = []

    currentX = dense["xInitial"]

    for sparseCorner in sortedSparseCorners:
        xDelta = sparseCorner["x"] - currentX if len(dense["corners"]) != 0 else None

        currentX = sparseCorner["x"]

        yOffset = sparseCorner["y"] - dense["yInitial"]

        maxHeight = max(sparseCorner["voxels"].keys())

        voxels = []

        for i in range((GROUND_HEIGHT + 1), maxHeight + 1):
            typee = sparseCorner["voxels"][i] if i in sparseCorner["voxels"] else None

            if typee is None:
                voxels.append(EMPTY_TYPE)
            else:
                voxels.append(types.index(typee))

        dense["corners"].append(
            {
                "xDelta": xDelta,
                "yOffset": yOffset,
                "hasGround": sparseCorner["hasGround"],
                "voxels": voxels,
            }
        )

    #root.debug(f"sparseToDense done :\n{dense}")
    return dense


# TEMPORARY CONVERSION : from sparse to corvox
def sparseToCorvox(sparse):

    corvox = {}

    for sparseCorner in sparse:

        key = sparseCorner["x"], sparseCorner["y"]
        count = len(sparseCorner["voxels"])

        corvox[key] = {"count": count, "voxels": sparseCorner["voxels"]}

    return corvox


# TEMPORARY CONVERSION : from corvox to sparse
def corvoxToSparse(corvox):

    sparse = []

    for (x, y), countAndVoxels in corvox.items():
        if countAndVoxels['voxels'] != {}:
            sparse.append({"x": x, "y": y, "voxels": countAndVoxels["voxels"]})

    return sparse
