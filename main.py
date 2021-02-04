import sys  # isort:skip
from os.path import abspath, exists  # isort:skip
from os import environ, mkdir  # isort:skip
from kivy.resources import resource_add_path, resource_find  # isort:skip

if __name__ == "__main__":  # isort:skip
    if hasattr(sys, "_MEIPASS"):  # isort:skip
        resource_add_path(os.path.join(sys._MEIPASS))  # isort:skip

# No logs
environ["KIVY_NO_CONSOLELOG"] = "True"  # isort:skip

from kivy.config import Config  # isort:skip

if exists("log") is False:
    mkdir("log")  # isort:skip
Config.setall(
    "kivy", {"log_dir": abspath("log"), "log_maxfiles": 10, "exit_on_escape": 0}
)  # isort:skip

import gui.tools
from bin.Town_table import *
from bin.Town_waiter import *
from gui.dig import DigScreen
from gui.level import LevelScreen
from gui.menu import MenuScreen
from gui.merge import MergeScreen
from gui.paint import PaintScreen
from gui.replicate import ReplicateScreen
from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager

# Window configuration
Window.minimum_height = 600
Window.minimum_width = 800

# Police added
KIVY_FONTS = [
    {
        "name": "Garamond",
        "fn_regular": "gui\\Garamond Regular.ttf",
    }
]

for font in KIVY_FONTS:
    LabelBase.register(**font)

# Utility class
class Utility(object):
    def __init__(self):

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
        init_townshell()

    # Undo
    def undo(self):
        return undoClip()

    # Redo
    def redo(self):
        return redoClip()


class MainManager(FloatLayout):
    pass


class ScreenManagerApp(App):
    util = Utility()
    icon = "Pictures\\TownShell.png"
    title = "TownShell"

    def build(self):
        return Builder.load_file(r"gui\screenmanager.kv")


if __name__ == "__main__":
    ScreenManagerApp().run()
