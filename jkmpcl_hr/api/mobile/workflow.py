import frappe
from frappe.model.workflow import get_workflow
from frappe.model.workflow import apply_workflow

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
    

@frappe.whitelist(methods=["POST"])
def bulk_workflow_action(doctype, docnames, action):
    """
    Bulk Approve/Reject API

    Args:
        doctype: DocType name
        docnames: List of document names
        action: Approve or Reject
    """

    if isinstance(docnames, str):
        docnames = frappe.parse_json(docnames)

    if action not in ["Approve", "Reject"]:
        frappe.throw("Action must be either 'Approve' or 'Reject'.")

    success = []
    failed = []

    for name in docnames:
        try:
            doc = frappe.get_doc(doctype, name)

            # Apply workflow action
            apply_workflow(doc, action)

            success.append(name)

        except Exception as e:
            failed.append({
                "name": name,
                "error": str(e)
            })

    frappe.db.commit()

    return {
        "success": success,
        "failed": failed
    }