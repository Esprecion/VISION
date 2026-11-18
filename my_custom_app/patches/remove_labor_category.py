import frappe


def execute():
	frappe.db.sql("UPDATE `tabExpense` SET category = 'Contractors and Freelancers' WHERE category = 'Labor'")
