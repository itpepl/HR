# Copyright (c) 2025, SanskarTechnolab and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document, getdate


class OffDayWorkRequest(Document):
    def validate(self):
        self.validate_working_day()
        self.validate_duplicate_request()

    def validate_working_day(self):
        if not check_working_day_valid(self.employee, self.date):
            frappe.throw(
            _("Selected date {0} is not a Week-Off or Holiday for this employee.").format(self.date)
        )
            
    def validate_duplicate_request(self):
        exists = frappe.db.exists(
            "Off-Day Work Request",
            {
                "employee": self.employee,
                "date": self.date,
                "docstatus": ["!=", 2],   # ignore cancelled
                "name": ["!=", self.name]  # allow updating same doc
            }
        )

        if exists:
            frappe.throw(
                _("Off-Day Work Request already exists for employee <b>{0}</b> on <b>{1}</b>.").format(
                    self.employee, self.date
                )
            )

@frappe.whitelist()
def check_working_day_valid(employee, date):
    date = getdate(date)
    return is_holiday(employee, date)
    # return is_week_off(employee, date) or is_holiday(employee, date)

def is_holiday(employee, date):
    holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")

    # if not holiday_list:
    #     holiday_list = frappe.db.get_value(
    #         "Company",
    #         frappe.defaults.get_global_default("company"),
    #         "default_holiday_list"
    #     )

    if not holiday_list:
        return False

    return frappe.db.exists("Holiday", {
        "parent": holiday_list,
        "holiday_date": date
    })


def is_week_off(employee, date):
    # Get active shift assignment
    shift_assignment = frappe.db.get_list(
        "Shift Assignment",
        filters={
            "employee": employee,
            "start_date": ["<=", date],
            "status": "Active"
        },
        or_filters=[
            {"end_date": [">=", date]},
            {"end_date": ["is", "not set"]}
        ],
        fields=["shift_type"],
        order_by="start_date desc",
        limit=1
    )

    shift_type = shift_assignment[0].shift_type if shift_assignment else None

    if not shift_type:
        return False

    # Get weekly off from Shift Type
    shift = frappe.db.get_value(
        "Shift Type",
        shift_type,
        ["weekly_off"],
        as_dict=True
    )

    if not shift or not shift.weekly_off:
        return False

    weekday = date.strftime("%A")  # Monday, Tuesday...

    weekly_off_days = [d.strip() for d in shift.weekly_off.split(",")]

    return weekday in weekly_off_days