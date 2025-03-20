#!/usr/bin/env bash

echo "Create virtual environment ..."
uv venv /opt/venv
# shellcheck disable=SC1091
. /opt/venv/bin/activate
# shellcheck disable=SC2102
uv pip install -e .[docs,test]

echo "Update .bashrc ..."
echo "" >> ~/.bashrc
echo "# Activate statick virtual environment." >> /root/.bashrc
echo ". /opt/venv/bin/activate" >> /root/.bashrc

echo "" >> ~/.bashrc
echo "alias pip='uv pip'" >> /root/.bashrc

dev --help
echo ""
echo "Setup complete. Development environment ready to go!!"
echo "Use the command 'dev --help' to get started."
