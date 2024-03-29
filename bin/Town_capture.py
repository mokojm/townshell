"""
Alternative screen capture device, when there is no camera of webcam connected
to the desktop.
"""

from datetime import datetime
from logging import getLogger
from math import cos, radians, sin
from os import getcwd, remove
from os.path import join
from threading import Thread
from time import sleep, time

import ffmpeg
from keyboard import is_pressed
from mouse import get_position
from mouse import is_pressed as is_mpressed
from mouse import move as mouse_move
from mouse import press, release
from mss.factory import mss

root = getLogger("Town.capture")


class TownCapture:
    """
    Captures a Townscaper application
    """

    def __init__(self, **kwargs):

        # mss instance for screenshot of Townscaper
        self.sct = mss("Townscaper")
        self.process = None  # ffmpeg process to handle encoding of the video
        self.region = None  # Used by 'record' to know the dimension of the output

        # Time management
        self._time_start = time()
        self._time_taken = 0
        self._time_average = 0.04

        # For record
        self.dirname = kwargs.get("dirname", "")
        self.target_fps = kwargs.get("target_fps")
        self.bts_vs_size = 3000 / (1920 * 1080)  # kbits/seconds/pixels
        self.preset = kwargs.get("preset", "ultrafast")
        self.force_bitrate = kwargs.get("bitrate")
        self.loglevel = "info" if kwargs.get("loglevel") == "DEBUG" else "quiet"
        root.debug(kwargs)

        # Benchmark
        self.is_recording = False

        # logging
        root.debug("Capture instance initialized")

    def __getitem__(self, item):
        return self._grab()

    def __next__(self):
        return self._grab()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and isinstance(exc_type, StopIteration):
            return True
        return False

    @property
    def path_to_disk(self):
        return join(
            self.dirname,
            "capture_{}.mp4".format(datetime.now().strftime("%Y%m%d%H%M%S")),
        )

    @property
    def fps(self):
        return int(1 / self._time_average) * (self._time_average > 0)

    @property
    def size(self):
        self.sct.update_window()
        return (
            self.sct.window if self.sct.window else self.sct.monitors[0]
        )  # Example : {"left": 0, "top": 0, "width": 1920, "height": 1080}

    def screenshot(self):

        self.is_recording = True
        img = self._grab()
        self.is_recording = False

        root.debug("Screenshot taken")
        return img

    def _grab(self, raw=True):

        img = self.sct.grab(self.sct.window, raw)

        # This makes sure that the FPS are taken in comparison to screenshots rates and vary only slightly.
        self._time_taken, self._time_start = time() - self._time_start, time()
        self._time_average = self._time_average * 0.95 + self._time_taken * 0.05

        return img

    def shotoqueue(self):
        """PUT process"""
        self.process.stdin.write(self._grab())

        sleep(max(0, 1 / self.target_fps - self._time_taken))

        # print(f"\rCapture framerate: {self.fps}", end='')

    def start_recorder(self):

        self.is_recording = True
        self.region = self.size if self.region is None else self.region
        path = self.path_to_disk

        # bitrate = amount_pixels * standard_bit_per_seconds / standard_amount_pixels
        if self.force_bitrate:
            bitrate = self.force_bitrate
        else:
            bitrate = round(
                self.region["width"] * self.region["height"] * self.bts_vs_size
            )
            root.debug(f"Bitrate: {bitrate}")

        SCREEN_SIZE = self.region["width"], self.region["height"]
        root.debug(f"Settings : {SCREEN_SIZE} ; {self.target_fps}")

        self.process = (
            ffmpeg.input(
                "pipe:",
                format="rawvideo",
                pix_fmt="bgra",
                fflags="discardcorrupt",
                s="{}x{}".format(self.region["width"], self.region["height"]),
            )
            .output(
                path,
                r=self.target_fps,
                pix_fmt="yuv420p",
                preset=self.preset,
                loglevel=self.loglevel,
                tune="zerolatency",
                **{"c:v": "libx264", "b:v": bitrate * 1000},
            )
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )

    def stop_recorder(self):
        """None indicate to record method that it's the end of recording"""
        self.process.stdin.close()
        self.process.wait()
        self.is_recording = False

    def capture(self, duration):

        if self.is_recording is False:
            return "record is not started"

        start = time()

        while "capture ongoing":

            if is_pressed("backspace") or time() - start > duration:
                break

            else:
                self.shotoqueue()


# Townscaper screen data
RIGHTSPACE = 300
LEFTSPACE = 70
MIN_WIDTH = 400


def move(x, y, absolute=True, duration=0, steps_per_second=120.0, synchro=None):
    """
    Same with mouse module move function except it checks whether the keyboard key 'backspace' is pressed or not between steps
    synchro is used to stop for unexpected reason
    """
    x = int(x)
    y = int(y)

    # Requires an extra system call on Linux, but `move_relative` is measured
    # in millimiters so we would lose precision.
    position_x, position_y = get_position()

    if not absolute:
        x = position_x + x
        y = position_y + y

    if duration:
        start_x = position_x
        start_y = position_y
        dx = x - start_x
        dy = y - start_y

        if dx == 0 and dy == 0:
            sleep(duration)
        else:
            # 'steps_per_second' movements per second, default is 120.
            # Round and keep float to ensure float division in Python 2
            steps = max(1.0, float(int(duration * float(steps_per_second))))
            for i in range(int(steps) + 1):
                mouse_move(start_x + dx * i / steps, start_y + dy * i / steps)
                if is_pressed("backspace") or synchro.is_set() is False:
                    return False
                sleep(duration / steps)
    else:
        mouse_move(x, y)

    # Feedback
    return True


def mydrag(
    start_x,
    start_y,
    end_x,
    end_y,
    absolute=True,
    duration=0,
    button="left",
    synchro=None,
):
    """
    Holds the right mouse button, moving from start to end position, then
    releases. `absolute` and `duration` are parameters regarding the mouse
    movement.
    """
    if is_mpressed(button):
        release(button)
    move(start_x, start_y, absolute, 0)
    press(button)
    answer = move(end_x, end_y, absolute, duration, synchro=synchro)
    release(button)
    return answer


def isShowcasable(pixels, duration, tomodify="duration"):
    """
    Calculate the speed, the mouse would need to reach and return True if it's considered feasible or a string precising what's wrong
    """

    MINSPEED = 40.0
    MAXSPEED = 2000.0

    speed = pixels / duration

    if (
        MINSPEED < speed < MAXSPEED or pixels == 0
    ):  # pixels = 0 means the capture is made without any computed move
        return True
    elif speed < MINSPEED:
        if tomodify == "duration":
            change = round(pixels / (MINSPEED + 1))
        else:
            change = duration * MINSPEED
        return f"Mouse move would be too slow: try {tomodify} : {change}"
    else:
        if tomodify == "duration":
            change = round(pixels / (MAXSPEED - 1))
        else:
            change = duration * MAXSPEED
        return f"Mouse move would be too fast: try {tomodify} : {change}"


def setShow(**kwargs):
    """
    Prepare the positions for the show
    """

    root.debug(f"Settings : {kwargs}")
    # Initialize
    region = kwargs.get("region")
    start = kwargs.get("start", "top-left")
    pixels = kwargs.get("pixels", 500)
    angle = kwargs.get("angle", 0)
    percent = 100

    LIMIT_LEFT = region["left"] + LEFTSPACE
    LIMIT_RIGHT = region["left"] + region["width"] - RIGHTSPACE
    LIMIT_UP = region["top"] + 50
    LIMIT_DOWN = region["top"] + region["height"] - 50

    MAX_LEN = (
        (LIMIT_RIGHT - LIMIT_LEFT) * cos(radians(angle))
        if angle <= 45
        else (LIMIT_DOWN - LIMIT_UP) * cos(radians(90 - angle))
    )  # Distance the mouse can do without having to get back to start position
    MAX_LEN = round(MAX_LEN)

    if start == "top-left":
        startX, startY = LIMIT_LEFT, LIMIT_UP
    elif start == "top-right":
        startX, startY = LIMIT_RIGHT, LIMIT_UP
    elif start == "bottom-left":
        startX, startY = LIMIT_LEFT, LIMIT_DOWN
    elif start == "bottom-right":
        startX, startY = LIMIT_RIGHT, LIMIT_DOWN

    # Calculate the end point
    if pixels < MAX_LEN:
        cycle = 1
        if start == "top-left":
            endX, endY = startX + pixels * cos(radians(angle)), startY + pixels * sin(
                radians(angle)
            )
        elif start == "top-right":
            endX, endY = startX - pixels * cos(radians(angle)), startY + pixels * sin(
                radians(angle)
            )
        elif start == "bottom-left":
            endX, endY = startX + pixels * cos(radians(angle)), startY - pixels * sin(
                radians(angle)
            )
        elif start == "bottom-right":
            endX, endY = startX - pixels * cos(radians(angle)), startY - pixels * sin(
                radians(angle)
            )

        lastX = endX
        lastY = endY

    else:
        lastLen = pixels % MAX_LEN
        cycle = int(pixels / MAX_LEN)
        percent = lastLen / MAX_LEN

        if start == "top-left":
            endX, endY = startX + MAX_LEN * cos(radians(angle)), startY + MAX_LEN * sin(
                radians(angle)
            )
            lastX, lastY = (
                startX + lastLen * cos(radians(angle)),
                startY + lastLen * sin(radians(angle)),
            )
        elif start == "top-right":
            endX, endY = startX - MAX_LEN * cos(radians(angle)), startY + MAX_LEN * sin(
                radians(angle)
            )
            lastX, lastY = (
                startX - lastLen * cos(radians(angle)),
                startY + lastLen * sin(radians(angle)),
            )
        elif start == "bottom-left":
            endX, endY = startX + MAX_LEN * cos(radians(angle)), startY - MAX_LEN * sin(
                radians(angle)
            )
            lastX, lastY = (
                startX + lastLen * cos(radians(angle)),
                startY - lastLen * sin(radians(angle)),
            )
        elif start == "bottom-right":
            endX, endY = startX - MAX_LEN * cos(radians(angle)), startY - MAX_LEN * sin(
                radians(angle)
            )
            lastX, lastY = (
                startX - lastLen * cos(radians(angle)),
                startY - lastLen * sin(radians(angle)),
            )

        # Round
        lastX, lastY = round(lastX), round(lastY)

    # Round
    endX, endY = round(endX), round(endY)

    # Return
    return startX, startY, endX, endY, lastX, lastY, MAX_LEN, cycle, percent


# region : {left, top, width, height} region of Townscaper window
# rythm : only 'linear' and 'round-trip' are available for now
# def showcase(region, button='left', start='top-left', pixels=500, duration=5, angle=0, rythm='linear'):  #Previous declaration
def showcase(**kwargs):

    """
    Angle is done from horizontal
    """

    # Initialization
    button = kwargs.get("button", "left")
    start = kwargs.get("start", "top-left")
    pixels = kwargs.get("pixels", 500)
    duration = kwargs.get("duration", 5)
    rythm = kwargs.get("rythm", "linear")
    synchro = kwargs.get("synchro")  # Event object to synchronize capture process

    # Time of pause
    pause = 1 / 30

    # Settings
    startX, startY, endX, endY, lastX, lastY, MAX_LEN, cycle, percent = setShow(
        **kwargs
    )
    root.debug(
        f"Positions : {(startX, startY, endX, endY, lastX, lastY, MAX_LEN, cycle, percent)}"
    )

    # Fetching the initial position of the mouse
    initPos = get_position()

    # Capture is launched if necessary
    if synchro:
        synchro.set()
    # Time to move the mouse

    if pixels < MAX_LEN and rythm == "linear":
        mydrag(
            startX,
            startY,
            endX,
            endY,
            button=button,
            duration=duration,
            synchro=synchro,
        )

    elif pixels < MAX_LEN and rythm == "round-trip":
        thisDuration = duration / 2
        mydrag(
            startX,
            startY,
            endX,
            endY,
            button=button,
            duration=thisDuration,
            synchro=synchro,
        )
        sleep(pause)
        mydrag(
            endX,
            endY,
            startX,
            startY,
            button=button,
            duration=thisDuration,
            synchro=synchro,
        )

    elif rythm == "linear":
        baseDuration = duration / (cycle + percent)
        for _ in range(cycle):
            if not mydrag(
                startX,
                startY,
                endX,
                endY,
                button=button,
                duration=baseDuration,
                synchro=synchro,
            ):
                return move(*initPos)
            sleep(pause)

        mydrag(
            startX,
            startY,
            lastX,
            lastY,
            button=button,
            duration=percent * baseDuration,
            synchro=synchro,
        )

    elif rythm == "round-trip":
        baseDuration = duration / (cycle + percent) / 2

        for _ in range(cycle):
            if not mydrag(
                startX,
                startY,
                endX,
                endY,
                button=button,
                duration=baseDuration,
                synchro=synchro,
            ):
                return move(*initPos)
            sleep(pause)

        if not mydrag(
            startX,
            startY,
            lastX,
            lastY,
            button=button,
            duration=percent * baseDuration,
            synchro=synchro,
        ):
            return move(*initPos)
        sleep(pause)
        if not mydrag(
            lastX,
            lastY,
            startX,
            startY,
            button=button,
            duration=percent * baseDuration,
            synchro=synchro,
        ):
            return move(*initPos)
        sleep(pause)

        for _ in range(cycle):
            if not mydrag(
                endX,
                endY,
                startX,
                startY,
                button=button,
                duration=baseDuration,
                synchro=synchro,
            ):
                return move(*initPos)
            sleep(pause)
    else:
        root.debug("Issue on showcase")
        move(*initPos)
        return "Unexpected error"

    # Back to initial position
    move(*initPos)

    # Return
    root.debug("Move finished")
    return True


if __name__ == "__main__":
    sleep(2)
    showcase(
        {"left": 0, "top": 0, "width": 1920, "height": 1080},
        button="left",
        start="top-right",
        duration=5,
        pixels=10000,
        angle=0,
        rythm="round-trip",
    )

    # with TownCapture(target_fps = 30, dirname=r'C:\Users\Jean-Marie\Documents\GitHub\townshell\temp\directory') as capture:
    #     sleep(15)
    #     capture.start_recording()
    #     for _ in range(100):
    #         capture.shotoqueue()
    #     capture.stop_recording()
