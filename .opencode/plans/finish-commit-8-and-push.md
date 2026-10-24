# Finish commit 8 and push `polish`

## Context
- Branch: `polish` (no upstream yet). Remote: `origin = https://github.com/Esprecion/VISION`.
- Commits 1-7 already made locally:
  - `059d4a4` Commit 1, `17e634e` Commit 2, `62b79b1` Commit 3, `e608924` Commit 4, `8ab523e` Commit 5, `4cc8719` Commit 6, `88da737` Commit 7.
- Uncommitted work in progress: `my_custom_app/api.py` (validate-before-insert refactor). Passes `ruff check` and `ruff format --check` with the pinned ruff 0.8.1.
- Tooling: exact `ruff 0.8.1` binary extracted at `C:\Users\Ashlee\AppData\Local\Temp\opencode\ruff-0.8.1\ruff.exe` (matches `.pre-commit-config.yaml` `ruff-pre-commit rev: v0.8.1`).

## Step 1 - Commit 8: api.py refactor + tests + CI
1. `my_custom_app/api.py` (already edited):
   - Added `_validate_client(client)` and `_validate_items(items)`.
   - `create_deal_with_details` now validates the whole payload BEFORE any insert, so a bad line saves nothing (all-or-nothing).
2. New `my_custom_app/tests/__init__.py` (empty).
3. New `my_custom_app/tests/test_api.py` (`frappe.tests.utils.FrappeTestCase`) with 6 cases:
   - `test_creates_new_client_and_products`
   - `test_reuses_existing_client_and_product`
   - `test_duplicate_client_name_is_reused`
   - `test_same_new_product_on_two_lines_created_once`
   - `test_user_without_create_permission_is_blocked`
   - `test_nothing_saved_when_one_line_fails`
   - Helpers: `ensure_stage()` (creates `Lead` Pipeline Stage), `_create()` wrapper.
4. New `.github/workflows/ci.yml`:
   - Trigger: `push` to `main`/`develop`, and `pull_request`.
   - Job `pre-commit`: checkout + setup-python 3.10 + `pre-commit/action@v3.0.1` (runs `--all-files`).
   - Job `frontend-build`: checkout + setup-node 20 (yarn cache on `frontend/yarn.lock`) + `yarn install --frozen-lockfile` + `yarn build`, `working-directory: frontend`.
   - No backend test job (per requirement).
5. Verify: `ruff check my_custom_app` and `ruff format --check my_custom_app` with the 0.8.1 binary; expect clean.
6. `git add` api.py + tests + workflow, commit: `Commit 8: add Deal-creation tests and CI (pre-commit + frontend build)`.
   - Note: api.py refactor could be its own commit if preferred; default is to fold into commit 8.

## Step 2 - Push
- `git push -u origin polish` (creates remote branch and sets upstream).
- If credentials/2FA are required, the user authenticates in the terminal.

## Notes / open items
- Backend tests are run by the user in WSL: `bench run-tests --app my_custom_app`.
- Case 6 relies on validate-before-insert (no rollback needed) - confirmed behavior of the refactor.
- test_api.py and ci.yml were NOT created yet (blocked by plan-mode write permissions).
