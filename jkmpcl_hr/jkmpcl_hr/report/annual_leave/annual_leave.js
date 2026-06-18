// frappe.query_reports["Annual Leave"] = {
//     filters: [

//         {
//             fieldname: "fiscal_year",
//             label: __("Fiscal Year"),
//             fieldtype: "Link",
//             options: "Fiscal Year",
//             reqd: 1,
//             default: frappe.defaults.get_user_default("fiscal_year")
//         },

//         {
//             fieldname: "as_on_date",
//             label: __("Leave Balance As On Date"),
//             fieldtype: "Date",
//             reqd: 1,
//             default: frappe.datetime.get_today()
//         },

//         // {
//         //     fieldname: "balance_type",
//         //     label: __("Leave Balance Type"),
//         //     fieldtype: "Select",
//         //     options: [
//         //         "All",
//         //         "Opening Balance",
//         //         "Accrued",
//         //         "Availed",
//         //         "Closing Balance"
//         //     ],
//         //     default: "All"
//         // },

//         {
//             fieldname: "branch",
//             label: __("Branch"),
//             fieldtype: "Link",
//             options: "Branch"
//         },

//         {
//             fieldname: "employment_type",
//             label: __("Employment Type"),
//             fieldtype: "Select",
//             options: "\nAll\nConfirmed\nProbation\nContractual",
//             default: "All"
//         },

// 		{
// 			fieldname: "leave_type",
// 			label: __("Leave Type"),
// 			fieldtype: "Select",
// 			options: "\nCasual Leave\nSick Leave\nPrivilege Leave",
// 			default: ""
// 		},

//         {
//             fieldname: "employee",
//             label: __("Employee Code - Name"),
//             fieldtype: "Link",
//             options: "Employee",
//             get_query: function() {
//                 return {
//                     filters: {
//                         status: "Active"
//                     }
//                 };
//             }
//         },

//         {
// 			fieldname: "group_by",
// 			label: __("Group By"),
// 			fieldtype: "Select",
// 			options: "\nBranch\nDepartment\nDesignation\nGrade\nEmployment Type"
// 		}

//     ],

//     onload: function(report) {

//         report.page.add_inner_message(
//             __("Annual Leave Report generated from Leave Ledger Entry")
//         );

//     }
// };

frappe.query_reports["Annual Leave"] = {
    filters: [
        {
            fieldname: "fiscal_year",
            label: __("Fiscal Year"),
            fieldtype: "Link",
            options: "Fiscal Year",
            reqd: 1,
            default: frappe.defaults.get_user_default("fiscal_year")
        },
        // {
        //     fieldname: "as_on_date",
        //     label: __("Leave Balance As On Date"),
        //     fieldtype: "Date",
        //     reqd: 1,
        //     default: frappe.datetime.get_today()
        // },
        {
            fieldname: "branch",
            label: __("Branch"),
            fieldtype: "Link",
            options: "Branch"
        },
        // {
        //     fieldname: "department",
        //     label: __("Department"),
        //     fieldtype: "Link",
        //     options: "Department"
        // },
        // {
        //     fieldname: "designation",
        //     label: __("Designation"),
        //     fieldtype: "Link",
        //     options: "Designation"
        // },
        // {
        //     fieldname: "grade",
        //     label: __("Grade"),
        //     fieldtype: "Link",
        //     options: "Grade"
        // },
        {
            fieldname: "employment_type",
            label: __("Employment Type"),
            fieldtype: "Select",
            options: "\nAll\nConfirmed\nProbation\nContractual",
            default: "All"
        },
        {
            fieldname: "leave_type",
            label: __("Leave Type"),
            fieldtype: "Select",
            options: "\nCasual Leave\nSick Leave\nPrivilege Leave",
            default: ""
        },
        {
            fieldname: "employee",
            label: __("Employee Code - Name"),
            fieldtype: "Link",
            options: "Employee",
            get_query: function() {
                return {
                    filters: {
                        status: "Active"
                    }
                };
            }
        },
        {
            fieldname: "group_by",
            label: __("Group By"),
            fieldtype: "Select",
            options: "\nBranch\nDepartment\nDesignation\nGrade\nEmployment Type"
        }
    ],
    
    onload: function(report) {
        // Add dynamic filter behavior
        report.filters.forEach(filter => {
            if (filter.fieldname === "group_by") {
                filter.on_change = function() {
                    report.refresh();
                };
            }
        });
    }
};