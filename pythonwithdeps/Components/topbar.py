from kivy.lang.builder import Builder
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout

Builder.load_file("Components/topbar.kv")


class TopBar(BoxLayout):
    progress_limit = NumericProperty(400)
    earned_hours = NumericProperty(0.0)

