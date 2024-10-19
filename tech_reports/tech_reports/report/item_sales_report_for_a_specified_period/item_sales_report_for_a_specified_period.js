// Copyright (c) 2024, omneyaeid827@gmail.com and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Sales Report for a Specified Period"] = {
	onload: function(report) {
        const customTitle = `
        <div class="custom-report-title" style="margin-top: 20px;">
            <div>
                <h1 style="color: darkred;text-align: center;">تقرير عن مبيعات الاصناف لصنف خلال فتره</h1>
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
        $('head').append(customStyles); // Add styles to the head of the document
        
        this.initializeFilters(report);
        // Call the function to modify the total row
        this.modifyTotalRow();
    },

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

    "filters": [
        {
            "fieldname": "item",
            "label": __("الصنف"),
            "width": "250",
            "fieldtype": "Link",
			"options": "Item",
        },
        {
            "fieldname": "from_date",
            "label": __("من"),
            "fieldtype": "Date",
            "width": "150",
            "reqd": 1,
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
        },
        {
            "fieldname": "to_date",
            "label": __("إلى"),
            "fieldtype": "Date",
            "width": "150",
            "reqd": 1,
            "default": frappe.datetime.get_today()
        }
    ],
	'formatter': function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.bold) {
			value = value.bold();
		}
		return value;
	}
};

function color_single_row(table_instance, rowIdx, color) {
	// Check if the current row is the total row
	if (table_instance.datamanager.data[rowIdx].is_total) { // Assuming `is_total` is a property that identifies the total row
		// Iterate over all columns in the row
		for (let col = 0; col < Object.entries(table_instance.datamanager.data[rowIdx]).length; col++) {
			// Set the background color for each cell in the total row
			table_instance.style.setStyle(`.dt-cell--${col}-${rowIdx}`, { backgroundColor: `${color} !important` });
		}
	}
}
