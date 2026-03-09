import frappe
from frappe.utils import getdate

def validate_weekly_off(doc, method):
    try:
        if not doc.weekly_off:
            frappe.log_error("no_data_found_error_while_validating_weekly_off", f"No Weekly off day found for Holiday List {doc.name}")
            return

        weekly_off_day = doc.weekly_off

        for row in doc.holidays:
            if row.holiday_date:
                day_name = getdate(row.holiday_date).strftime("%A")

                if day_name == weekly_off_day and not row.weekly_off:
                    row.weekly_off = 1

    except Exception as e:
        frappe.log_error("error_while_validating_weekly_off", frappe.get_traceback())
    