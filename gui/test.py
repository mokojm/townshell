from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget

KIVY_FONTS = [
    {
        "name": "Garamond",
        "fn_regular": "Garamond Regular.ttf",
    }
]
    
for font in KIVY_FONTS:
    LabelBase.register(**font)

class TownButton(Button):
    pass

class MainMenu(Widget):
    pass

class MySpinner(Spinner):
    dico = {'1':(0,0.3,0.4,1), '2':(1,0.3,0.4,1)}
    def f(self, arg):
        return self.dico.get(arg,(0,0,0,1))

class LevelMenu(Widget):
    def f(self):
        return "TownShell.ico"

# class MenuApp(App):
#     def build(self):
#         return MainMenu()

class LevelApp(App):
    def build(self):
        return LevelMenu()

if __name__ == "__main__":
    LevelApp().run()
