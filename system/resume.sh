#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "$SCRIPT_DIR"

# Code created by Jez, on 6 November 2026. Updated 11 November 2026
# resume.sh is the file to be executed after the Codespace or the Azure VM has restarted. This assumes the system has been setup.

echo "Starting services..."
sudo service mariadb start
# The prototype had Redis server, but since `bench start` launches its own instance
# The prototype had cron, but cron was only needed for installation in setup.sh

# Wait for MariaDB to start
for i in $(seq 1 30); do
    mariadb-admin ping --silent >/dev/null 2>&1 && break
    sleep 1
done
mariadb-admin ping --silent >/dev/null 2>&1 || { echo "MariaDB did not come up."; exit 1; }
echo "MariaDB is up."

# To check if MariaDB is up, use `sudo service mariadb status`. Without sudo, this will say it is stopped.

echo "Starting Frappe Bench"
cd "$SCRIPT_DIR/backend/frappe-bench"
bench start