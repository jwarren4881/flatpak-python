from kivy.uix.progressbar import ProgressBar
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp

TIMEOUT = 400

class KioskTopBar(BoxLayout):

    def __init__(self, **kwargs):
        super(KioskTopBar, self).__init__(**kwargs)

        self.timeout_bar = ProgressBar(value=0, max=TIMEOUT)
        employee_info = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(29))
        employee_name = Label(text='Jake Warren')
        kiosk_device_name = Label(text='KSK198')
        clock_in_info = Label(text='Clocked in X Seconds ago')

        employee_info.add_widget(employee_name)
        employee_info.add_widget(kiosk_device_name)
        employee_info.add_widget(clock_in_info)

        self.add_widget(self.timeout_bar)
        self.add_widget(employee_info)




