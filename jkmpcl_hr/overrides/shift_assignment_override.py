import frappe
from frappe.utils import getdate, add_days
from hrms.hr.doctype.shift_assignment.shift_assignment import ShiftAssignment


class CustomShiftAssignment(ShiftAssignment):

    # -----------------------------------------
    # Override overlap validation
    # -----------------------------------------

    def validate_overlapping_shifts(self):

        # prevent validation when auto-created split record is inserted
        if getattr(self.flags, "from_auto_split", False):
            return

        # allow overlap only if it can be split
        if self.can_split_existing_shift():
            return

        # otherwise keep standard HRMS behavior
        super().validate_overlapping_shifts()


    # -----------------------------------------
    # Check whether overlap is valid for split
    # -----------------------------------------

    def can_split_existing_shift(self):

        existing = frappe.db.sql("""
            SELECT
                name,
                start_date,
                end_date
            FROM `tabShift Assignment`
            WHERE employee = %s
            AND docstatus = 1
            AND name != %s
            AND start_date <= %s
            AND end_date >= %s
            ORDER BY start_date DESC
            LIMIT 1
        """,
        (
            self.employee,
            self.name,
            self.start_date,
            self.end_date
        ),
        as_dict=1)

        return bool(existing)


    # -----------------------------------------
    # Run split logic after approval on submit
    # -----------------------------------------

    def before_submit(self):

        # skip when system creates trailing split record
        if getattr(self.flags, "from_auto_split", False):
            return

        self.split_existing_shift()


    # -----------------------------------------
    # Split old assignment into 3 parts
    # -----------------------------------------

    def split_existing_shift(self):

        existing = frappe.db.sql("""
            SELECT
                name,
                start_date,
                end_date,
                shift_type
            FROM `tabShift Assignment`
            WHERE employee = %s
            AND docstatus = 1
            AND name != %s
            AND start_date <= %s
            AND end_date >= %s
            ORDER BY start_date DESC
            LIMIT 1
        """,
        (
            self.employee,
            self.name,
            self.start_date,
            self.end_date
        ),
        as_dict=1)


        if not existing:
            return


        old = existing[0]

        old_from = getdate(old.start_date)
        old_to = getdate(old.end_date)

        new_from = getdate(self.start_date)
        new_to = getdate(self.end_date)

        before_end = add_days(new_from, -1)
        after_start = add_days(new_to, 1)


        # -------------------------------------
        # PART 1:
        # shorten original assignment
        # -------------------------------------

        if old_from <= before_end:

            frappe.db.set_value(
                "Shift Assignment",
                old.name,
                "end_date",
                before_end,
                update_modified=False
            )


        # -------------------------------------
        # PART 2:
        # current submitted request remains as-is
        # (this document)
        # -------------------------------------


        # -------------------------------------
        # PART 3:
        # create tail assignment if needed
        # -------------------------------------

        if after_start <= old_to:

            old_doc = frappe.get_doc(
                "Shift Assignment",
                old.name
            )

            split_doc = frappe.copy_doc(old_doc)

            split_doc.start_date = after_start
            split_doc.end_date = old_to

            # avoid recursive split logic
            split_doc.flags.from_auto_split = True

            split_doc.insert()
            split_doc.submit()