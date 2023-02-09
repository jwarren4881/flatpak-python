from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.relativelayout import RelativeLayout

Builder.load_file("./Components/availableshoporder.kv")


class ShopOperations(BoxLayout):
    """
    Plan is o provide a list of dictionaries to this class in the form of
    [{ 'description': 'ASSM SLV&GUARDS&PLGS>9590 BASE',
        'remaining': 12.0,
        'required': 12.0,
        'state': 'ready'},
   { 'description': 'SLING/FINAL/WRAP&HANG TAG 9050',
     'operation': [21842, 'SLING/FINAL/WRAP&HANG TAG 9050'],
     'remaining': 12.0,
     'required': 12.0,
     'state': 'pending'},
   { 'description': 'BAG SWIVEL (TIE)',
     'operation': [21838, 'BAG SWIVEL (TIE)'],
     'remaining': 12.0,
     'required': 12.0,
     'state': 'pending'},
   { 'description': '1PK SWL BAR CHR"DW";H TAPE/3PC',
     'operation': [21839, '1PK SWL BAR CHR"DW";H TAPE/3PC'],
     'remaining': 12.0,
     'required': 12.0,
     'state': 'pending'}
    ],

    Then I should be able to initialize each instance of this class with the proper data and
    fill in the labels
    """

    order_state = StringProperty("")
    order_operation = StringProperty("")
    order_description = StringProperty("")
    order_required = StringProperty("")
    order_remaining = StringProperty("")
    order_per_hour = StringProperty("")

    def __init__(
        self, state, description, required, remaining, per_hour, operation=995, **kwargs
    ):
        super().__init__(*kwargs)
        self.order_state = state
        self.order_operation = str(operation)
        self.order_description = description
        self.order_required = str(required)
        self.order_remaining = str(remaining)
        self.order_per_hour = str(per_hour)
        self.ids.order_state.text = self.order_state.upper()
        self.ids.order_operation.text = self.order_operation
        self.ids.order_description.text = self.order_description
        self.ids.order_required.text = f"{self.order_required} Required"
        self.ids.order_remaining.text = f"{self.order_remaining} Remaining"
        self.ids.order_per_hour.text = f"{self.order_per_hour} per Hour"


class ShopOrder(BoxLayout):

    shop_order_number = StringProperty("")
    shop_operations = ListProperty()

    def __init__(self, shop_order_data, shop_operation_data, **kwargs):
        super().__init__(**kwargs)
        self.shop_order_number = f"Shop Order {shop_order_data}"
        self.shop_operations = shop_operation_data

    def on_shop_order_number(self, *args):

        self.ids.shop_order_number.text = self.shop_order_number

    def on_shop_operations(self, *args):

        self.shop_operation_boxlayout = self.ids.shop_operation_detail
        for item in self.shop_operations:
            self.shop_operation_boxlayout.add_widget(
                ShopOperations(
                    state=item["state"],
                    description=item["description"],
                    required=item["remaining"],
                    remaining=item["remaining"],
                    per_hour=item["qty_per_hr"],
                )
            )
