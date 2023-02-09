import datetime
import pprint
import time
from dataclasses import dataclass
from decimal import *

import odoorpc

HOST = "telescopecasual-sandbox-kiosk-6449204.dev.odoo.com"
PORT = 443
DB = "telescopecasual-sandbox-kiosk-6449204"
USER = "kioskuser"
PASSW = "kioskuser"


@dataclass
class LoggedInUser:
    employee_id: int = 0
    clock_number: int = 0
    clock_status: str = ""
    clocked_in_department: int = 0
    clocked_in_cell: str = ""
    emtoken: str = ""
    name: str = ""


class OdooDatabaseConnector:
    def __init__(self, host, port, db, user, pwd):
        self.api = odoorpc.ODOO(host, port=port, protocol="jsonrpc+ssl")
        self.api.login(db, user, pwd)
        # self.Model = self.api.env[self.model]

    def get_attendance_status(self, badge_number):
        # Hardcode my employee 'barcode' in for testing from sandbox-jake
        # badge_number = 'EMTKN=9FSMGIJLNWY?'
        employee_id = self.api.env["hr.employee"].search_read(
            [("barcode", "=", badge_number)],
            ["clock_number", "name", "barcode"],
            limit=1,
        )
        # This should give me the last check in from the given employee
        if employee_id:
            attendance = self.api.env["hr.attendance"].search_read(
                [("employee_id", "=", employee_id[0]["id"]), ("check_out", "=", False)],
                ["check_in", "check_out", "clocked_in_department", "clocked_in_cell"],
                limit=1,
                order="id desc",
            )
            if attendance:
                last_check_in = datetime.datetime.strptime(
                    attendance[0]["check_in"], "%Y-%m-%d %H:%M:%S"
                ).date()
                # Check whether the last checked_in date is today and we haven't checked_out yet
                if (
                    last_check_in == datetime.datetime.now().date()
                    and attendance[0]["check_out"] == False
                ):
                    department_id = attendance[0]["clocked_in_department"][0]
                    department_number = self.api.env["hr.department"].search_read(
                        [("id", "=", department_id)], ["name", "dept_no"]
                    )
                    if attendance[0]["clocked_in_cell"]:
                        workcenter_id = attendance[0]["clocked_in_cell"][0]
                        workcenter_code = self.api.env["mrp.workcenter"].search_read(
                            [("id", "=", workcenter_id)], ["code"]
                        )
                    else:
                        workcenter_code = False
                    logged_in_user = LoggedInUser(
                        employee_id=employee_id[0]["id"],
                        clock_number=employee_id[0]["clock_number"],
                        clock_status="in",
                        emtoken=employee_id[0]["barcode"],
                        name=employee_id[0]["name"],
                        clocked_in_department=(
                            department_number[0]["dept_no"],
                            department_number[0]["name"],
                        ),
                        clocked_in_cell=workcenter_code[0]["code"]
                        if workcenter_code
                        else False,
                    )
                    return logged_in_user
            else:
                """If we don't have attendance but we do have an employee they just have clocked in yet today"""
                employee_to_check_in = self.api.env["hr.employee"].search_read(
                    [("id", "=", employee_id[0]["id"])],
                    ["name", "clock_number", "barcode"],
                )
                clocked_out_employee = LoggedInUser(
                    employee_id=employee_to_check_in[0]["id"],
                    clock_number=employee_to_check_in[0]["clock_number"],
                    clock_status="out",
                    emtoken=employee_to_check_in[0]["barcode"],
                    name=employee_id[0]["name"],
                )
                return clocked_out_employee
        return None

    def badge_to_employee(self, badge_number):

        employee_id = self.api.env["hr.employee"].search_read(
            [("barcode", "=", badge_number)], ["id"]
        )
        return employee_id

    def department_number_to_department_id(self, department_number):

        return self.api.env["hr.department"].search(
            [("dept_no", "=", department_number)]
        )

    def get_clocked_in_department(self, department_number):

        """Use our custom field dept_no to get the department number off of the buttons
        custom property dept_no!!!!"""

        return self.api.env["hr.department"].search(
            [("dept_no", "=", department_number)], limit=1
        )

    def check_into_odoo(self, badge_number=None, department_number=None):

        """
        I'm going to assume that for now if we have made it to this method that the
        user has not clocked in yet for this day. Swtiching departments will be another thing.

        TODO: create checked_in_department field so that I can pass department_id to Odoo
        """

        employee_id = self.badge_to_employee(badge_number)

        department_id = self.get_clocked_in_department(department_number)

        self.api.env["hr.attendance"].create(
            {
                "employee_id": employee_id[0]["id"],
                "check_in": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "clocked_in_department": department_id[0],
            }
        )

    def check_out_of_odoo(self, employee_id):

        attendance_record = self.api.env["hr.attendance"].search(
            [("employee_id", "=", employee_id), ("check_out", "=", False)]
        )

        check_out = self.api.env["hr.attendance"].browse(attendance_record[0])
        check_out.write(
            {"check_out": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        )

    def find_department_cells(self, department_number):

        department_id = self.department_number_to_department_id(department_number)
        print(f"finding cells in department {department_id[0]}")

        return self.api.env["mrp.workcenter"].search_read(
            [("department_id", "=", department_id[0])], ["code"]
        )

    def clock_into_cell(self, badge_number=None, department_number=None, cell=None):
        """
        Find the current department that the operator is currently clocked into. Then find the Odoo id of
        the selected cell. The user should only be presented with the cells available for whichever department
        they are currently clocked into
        """
        employee_id = self.badge_to_employee(badge_number)
        current_department_id = self.get_clocked_in_department(department_number)
        workcenter_id = self.api.env["mrp.workcenter"].search([("code", "=", cell)])

        self.check_out_of_odoo(employee_id[0]["id"])
        self.api.env["hr.attendance"].create(
            {
                "employee_id": employee_id[0]["id"],
                "check_in": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "clocked_in_department": current_department_id[0],
                "clocked_in_cell": workcenter_id[0],
            }
        )

        return True

    def switch_cells(self, employee_id, old_cell, new_cell):

        pass

    def switch_departments(self, badge_number=None, new_department=None):

        """This method will be used to switch departments within an hr.attendance model:
        im thinking something like:
            check_out with old department
            check_in with new department
            leave the timestamps the same?"""
        employee_id = self.badge_to_employee(badge_number=badge_number)
        print(employee_id)

        self.check_out_of_odoo(employee_id[0]["id"])
        self.check_into_odoo(
            badge_number=badge_number, department_number=new_department
        )

    def get_available_daywork(self, department_number):
        @dataclass
        class DayworkJobs:
            id: int
            job_number: str
            description: str

        department_id = self.department_number_to_department_id(int(department_number))

        daywork_jobs = self.api.env["payroll.job.numbers"].search_read(
            [
                ("job_number_type", "=", "daywork"),
                ("department_ids", "in", department_id[0]),
            ],
            ["job_number", "description"],
        )
        return daywork_jobs

    def get_selected_radio_station(self, selected_station):

        if selected_station != "None - Stop Playing Radio":

            available_radio_stations = self.api.env["kiosk.radio.stations"].search_read(
                [("name", "=", selected_station)], ["name", "url"], limit=1
            )

            return available_radio_stations

    def get_all_radio_stations(self):

        return self.api.env["kiosk.radio.stations"].search_read([], ["name"])

    def get_department_id_from_dept_no(self, department_num):

        return self.api.env["hr.department"].search([("dept_no", "=", department_num)])

    def get_available_shop_orders(self, clocked_in_department, scanned_shop_order=None):
        start = time.time()
        """
            BPCSF.FSO could be replaced by MRP.PRODUCTION
            BPCSF.FOD could be replaced by MRP.WORKORDER
            The dictionary from this method needs to return the following keys
            *production_id.name
            *production_id.product_tmpl_id.name (or default_code)
            *workorder_ids
                *workorder_ids.state
                *workorder_ids.sequence
                *workorder_ids.name
                *workorder_ids.qty_production (Original Production Quantity)
                *workorder_ids.qty_remaining

            I may still need to filter out shop orders that don't have material ready
        """
        # TODO: A future manufacturing_customizations module will need to introduce the concept of operation
        #  numbers so that they can be provided here instead of doing a bunch of extra queries. We will need to
        #  record both the original operation number and operation number for the actual shop order backed up from the
        #  last op being 999.

        # dept_no = self.get_attendance_status("9FSMGIJLNWY").clocked_in_department[0]
        department_id = self.get_department_id_from_dept_no(clocked_in_department)

        # Need to do some additional filtering here to make sure that the workorder is actually 'available'
        # ie no other operators are working on it and the material is ready/available
        if scanned_shop_order:
            dept_workorders = self.api.env["mrp.workorder"].search_read(
                [
                    ("workcenter_id.department_id", "=", department_id[0]),
                    ("production_id.name", "=", scanned_shop_order),
                ],
                [
                    "name",
                    "production_id",
                    "product_id",
                    "state",
                    "operation_id",
                    "qty_production",
                    "qty_remaining",
                    "duration_expected",
                    "is_user_working",
                ],
            )
        else:
            dept_workorders = self.api.env["mrp.workorder"].search_read(
                [("workcenter_id.department_id", "=", department_id[0])],
                [
                    "name",
                    "production_id",
                    "product_id",
                    "state",
                    "operation_id",
                    "qty_production",
                    "qty_remaining",
                    "duration_expected",
                    "is_user_working",
                ],
            )

        # if scanned_shop_order:

        #   dept_workorders.filtered(lambda s: s.name == scanned_shop_order)

        available_shop_orders = set()
        shop_order_dict = dict()
        for shop in dept_workorders:
            available_shop_orders.add(
                f"{shop['production_id'][1]} {shop['product_id'][1]}"
            )

        for item in available_shop_orders:
            shop_order_dict[item] = []

        for shop in dept_workorders:
            for item in list(shop_order_dict.keys()):
                if f"{shop['production_id'][1]} {shop['product_id'][1]}" == item:
                    qty_per_hr = Decimal(
                        60 / (shop["duration_expected"] / shop["qty_production"])
                    ).quantize(Decimal(1.0), rounding="ROUND_UP")

                    shop_order_dict[
                        f"{shop['production_id'][1]} {shop['product_id'][1]}"
                    ].append(
                        dict(
                            state=shop["state"],
                            is_user_working=shop["is_user_working"],
                            # operation=operations.search_read(
                            #    [("id", "=", shop["operation_id"][0])], ["sequence"]
                            # )[0]["sequence"],
                            description=shop["operation_id"][1],
                            required=shop["qty_production"],
                            remaining=shop["qty_remaining"],
                            duration_expected=shop["duration_expected"],
                            qty_per_hr=str(qty_per_hr),
                        )
                    )
        stop = time.time()
        print(f"Finished method in {stop-start} seconds")
        # print(shop_order_dict)
        return shop_order_dict


if __name__ == "__main__":

    pp = pprint.PrettyPrinter(indent=2)
    kiosk_login = OdooDatabaseConnector(HOST, PORT, DB, USER, PASSW)
    # start = time.time()
    # attendance = kiosk_login.get_attendance_status("9FSMGIJLNWY")
    # stop = time.time()
    # print(f"Finished in {stop - start} seconds")
    # print(attendance)
    shop_order_data = kiosk_login.get_available_shop_orders(7, "WH/MO/00024")
    pp.pprint(shop_order_data)
    # radio_stations = kiosk_login.get_selected_radio_station("Country")
    # print(kiosk_login.get_all_radio_stations())
    # print(radio_stations[0]["url"])
    # workcenters = kiosk_login.find_department_cells(44)
    # print(workcenters)
    # cell_clock_in = kiosk_login.clock_into_cell("9FSMGIJLNWY", "44", "HP1")
    # daywork_jobs = kiosk_login.get_available_daywork("7")
