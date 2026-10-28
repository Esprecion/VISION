import re

import frappe

from my_custom_app.admin_roles import (
	ALLOWED_ROLES,
	PROTECTED_USERS,
	SYSTEM_ADMIN_ROLE,
	_placeholder_email,
)

PROTECTED_USER_NAMES = {user.lower() for user in PROTECTED_USERS}

REQUIRED_DETAILS_MESSAGE = "Please complete all required user details."
DUPLICATE_NAME_MESSAGE = "This account name is already taken."
INVALID_ROLE_MESSAGE = "Please choose a valid role."
CREATE_FAILED_MESSAGE = "Unable to create user. Please try again."


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


@frappe.whitelist()
def create_user(account_name=None, password=None, role=None):
	"""Create an administration user with exactly one managed role."""
	_require_system_admin()

	account_name = (account_name or "").strip()
	password = password or ""
	role = (role or "").strip()

	missing = []
	if not account_name:
		missing.append("account_name")
	if not password:
		missing.append("password")
	if not role:
		missing.append("role")
	if missing:
		return _error(missing[0], REQUIRED_DETAILS_MESSAGE, missing)

	if role not in ALLOWED_ROLES or not frappe.db.exists("Role", role):
		return _error("role", INVALID_ROLE_MESSAGE, ["role"])

	if _account_name_taken(account_name):
		return _error("account_name", DUPLICATE_NAME_MESSAGE, ["account_name"])

	email = _placeholder_email(account_name)
	password_message = _password_problem(account_name, email, password)
	if password_message:
		return _error("password", password_message, ["password"])

	try:
		doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": account_name,
				"username": account_name,
				"send_welcome_email": 0,
				"enabled": 1,
				"user_type": "System User",
				"roles": [{"role": role}],
				"new_password": password,
			}
		)
		doc.insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		return _error("account_name", DUPLICATE_NAME_MESSAGE, ["account_name"])
	except frappe.ValidationError as error:
		if _last_error_title().lower() == "password requirements not met":
			return _error("password", _password_message(str(error)), ["password"])
		return _error(None, _clean_message(str(error)) or CREATE_FAILED_MESSAGE)
	except Exception as error:
		frappe.log_error(
			message=f"create_user failed ({type(error).__name__})",
			title="Administration: create user",
		)
		return _error(None, CREATE_FAILED_MESSAGE)

	return {
		"ok": True,
		"message": "User Created",
		"user": {
			"account_name": doc.username,
			"role": role,
			"has_extra_roles": False,
		},
	}


def _error(field, message, fields=None):
	return {
		"ok": False,
		"field": field,
		"fields": list(fields) if fields else ([field] if field else []),
		"message": message,
	}


def _account_name_taken(account_name):
	if account_name.lower() in PROTECTED_USER_NAMES:
		return True
	return bool(frappe.db.exists("User", {"username": account_name}))


def _password_problem(account_name, email, password):
	try:
		from frappe.core.doctype.user.user import test_password_strength

		result = (
			test_password_strength(
				new_password=password,
				user_data=(account_name, "", "", email, None),
			)
			or {}
		)
	except Exception:
		return None

	feedback = result.get("feedback") or {}
	if feedback and not feedback.get("password_policy_validation_passed", False):
		return _password_message(_password_feedback_text(feedback))
	return None


def _password_feedback_text(feedback):
	parts = []
	warning = _clean_message(feedback.get("warning") or "")
	if warning:
		parts.append(warning)
	for suggestion in feedback.get("suggestions") or []:
		text = _clean_message(suggestion)
		if text:
			parts.append(text)
	return " ".join(parts)


def _password_message(detail):
	detail = _clean_message(detail)
	if detail.lower().startswith("password requirements not met"):
		return detail
	if detail:
		return f"Password requirements not met. {detail}"
	return "Password requirements not met. Please choose a stronger password."


def _clean_message(message):
	text = re.sub(r"<[^>]*>", " ", str(message or ""))
	return re.sub(r"\s+", " ", text).strip()


def _last_error_title():
	for message in reversed(getattr(frappe.local, "message_log", None) or []):
		title = message.get("title") if isinstance(message, dict) else None
		if title:
			return title
	return ""


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
