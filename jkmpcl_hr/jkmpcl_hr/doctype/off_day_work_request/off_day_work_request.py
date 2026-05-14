# Copyright (c) 2025, SanskarTechnolab and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document, getdate
from jkmpcl_hr.py.utils import send_notification_email, get_current_holiday_list
from frappe.model.workflow import apply_workflow
from frappe.utils import add_days, date_diff,formatdate
from jkmpcl_hr.jkmpcl_hr.doctype.attendance_lock.attendance_lock import AttendanceLock


class OffDayWorkRequest(Document):
    def validate(self):
        self.validate_working_day()
        self.validate_duplicate_request()
        if self.date:
            lock_name = AttendanceLock.is_attendance_locked(self.date,self.employee)

            if lock_name:
                # ✅ Permission-safe fetch
                month = frappe.db.get_value("Attendance Lock", lock_name, "month")

                # ✅ fallback if month is empty
                if not month:
                    month = formatdate(self.date, "MMMM yyyy")

                frappe.throw(
                    f"Attendance is locked for {month}. Cannot apply Off Day Request.",
                    title="Attendance Lock"
                )

    def after_insert(self):
        approver = frappe.db.get_list(
            "Approver",
            filters={
                "parent": self.employee,
                "effective_from": ["<=", frappe.utils.now_datetime()],
                "parentfield": "custom_reporting_manager"
            },
            fields=["name"],
            order_by="effective_from desc",
            ignore_permissions=True,
            limit=1
        )
        approver_user = frappe.db.get_value("Approver", approver[0].name, "user") if approver else None

        if approver_user == frappe.session.user:
            apply_workflow(self, "Approve")

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
                "docstatus": ["!=", 2], 
                "workflow_state": ["!=", "Rejected"],
                "name": ["!=", self.name]  # allow updating same doc
            }
        )

        if exists:
            frappe.throw(
                _("Off-Day Work Request already exists for employee <b>{0}</b> on <b>{1}</b>.").format(
                    self.employee, self.date
                )
            )

    def on_update(self):
        self.handle_workflow_notification()

    def handle_workflow_notification(self):

        recipients,notification_name = self.get_notification_recipients()

        notification_doc = frappe.get_doc("Notification", notification_name)
        if notification_doc:

            # Call your custom notification function
            send_notification_email(
                recipients=recipients,
                doctype=self.doctype,
                docname=self.name,
                notification_name=notification_name,
                send_link=False,
                fallback_subject=f"Off-Day Work Request for {self.date}",
                fallback_message=f"Off-Day Work Request for { self.date } is now in '{ self.workflow_state }' state.",
                enabled=notification_doc.enabled,
                send_system_notification=notification_doc.send_system_notification,
                channel=notification_doc.channel
            )

    def get_notification_recipients(self):
        recipients = []
        approver_user = None
        notification_name = "Off-Day Work Request Approval"

        if self.owner == frappe.db.get_value("Employee", self.employee, "user_id"):
            if self.workflow_state == "Pending":
                approver = frappe.db.get_list(
                    "Approver",
                    filters={
                        "parent": self.employee,
                        "effective_from": ["<=", frappe.utils.now_datetime()],
                        "parentfield": "custom_reporting_manager"
                    },
                    fields=["name"],
                    order_by="effective_from desc",
                    ignore_permissions=True,
                    limit=1
                )

                if approver:
                    approver_user = frappe.db.get_value("Approver", approver[0].name, "user")

            elif self.workflow_state in ["Approved", "Rejected"]:
                approver_user = frappe.db.get_value("Employee", self.employee, "user_id")
                if self.workflow_state == "Approved":
                    notification_name = "Off-Day Work Request Approved"
                else:
                    notification_name = "Off-Day Work Request Rejected"

        else:
            if self.workflow_state == "Approved":
                approver_user = frappe.db.get_value("Employee", self.employee, "user_id")
                notification_name = "Off-Day Work Request Assigned"

        if approver_user:
            recipients.append(approver_user)

        return recipients, notification_name


@frappe.whitelist()
def check_working_day_valid(employee, date):
    date = getdate(date)
    return is_holiday(employee, date)
    # return is_week_off(employee, date) or is_holiday(employee, date)

def is_holiday(employee, date):
    holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")
    #* FOR SAFETY
    correct_holiday_list = None
    current_holiday_list = get_current_holiday_list(employee, date)

    
    if current_holiday_list:
        correct_holiday_list = current_holiday_list
    else:
        correct_holiday_list = holiday_list if holiday_list else None
        
    # if not holiday_list:
    #     holiday_list = frappe.db.get_value(
    #         "Company",
    #         frappe.defaults.get_global_default("company"),
    #         "default_holiday_list"
    #     )

    if not correct_holiday_list:
        return False

    return frappe.db.exists("Holiday", {
        "parent": correct_holiday_list,
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