from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

Builder.load_file(r"gui\flip.kv")


class FlipScreen(Screen):
    def __init__(self, **kwargs):

        self.util = App.get_running_app().util
        super(FlipScreen, self).__init__(**kwargs)

    def save_to_clipboard(self):

        filters = tuple(
            int(child.text)
            for child in self.box_filter.children
            if child.name == "colspin" and child.text != ""
        )

        settings = {
            "color_filter": filters,
            "color": self.box_newc.mync.text,
            "copy": self.box_cop.cop.text,
        }
        # print(settings)

        myPopUp = Factory.NotifPopUp()
        myPopUp.title = "Flip"
        if self.util.flip(**settings):
            myPopUp.level = "INFO"
            myPopUp.mytext = "Click 'Load from Clipboard'"
        else:
            myPopUp.level = "ERROR"
            myPopUp.mytext = "See 'town.log' for more information"
        myPopUp.open()

    def reset(self):
        self.box_newc.mync.text = ""
        self.box_cop.cop.text = "None"
        self.box_filter.reset()
