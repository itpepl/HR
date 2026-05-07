frappe.ui.form.on("Attendance Lock", {

    refresh(frm) {

        // =========================================
        // YEAR OPTIONS
        // =========================================
        let current_year = new Date().getFullYear();

        let years = [
            current_year,
            current_year - 1,
            current_year - 2
        ];

        frm.set_df_property(
            "year",
            "options",
            years.join("\n")
        );

        // =========================================
        // ONLY FOR NEW DOC
        // =========================================
        if (frm.is_new() && !frm.doc.year) {

            frm.doc.year = current_year;

            frm.refresh_field("year");
        }
    },

    month(frm) {

        set_month_dates(frm);
    },

    year(frm) {

        set_month_dates(frm);
    }
});


// =============================================
// COMMON FUNCTION
// =============================================
function set_month_dates(frm) {

    const month_map = {
        "January": 0,
        "February": 1,
        "March": 2,
        "April": 3,
        "May": 4,
        "June": 5,
        "July": 6,
        "August": 7,
        "September": 8,
        "October": 9,
        "November": 10,
        "December": 11
    };

    if (frm.doc.month && frm.doc.year) {

        let year = parseInt(frm.doc.year);
        let month = month_map[frm.doc.month];

        // =========================================
        // FIRST DATE
        // =========================================
        let first_date = new Date(year, month, 1);

        // =========================================
        // LAST DATE
        // =========================================
        let last_date = new Date(year, month + 1, 0);

        let from_date = frappe.datetime.obj_to_str(first_date);
        let to_date = frappe.datetime.obj_to_str(last_date);

        // =========================================
        // SET VALUES
        // =========================================
        frm.set_value("from_date", from_date);
        frm.set_value("to_date", to_date);
    }
}