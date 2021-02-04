from gui.tools import HeightSlideTextInput
from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

Builder.load_file(r"gui\replicate.kv")


class ReplicateScreen(Screen):
    def __init__(self, **kwargs):
        self.util = App.get_running_app().util
        super(ReplicateScreen, self).__init__(**kwargs)

    def save_to_clipboard(self):
        settings = {
            "height": int(self.box_height.myheight.value),
            "plain": self.box_plain.myplain.active,
            "copy": int(self.box_cop.cop.value),
            "cf": self.box_fc.myfc.text,
            "color": self.box_newc.mync.text,
        }
        #print(settings)

        myPopUp = Factory.NotifPopUp()
        myPopUp.title = "Replicate"
        if self.util.replicate(settings):
            myPopUp.level = "INFO"
            myPopUp.mytext = "Click 'Load from Clipboard'"
        else:
            myPopUp.level = "ERROR"
            myPopUp.mytext = "See 'town.log' for more information"
        myPopUp.open()
