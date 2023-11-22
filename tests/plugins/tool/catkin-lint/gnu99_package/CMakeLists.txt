cmake_minimum_required(VERSION 2.8.3)
project(empty_pkg)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=gnu99")

find_package(catkin REQUIRED COMPONENTS)

catkin_package(
  CATKIN_DEPENDS
)
