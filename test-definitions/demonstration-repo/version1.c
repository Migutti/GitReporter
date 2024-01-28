#include <stdio.h>

int add(int a, int b);

int main(void) {
  int a=20;
  int b=24;

  int sum=add(a, b);
  printf("Sum: %d\n", sum);
  return 0;
}

int add(int a, int b) {
  int sum=a+b;
  return sum;
}
