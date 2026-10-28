import frappe

from my_custom_app.admin_roles import ALLOWED_ROLES, PROTECTED_USERS, SYSTEM_ADMIN_ROLE

PROTECTED_USER_NAMES = {user.lower() for user in PROTECTED_USERS}


@frappe.whitelist()
def list_users():
	"""Return every non-protected user with at least one managed role."""
	_require_system_admin()

	try:
		return _load_users()
	except Exception:
		frappe.log_error(message=frappe.get_traceback(), title="Administration: list users")
		frappe.throw("Unable to load users. Please try again.")


@frappe.whitelist()
def get_user(account_name):
	"""Return the account name and managed role for one user."""
	_require_system_admin()

	try:
		return _load_user(account_name)
	except frappe.DoesNotExistError:
		raise
	except Exception:
		frappe.log_error(message=frappe.get_traceback(), title="Administration: get user")
		frappe.throw("Unable to load user. Please try again.")


def _require_system_admin():
	if frappe.session.user == "Administrator":
		return
	if SYSTEM_ADMIN_ROLE not in frappe.get_roles(frappe.session.user):
		frappe.throw("Not permitted", frappe.PermissionError)


def _load_users():
	parents = frappe.get_all(
		"Has Role",
		filters={"parenttype": "User", "role": ("in", ALLOWED_ROLES)},
		pluck="parent",
		distinct=True,
	)
	parents = [name for name in parents if (name or "").lower() not in PROTECTED_USER_NAMES]
	if not parents:
		return []

	role_rows = frappe.get_all(
		"Has Role",
		filters={"parenttype": "User", "parent": ("in", parents)},
		fields=["parent", "role"],
		order_by="idx asc",
	)
	users = frappe.get_all(
		"User",
		filters={"name": ("in", parents)},
		fields=["name", "username"],
	)

	roles_by_user = {}
	for row in role_rows:
		roles_by_user.setdefault(row.parent, []).append(row.role)

	users_by_name = {user.name: user for user in users}
	items = []
	for account_name in parents:
		user = users_by_name.get(account_name)
		if not user or (user.username or "").lower() in PROTECTED_USER_NAMES:
			continue

		roles = roles_by_user.get(account_name, [])
		managed_roles = [role for role in roles if role in ALLOWED_ROLES]
		if not managed_roles:
			continue

		items.append(
			{
				"account_name": user.username or user.name,
				"role": managed_roles[0],
				"has_extra_roles": len(roles) > 1,
			}
		)

	items.sort(key=lambda item: item["account_name"].lower())
	return items


def _load_user(account_name):
	account_name = (account_name or "").strip()
	if not account_name or account_name.lower() in PROTECTED_USER_NAMES:
		frappe.throw("User not found", frappe.DoesNotExistError)

	user = frappe.db.get_value(
		"User",
		{"username": account_name},
		["name", "username"],
		as_dict=True,
	)
	if not user:
		user = frappe.db.get_value("User", account_name, ["name", "username"], as_dict=True)

	if not user or (user.name or "").lower() in PROTECTED_USER_NAMES:
		frappe.throw("User not found", frappe.DoesNotExistError)

	roles = frappe.get_all(
		"Has Role",
		filters={"parenttype": "User", "parent": user.name},
		pluck="role",
		order_by="idx asc",
	)
	managed_roles = [role for role in roles if role in ALLOWED_ROLES]
	if not managed_roles:
		frappe.throw("User not found", frappe.DoesNotExistError)

	return {
		"account_name": user.username or user.name,
		"role": managed_roles[0],
		"has_extra_roles": len(roles) > 1,
	}
