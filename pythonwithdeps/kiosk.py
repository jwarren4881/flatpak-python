import datetime

# from widgets.top_bar import KioskTopBar
import threading
import time
from dataclasses import dataclass

from kivy.app import App
from kivy.base import Builder
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.properties import (
    DictProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
)
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.stacklayout import StackLayout

from Components import availableshoporder, numberpadpopup, topbar
from Components.feedbackpopup import FeedbackPopup
from Components.postgoodshopoperationspopup import PostGoodShopOperationsPopup
from Components.postscrappopup import PostScrapPopup
from Services import WifiSignalStrength, mediaplayer, odoodatabase, sqlite_connection

HOST = "telescopecasual-sandbox-kiosk-6449204.dev.odoo.com"
PORT = 443
DB = "telescopecasual-sandbox-kiosk-6449204"
USER = "kioskuser"
PASSW = "kioskuser"

DEPARTMENTS_DICT = {
    "Metal": 7,
    "Office": 15,
    "Sewing": 3,
    "Shipping": 71,
    "Polymer": 48,
    "Powdercoat": 43,
    "Paint Room": 6,
    "Maintenance": 9,
    "Alum Assembly/ Tables": 42,
    "Mettowee Lumbermill": 80,
    "Receiving & Loading": 910,
    "Box on Demand": 72,
    "Inventory": 915,
    "Pellet Mill": 83,
    "Metowee Plastics": 90,
    "Beach Assembly": 40,
    "Boiler Room": 9998,
    "PC Assem/Sling": 44,
    "Woodworking": 2,
    "Wood Assembly": 41,
    "Warehouse": 115,
}


@dataclass()
class AttendanceInfo:
    employee_number: int = 0
    in_time: str = ""
    out_time: str = ""
    clocked_in: str = ""
    clocked_out: str = ""
    department: str = ""


@dataclass
class LoggedInUser:
    employee_id: int = 0
    clock_number: int = 0
    clocked_in_department: int = 0
    clocked_in_cell: str = ""
    active_shop_order: str = ""
    emtoken: str = ""
    name: str = ""


@dataclass
class ShopOrderData:
    name: str = ""
    production_id: str = ""
    product_id: str = ""
    state: str = ""
    operation_id: str = ""
    required: str = ""
    remaining: str = ""
    duration_expected: str = ""
    qty_per_hr: str = ""


@dataclass()
class ScreenTracker:
    previous_screen: str = ""


class ScreenPrep(Screen):

    top_bar = topbar.TopBar()

    def __init__(self, top_bar_id, custom_timeout=None, **kwargs):
        super().__init__(**kwargs)
        self.top_bar_id = top_bar_id
        self.custom_timeout = custom_timeout
        # self.odooconn = odoodatabase.OdooDatabaseConnector(
        #    host=HOST, port=PORT, db=DB, user=USER, pwd=PASSW
        # )

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        """Screen tracker currently not utilized"""
        # self.screen_tracker = ScreenTracker(previous_screen=self.manager.current)
        # print(self.screen_tracker)
        # App.get_running_app().screen_tracker = self.screen_tracker
        self.ids[self.top_bar_id].ids.current_screen.text = self.manager.current
        self.logged_in_user = self.get_logged_in_user()
        self.start_timeout()
        user_id = self.ids[self.top_bar_id].ids.user_id
        user_id.text = f"{self.logged_in_user.name.upper()}"
        """Need to think a litte more on the best way to implement below"""
        # self.attendance_button = (
        #    self.ids[self.top_bar_id].ids.top_bar_middle_button
        # )
        # self.attendance_button.disabled = True
        # self.attendance_button.color = [1, 1, 1, 1]

    def is_custom_timeout(self):

        if self.custom_timeout is None:

            return False
        else:

            return True

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        timeout_bar = self.ids[self.top_bar_id].ids.timeout_bar
        timeout_bar.value = 0

    def timeout_countdown(self, *args):
        timeout_bar = self.ids[self.top_bar_id].ids.timeout_bar

        if self.is_custom_timeout():
            timeout_bar.max = self.custom_timeout
        timeout_bar.value += 1 / 60
        if timeout_bar.value >= timeout_bar.max:
            timeout_bar.value = 0
            self.logout()

    def start_timeout(self, *args):
        self.event = Clock.schedule_interval(self.timeout_countdown, 1 / 60)

    def get_logged_in_user(self):
        self.logged_in_user = App.get_running_app().logged_in_user
        return self.logged_in_user

    def logout(self, *args):
        self.parent.current = "welcome_screen"
        self.event.cancel()
        del self.logged_in_user

    def on_leave(self, *args):
        super().on_leave(*args)
        self.event.cancel()


class IndividualDepartment(Button):

    dept_no = NumericProperty(0)

    def __init__(self, **kwargs):
        super(IndividualDepartment, self).__init__(**kwargs)
        self.size_hint = ((1 / 3), (1 / 8))
        self.background_normal = ""
        self.color = (0, 0, 0, 1)
        self.text_size = (self.width + dp(10), None)
        self.halign = "center"


class ClockOutReasons(StackLayout):

    reasons = [
        "End of Shift",
        "Appointment",
        "Fire/EMS Call",
        "Lunch",
        "Running Home",
        "In & Out",
        "Telescope Errand",
        "Personal Errand",
    ]

    def __init__(self, **kwargs):
        super(ClockOutReasons, self).__init__(**kwargs)

        for out_reason in self.reasons:

            btn = Button(
                text=out_reason,
                size_hint=((1 / 3), (1 / 7)),
                background_normal="",
                color=(0, 0, 0, 1),
                text_size=(self.width, None),
                halign="center",
            )
            btn.bind(on_release=self.clock_out_with_reason)
            self.add_widget(btn)

    def clock_out_with_reason(self, instance):

        app = App.get_running_app()

        self.logged_in_user = app.logged_in_user

        odooconn = odoodatabase.OdooDatabaseConnector(
            host=HOST, port=PORT, db=DB, user=USER, pwd=PASSW
        )
        odooconn.check_out_of_odoo(self.logged_in_user.employee_id)
        app.root.current = "welcome_screen"


class WelcomeScreen(Screen):
    label_time = StringProperty(time.strftime("%I:%M:%S %p", time.localtime()))
    event = None
    wifi_signal_event = None
    pop_up = FeedbackPopup()
    temp_list = []
    token_list_property = ListProperty([])
    swipe_verification = NumericProperty(0)
    popup_thread = None
    radio_station_list = ListProperty([])

    def _keyboard_closed(self):
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] not in ["shift", "/"]:
            if keycode[1] == "enter":
                self.token_list_property = self.temp_list[:]
                self.temp_list = []
            else:
                self.temp_list.append(text)

    def show_popup(self, information):
        self.pop_up.update_pop_up_text(information)
        self.pop_up.open()

    def on_token_list_property(self, *args):
        if self.token_list_property:
            self.show_popup("Connecting to Odoo....")
            self.popup_thread = threading.Thread(target=self.verify_swipe)
            # self.verify_swipe()
            self.popup_thread.start()

    def on_pre_enter(self, *args):
        self.dbconn = sqlite_connection.sqliteConnection().sqlite_connect()
        self.get_time()
        self.get_wifi_signal_strength()
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, "text")
        if self._keyboard.widget:
            # If it exists, this widget is a VKeyboard object which you can use
            # to change the keyboard layout.
            pass
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def on_kv_post(self, base_widget):
        # print(f"kv_posted {self.ids}")
        self.swipe_button = self.ids.swipe_card_button
        self.swipe_button.bind(on_release=self.provide_token)
        self.streaming_button = self.ids.streaming_radio_button
        self.streaming_button.bind(on_release=self.on_streaming_radio_release)

    def on_streaming_radio_release(self, instance):
        self.show_popup("Getting Available Radio Stations....")
        self.radio_station_thread = threading.Thread(target=self.find_radio_stations)
        self.radio_station_thread.start()

    def find_radio_stations(self):
        self.radio_station_buttons = []
        odooconn = odoodatabase.OdooDatabaseConnector(
            host=HOST, port=PORT, db=DB, user=USER, pwd=PASSW
        )
        self.manager.ODOOCONN = odooconn
        self.radio_stations = odooconn.get_all_radio_stations()
        for radio in self.radio_stations:
            self.radio_station_buttons.append(radio["name"])

        App.get_running_app().radio_stations = self.radio_station_buttons

        self.switch_to_radio_station_screen()

    @mainthread
    def switch_to_radio_station_screen(self):
        self.manager.current = "StreamingRadio"
        self.pop_up.dismiss()

    def provide_token(self, instance):

        self.token_list_property = [
            "5",
            "e",
            "m",
            "t",
            "k",
            "n",
            "=",
            "9",
            "f",
            "s",
            "m",
            "g",
            "i",
            "j",
            "l",
            "n",
            "w",
            "y",
        ]

    def get_time(self, *args):
        self.event = Clock.schedule_interval(self.update, 1)
        return self.label_time

    def get_wifi_signal_strength(self, *args):
        self.wifi_signal_event = Clock.schedule_interval(
            self.wifi_signal_strength_result, 10
        )

    def verify_swipe(self, timer=None, token=None):
        """This method is used to find employees by the Odoo badge_id. It needs some cleanup and has some
        extra bits for testing that will be removed.
        BUG - If an employee did not clock out and a couple of days pass (on vacation) then I can not find that
        employee. I'm assuming the auto logout will be in place before this kiosk is implemeneted so maybe not
        worry about it for now?"""
        # 9FSMGIJLNWY
        app = App.get_running_app()
        if self.token_list_property:
            parsed_token = "".join(self.token_list_property[1:])
            if parsed_token.upper().startswith("EMTKN="):
                parsed_token = parsed_token.split("=")[1].upper()
                odooconn = odoodatabase.OdooDatabaseConnector(
                    host=HOST, port=PORT, db=DB, user=USER, pwd=PASSW
                )
                self.manager.ODOODBCONN = odooconn
                attendance_status = odooconn.get_attendance_status(parsed_token)
                if attendance_status and attendance_status.clock_status == "in":
                    self.logged_in_user = LoggedInUser(
                        employee_id=attendance_status.employee_id,
                        clock_number=attendance_status.clock_number,
                        emtoken=attendance_status.emtoken,
                        name=attendance_status.name,
                        clocked_in_department=attendance_status.clocked_in_department,
                        clocked_in_cell=attendance_status.clocked_in_cell,
                    )
                    app.logged_in_user = self.logged_in_user
                    if (
                        self.logged_in_user.clocked_in_department[0] in ["44", "42"]
                        and not self.logged_in_user.clocked_in_cell
                    ):
                        # Go to cell clock in screen
                        self.swipe_verification = 1
                    elif self.logged_in_user.clocked_in_department[0] == "7":
                        self.swipe_verification = 4
                    elif self.logged_in_user.clocked_in_cell:
                        # If clocked into a cell go to the available shop order
                        self.swipe_verification = 4
                    else:
                        # If not clocked into a cell and not in depts 44, 42 or 7
                        # Probably in the Office, Go to the Attendance clocked in screen
                        self.swipe_verification = 2
                elif attendance_status and attendance_status.clock_status == "out":
                    self.logged_in_user = LoggedInUser(
                        employee_id=attendance_status.employee_id,
                        clock_number=attendance_status.clock_number,
                        emtoken=attendance_status.emtoken,
                        name=attendance_status.name,
                    )
                    app.logged_in_user = self.logged_in_user
                    self.swipe_verification = 3
                else:
                    print("Sorry Employee not found")
                    self.swipe_verification = 5
            else:
                print("Improperly formed token string!")
                self.swipe_verification = 5

    @mainthread
    def on_swipe_verification(self, *args):
        if self.swipe_verification > 0:
            if self.swipe_verification == 1:
                """User is swiped into a cell department ie Finaling but has not clocked into a cell"""
                self.manager.current = "Cell Clock In"
                self.pop_up.update_pop_up_text("Successfully Logged In!")
                self.pop_up.provide_feedback_image(
                    "./Resources/Images/Feedback/check-128.png"
                )
                Clock.schedule_once(self.pop_up.dismiss_pop_up_with_delay, 0.3)
                self.swipe_verification = 0
            elif self.swipe_verification == 2:
                self.manager.current = "AttendanceClockedIn"
                self.pop_up.update_pop_up_text("Successfully Logged In!")
                self.pop_up.provide_feedback_image(
                    "./Resources/Images/Feedback/check-128.png"
                )
                Clock.schedule_once(self.pop_up.dismiss_pop_up_with_delay, 0.3)
                self.swipe_verification = 0
            elif self.swipe_verification == 3:
                self.manager.current = "Attendance"
                self.pop_up.dismiss()
            elif self.swipe_verification == 4:
                # User has clocked into a department where shop orders are going to exist
                self.manager.current = "available_shop_orders"
                self.pop_up.update_pop_up_text("Successfully Logged In!")
                self.pop_up.provide_feedback_image(
                    "./Resources/Images/Feedback/check-128.png"
                )
                Clock.schedule_once(self.pop_up.dismiss_pop_up_with_delay, 0.3)
                self.swipe_verification = 0
            elif self.swipe_verification == 5:
                self.pop_up.update_pop_up_text("Invalid Swipe, Please Try Again!")
                self.pop_up.provide_feedback_image(
                    "./Resources/Images/Feedback/x-128.png"
                )
                self.token_list_property = []
                Clock.schedule_once(self.pop_up.dismiss_pop_up_with_delay, 1.5)
                self.swipe_verification = 0
            else:
                self.swipe_verification = 0
                self.token_list_property = []
        else:
            pass

    def wifi_signal_strength_result(self, *args):

        self.wifi_signal = WifiSignalStrength.read_data_from_cmd()
        self.wifi_signal_image = self.ids["wifi_signal_image"]
        self.wifi_signal_text = self.ids["wifi_signal_text"]
        if not self.wifi_signal:
            self.wifi_signal_image.source = (
                "./Resources/Images/WifiAndWired/wifi_searching_1.png"
            )
            self.wifi_signal_text.text = "Searching"
        else:
            integer_signal = int(self.wifi_signal[0][1])
            # measured in dbm (Linux)
            if integer_signal < 0:
                if integer_signal >= -50:
                    self.wifi_signal_image.source = (
                        "./Resources/Images/WifiAndWired/wifi_excellent.png"
                    )
                    self.wifi_signal_text.text = "Excellent"
                elif integer_signal >= -70:
                    self.wifi_signal_image.source = (
                        "./Resources/Images/WifiAndWired/wifi_good.png"
                    )
                    self.wifi_signal_text.text = "Good"
                elif integer_signal >= -80:
                    self.wifi_signal_image.source = (
                        "./Resources/Images/WifiAndWired/wifi_fair.png"
                    )
                    self.wifi_signal_text.text = "Fair"
                else:
                    self.wifi_signal_image.source = (
                        "./Resources/Images/WifiAndWired/wifi_poor.png"
                    )
                    self.wifi_signal_text.text = "Poor"
            else:
                if integer_signal >= 80:
                    self.wifi_signal_image.source = (
                        "./Resources/Images/WifiAndWired/wifi_excellent.png"
                    )
                    self.wifi_signal_text.text = "Excellent"
                elif integer_signal >= 60:
                    self.wifi_signal_image.source = (
                        "./Resources/Images/WifiAndWired/wifi_good.png"
                    )
                    self.wifi_signal_text.text = "Good"
                elif integer_signal >= 40:
                    self.wifi_signal_image.source = (
                        "./Resources/Images/WifiAndWired/wifi_fair.png"
                    )
                    self.wifi_signal_text.text = "Fair"
                else:
                    self.wifi_signal_image.source = (
                        "./Resources/Images/WifiAndWired/wifi_poor.png"
                    )
                    self.wifi_signal_text.text = "Poor"

        return self.wifi_signal

    def update(self, *args):
        self.label_time = time.strftime("%I:%M:%S %p", time.localtime())

    def on_leave(self, *args):
        self.event.cancel()
        self.token_list_property = []


class StreamingRadio(Screen):

    odooconn = ObjectProperty
    vlc_instance = mediaplayer.VLC()
    streaming_timeout = NumericProperty(20)

    """
        This screen is meant to replicate the RadioStation feature on the current kiosks
        that system uses a bash script on the kiosks to do a lot of the work. The usages for that are
        as follows:
        bash streaming_radio.sh show: Show which station is currently being streamed using cvlc/vlc
        bash streaming_radio.sh stop: Stop all instances of cvlc/vlc
        bash streaming_radio.sh play <url>: Kill all instance and play a single cvlc on the URL (do not kill/restart if the url is the same)
        bash streaming_radio.sh get-volume: Get the current volume
        bash streaming_radio.sh set-volume <volume>: Set the volume (range is 0 to 400)
    """

    def on_pre_enter(self, *args):
        super(StreamingRadio, self).on_pre_enter(*args)
        self.radio_stations = App.get_running_app().radio_stations
        for item in self.radio_stations:
            btn = Button(
                text=item,
                size_hint=((1 / 3), (1 / 7)),
                background_normal="",
                color=(0, 0, 0, 1),
                font_size=28,
            )
            btn.bind(on_release=self.play_streaming_radio)
            self.ids.radio_buttons_layout.add_widget(btn)

    def on_enter(self, *args):
        self.start_timeout()

    def play_streaming_radio(self, instance):

        # self.odooconn = odoodatabase.OdooDatabaseConnector(
        #    host=HOST, port=PORT, db=DB, user=USER, pwd=PASSW
        # )

        # radios = self.odooconn.get_selected_radio_station(instance.text)
        radios = self.manager.ODOOCONN.get_selected_radio_station(instance.text)

        if radios:
            self.stop_music()
            url = radios[0]["url"]
            self.vlc_instance.play_music_from_list([url])

        else:
            self.vlc_instance.stop_music()

    def stop_music(self):

        self.vlc_instance.stop_music()

    def start_timeout(self, *args):
        self.event = Clock.schedule_interval(self.timeout_countdown, 1 / 60)

    def timeout_countdown(self, *args):
        timeout_bar = self.ids.streaming_timeout_bar
        timeout_bar.value += 1 / 60
        if timeout_bar.value >= timeout_bar.max:
            timeout_bar.value = 0
            self.logout()

    def on_touch_up(self, touch):
        timeout_bar = self.ids.streaming_timeout_bar
        timeout_bar.value = 0

    def on_leave(self, *args):
        super(StreamingRadio, self).on_leave(*args)
        self.ids.radio_buttons_layout.clear_widgets()
        self.event.cancel()

    def logout(self, *args):
        self.manager.current = "welcome_screen"
        self.event.cancel()


class Attendance(ScreenPrep):
    """
    Top bar id for this class is:
        'top_attendance'
    """

    clock_in_event = None
    clock_status = OptionProperty("Out", options=["In", "Out"])
    dept = IndividualDepartment()

    def __init__(self, **kwargs):
        super().__init__(top_bar_id="top_attendance", custom_timeout=None, **kwargs)

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        for department, dept_no in sorted(list(DEPARTMENTS_DICT.items())):
            btn = IndividualDepartment(text=department, dept_no=dept_no)
            btn.on_release()
            self.ids.department_buttons.add_widget(btn)
            btn.bind(on_release=self.clock_in_to_department)

    def clock_in_to_department(self, instance):
        """TODO: I think I am doing an extra call to 'App.get_running_app()' since I do it on_pre_enter as well"""
        app = App.get_running_app()

        self.logged_in_user = app.logged_in_user
        # odooconn = odoodatabase.OdooDatabaseConnector(
        #    host=HOST, port=PORT, db=DB, user=USER, pwd=PASSW
        # )
        self.manager.ODOODBCONN.check_into_odoo(
            self.logged_in_user.emtoken, instance.dept_no
        )
        app.root.current = "welcome_screen"

    def on_leave(self, *args):
        super().on_leave(*args)
        self.ids.department_buttons.clear_widgets()


class AttendanceSwitchDepts(ScreenPrep):
    """Top bar_id for this class
        'top_attendance_switch_depts'
    """

    logged_in_user = ObjectProperty
    switch_dept_popup = FeedbackPopup()

    def __init__(self, **kwargs):
        super().__init__(
            top_bar_id="top_attendance_switch_depts", custom_timeout=None, **kwargs
        )

    def on_pre_enter(self, *args):
        super().on_pre_enter()
        """self.logged_in_user = App.get_running_app().logged_in_user
        user_id = self.ids["top_attendance_switch_depts"].ids.user_id
        user_id.text = f"{self.logged_in_user.name.upper()}"
        self.attendance_button = (
            self.ids.top_attendance_switch_depts.ids.top_bar_middle_button
        )
        self.attendance_button.disabled = True
        self.attendance_button.color = [1, 1, 1, 1]"""
        for department, dept_no in sorted(list(DEPARTMENTS_DICT.items())):
            btn = IndividualDepartment(text=department, dept_no=dept_no)
            btn.on_release()
            self.ids.department_switch_buttons.add_widget(btn)
            btn.bind(on_release=self.on_department_clock_in_release)

    def show_popup(self, instance):

        self.switch_dept_popup.update_pop_up_text(
            f"Attempting to clock you into {instance.text}"
        )
        self.switch_dept_popup.open()

    def on_department_clock_in_release(self, instance):
        self.show_popup(instance)
        self.department_pop_up_thread = threading.Thread(
            target=self.switch_departments, args=(instance,)
        )
        self.department_pop_up_thread.start()

    def switch_departments(self, instance):

        new_department = instance.dept_no
        badge_number = self.logged_in_user.emtoken

        # self.odooconn = odoodatabase.OdooDatabaseConnector(
        #    host=HOST, port=PORT, db=DB, user=USER, pwd=PASSW
        # )
        self.manager.ODOODBCONN.switch_departments(
            badge_number=badge_number, new_department=new_department
        )
        self.switch_from_department_screen(instance)
        self.switch_dept_popup.dismiss()

    @mainthread
    def switch_from_department_screen(self, instance):

        """
        TODO - I dont love these lines below, I think I may need to tie logged_in_user
            to a property so I can trigger and event when something changes. Seems to work for now
            but it's a little clunky. I found that my logged_in_used data type wasnt being updated
            to the cell clock in screen quick enough, it would show the cells for the preivously
            clocked in department, not the one I was switching to.
        """

        new_department = instance.dept_no
        badge_number = self.logged_in_user.emtoken

        App.get_running_app().logged_in_user = self.manager.ODOODBCONN.get_attendance_status(
            badge_number=badge_number
        )

        self.logged_in_user = App.get_running_app().logged_in_user

        if (
            str(new_department) in ["44", "42"]
            and self.logged_in_user.clocked_in_cell == False
        ):
            self.manager.current = "Cell Clock In"
        elif str(new_department) == "7":
            if self.manager.ODOODBCONN.get_available_shop_orders(7):
                self.manager.current = "available_shop_orders"
            else:
                self.manager.current = "AvailableDayWorkScreen"
        # Need a little better logic here
        # elif (
        #    str(new_department) in ["44", "42"]
        #    and self.logged_in_user.clocked_in_cell != False
        # ):
        #    self.manager.current = "available_shop_orders"
        else:
            self.manager.current = "welcome_screen"

    def on_leave(self, *args):
        super().on_leave(*args)
        self.ids.department_switch_buttons.clear_widgets()


class AttendanceClockedIn(ScreenPrep):

    """
    The id of the Attendance top bar in this class is:
        'top_attendance_clocked_in'
    """

    department = StringProperty("")
    department_number = StringProperty("0")
    daywork_jobs = ListProperty
    odooconn = ObjectProperty

    def __init__(self, **kwargs):
        super().__init__(
            top_bar_id="top_attendance_clocked_in", custom_timeout=100, **kwargs
        )

    def on_pre_enter(self, *args):
        super(AttendanceClockedIn, self).on_pre_enter(*args)
        # self.logged_in_user = App.get_running_app().logged_in_user
        self.department = self.logged_in_user.clocked_in_department[1]
        self.department_number = self.logged_in_user.clocked_in_department[0]
        self.attendance_button = (
            self.ids.top_attendance_clocked_in.ids.top_bar_middle_button
        )
        self.attendance_button.disabled = True
        self.attendance_button.color = [1, 1, 1, 1]
        # user_id = self.ids["top_attendance_clocked_in"].ids.user_id
        # user_id.text = f"{self.logged_in_user.name.upper()}"
        self.switch_cell_button = Button(
            text="Switch Cell",
            size_hint=(0.9, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(10, 10),
            background_normal="",
            background_color=[1, 1, 1, 1],
            color=[0, 0, 0, 1],
        )
        self.switch_cell_button.bind(on_release=self.on_switch_cell_release)

        self.daywork_button = Button(
            text="Available Daywork",
            size_hint=(0.9, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(10, 10),
            background_normal="",
            background_color=[1, 1, 1, 1],
            color=[0, 0, 0, 1],
        )

        self.daywork_button.bind(on_release=self.get_available_daywork)

        if self.logged_in_user.clocked_in_department[0] in ["44", "42"]:
            self.ids.attendance_switching_options.add_widget(self.switch_cell_button)
            self.ids.attendance_switching_options.add_widget(self.daywork_button)
        elif self.logged_in_user.clocked_in_department[0] in ["7"]:
            self.ids.attendance_switching_options.add_widget(self.daywork_button)

    def on_switch_cell_release(self, *args):

        self.manager.current = "Cell Clock In"

    def get_available_daywork(self, department_number):

        self.manager.current = "AvailableDayWorkScreen"

    def on_leave(self, *args):
        super(AttendanceClockedIn, self).on_leave(*args)
        self.ids.attendance_switching_options.remove_widget(self.switch_cell_button)
        self.ids.attendance_switching_options.remove_widget(self.daywork_button)


class CellClockIn(ScreenPrep):

    """The id for the top_attendance bar for this class is
        'top_attendance_switch_cells'
    """

    aqua = [0, 1, 1, 1]
    green = [0, 1, 0, 1]
    hot_pink = [1, 0.412, 0.706, 1]
    purple = [0.627, 0.125, 0.941, 1]
    orange = [1, 0.647, 0, 1]
    normal = [1, 1, 1, 1]
    navy = [0, 0, 0.502, 1]
    black = [0, 0, 0, 1]

    odooconn = ObjectProperty
    logged_in_user = ObjectProperty

    def __init__(self, **kwargs):
        super().__init__(
            top_bar_id="top_attendance_switch_cells", custom_timeout=None, **kwargs
        )

    def on_pre_enter(self, *args):
        super().on_pre_enter()
        # self.odooconn = odoodatabase.OdooDatabaseConnector(
        #    host=HOST, port=PORT, db=DB, user=USER, pwd=PASSW
        # )
        self.attendance_button = (
            self.ids.top_attendance_switch_cells.ids.top_bar_middle_button
        )
        self.attendance_button.bind(on_release=self.on_attendance_release)
        cells = self.get_cells()
        for cell in sorted(cells):
            btn = Button(
                text=cell,
                size_hint=((1 / 3), (1 / 7)),
                background_normal="",
                background_color=self.get_button_color(cell)[1],
                color=self.get_button_color(cell)[0],
                text_size=(self.width, None),
                halign="center",
                font_size=28,
            )
            btn.bind(on_release=self.on_cell_clock_in_release)
            self.ids.available_cells_stack_layout.add_widget(btn)

    def show_cell_popup(self, instance):

        self.pop_up = Factory.FeedbackPopup()
        self.pop_up.update_pop_up_text(f"Clocking you into {instance.text}")
        self.pop_up.open()

    def get_cells(self):
        department_number = int(self.logged_in_user.clocked_in_department[0])
        workcenters = self.manager.ODOODBCONN.find_department_cells(department_number)
        available_cells = []
        for workcenter in workcenters:
            if workcenter["code"][0].isalpha():
                available_cells.append(workcenter["code"])
        return available_cells

    def get_button_color(self, text):

        letter = text[0]
        if letter == "A":
            return self.black, self.aqua
        elif letter == "G":
            return self.black, self.green
        elif letter == "N":
            return self.normal, self.navy
        elif letter == "P" and text != "PLG":
            return self.black, self.purple
        elif letter == "M":
            return self.black, self.orange
        elif letter == "H":
            return self.black, self.hot_pink
        else:
            return self.black, self.normal

    def on_attendance_release(self, *args):
        self.manager.current = "AttendanceClockedIn"

    def on_cell_clock_in_release(self, instance):
        self.show_cell_popup(instance)
        self.cell_pop_up_thread = threading.Thread(
            target=self.clock_into_cell, args=(instance,)
        )
        self.cell_pop_up_thread.start()

    def clock_into_cell(self, instance):

        """ "In this method I will need to find the available shop order within selected cell and pass those
        to the AvaialableShopOrder screen. This might be a good spot for a list of dataclasses or something"""
        self.manager.ODOODBCONN.clock_into_cell(
            badge_number=self.logged_in_user.emtoken,
            department_number=self.logged_in_user.clocked_in_department[0],
            cell=instance.text,
        )
        self.switch_to_available_shop_orders()

    @mainthread
    def switch_to_available_shop_orders(self):
        self.manager.current = "available_shop_orders"
        self.pop_up.dismiss()

    def on_leave(self, *args):
        super().on_leave(*args)
        self.ids.available_cells_stack_layout.clear_widgets()


class AvailableShopOrders(ScreenPrep):
    """
        The id of the main attendance top bar for this screen is:
            'available_shop_order_top_bar'
    """

    """
        Plan: Get the available shop orders based on the swiped in department and probably the employee (in the case
        of self assignment or supervisor assignment). Populate the ShopOrder class with the set of shop orders my
        'get_available_shop_orders' method returns. Then populate all of the ShopOperation data based on that same 
        method call. The return of get_available_shop_orders is a dictionary where the keys() are the unique shop
        orders, each key provides a list of dictionaries that are the ShopOperations data.
    """
    available_shop_orders = DictProperty()
    shop_orders_section = ObjectProperty()
    scanned_shop_order = StringProperty("")
    temp_list = []

    odooconn = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(
            top_bar_id="available_shop_order_top_bar", custom_timeout=None, **kwargs
        )

    def _keyboard_closed(self):
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] not in ["shift"]:
            if keycode[1] == "enter":
                self.scanned_shop_order = "".join(self.temp_list[:]).upper()
                self.temp_list = []
            else:
                self.temp_list.append(text)

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        # self.odooconn = odoodatabase.OdooDatabaseConnector(
        #    host=HOST, port=PORT, db=DB, user=USER, pwd=PASSW
        # )
        self.get_shop_orders(self.logged_in_user.clocked_in_department[0])
        self.attendance_button = (
            self.ids.available_shop_order_top_bar.ids.top_bar_middle_button
        )
        self.attendance_button.bind(on_release=self.on_release_attendance)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, "text")
        if self._keyboard.widget:
            # If it exists, this widget is a VKeyboard object which you can use
            # to change the keyboard layout.
            pass
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def on_scanned_shop_order(self, *args):

        if self.scanned_shop_order != "":
            shop_order_data = self.manager.ODOODBCONN.get_available_shop_orders(
                clocked_in_department=self.logged_in_user.clocked_in_department,
                scanned_shop_order=self.scanned_shop_order,
            )
            shop_order_dataclass = ShopOrderData()
            data = []
            for shop in shop_order_data.values():
                for operation in shop:
                    data.append(
                        ShopOrderData(
                            name=operation["description"],
                            production_id=self.scanned_shop_order,
                            product_id="TODO",
                            state=operation["state"],
                            operation_id="TODO",
                            required=operation["required"],
                            remaining=operation["remaining"],
                            duration_expected=operation["duration_expected"],
                            qty_per_hr=operation["qty_per_hr"],
                        )
                    )
            self.scanned_shop_order = ""
            # print(shop_order_data)
            App.get_running_app().shop_order_data = data
            self.manager.current = "active_shop_order"

    def get_shop_orders(self, clocked_in_department):

        self.available_shop_orders = self.manager.ODOODBCONN.get_available_shop_orders(
            clocked_in_department=clocked_in_department
        )
        print(f"Clocked into {self.logged_in_user.clocked_in_department[0]}")
        self.shop_orders_section = self.ids.shop_orders
        if not self.available_shop_orders:
            self.shop_orders_section.add_widget(
                Label(
                    text="You have no assigned work, \n Please see your supervisor for more work.",
                    font_size=24,
                    text_size=self.size,
                    halign="center",
                    valign="center",
                )
            )
        else:
            for item in self.available_shop_orders.keys():
                self.shop_orders_section.add_widget(
                    availableshoporder.ShopOrder(
                        shop_order_data=item,
                        shop_operation_data=self.available_shop_orders[item],
                    )
                )

    def on_release_attendance(self, instance):
        self.manager.current = "AttendanceClockedIn"

    def on_leave(self, *args):
        super().on_leave(*args)
        self.shop_orders_section.clear_widgets()


class AvailableDayWork(ScreenPrep):

    """Top bar ID for this class is:
        top_attendance_available_daywork
    """

    odooconn = ObjectProperty
    available_daywork = ListProperty

    def __init__(self, **kwargs):
        super().__init__(
            top_bar_id="top_attendance_available_daywork", custom_timeout=None, **kwargs
        )

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        # self.odooconn = odoodatabase.OdooDatabaseConnector(
        #    host=HOST, port=PORT, db=DB, user=USER, pwd=PASSW
        # )
        if self.logged_in_user.clocked_in_department:
            self.available_daywork = self.manager.ODOODBCONN.get_available_daywork(
                self.logged_in_user.clocked_in_department[0]
            )
        else:
            self.available_daywork = []
        self.main_grid = self.ids.available_daywork_gridlayout
        for job in self.available_daywork:
            btn = Button(
                text=job["description"],
                size_hint=((1 / 3), (1 / 7)),
                background_normal="",
                background_color=[1, 1, 1, 1],
                color=[0, 0, 0, 1],
                halign="center",
                font_size=28,
            )
            self.main_grid.add_widget(btn)
        self.attendance_button = (
            self.ids.top_attendance_available_daywork.ids.top_bar_middle_button
        )
        self.attendance_button.bind(on_release=self.on_attendance_button_release)

    def on_attendance_button_release(self, instance):

        self.manager.current = "AttendanceClockedIn"

    def on_leave(self, *args):
        super().on_leave(*args)
        self.main_grid.clear_widgets()


class ActiveShopOrder(ScreenPrep):

    """The id of the top_bar for this class is:
            active_shop_order_top_bar
    """

    post_good_popup = PostGoodShopOperationsPopup()
    post_scrap_popup = PostScrapPopup()
    current_app = ObjectProperty()

    qty_required = ObjectProperty()
    qty_remaining = ObjectProperty()
    operation_description = ObjectProperty()
    operation_parts_per_hour = ObjectProperty()
    part_description = ObjectProperty()
    workcenter = ObjectProperty()
    shop_order_sequence = ObjectProperty()
    qty_posted_this_shift = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(
            top_bar_id="active_shop_order_top_bar", custom_timeout=None, **kwargs
        )

    def gather_data_fields(self):
        # print(self.ids)
        self.qty_required = self.ids.operation_parts_required
        self.qty_remaining = self.ids.operation_parts_remaining
        self.operation_description = self.ids.operation_description
        self.operation_parts_per_hour = self.ids.operation_parts_per_hour

    def populate_fields(self):
        self.gather_data_fields()
        self.qty_required.text = str(self.shop_order_data[0].required)
        self.qty_remaining.text = str(self.shop_order_data[0].remaining)
        self.operation_description.text = self.shop_order_data[0].name
        self.operation_parts_per_hour.text = (
            f"{str(self.shop_order_data[0].qty_per_hr)} Parts per Hour"
        )
        print(self.operation_description.text)

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        self.post_good_button = self.ids.post_good_button
        self.post_scrap_button = self.ids.post_scrap_button
        self.post_good_button.bind(on_release=self.on_post_good)
        self.post_scrap_button.bind(on_release=self.on_post_scrap)
        self.attendance_button = (
            self.ids.active_shop_order_top_bar.ids.top_bar_middle_button
        )
        self.attendance_button.bind(on_release=self.on_attendance_release)
        self.shop_order_data = App.get_running_app().shop_order_data
        self.populate_fields()
        print(self.shop_order_data)

    def show_post_good_popup(self, *args):

        self.post_good_popup.open()

    def on_post_good(self, instance):

        self.show_post_good_popup()

    def on_post_scrap(self, instance):

        self.post_scrap_popup.open()

    def on_attendance_release(self, instance):

        pass

    def close_all_popups(self):

        self.post_scrap_popup.dismiss()
        self.post_good_popup.dismiss()

    def logout(self, *args):
        super().logout(*args)
        self.close_all_popups()


class Timesheet(ScreenPrep):
    """
    The ID of the top bar for this class is:
        timesheet_top_bar
    """

    def __init__(self, **kwargs):
        super().__init__(top_bar_id="timesheet_top_bar", custom_timeout=None, **kwargs)

    def on_enter(self, *args):
        # self.start_timeout()
        super(Timesheet, self).on_pre_enter(*args)
        # self.ids.timesheet_top_bar.ids.current_screen.text = "Timesheets"
        self.back_button = self.ids.timesheet_top_bar.ids.top_bar_middle_button
        self.back_button.text = "Back"
        self.back_button.bind(on_release=self.go_to_previous_screen)

    # def on_touch_up(self, touch):
    #    timeout_bar = self.ids["timesheet_top_bar"].ids.timeout_bar
    #    timeout_bar.value = 0

    # def start_timeout(self, *args):
    #    self.event = Clock.schedule_interval(self.timeout_countdown, 1 / 60)

    # def timeout_countdown(self, *args):
    #    timeout_bar = self.ids["timesheet_top_bar"].ids.timeout_bar
    #    timeout_bar.value += 1 / 60
    #    if timeout_bar.value >= timeout_bar.max:
    #        timeout_bar.value = 0
    #        self.logout()

    def go_to_previous_screen(self, instance):

        self.manager.current = App.get_running_app().screen_tracker.previous_screen

    # def on_leave(self, *args):
    #    self.event.cancel()


class KioskScreenManager(ScreenManager):

    ODOODBCONN = ObjectProperty()


class KioskApp(App):
    def __init__(self, **kwargs):
        super(KioskApp, self).__init__(**kwargs)
        self.logged_in_user = LoggedInUser()
        self.attendance = AttendanceInfo()
        self.s_m = ScreenManager()
        self.streaming_radio = StreamingRadio()
        self.screen_tracker = ScreenTracker()
        self.radio_stations = []
        self.shop_order_data = []

    def build(self):
        k = Builder.load_file("kiosk_main.kv")
        return k


if __name__ == "__main__":

    KioskApp().run()
