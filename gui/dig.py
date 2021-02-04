from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

Builder.load_file(r"gui\dig.kv")


class DigScreen(Screen):
    def __init__(self, **kwargs):

        self.util = App.get_running_app().util
        super(DigScreen, self).__init__(**kwargs)

    def save_to_clipboard(self):

        filters = tuple(
            int(child.text)
            for child in self.box_filter.children
            if child.name == "colspin" and child.text != ""
        )

        # Heights
        hfs = int(self.box_hf.hfs.value)
        hfe = int(self.box_hf.hfe.value)
        hf_filter = hfs if hfs == hfe else ((hfs, hfe),)

        settings = {
            "percent": int(self.box_per.per.value),
            "cf": filters,
            "height": hf_filter,
        }
        #print(settings)

        myPopUp = Factory.NotifPopUp()
        myPopUp.title = "Dig"
        if self.util.dig(settings):
            myPopUp.level = "INFO"
            myPopUp.mytext = "Click 'Load from Clipboard'"
        else:
            myPopUp.level = "ERROR"
            myPopUp.mytext = "See 'town.log' for more information"
        myPopUp.open()
