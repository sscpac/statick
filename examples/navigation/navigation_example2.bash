# Example script for running statick against a single ROS package

if [ ! -d src ]; then 
    mkdir src

    pushd src
    git clone https://github.com/ros-planning/navigation.git
    popd
fi

catkin_make -DCMAKE_BUILD_TYPE=RelWithDebInfo

. devel/setup.bash

if [ ! -d statick_example2 ]; then
    mkdir statick_example2
fi

statick src/navigation/amcl statick_example2/
