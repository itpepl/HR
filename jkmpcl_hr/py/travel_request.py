import frappe
from frappe import _

def validate(self, method):
    existing = frappe.db.exists(
        "Travel Request",
        {
            "employee": self.employee,
            "custom_travel_request_date": self.custom_travel_request_date,
            "name": ["!=", self.name]
        }
    )

    if existing:
        frappe.throw(
            _("Travel Request already exists for Employee {0} on date {1}")
            .format(self.employee, self.custom_travel_request_date)
        )