import frappe
from frappe import _
from frappe.utils import flt, date_diff
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip, verify_lwp_days_corrected

from jkmpcl_hr.py.pl_accrual import get_eligible_days



class CustomSalarySlip(SalarySlip):

    # def get_working_days_details(self, lwp=None, for_preview=0, lwp_days_corrected=None):
    #     payroll_settings = frappe.get_cached_value(
    #         "Payroll Settings",
    #         None,
    #         (
    #             "payroll_based_on",
    #             "include_holidays_in_total_working_days",
    #             "consider_marked_attendance_on_holidays",
    #             "daily_wages_fraction_for_half_day",
    #             "consider_unmarked_attendance_as",
    #         ),
    #         as_dict=1,
    #     )

    #     consider_marked_attendance_on_holidays = (
    #         payroll_settings.include_holidays_in_total_working_days
    #         and payroll_settings.consider_marked_attendance_on_holidays
    #     )

    #     daily_wages_fraction_for_half_day = flt(payroll_settings.daily_wages_fraction_for_half_day) or 0.5

    #     # ================================
    #     # ✅ NEW WORKING DAYS LOGIC
    #     # ================================
    #     eligible_days, total_days = get_eligible_days(
    #         self.employee, self.start_date, self.end_date
    #     )

    #     print(f" \n\n Eligible Days: {eligible_days}, Total Days: {total_days} \n\n ")

    #     working_days = total_days

    #     if for_preview:
    #         self.total_working_days = working_days
    #         self.payment_days = working_days
    #         return

    #     holidays = self.get_holidays_for_employee(self.start_date, self.end_date)

    #     if not payroll_settings.payroll_based_on:
    #         frappe.throw(_("Please set Payroll based on in Payroll settings"))

    #     # ================================
    #     # ✅ NEW LWP LOGIC
    #     # ================================
    #     lle = frappe.qb.DocType("Leave Ledger Entry")

    #     lwp_entries = (
    #         frappe.qb.from_(lle)
    #         .select(lle.leaves)
    #         .where(
    #             (lle.employee == self.employee)
    #             & (lle.docstatus == 1)
    #             & (lle.is_lwp == 1)
    #             & (lle.from_date.between(self.start_date, self.end_date))
    #         )
    #     ).run(as_dict=True)

    #     actual_lwp = sum(abs(flt(row.leaves)) for row in lwp_entries)

    #     self.absent_days = flt(total_days) - flt(eligible_days)

    #     if not lwp:
    #         lwp = actual_lwp
    #     elif lwp != actual_lwp:
    #         frappe.msgprint(
    #             _("Leave Without Pay does not match with approved {} records").format(
    #                 payroll_settings.payroll_based_on
    #             )
    #         )

    #     self.leave_without_pay = lwp
    #     self.total_working_days = working_days

    #     # ================================
    #     # 🔁 ORIGINAL LOGIC (UNCHANGED)
    #     # ================================
    #     payment_days = self.get_payment_days(
    #         payroll_settings.include_holidays_in_total_working_days
    #     )

    #     if flt(payment_days) > flt(lwp):
    #         self.payment_days = flt(payment_days) - flt(lwp)

    #         if payroll_settings.payroll_based_on == "Attendance":
    #             self.payment_days -= flt(self.absent_days)

    #         consider_unmarked_attendance_as = (
    #             payroll_settings.consider_unmarked_attendance_as or "Present"
    #         )

    #         if payroll_settings.payroll_based_on == "Attendance":
    #             if consider_unmarked_attendance_as == "Absent":
    #                 unmarked_days = self.get_unmarked_days(
    #                     payroll_settings.include_holidays_in_total_working_days,
    #                     holidays,
    #                 )
    #                 self.absent_days += unmarked_days
    #                 self.payment_days -= unmarked_days

    #             half_absent_days = self.get_half_absent_days(
    #                 consider_marked_attendance_on_holidays,
    #                 holidays,
    #             )
    #             self.absent_days += (
    #                 half_absent_days * daily_wages_fraction_for_half_day
    #             )
    #             self.payment_days -= (
    #                 half_absent_days * daily_wages_fraction_for_half_day
    #             )
    #     else:
    #         self.payment_days = 0

    #     if lwp_days_corrected and lwp_days_corrected > 0:
    #         if verify_lwp_days_corrected(
    #             self.employee,
    #             self.start_date,
    #             self.end_date,
    #             lwp_days_corrected,
    #         ):
    #             self.payment_days += lwp_days_corrected
    
    
    
    def get_working_days_details(self, lwp=None, for_preview=0, lwp_days_corrected=None):
        
        print(f" \n\n Calculating working days for Employee: {self.employee}, Period: {self.start_date} to {self.end_date}  {lwp_days_corrected}\n\n ")
        
        payroll_settings = frappe.get_cached_value(
            "Payroll Settings",
            None,
            (
                "payroll_based_on",
                "include_holidays_in_total_working_days",
                "consider_marked_attendance_on_holidays",
                "daily_wages_fraction_for_half_day",
                "consider_unmarked_attendance_as",
            ),
            as_dict=1,
        )

        consider_marked_attendance_on_holidays = (
            payroll_settings.include_holidays_in_total_working_days
            and payroll_settings.consider_marked_attendance_on_holidays
        )

        daily_wages_fraction_for_half_day = flt(payroll_settings.daily_wages_fraction_for_half_day) or 0.5

        # ================================
        # ✅ WORKING DAYS LOGIC
        # ================================
        eligible_days, total_days = get_eligible_days(
            self.employee, self.start_date, self.end_date
        )

        working_days = total_days

        if for_preview:
            self.total_working_days = working_days
            self.payment_days = working_days
            return

        holidays = self.get_holidays_for_employee(self.start_date, self.end_date)

        if not payroll_settings.payroll_based_on:
            frappe.throw(_("Please set Payroll based on in Payroll settings"))

        # ================================
        # ✅ LWP LOGIC (UNCHANGED)
        # ================================
        lle = frappe.qb.DocType("Leave Ledger Entry")

        lwp_entries = (
            frappe.qb.from_(lle)
            .select(lle.leaves)
            .where(
                (lle.employee == self.employee)
                & (lle.docstatus == 1)
                & (lle.is_lwp == 1)
                & (lle.from_date.between(self.start_date, self.end_date))
            )
        ).run(as_dict=True)

        actual_lwp = sum(abs(flt(row.leaves)) for row in lwp_entries)

        # ==========================================================
        # 🔥 FIX: UAB (ABSENT DAYS) SAME AS REPORT
        # ==========================================================
        uab = 0

        attendance_list = frappe.get_all(
            "Attendance",
            filters={
                "employee": self.employee,
                "attendance_date": ["between", [self.start_date, self.end_date]],
            },
            fields=[
                "attendance_date",
                "status",
                "leave_type",
            ],
        )

        for att in attendance_list:
            status = att.status
            leave_type = att.leave_type

            if status == "Absent":
                uab += 1

            elif status == "Half Day":
                if not leave_type:
                    uab += 0.5
                elif leave_type == "Leave Without Pay":
                    uab += 0.5

        self.absent_days = uab

        # ================================
        # ORIGINAL FLOW CONTINUES
        # ================================
        if not lwp:
            lwp = actual_lwp
        elif lwp != actual_lwp:
            frappe.msgprint(
                _("Leave Without Pay does not match with approved {} records").format(
                    payroll_settings.payroll_based_on
                )
            )

        self.leave_without_pay = lwp
        self.total_working_days = working_days

        payment_days = self.get_payment_days(
            payroll_settings.include_holidays_in_total_working_days
        )
        print(f"\n\n payment dgfdgfddays {payment_days} \n\n")

        if flt(payment_days) > flt(lwp):
            self.payment_days = flt(payment_days) - flt(lwp)

            if payroll_settings.payroll_based_on == "Attendance":
                self.payment_days -= flt(self.absent_days)

            consider_unmarked_attendance_as = (
                payroll_settings.consider_unmarked_attendance_as or "Present"
            )

            if payroll_settings.payroll_based_on == "Attendance":
                if consider_unmarked_attendance_as == "Absent":
                    unmarked_days = self.get_unmarked_days(
                        payroll_settings.include_holidays_in_total_working_days,
                        holidays,
                    )
                    self.absent_days += unmarked_days
                    self.payment_days -= unmarked_days

                half_absent_days = self.get_half_absent_days(
                    consider_marked_attendance_on_holidays,
                    holidays,
                )
                self.absent_days += (
                    half_absent_days * daily_wages_fraction_for_half_day
                )
                self.payment_days -= (
                    half_absent_days * daily_wages_fraction_for_half_day
                )
        else:
            self.payment_days = 0
        print(f"\n\n payment days {payment_days} \n\n")
        if lwp_days_corrected and lwp_days_corrected > 0:
            if verify_lwp_days_corrected(
                self.employee,
                self.start_date,
                self.end_date,
                lwp_days_corrected,
            ):
                print(f"\n\n corrected days \n\n")
                self.payment_days += lwp_days_corrected
    