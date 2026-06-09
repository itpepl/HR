import frappe

def validate(self, method):
    if self.custom_geo_fence_radius < 0:
        frappe.throw(f" Geo Fence Radius cannot be negative.")

    seen_combinations = set()

    for row in self.custom_punch_limit_setting:

        # Negative value validation
        if row.punch_count < 0:
            frappe.throw(
                f"Row #{row.idx}: Punch Count cannot be negative."
            )
        if row.punch_count > 9:
            frappe.throw(
                f"Row #{row.idx}: Punch Count cannot be a double-digit number."
            )

        # Duplicate Department + Attendance Source validation
        key = (row.department, row.attendnace_source)

        if key in seen_combinations:
            frappe.throw(
                f"Row #{row.idx}: Department '{row.department}' and Attendance Source '{row.attendnace_source}' already exist in another row."
            )

        seen_combinations.add(key)