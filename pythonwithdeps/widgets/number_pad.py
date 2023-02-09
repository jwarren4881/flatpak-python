from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty, ObjectProperty

class NumberPad(GridLayout):
    post_good_quantity = ObjectProperty()
    posted_quantity = StringProperty('Hello from string property')

    def __init__(self, **kwargs):
        super(NumberPad, self).__init__(**kwargs)
        input = BoxLayout()
        self.text_box = TextInput(font_size=32, multiline=False,
                                   halign='center')
        a = BoxLayout()
        b = BoxLayout()
        c = BoxLayout()
        d = BoxLayout()
        e = BoxLayout()

        input.add_widget(self.text_box)
        for item in list(range(1,4)):
            item = Button(text=str(item),on_release=self.enter_text,)
            a.add_widget(item)
        for item in list(range(4,7)):
            item = Button(text=str(item),on_release=self.enter_text,)
            b.add_widget(item)
        for item in list(range(7,10)):
            item = Button(text=str(item),on_release=self.enter_text,)
            c.add_widget(item)
        d.add_widget(Label(text=''))
        d.add_widget(Button(text='0',on_release=self.enter_text,))
        d.add_widget(Button(text='-',on_release=self.make_negative,))

        e.add_widget(Button(text='Submit'))
        e.add_widget(Button(text='Delete', on_release=self.delete_one,))

        self.add_widget(input)
        self.add_widget(a)
        self.add_widget(b)
        self.add_widget(c)
        self.add_widget(d)
        self.add_widget(e)

    def enter_text(self, instance):
        data = instance.text
        self.text_box.text += data

    def make_negative(self, instance):
        if instance.text == '-':
            postive_text = self.text_box.text[:]
            self.text_box.text = instance.text + postive_text

    def delete_one(self, *args):
        self.text_box.text = self.text_box.text[:-1]

    def submit(self):
        self.posted_quantity = 'Hello World!'
