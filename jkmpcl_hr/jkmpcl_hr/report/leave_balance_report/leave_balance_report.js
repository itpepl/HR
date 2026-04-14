frappe.query_reports["Leave Balance Report"] = {

    filters: [

        {
            fieldname: "branch",
            label: "Branch",
            fieldtype: "Link",
            options: "Branch"
        },

        {
            fieldname: "month",
            label: "Month",
            fieldtype: "Select",
            options: [
                "January","February","March","April","May","June",
                "July","August","September","October","November","December"
            ],
            default: moment().format("MMMM"),
            on_change: function () {
                set_as_on_date();
            }
        },

        {
            fieldname: "year",
            label: "Year",
            fieldtype: "Select",
            options: get_years(),
            default: new Date().getFullYear(),
            on_change: function () {
                set_as_on_date();
            }
        },

        {
            fieldname: "as_on_date",
            label: "As On Date",
            fieldtype: "Date",
            read_only: 1
        },

        {
            fieldname: "employment_type",
            label: "Employment Type",
            fieldtype: "Select",
            options: [
                "",
                "Confirmed",
                "Probation",
                "Contractual"
            ]
        },

        {
            fieldname: "leave_type",
            label: "Leave Type",
            fieldtype: "Link",
            options: "Leave Type"
        },

        {
            fieldname: "employee",
            label: "Employee",
            fieldtype: "Link",
            options: "Employee"
        },

        {
            fieldname: "group_by",
            label: "Group By Option",
            fieldtype: "Select",
            options: [
                "",
                "Branch",
                "Grade",
                "Designation"
            ]
        }
    ],

    onload: function () {
        set_as_on_date();
    }
};


function set_as_on_date() {

    let month = frappe.query_report.get_filter_value("month");
    let year = frappe.query_report.get_filter_value("year");

    if (!month || !year) return;

    let month_index = moment().month(month).month();

    let selected_date = moment([year, month_index]);

    let current_month = moment().month();
    let current_year = moment().year();

    let as_on_date;

    if (month_index === current_month && year == current_year) {

        as_on_date = moment();

    } else {

        as_on_date = moment([year, month_index]).endOf("month");

    }

    frappe.query_report.set_filter_value(
        "as_on_date",
        as_on_date.format("YYYY-MM-DD")
    );
}


function get_years() {

    let years = [];
    let current_year = new Date().getFullYear();

    for (let i = current_year + 0; i >= current_year - 1; i--) {
        years.push(i);
    }

    return years;
}