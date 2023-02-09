from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

class AvailableShopOrdersTemplate(BoxLayout):

    def __init__(self, **kwargs):
        super(AvailableShopOrdersTemplate, self).__init__(**kwargs)

        self.upper_details = BoxLayout(orientation = 'horizontal')
        self.shop_order_num = Label(text="Shop order 128746 Part Number 5021TOP",color=[0,0,0,1],)
        self.start_button = Button(text='Start',
                                   background_normal='',
                                   background_color= [0, 1, 0, 1],
                                   color=[0,0,0,1],
                                   size_hint_x = None,
                                   width = 300,
                                   padding_y = 20)
        self.shop_details = BoxLayout(orientation='horizontal',)
        self.ostatus = Label(text='Running', color=[0,1,0,1] )
        self.operation = Label(text='999',color=[0,0,0,1])
        self.op_desc = Label(text='U-BEND/MIDDLE BEND B010-2', color=[0,0,0,1])
        self.so_required = Label(text= '50 Required', color=[0,0,0,1])
        self.so_remaining = Label(text='50 Remaining', color=[0,0,0,1])
        self.so_pr_hour = Label(text='104 per hour', color=[0,0,0,1])

        self.add_widget(self.upper_details)
        self.upper_details.add_widget(self.shop_order_num)
        self.upper_details.add_widget(self.start_button)
        self.add_widget(self.shop_details)
        self.shop_details.add_widget(self.ostatus)
        self.shop_details.add_widget(self.operation)
        self.shop_details.add_widget(self.op_desc)
        self.shop_details.add_widget(self.so_required)
        self.shop_details.add_widget(self.so_remaining)
        self.shop_details.add_widget(self.so_pr_hour)
