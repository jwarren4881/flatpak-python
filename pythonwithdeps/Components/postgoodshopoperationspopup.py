from kivy.lang import Builder
from kivy.properties import DictProperty
from kivy.uix.popup import Popup

from .numberpadpopup import NumberPadPopup

Builder.load_file("./Components/postgoodshopoperationspopup.kv")


class PostGoodShopOperationsPopup(Popup):
    state_dict = DictProperty(
        {"no_ticket": "normal", "print_ticket": "normal", "post_quantity": 0}
    )

    def on_pre_open(self):

        self.numberpad = NumberPadPopup(cb=self.number_pad_callback)
        self.posted_good_quant_button = self.ids.posted_good_quantity
        self.posted_good_quant_button.bind(on_release=self.on_post_good_quantity)
        self.post_button = self.ids.post
        self.post_button.bind(on_release=self.post_good_quantities)
        self.no_ticket_toggle = self.ids.no_ticket_toggle
        self.print_ticket_toggle = self.ids.print_ticket_toggle
        self.no_ticket_toggle.bind(state=self.handle_ticket_printing)
        self.print_ticket_toggle.bind(state=self.handle_ticket_printing)

    def check_allow_posting(self):

        if "down" in list(self.state_dict.values()):
            if (
                self.posted_good_quant_button.text
                and (int(self.posted_good_quant_button.text)) > 0
            ):
                self.post_button.disabled = False
            else:
                self.post_button.disabled = True
        else:
            self.post_button.disabled = True

    def post_good_quantities(self, *args):
        """
        Since this pop_up is becoming something like a wizard, this method will do the work of making some
        calls to Odoo in order to post on to a shop order, I think, maybe.
        """
        self.dismiss()

    def handle_ticket_printing(self, _instance, _state):

        self.state_dict["no_ticket"] = self.no_ticket_toggle.state
        self.state_dict["print_ticket"] = self.print_ticket_toggle.state

    def on_state_dict(self, *args):

        self.check_allow_posting()

    def number_pad_callback(self, qty, *args):

        if qty:
            self.posted_good_quant_button.text = qty
            self.state_dict["post_quantity"] = int(self.posted_good_quant_button.text)
        else:
            self.posted_good_quant_button.text = "0"

    def on_post_good_quantity(self, *args):

        self.numberpad.open()

    def on_dismiss(self):

        self.posted_good_quant_button.text = "0"
        self.numberpad.dismiss()
