# Example script for running statick against a python package (no CMake/ROS/catkin)

if [ ! -d werkzeug ]; then 
    git clone https://github.com/pallets/werkzeug.git
fi

if [ ! -d statick_example1 ]; then
    mkdir statick_example1
fi

statick werkzeug/ statick_example1/
