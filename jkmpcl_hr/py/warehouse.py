import frappe

def validate(self, method):
    if self.custom_location:
        latitude = frappe.db.get_value("Location", self.custom_location, "latitude")
        longitude = frappe.db.get_value("Location", self.custom_location, "longitude")

        if not latitude or not longitude or float(latitude) == 0.0 or float(longitude) == 0.0:
            frappe.msgprint(
                f"Please set valid Latitude and Longitude in Location {self.custom_location}."
            )