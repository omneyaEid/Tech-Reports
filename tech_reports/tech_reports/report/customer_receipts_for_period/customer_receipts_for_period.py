import frappe
from frappe import _, scrub
from frappe.utils import getdate, nowdate


class PartyLedgerSummaryReport(object):
    def __init__(self, filters=None):
        self.filters = frappe._dict(filters or {})
        self.filters.from_date = getdate(self.filters.from_date or nowdate())
        self.filters.to_date = getdate(self.filters.to_date or nowdate())

        if not self.filters.get("company"):
            self.filters["company"] = frappe.db.get_single_value("Global Defaults", "default_company")

        self.territories = frappe._dict({})

    def run(self, args):
        if self.filters.from_date > self.filters.to_date:
            frappe.throw(_("From Date must be before To Date"))

        self.filters.party_type = args.get("party_type")
        self.party_naming_by = frappe.db.get_value(
            args.get("naming_by")[0], None, args.get("naming_by")[1]
        )

        self.get_gl_entries()
        self.get_return_invoices()
        self.get_party_adjustment_amounts()

        columns = self.get_columns()
        data = self.get_data()
        return columns, data

    def get_columns(self):
        columns = [
            {
                "label": "اسم العميل",  
                "fieldtype": "Data", 
                "fieldname": "customer_name", 
                "width": 500,
            },
            {
                "label": "التاريخ",  
                "fieldtype": "Date", 
                "fieldname": "posting_date", 
                "width": 200,
            },
            {
                "label": "التحصيل",  # Paid Amount
                "fieldname": "paid_amount",
                "fieldtype": "Currency",
                "options": "currency",
                "width": 500,
            },
        ]
        return columns

    def get_gl_entries(self):
        conditions = self.prepare_conditions()
        join = join_field = ""
        
        if self.filters.party_type == "Customer":
            join_field = ", cm.customer_name as party_name"  # Fetch customer_name from Customer Mapping
            join = """
                LEFT JOIN `tabCustomer Mapping` cm ON gle.party = cm.customer_code
            """  # Join with Customer Mapping to get the customer_name

        self.gl_entries = frappe.db.sql(
            """
            SELECT
                gle.posting_date,
                cm.customer_name as party,  # Use customer_name instead of party (customer code)
                gle.voucher_type,
                gle.voucher_no,
                gle.against_voucher_type,
                gle.against_voucher,
                gle.debit,
                gle.credit,
                gle.is_opening {join_field}
            FROM
                `tabGL Entry` gle
            {join}
            WHERE
                gle.docstatus < 2
                AND gle.is_cancelled = 0
                AND gle.party_type = %(party_type)s
                AND IFNULL(gle.party, '') != ''
                AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s  # Updated filter
                {conditions}
            ORDER BY
                gle.posting_date
            """.format(
                join=join,
                join_field=join_field,
                conditions=conditions
            ),
            self.filters,
            as_dict=True,
        )

    def get_data(self):
        company_currency = frappe.get_cached_value(
            "Company", self.filters.get("company"), "default_currency"
        )
        invoice_dr_or_cr = "debit" if self.filters.party_type == "Customer" else "credit"
        reverse_dr_or_cr = "credit" if self.filters.party_type == "Customer" else "debit"

        self.party_data = frappe._dict({})
        for gle in self.gl_entries:
            # Ensure posting_date is formatted correctly
            posting_date = getdate(gle.posting_date).strftime('%Y-%m-%d') if gle.posting_date else None
            
            self.party_data.setdefault(
                gle.party,
                frappe._dict(
                    {
                        "customer_name": gle.party_name,  # Updated to show customer_name
                        "posting_date": posting_date,  # Added posting date
                        "opening_balance": 0,
                        "invoiced_amount": 0,
                        "paid_amount": 0,
                        "return_amount": 0,
                        "closing_balance": 0,
                        "currency": company_currency,
                    }
                ),
            )

            amount = gle.get(invoice_dr_or_cr) - gle.get(reverse_dr_or_cr)
            self.party_data[gle.party].closing_balance += amount

            if gle.posting_date < self.filters.from_date or gle.is_opening == "Yes":
                self.party_data[gle.party].opening_balance += amount
            else:
                if amount > 0:
                    self.party_data[gle.party].invoiced_amount += amount
                elif gle.voucher_no in self.return_invoices:
                    self.party_data[gle.party].return_amount -= amount
                else:
                    self.party_data[gle.party].paid_amount -= amount

        out = []
        for party, row in self.party_data.items():
            if (
                row.opening_balance
                or row.invoiced_amount
                or row.paid_amount
                or row.return_amount
                or row.closing_balance
            ):
                total_party_adjustment = sum(
                    amount for amount in self.party_adjustment_details.get(party, {}).values()
                )
                row.paid_amount -= total_party_adjustment

                adjustments = self.party_adjustment_details.get(party, {})
                for account in self.party_adjustment_accounts:
                    row["adj_" + scrub(account)] = adjustments.get(account, 0)

                out.append(row)

        return out

    def prepare_conditions(self):
        conditions = [""]

        if self.filters.company:
            conditions.append("gle.company=%(company)s")

        if self.filters.finance_book:
            conditions.append("ifnull(finance_book,'') in (%(finance_book)s, '')")

        if self.filters.get("customer"):
            conditions.append("cm.customer_name=%(customer)s")

        return " and ".join(conditions)

    def get_return_invoices(self):
        self.return_invoices = frappe._dict(
            frappe.db.sql_list(
                """
                SELECT name FROM `tabSales Invoice`
                WHERE docstatus=1 AND is_return=1 AND posting_date >= %(from_date)s
                """,
                self.filters,
            )
        )

    def get_party_adjustment_amounts(self):
        self.party_adjustment_accounts = []
        self.party_adjustment_details = frappe._dict({})


def execute(filters=None):
    args = {
        "party_type": "Customer",
        "naming_by": ["Selling Settings", "cust_master_name"],
    }
    return PartyLedgerSummaryReport(filters).run(args)
