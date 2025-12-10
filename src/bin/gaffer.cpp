// Duplicating Python's main executable found in `Programs/python.c` of CPython.

#include "Python.h"

#ifdef MS_WINDOWS

#pragma comment(lib, "tbbmalloc_proxy.lib")
#pragma comment(linker, "/include:__TBB_malloc_proxy")

int wmain( int argc, wchar_t **argv )
{
	return Py_Main( argc, argv );
}
#else
int main( int argc, char **argv )
{
	return Py_BytesMain( argc, argv );
}
#endif