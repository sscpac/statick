#!/bin/bash

# Example script for running statick against a single ROS package

if [ ! -d src ]; then 
    mkdir src

    pushd src || exit
    git clone https://github.com/ros-planning/navigation.git
    popd || exit
fi

catkin_make -DCMAKE_BUILD_TYPE=RelWithDebInfo

. devel/setup.bash  # NOLINT

if [ ! -d statick_example2 ]; then
    mkdir statick_example2
fi

statick src/navigation/amcl --output-directory statick_example2/
