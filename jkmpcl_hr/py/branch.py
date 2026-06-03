import re
import frappe

def validate(self, method):

    for row in self.custom_branch_hours_setting:

        hours_value = str(row.hours).strip()
        if not re.match(r'^\d+hours$', hours_value):
            frappe.throw(
                f"Please enter valid format in row {row.idx}. Example: 8hours"
            )

        # From Month Validation
        if row.from_month and (int(row.from_month) < 1 or int(row.from_month) > 12):
            frappe.throw(
                f"From Month in row {row.idx} must be between 1 to 12."
            )

        # To Month Validation
        if row.to_month and (int(row.to_month) < 1 or int(row.to_month) > 12):
            frappe.throw(
                f"To Month in row {row.idx} must be between 1 to 12."
            )