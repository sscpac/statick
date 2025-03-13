#!/usr/bin/env bash

REPO_NAME=statick
HOME=/opt

# Uncomment this line if necessary.
# git config --global --add safe.directory $HOME/$REPO_NAME

bash $HOME/$REPO_NAME/.devcontainer/scripts/postCreateCommandUser.sh
