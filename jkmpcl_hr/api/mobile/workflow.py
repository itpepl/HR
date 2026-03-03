import frappe
from frappe.model.workflow import get_workflow

@frappe.whitelist()
def get_workflow_actions_for_doc(doctype, docname):
    from frappe.model.workflow import get_transitions

    doc = frappe.get_doc(doctype, docname)

    transitions = get_transitions(doc)

    return transitions


@frappe.whitelist()
def apply_workflow_action(doctype, docname, action):
    try:
        from frappe.model.workflow import apply_workflow

        doc = frappe.get_doc(doctype, docname)

        apply_workflow(doc, action)

        frappe.db.commit()

        if action == "Reject":
            return {
                "success": True,
                "message": f"Request Rejected",
                "workflow_state": doc.workflow_state
            }

        else:
            return {
                "success": True,
                "message": f"{action} applied successfully",
                "workflow_state": doc.workflow_state
            }

    except Exception as e:
        frappe.db.rollback()
        return {
            "success": False,
            "message": str(e)
        }