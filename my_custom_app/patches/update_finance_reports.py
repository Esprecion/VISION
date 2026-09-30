import frappe

REVENUE = """SELECT client AS `Client:Link/Client:220`,
       SUM(amount) AS `Total Paid Revenue:Currency:160`,
       COUNT(*) AS `Paid Invoices:Int:120`
FROM `tabInvoice`
WHERE status = 'Paid'
  AND issue_date BETWEEN %(from_date)s AND %(to_date)s
GROUP BY client
ORDER BY `Total Paid Revenue:Currency:160` DESC"""

BURN = """SELECT m.month AS `Month:Data:100`,
       COALESCE(r.revenue, 0) AS `Revenue:Currency:140`,
       COALESCE(e.expense, 0) AS `Expenses:Currency:140`,
       COALESCE(e.expense, 0) - COALESCE(r.revenue, 0) AS `Net Burn:Currency:140`
FROM (
    SELECT DISTINCT CONCAT(YEAR(issue_date), '-', LPAD(MONTH(issue_date), 2, '0')) AS month
    FROM `tabInvoice`
    WHERE issue_date BETWEEN %(from_date)s AND %(to_date)s
    UNION
    SELECT DISTINCT CONCAT(YEAR(expense_date), '-', LPAD(MONTH(expense_date), 2, '0'))
    FROM `tabExpense`
    WHERE expense_date BETWEEN %(from_date)s AND %(to_date)s
) m
LEFT JOIN (
    SELECT CONCAT(YEAR(issue_date), '-', LPAD(MONTH(issue_date), 2, '0')) AS month, SUM(amount) AS revenue
    FROM `tabInvoice`
    WHERE status = 'Paid' AND issue_date BETWEEN %(from_date)s AND %(to_date)s
    GROUP BY month
) r ON r.month = m.month
LEFT JOIN (
    SELECT CONCAT(YEAR(expense_date), '-', LPAD(MONTH(expense_date), 2, '0')) AS month, SUM(amount) AS expense
    FROM `tabExpense`
    WHERE expense_date BETWEEN %(from_date)s AND %(to_date)s
    GROUP BY month
) e ON e.month = m.month
ORDER BY m.month"""


def execute():
    for name, q in (("Revenue per Client", REVENUE), ("Net Burn Rate", BURN)):
        if frappe.db.exists("Report", name):
            frappe.db.set_value("Report", name, "query", q)
