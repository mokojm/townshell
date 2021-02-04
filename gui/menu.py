from gui.tools import MyLabel, SmartLabel
from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

Builder.load_file(r"gui\menu.kv")


class KeyboardSwitch(Button):
    def switch(self, *args):
        if self.active:
            self.active = False
        else:
            self.active = True


class ShortcutLabel(SmartLabel):
    def on_enter(self):

        self.myPopUp = Factory.KeyboardPopup()
        self.myPopUp.open()

    def on_leave(self):
        self.myPopUp.dismiss()


class MenuScreen(Screen):
    def __init__(self, **kwargs):

        super(MenuScreen, self).__init__(**kwargs)
        util = App.get_running_app().util
