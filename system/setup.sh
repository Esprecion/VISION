#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "$SCRIPT_DIR"

# Code created by Jez, on 4 November 2026. Updated 11 November 2026.
# setup.sh is the first file to be executed after the Codespace or the Azure VM running Ubuntu hosting it has been set up.

echo "Following Frappe Framework installation guide on Debian/Ubuntu. At https://docs.frappe.io/framework/user/en/installation"

echo "Updating system's package index"
sudo apt update

echo "Installing git, redis, and mariadb"
sudo apt install -y git redis-server libmariadb-dev mariadb-server mariadb-client pkg-config cron

echo "Configuring and starting MariaDB"
sudo service mariadb start
sudo mariadb-secure-installation

# Simple guide for me, because I need this to work:
#   Root Password: Enter
#   Unix Socket Authentication: n
#   Change root password: Y, then type password, for my purposes (not VL's), it's 'apc2026' DO NOT USE IN PROD!!!!!
#   Remove anonymous users: Y
#   Disallow root login remotely: Y
#   Remove test database: Y
#   Reload privilege tables: Y

echo "Installing nvm, node, and yarn"
export COREPACK_ENABLE_DOWNLOAD_PROMPT=0
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [ ! -s "$NVM_DIR/nvm.sh" ]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
fi
. "$NVM_DIR/nvm.sh"
nvm install 24
command -v yarn >/dev/null || npm install -g yarn

echo "Installing uv and python"
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv python install 3.12 --default

echo "Installing bench via uv"
uv tool install frappe-bench


echo "Following Install and Setup Bench guide. At https://docs.frappe.io/framework/user/en/tutorial/install-and-setup-bench"

echo "Creating the frappe-bench directory"
cd "$SCRIPT_DIR/backend"
bench init --frappe-branch version-15 --python python3.12 frappe-bench

echo "Creating the frontend directory and installing dependencies"
cd "$SCRIPT_DIR/frontend"
yarn install

echo "setup.sh has finished running."