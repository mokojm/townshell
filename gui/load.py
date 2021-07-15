from kivy.app import App
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

Builder.load_file(r"gui\load.kv")

class BoxSpot(FloatLayout):

    spot = ObjectProperty(None)

    def __init__(self, **kwargs):
        
        super(BoxSpot, self).__init__(**kwargs)
        self.spot = kwargs.get('spot')

    def getName(self):
        return self.spot['name']

    def getPicture(self):
        return self.spot['picture']

    def getTags(self):
        return self.spot['tags'].replace(";", " ; ")

    def getComment(self):
        return self.spot['comment']

    def save_to_clipboard(self):
        myPopUp = Factory.NotifPopUp()
        myPopUp.title = "Load"
        myPopUp.level = "INFO"
        myPopUp.open()

class BoxTags(FloatLayout):

    def __init__(self, **kwargs):
        
        self.util = App.get_running_app().util
        super(BoxTags, self).__init__(**kwargs)

    def getAllTags(self):
        tags = set()

        for spot in self.util.dictSpots.values():
            for tag in spot['tags'].split(';'):
                tags.add(tag)

        tags = list(tags)
        tags.append("All")
        tags.sort()
        return tags


class LoadScreen(Screen):

    spots = ObjectProperty(None)

    def __init__(self, **kwargs):

        self.util = App.get_running_app().util
        super(LoadScreen, self).__init__(**kwargs)

        self.screenInitialized = False

    def on_win_height(self):
        return Window.height*0.2

    def initScreen(self, filt=None):
        boxHeight=250
        if self.screenInitialized is False:
            for spot in self.util.dictSpots.values():
                if filt is None or filt == 'All' or filt in spot['tags']:
                    newWidget = BoxSpot(size_hint_y=None, spot=spot)
                    newWidget.height = boxHeight
                    newWidget.bind(height=self.on_win_height)
                    self.spots.slayout.add_widget(newWidget)

            self.screenInitialized = True

    def updateScreen(self, filt=None):
        for child in self.walk(loopback=True):
            if isinstance(child, BoxSpot):
                self.spots.slayout.remove_widget(child)

        self.screenInitialized = False

        self.initScreen(filt)
