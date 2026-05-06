import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class AttendanceLock(Document):

    def validate(self):
        # -----------------------------
        # Date validation
        # -----------------------------
        if self.from_date and self.to_date:
            if getdate(self.from_date) > getdate(self.to_date):
                frappe.throw("From Date cannot be greater than To Date")

        # -----------------------------
        # Overlapping lock check
        # -----------------------------
        existing = frappe.db.exists(
            "Attendance Lock",
            {
                "name": ["!=", self.name],
                # "docstatus": 1,
                "from_date": ["<=", self.to_date],
                "to_date": [">=", self.from_date],
            }
        )

        if existing:
            frappe.throw("Attendance already locked for this period")

    # -------------------------------------------------
    # MAIN FUNCTION
    # -------------------------------------------------
    @staticmethod
    def is_attendance_locked(date):

        date = getdate(date)

        locks = frappe.get_all(
            "Attendance Lock",
            # filters={"docstatus": 0},
            fields=["name", "from_date", "to_date"]
        )

        user_roles = set(frappe.get_roles())

        for lock in locks:

            from_date = getdate(lock.from_date)
            to_date = getdate(lock.to_date)

            # ✅ Check only inside lock period
            if not (from_date <= date <= to_date):
                continue

            # -----------------------------
            # Get roles from child table
            # -----------------------------
            allowed = frappe.get_all(
                "Attendance Lock Table",
                filters={"parent": lock.name},
                fields=["role"]
            )

            lock_roles = set(d.role for d in allowed if d.role)

            # -----------------------------
            # 🔥 HR MANAGER BYPASS LOGIC
            # -----------------------------

            # If HR Manager NOT in table → bypass
            if "HR Manager" in user_roles and "HR Manager" not in lock_roles:
                return False

            # -----------------------------
            # NORMAL LOGIC
            # -----------------------------

            # If no roles defined → lock for everyone
            if not lock_roles:
                return True

            # If user has role in table → BLOCK
            if user_roles.intersection(lock_roles):
                return True

            # Otherwise allow
            return False

        # No lock found → allow
        return False
