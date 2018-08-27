# Example script for running statick with a custom configuration and custom
# tool plugin

if [ ! -d src ]; then 
    mkdir src

    pushd src
    git clone https://github.com/ros-planning/navigation.git
    popd
fi

catkin_make -DCMAKE_BUILD_TYPE=RelWithDebInfo

. devel/setup.bash

if [ ! -d statick_example5 ]; then
    mkdir statick_example5
fi

statick src/navigation/amcl statick_example5/ --user-paths ./navigation_config --profile profile_custom.yaml
