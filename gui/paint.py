from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

Builder.load_file(r"gui\paint.kv")


class PaintScreen(Screen):
    def __init__(self, **kwargs):

        self.util = App.get_running_app().util
        super(PaintScreen, self).__init__(**kwargs)

    def save_to_clipboard(self):

        if any([child.text == "R" for child in self.box_color.children]):
            colors = "random"
        else:
            colors = tuple(
                child.text if child.text == "r" else int(child.text)
                for child in self.box_color.children
                if child.name == "colspin" and child.text != ""
            )

        filters = tuple(
            int(child.text)
            for child in self.box_filter.children
            if child.name == "colspin" and child.text != ""
        )

        hfs = int(self.box_hf.hfs.value)
        hfe = int(self.box_hf.hfe.value)
        hf_filter = hfs if hfs == hfe else ((hfs, hfe),)

        settings = {"color": colors, "cf": filters, "height": hf_filter, "alternate":self.box_alt.myplain.active}
        #print(settings)

        myPopUp = Factory.NotifPopUp()
        myPopUp.title = "Paint"
        if self.util.paint(settings):
            myPopUp.level = "INFO"
            myPopUp.mytext = "Click 'Load from Clipboard'"
        else:
            myPopUp.level = "ERROR"
            myPopUp.mytext = "See 'town.log' for more information"
        myPopUp.open()

    def reset(self):
        self.box_alt.myplain.active = False
        self.box_hf.hfs.value = 0
        self.box_hf.hfe.value = 255
        self.box_color.reset()
        self.box_filter.reset()
