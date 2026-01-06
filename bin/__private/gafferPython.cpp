// Duplicating Python's main executable found in `Programs/python.c` of CPython.

#include "Python.h"

#ifdef MS_WINDOWS

#include "tbb/tbbmalloc_proxy.h"

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