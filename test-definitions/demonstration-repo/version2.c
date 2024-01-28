//------------------------------------------------------------------------------
// File Header Comment
#include <stdio.h>

// This function adds to numbers.
int add(int a, int b)
{
  int sum = a + b;
  return sum;
}

// The main function of the program.
int main(void)
{
  int a = 20;
  int b = 24;

  int sum = add(a, b);

  printf("Sum: %d\n", sum);
  return 0;
}
