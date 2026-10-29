# VISION Administration Panel

The Administration panel manages VISION user accounts without deleting Frappe users. It covers create, list, edit, deactivate, and reactivate flows for the account types used by the business.

## Access

- Route: `/admin/users` in the VISION frontend.
- Access is controlled by the server endpoint `my_custom_app.admin.can_manage_users`.
- Only users with the `System Admin` role can use the admin APIs.
- The sidebar link and the route guard both use the server check. Direct visits to `/admin/users` by non-admins redirect to `/dashboard`.
- `Administrator` and `Guest` are protected. They are never listed and cannot be created, edited, deactivated, or reactivated through this panel.

## Managed Roles

VISION manages exactly one of these roles per account:

- `System Admin`
- `COO`
- `CFO`
- `CTO`
- `CBO`

There is no CEO role; the founder is CEO and COO. `System Manager` is never granted by the Administration APIs.

When editing a user:

- The selected managed role replaces other managed roles.
- Unrelated roles are preserved.
- The table shows a small `Extra roles` note when `has_extra_roles` is true.

## First Admin Setup

Create the first `System Admin` from the bench environment:

```bash
VISION_ADMIN_USERNAME=sysadmin01 \
VISION_ADMIN_PASSWORD='replace-with-a-strong-password' \
bench --site site1.local execute my_custom_app.admin_roles.seed_first_admin
```

`seed_first_admin` is idempotent and does not print the password.

## Username Login

The `enable_username_login` patch sets `System Settings.allow_login_using_user_name`. Users sign in with their account name instead of the internal `@vision.local` email address.

The patch is listed in `my_custom_app/patches.txt` and is safe to run again.

## API Endpoints

All endpoints are in `my_custom_app.admin`.

| Endpoint | Purpose |
| --- | --- |
| `can_manage_users()` | Returns whether the current session can manage users. |
| `get_managed_roles()` | Returns the allowed managed roles. |
| `list_users()` | Returns all non-protected users with at least one managed role. |
| `get_user(account_name)` | Returns one managed user. |
| `create_user(account_name, password, role)` | Creates a user with one managed role. |
| `edit_user(account_name, role, password=None)` | Changes the managed role and optionally resets the password. |
| `deactivate_user(account_name)` | Disables the account and ends its active sessions. |
| `reactivate_user(account_name)` | Enables the account without changing roles. |

A user row has this shape:

```json
{
  "account_name": "juan.delacruz",
  "role": "COO",
  "roles": ["COO"],
  "has_extra_roles": false,
  "enabled": true
}
```

Success responses use:

```json
{ "ok": true, "message": "User Created", "user": { "...": "..." } }
```

Errors use:

```json
{ "ok": false, "field": "password", "fields": ["password"], "message": "Password requirements not met." }
```

## Safety Rules

- Nobody can deactivate or demote their own account.
- The last active `System Admin` cannot be deactivated or have their role changed.
- Deactivation never deletes the Frappe user record.
- Passwords are never logged, printed, or returned in API responses.
- Role changes, password resets, and deactivation end the target user's active sessions so access changes apply immediately.
- If an admin resets their own password, their current session is also ended.
- Reactivation does not change the user's roles and does not grant a new role.

## Tests

Backend tests live in `my_custom_app/tests/`:

- `test_admin_api.py`: read permissions, status, protected users, and extra-role flags.
- `test_admin_create.py`: create validation, password rules, duplicate names, and logging safety.
- `test_admin_edit_deactivate.py`: edit/deactivate rules, extra roles, session revocation, and guardrails.
- `test_admin_reactivate.py`: reactivation flow and permissions.
- `test_admin_permissions.py`: non-admin and `System Manager` denial.
- `test_admin_roles.py`: role creation and first-admin seeding.
- `test_username_login_patch.py`: username-login patch behavior.

Run from the bench root:

```bash
bench --site site1.local migrate
bench --site site1.local set-config allow_tests true
bench --site site1.local run-tests --app my_custom_app
```

## Frontend Build and Restart

The built frontend is generated output and must not be committed.

```bash
cd ~/frappe-bench/apps/my_custom_app/frontend
corepack yarn build
cd ~/frappe-bench
bench build --app my_custom_app
```

This setup runs `bench start` directly; there is no supervisor. Do **not** use `bench restart`. Stop the running `bench start` process with `Ctrl+C`, then start it again:

```bash
cd ~/frappe-bench
bench start
```

## Phase Progress

- Phase A: Read-only audit and implementation plan approved.
- Phase B: Backend APIs and tests complete.
- Phase C: Admin panel frontend, mobile layout, validation, search, reactivation, and route guard complete.
- Phase D: Documentation and final verification.

Last updated: 2026-10-29.
