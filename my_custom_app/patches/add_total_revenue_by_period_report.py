import frappe

NAME = "Total Revenue by Period"
QUERY = """
SELECT CONCAT(YEAR(issue_date), '-', LPAD(MONTH(issue_date), 2, '0')) AS `Month:Data:100`,
       SUM(paid_amount) AS `Total Paid Revenue:Currency:160`,
       COUNT(*) AS `Paid Invoices:Int:120`
FROM `tabInvoice`
WHERE status = 'Paid'
  AND issue_date BETWEEN %(from_date)s AND %(to_date)s
GROUP BY YEAR(issue_date), MONTH(issue_date)
ORDER BY YEAR(issue_date), MONTH(issue_date)
""".strip()


def execute():
	if frappe.db.exists("Report", NAME):
		doc = frappe.get_doc("Report", NAME)
		doc.query = QUERY
		doc.save(ignore_permissions=True)
		return
	frappe.get_doc(
		{
			"doctype": "Report",
			"report_name": NAME,
			"ref_doctype": "Invoice",
			"report_type": "Query Report",
			"is_standard": "No",
			"module": "Finance",
			"query": QUERY,
			"roles": [{"role": "System Manager"}, {"role": "CBO"}, {"role": "COO"}, {"role": "CFO"}],
		}
	).insert(ignore_permissions=True)
