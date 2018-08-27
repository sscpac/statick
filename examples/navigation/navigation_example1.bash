# Example script for running statick against an entire catkin workspace

if [ ! -d src ]; then 
    mkdir src

    pushd src
    git clone https://github.com/ros-planning/navigation.git
    popd
fi

catkin_make -DCMAKE_BUILD_TYPE=RelWithDebInfo

. devel/setup.bash

if [ ! -d statick_example1 ]; then
    mkdir statick_example1
fi

statick_ws src/ statick_example1/
