# Example script for running statick with a custom configuration and custom
# profile

if [ ! -d src ]; then 
    mkdir src

    pushd src
    git clone https://github.com/ros-planning/navigation.git
    popd
fi

catkin_make -DCMAKE_BUILD_TYPE=RelWithDebInfo

. devel/setup.bash

if [ ! -d statick_example4 ]; then
    mkdir statick_example4
fi

statick src/navigation/amcl statick_example4/ --user-paths ./navigation_config --profile profile_objective.yaml
