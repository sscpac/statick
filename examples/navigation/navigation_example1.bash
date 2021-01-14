#!/bin/bash

# Example script for running statick against an entire catkin workspace

if [ ! -d src ]; then 
    mkdir src

    pushd src || exit
    git clone https://github.com/ros-planning/navigation.git
    popd || exit
fi

catkin_make -DCMAKE_BUILD_TYPE=RelWithDebInfo

. devel/setup.bash  # NOLINT

if [ ! -d statick_example1 ]; then
    mkdir statick_example1
fi

statick src/ --output-directory statick_example1/ -ws
