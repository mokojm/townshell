import sys
from multiprocessing import freeze_support
from os import environ, mkdir
from os.path import abspath, exists

if __name__ == "__main__":
    freeze_support()
    from bin.Town_table import *
    from bin.Town_waiter import Utility


def main():

    from kivy.resources import resource_add_path, resource_find

    if __name__ == "__main__":
        if hasattr(sys, "_MEIPASS"):
            resource_add_path(os.path.join(sys._MEIPASS))

    # No logs
    environ["KIVY_NO_CONSOLELOG"] = "True"

    from kivy.config import Config

    # isort:skip
    Config.setall(
        "kivy", {"log_dir": abspath("log"), "log_maxfiles": 10, "exit_on_escape": 0}
    )  # isort:skip

    import gui.tools
    from gui.dig import DigScreen
    from gui.level import LevelScreen
    from gui.menu import MenuScreen
    from gui.merge import MergeScreen
    from gui.paint import PaintScreen
    from gui.replicate import ReplicateScreen
    from gui.capture import CaptureScreen
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

    class MainManager(FloatLayout):
        pass

    class ScreenManagerApp(App):
        util = Utility()
        icon = "Pictures\\TownShell.png"
        title = "TownShell"

        def build(self):
            return Builder.load_file(r"gui\screenmanager.kv")

    # Main part
    mainApp = ScreenManagerApp()
    try:
        mainApp.run()
    except:
        mainApp.util.end_core(-1)
        raise
    else:
        mainApp.util.end_core()


# Cmd-line function
def townShell(args):

    util = Utility()
    feedback = None
    cmd = args[0]
    if len(args) > 1:
        settings = parse(" ".join(args[1:]))

    if cmd == "level":
        feedback = util.level(settings)
    elif cmd == "paint":
        feedback = util.paint(settings)
    elif cmd == "replicate":
        feedback = util.replicate(settings)
    elif cmd == "dig":
        feedback = util.dig(settings)
    elif cmd == "merge":
        feedback = util.merge(settings)
    elif cmd == "write":
        settings = None
        feedback = util.write(settings)

    if feedback is False:
        print("Error, check 'town.log'")
    elif feedback is None:
        print("Wrong command")
    else:
        print("Successful execution")


if __name__ == "__main__":

    # Handle cli and gui TownShell
    args = sys.argv
    if len(args) > 0 and ".py" in args[0]:
        args = args[1:]

    # No commands, TownShell ui will be loaded
    if len(args) == 0 or ".exe" in args[0]:
        main()

    # Command line version
    else:
        townShell(args)
