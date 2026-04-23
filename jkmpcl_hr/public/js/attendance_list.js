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
			else if (doc.status == "Suspended") {
				return [__(doc.status), "darkgrey", "status,=," + doc.status];
		}
	},

	onload: function (list_view) {

		if (list_view.custom_filter_applied) return;

		frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name")
		.then(res => {
			let emp = res.message.name;
			if (!emp) return;

			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Employee",
					filters: { "reports_to": emp },
					pluck: "name",
					limit_page_length: 1000
				},
				callback: function (r) {

					let employee_list = (r.message || []).map(e => 
	          typeof e === "object" ? e.name : e
          );

					// include self
					if (!employee_list.includes(emp)) {
						employee_list.push(emp);
					}

          if (list_view.filter_area) {
            list_view.filter_area.clear();
          }

					list_view.filter_area.add([
						["Attendance", "employee", "in", employee_list]
					]);

					list_view.custom_filter_applied = true;
				}
			});
		});
	}
};
