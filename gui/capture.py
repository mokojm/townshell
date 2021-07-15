from os import getcwd

from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

Builder.load_file(r"gui\capture.kv")


class CaptureScreen(Screen):
    def __init__(self, **kwargs):

        self.util = App.get_running_app().util
        super(CaptureScreen, self).__init__(**kwargs)


    def durShowcasable(self, *args):
        duration = int(self.box_dur.dur.value)
        pixels = int(self.box_dist.dist.value)

        answer = self.util.isShowcasable(pixels, duration, 'duration')
        if answer is True:
            pass
        else:
            myPopUp = Factory.NotifPopUp()
            myPopUp.title = "Capture"
            myPopUp.level = "ERROR"
            myPopUp.mytext = answer
            myPopUp.open()

    def disShowcasable(self, *args):
        duration = int(self.box_dur.dur.value)
        pixels = int(self.box_dist.dist.value)

        answer = self.util.isShowcasable(pixels, duration, 'distance')
        if answer is True:
            pass
        else:
            myPopUp = Factory.NotifPopUp()
            myPopUp.title = "Capture"
            myPopUp.level = "ERROR"
            myPopUp.mytext = answer
            myPopUp.open()

    def reset(self):
        self.box_fps.fps.value = 30
        self.box_butt.butt.text = self.box_butt.butt.values[0]
        self.box_dur.dur.value = 5
        self.box_dist.dist.value = 500
        self.box_ang.ang.value = 0
        self.box_ryt.ryth.text = self.box_ryt.ryth.values[0]
        self.box_spos.spos.text = self.box_spos.spos.values[0]

    def capture(self, dryrun=False):

        target_fps = int(self.box_fps.fps.value)
        settings = {
            "fps": target_fps,
            "button": self.box_butt.butt.text,
            "duration": int(self.box_dur.dur.value),
            "pixels": int(self.box_dist.dist.value),
            "angle": int(self.box_ang.ang.value),
            "rythm": self.box_ryt.ryth.text,
            "start": self.box_spos.spos.text,
            "dirname": getcwd(),  # temporary
            "cqueue": self.util.captureQueue,
            "mqueue": self.util.mainQueue,
            "synchro": self.util.synchro,
            "dryrun": dryrun,
        }

        # Call the capture method of self.util
        answer = self.util.capture(**settings)

        if dryrun:
            if answer is True:
                level = "INFO"
                mytext = "Move successfully performed"
            else:
                level = "ERROR"
                mytext = answer

        else:
            # Good FPS
            if isinstance(answer, int) and abs(answer - target_fps) < 5:
                level = "INFO"
                mytext = f"File created. Good FPS : {answer}"

            # Unexpected FPS
            elif isinstance(answer, int):
                level = "WARNING"
                mytext = f"File Created. Unexpected FPS : {answer}"

            # Error during process
            else:
                level = "ERROR"
                mytext = f"Something went wrong : {answer}"

        myPopUp = Factory.NotifPopUp()
        myPopUp.title = "Capture"
        myPopUp.level = level
        myPopUp.mytext = mytext
        myPopUp.open()
