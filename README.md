# VISION

VISION is a unified platform for MSMEs and others to manage business development, operations, and finance in one place.

## Modules

- **Business Development** - Clients, Deals, Pipeline Stages, Products, and Service Contracts
- **Operations** - Projects, Tool Subscriptions and tracking, and Client Engagement Logs
- **Finance** - Invoices, Expenses, and financial reporting
- **Administration** - User accounts, roles, and access management

## Roles

- **CBO** (Chief Business Officer)
- **COO** (Chief Operating Officer)
- **CFO** (Chief Financial Officer)
- **System Admin** - Manages users and role assignments
- **CTO** (Chief Technology Officer)

See [ROLE_OWNERSHIP.md](ROLE_OWNERSHIP.md) for role ownership, read-only access, and shared files.

## Development environment

The development setup is based on the scripts in `system/` and the devcontainer definition in `.devcontainer/devcontainer.json`. These scripts are for development only.

**How to deploy (19 November 2026 | For Development)**
1. `cd system`
2. `bash setup.sh`
3. `bash frappe_setup.sh`

**How to resume after shutdown (19 November 2026 | For Development)**
1. `cd system`
2. `bash resume.sh`

**How to reset the Frappe app (20 November 2026 | For Development)**
1. `cd system/backend/frappe-bench`
2. `bench drop-site dashboard.localhost --root-password [Insert MariaDB root user password]`
3. `bench remove-app vision_system`

Supporting course and design artifacts live in `docs/`, including C4 diagrams and the final paper/presentation.

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

`ash
cd 
bench get-app  --branch main
bench install-app my_custom_app
`

## Deploy

To deploy VISION on [Frappe Cloud](https://frappecloud.com/), follow the standard Frappe app deployment process. Ensure all dependencies are installed and migrations run successfully.

## Contributing

This app uses pre-commit for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

`ash
cd apps/my_custom_app
pre-commit install
`

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade
