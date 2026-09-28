import frappe

# Dev helper: creates the 3 Finance Query Reports. Safe to re-run.

REPORTS = [
    ("Revenue per Client", "Invoice", """
SELECT client AS `Client:Link/Client:220`,
       SUM(amount) AS `Total Paid Revenue:Currency:160`,
       COUNT(*) AS `Paid Invoices:Int:120`
FROM `tabInvoice`
WHERE status = 'Paid'
GROUP BY client
ORDER BY `Total Paid Revenue:Currency:160` DESC
"""),
    ("Accounts Receivable Aging", "Invoice", """
SELECT name AS `Invoice:Link/Invoice:120`,
       client AS `Client:Link/Client:200`,
       amount AS `Amount:Currency:130`,
       due_date AS `Due Date:Date:110`,
       status AS `Status:Data:90`,
       GREATEST(DATEDIFF(CURDATE(), due_date), 0) AS `Days Overdue:Int:110`
FROM `tabInvoice`
WHERE status IN ('Sent', 'Overdue')
ORDER BY `Days Overdue:Int:110` DESC
"""),
    ("Net Burn Rate", "Invoice", """
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
    SELECT DATE_FORMAT(issue_date, '%Y-%m') AS month, SUM(amount) AS revenue
    FROM `tabInvoice` WHERE status = 'Paid' GROUP BY DATE_FORMAT(issue_date, '%Y-%m')
) r ON r.month = m.month
LEFT JOIN (
    SELECT DATE_FORMAT(expense_date, '%Y-%m') AS month, SUM(amount) AS expense
    FROM `tabExpense` GROUP BY DATE_FORMAT(expense_date, '%Y-%m')
) e ON e.month = m.month
ORDER BY m.month
"""),
]


def run():
    for name, ref, query in REPORTS:
        if frappe.db.exists("Report", name):
            print("exists:", name)
            continue
        frappe.get_doc({
            "doctype": "Report",
            "report_name": name,
            "ref_doctype": ref,
            "report_type": "Query Report",
            "is_standard": "No",
            "module": "Finance",
            "query": query.strip(),
            "roles": [{"role": "System Manager"}],
        }).insert(ignore_permissions=True)
        print("created:", name)
    frappe.db.commit()
