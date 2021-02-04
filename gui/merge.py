from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

Builder.load_file(r"gui\merge.kv")


class BoxClip(FloatLayout):
    def __init__(self, **kwargs):
        self.util = App.get_running_app().util
        super(BoxClip, self).__init__(**kwargs)

        self.clip = ""
        self.clipIsValid = False

    def checkClip(self, *args):
        if self.util.isclip(self.boxclip.text) is False:
            self.boxclip.color = 1, 0, 0, 1
            self.clipIsValid = False
        else:
            self.boxclip.color = 0, 0, 0, 1
            self.clip = self.boxclip.text
            self.clipIsValid = True


class MergeScreen(Screen):
    def __init__(self, **kwargs):

        self.util = App.get_running_app().util
        super(MergeScreen, self).__init__(**kwargs)

        self.amountBoxClip = 2
        self.maxAmountBoxClip = 5

    def add_boxclip(self):
        if self.amountBoxClip < self.maxAmountBoxClip:
            self.add_widget(BoxClip(pos_hint=self.add.pos_hint, size_hint=(0.5, 0.1)))
            self.add.pos_hint = {
                "x": self.add.pos_hint["x"],
                "y": self.add.pos_hint["y"] - 0.1,
            }
            self.amountBoxClip += 1

    def del_boxclip(self):
        for child in self.children:
            if isinstance(child, BoxClip):
                self.remove_widget(child)
                self.add.pos_hint = {
                    "x": self.add.pos_hint["x"],
                    "y": self.add.pos_hint["y"] + 0.1,
                }
                self.amountBoxClip -= 1
                break

    def save_to_clipboard(self):

        myPopUp = Factory.NotifPopUp()
        myPopUp.title = "Merge"

        if any(
            [
                isinstance(child, BoxClip) and child.clipIsValid is False
                for child in self.walk(loopback=True)
            ]
        ):
            myPopUp.level = "ERROR"
            myPopUp.mytext = "One of the clip is wrong or not filled"
            myPopUp.open()
        else:
            settings = {
                "input" + str(i): child.clip
                for i, child in enumerate(self.walk(loopback=True))
                if isinstance(child, BoxClip)
            }

            #print(settings)
            if self.util.merge(settings):
                myPopUp.level = "INFO"
                myPopUp.mytext = "Click 'Load from Clipboard'"
            else:
                myPopUp.level = "ERROR"
                myPopUp.mytext = "See 'town.log' for more information"
            myPopUp.open()
