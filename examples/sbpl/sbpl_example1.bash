# Example script for running statick against a standard CMake package (no ROS/catkin)

if [ ! -d sbpl ]; then 
    git clone https://github.com/sbpl/sbpl.git
fi

if [ ! -d statick_example1 ]; then
    mkdir statick_example1
fi

statick sbpl/ statick_example1/
