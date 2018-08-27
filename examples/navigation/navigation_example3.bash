# Example script for running statick with a custom configuration

if [ ! -d src ]; then 
    mkdir src

    pushd src
    git clone https://github.com/ros-planning/navigation.git
    popd
fi

catkin_make -DCMAKE_BUILD_TYPE=RelWithDebInfo

. devel/setup.bash

if [ ! -d statick_example3 ]; then
    mkdir statick_example3
fi

statick src/navigation/amcl statick_example3/ --user-paths ./navigation_config
