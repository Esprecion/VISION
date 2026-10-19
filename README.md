# VISION

VISION is a unified platform for MSMEs and others to manage business development, operations, and finance in one place.

## Modules

- **Business Development** - Clients, Deals, Pipeline Stages, Products, and Service Contracts
- **Operations** - Projects, Tool Subscriptions and tracking, and Client Engagement Logs
- **Finance** - Invoices, Expenses, and financial reporting

## Roles

- **CBO** (Chief Business Officer)
- **COO** (Chief Operating Officer)
- **CFO** (Chief Financial Officer)

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
