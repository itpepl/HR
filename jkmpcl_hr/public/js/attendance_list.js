frappe.listview_settings["Attendance"] = {
	add_fields: ["status", "attendance_date"],

	// onload: async function (listview) {

	// 	// example async call
	// 	let r = await frappe.call({
	// 		method: "your_app.api.get_partially_config",
	// 	});

	// 	listview.partially_color = r.message || "blue";
	// },
	get_indicator: function (doc) {
		if (["Present", "Work From Home"].includes(doc.status)) {
				return [__(doc.status), "green", "status,=," + doc.status];
		} else if (["Absent", "On Leave"].includes(doc.status)) {
				return [__(doc.status), "red", "status,=," + doc.status];
		} else if (doc.status == "Half Day") {
				return [__(doc.status), "orange", "status,=," + doc.status];
		}
		else if (doc.status == "Partially") {
				return [__(doc.status), "blue", "status,=,Holiday"];
		}
			else if (doc.status == "Holiday") {
				return [__(doc.status), "purple", "status,=," + doc.status];
		}
			else if (doc.status == "Weekly Off") {
				return [__(doc.status), "gray", "status,=," + doc.status];
		}
			else if (doc.status == "Restricted Holiday") {
				return [__(doc.status), "yellow", "status,=," + doc.status];
		}
	},
};