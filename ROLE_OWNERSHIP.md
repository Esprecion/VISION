# Role Ownership Map

This file documents ownership only. Permissions still come from DocType JSON and backend checks.

| Role | Department folders owned | Can only read | Shared files it depends on |
| --- | --- | --- | --- |
| System Admin | `my_custom_app/administration/`, `frontend/src/pages/admin/` | None; no department DocType access by design | Common shared files; `my_custom_app/shared/api.py`, `my_custom_app/www/frontend.py`, `my_custom_app/www/frontend.html` |
| COO | `my_custom_app/operations/`, `frontend/src/pages/operations/` (Projects and Engagement Logs) | `my_custom_app/operations/doctype/tool_subscription/`, `my_custom_app/finance/doctype/client_payment/` | Common shared files; `frontend/src/components/FinanceFormDialog.vue`, `my_custom_app/finance/seed_reports.py`, `my_custom_app/operations/seed_reports.py` |
| CFO | `my_custom_app/finance/`, `frontend/src/pages/finance/` | `my_custom_app/business_development/`, `my_custom_app/operations/` | Common shared files; `my_custom_app/shared/ai_imports.py`, `frontend/src/components/FinanceFormDialog.vue`, `frontend/src/components/ui/ImportDialog.vue`, `my_custom_app/finance/seed_reports.py` |
| CBO | `my_custom_app/business_development/`, `frontend/src/pages/business-dev/` | `my_custom_app/finance/`, `my_custom_app/operations/` | Common shared files; `my_custom_app/shared/ai_imports.py`, `frontend/src/components/ui/ImportDialog.vue`, `frontend/src/components/FinanceFormDialog.vue`, `my_custom_app/finance/projects.py` |
| CTO | `my_custom_app/operations/doctype/tool_subscription/`, the Tools view in `frontend/src/pages/operations/` | `my_custom_app/business_development/`, `my_custom_app/finance/` | Common shared files; `my_custom_app/operations/seed_reports.py`, `my_custom_app/patches/update_role_report_permissions.py` |

## Common shared files

- Frontend: `frontend/src/router.ts`, `frontend/src/data/session.ts`, `frontend/src/components/Sidebar.vue`, `frontend/src/layouts/DepartmentLayout.vue`, `frontend/src/components/TopTabs.vue`, `frontend/src/App.vue`, `frontend/src/components/ToastContainer.vue`, `frontend/src/components/ui/*`, `frontend/src/utils/*`.
- Backend: `my_custom_app/shared/api.py`, `my_custom_app/shared/dashboard.py`, `my_custom_app/administration/admin_roles.py`, `my_custom_app/hooks.py`, `my_custom_app/patches.txt`, `my_custom_app/www/frontend.py`, `my_custom_app/www/frontend.html`, and the report/permission patches in `my_custom_app/patches/`.

## CEO

There is no `CEO` role yet; the founder is CEO and COO. No CEO folder or placeholder file is created.
