cmake_minimum_required(VERSION 2.8.3)
project(empty_pkg)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

find_package(catkin REQUIRED COMPONENTS)

catkin_package(
  CATKIN_DEPENDS
)
