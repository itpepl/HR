import frappe
from frappe import _
from frappe.utils import (
    getdate,
    format_time,
    time_diff_in_seconds,
    get_datetime,
    format_duration,
)


@frappe.whitelist()
def get_employee_activity_summary(employee):

    if not frappe.db.exists("Employee", employee):
        frappe.throw(_("Employee does not exist."))

    today = getdate()

    today_start = f"{today} 00:00:00"
    today_end = f"{today} 23:59:59"

    # -------------------------------------------------------
    # Get today's Start & End records
    # -------------------------------------------------------

    start_record = frappe.db.get_value(
        "Geolocation Tracking",
        {
            "employee": employee,
            "custom_type": "S",
            "timestamp": ["between", [today_start, today_end]],
        },
        ["timestamp"],
        as_dict=True,
        order_by="timestamp asc",
    )

    end_record = frappe.db.get_value(
        "Geolocation Tracking",
        {
            "employee": employee,
            "custom_type": "E",
            "timestamp": ["between", [today_start, today_end]],
        },
        ["timestamp", "total_distance"],
        as_dict=True,
        order_by="timestamp desc",
    )

    total_time = "00:00:00"
    total_distance = "0 km"

    if start_record and end_record:

        seconds = time_diff_in_seconds(
            end_record.timestamp,
            start_record.timestamp,
        )

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        total_time = f"{hours:02}:{minutes:02}:{secs:02}"

        total_distance = f"{round(end_record.total_distance or 0,2)} km"

    # -------------------------------------------------------
    # Employee Activity
    # -------------------------------------------------------

    activities = frappe.get_all(
        "Employee Activity",
        filters={
            "employee": employee,
            "request_date": ["between", [today_start, today_end]],
        },
        fields=[
            "visit_location",
            "purpose",
            "request_date",
        ],
        order_by="request_date asc",
    )

    activity_list = []

    if len(activities) > 1:

      for row in activities:
          activity_list.append(
              {
                  "visit_location": row.visit_location,
                  "purpose": row.purpose,
                  "activity_time": format_time(row.request_date),
              }
          )

      return {
          "success": True,
          "message": "Activity summary fetched successfully.",
          "data": {
              "summary": {
                  "distance": total_distance,
                  "time": total_time,
                  "activity_count": len(activities),
              },
              "activities": activity_list,
          },
      }

    else:
        return