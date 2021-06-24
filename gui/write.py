from json import loads

from gui.tools import HeightSlideTextInput
from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

Builder.load_file(r"gui\write.kv")


class WriteScreen(Screen):
    def __init__(self, **kwargs):
        self.util = App.get_running_app().util
        self.dictTemp = self.util.fetch_templates()
        super(WriteScreen, self).__init__(**kwargs)

    #Gather all templates
    def fetch(self):
        self.dictTemp = self.util.fetch_templates()
        self.box_path.path.values = list(self.dictTemp)

    #Validate that advanced content is a valid json
    def validateJson(self):

        advContent = self.box_adv.clip_text.text
        
        #When advanced is empty
        if advContent == '':
            self.box_adv.clip_text.json_valid = True

        else:
            try:
                loads(advContent)
                self.box_adv.clip_text.json_valid = True
            except:
                self.box_adv.clip_text.json_valid = False



    def save_to_clipboard(self):

        #Colors handling
        colors = tuple(
            child.text
            for child in self.box_color.children
            if child.name == "colspin" and child.text != ""
        )
        colors = tuple(int(c) if c.isnumeric() else 'empty' if c == 'E' else 'random' if c == 'R' else c for c in colors)
        colors = colors[0] if len(colors) == 1 else colors

        #Background handling
        background = tuple(
            child.text
            for child in self.box_back.children
            if child.name == "colspin" and child.text != ""
        )
        background = tuple(int(c) if c.isnumeric() else 'empty' if c == 'E' else 'random' if c == 'R' else c for c in background)
        background = background[0] if len(background) == 1 else background

        settings = {
            "text": self.box_text.clip_text.text,
            "wallpath": self.dictTemp[self.box_path.path.text],
            "reverse": self.box_plain.myplain.active,
            "font": self.box_font.font.text,
            "wordwrap": self.box_wwrap.myplain.active,
            "align": self.box_ali.ali.text,
            "color": colors,
            "background": background,
            "advanced": self.box_adv.clip_text.text
        }
        #print(settings)

        # Call the Write method of self.util
        answer = self.util.write(**settings)

        if answer is True:
            level = "INFO"
            mytext = "Click 'Load from Clipboard"
        else:
            level = "ERROR"
            mytext = answer

        myPopUp = Factory.NotifPopUp()
        myPopUp.title = "Write"
        myPopUp.level = level
        myPopUp.mytext = mytext
        myPopUp.open()
