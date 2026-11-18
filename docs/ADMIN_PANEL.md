# VISION Administration Panel

The Administration panel manages VISION user accounts. It covers create, list, edit, and delete flows for the account types used by the business.

## Access

- Route: `/admin/users` in the VISION frontend.
- Access is controlled by the server endpoint `my_custom_app.administration.admin.can_manage_users`.
- Only users with the `System Admin` role can use the admin APIs.
- The sidebar link and the route guard both use the server check. Direct visits to `/admin/users` by non-admins redirect to `/dashboard`.
- `Administrator` and `Guest` are protected. They are never listed and cannot be created, edited, or deleted through this panel.

## Managed Roles

VISION manages exactly one of these roles per account:

- `System Admin`
- `COO`
- `CFO`
- `CTO`
- `CBO`

There is no CEO role; the founder is CEO and COO. `System Manager` is never granted by the Administration APIs.

When editing a user, only the account name and role can change:

- The account name must be filled in and unique; changing it updates the login name and ends the user's sessions.
- The selected managed role replaces other managed roles.
- Unrelated roles are preserved.
- The table shows a small `Extra roles` note when `has_extra_roles` is true.

## First Admin Setup

Create the first `System Admin` from the bench environment:

```bash
VISION_ADMIN_USERNAME=sysadmin01 \
VISION_ADMIN_PASSWORD='replace-with-a-strong-password' \
bench --site site1.local execute my_custom_app.administration.admin_roles.seed_first_admin
```

`seed_first_admin` is idempotent and does not print the password.

## Username Login

The `enable_username_login` patch sets `System Settings.allow_login_using_user_name`. Users sign in with their account name instead of the internal `@vision.local` email address.

The patch is listed in `my_custom_app/patches.txt` and is safe to run again.

## API Endpoints

All endpoints are in `my_custom_app.administration.admin`.

| Endpoint | Purpose |
| --- | --- |
| `can_manage_users()` | Returns whether the current session can manage users. |
| `get_managed_roles()` | Returns the allowed managed roles. |
| `list_users()` | Returns all non-protected users with at least one managed role. |
| `get_user(account_name)` | Returns one managed user. |
| `create_user(account_name, password, role)` | Creates a user with one managed role. |
| `edit_user(account_name, role, new_account_name)` | Changes the account name and managed role. |
| `delete_user(account_name)` | Deletes the account and ends its active sessions. |
| `deactivate_user(account_name)` | Legacy endpoint that disables the account; not exposed in the UI. |
| `reactivate_user(account_name)` | Legacy endpoint that enables the account; not exposed in the UI. |

A user row has this shape:

```json
{
  "account_name": "juan.delacruz",
  "role": "COO",
  "roles": ["COO"],
  "has_extra_roles": false,
  "enabled": true,
  "is_self": false,
  "is_last_active_system_admin": false
}
```

`is_self` marks the signed-in administrator's own row. `is_last_active_system_admin` marks the only enabled `System Admin`. The Users page uses these flags to label accounts and disable actions the server would reject anyway.

Success responses use:

```json
{ "ok": true, "message": "User Created", "user": { "...": "..." } }
```

Errors use:

```json
{ "ok": false, "field": "password", "fields": ["password"], "message": "Password requirements not met." }
```

## Safety Rules

- Nobody can delete their own account; the API returns `This user cannot be deleted.`
- The last active `System Admin` cannot be deleted or demoted; demotion returns `At least one System Admin is required.`
- Deleting a user removes the account but keeps records they created, as their owner is stored as a name string.
- Passwords are never logged, printed, or returned in API responses, and cannot be changed through `edit_user`.
- Account-name and role changes end the target user's active sessions so access changes apply immediately.
- A blank or duplicate account name returns `Please enter a unique account name.` (missing values return the required-details message).

## Users Page Behavior

- The list can be searched by account name or role and sorted by account name.
- The page shows the total account count.
- The signed-in admin's row is labelled `You`; the only enabled `System Admin` is labelled `Last admin`.
- `Delete` is disabled for your own account and for the last active `System Admin`.
- The role field is locked only for the last active `System Admin`; all other accounts, including your own, can be renamed and have their role changed when another admin remains.
- Disabled actions are also enforced by the API; the UI only mirrors the server rules.

## Tests

Backend tests live in `my_custom_app/tests/`:

- `test_admin_api.py`: read permissions, status, protected users, and extra-role flags.
- `test_admin_create.py`: create validation, password rules, duplicate names, and logging safety.
- `test_admin_edit_deactivate.py`: edit and delete rules, extra roles, session revocation, and guardrails.
- `test_admin_reactivate.py`: legacy reactivation endpoint behavior and permissions.
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

Last updated: 2026-11-02.
