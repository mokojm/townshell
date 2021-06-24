from collections import namedtuple
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

Builder.load_file(r"gui\tools.kv")


class HoverBehavior(object):
    """Hover behavior.
    :Events:
        `on_enter`
            Fired when mouse enter the bbox of the widget.
        `on_leave`
            Fired when the mouse exit the widget
    """

    hovered = BooleanProperty(False)
    border_point = ObjectProperty(None)
    """Contains the last relevant point received by the Hoverable. This can
    be used in `on_enter` or `on_leave` in order to know where was dispatched the event.
    """

    def __init__(self, **kwargs):
        self.register_event_type("on_enter")
        self.register_event_type("on_leave")
        Window.bind(mouse_pos=self.on_mouse_pos)
        super(HoverBehavior, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return  # do proceed if I'm not displayed <=> If have no parent
        pos = args[1]
        # Next line to_widget allow to compensate for relative layout
        inside = self.collide_point(*self.to_widget(*pos))
        if self.hovered == inside:
            # We have already done what was needed
            return
        self.border_point = pos
        self.hovered = inside
        if inside:
            self.dispatch("on_enter")
        else:
            self.dispatch("on_leave")

    def on_enter(self):
        pass

    def on_leave(self):
        pass


Factory.register("HoverBehavior", HoverBehavior)


class MyLabel(Label):
    pass


class SmartLabel(MyLabel, HoverBehavior):
    pass


class SlideTextInput(TextInput):
    pass


class HeightSlideTextInput(SlideTextInput):
    def validate(self, *args):
        if self.text.startswith("+"):
            self.text = self.text[1:]

        if self.text.startswith("-") and self.text[1:].isnumeric():
            pass
        elif self.text.isnumeric() is False:
            self.text = "+0"


class BoxUndoRedo(BoxLayout):
    def __init__(self, **kwargs):
        self.util = App.get_running_app().util
        super(BoxUndoRedo, self).__init__(**kwargs)

    def undo(self):
        myPopUp = Factory.NotifPopUp()
        myPopUp.title = "Undo"
        if self.util.undo():
            myPopUp.level = "INFO"
            myPopUp.mytext = "Click 'Load from Clipboard'"
        else:
            myPopUp.level = "WARNING"
            myPopUp.mytext = "No older clip"
        myPopUp.open()

    def redo(self):
        myPopUp = Factory.NotifPopUp()
        myPopUp.title = "Redo"
        if self.util.redo():
            myPopUp.level = "INFO"
            myPopUp.mytext = "Click 'Load from Clipboard'"
        else:
            myPopUp.level = "WARNING"
            myPopUp.mytext = "No newer clip"
        myPopUp.open()


class ColorSpinner(Spinner):
    def __init__(self, **kwargs):

        super(ColorSpinner, self).__init__(**kwargs)


class BoxColor(FloatLayout):
    BColor = namedtuple("BColor", ["x", "y"])
    button_size = BColor(x=30, y=30)

    def __init__(self, **kwargs):
        super(BoxColor, self).__init__(**kwargs)

    def add_color(self):
        if any([child.text in ("R", "") for child in self.children]):
            return
        else:
            self.add_widget(
                ColorSpinner(
                    pos_hint={
                        "x": self.add_button.pos_hint["x"],
                        "center_y": self.add_button.pos_hint["center_y"],
                    },
                    size=(30, 30),
                    values=self.values,
                )
            )
            self.add_button.pos_hint = {
                "x": self.add_button.pos_hint["x"] + 0.2,
                "center_y": self.add_button.pos_hint["center_y"],
            }

        #Complementary function
        self.addCompFunc()

    def del_color(self):
        if self.children[0].name == "colspin":
            self.remove_widget(self.children[0])
            self.add_button.pos_hint = {
                "x": self.add_button.pos_hint["x"] - 0.2,
                "center_y": self.add_button.pos_hint["center_y"],
            }

        #Complementary function
        self.delCompFunc()


class BoxUpDown(FloatLayout):
    def __init__(self, **kwargs):
        super(BoxUpDown, self).__init__(**kwargs)
        self.event = None

    def stopupdate(self, more=False, new_event=None, *args):
        self.event.cancel()
        if more:
            self.event = new_event
            self.event()

    def myTextFunc(self, **kwargs):
        newVal = kwargs["text"]
        if newVal == "None":
            self.value = newVal
        elif newVal.isnumeric() or newVal.isdecimal():
            newVal = int(newVal)
        else:
            return

        if newVal < self.min or newVal > self.max:
            return
        else:
            self.value = newVal

    def myTextCheck(self, *args):
        pass

    def uppress(self, *args):
        def autoUpPress(*args):

            if (
                isinstance(self.value, (int, float))
                and self.value < self.max
                and self.upb.state == "down"
            ):
                setattr(self, "value", self.value + 1)
            else:
                self.event.cancel()

        self.event = Clock.schedule_interval(autoUpPress, 0.5)
        new_event = Clock.create_trigger(autoUpPress, timeout=0.1, interval=True)
        Clock.schedule_once(partial(self.stopupdate, True, new_event), 2.5)
        autoUpPress()

    def uprelease(self, *args):
        pass

    def downpress(self, *args):
        def autoDownPress(*args):

            if (
                isinstance(self.value, (int, float))
                and self.value > self.min
                and self.downb.state == "down"
            ):
                setattr(self, "value", self.value - 1)
            else:
                self.event.cancel()

        self.event = Clock.schedule_interval(autoDownPress, 0.5)
        new_event = Clock.create_trigger(autoDownPress, timeout=0.1, interval=True)
        Clock.schedule_once(partial(self.stopupdate, True, new_event), 2.5)
        autoDownPress()

    def downrelease(self, *args):
        pass


class BoxHeightFilter(FloatLayout):
    def hfsUpRelease(self, *args):

        if self.hfs.value > self.hfe.value:
            self.hfe.value = self.hfs.value

    def hfeDownRelease(self, *args):

        if self.hfe.value < self.hfs.value:
            self.hfs.value = self.hfe.value
