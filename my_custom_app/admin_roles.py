import os
import re

import frappe

ALLOWED_ROLES = ("System Admin", "COO", "CFO", "CTO", "CBO")

SYSTEM_ADMIN_ROLE = "System Admin"
PROTECTED_USERS = ("Administrator", "Guest")


def ensure_roles():
	"""Create every allowed role if it does not exist yet."""
	for role in ALLOWED_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc(
				{
					"doctype": "Role",
					"role_name": role,
					"desk_access": 1,
				}
			).insert(ignore_permissions=True)


def seed_first_admin():
	"""Create the first System Admin from environment variables.

	Run with:
		VISION_ADMIN_USERNAME=sysadmin01 VISION_ADMIN_PASSWORD=... \
			bench --site site1.local execute my_custom_app.admin_roles.seed_first_admin
	"""
	account_name = (os.environ.get("VISION_ADMIN_USERNAME") or "").strip()
	password = os.environ.get("VISION_ADMIN_PASSWORD") or ""

	if not account_name or not password:
		frappe.throw("Set VISION_ADMIN_USERNAME and VISION_ADMIN_PASSWORD before running this.")

	ensure_roles()

	existing = frappe.db.get_value("User", {"username": account_name}, "name")
	if existing:
		print(f"A user with account name '{account_name}' already exists: {existing}")
		return existing

	if account_name.lower() in {user.lower() for user in PROTECTED_USERS}:
		frappe.throw("That account name is not available.")

	email = _placeholder_email(account_name)
	doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": account_name,
			"username": account_name,
			"send_welcome_email": 0,
			"enabled": 1,
			"user_type": "System User",
			"roles": [{"role": SYSTEM_ADMIN_ROLE}],
			"new_password": password,
		}
	)
	doc.insert(ignore_permissions=True)
	print(f"Created System Admin account '{account_name}'.")
	return doc.name


def _placeholder_email(account_name):
	"""Build a unique internal email; users log in with their account name."""
	local = re.sub(r"[^a-z0-9._-]+", "-", account_name.lower()).strip("-._") or "user"
	email = f"{local}@vision.local"
	suffix = 1
	while frappe.db.exists("User", email):
		email = f"{local}{suffix}@vision.local"
		suffix += 1
	return email
