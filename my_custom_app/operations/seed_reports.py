import frappe

# Dev helper: creates the 5 Operations Query Reports. Safe to re-run.

REPORTS = [
    ("On-time Delivery Rate", "Project", """
SELECT COUNT(*) AS `Delivered:Int:100`,
       SUM(actual_delivery_date <= committed_date) AS `On Time:Int:100`,
       ROUND(100 * SUM(actual_delivery_date <= committed_date) / COUNT(*), 1) AS `On-time Rate (pct):Float:130`
FROM `tabProject`
WHERE actual_delivery_date IS NOT NULL
"""),
    ("Average Project Cycle Time", "Project", """
SELECT COUNT(*) AS `Delivered Projects:Int:140`,
       ROUND(AVG(DATEDIFF(actual_delivery_date, start_date)), 1) AS `Avg Cycle Time (days):Float:160`
FROM `tabProject`
WHERE actual_delivery_date IS NOT NULL AND start_date IS NOT NULL
"""),
    ("Active Client Count", "Project", """
SELECT project_type AS `Project Type:Data:180`,
       COUNT(DISTINCT client) AS `Active Clients:Int:120`
FROM `tabProject`
WHERE stage != 'Deployed'
GROUP BY project_type
ORDER BY `Active Clients:Int:120` DESC
"""),
    ("Average Client Tenure", "Service Contract", """
SELECT client AS `Client:Link/Client:220`,
       MIN(start_date) AS `First Contract:Date:130`,
       DATEDIFF(CURDATE(), MIN(start_date)) AS `Tenure (days):Int:120`
FROM `tabService Contract`
WHERE start_date <= CURDATE()
GROUP BY client
ORDER BY `Tenure (days):Int:120` DESC
"""),
    ("Tool and API Cost Trend", "Tool Subscription", """
SELECT CONCAT(YEAR(month), '-', LPAD(MONTH(month), 2, '0')) AS `Month:Data:100`,
       SUM(amount) AS `Total Monthly Cost:Currency:160`
FROM `tabTool Cost Entry`
WHERE parent IN (SELECT name FROM `tabTool Subscription` WHERE billing_cycle = 'Monthly')
GROUP BY YEAR(month), MONTH(month)
ORDER BY YEAR(month), MONTH(month)
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
            "module": "Operations",
            "query": query.strip(),
            "roles": [{"role": "System Manager"}],
        }).insert(ignore_permissions=True)
        print("created:", name)
    frappe.db.commit()
