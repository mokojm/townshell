from ctypes import create_unicode_buffer, windll, wintypes
from logging import getLogger
from platform import system
from time import sleep, time

from keyboard import is_pressed as is_clipped
from keyboard import on_release, send, unhook_all
from mouse import click, is_pressed

# Logging
root = getLogger("Town.shortcuts")

# Return the active window title (Work only on Windows system)
def getForegroundWindowTitle():
    hWnd = windll.user32.GetForegroundWindow()
    length = windll.user32.GetWindowTextLengthW(hWnd)
    buf = create_unicode_buffer(length + 1)
    windll.user32.GetWindowTextW(hWnd, buf, length + 1)

    return buf.value


# Detect whether another numpad click happenned a determined time before
def numpad_click(key):
    global amount
    global previous_time

    if key.name.isdigit() and key.name != "²":
        current_time = time()

        if current_time - previous_time < 1.0 and amount != 0:
            amount = int("".join((str(amount), key.name)))

        else:
            amount = int(key.name)

        previous_time = current_time


# Main function activating the keyboard shortcuts to perform fast click on Townscaper
# stopnow: Event determining if the main loop should be running or not
# shortcuts: dictionary of the keyboard shortcuts to be used
def shortcut(stopnow, shortcuts):

    # lclick: Keyboard shortcut for fast left click
    # rclick: Keyboard shortcut for fast right click
    # undo: Keyboard shortcut for fast 'Undo'
    # redo: Keyboard shortcut for fast 'Redo'
    # custom_lclick: Keyboard shortcut for fast left click for a chosen number of times
    # custom_rclick: Keyboard shortcut for fast right click for a chosen number of times
    # custom_undo: Keyboard shortcut for fast 'Undo' for a chosen number of times
    # custom_redo: Keyboard shortcut for fast 'Redo' for a chosen number of times
    # pause: Time in seconds to wait between clicks
    lclick = shortcuts["left_click"]
    rclick = shortcuts["right_click"]
    undo = shortcuts["undo"]
    redo = shortcuts["redo"]
    custom_lclick = shortcuts["custom_left_click"]
    custom_rclick = shortcuts["custom_right_click"]
    custom_undo = shortcuts["custom_undo"]
    custom_redo = shortcuts["custom_redo"]
    pause = shortcuts["pause"]

    global amount
    amount = 0
    global previous_time
    previous_time = 0.0
    on_release(numpad_click)

    # Checks what's the platform
    if system() == "Windows":
        os_is_windows = True
    else:
        os_is_windows = False

    # Main loop
    while True:

        # Handling stopnow
        if stopnow.is_set():
            root.debug("STOPNOW received")
            break

        # On Windows checks that the active window is Townscaper
        # On other system it does not check
        if os_is_windows:
            # root.debug("Current screen : %s", getForegroundWindowTitle())
            if "Townscaper" not in getForegroundWindowTitle():
                sleep(0.05)
                continue

        # Fast add block
        if is_clipped(lclick):
            click()

        # Fast erase block
        elif is_clipped(rclick):
            click("right")

        # Fast undo
        elif is_clipped(undo):
            send("ctrl+z")

        # Fast redo
        elif is_clipped(redo):
            send("ctrl+x")

        # Fast chosen amount add
        elif is_clipped(custom_lclick):
            for i in range(amount):
                click()
                sleep(pause)

        # Fast chosen amount erase
        elif is_clipped(custom_rclick):
            for i in range(amount):
                click("right")
                sleep(pause)

        # Fast chosen amount undo
        elif is_clipped(custom_undo):
            for i in range(amount):
                send("ctrl+z")
                sleep(pause)

        # Fast chosen amount redo
        elif is_clipped(custom_redo):
            for i in range(amount):
                send("ctrl+y")
                sleep(pause)

        sleep(pause)

    # Last operation if a stop or a break happen, all hotkeys are unhooked
    unhook_all()
