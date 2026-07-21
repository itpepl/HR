import frappe 
from hrms.hr.doctype.expense_claim.expense_claim import ExpenseClaim
from erpnext.accounts.general_ledger import make_gl_entries
from hrms.hr.doctype.expense_claim.expense_claim import (
    update_reimbursed_amount,
)


class CustomExpenseClaim(ExpenseClaim):
    def on_submit(self):
        # Removed: the throw that blocked submission when approval_status == "Draft"
        self.update_task_and_project()
        self.make_gl_entries()
        update_reimbursed_amount(self)
        self.update_claimed_amount_in_employee_advance()
        self.create_exchange_gain_loss_je()
        if not frappe.db.get_single_value("Accounts Settings", "make_payment_via_journal_entry"):
            self.update_against_claim_in_pe()