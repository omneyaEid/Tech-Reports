// Copyright (c) 2024, omneyaeid827@gmail.com and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer Balance Summary for Period"] = {
	onload: function(report) {
        const customTitle = `
        <div class="custom-report-title" style="margin-top: 20px;">
            <div>
                <h1 style="color: darkred;text-align: center;">تقرير اجمالي مركز العملاء خلال فتره</h1>
                <hr style="border: 1px solid darkred; border-color: darkred; margin-top: 10px;">
            </div> 
        </div>
        `;
        
        // Inject the title HTML into the report container
        $(report.page.main).prepend(customTitle);

        // Inject custom styles via JavaScript
        const customStyles = `
            <style>
                .frappe-control {
                    display: flex;
                    align-items: center;
                    justify-content: flex-end;
                    margin-bottom: 15px;
                }
                .frappe-control label {
                    font-weight: bold;
                    margin-right: 5px;
                }
                .frappe-control input, .frappe-control select {
                    border: none;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 5px;
                    width: 200px;
                }
                .page-form {
                    direction: rtl;
                    text-align: right;
                    margin-right: 150px;
                    justify-content: space-around;
                }
                .select-icon {
                    display: none; /* Hide the default icon if needed */
                }
                .dt-cell__content {
                    border-bottom: 1px darkred solid;
                    border-left: 1px darkred solid;
					text-align: center;
                }
            </style>
        `;
        $('head').append(customStyles);

        this.initializeFilters(report);
    },

	"filters": [
        {
            "fieldname": "customer",
            "label": __("اسم العميل"),
            "fieldtype": "Link",
            "width": "250",
            options: "Customer Mapping"
        },
		{
			"fieldname":"from_date",
			"label": __("من"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("الي"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
        
	],
    initializeFilters: function(report) {
        const from_date_filter = report.get_filter('from_date');
        const to_date_filter = report.get_filter('to_date');

        if (from_date_filter) {
            from_date_filter.$wrapper.find('label').text('من تاريخ:');
        }
        if (to_date_filter) {
            to_date_filter.$wrapper.find('label').text('إلى تاريخ:');
        }
    },
};
