from kivy.uix.stacklayout import StackLayout
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import BooleanProperty, StringProperty, OptionProperty
from kivy.metrics import dp
from dataclasses import dataclass

@dataclass()
class AttendanceInfo:
    employee_number: int = 0
    in_time: str = ''
    out_time: str = ''
    clock_status: str = ''
    department: str = ''


class IndividualDepartment(Button):
    def __init__(self, **kwargs):
        super(IndividualDepartment, self).__init__(**kwargs)
        self.size_hint=((1/3), (1/8))
        self.background_normal = ''
        self.color = (0,0,0,1)
        self.text_size =(self.width + dp(10), None)
        self.halign = 'center'

    def on_release(self):
        self.selected_department = self.text
        self.clock_status = 'In'
        return super(IndividualDepartment, self).on_release()

    def on_clock_status(self, instance, value):

        print('Modifying Clock Status')
        db = DepartmentButtons()
        db.clock_status = 'In'


class DepartmentButtons(StackLayout):

    DEPARTMENTS = ['Metal', 'Office', 'Sewing', 'Shipping',
                   'Polymer', 'Powdercoat', 'Paint Room',
                   'Maintenance', 'Alum Assembly/ Tables', 'Mettowee Lumbermill',
                   'Receiving & Loading','Box on Demand', 'Inventory',
                   'Pellet Mill','Metowee Plastics','Beach Assembly',
                   'Boiler Room','PC Assem/Sling', 'Woodworking', 'Wood Assembly',
                   'Warehouse',]

    reasons = ['End of Shift','Appointment', 'Fire/EMS Call','Lunch',
               'Running Home','In & Out','Telescope Errand','Personal Errand']

    def __init__(self, **kwargs):
        super(DepartmentButtons, self).__init__(**kwargs)
        for department in sorted(self.DEPARTMENTS):

            btn = IndividualDepartment(
                text=department,
            )
            btn.on_release()
            self.add_widget(btn)
            self.ids[btn.text] = btn
            btn.bind(on_release=self.get_app)
    def get_app(self, instance):

        app = App.get_running_app()
        print(app.root)

