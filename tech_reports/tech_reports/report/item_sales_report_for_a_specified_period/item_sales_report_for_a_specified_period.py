# Copyright (c) 2024, omneyaeid827@gmail.com and contributors
# For license information, please see license.txt


import copy
from collections import OrderedDict

import frappe
from frappe import _, qb
from frappe.query_builder import CustomFunction
from frappe.query_builder.functions import Max
from frappe.utils import date_diff, flt, getdate


def execute(filters=None):
	if not filters:
		return [], [], None, []

	validate_filters(filters)

	columns = get_columns(filters)
	conditions = get_conditions(filters)
	data = get_data(conditions, filters)

	if not data:
		return [], [], None, []

	data = prepare_data(data, filters)

	return columns, data, None, None


def validate_filters(filters):
	from_date, to_date = filters.get("from_date"), filters.get("to_date")

	if not from_date and to_date:
		frappe.throw(_("From and To Dates are required."))
	elif date_diff(to_date, from_date) < 0:
		frappe.throw(_("To Date cannot be before From Date."))


def get_conditions(filters):
	conditions = ""
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and so.transaction_date between %(from_date)s and %(to_date)s"

	if filters.get("item"):
		conditions += " and soi.item_code = %(item)s"

	return conditions


def get_data(conditions, filters):
    data = frappe.db.sql(
        """
        SELECT
            so.transaction_date as date,
            soi.delivery_date as delivery_date,
            so.name as sales_order,
            so.status, 
            cu.customer_name, 
            soi.item_code,
            DATEDIFF(CURRENT_DATE, soi.delivery_date) as delay_days,
            soi.qty, 
            soi.delivered_qty,
            (soi.qty - soi.delivered_qty) AS pending_qty,
            IFNULL(SUM(sii.qty), 0) as billed_qty,
            soi.base_amount as amount,
            so.company, 
            soi.name as soi_name,
            iv.attribute_value as grade  
        FROM
            `tabSales Order` so
        JOIN `tabSales Order Item` soi ON soi.parent = so.name
        LEFT JOIN `tabCustomer Mapping` cu ON cu.customer_code = so.customer 
        LEFT JOIN `tabSales Invoice Item` sii ON sii.so_detail = soi.name AND sii.docstatus = 1
        LEFT JOIN `tabItem Variant Attribute` iv ON iv.parent = soi.item_code AND iv.attribute = 'الدرجة' 
        WHERE
            so.status NOT IN ('Stopped', 'Closed', 'On Hold')
            AND so.docstatus = 1
            {conditions}
        GROUP BY soi.name
        ORDER BY so.transaction_date ASC, soi.item_code ASC
        """.format(
            conditions=conditions
        ),
        filters,
        as_dict=1,
    )

    return data


def get_so_elapsed_time(data):
	"""
	query SO's elapsed time till latest delivery note
	"""
	so_elapsed_time = OrderedDict()
	if data:
		sales_orders = [x.sales_order for x in data]

		so = qb.DocType("Sales Order")
		soi = qb.DocType("Sales Order Item")
		dn = qb.DocType("Delivery Note")
		dni = qb.DocType("Delivery Note Item")

		to_seconds = CustomFunction("TO_SECONDS", ["date"])

		query = (
			qb.from_(so)
			.inner_join(soi)
			.on(soi.parent == so.name)
			.left_join(dni)
			.on(dni.so_detail == soi.name)
			.left_join(dn)
			.on(dni.parent == dn.name)
			.select(
				so.name.as_("sales_order"),
				soi.item_code.as_("so_item_code"),
				(to_seconds(Max(dn.posting_date)) - to_seconds(so.transaction_date)).as_("elapsed_seconds"),
			)
			.where((so.name.isin(sales_orders)) & (dn.docstatus == 1))
			.orderby(so.name, soi.name)
			.groupby(soi.name)
		)
		dn_elapsed_time = query.run(as_dict=True)

		for e in dn_elapsed_time:
			key = (e.sales_order, e.so_item_code)
			so_elapsed_time[key] = e.elapsed_seconds

	return so_elapsed_time


def prepare_data(data, filters):
	completed, pending = 0, 0

	# for row in data:
	# 	# sum data for chart
	# 	pending += row["pending_amount"]

	return data



def get_columns(filters):
	columns = [
		{
			"label": _("اسم العميل"),
			"fieldname": "customer_name",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 300,
		},
		{
			"label": _("الصنف"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 400,
		},
		{
			"label": _("الصناديق"),
			"fieldname": "boxs",
			"fieldtype": "Data",
			"width": 250,
		},
		{
			"label": _("الكمية"),
			"fieldname": "qty",
			"fieldtype": "Float",
			"width": 250,
			"convertible": "qty",
		},
		{
			"label": _("الدرجة"),
			"fieldname": "grade",
			"fieldtype": "Data",
			"width": 250,
		},
	]

	return columns
