from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

Builder.load_file(r"gui\dig.kv")


class DigScreen(Screen):
    def __init__(self, **kwargs):

        self.util = App.get_running_app().util
        super(DigScreen, self).__init__(**kwargs)

        self.filter_pos_hint = None
        self.hf_pos_hint = None
        self.max_pos_hint = None
        self.cor_pos_hint = None

        
    def initSwitch(self):
        self.box_cor.myplain.bind(active=self.cornerSwitch)
        self.hf_pos_hint = self.box_hf.pos_hint
        self.filter_pos_hint = self.box_filter.pos_hint
        self.max_pos_hint = self.box_max.pos_hint
        self.cor_pos_hint = self.box_cor.pos_hint

    def cornerSwitch(self, *args):
        if self.box_cor.myplain.active is True:
            self.box_hf.opacity = 0
            self.box_hf.pos_hint = {'x':0, 'y':2}

            self.box_filter.opacity = 0
            self.box_filter.pos_hint = {'x':0, 'y':2}

            self.box_max.pos_hint = self.filter_pos_hint
            self.box_cor.pos_hint = self.hf_pos_hint

        else:
            self.box_hf.opacity = 1
            self.box_hf.pos_hint = self.hf_pos_hint
            self.box_filter.opacity = 1
            self.box_filter.pos_hint = self.filter_pos_hint
            self.box_max.pos_hint = self.max_pos_hint
            self.box_cor.pos_hint = self.cor_pos_hint


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

        # Max Height filter
        hfs = int(self.box_max.hfs.value)
        hfe = int(self.box_max.hfe.value)
        maxhf_filter = hfs if hfs == hfe else ((hfs, hfe),)

        settings = {
            "percent": int(self.box_per.per.value),
            "cf": filters,
            "height": hf_filter,
            "maxhf": maxhf_filter,
            "corner": self.box_cor.myplain.active

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

    def reset(self):
        self.box_per.per.value = 100
        self.box_hf.hfs.value = 0
        self.box_hf.hfe.value = 255
        self.box_max.hfs.value = 0
        self.box_max.hfe.value = 255
        self.box_cor.myplain.active = False
        self.box_filter.reset()
