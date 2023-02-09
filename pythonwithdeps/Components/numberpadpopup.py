from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup

Builder.load_file("./Components/numberpadpopup.kv")


class NumberPadPopup(Popup):
    quantity = ObjectProperty(None)

    def __init__(self, cb, **kwargs):
        super().__init__(**kwargs)
        self.callback = cb

    def button_press(self, instance):
        self.quantity.text += instance.text

    def delete(self, instance):
        self.quantity.text = self.quantity.text[:-1]

    def clear(self):
        self.quantity.text = ""

    def make_negative(self, instance):

        if not self.quantity.text:
            self.quantity.text = "-"
        elif "-" not in self.quantity.text:
            self.quantity.text = "-" + self.quantity.text
        else:
            self.quantity.text = self.quantity.text.replace("-", "")

    def close_numberpad(self):
        self.clear()
        self.dismiss()

    def on_dismiss(self, *args):
        super().on_dismiss(*args)
        if self.callback != None:
            self.callback(self.quantity.text)
        self.clear()

    def submit_posted_quantity(self):
        self.dismiss()
