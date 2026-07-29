import frappe
from frappe import _
from frappe.utils import get_datetime, flt
from geopy.distance import geodesic
from geopy.geocoders import Nominatim


# Create geolocator once
geolocator = Nominatim(
    user_agent="geolocation_tracking"
)


@frappe.whitelist()
def log_employee_location(
    employee,
    latitude,
    longitude,
    timestamp,
    type=None
):
    """
    API called by Mobile App every 5 minutes.

    Parameters

    employee
    latitude
    longitude
    timestamp
    """

    latitude = flt(latitude)
    longitude = flt(longitude)
    timestamp = get_datetime(timestamp)
    custom_type = type

    # -----------------------------------------
    # Validate Employee
    # -----------------------------------------

    if not frappe.db.exists("Employee", employee):
        frappe.throw(_("Employee does not exist."))

    # -----------------------------------------
    # Get Previous Location
    # -----------------------------------------

    hr_settings = frappe.get_single("HR Settings")
    
    geolocation_min_distaance = float(hr_settings.custom_geolocation_minimum_distance_in_meters)
    convert_into_km = round(geolocation_min_distaance / 1000, 2)

    if type != "S":

      previous = frappe.get_all(
          "Geolocation Tracking",
          filters={
              "employee": employee
          },
          fields=[
              "latitude",
              "longitude",
              "total_distance"
          ],
          order_by="timestamp desc",
          limit=1
      )

      distance = 0
      total_distance = 0

      if previous:

          previous_point = (
              previous[0].latitude,
              previous[0].longitude,
          )

          current_point = (
              latitude,
              longitude,
          )

          distance = geodesic(
              previous_point,
              current_point
          ).km

          # Ignore GPS drift
          if distance < convert_into_km:
              return

          total_distance = (
              flt(previous[0].total_distance)
              + distance
          )

      else:
          distance = 0
          total_distance = 0

    else:
      distance = 0
      total_distance = 0
    

    # -----------------------------------------
    # Reverse Geocode
    # -----------------------------------------

    address = ""

    try:

        location = geolocator.reverse(
            f"{latitude},{longitude}",
            exactly_one=True
        )

        if location:
            address = location.address

    except Exception:

        frappe.log_error(
            frappe.get_traceback(),
            "Employee Tracker Reverse Geocoding"
        )

    # -----------------------------------------
    # Save Location
    # -----------------------------------------

    doc = frappe.new_doc("Geolocation Tracking")

    doc.employee = employee
    doc.timestamp = timestamp
    doc.latitude = latitude
    doc.longitude = longitude
    doc.address = address
    doc.distance_from_previous = round(distance, 3)
    doc.total_distance = round(total_distance, 3)
    doc.custom_type = type

    doc.insert(ignore_permissions=True)

    frappe.db.commit()

    return {
        "success": True,
        "message": "Location logged successfully.",
        "data": {
            "employee": employee,
            "distance_from_previous": round(distance, 3),
            "total_distance": round(total_distance, 3),
            "address": address,
        },
    }