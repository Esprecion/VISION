import frappe

QUERY = """SELECT p.name AS `Project:Link/Project:150`,
       p.client AS `Client:Link/Client:180`,
       COALESCE(r.revenue, 0) AS `Revenue:Currency:140`,
       COALESCE(e.expense, 0) AS `Expenses:Currency:140`,
       COALESCE(r.revenue, 0) - COALESCE(e.expense, 0) AS `Net:Currency:140`,
       IF(COALESCE(r.revenue, 0) = 0, 0,
          ROUND((r.revenue - COALESCE(e.expense, 0)) / r.revenue * 100, 1)) AS `Margin Pct:Percent:100`
FROM `tabProject` p
LEFT JOIN (
    SELECT contract, SUM(amount) AS revenue
    FROM `tabInvoice`
    WHERE status = 'Paid' AND issue_date BETWEEN %(from_date)s AND %(to_date)s
    GROUP BY contract
) r ON r.contract = p.contract
LEFT JOIN (
    SELECT project, SUM(amount) AS expense
    FROM `tabExpense`
    WHERE expense_date BETWEEN %(from_date)s AND %(to_date)s
    GROUP BY project
) e ON e.project = p.name
WHERE r.revenue IS NOT NULL OR e.expense IS NOT NULL

UNION ALL

SELECT 'Unassigned / Overhead', NULL, 0, SUM(amount), -SUM(amount), 0
FROM `tabExpense`
WHERE (project IS NULL OR project = '')
  AND expense_date BETWEEN %(from_date)s AND %(to_date)s
HAVING COUNT(*) > 0

UNION ALL

SELECT 'COMPANY TOTAL', NULL,
  (SELECT COALESCE(SUM(amount), 0) FROM `tabInvoice`
    WHERE status = 'Paid' AND issue_date BETWEEN %(from_date)s AND %(to_date)s),
  (SELECT COALESCE(SUM(amount), 0) FROM `tabExpense`
    WHERE expense_date BETWEEN %(from_date)s AND %(to_date)s),
  (SELECT COALESCE(SUM(amount), 0) FROM `tabInvoice`
    WHERE status = 'Paid' AND issue_date BETWEEN %(from_date)s AND %(to_date)s)
  - (SELECT COALESCE(SUM(amount), 0) FROM `tabExpense`
    WHERE expense_date BETWEEN %(from_date)s AND %(to_date)s),
  0"""

NAME = "Project Profitability"


def execute():
    if frappe.db.exists("Report", NAME):
        frappe.db.set_value("Report", NAME, "query", QUERY)
        return
    frappe.get_doc({
        "doctype": "Report",
        "report_name": NAME,
        "ref_doctype": "Invoice",
        "report_type": "Query Report",
        "is_standard": "No",
        "module": frappe.db.get_value("DocType", "Invoice", "module"),
        "query": QUERY,
        "roles": [{"role": "CFO"}, {"role": "System Manager"}],
    }).insert(ignore_permissions=True)
