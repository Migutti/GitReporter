#include <stdio.h>
int add(int a, int b);
int main(void) {
  int a=20, b=24;

  printf("Sum: %d\n",add(a,b));
  return 0;
}
int add(int a, int b) {
  int sum=a+b;
  return sum;
}
