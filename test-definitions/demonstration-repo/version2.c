#include <stdio.h>
// This function adds two numbers.
int add(int a, int b)
{
  int sum = a + b;
  return sum;
}
// The main function of the program.
int main(void)
{
  int a = 20, b = 24;

  printf("Sum: %d\n", add(a, b));
  return 0;
}
