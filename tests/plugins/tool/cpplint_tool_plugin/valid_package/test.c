#include <stdlib.h>
void func(const char *buff) {
  int si;

  if (buff) {
    si = atoi(buff); /* 'atoi' used to convert a string to an integer, but function will
                         not report conversion errors; consider using 'strtol' instead. */
  } else {
    /* Handle error */
  }
}
