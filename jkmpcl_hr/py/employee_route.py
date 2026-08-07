import frappe
from frappe.utils import get_datetime


@frappe.whitelist()
def get_employee_route(employee, date):

    from_datetime = f"{date} 00:00:00"
    to_datetime = f"{date} 23:59:59"

    start = frappe.get_all(
        "Geolocation Tracking",
        filters={
            "employee": employee,
            "timestamp": ["between", [from_datetime, to_datetime]],
            "custom_type": "S"
        },
        fields=["latitude", "longitude", "timestamp"],
        order_by="timestamp asc",
        limit=1
    )

    end = frappe.get_all(
        "Geolocation Tracking",
        filters={
            "employee": employee,
            "timestamp": ["between", [from_datetime, to_datetime]],
            "custom_type": "E"
        },
        fields=["latitude", "longitude", "timestamp"],
        order_by="timestamp desc",
        limit=1
    )

    latest_distance = frappe.get_all(
        "Geolocation Tracking",
        filters={
            "employee": employee,
            "timestamp": ["between", [from_datetime, to_datetime]]
        },
        fields=["total_distance"],
        order_by="timestamp desc",
        limit=1
    )

    route_points = frappe.get_all(
        "Geolocation Tracking",
        filters={
            "employee": employee,
            "timestamp": ["between", [from_datetime, to_datetime]]
        },
        fields=[
            "latitude",
            "longitude",
            "timestamp",
            "custom_type"
        ],
        order_by="timestamp asc"
    )

    activities = frappe.get_all(
        "Employee Activity",
        filters={
            "employee": employee,
            "request_date": ["between", [from_datetime, to_datetime]]
        },
        fields=[
            "latitude",
            "longitude",
            "purpose",
            "activity_details",
            "custom_location",
            "request_date"
        ],
        order_by="request_date asc"
    )

    for p in route_points:
      frappe.errprint(f"{p.timestamp} - {p.latitude},{p.longitude}")

    return {
        "start": start[0] if start else None,
        "route_points": route_points,
        "activities": activities,
        "end": end[0] if end else None,
        "total_distance": latest_distance[0].total_distance if latest_distance else 0
    }