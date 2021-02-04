from gui.tools import HeightSlideTextInput
from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

Builder.load_file(r"gui\level.kv")


class LevelScreen(Screen):
    def __init__(self, **kwargs):
        self.util = App.get_running_app().util
        super(LevelScreen, self).__init__(**kwargs)
        self.touched_height_box = None

    def minHeightCheck(self, *args):
        if self.box_max.max_height.value < self.box_min.min_height.value:
            self.box_max.max_height.value = self.box_min.min_height.value

    def maxHeightCheck(self, *args):
        if self.box_min.min_height.value > self.box_max.max_height.value:
            self.box_min.min_height.value = self.box_max.max_height.value
        if self.box_height.myheight.value > self.box_max.max_height.value:
            self.box_height.myheight.value = self.box_max.max_height.value

    def heightCheck(self, *args):
        if self.box_height.myheight.value > self.box_max.max_height.value:
            self.box_max.max_height.value = self.box_height.myheight.value

    def save_to_clipboard(self):
        settings = {
            "height": int(self.box_height.myheight.value),
            "plain": self.box_plain.myplain.active,
            "maxh": int(self.box_max.max_height.value),
            "minh": int(self.box_min.min_height.value),
            "cf": self.box_fc.myfc.text,
            "color": self.box_newc.mync.text,
        }

        myPopUp = Factory.NotifPopUp()
        myPopUp.title = "Level"
        if self.util.level(settings):
            myPopUp.level = "INFO"
            myPopUp.mytext = "Click 'Load from Clipboard'"
        else:
            myPopUp.level = "ERROR"
            myPopUp.mytext = "See 'town.log' for more information"
        myPopUp.open()
