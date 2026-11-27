import frappe

# Dev helper: creates the 4 Finance Query Reports. Safe to re-run.

AR_QUERY = """
SELECT inv.name AS `Invoice:Link/Invoice:120`,
       inv.client AS `Client:Link/Client:200`,
       GREATEST(COALESCE(inv.amount, 0) - COALESCE(pay.paid, 0), 0) AS `Amount:Currency:130`,
       inv.due_date AS `Due Date:Date:110`,
       inv.status AS `Status:Data:90`,
       COALESCE(DATEDIFF(%(as_of)s, inv.due_date), 0) AS `Days Overdue:Int:110`
FROM `tabInvoice` inv
LEFT JOIN (
    SELECT invoice, SUM(amount) AS paid
    FROM `tabClient Payment`
    WHERE payment_date <= %(as_of)s
    GROUP BY invoice
) pay ON pay.invoice = inv.name
WHERE (inv.issue_date IS NULL OR inv.issue_date <= %(as_of)s)
  AND GREATEST(COALESCE(inv.amount, 0) - COALESCE(pay.paid, 0), 0) > 0
ORDER BY `Days Overdue:Int:110` DESC
"""

REPORT_FILTERS = {
	"Accounts Receivable Aging": [
		{"fieldname": "as_of", "label": "As Of", "fieldtype": "Date", "reqd": 1},
	],
}

REPORTS = [
	(
		"Revenue per Client",
		"Invoice",
		"""
SELECT client AS `Client:Link/Client:220`,
       SUM(paid_amount) AS `Total Paid Revenue:Currency:160`,
       COUNT(*) AS `Paid Invoices:Int:120`
FROM `tabInvoice`
WHERE paid_amount > 0
GROUP BY client
ORDER BY `Total Paid Revenue:Currency:160` DESC
""",
	),
	("Accounts Receivable Aging", "Invoice", AR_QUERY),
	(
		"Net Burn Rate",
		"Invoice",
		"""
SELECT m.month AS `Month:Data:100`,
       COALESCE(r.revenue, 0) AS `Revenue:Currency:140`,
       COALESCE(e.expense, 0) AS `Expenses:Currency:140`,
       COALESCE(e.expense, 0) - COALESCE(r.revenue, 0) AS `Net Burn:Currency:140`
FROM (
    SELECT DISTINCT DATE_FORMAT(issue_date, '%Y-%m') AS month FROM `tabInvoice`
    UNION
    SELECT DISTINCT DATE_FORMAT(expense_date, '%Y-%m') FROM `tabExpense`
) m
LEFT JOIN (
    SELECT DATE_FORMAT(issue_date, '%Y-%m') AS month, SUM(paid_amount) AS revenue
    FROM `tabInvoice` WHERE paid_amount > 0 GROUP BY DATE_FORMAT(issue_date, '%Y-%m')
) r ON r.month = m.month
LEFT JOIN (
    SELECT DATE_FORMAT(expense_date, '%Y-%m') AS month, SUM(amount) AS expense
    FROM `tabExpense` GROUP BY DATE_FORMAT(expense_date, '%Y-%m')
) e ON e.month = m.month
ORDER BY m.month
""",
	),
	(
		"Total Revenue by Period",
		"Invoice",
		"""
SELECT CONCAT(YEAR(issue_date), '-', LPAD(MONTH(issue_date), 2, '0')) AS `Month:Data:100`,
       SUM(paid_amount) AS `Total Paid Revenue:Currency:160`,
       COUNT(*) AS `Paid Invoices:Int:120`
FROM `tabInvoice`
WHERE status = 'Paid'
GROUP BY YEAR(issue_date), MONTH(issue_date)
ORDER BY YEAR(issue_date), MONTH(issue_date)
""",
	),
]


def run():
	for name, ref, query in REPORTS:
		if frappe.db.exists("Report", name):
			print("exists:", name)
			continue
		frappe.get_doc(
			{
				"doctype": "Report",
				"report_name": name,
				"ref_doctype": ref,
				"report_type": "Query Report",
				"is_standard": "No",
				"module": "Finance",
				"query": query.strip(),
				"filters": REPORT_FILTERS.get(name, []),
				"roles": [{"role": "System Manager"}, {"role": "CBO"}, {"role": "COO"}, {"role": "CFO"}],
			}
		).insert(ignore_permissions=True)
		print("created:", name)
	frappe.db.commit()
