
import json

import frappe
import firebase_admin
from firebase_admin import credentials, messaging


def initialize_firebase():
    """Initialize Firebase Admin SDK."""

    settings = frappe.get_single("Firebase Settings")

    if not settings.enable:
        frappe.throw("Firebase Notifications are disabled.")

    if not settings.service_account_json:
        frappe.throw("Service Account JSON is missing in Firebase Settings.")

    try:
        service_account = json.loads(settings.service_account_json)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Invalid Firebase Service Account JSON"
        )
        frappe.throw("Invalid Firebase Service Account JSON.")

    # Fix escaped newlines in private key
    if service_account.get("private_key"):
        service_account["private_key"] = service_account["private_key"].replace(
            "\\n",
            "\n"
        )

    # Initialize only once
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(service_account)
            firebase_admin.initialize_app(cred)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "Firebase Initialization Error"
            )
            raise


def send_fcm_notification(token, title, body, data=None):
    """
    Send FCM push notification.

    Args:
        token (str): Device FCM token
        title (str): Notification title
        body (str): Notification body
        data (dict): Optional custom payload
    """

    if not token:
        return {
            "success": False,
            "message": "FCM token is missing."
        }

    initialize_firebase()

    try:
        message = messaging.Message(
            token=token,
            # notification=messaging.Notification(
            #     title=title,
            #     body=body,
            # ),
            data={str(k): str(v) for k, v in (data or {}).items()},
        )

        response = messaging.send(message)

        return {
            "success": True,
            "message": "Notification sent successfully.",
            "message_id": response,
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Firebase Send Notification Error"
        )

        return {
            "success": False,
            "message": "Failed to send notification."
        }