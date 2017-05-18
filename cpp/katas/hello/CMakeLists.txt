cmake_minimum_required(VERSION 2.8.9)

# project
project (hello)
add_executable(hello hello.cpp)
# target_link_libraries(hello hello_lib)

# gtest
add_executable(run_tests test_hello.cpp)
# target_link_libraries(run_tests hello_lib gtest gtest_main)
target_link_libraries(run_tests gtest gtest_main)
