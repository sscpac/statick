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
# shellcheck disable=SC2016
echo ". /opt/venv/bin/activate" >> /root/.bashrc
echo /root/.bashrc
cat /root/.bashrc

echo "" >> ~/.bashrc
echo "alias pip='uv pip'" >> /root/.bashrc
echo "alias pip='uv pip'" >> /root/.bashrc
echo "alias self-check='statick . --level self_check --check --output-dir /tmp/statick-output --log info'" >> /root/.bashrc

echo ""
echo "Setup complete. Development environment ready to go!!"
