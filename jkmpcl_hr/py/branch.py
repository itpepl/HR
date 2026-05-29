import re
import frappe

def validate(self, method):

    for row in self.custom_branch_hours_setting:
        hours_value = str(row.hours).strip()
        if not re.match(r'^\d+hours$', hours_value):

            frappe.throw(
                f"Please enter valid format in row {row.idx}. Example: 8hours"
            )