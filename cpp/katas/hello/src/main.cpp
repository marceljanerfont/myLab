#include <iostream>
#include "gtest/gtest.h"

int sum(int a, int b) {
    return a + b;
}

TEST(MathTest, TwoPlusTwoEqualsFour) {
    EXPECT_EQ(sum(2, 2), 4);
}

int main(int argc, char **argv)
{
    std::cout << "Hello, world!\n";
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
