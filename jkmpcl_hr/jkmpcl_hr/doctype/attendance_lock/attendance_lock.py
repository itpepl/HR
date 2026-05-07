# import frappe
# from frappe.model.document import Document
# from frappe.utils import getdate


# class AttendanceLock(Document):

#     def validate(self):
#         # -----------------------------
#         # Date validation
#         # -----------------------------
#         if self.from_date and self.to_date:
#             if getdate(self.from_date) > getdate(self.to_date):
#                 frappe.throw("From Date cannot be greater than To Date")

#         # -----------------------------
#         # Overlapping lock check
#         # -----------------------------
#         existing = frappe.db.exists(
#             "Attendance Lock",
#             {
#                 "name": ["!=", self.name],
#                 # "docstatus": 1,
#                 "from_date": ["<=", self.to_date],
#                 "to_date": [">=", self.from_date],
#             }
#         )

#         if existing:
#             frappe.throw("Attendance already locked for this period")

#     # -------------------------------------------------
#     # MAIN FUNCTION
#     # -------------------------------------------------
#     @staticmethod
#     def is_attendance_locked(date):

#         date = getdate(date)

#         locks = frappe.get_all(
#             "Attendance Lock",
#             # filters={"docstatus": 0},
#             fields=["name", "from_date", "to_date"]
#         )

#         user_roles = set(frappe.get_roles())

#         for lock in locks:

#             from_date = getdate(lock.from_date)
#             to_date = getdate(lock.to_date)

#             # ✅ Check only inside lock period
#             if not (from_date <= date <= to_date):
#                 continue

#             # -----------------------------
#             # Get roles from child table
#             # -----------------------------
#             allowed = frappe.get_all(
#                 "Attendance Lock Table",
#                 filters={"parent": lock.name},
#                 fields=["role"]
#             )

#             lock_roles = set(d.role for d in allowed if d.role)

#             # -----------------------------
#             # 🔥 HR MANAGER BYPASS LOGIC
#             # -----------------------------

#             # If HR Manager NOT in table → bypass
#             if "HR Manager" in user_roles and "HR Manager" not in lock_roles:
#                 return False

#             # -----------------------------
#             # NORMAL LOGIC
#             # -----------------------------

#             # If no roles defined → lock for everyone
#             if not lock_roles:
#                 return True

#             # If user has role in table → BLOCK
#             if user_roles.intersection(lock_roles):
#                 return True

#             # Otherwise allow
#             return False

#         # No lock found → allow
#         return False

import frappe
from frappe.model.document import Document
from frappe.utils import (
    getdate,
    get_first_day,
    get_last_day
)
from datetime import datetime


class AttendanceLock(Document):

    def validate(self):

        month_map = {
            "January": 1,
            "February": 2,
            "March": 3,
            "April": 4,
            "May": 5,
            "June": 6,
            "July": 7,
            "August": 8,
            "September": 9,
            "October": 10,
            "November": 11,
            "December": 12
        }


        if self.month and self.year:

            month_number = month_map.get(self.month)

            if month_number:

                # Example: 2026-03-01
                first_date = f"{self.year}-{month_number:02d}-01"

                self.from_date = get_first_day(first_date)
                self.to_date = get_last_day(first_date)

        # =================================================
        # DATE VALIDATION
        # =================================================
        if self.from_date and self.to_date:

            if getdate(self.from_date) > getdate(self.to_date):
                frappe.throw("From Date cannot be greater than To Date")

        # =================================================
        # CHILD TABLE AUTO VALUES
        # =================================================
        for row in self.attendance_lock_details:


            if not row.locked_on:
                row.locked_on = frappe.utils.now_datetime()

    
            if not row.locked_by:
                row.locked_by = frappe.session.user

     
            if not row.user_name:

                full_name = frappe.db.get_value(
                    "User",
                    frappe.session.user,
                    "full_name"
                )

                row.user_name = full_name

        
        if self.month and self.attendance_lock_details:

            selected_month = month_map.get(self.month)

            for row in self.attendance_lock_details:

                if row.locked_on:

                    locked_date = getdate(row.locked_on)

                    if locked_date.month != selected_month:

                        frappe.throw(
                            f"Row {row.idx}: Locked On date "
                            f"{locked_date} is not inside selected month {self.month}"
                        )

                    if str(locked_date.year) != str(self.year):

                        frappe.throw(
                            f"Row {row.idx}: Locked On date year "
                            f"{locked_date.year} does not match selected year {self.year}"
                        )

                    # -----------------------------------------
                    # DATE RANGE VALIDATION
                    # -----------------------------------------
                    if not (
                        getdate(self.from_date)
                        <= locked_date
                        <= getdate(self.to_date)
                    ):

                        frappe.throw(
                            f"Row {row.idx}: Locked On date "
                            f"{locked_date} must be between "
                            f"{self.from_date} and {self.to_date}"
                        )

        existing = frappe.db.exists(
            "Attendance Lock",
            {
                "name": ["!=", self.name],
                "docstatus": ["!=", 2],

                # overlap condition
                "from_date": ["<=", self.to_date],
                "to_date": [">=", self.from_date],
            }
        )

        if existing:
            frappe.throw("Attendance already locked for this period")
        # =====================================================
        # MAIN FUNCTION
        # =====================================================
    @staticmethod
    def is_attendance_locked(date):

        date = getdate(date)


        locks = frappe.get_all(
            "Attendance Lock",
            filters={
                "docstatus": ["!=", 2]
            },
            fields=[
                "name",
                "from_date",
                "to_date"
            ]
        )


        user_roles = set(frappe.get_roles())

        for lock in locks:

            from_date = getdate(lock.from_date)
            to_date = getdate(lock.to_date)


            if not (from_date <= date <= to_date):
                continue


            allowed_roles = frappe.get_all(
                "Attendance Lock Table",
                filters={
                    "parent": lock.name
                },
                fields=[
                    "role"
                ]
            )

            lock_roles = set(
                d.role for d in allowed_roles if d.role
            )


            if (
                "HR Manager" in user_roles
                and "HR Manager" not in lock_roles
            ):
                return False

            if not lock_roles:
                return True

            if user_roles.intersection(lock_roles):
                return True

            return False

        return False