from kivy.animation import Animation
from kivy.base import Builder
from kivy.graphics import Rotate
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView

Builder.load_file("Components/feedbackpopup.kv")


class FeedbackPopup(ModalView):

    pop_up_text = ObjectProperty()
    pop_up_image = ObjectProperty()

    def on_pre_open(self):
        self.pop_up_image.source = "./Resources/Images/Spinner/gear.png"
        self.pop_up_image.start_animation()

    def stop_spinner(self, *args):
        self.pop_up_image.stop_animation()

    def update_pop_up_text(self, p_message):
        self.pop_up_text.text = p_message

    def provide_feedback_image(self, source):
        self.stop_spinner()
        self.pop_up_image.source = source

    def on_dismiss(self):
        self.pop_up_image.stop_animation()

    def dismiss_pop_up_with_delay(self, dt):
        """dt Stands for delta-time, it is passed to this method via Clock.schedule_once
        autmatically. Therfore it is required here although not used!"""
        self.dismiss()


class LoadingSpinner(Image):
    angle = NumericProperty(0)
    anim = ObjectProperty()

    def start_animation(self, *args):
        self.anim = Animation(angle=1080, duration=8)
        self.anim += Animation(angle=-1080, duration=8)
        self.anim.repeat = True
        self.anim.start(self)

    def stop_animation(self, *args):
        self.angle = 0
        self.anim.stop_all(self)
