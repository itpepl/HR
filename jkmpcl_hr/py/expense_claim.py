# # import frappe
# # from frappe.utils import getdate, date_diff
# # from calendar import isleap


# # def validate(self, method):

# #     if not self.employee:
# #         return

# #     # =====================================
# #     # Employee Details
# #     # =====================================
# #     employee = frappe.get_doc("Employee", self.employee)

# #     # =====================================
# #     # Only Confirmed Employee Allowed
# #     # =====================================
# #     if employee.employment_type != "Confirmed":
# #         frappe.throw(
# #             "Only Confirmed employees can apply for LTA."
# #         )

# #     # =====================================
# #     # Final Confirmation Date
# #     # =====================================
# #     if not employee.final_confirmation_date:
# #         frappe.throw(
# #             "Employee Final Confirmation Date is missing."
# #         )

# #     confirmation_date = getdate(
# #         employee.final_confirmation_date
# #     )

# #     # =====================================
# #     # HR Settings
# #     # =====================================
# #     lta_limit = frappe.db.get_single_value(
# #         "HR Settings",
# #         "custom_lta_per_year"
# #     ) or 1

# #     # =====================================
# #     # Total LTA Amount
# #     # =====================================
# #     total_lta_amount = 0
# #     applicable_lta = 0

# #     # =====================================
# #     # Loop Expense Rows
# #     # =====================================
# #     for row in self.expenses:

# #         # =====================================
# #         # Only LTA Expense Type
# #         # =====================================
# #         if row.expense_type != "LTA":
# #             continue

# #         total_lta_amount += (
# #             row.amount or 0
# #         )

# #         if not row.expense_date:
# #             frappe.throw(
# #                 f"Expense Date is required in row {row.idx}"
# #             )

# #         expense_date = getdate(row.expense_date)

# #         # =====================================
# #         # Get Leave Applications
# #         # =====================================
# #         leave_applications = frappe.get_all(
# #             "Leave Application",
# #             filters={
# #                 "employee": self.employee,
# #                 "status": "Approved",
# #                 "docstatus": 1
# #             },
# #             fields=[
# #                 "name",
# #                 "from_date",
# #                 "to_date",
# #                 "leave_type"
# #             ]
# #         )

# #         # =====================================
# #         # Default Claim Year
# #         # =====================================
# #         claim_year = expense_date.year

# #         valid_leave_found = False

# #         # =====================================
# #         # Leave Validation
# #         # =====================================
# #         for leave in leave_applications:

# #             leave_from = getdate(leave.from_date)
# #             leave_to = getdate(leave.to_date)

# #             total_days = (
# #                 date_diff(leave_to, leave_from) + 1
# #             )

# #             # Minimum 4 days leave
# #             if total_days < 4:
# #                 continue

# #             # Only CL / PL
# #             if leave.leave_type not in [
# #                 "Casual Leave",
# #                 "Privilege Leave"
# #             ]:
# #                 continue

# #             # Claim within 30 days
# #             days_after_leave = date_diff(
# #                 expense_date,
# #                 leave_to
# #             )

# #             if days_after_leave > 30:
# #                 continue

# #             # =====================================
# #             # December Leave + January Claim
# #             # Consider Previous Year
# #             # =====================================
# #             if (
# #                 leave_to.month == 12
# #                 and expense_date.month == 1
# #                 and days_after_leave <= 30
# #             ):

# #                 claim_year = leave_to.year
# #                 valid_leave_found = True
# #                 break

# #             # =====================================
# #             # Same Year Normal Case
# #             # =====================================
# #             elif leave_to.year == expense_date.year:

# #                 valid_leave_found = True
# #                 break

# #         if not valid_leave_found:
# #             frappe.throw(
# #                 "Employee must take minimum 4 days CL/PL leave and apply within 30 days."
# #             )

# #         # =====================================
# #         # LTA Claim Count Validation
# #         # =====================================
# #         existing_claim_count = frappe.db.sql("""
# #             SELECT COUNT(DISTINCT ec.name)
# #             FROM `tabExpense Claim` ec
# #             INNER JOIN `tabExpense Claim Detail` ecd
# #                 ON ecd.parent = ec.name
# #             WHERE ec.employee = %s
# #             AND ecd.expense_type = 'LTA'
# #             AND YEAR(ecd.expense_date) = %s
# #             AND ec.docstatus != 2
# #             AND ec.name != %s
# #         """, (
# #             self.employee,
# #             claim_year,
# #             self.name
# #         ))[0][0]

# #         if existing_claim_count >= lta_limit:

# #             frappe.throw(
# #                 f"Only {lta_limit} LTA claims are allowed in year {claim_year}."
# #             )

# #         # =====================================
# #         # Total Days in Calendar Year
# #         # =====================================
# #         total_days_in_year = (
# #             366 if isleap(claim_year) else 365
# #         )

# #         start_of_year = getdate(
# #             f"{claim_year}-01-01"
# #         )

# #         end_of_year = getdate(
# #             f"{claim_year}-12-31"
# #         )

# #         # =====================================
# #         # Confirmed Days Calculation
# #         # =====================================
# #         confirmed_start = max(
# #             confirmation_date,
# #             start_of_year
# #         )

# #         confirmed_days = (
# #             date_diff(
# #                 end_of_year,
# #                 confirmed_start
# #             ) + 1
# #         )

# #         if confirmed_days < 0:
# #             confirmed_days = 0

# #         # =====================================
# #         # Salary Structure Assignment
# #         # =====================================
# #         salary_structure_assignment = frappe.db.get_value(
# #             "Salary Structure Assignment",
# #             {
# #                 "employee": self.employee
# #             },
# #             ["base"],
# #             as_dict=True,
# #             order_by="from_date desc"
# #         )

# #         if not salary_structure_assignment:
# #             frappe.throw(
# #                 "Salary Structure Assignment not found."
# #             )

# #         monthly_basic = (
# #             salary_structure_assignment.base or 0
# #         )

# #         if monthly_basic <= 0:
# #             frappe.throw(
# #                 "Monthly Basic Salary should be greater than 0."
# #             )

# #         # =====================================
# #         # LTA Formula
# #         # =====================================
# #         applicable_lta = (
# #             monthly_basic *
# #             (
# #                 confirmed_days /
# #                 total_days_in_year
# #             )
# #         )

# #         applicable_lta = round(applicable_lta)

# #     # =====================================
# #     # Final Total Amount Validation
# #     # =====================================
# #     if total_lta_amount > applicable_lta:

# #         frappe.throw(
# #             f"""
# #             <b>LTA Policy Validation</b><br><br>

# #             Maximum allowed LTA amount as per company policy is:
# #             <b>₹{applicable_lta}</b><br><br>

# #             Your current total LTA claim amount is:
# #             <b>₹{total_lta_amount}</b><br><br>

# #             LTA is calculated based on:
# #             <br><br>

# #             Monthly Basic Salary ×
# #             (Confirmed Days ÷ Total Days in Calendar Year)
# #             """
# #         )

# import frappe
# from frappe.utils import getdate, date_diff
# from calendar import isleap
# from datetime import timedelta


# def validate(self, method):

#     if not self.employee:
#         return

#     # =====================================
#     # Employee Details
#     # =====================================
#     employee = frappe.get_doc("Employee", self.employee)

#     if employee.employment_type != "Confirmed":
#         frappe.throw("Only Confirmed employees can apply for LTA.")
    

#     # =====================================
#     # Suspension Period Validation
#     # =====================================

#     if employee.status == "Suspended":
#         frappe.throw("Suspended employees are not allowed to apply for LTA.")

#     if employee.custom_suspended_from_date:

#         suspended_from = getdate(employee.custom_suspended_from_date)

#         # Suspension still active
#         if not employee.custom_suspended_to_date:

#             if expense_date >= suspended_from:
#                 frappe.throw(
#                     f"Employee is under suspension since {frappe.format(suspended_from)}. "
#                     f"LTA claim is not allowed until suspension is revoked."
#                 )

#         # Suspension period defined
#         else:

#             suspended_to = getdate(employee.custom_suspended_to_date)

#             if suspended_from <= expense_date <= suspended_to:
#                 frappe.throw(
#                     f"Employee was under suspension from "
#                     f"{frappe.format(suspended_from)} to "
#                     f"{frappe.format(suspended_to)}. "
#                     f"LTA claim cannot be applied during this period."
#                 )
    
#     if not employee.final_confirmation_date:
#         frappe.throw("Employee Final Confirmation Date is missing.")

#     confirmation_date = getdate(employee.final_confirmation_date)

#     # =====================================
#     # HR Settings
#     # =====================================
#     lta_limit = frappe.db.get_single_value(
#         "HR Settings",
#         "custom_lta_per_year"
#     )

#     total_lta_amount = 0
#     applicable_lta = 0

#     # =====================================
#     # Leave Applications (fetch once)
#     # =====================================
#     leave_applications = frappe.get_all(
#         "Leave Application",
#         filters={
#             "employee": self.employee,
#             "status": "Approved",
#             "docstatus": 1
#         },
#         fields=["name", "from_date", "to_date", "leave_type"]
#     )

#     # =====================================
#     # Loop Expense Rows
#     # =====================================
#     for row in self.expenses:

#         if row.expense_type != "LTA":
#             continue

#         total_lta_amount += (row.amount or 0)

#         if not row.expense_date:
#             frappe.throw(f"Expense Date is required in row {row.idx}")

#         expense_date = getdate(row.expense_date)
#         claim_year = expense_date.year

#         # =====================================
#         # LTA Claim Count Validation
#         # =====================================
#         existing_claim_count = frappe.db.sql("""
#             SELECT COUNT(DISTINCT ec.name)
#             FROM `tabExpense Claim` ec
#             INNER JOIN `tabExpense Claim Detail` ecd
#                 ON ecd.parent = ec.name
#             WHERE ec.employee = %s
#               AND ecd.expense_type = 'LTA'
#               AND YEAR(ecd.expense_date) = %s
#               AND ec.docstatus != 2
#               AND ec.name != %s
#         """, (self.employee, claim_year, self.name))[0][0]

#         if existing_claim_count >= lta_limit:
#             # frappe.throw(f"Only {lta_limit} LTA claims allowed in year {claim_year}.")
#             frappe.throw("Current Year LTA claim is already done")
#         # =====================================
#         # Leave + Holiday + Weekoff Continuous Check
#         # =====================================
#         continuous_dates = set()

#         for leave in leave_applications:

#             if leave.leave_type not in ["Casual Leave", "Privilege Leave"]:
#                 continue

#             leave_from = getdate(leave.from_date)
#             leave_to = getdate(leave.to_date)

#             # =====================================
#             # Consider only leave after confirmation
#             # =====================================
#             if leave_to < confirmation_date:
#                 continue

#             if leave_from < confirmation_date:
#                 leave_from = confirmation_date

#             days_after_leave = date_diff(expense_date, leave_to)

#             if days_after_leave > 30:
#                 continue

#             # December to January exception
#             if not (
#                 leave_to.month == 12
#                 and expense_date.month == 1
#                 and days_after_leave <= 30
#             ):
#                 if leave_to.year != expense_date.year:
#                     continue

#             current_date = leave_from

#             while current_date <= leave_to:
#                 continuous_dates.add(current_date)
#                 current_date += timedelta(days=1)

#         # Add Weekoff + Holidays
#         if continuous_dates:

#             min_date = min(continuous_dates)
#             max_date = max(continuous_dates)

#             holiday_list = employee.holiday_list
#             holiday_dates = set()

#             if holiday_list:
#                 holidays = frappe.get_all(
#                     "Holiday",
#                     filters={"parent": holiday_list},
#                     fields=["holiday_date"]
#                 )
#                 holiday_dates = {getdate(h.holiday_date) for h in holidays}

#             current_date = min_date

#             while current_date <= max_date:

#                 if current_date.weekday() in [5, 6]:
#                     continuous_dates.add(current_date)

#                 if current_date in holiday_dates:
#                     continuous_dates.add(current_date)

#                 current_date += timedelta(days=1)

#         sorted_dates = sorted(continuous_dates)

#         max_streak = 1
#         streak = 1

#         for i in range(1, len(sorted_dates)):
#             if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
#                 streak += 1
#                 max_streak = max(max_streak, streak)
#             else:
#                 streak = 1

#         if max_streak < 4:
#             frappe.throw(
#                 "Minimum 4 continuous days (Leave + Holiday + Weekoff) required for LTA."
#             )

#         # =====================================
#         # Salary Structure (IMPORTANT FIX)
#         # Get based on expense_date (NOT latest)
#         # =====================================
#         salary = frappe.db.sql("""
#             SELECT base
#             FROM `tabSalary Structure Assignment`
#             WHERE employee = %s
#               AND docstatus = 1
#               AND from_date <= %s
#             ORDER BY from_date DESC
#             LIMIT 1
#         """, (self.employee, expense_date), as_dict=True)

#         if not salary:
#             frappe.throw(
#                 "Salary Structure Assignment not found for expense date."
#             )

#         monthly_basic = salary[0].base or 0

#         if monthly_basic <= 0:
#             frappe.throw("Monthly Basic Salary must be greater than 0.")

#         # =====================================
#         # LTA Calculation
#         # =====================================
#         total_days_in_year = 366 if isleap(claim_year) else 365

#         start_of_year = getdate(f"{claim_year}-01-01")
#         end_of_year = getdate(f"{claim_year}-12-31")

#         confirmed_start = max(confirmation_date, start_of_year)

#         confirmed_days = date_diff(end_of_year, confirmed_start) + 1

#         if confirmed_days < 0:
#             confirmed_days = 0

#         applicable_lta = round(
#             monthly_basic * (confirmed_days / total_days_in_year)
#         )

#     # =====================================
#     # Final Validation
#     # =====================================
#     if total_lta_amount > applicable_lta:
#         frappe.throw(f"""
#             <b>LTA Policy Validation</b><br><br>

#             Allowed LTA: <b>₹{applicable_lta}</b><br>
#             Claimed LTA: <b>₹{total_lta_amount}</b><br><br>

#             Formula:<br>
#             Monthly Basic × (Confirmed Days ÷ Total Year Days)
#         """)

import frappe
from frappe.utils import getdate, date_diff
from calendar import isleap
from datetime import timedelta
from frappe.utils import getdate, date_diff, cint


def validate(self, method):

    if not self.employee:
        return

    # =====================================
    # Employee Details
    # =====================================
    employee = frappe.get_doc("Employee", self.employee)

    # =====================================
    # Only Confirmed Employee Allowed
    # =====================================
    if employee.employment_type != "Confirmed":
        frappe.throw(
            "Only Confirmed employees can apply for LTA."
        )

    # =====================================
    # Employee Suspension Status
    # =====================================
    if employee.status == "Suspended":
        frappe.throw(
            "Suspended employees are not allowed to apply for LTA."
        )

    # =====================================
    # Final Confirmation Date
    # =====================================
    if not employee.final_confirmation_date:
        frappe.throw(
            "Employee Final Confirmation Date is missing."
        )

    confirmation_date = getdate(
        employee.final_confirmation_date
    )

    # =====================================
    # HR Settings
    # =====================================
    lta_limit = (
        frappe.db.get_single_value(
            "HR Settings",
            "custom_lta_per_year"
        )
    )

    total_lta_amount = 0
    applicable_lta = 0

    # =====================================
    # Leave Applications
    # =====================================
    leave_applications = frappe.get_all(
        "Leave Application",
        filters={
            "employee": self.employee,
            "status": "Approved",
            "docstatus": 1
        },
        fields=[
            "name",
            "from_date",
            "to_date",
            "leave_type"
        ],
        order_by="to_date desc"
    )

    # =====================================
    # Loop Expense Rows
    # =====================================
    for row in self.expenses:

        if row.expense_type != "LTA":
            continue

        total_lta_amount += (row.amount or 0)

        if not row.expense_date:
            frappe.throw(
                f"Expense Date is required in row {row.idx}"
            )

        expense_date = getdate(row.expense_date)

        # =====================================
        # Suspension Period Validation
        # =====================================
        if employee.custom_suspended_from_date:

            suspended_from = getdate(
                employee.custom_suspended_from_date
            )

            if not employee.custom_suspended_to_date:

                if expense_date >= suspended_from:
                    frappe.throw(
                        f"Employee is under suspension since "
                        f"{frappe.format(suspended_from)}. "
                        f"LTA claim is not allowed until suspension is revoked."
                    )

            else:

                suspended_to = getdate(
                    employee.custom_suspended_to_date
                )

                if suspended_from <= expense_date <= suspended_to:
                    frappe.throw(
                        f"Employee was under suspension from "
                        f"{frappe.format(suspended_from)} to "
                        f"{frappe.format(suspended_to)}. "
                        f"LTA claim cannot be applied during this period."
                    )

        
        # =====================================
        # Leave Validation
        # =====================================
        valid_leave_found = False
        continuous_dates = set()
        qualifying_leave_to = None

        for leave in leave_applications:

            if leave.leave_type not in [
                "Casual Leave",
                "Privilege Leave"
            ]:
                continue

            leave_from = getdate(leave.from_date)
            leave_to = getdate(leave.to_date)

            # =====================================
            # LTA Cannot Be Claimed Before Leave Completion
            # =====================================
            if expense_date < leave_to:
                continue

            # Ignore leaves before confirmation
            if leave_to < confirmation_date:
                continue

            if leave_from < confirmation_date:
                leave_from = confirmation_date

            total_days = (
                date_diff(leave_to, leave_from) + 1
            )

            if total_days < 4:
                continue

            # =====================================
            # Claim Within 30 Days
            # =====================================
            days_after_leave = date_diff(
                expense_date,
                leave_to
            )

            if days_after_leave < 0:
                continue

            if days_after_leave > 30:
                continue

            valid_leave_found = True
            qualifying_leave_to = leave_to

            current_date = leave_from

            while current_date <= leave_to:
                continuous_dates.add(current_date)
                current_date += timedelta(days=1)

            break

        if not valid_leave_found:
            frappe.throw(
                "Employee must complete minimum 4 continuous days CL/PL leave and apply for LTA only after leave completion and within 30 days from leave end date."
            )
        # =====================================
        # LTA Entitlement Year
        # =====================================
        claim_year = qualifying_leave_to.year

        # =====================================
        # Add Weekoff + HolidaysWhat is the value of lta_limit?
        # =====================================
        if continuous_dates:

            min_date = min(continuous_dates)
            max_date = max(continuous_dates)

            holiday_dates = set()

            if employee.holiday_list:

                holidays = frappe.get_all(
                    "Holiday",
                    filters={
                        "parent": employee.holiday_list
                    },
                    fields=["holiday_date"]
                )

                holiday_dates = {
                    getdate(h.holiday_date)
                    for h in holidays
                }

            current_date = min_date

            while current_date <= max_date:

                # Saturday / Sunday
                if current_date.weekday() in [5, 6]:
                    continuous_dates.add(current_date)

                if current_date in holiday_dates:
                    continuous_dates.add(current_date)

                current_date += timedelta(days=1)

        sorted_dates = sorted(continuous_dates)

        max_streak = 1
        streak = 1

        for i in range(1, len(sorted_dates)):

            if (
                sorted_dates[i]
                - sorted_dates[i - 1]
            ).days == 1:

                streak += 1
                max_streak = max(
                    max_streak,
                    streak
                )

            else:
                streak = 1

        if max_streak < 4:
            frappe.throw(
                "Minimum 4 continuous days (Leave + Holiday + Weekoff) required for LTA."
            )

        # =====================================
        # LTA Claim Count Validation
        # =====================================

        existing_claim_count = 0

        existing_lta_claims = frappe.db.sql("""
            SELECT
                ec.name,
                ecd.expense_date
            FROM `tabExpense Claim` ec
            INNER JOIN `tabExpense Claim Detail` ecd
                ON ecd.parent = ec.name
            WHERE ec.employee = %s
            AND ecd.expense_type = 'LTA'
            AND ec.docstatus != 2
            AND ec.name != %s
        """, (
            self.employee,
            self.name
        ), as_dict=True)

        for claim in existing_lta_claims:

            existing_expense_date = getdate(claim.expense_date)

            existing_claim_year = existing_expense_date.year

            matching_leave = frappe.db.sql("""
                SELECT to_date
                FROM `tabLeave Application`
                WHERE employee = %s
                AND status = 'Approved'
                AND docstatus = 1
                AND to_date <= %s
                ORDER BY to_date DESC
                LIMIT 1
            """, (
                self.employee,
                existing_expense_date
            ), as_dict=True)

            if matching_leave:
                existing_claim_year = getdate(
                    matching_leave[0].to_date
                ).year

            if existing_claim_year == claim_year:
                existing_claim_count += 1

        if existing_claim_count >= cint(lta_limit):
            frappe.msgprint(
                f"""
                Claim Year : {claim_year}
                Existing Count : {existing_claim_count}
                """
            )

            frappe.throw(
                f"Only {lta_limit} LTA claim(s) are allowed for year {claim_year}."
            )

        # =====================================
        # Salary Structure Assignment
        # Based on Qualifying Leave End Date
        # =====================================
        salary = frappe.db.sql("""
            SELECT base
            FROM `tabSalary Structure Assignment`
            WHERE employee = %s
            AND docstatus = 1
            AND from_date <= %s
            ORDER BY from_date DESC
            LIMIT 1
        """, (
            self.employee,
            qualifying_leave_to
        ), as_dict=True)
        if not salary:
            frappe.throw(
                "Salary Structure Assignment not found for qualifying leave date."
            )

        monthly_basic = salary[0].base or 0

        if monthly_basic <= 0:
            frappe.throw(
                "Monthly Basic Salary must be greater than 0."
            )

        # =====================================
        # LTA Calculation
        # =====================================
        total_days_in_year = (
            366 if isleap(claim_year) else 365
        )

        start_of_year = getdate(
            f"{claim_year}-01-01"
        )

        end_of_year = getdate(
            f"{claim_year}-12-31"
        )

        confirmed_start = max(
            confirmation_date,
            start_of_year
        )

        confirmed_days = (
            date_diff(
                end_of_year,
                confirmed_start
            ) + 1
        )

        if confirmed_days < 0:
            confirmed_days = 0

        applicable_lta = round(
            monthly_basic *
            (
                confirmed_days /
                total_days_in_year
            )
        )

    # =====================================
    # Final Amount Validation
    # =====================================
    if total_lta_amount > applicable_lta:

        frappe.throw(
            f"""
            <b>LTA Policy Validation</b><br><br>

            Maximum allowed LTA amount as per company policy:
            <b>₹{applicable_lta}</b><br><br>

            Your current LTA claim amount:
            <b>₹{total_lta_amount}</b><br><br>

            """
        )