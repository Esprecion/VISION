import frappe


def execute():
	"""Allow users to sign in with their account name instead of only email."""
	frappe.db.set_single_value("System Settings", "allow_login_using_user_name", 1)
	frappe.clear_cache()
