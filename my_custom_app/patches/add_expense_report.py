import frappe

NAME = "Expense by Category"
QUERY = """
SELECT e.category AS `Category:Data:160`,
       COALESCE(NULLIF(i.vendor, ''), '(no vendor)') AS `Vendor:Data:200`,
       SUM(i.amount) AS `Amount:Currency:140`
FROM `tabExpense` e
JOIN `tabExpense Item` i ON i.parent = e.name AND i.parenttype = 'Expense'
WHERE e.expense_date BETWEEN %(from_date)s AND %(to_date)s
GROUP BY e.category, i.vendor
ORDER BY e.category, SUM(i.amount) DESC
""".strip()


def execute():
    if frappe.db.exists("Report", NAME):
        doc = frappe.get_doc("Report", NAME)
        doc.query = QUERY
        doc.save(ignore_permissions=True)
        return
    frappe.get_doc({
        "doctype": "Report",
        "report_name": NAME,
        "ref_doctype": "Expense",
        "report_type": "Query Report",
        "is_standard": "No",
        "module": "Finance",
        "query": QUERY,
        "roles": [{"role": "System Manager"}, {"role": "CBO"}, {"role": "COO"}, {"role": "CFO"}],
    }).insert(ignore_permissions=True)
