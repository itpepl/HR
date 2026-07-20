import frappe
from frappe.utils import getdate,formatdate


@frappe.whitelist()
def create_employee_advance(**args):
    """
    API to create Employee Advance
    """

    employee = args.get("employee")
    from_date = args.get("custom_from_date")
    to_date = args.get("custom_to_date")
    places = args.get("custom_places_to_be_visited")
    purpose = args.get("purpose")
    claim_amount = args.get("custom_claim_amount")
    # advance_amount = args.get("advance_amount")

    # Mandatory Validation
    mandatory_fields = {
        "employee": employee,
        "custom_from_date": from_date,
        "custom_to_date": to_date,
        "purpose": purpose,
        "custom_claim_amount": claim_amount,
    }

    for field, value in mandatory_fields.items():
        if not value:
            frappe.throw(f"{field.replace('_', ' ').title()} is mandatory.")

    from_date = getdate(from_date)
    to_date = getdate(to_date)

    if to_date < from_date:
        frappe.throw("To Date cannot be earlier than From Date.")

    doc = frappe.new_doc("Employee Advance")
    doc.employee = employee
    doc.custom_from_date = from_date
    doc.custom_to_date = to_date
    doc.custom_places_to_be_visited = places
    doc.purpose = purpose
    doc.custom_claim_amount = claim_amount
    doc.advance_amount = claim_amount

    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": "Employee Advance created successfully.",
        "name": doc.name
    }

@frappe.whitelist()
def employee_advance_list(filters=None):
    """
    Returns Employee Advance list of logged-in employee.
    """

    user = frappe.session.user

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        "name"
    )

    if not employee:
        return {
            "success": True,
            "message": "Employee Advance list fetched successfully.",
            "data": []
        }

    # Parse filters
    filters = frappe.parse_json(filters) if filters else []

    if isinstance(filters, dict):
        filters = [[k, "=", v] for k, v in filters.items()]

    # Convert status filter to workflow_state
    for f in filters:
        if isinstance(f, list) and len(f) >= 3 and f[0] == "status":
            f[0] = "workflow_state"

    # Employee filter
    filters.append(["employee", "=", employee])

    advances = frappe.get_all(
        "Employee Advance",
        filters=filters,
        fields=[
            "name",
            "employee",
            "custom_from_date",
            "custom_to_date",
            "custom_places_to_be_visited",
            "purpose",
            "custom_claim_amount",
            "advance_amount",
            "workflow_state",
            "status",
            "docstatus",
            "posting_date"
        ],
        order_by="creation desc"
    )

    data = []

    for d in advances:
        data.append({
            "name": d.name,
            "employee": d.employee,
            "from_date": formatdate(d.custom_from_date, "dd-MM-yyyy") if d.custom_from_date else "",
            "to_date": formatdate(d.custom_to_date, "dd-MM-yyyy") if d.custom_to_date else "",
            "places_to_be_visited": d.custom_places_to_be_visited,
            "purpose": d.purpose,
            "claim_amount": d.custom_claim_amount,
            "advance_amount": d.advance_amount,
            "status": d.workflow_state or d.status,
            "docstatus": d.docstatus,
            "posting_date": formatdate(d.posting_date, "dd-MM-yyyy") if d.posting_date else ""
        })

    return {
        "success": True,
        "message": "Employee Advance list fetched successfully.",
        "data": data
    }