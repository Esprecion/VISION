#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "$SCRIPT_DIR"

# Code created by Jez, on 11 November 2026. Updated on 20 November 2026.
# frappe_setup.sh is the file to run after setup.sh, to establish the new app on Frappe Framework. Only use in dev.

cd "$SCRIPT_DIR/backend/frappe-bench/"
# bench start

echo "Creating the VISION system's files"

# For creating the new site
echo "Creating the Frappe site"
bench new-site dashboard.localhost
echo "set dashboard"
bench use dashboard.localhost

# For recording DocTypes as files instead of simple database objects
echo "Setting the Frappe site to developer mode"
bench --site dashboard.localhost set-config developer_mode 1

# For creating the new app
echo "Creating the new app"
bench new-app vision_system

# For creating the modules
echo "Creating the app's modules"
APP_DIR="$SCRIPT_DIR/backend/frappe-bench/apps/vision_system/vision_system"
cp "$SCRIPT_DIR/backend/copies/modules.txt" "$APP_DIR/modules.txt"

while IFS= read -r module || [ -n "$module" ]; do
    [ -z "$module" ] && continue
    folder=$(echo "$module" | tr '[:upper:] ' '[:lower:]_')
    mkdir -p "$APP_DIR/$folder"
    touch "$APP_DIR/$folder/__init__.py"
    cp -r "$SCRIPT_DIR/backend/copies/module_doctypes/$folder/doctype" "$APP_DIR/$folder/"
done < "$APP_DIR/modules.txt" 

# For installing the vision_system app onto the site
echo "Installing the app onto the site"
bench --site dashboard.localhost install-app vision_system