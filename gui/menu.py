from random import choice

from gui.tools import MyLabel, SmartLabel
from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
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
        self.Backgrounds = ["Pictures\\Back1.png", "Pictures\\Back2.png", "Pictures\\Back3.png"]


    def changeIm(self):
        def changeBack():
            otherBacks = self.Backgrounds.copy()
            otherBacks.remove(self.myIm.source)
            self.myIm.source = choice(otherBacks)

        anim1 = Animation(opacity=0, duration=1, t='out_circ')
        anim2 = Animation(opacity=1, duration=1, t='out_circ')

        if self.myIm.mouse:
            anim1.start(self.myIm)      
            Clock.schedule_once(lambda dt: changeBack(), 1)
            Clock.schedule_once(lambda dt: anim2.start(self.myIm), 1)
