#!/bin/bash

# Example script for running statick with a custom configuration and custom
# tool plugin

if [ ! -d src ]; then 
    mkdir src

    'pushd src || exit'
    git clone https://github.com/ros-planning/navigation.git
    'popd || exit'
fi

catkin_make -DCMAKE_BUILD_TYPE=RelWithDebInfo

# shellcheck source=./devel/setup.bash
. devel/setup.bash  # NOLINT

if [ ! -d statick_example5 ]; then
    mkdir statick_example5
fi

statick src/navigation/amcl --output-directory statick_example5/ --user-paths ./navigation_config --profile profile_custom.yaml
