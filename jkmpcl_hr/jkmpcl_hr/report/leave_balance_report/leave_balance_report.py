# import frappe
# from frappe.utils import flt, getdate, today
# import calendar


# def execute(filters=None):

#     filters = frappe._dict(filters or {})

#     from_date, to_date = get_date_range(filters)

#     employees = get_employees(filters)

#     data = []

#     leave_types = get_leave_types(filters)

#     fy_start = getdate(f"{from_date.year}-04-01")

#     if from_date.month < 4:
#         fy_start = getdate(f"{from_date.year - 1}-04-01")

#     ledger_entries = get_leave_ledger_entries(fy_start, to_date)

#     for emp in employees:

#         row = {
#             "employee": emp.name,
#             "employee_name": emp.employee_name,
#             "branch": emp.branch,
#             "designation": emp.designation,
#         }

#         for lt in leave_types:

#             prefix = get_prefix(lt)

#             opening = 0
#             accrued = 0
#             availed_till_last_month = 0
#             availed = 0
#             deduction = 0

#             for entry in ledger_entries:

#                 if entry.employee != emp.name:
#                     continue

#                 if entry.leave_type != lt:
#                     continue

#                 leaves = flt(entry.leaves)

#                 # Opening balance
#                 if fy_start <= entry.from_date < from_date:
#                     # Casual Leave lapses every financial year
#                     if lt == "Casual Leave" and entry.from_date < fy_start:
#                         continue
                    
#                     opening += leaves

#                     if entry.transaction_type == "Leave Application":
#                         availed_till_last_month += abs(leaves)
#                     # opening += leaves
#                     # availed_till_last_month += abs(leaves) if entry.transaction_type == "Leave Application" else 0

#                 # Inside period
#                 if fy_start <= entry.from_date <= to_date and entry.from_date >= from_date:

#                     if entry.transaction_type == "Leave Allocation" and not entry.custom_is_penalty:
#                         accrued += leaves

#                     elif entry.transaction_type == "Leave Application":
#                         availed += abs(leaves)

#                     elif entry.custom_is_penalty:
#                         deduction += abs(leaves)

#             # row[f"{prefix}_opening"] = opening
#             # row[f"{prefix}_accrued"] = accrued

#             # ✅ For April month — override opening and accrued from
#             # Leave Allocation document directly via Leave Ledger Entry
#             is_april = (from_date.month == 4)
#             if is_april and lt in ("Sick Leave", "Privilege Leave"):
#                 # Contractual and Probation employees accrue on 30-Apr
#                 # Confirmed and others accrue on 01-Apr
#                 is_monthly_accrual = emp.get("employment_type") in (
#                     "Contractual", "Probation"
#                 )
#                 april_first = from_date  # always 01-04-yyyy
#                 april_last = getdate(f"{from_date.year}-04-30")

#                 accrual_date = april_last if is_monthly_accrual else april_first

#                 april_data = get_april_allocation_data(
#                     emp.name, lt, april_first, accrual_date
#                 )
#                 opening = april_data["opening"]
#                 accrued = april_data["accrued"]

#             row[f"{prefix}_opening"] = opening
#             row[f"{prefix}_accrued"] = accrued
#             row[f"{prefix}_availed_last_month"] = availed_till_last_month
#             row[f"{prefix}_availed_current_month"] = availed
#             row[f"{prefix}_deduction"] = deduction
#             row[f"{prefix}_total_availed"] = (
#                 row.get(f"{prefix}_availed_last_month", 0) + row.get(f"{prefix}_availed_current_month", 0) + row.get(f"{prefix}_deduction", 0)
#             )
#             row[f"{prefix}_closing"] = (
#                 row.get(f"{prefix}_opening", 0) + row.get(f"{prefix}_accrued", 0) - row.get(f"{prefix}_availed_current_month", 0) - row.get(f"{prefix}_deduction", 0)
#             )

#         data.append(row)

#     columns = get_columns(leave_types)

#     return columns, data


# # -------------------------------------------------------


# def get_columns(leave_types):

#     columns = [

#         {
#             "label": "Employee",
#             "fieldname": "employee",
#             "fieldtype": "Link",
#             "options": "Employee",
#             "width": 120,
#         },

#         {
#             "label": "Employee Name",
#             "fieldname": "employee_name",
#             "fieldtype": "Data",
#             "width": 150,
#         },

#         {
#             "label": "Branch",
#             "fieldname": "branch",
#             "fieldtype": "Data",
#             "width": 120,
#         },

#         {
#             "label": "Designation",
#             "fieldname": "designation",
#             "fieldtype": "Data",
#             "width": 140,
#         },
#     ]

#     for lt in leave_types:

#         prefix = get_prefix(lt)

#         columns.extend(
#             [
#                 {
#                     "label": f"{prefix.upper()} Monthly Opening",
#                     "fieldname": f"{prefix}_opening",
#                     "fieldtype": "Float",
#                     "width": 120,
#                 },
#                 {
#                     "label": f"{prefix.upper()} Monthly Accrued",
#                     "fieldname": f"{prefix}_accrued",
#                     "fieldtype": "Float",
#                     "width": 120,
#                 },
#                 {
#                     "label": f"{prefix.upper()} Availed Till Last Month",
#                     "fieldname": f"{prefix}_availed_last_month",
#                     "fieldtype": "Float",
#                     "width": 120,
#                 },
#                 {
#                     "label": f"{prefix.upper()} Availed Current Month",
#                     "fieldname": f"{prefix}_availed_current_month",
#                     "fieldtype": "Float",
#                     "width": 120,
#                 },
#                 {
#                     "label": f"{prefix.upper()} Deduction",
#                     "fieldname": f"{prefix}_deduction",
#                     "fieldtype": "Float",
#                     "width": 120,
#                 },
#                 {
#                     "label": f"{prefix.upper()} Total Availed",
#                     "fieldname": f"{prefix}_total_availed",
#                     "fieldtype": "Float",
#                     "width": 120,
#                 },
#                 {
#                     "label": f"{prefix.upper()} Closing",
#                     "fieldname": f"{prefix}_closing",
#                     "fieldtype": "Float",
#                     "width": 120,
#                 },
#             ]
#         )

#     return columns


# # -------------------------------------------------------


# def get_date_range(filters):

#     # Validate filters
#     if not filters.get("month"):
#         frappe.throw("Please select Month")

#     if not filters.get("year"):
#         frappe.throw("Please select Year")

#     if not filters.get("as_on_date"):
#         frappe.throw("As On Date is missing")

#     # Month mapping
#     month_map = {
#         "January": 1,
#         "February": 2,
#         "March": 3,
#         "April": 4,
#         "May": 5,
#         "June": 6,
#         "July": 7,
#         "August": 8,
#         "September": 9,
#         "October": 10,
#         "November": 11,
#         "December": 12,
#     }

#     month = month_map.get(filters.month)
#     year = int(filters.year)

#     # First date of selected month
#     from_date = f"{year}-{month:02d}-01"

#     # As On Date comes from JS logic
#     to_date = filters.as_on_date

#     return getdate(from_date), getdate(to_date)


# # -------------------------------------------------------


# def get_employees(filters):

#     conditions = " WHERE status = 'Active' "

#     if filters.branch:
#         conditions += " AND branch = %(branch)s"

#     if filters.employee:
#         conditions += " AND name = %(employee)s"

#     if filters.employment_type:
#         conditions += " AND employment_type = %(employment_type)s"

#     employees = frappe.db.sql(
#         f"""
#         SELECT
#             name,
#             employee_name,
#             branch,
#             designation,
#             employment_type
#         FROM `tabEmployee`
#         {conditions}
#     """,
#         filters,
#         as_dict=1,
#     )

#     return employees


# # -------------------------------------------------------


# def get_leave_ledger_entries(fy_start, to_date):

#     return frappe.db.sql(
#         """
#         SELECT
#             employee,
#             leave_type,
#             transaction_type,
#             leaves,
#             from_date,
#             custom_is_penalty
#         FROM `tabLeave Ledger Entry`
#         WHERE from_date BETWEEN %s AND %s
#         """,
#         (fy_start, to_date),
#         as_dict=1,
#     )


# # -------------------------------------------------------


# def get_leave_types(filters):

#     if filters.leave_type:
#         return [filters.leave_type]

#     return ["Casual Leave", "Privilege Leave", "Sick Leave"]


# # -------------------------------------------------------


# def get_prefix(leave_type):

#     mapping = {
#         "Casual Leave": "cl",
#         "Privilege Leave": "pl",
#         "Sick Leave": "sl",
#     }

#     return mapping.get(leave_type, leave_type.lower())


# # -------------------------------------------------------


# def get_april_allocation_data(employee: str, leave_type: str, april_date, accrual_date=None) -> dict:
#     """
#     For April month only — fetch opening balance and new leaves allocated
#     directly from the Leave Allocation document linked via Leave Ledger Entry.
#     - april_date   → used to fetch opening balance (01-04-yyyy)
#     - accrual_date → used to fetch accrued leaves
#                      01-04-yyyy for Confirmed (from Leave Allocation doc)
#                      30-04-yyyy for Contractual/Probation (from Leave Ledger Entry leaves field directly)
#     Returns {"opening": 0, "accrued": 0}
#     """
#     if accrual_date is None:
#         accrual_date = april_date

#     # ── Opening balance → always from 01-Apr ledger entry ──────────
#     opening_ledger = frappe.db.get_value(
#         "Leave Ledger Entry",
#         {
#             "employee": employee,
#             "leave_type": leave_type,
#             "from_date": april_date,
#             "transaction_type": "Leave Allocation",
#             "custom_is_penalty": 0,
#             "docstatus": 1,
#         },
#         ["transaction_name"],
#         as_dict=True,
#     )

#     opening = 0
#     if opening_ledger and opening_ledger.transaction_name:
#         allocation = frappe.db.get_value(
#             "Leave Allocation",
#             {
#                 "name": opening_ledger.transaction_name,
#                 "docstatus": 1,
#             },
#             ["custom_opening_balance"],
#             as_dict=True,
#         )
#         if allocation:
#             opening = flt(allocation.custom_opening_balance or 0)

#     # ── Accrued → read directly from the Leave Ledger Entry leaves field
#     # For Contractual/Probation the accrual entry on 30-Apr updates the
#     # existing allocation — so new_leaves_allocated on the allocation doc
#     # is not reliable. The actual accrued amount is in the ledger entry itself.
#     accrual_ledger = frappe.db.get_value(
#         "Leave Ledger Entry",
#         {
#             "employee": employee,
#             "leave_type": leave_type,
#             "from_date": accrual_date,
#             "transaction_type": "Leave Allocation",
#             "custom_is_penalty": 0,
#             "docstatus": 1,
#         },
#         ["transaction_name", "leaves"],
#         as_dict=True,
#     )

#     accrued = 0
#     if accrual_ledger:
#         # ── Confirmed employees (accrual_date == april_date == 01-Apr):
#         # fetch new_leaves_allocated from the Leave Allocation document
#         if accrual_date == april_date:
#             if accrual_ledger.transaction_name:
#                 allocation = frappe.db.get_value(
#                     "Leave Allocation",
#                     {
#                         "name": accrual_ledger.transaction_name,
#                         "docstatus": 1,
#                     },
#                     ["new_leaves_allocated"],
#                     as_dict=True,
#                 )
#                 if allocation:
#                     accrued = flt(allocation.new_leaves_allocated or 0)

#         # ── Contractual/Probation (accrual_date == 30-Apr):
#         # new_leaves_allocated on the allocation is unreliable since
#         # monthly accrual only updates total_leaves_allocated.
#         # Read the actual accrued amount directly from the ledger entry.
#         else:
#             accrued = flt(accrual_ledger.leaves or 0)

#     return {"opening": opening, "accrued": accrued}


















# -------------------------------- UPDATED CODES IN THIS FILE RECENTLY ---------------------------------

# import frappe
# from frappe.utils import flt, getdate, today
# import calendar


# def execute(filters=None):

#     filters = frappe._dict(filters or {})

#     from_date, to_date = get_date_range(filters)

#     employees = get_employees(filters)

#     data = []

#     leave_types = get_leave_types(filters)

#     fy_start = getdate(f"{from_date.year}-04-01")
#     if from_date.month < 4:
#         fy_start = getdate(f"{from_date.year - 1}-04-01")

#     SYSTEM_START_DATE = getdate("2025-11-30")

#     ledger_entries = get_leave_ledger_entries(fy_start, to_date)

#     # Also fetch entries from beginning of time up to system start date
#     # for yearly opening calculation in first FY
#     ledger_entries_for_opening = get_leave_ledger_entries_for_opening(
#         fy_start, SYSTEM_START_DATE
#     )

#     for emp in employees:

#         row = {
#             "employee": emp.name,
#             "employee_name": emp.employee_name,
#             "branch": emp.branch,
#             "designation": emp.designation,
#         }

#         for lt in leave_types:

#             prefix = get_prefix(lt)

#             opening = 0
#             accrued = 0
#             availed_till_last_month = 0
#             availed = 0
#             deduction = 0

#             for entry in ledger_entries:

#                 if entry.employee != emp.name:
#                     continue

#                 if entry.leave_type != lt:
#                     continue

#                 leaves = flt(entry.leaves)

#                 # Opening balance
#                 if fy_start <= entry.from_date < from_date:
#                     if lt == "Casual Leave" and entry.from_date < fy_start:
#                         continue
#                     opening += leaves
#                     if entry.transaction_type == "Leave Application":
#                         availed_till_last_month += abs(leaves)

#                 # Inside period
#                 if fy_start <= entry.from_date <= to_date and entry.from_date >= from_date:
#                     if entry.transaction_type == "Leave Allocation" and not entry.custom_is_penalty:
#                         accrued += leaves
#                     elif entry.transaction_type == "Leave Application":
#                         availed += abs(leaves)
#                     elif entry.custom_is_penalty:
#                         deduction += abs(leaves)

#             is_april = (from_date.month == 4)
#             if is_april and lt in ("Sick Leave", "Privilege Leave"):
#                 is_monthly_accrual = emp.get("employment_type") in ("Contractual", "Probation")
#                 april_first = from_date
#                 april_last = getdate(f"{from_date.year}-04-30")
#                 accrual_date = april_last if is_monthly_accrual else april_first
#                 april_data = get_april_allocation_data(emp.name, lt, april_first, accrual_date)
#                 opening = april_data["opening"]
#                 accrued = april_data["accrued"]

#             row[f"{prefix}_opening"] = opening
#             row[f"{prefix}_accrued"] = accrued
#             row[f"{prefix}_availed_last_month"] = availed_till_last_month
#             row[f"{prefix}_availed_current_month"] = availed
#             row[f"{prefix}_deduction"] = deduction
#             row[f"{prefix}_total_availed"] = (
#                 availed_till_last_month + availed + deduction
#             )
#             row[f"{prefix}_closing"] = opening + accrued - availed - deduction

#             # ── Yearly Opening ───────────────────────────────────────
#             # First FY (fy_start <= SYSTEM_START_DATE):
#             #   → sum of ledger entries exactly on 30-11-2025
#             # Next FY (fy_start > SYSTEM_START_DATE):
#             #   → sum of Leave Allocation entries exactly on 01-Apr-yyyy
#             row[f"{prefix}_yearly_opening"] = get_yearly_opening(
#                 emp.name, lt, fy_start, SYSTEM_START_DATE,
#                 ledger_entries_for_opening, ledger_entries
#             )

#             # ── Yearly Accrual ───────────────────────────────────────
#             # Sum of all Leave Allocation (non-penalty) entries
#             # from day after fy_start up to to_date
#             row[f"{prefix}_yearly_accrual"] = get_yearly_accrual(
#                 emp.name, lt, fy_start, SYSTEM_START_DATE, to_date, ledger_entries
#             )

#         data.append(row)

#     columns = get_columns(leave_types)

#     return columns, data


# # -------------------------------------------------------


# def get_columns(leave_types):

#     columns = [
#         {
#             "label": "Employee",
#             "fieldname": "employee",
#             "fieldtype": "Link",
#             "options": "Employee",
#             "width": 120,
#         },
#         {
#             "label": "Employee Name",
#             "fieldname": "employee_name",
#             "fieldtype": "Data",
#             "width": 150,
#         },
#         {
#             "label": "Branch",
#             "fieldname": "branch",
#             "fieldtype": "Data",
#             "width": 120,
#         },
#         {
#             "label": "Designation",
#             "fieldname": "designation",
#             "fieldtype": "Data",
#             "width": 140,
#         },
#     ]

#     for lt in leave_types:

#         prefix = get_prefix(lt)

#         columns.extend([
#             {
#                 "label": f"{prefix.upper()} Yearly Opening",
#                 "fieldname": f"{prefix}_yearly_opening",
#                 "fieldtype": "Float",
#                 "width": 140,
#             },
#             {
#                 "label": f"{prefix.upper()} Yearly Accrual",
#                 "fieldname": f"{prefix}_yearly_accrual",
#                 "fieldtype": "Float",
#                 "width": 140,
#             },
#             {
#                 "label": f"{prefix.upper()} Monthly Opening",
#                 "fieldname": f"{prefix}_opening",
#                 "fieldtype": "Float",
#                 "width": 120,
#             },
#             {
#                 "label": f"{prefix.upper()} Monthly Accrued",
#                 "fieldname": f"{prefix}_accrued",
#                 "fieldtype": "Float",
#                 "width": 120,
#             },
#             {
#                 "label": f"{prefix.upper()} Availed Till Last Month",
#                 "fieldname": f"{prefix}_availed_last_month",
#                 "fieldtype": "Float",
#                 "width": 120,
#             },
#             {
#                 "label": f"{prefix.upper()} Availed Current Month",
#                 "fieldname": f"{prefix}_availed_current_month",
#                 "fieldtype": "Float",
#                 "width": 120,
#             },
#             {
#                 "label": f"{prefix.upper()} Deduction",
#                 "fieldname": f"{prefix}_deduction",
#                 "fieldtype": "Float",
#                 "width": 120,
#             },
#             {
#                 "label": f"{prefix.upper()} Total Availed",
#                 "fieldname": f"{prefix}_total_availed",
#                 "fieldtype": "Float",
#                 "width": 120,
#             },
#             {
#                 "label": f"{prefix.upper()} Closing",
#                 "fieldname": f"{prefix}_closing",
#                 "fieldtype": "Float",
#                 "width": 120,
#             },
#         ])

#     return columns


# # -------------------------------------------------------


# def get_date_range(filters):

#     if not filters.get("month"):
#         frappe.throw("Please select Month")

#     if not filters.get("year"):
#         frappe.throw("Please select Year")

#     if not filters.get("as_on_date"):
#         frappe.throw("As On Date is missing")

#     month_map = {
#         "January": 1,
#         "February": 2,
#         "March": 3,
#         "April": 4,
#         "May": 5,
#         "June": 6,
#         "July": 7,
#         "August": 8,
#         "September": 9,
#         "October": 10,
#         "November": 11,
#         "December": 12,
#     }

#     month = month_map.get(filters.month)
#     year = int(filters.year)

#     from_date = f"{year}-{month:02d}-01"
#     to_date = filters.as_on_date

#     return getdate(from_date), getdate(to_date)


# # -------------------------------------------------------


# def get_employees(filters):

#     conditions = " WHERE status = 'Active' "

#     if filters.branch:
#         conditions += " AND branch = %(branch)s"

#     if filters.employee:
#         conditions += " AND name = %(employee)s"

#     if filters.employment_type:
#         conditions += " AND employment_type = %(employment_type)s"

#     employees = frappe.db.sql(
#         f"""
#         SELECT
#             name,
#             employee_name,
#             branch,
#             designation,
#             employment_type
#         FROM `tabEmployee`
#         {conditions}
#     """,
#         filters,
#         as_dict=1,
#     )

#     return employees


# # -------------------------------------------------------


# def get_leave_ledger_entries(fy_start, to_date):

#     return frappe.db.sql(
#         """
#         SELECT
#             employee,
#             leave_type,
#             transaction_type,
#             leaves,
#             from_date,
#             custom_is_penalty
#         FROM `tabLeave Ledger Entry`
#         WHERE from_date BETWEEN %s AND %s
#         AND docstatus = 1
#         """,
#         (fy_start, to_date),
#         as_dict=1,
#     )


# def get_leave_ledger_entries_for_opening(fy_start, system_start_date):
#     """
#     Fetch ledger entries exactly on system_start_date (30-11-2025)
#     for first FY yearly opening calculation.
#     Also fetches entries on fy_start for next FY scenario.
#     We fetch both dates in one query for efficiency.
#     """
#     return frappe.db.sql(
#         """
#         SELECT
#             employee,
#             leave_type,
#             transaction_type,
#             leaves,
#             from_date,
#             custom_is_penalty
#         FROM `tabLeave Ledger Entry`
#         WHERE from_date IN (%s, %s)
#         AND docstatus = 1
#         """,
#         (system_start_date, fy_start),
#         as_dict=1,
#     )


# # -------------------------------------------------------


# def get_leave_types(filters):

#     if filters.leave_type:
#         return [filters.leave_type]

#     return ["Casual Leave", "Privilege Leave", "Sick Leave"]


# # -------------------------------------------------------


# def get_prefix(leave_type):

#     mapping = {
#         "Casual Leave": "cl",
#         "Privilege Leave": "pl",
#         "Sick Leave": "sl",
#     }

#     return mapping.get(leave_type, leave_type.lower())


# # -------------------------------------------------------


# def get_yearly_opening(employee, leave_type, fy_start, system_start_date,
#                        ledger_entries_for_opening, ledger_entries):
#     """
#     Returns yearly opening balance for a leave type.

#     First FY (fy_start <= system_start_date, i.e. Apr 2025 - Mar 2026):
#         → Sum of Leave Allocation ledger entries whose from_date
#           is exactly 30-11-2025 (system start date).
#           These are the opening balance entries posted when the
#           system went live.

#     Next FY (fy_start > system_start_date, i.e. Apr 2026 onwards):
#         → Sum of Leave Allocation ledger entries whose from_date
#           is exactly 01-Apr-yyyy (fy_start).
#           These are the carry-forward/new allocation entries
#           posted at the start of each financial year.
#     """
#     if fy_start <= system_start_date:
#         # First FY — opening snapshot on system go-live date (30-11-2025)
#         opening = 0.0
#         for entry in ledger_entries_for_opening:
#             if entry.employee != employee:
#                 continue
#             if entry.leave_type != leave_type:
#                 continue
#             if entry.from_date != system_start_date:
#                 continue
#             if entry.transaction_type != "Leave Allocation":
#                 continue
#             if entry.custom_is_penalty:
#                 continue
#             opening += flt(entry.leaves)
#         return opening

#     else:
#         # Next FY — opening is allocation posted exactly on 01-Apr-yyyy
#         opening = 0.0
#         for entry in ledger_entries_for_opening:
#             if entry.employee != employee:
#                 continue
#             if entry.leave_type != leave_type:
#                 continue
#             if entry.from_date != fy_start:
#                 continue
#             if entry.transaction_type != "Leave Allocation":
#                 continue
#             if entry.custom_is_penalty:
#                 continue
#             opening += flt(entry.leaves)
#         return opening


# # -------------------------------------------------------


# def get_yearly_accrual(employee, leave_type, fy_start, system_start_date, to_date, ledger_entries):
#     """
#     Returns total leaves accrued after the opening snapshot date up to to_date.

#     First FY (fy_start <= system_start_date):
#         → Opening was taken on 30-11-2025
#         → So accrual starts AFTER 30-11-2025 (i.e. from_date > 30-11-2025)
#         → Excludes fy_start (01-04-2025) and system_start_date (30-11-2025) both

#     Next FY (fy_start > system_start_date):
#         → Opening was taken on 01-Apr-yyyy
#         → So accrual starts AFTER 01-Apr-yyyy (i.e. from_date > fy_start)
#         → Excludes fy_start (01-Apr-yyyy) only
#     """
#     # Determine the cutoff — entries ON or BEFORE this date are excluded
#     # because they belong to yearly_opening
#     if fy_start <= system_start_date:
#         cutoff = system_start_date   # 30-11-2025 for first FY
#     else:
#         cutoff = fy_start            # 01-Apr-yyyy for next FY

#     accrual = 0.0
#     for entry in ledger_entries:
#         if entry.employee != employee:
#             continue
#         if entry.leave_type != leave_type:
#             continue
#         if entry.transaction_type != "Leave Allocation":
#             continue
#         if entry.custom_is_penalty:
#             continue
#         # Only entries STRICTLY AFTER the cutoff date
#         if entry.from_date <= cutoff:
#             continue
#         if entry.from_date > to_date:
#             continue
#         accrual += flt(entry.leaves)
#     return accrual

# # -------------------------------------------------------


# def get_april_allocation_data(employee: str, leave_type: str, april_date, accrual_date=None) -> dict:
#     """
#     For April month only — fetch opening balance and new leaves allocated
#     directly from the Leave Allocation document linked via Leave Ledger Entry.
#     - april_date   → used to fetch opening balance (01-04-yyyy)
#     - accrual_date → used to fetch accrued leaves
#                      01-04-yyyy for Confirmed (from Leave Allocation doc)
#                      30-04-yyyy for Contractual/Probation (from Leave Ledger Entry leaves field directly)
#     Returns {"opening": 0, "accrued": 0}
#     """
#     if accrual_date is None:
#         accrual_date = april_date

#     opening_ledger = frappe.db.get_value(
#         "Leave Ledger Entry",
#         {
#             "employee": employee,
#             "leave_type": leave_type,
#             "from_date": april_date,
#             "transaction_type": "Leave Allocation",
#             "custom_is_penalty": 0,
#             "docstatus": 1,
#         },
#         ["transaction_name"],
#         as_dict=True,
#     )

#     opening = 0
#     if opening_ledger and opening_ledger.transaction_name:
#         allocation = frappe.db.get_value(
#             "Leave Allocation",
#             {
#                 "name": opening_ledger.transaction_name,
#                 "docstatus": 1,
#             },
#             ["custom_opening_balance"],
#             as_dict=True,
#         )
#         if allocation:
#             opening = flt(allocation.custom_opening_balance or 0)

#     accrual_ledger = frappe.db.get_value(
#         "Leave Ledger Entry",
#         {
#             "employee": employee,
#             "leave_type": leave_type,
#             "from_date": accrual_date,
#             "transaction_type": "Leave Allocation",
#             "custom_is_penalty": 0,
#             "docstatus": 1,
#         },
#         ["transaction_name", "leaves"],
#         as_dict=True,
#     )

#     accrued = 0
#     if accrual_ledger:
#         if accrual_date == april_date:
#             if accrual_ledger.transaction_name:
#                 allocation = frappe.db.get_value(
#                     "Leave Allocation",
#                     {
#                         "name": accrual_ledger.transaction_name,
#                         "docstatus": 1,
#                     },
#                     ["new_leaves_allocated"],
#                     as_dict=True,
#                 )
#                 if allocation:
#                     accrued = flt(allocation.new_leaves_allocated or 0)
#         else:
#             accrued = flt(accrual_ledger.leaves or 0)

#     return {"opening": opening, "accrued": accrued}


























# # ----------------------------- Latest UPDATED CODE (26-03-2026) -------------------------------
# # Yearly Balance Logic Updated:


# import frappe
# from frappe.utils import flt, getdate, today
# import calendar


# # ─────────────────────────────────────────────────────────────────────────────
# # CONSTANTS
# # ─────────────────────────────────────────────────────────────────────────────

# # The first financial year under the new scheme starts on this date.
# # All months from Dec-2025 through Mar-2026 belong to "FY 2025".
# # From Apr-2026 onwards every normal April-to-March year is a new FY.
# NEW_SCHEME_START = getdate("2025-12-01")   # first accrual date of FY 2025
# FY2025_OPENING_DATE = getdate("2025-11-30")  # opening snapshot date for FY 2025
# FY2026_START = getdate("2026-04-01")         # first day of FY 2026 and beyond


# # ─────────────────────────────────────────────────────────────────────────────
# # MAIN EXECUTE
# # ─────────────────────────────────────────────────────────────────────────────

# def execute(filters=None):

#     filters = frappe._dict(filters or {})

#     # from_date  → 1st of the filtered month
#     # to_date    → last date of the filtered month  (or today if current month)
#     from_date, to_date = get_date_range(filters)

#     employees   = get_employees(filters)
#     leave_types = get_leave_types(filters)

#     # ── Determine which Financial Year window we are in ───────────────────────
#     # FY 2025  : Dec-2025 … Mar-2026  (fy_accrual_start = 01-Dec-2025)
#     # FY 2026+ : Apr-2026 … Mar-2027  (fy_accrual_start = 01-Apr-2026)
#     # FY 2027+ : Apr-2027 … Mar-2028  (fy_accrual_start = 01-Apr-2027)  … etc.
#     fy_accrual_start, opening_date = get_fy_boundaries(from_date)

#     # ── Fetch ALL relevant ledger entries in one query ────────────────────────
#     # We need entries from the opening_date itself all the way to to_date.
#     ledger_entries = get_leave_ledger_entries(opening_date, to_date)

#     # ── Previous-month boundary for "Availed Till Last Month" ─────────────────
#     # For FY 2025, the very first reportable month is December 2025.
#     #   • If filtered month == Dec-2025  → no "last month" inside FY, so
#     #     availed_till_last_month = 0 (nothing before 01-Dec-2025 counts).
#     #   • Otherwise                      → count from fy_accrual_start up to
#     #     (from_date - 1 day), i.e. last month's last date.
#     # For FY 2026+, fy_accrual_start == 01-Apr-YYYY.
#     #   • If filtered month == Apr-YYYY  → availed_till_last_month = 0.
#     #   • Otherwise                      → count from fy_accrual_start up to
#     #     (from_date - 1 day).
#     # For FY 2025 : fy_accrual_start = 01-Dec-2025, from_date for Dec = 01-Dec -> match, correct
#     # For FY 2026+: fy_accrual_start = 02-Apr-YYYY, from_date for Apr = 01-Apr -> no match,
#     #               but April IS still the first month of the FY, so we also check
#     #               whether from_date == opening_date (01-Apr-YYYY) for FY 2026+.
#     is_first_month_of_fy = (
#         from_date == fy_accrual_start  # covers FY 2025 December case
#         or (
#             opening_date != FY2025_OPENING_DATE  # FY 2026+ only
#             and from_date == opening_date         # April = first month of FY
#         )
#     )
#     if is_first_month_of_fy:
#         availed_prev_end = None   # first month of FY — nothing before it counts
#     else:
#         availed_prev_end = add_days(from_date, -1)   # last day of previous month

#     data = []

#     for emp in employees:

#         row = {
#             "employee":      emp.name,
#             "employee_name": emp.employee_name,
#             "branch":        emp.branch,
#             "designation":   emp.designation,
#         }

#         # Is this employee on monthly accrual schedule?
#         # Contractual and Probation get CL accrued on 01st of every month
#         # (including 01-Apr) instead of a lump-sum annual grant.
#         is_monthly_accrual_emp = emp.get("employment_type") in (
#             "Contractual", "Probation"
#         )

#         for lt in leave_types:

#             prefix = get_prefix(lt)

#             opening               = 0.0
#             accrued               = 0.0
#             availed_till_last_mth = 0.0
#             availed_current_mth   = 0.0
#             deduction             = 0.0

#             for entry in ledger_entries:

#                 if entry.employee   != emp.name: continue
#                 if entry.leave_type != lt:        continue

#                 leaves     = flt(entry.leaves)
#                 e_date     = getdate(entry.from_date)
#                 txn_type   = entry.transaction_type
#                 is_penalty = entry.custom_is_penalty

#                 # ── 1. OPENING BALANCE ────────────────────────────────────────
#                 # Static for all months of the FY.
#                 # FY 2025 : entries whose from_date == 30-Nov-2025
#                 # FY 2026+: entries whose from_date == 01-Apr-YYYY
#                 #
#                 # EXCEPTION: CL for Contractual/Probation on 01-Apr-YYYY is
#                 # a monthly accrual entry, NOT an opening balance.
#                 # It must go to Accrued, not Opening.
#                 # SL/PL carry-forward and Confirmed annual grant on 01-Apr
#                 # are genuine opening entries and stay here.
#                 if (
#                     e_date == opening_date
#                     and txn_type == "Leave Allocation"
#                     and not is_penalty
#                 ):
#                     is_cl_monthly_accrual_on_apr1 = (
#                         lt == "Casual Leave"
#                         and is_monthly_accrual_emp
#                         and opening_date != FY2025_OPENING_DATE  # only FY2026+
#                     )
#                     if is_cl_monthly_accrual_on_apr1:
#                         # Route to accrued instead
#                         accrued += leaves
#                     else:
#                         opening += leaves

#                 # ── 2. ACCRUED ────────────────────────────────────────────────
#                 # FY 2025 : fy_accrual_start (01-Dec-2025) → to_date
#                 # FY 2026+: fy_accrual_start (02-Apr-YYYY) → to_date
#                 # Only Leave Allocation, not penalty.
#                 # Note: CL for Contractual/Probation on 01-Apr is handled
#                 # above in the opening block and re-routed here.
#                 elif (
#                     fy_accrual_start <= e_date <= to_date
#                     and txn_type == "Leave Allocation"
#                     and not is_penalty
#                 ):
#                     accrued += leaves

#                 # ── 3. AVAILED TILL LAST MONTH ────────────────────────────────
#                 # Entries from fy_accrual_start up to end of previous month.
#                 # Zero for the very first month of the FY.
#                 elif (
#                     availed_prev_end is not None
#                     and fy_accrual_start <= e_date <= availed_prev_end
#                     and txn_type == "Leave Application"
#                 ):
#                     availed_till_last_mth += abs(leaves)

#                 # ── 4. AVAILED CURRENT MONTH ─────────────────────────────────
#                 # Entries within the filtered month only.
#                 elif (
#                     from_date <= e_date <= to_date
#                     and txn_type == "Leave Application"
#                 ):
#                     availed_current_mth += abs(leaves)

#                 # ── 5. DEDUCTION (penalty) ────────────────────────────────────
#                 # FY 2025 : 01-Dec-2025 → to_date,  is_penalty = True
#                 # FY 2026+: 01-Apr-YYYY → to_date,  is_penalty = True
#                 elif (
#                     fy_accrual_start <= e_date <= to_date
#                     and is_penalty
#                 ):
#                     deduction += abs(leaves)

#             # ── 6 & 7. DERIVED COLUMNS ────────────────────────────────────────
#             total_availed = availed_till_last_mth + availed_current_mth + deduction
#             closing       = opening + accrued - total_availed

#             row[f"{prefix}_opening"]              = opening
#             row[f"{prefix}_accrued"]              = accrued
#             row[f"{prefix}_availed_last_month"]   = availed_till_last_mth
#             row[f"{prefix}_availed_current_month"]= availed_current_mth
#             row[f"{prefix}_deduction"]            = deduction
#             row[f"{prefix}_total_availed"]        = total_availed
#             row[f"{prefix}_closing"]              = closing

#         data.append(row)

#     columns = get_columns(leave_types)
#     return columns, data


# # ─────────────────────────────────────────────────────────────────────────────
# # HELPER: FY BOUNDARIES
# # ─────────────────────────────────────────────────────────────────────────────

# def get_fy_boundaries(from_date):
#     """
#     Returns (fy_accrual_start, opening_date) for the given report month.

#     FY 2025  (Dec-2025 to Mar-2026)
#         fy_accrual_start = 2025-12-01
#         opening_date     = 2025-11-30

#     FY 2026+ (Apr-YYYY to Mar-YYYY+1)
#         fy_accrual_start = YYYY-04-01   where YYYY = calendar year of April
#         opening_date     = YYYY-04-01   (same day; opening entries are posted on 01-Apr)

#     NOTE: For FY 2026+ the opening_date == fy_accrual_start because the
#     Leave Allocation that carries forward the balance is posted on 01-Apr,
#     and we read it separately via the opening_date == e_date check.
#     The accrual loop uses a strict > comparison so that the 01-Apr
#     opening allocation is NOT double-counted inside accrued.
#     To keep the logic clean we therefore distinguish them by transaction
#     semantics inside the main loop (opening uses only the opening_date
#     equality check; accrued excludes that same date for FY 2026+).
#     """

#     # ── FY 2025 window: Dec-2025 through Mar-2026 ────────────────────────────
#     fy2025_end = getdate("2026-03-31")
#     if NEW_SCHEME_START <= from_date <= fy2025_end:
#         return NEW_SCHEME_START, FY2025_OPENING_DATE

#     # ── FY 2026 and beyond ───────────────────────────────────────────────────
#     # Find the April-start of the current FY.
#     # e.g. from_date = 2026-07-01  → fy_year = 2026, fy_start = 2026-04-01
#     #      from_date = 2027-02-01  → fy_year = 2026, fy_start = 2026-04-01
#     if from_date.month >= 4:
#         fy_year = from_date.year
#     else:
#         fy_year = from_date.year - 1

#     fy_start = getdate(f"{fy_year}-04-01")

#     # For FY 2026 the accrual starts from 02-Apr-2026 per the requirement
#     # ("from_date >= 02-04-2026") to avoid picking up the opening allocation
#     # posted on 01-Apr-2026.  For FY 2027+ the same rule applies.
#     # We handle this by:
#     #   opening_date     = fy_start          (01-Apr-YYYY)
#     #   fy_accrual_start = fy_start + 1 day  (02-Apr-YYYY)
#     fy_accrual_start = add_days(fy_start, 1)   # 02-Apr-YYYY

#     return fy_accrual_start, fy_start


# # ─────────────────────────────────────────────────────────────────────────────
# # HELPER: DATE ARITHMETIC
# # ─────────────────────────────────────────────────────────────────────────────

# def add_days(date, n):
#     """Return date + n calendar days as a date object."""
#     from datetime import timedelta
#     return date + timedelta(days=n)


# # ─────────────────────────────────────────────────────────────────────────────
# # COLUMNS
# # ─────────────────────────────────────────────────────────────────────────────

# def get_columns(leave_types):

#     columns = [
#         {
#             "label":     "Employee",
#             "fieldname": "employee",
#             "fieldtype": "Link",
#             "options":   "Employee",
#             "width":     120,
#         },
#         {
#             "label":     "Employee Name",
#             "fieldname": "employee_name",
#             "fieldtype": "Data",
#             "width":     150,
#         },
#         {
#             "label":     "Branch",
#             "fieldname": "branch",
#             "fieldtype": "Data",
#             "width":     120,
#         },
#         {
#             "label":     "Designation",
#             "fieldname": "designation",
#             "fieldtype": "Data",
#             "width":     140,
#         },
#     ]

#     for lt in leave_types:
#         prefix = get_prefix(lt)
#         label  = prefix.upper()

#         columns.extend([
#             {
#                 "label":     f"{label} Opening Balance",
#                 "fieldname": f"{prefix}_opening",
#                 "fieldtype": "Float",
#                 "width":     140,
#             },
#             {
#                 "label":     f"{label} Accrued Balance",
#                 "fieldname": f"{prefix}_accrued",
#                 "fieldtype": "Float",
#                 "width":     140,
#             },
#             {
#                 "label":     f"{label} Availed Till Last Month",
#                 "fieldname": f"{prefix}_availed_last_month",
#                 "fieldtype": "Float",
#                 "width":     170,
#             },
#             {
#                 "label":     f"{label} Availed Current Month",
#                 "fieldname": f"{prefix}_availed_current_month",
#                 "fieldtype": "Float",
#                 "width":     170,
#             },
#             {
#                 "label":     f"{label} Deduction Till Current Month",
#                 "fieldname": f"{prefix}_deduction",
#                 "fieldtype": "Float",
#                 "width":     180,
#             },
#             {
#                 "label":     f"{label} Total Availed",
#                 "fieldname": f"{prefix}_total_availed",
#                 "fieldtype": "Float",
#                 "width":     140,
#             },
#             {
#                 "label":     f"{label} Closing Balance",
#                 "fieldname": f"{prefix}_closing",
#                 "fieldtype": "Float",
#                 "width":     140,
#             },
#         ])

#     return columns


# # ─────────────────────────────────────────────────────────────────────────────
# # DATE RANGE FROM FILTERS
# # ─────────────────────────────────────────────────────────────────────────────

# def get_date_range(filters):

#     if not filters.get("month"):
#         frappe.throw("Please select Month")
#     if not filters.get("year"):
#         frappe.throw("Please select Year")

#     month_map = {
#         "January": 1, "February": 2,  "March": 3,
#         "April":   4, "May":      5,  "June":  6,
#         "July":    7, "August":   8,  "September": 9,
#         "October": 10,"November": 11, "December":  12,
#     }

#     month = month_map.get(filters.month)
#     year  = int(filters.year)

#     from_date = getdate(f"{year}-{month:02d}-01")

#     # Last day of the filtered month; cap at today if it is the current month
#     last_day_of_month = calendar.monthrange(year, month)[1]
#     last_date_of_month = getdate(f"{year}-{month:02d}-{last_day_of_month:02d}")
#     to_date = min(last_date_of_month, getdate(today()))
#     # to_date = min(last_date_of_month, getdate("2026-06-01"))

#     return from_date, to_date


# # ─────────────────────────────────────────────────────────────────────────────
# # EMPLOYEES
# # ─────────────────────────────────────────────────────────────────────────────

# def get_employees(filters):

#     conditions = " WHERE status = 'Active' "

#     if filters.branch:
#         conditions += " AND branch = %(branch)s"
#     if filters.employee:
#         conditions += " AND name = %(employee)s"
#     if filters.employment_type:
#         conditions += " AND employment_type = %(employment_type)s"

#     return frappe.db.sql(
#         f"""
#         SELECT
#             name,
#             employee_name,
#             branch,
#             designation,
#             employment_type
#         FROM `tabEmployee`
#         {conditions}
#         """,
#         filters,
#         as_dict=1,
#     )


# # ─────────────────────────────────────────────────────────────────────────────
# # LEDGER ENTRIES
# # ─────────────────────────────────────────────────────────────────────────────

# def get_leave_ledger_entries(fetch_from, fetch_to):
#     """
#     Fetch all submitted Leave Ledger Entries between fetch_from and fetch_to
#     (inclusive).  fetch_from is opening_date so we capture opening-balance
#     entries posted on that date as well.
#     """
#     return frappe.db.sql(
#         """
#         SELECT
#             employee,
#             leave_type,
#             transaction_type,
#             leaves,
#             from_date,
#             custom_is_penalty
#         FROM `tabLeave Ledger Entry`
#         WHERE
#             docstatus = 1
#             AND from_date BETWEEN %s AND %s
#         """,
#         (fetch_from, fetch_to),
#         as_dict=1,
#     )


# # ─────────────────────────────────────────────────────────────────────────────
# # LEAVE TYPES
# # ─────────────────────────────────────────────────────────────────────────────

# def get_leave_types(filters):
#     if filters.get("leave_type"):
#         return [filters.leave_type]
#     return ["Casual Leave", "Privilege Leave", "Sick Leave"]


# # ─────────────────────────────────────────────────────────────────────────────
# # PREFIX MAPPING
# # ─────────────────────────────────────────────────────────────────────────────

# def get_prefix(leave_type):
#     return {
#         "Casual Leave":    "cl",
#         "Privilege Leave": "pl",
#         "Sick Leave":      "sl",
#     }.get(leave_type, leave_type.lower().replace(" ", "_"))

























# ---------------------------------------- Leave Required Report Updated Code (08-04-2026) ----------------------------------------

# ----------------------------- Latest UPDATED CODE (08-04-2026) -------------------------------


import frappe
from frappe.utils import flt, getdate, today
import calendar


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

NEW_SCHEME_START    = getdate("2025-12-01")   # first accrual date of FY 2025
FY2025_OPENING_DATE = getdate("2025-11-30")   # opening snapshot date for FY 2025
FY2026_START        = getdate("2026-04-01")   # first day of FY 2026 and beyond


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTE
# ─────────────────────────────────────────────────────────────────────────────

def execute(filters=None):

    filters = frappe._dict(filters or {})

    # from_date → 1st of the filtered month
    # to_date   → last date of the filtered month (or today if current month)
    from_date, to_date = get_date_range(filters)

    employees   = get_employees(filters)
    leave_types = get_leave_types(filters)

    # ── Determine which Financial Year window we are in ───────────────────────
    fy_accrual_start, opening_date = get_fy_boundaries(from_date)

    is_fy2025 = (opening_date == FY2025_OPENING_DATE)

    # ── Fetch ALL relevant ledger entries in one query ────────────────────────
    ledger_entries = get_leave_ledger_entries(opening_date, to_date)

    # ── Pre-fetch custom_opening_balance for SL allocations on opening_date ──
    # Only needed for FY 2026+ where SL opening = custom_opening_balance
    # from the linked Leave Allocation document.
    sl_opening_balance_map = {}
    if not is_fy2025:
        sl_opening_balance_map = get_sl_custom_opening_balances(
            ledger_entries, opening_date
        )

    # ── Previous-month boundaries ─────────────────────────────────────────────
    # availed_prev_end  : last day of previous month  (None for first FY month)
    # prev_month_start  : first day of previous month (None for first FY month)
    #
    # "Availed Till Last Month" accumulates:
    #   • Leave Applications  from fy_accrual_start → availed_prev_end
    #   • Penalty deductions  from prev_month_start → availed_prev_end ONLY
    #     (i.e. deductions of the previous month, not the whole FY)

    is_first_month_of_fy = (
        from_date == fy_accrual_start          # covers FY 2025 December case
        or (
            not is_fy2025                      # FY 2026+ only
            and from_date == opening_date      # April = first month of FY
        )
    )

    if is_first_month_of_fy:
        availed_prev_end = None
        prev_month_start = None
    else:
        # Last day of previous month
        availed_prev_end = add_days(from_date, -1)
        # First day of previous month
        prev_month_start = getdate(
            f"{availed_prev_end.year}-{availed_prev_end.month:02d}-01"
        )

    data = []

    for emp in employees:

        row = {
            "employee":      emp.name,
            "employee_name": emp.employee_name,
            "branch":        emp.branch,
            "designation":   emp.designation,
        }

        is_monthly_accrual_emp = emp.get("employment_type") in (
            "Contractual", "Probation"
        )

        for lt in leave_types:

            prefix = get_prefix(lt)

            opening               = 0.0
            accrued               = 0.0
            availed_till_last_mth = 0.0
            availed_current_mth   = 0.0
            deduction_current_mth = 0.0

            for entry in ledger_entries:

                if entry.employee   != emp.name: continue
                if entry.leave_type != lt:        continue

                leaves     = flt(entry.leaves)
                e_date     = getdate(entry.from_date)
                txn_type   = entry.transaction_type
                is_penalty = entry.custom_is_penalty

                # ── 1. OPENING BALANCE ────────────────────────────────────────
                #
                # FY 2025:
                #   All leave types: entries on 30-Nov-2025, Leave Allocation,
                #   not penalty → Opening.
                #
                # FY 2026+:
                #   CL  : Always 0. The 01-Apr CL allocation → Accrued.
                #   SL  : Entry on 01-Apr-YYYY, Leave Allocation, not penalty.
                #         Fetch custom_opening_balance from the linked Leave
                #         Allocation doc (via transaction_name). That value is
                #         the SL Opening Balance. The remainder (new grant)
                #         goes to Accrued.
                #   PL  : Entry on 01-Apr-YYYY, Leave Allocation, not penalty.
                #         Use leaves directly from the ledger entry as Opening
                #         (this is the carry-forward balance).
                #         Monthly accrual entries after 01-Apr → Accrued.

                if (
                    e_date == opening_date
                    and txn_type == "Leave Allocation"
                    and not is_penalty
                ):
                    if is_fy2025:
                        # FY 2025: all opening allocations on 30-Nov-2025 → Opening
                        opening += leaves

                    else:
                        # FY 2026+
                        if lt == "Casual Leave":
                            # CL lapses at year-end → 01-Apr allocation goes to Accrued
                            accrued += leaves

                        elif lt == "Sick Leave":
                            # SL Opening = custom_opening_balance from the linked
                            # Leave Allocation document. Remainder = new grant → Accrued.
                            key = (emp.name, lt)
                            custom_ob = sl_opening_balance_map.get(key, 0.0)
                            opening += custom_ob
                            new_grant = leaves - custom_ob
                            if new_grant > 0:
                                accrued += new_grant

                        elif lt == "Privilege Leave":
                            # PL: the 01-Apr-YYYY ledger entry is the carry-forward.
                            # Use leaves directly as Opening Balance.
                            opening += leaves

                # ── 2. ACCRUED ────────────────────────────────────────────────
                #
                # FY 2025 : fy_accrual_start (01-Dec-2025) → to_date
                # FY 2026+: fy_accrual_start (02-Apr-YYYY) → to_date
                # Leave Allocation entries that are not penalties.
                # 01-Apr entries are handled in block 1 above and naturally
                # excluded here because fy_accrual_start = 02-Apr for FY 2026+.

                elif (
                    fy_accrual_start <= e_date <= to_date
                    and txn_type == "Leave Allocation"
                    and not is_penalty
                ):
                    accrued += leaves

                # ── 3. AVAILED TILL LAST MONTH — Leave Applications ───────────
                # Leave Applications (not penalty) from fy_accrual_start up to
                # end of the previous month.
                # Zero for the very first month of the FY.

                elif (
                    availed_prev_end is not None
                    and opening_date <= e_date <= availed_prev_end
                    and txn_type == "Leave Application"
                    and not is_penalty
                ):
                    availed_till_last_mth += abs(leaves)

                # ── 3b. AVAILED TILL LAST MONTH — Previous-month deductions ───
                # Penalty Leave Allocations within the PREVIOUS MONTH ONLY
                # (prev_month_start → availed_prev_end).
                # NOT the entire FY — strictly the one previous month.

                elif (
                    prev_month_start is not None
                    and availed_prev_end is not None
                    and prev_month_start <= e_date <= availed_prev_end
                    and txn_type == "Leave Allocation"
                    and is_penalty
                ):
                    availed_till_last_mth += abs(leaves)

                # ── 4. AVAILED CURRENT MONTH ─────────────────────────────────
                # Leave Application entries (not penalty) within the filtered
                # month only (from_date → to_date).

                elif (
                    from_date <= e_date <= to_date
                    and txn_type == "Leave Application"
                    and not is_penalty
                ):
                    availed_current_mth += abs(leaves)

                # ── 5. DEDUCTION CURRENT MONTH ────────────────────────────────
                # Penalty Leave Allocations within the current filtered month
                # only (from_date → to_date). NOT cumulative from FY start.

                elif (
                    from_date <= e_date <= to_date
                    and txn_type == "Leave Allocation"
                    and is_penalty
                ):
                    deduction_current_mth += abs(leaves)

            # ── 6 & 7. DERIVED COLUMNS ────────────────────────────────────────
            total_availed = availed_till_last_mth + availed_current_mth + deduction_current_mth
            closing       = opening + accrued - total_availed

            row[f"{prefix}_opening"]               = opening
            row[f"{prefix}_accrued"]               = accrued
            row[f"{prefix}_availed_last_month"]    = availed_till_last_mth
            row[f"{prefix}_availed_current_month"] = availed_current_mth
            row[f"{prefix}_deduction"]             = deduction_current_mth
            row[f"{prefix}_total_availed"]         = total_availed
            row[f"{prefix}_closing"]               = closing

        data.append(row)

    columns = get_columns(leave_types)
    return columns, data


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: SL CUSTOM OPENING BALANCE PRE-FETCH
# ─────────────────────────────────────────────────────────────────────────────

def get_sl_custom_opening_balances(ledger_entries, opening_date):
    """
    For FY 2026+, find all Sick Leave ledger entries posted on opening_date
    (01-Apr-YYYY) with transaction_type = "Leave Allocation" and not penalty.
    For each, fetch the linked Leave Allocation document via transaction_name
    and read the custom_opening_balance field.

    Returns a dict keyed by (employee, leave_type) → custom_opening_balance.
    """
    result = {}

    for entry in ledger_entries:
        if entry.leave_type         != "Sick Leave":       continue
        if getdate(entry.from_date) != opening_date:       continue
        if entry.transaction_type   != "Leave Allocation": continue
        if entry.custom_is_penalty:                        continue

        transaction_name = entry.get("transaction_name")
        if not transaction_name:
            continue

        try:
            custom_ob = frappe.db.get_value(
                "Leave Allocation",
                transaction_name,
                "custom_opening_balance"
            )
            key = (entry.employee, entry.leave_type)
            result[key] = flt(custom_ob)
        except Exception:
            result[(entry.employee, entry.leave_type)] = 0.0

    return result


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: FY BOUNDARIES
# ─────────────────────────────────────────────────────────────────────────────

def get_fy_boundaries(from_date):
    """
    Returns (fy_accrual_start, opening_date) for the given report month.

    FY 2025  (Dec-2025 to Mar-2026)
        fy_accrual_start = 2025-12-01
        opening_date     = 2025-11-30

    FY 2026+ (Apr-YYYY to Mar-YYYY+1)
        fy_accrual_start = YYYY-04-02   (day after opening_date, to avoid
                                          double-counting the 01-Apr allocation)
        opening_date     = YYYY-04-01
    """

    fy2025_end = getdate("2026-03-31")
    if NEW_SCHEME_START <= from_date <= fy2025_end:
        return NEW_SCHEME_START, FY2025_OPENING_DATE

    if from_date.month >= 4:
        fy_year = from_date.year
    else:
        fy_year = from_date.year - 1

    fy_start         = getdate(f"{fy_year}-04-01")
    fy_accrual_start = add_days(fy_start, 1)   # 02-Apr-YYYY

    return fy_accrual_start, fy_start


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: DATE ARITHMETIC
# ─────────────────────────────────────────────────────────────────────────────

def add_days(date, n):
    """Return date + n calendar days as a date object."""
    from datetime import timedelta
    return date + timedelta(days=n)


# ─────────────────────────────────────────────────────────────────────────────
# COLUMNS
# ─────────────────────────────────────────────────────────────────────────────

def get_columns(leave_types):

    columns = [
        {
            "label":     "Employee",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options":   "Employee",
            "width":     120,
        },
        {
            "label":     "Employee Name",
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width":     150,
        },
        {
            "label":     "Branch",
            "fieldname": "branch",
            "fieldtype": "Data",
            "width":     120,
        },
        {
            "label":     "Designation",
            "fieldname": "designation",
            "fieldtype": "Data",
            "width":     140,
        },
    ]

    for lt in leave_types:
        prefix = get_prefix(lt)
        label  = prefix.upper()

        columns.extend([
            {
                "label":     f"{label} Opening Balance",
                "fieldname": f"{prefix}_opening",
                "fieldtype": "Float",
                "width":     140,
            },
            {
                "label":     f"{label} Accrued Balance",
                "fieldname": f"{prefix}_accrued",
                "fieldtype": "Float",
                "width":     140,
            },
            {
                "label":     f"{label} Availed Till Last Month",
                "fieldname": f"{prefix}_availed_last_month",
                "fieldtype": "Float",
                "width":     170,
            },
            {
                "label":     f"{label} Availed Current Month",
                "fieldname": f"{prefix}_availed_current_month",
                "fieldtype": "Float",
                "width":     170,
            },
            {
                "label":     f"{label} Deduction Current Month",
                "fieldname": f"{prefix}_deduction",
                "fieldtype": "Float",
                "width":     180,
            },
            {
                "label":     f"{label} Total Availed",
                "fieldname": f"{prefix}_total_availed",
                "fieldtype": "Float",
                "width":     140,
            },
            {
                "label":     f"{label} Closing Balance",
                "fieldname": f"{prefix}_closing",
                "fieldtype": "Float",
                "width":     140,
            },
        ])

    return columns


# ─────────────────────────────────────────────────────────────────────────────
# DATE RANGE FROM FILTERS
# ─────────────────────────────────────────────────────────────────────────────

def get_date_range(filters):

    if not filters.get("month"):
        frappe.throw("Please select Month")
    if not filters.get("year"):
        frappe.throw("Please select Year")

    month_map = {
        "January": 1, "February": 2,  "March":     3,
        "April":   4, "May":      5,  "June":      6,
        "July":    7, "August":   8,  "September": 9,
        "October": 10,"November": 11, "December":  12,
    }

    month = month_map.get(filters.month)
    year  = int(filters.year)

    from_date = getdate(f"{year}-{month:02d}-01")

    last_day_of_month  = calendar.monthrange(year, month)[1]
    last_date_of_month = getdate(f"{year}-{month:02d}-{last_day_of_month:02d}")
    to_date            = min(last_date_of_month, getdate(today()))
    # to_date = min(last_date_of_month, getdate("2026-07-01"))

    return from_date, to_date


# ─────────────────────────────────────────────────────────────────────────────
# EMPLOYEES
# ─────────────────────────────────────────────────────────────────────────────

def get_employees(filters):

    conditions = " WHERE status = 'Active' "

    if filters.branch:
        conditions += " AND branch = %(branch)s"
    if filters.employee:
        conditions += " AND name = %(employee)s"
    if filters.employment_type:
        conditions += " AND employment_type = %(employment_type)s"

    return frappe.db.sql(
        f"""
        SELECT
            name,
            employee_name,
            branch,
            designation,
            employment_type
        FROM `tabEmployee`
        {conditions}
        """,
        filters,
        as_dict=1,
    )


# ─────────────────────────────────────────────────────────────────────────────
# LEDGER ENTRIES
# ─────────────────────────────────────────────────────────────────────────────

def get_leave_ledger_entries(fetch_from, fetch_to):
    """
    Fetch all submitted Leave Ledger Entries between fetch_from and fetch_to
    (inclusive). fetch_from is opening_date so we capture opening-balance
    entries posted on that date as well.
    """
    return frappe.db.sql(
        """
        SELECT
            employee,
            leave_type,
            transaction_type,
            transaction_name,
            leaves,
            from_date,
            custom_is_penalty
        FROM `tabLeave Ledger Entry`
        WHERE
            docstatus = 1
            AND from_date BETWEEN %s AND %s
        """,
        (fetch_from, fetch_to),
        as_dict=1,
    )


# ─────────────────────────────────────────────────────────────────────────────
# LEAVE TYPES
# ─────────────────────────────────────────────────────────────────────────────

def get_leave_types(filters):
    if filters.get("leave_type"):
        return [filters.leave_type]
    return ["Casual Leave", "Privilege Leave", "Sick Leave"]


# ─────────────────────────────────────────────────────────────────────────────
# PREFIX MAPPING
# ─────────────────────────────────────────────────────────────────────────────

def get_prefix(leave_type):
    return {
        "Casual Leave":    "cl",
        "Privilege Leave": "pl",
        "Sick Leave":      "sl",
    }.get(leave_type, leave_type.lower().replace(" ", "_"))