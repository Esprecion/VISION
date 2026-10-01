import frappe


def execute():
    frappe.db.sql(
        "UPDATE `tabExpense` SET category = 'Tools and Subscriptions' WHERE category = 'Infrastructure'"
    )
