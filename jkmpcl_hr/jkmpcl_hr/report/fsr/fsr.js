// // FSR - Field Staff / TA-DA Report
// frappe.query_reports["FSR"] = {
// 	"filters": [
// 		{
// 			"fieldname": "employee",
// 			"label": __("Employee"),
// 			"fieldtype": "Link",
// 			"options": "Employee",
// 			"width": "120px"
// 		},
// 		{
// 			"fieldname": "branch",
// 			"label": __("Branch"),
// 			"fieldtype": "Link",
// 			"options": "Branch",
// 			"width": "120px"
// 		},
// 		{
// 			"fieldname": "from_date",
// 			"label": __("From Date"),
// 			"fieldtype": "Date",
// 			"default": frappe.datetime.month_start(),
// 			"width": "80px"
// 		},
// 		{
// 			"fieldname": "to_date",
// 			"label": __("To Date"),
// 			"fieldtype": "Date",
// 			"default": frappe.datetime.get_today(),
// 			"width": "80px"
// 		}
// 	],

// 	onload: function(report) {
// 		console.log("===== FSR JS LOADED =====");
// 		set_date_limits(report);
// 		report.page.add_inner_button(
//     __("Export Excel"),
//     	function() {

//         const filters = report.get_values();

// 				// -------------------------------------------------
//         // VALIDATE FROM DATE
//         // -------------------------------------------------

//         if (!filters.from_date) {
//             frappe.msgprint({
//                 title: __("Missing From Date"),
//                 message: __("Please select From Date before exporting."),
//                 indicator: "red"
//             });

//             return;
//         }

//         // -------------------------------------------------
//         // VALIDATE TO DATE
//         // -------------------------------------------------

//         if (!filters.to_date) {
//             frappe.msgprint({
//                 title: __("Missing To Date"),
//                 message: __("Please select To Date before exporting."),
//                 indicator: "red"
//             });

//             return;
//         }

//         const form = document.createElement("form");

//         form.method = "POST";

//         form.action =
//             "/api/method/jkmpcl_hr.jkmpcl_hr.report.fsr.fsr.export_excel_with_header";

//         form.target = "_blank";

//         // Filters
//         const filtersInput = document.createElement("input");

//         filtersInput.type = "hidden";
//         filtersInput.name = "filters";
//         filtersInput.value = JSON.stringify(filters);

//         form.appendChild(filtersInput);

//         // CSRF Token
//         const csrfInput = document.createElement("input");

//         csrfInput.type = "hidden";
//         csrfInput.name = "csrf_token";
//         csrfInput.value = frappe.csrf_token;

//         form.appendChild(csrfInput);

//         document.body.appendChild(form);

//         form.submit();

//         form.remove();
//     	}
// 		);
// 		const generate_report_button = report.page.btn_primary;

// 		if (generate_report_button) {
// 			generate_report_button.off("click.fsr_validation");

// 			generate_report_button.on("click.fsr_validation", function(e) {

// 				const from_date = report.get_filter_value("from_date");
// 				const to_date = report.get_filter_value("to_date");

// 				console.log("FSR Generate Report:", {
// 					from_date: from_date,
// 					to_date: to_date
// 				});

// 				if (!from_date) {
// 					e.preventDefault();
// 					e.stopImmediatePropagation();

// 					frappe.msgprint({
// 						title: __("Missing From Date"),
// 						message: __("Please select From Date."),
// 						indicator: "red"
// 					});

// 					return false;
// 				}

// 				if (!to_date) {
// 					e.preventDefault();
// 					e.stopImmediatePropagation();

// 					frappe.msgprint({
// 						title: __("Missing To Date"),
// 						message: __("Please select To Date."),
// 						indicator: "red"
// 					});

// 					return false;
// 				}
// 			});
// 		}
// 	},

// 	refresh: function(report) {
// 		set_date_limits(report);
// 	},

// 	"formatter": function (value, row, column, data, default_formatter) {
// 		value = default_formatter(value, row, column, data);
// 		if (data && data.is_total_row) {
// 			value = "<b>" + value + "</b>";
// 		}
// 		if (data && data.is_group_header) {
// 			value = "<b>" + value + "</b>";
// 		}
// 		return value;
// 	}
// };

// // function set_default_dates(report) {
// // 	const today = frappe.datetime.get_today();
// // 	const month_start = frappe.datetime.month_start();

// // 	const from = report.get_filter("from_date");
// // 	const to = report.get_filter("to_date");

// // 	from.df.max_date = today;
// // 	to.df.max_date = today;

// // 	if (!from.get_value()) {
// // 		from.set_value(month_start);
// // 	}

// // 	if (!to.get_value()) {
// // 		to.set_value(today);
// // 	}

// // 	from.refresh();
// // 	to.refresh();
// // }


// function set_date_limits(report) {

// 	const today = frappe.datetime.get_today();

// 	const from = report.get_filter("from_date");
// 	const to = report.get_filter("to_date");

// 	if (!from || !to) {
// 		return;
// 	}

// 	from.df.max_date = today;
// 	to.df.max_date = today;

// 	from.refresh();
// 	to.refresh();
// }





// FSR - Field Staff / TA-DA Report
frappe.query_reports["FSR"] = {
	"filters": [
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": "120px"
		},
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"width": "120px"
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.month_start(),
			"width": "80px"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.get_today(),
			"width": "80px"
		}
	],

	onload: function(report) {
		console.log("===== FSR JS LOADED =====");
		inject_fsr_error_css();
		force_default_dates(report);
		set_date_limits(report);
		bind_generate_validation(report);
		patch_report_refresh(report);

		report.page.wrapper.on("show", function () {
			force_default_dates(report);
		});

		report.page.add_inner_button(
			__("Export Excel"),
			function() {

				const filters = report.get_values();

				// -------------------------------------------------
				// VALIDATE FROM DATE
				// -------------------------------------------------

				if (!filters.from_date) {
					frappe.msgprint({
						title: __("Missing From Date"),
						message: __("Please select From Date before exporting."),
						indicator: "red"
					});

					return;
				}

				// -------------------------------------------------
				// VALIDATE TO DATE
				// -------------------------------------------------

				if (!filters.to_date) {
					frappe.msgprint({
						title: __("Missing To Date"),
						message: __("Please select To Date before exporting."),
						indicator: "red"
					});

					return;
				}

				const form = document.createElement("form");

				form.method = "POST";

				form.action =
					"/api/method/jkmpcl_hr.jkmpcl_hr.report.fsr.fsr.export_excel_with_header";

				form.target = "_blank";

				// Filters
				const filtersInput = document.createElement("input");

				filtersInput.type = "hidden";
				filtersInput.name = "filters";
				filtersInput.value = JSON.stringify(filters);

				form.appendChild(filtersInput);

				// CSRF Token
				const csrfInput = document.createElement("input");

				csrfInput.type = "hidden";
				csrfInput.name = "csrf_token";
				csrfInput.value = frappe.csrf_token;

				form.appendChild(csrfInput);

				document.body.appendChild(form);

				form.submit();

				form.remove();
			}
		);
	},

	refresh: function(report) {
		// Runs every time the report re-renders (including navigating back to it)
		if (is_fsr_filter_broken(report)) {
			console.warn("FSR: filter controls corrupted, forcing full reload.");
			window.location.reload();
			return;
		}
		inject_fsr_error_css();
		ensure_default_dates(report);
		set_date_limits(report);
		bind_generate_validation(report);
		patch_report_refresh(report);
	},

	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.is_total_row) {
			value = "<b>" + value + "</b>";
		}
		if (data && data.is_group_header) {
			value = "<b>" + value + "</b>";
		}
		return value;
	}
};

function ensure_default_dates(report) {
	if (!report || typeof report.set_filter_value !== "function") {
		return;
	}

	const updates = {};
	if (!report.get_filter_value("from_date")) updates.from_date = frappe.datetime.month_start();
	if (!report.get_filter_value("to_date")) updates.to_date = frappe.datetime.get_today();
	if (Object.keys(updates).length) {
		report.set_filter_value(updates);
	}
}

// -------------------------------------------------------------
// (Re)bind the mandatory-filter check on the "Generate Report"
// (primary) button. Must be called on refresh too, since Frappe
// recreates the primary button whenever the report re-renders.
// -------------------------------------------------------------
function bind_generate_validation(report) {
	const generate_report_button = report.page.btn_primary;

	if (!generate_report_button) {
		return;
	}

	generate_report_button.off("click.fsr_validation");

	generate_report_button.on("click.fsr_validation", function(e) {

		const from_date = report.get_filter_value("from_date");
		const to_date = report.get_filter_value("to_date");

		console.log("FSR Generate Report:", {
			from_date: from_date,
			to_date: to_date
		});

		if (!from_date) {
			e.preventDefault();
			e.stopImmediatePropagation();

			frappe.msgprint({
				title: __("Missing From Date"),
				message: __("Please select From Date."),
				indicator: "red"
			});

			return false;
		}

		if (!to_date) {
			e.preventDefault();
			e.stopImmediatePropagation();

			frappe.msgprint({
				title: __("Missing To Date"),
				message: __("Please select To Date."),
				indicator: "red"
			});

			return false;
		}
	});
}

// -------------------------------------------------------------
// Inject CSS once for highlighting invalid/empty mandatory fields
// -------------------------------------------------------------
function inject_fsr_error_css() {
	if (document.getElementById("fsr-error-style")) {
		return;
	}
	const style = document.createElement("style");
	style.id = "fsr-error-style";
	style.innerHTML = `
		.fsr-invalid-field input {
			border-color: #d73925 !important;
			box-shadow: 0 0 0 1px #d73925 !important;
			background-color: #fff5f5 !important;
		}
	`;
	document.head.appendChild(style);
}

// -------------------------------------------------------------
// Checks from_date / to_date are set. Highlights empty fields
// red and shows a message. Returns true if valid, false if not.
// -------------------------------------------------------------
function validate_mandatory_dates(report) {
	const from = report.get_filter("from_date");
	const to = report.get_filter("to_date");

	if (!from || !to) {
		return true; // filters not ready yet, don't block
	}

	const from_date = from.get_value();
	const to_date = to.get_value();

	let is_valid = true;

	if (from.$wrapper) {
		from.$wrapper.toggleClass("fsr-invalid-field", !from_date);
	}
	if (to.$wrapper) {
		to.$wrapper.toggleClass("fsr-invalid-field", !to_date);
	}

	if (!from_date) {
		is_valid = false;
	}
	if (!to_date) {
		is_valid = false;
	}

	if (!is_valid) {
		frappe.show_alert({
			message: __("From Date and To Date are mandatory to generate the report."),
			indicator: "red"
		});
	}

	return is_valid;
}

// -------------------------------------------------------------
// Monkey-patch frappe.query_report.refresh so that EVERY trigger
// of a report refresh - the "Generate Report" button, the toolbar
// refresh icon, a filter change, or a keyboard shortcut - is
// validated before the report is actually allowed to run.
// Patched only once; guards by report_name on every call so it
// only intercepts FSR and passes everything else through as-is.
// -------------------------------------------------------------
function patch_report_refresh(report) {
	if (frappe.query_report.__fsr_patched) {
		return;
	}

	const original_refresh = frappe.query_report.refresh.bind(frappe.query_report);

	frappe.query_report.refresh = function() {
		const is_fsr =
			frappe.query_report.report_name === "FSR" ||
			(frappe.query_report.report_doc &&
				frappe.query_report.report_doc.name === "FSR");

		if (!is_fsr) {
			return original_refresh.apply(this, arguments);
		}

		if (!validate_mandatory_dates(report)) {
			// Block the refresh entirely - don't call original_refresh
			return Promise.resolve();
		}

		return original_refresh.apply(this, arguments);
	};

	frappe.query_report.__fsr_patched = true;
}

function set_date_limits(report) {

	const today = frappe.datetime.get_today();

	const from = report.get_filter("from_date");
	const to = report.get_filter("to_date");

	if (!from || !to) {
		return;
	}

	from.df.max_date = today;
	to.df.max_date = today;

	from.refresh();
	to.refresh();
}


// -------------------------------------------------------------
// Forcibly reset from_date / to_date to their defaults.
// Uses the report's own set_filter_value() API (instead of
// manually calling control.set_value() + control.refresh()),
// since manual refresh right after an async set_value() creates
// a race condition. That race silently corrupts the filter
// control's internal state, which then crashes the datepicker
// re-init the next time the report page is revisited (the
// query-report page is a singleton and reuses controls instead
// of recreating them on navigation).
// -------------------------------------------------------------
function force_default_dates(report) {
	if (!report || typeof report.set_filter_value !== "function") {
		return;
	}

	report.set_filter_value({
		employee: null,
		branch: null,
		from_date: frappe.datetime.month_start(),
		to_date: frappe.datetime.get_today(),
	});
}


// -------------------------------------------------------------
// Returns true if the to_date (or from_date) filter control
// failed to render properly - i.e. the control object is
// missing, or its input element never got attached to the DOM.
// This is what happens when the query-report singleton page's
// cached filter state gets corrupted between SPA navigations.
// -------------------------------------------------------------
function is_fsr_filter_broken(report) {
	const to_ctrl = report.get_filter("to_date");
	const from_ctrl = report.get_filter("from_date");

	if (!to_ctrl || !from_ctrl) {
		return true;
	}

	if (!to_ctrl.$input || !to_ctrl.$input.length) {
		return true;
	}
	if (!from_ctrl.$input || !from_ctrl.$input.length) {
		return true;
	}

	return false;
}