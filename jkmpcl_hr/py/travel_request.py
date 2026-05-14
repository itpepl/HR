import frappe
from frappe import _
from frappe.utils import get_datetime

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

    for row in self.itinerary:

        if row.departure_date and row.arrival_date:

            departure = get_datetime(row.departure_date)
            arrival = get_datetime(row.arrival_date)

            if arrival < departure:
                frappe.throw(
                    _("Row {0}: Arrival Datetime cannot be before Departure Datetime")
                    .format(row.idx)
                )