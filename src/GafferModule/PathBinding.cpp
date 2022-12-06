//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#include "boost/python.hpp"
#include "boost/python/slice.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"

#include "PathBinding.h"

#include "GafferBindings/PathBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Path.h"
#include "Gaffer/PathFilter.h"
#include "Gaffer/FileSystemPath.h"

#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/ExceptionAlgo.h"

#include <filesystem>

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

std::vector<IECore::InternedString> listToInternedStringVector( list l )
{
	std::vector<IECore::InternedString> result;
	boost::python::container_utils::extend_container( result, l );
	return result;
}

template<typename WrappedType>
class PathWrapper : public IECorePython::RunTimeTypedWrapper<WrappedType>
{

	public :

		// At one time, the Path class was implemented in pure Python.
		// Because Python doesn't allow function overloads, we couldn't
		// have the nice sensible set of overloaded constructors you see
		// in the C++ Path implementation now. Instead we had a single
		// constructor :
		//
		// def __init__( self, path=None, root="/", filter=None ) :
		//
		// This accepted None, list, or string for the path argument, and
		// we must emulate that in our python bindings for backwards
		// compatibility. This breaks down to the following cases below.

		// This deals with the case where path is None. It is bound last in the resolution
		// order so that it won't mask the constructors below.
		PathWrapper( PyObject *self, object path, object root, PathFilterPtr filter )
			:	IECorePython::RunTimeTypedWrapper<WrappedType>( self, filter )
		{
		}

		// This covers the case where path is a list.
		PathWrapper( PyObject *self, list path, const IECore::InternedString &root, PathFilterPtr filter )
			:	IECorePython::RunTimeTypedWrapper<WrappedType>( self, listToInternedStringVector( path ), root, filter )
		{
		}

		// This covers the case where path is a string. The root argument is ignored because the
		// string already includes the root.
		PathWrapper( PyObject *self, const std::string &path, object root, PathFilterPtr filter )
			:	IECorePython::RunTimeTypedWrapper<WrappedType>( self, path, filter )
		{
		}

		// Caution : In the overrides below, we pass `canceller` to Python via
		// `boost::python::ptr()`. This produces a Python object which
		// references `canceller` directly. We can't guarantee the lifetime of
		// `canceller` beyond the function call,  but we can't stop a Python
		// override from storing the Python object outside that scope, after
		// which any accesses will crash. Our only advice is "don't do that",
		// which seems fairly reasonable given that the only expected use is
		// to call `IECore.Canceller.check( canceller )` within the override
		// itself.

		bool isValid( const IECore::Canceller *canceller = nullptr ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "isValid" );
					if( f )
					{
						return f( boost::python::ptr( canceller ) );
					}
				}
				catch( const error_already_set &e )
				{
					ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::isValid( canceller );
		}

		bool isLeaf( const IECore::Canceller *canceller = nullptr ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "isLeaf" );
					if( f )
					{
						return f( boost::python::ptr( canceller ) );
					}
				}
				catch( const error_already_set &e )
				{
					ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::isLeaf( canceller );
		}

		void propertyNames( std::vector<IECore::InternedString> &names, const IECore::Canceller *canceller = nullptr ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "propertyNames" );
					if( f )
					{
						WrappedType::propertyNames( names, canceller  );
						boost::python::list pythonNames = extract<boost::python::list>( f( boost::python::ptr( canceller ) ) );
						boost::python::container_utils::extend_container( names, pythonNames );
						return;
					}
					// fall back to emulating properties using the deprecated python info() method.
					f = this->methodOverride( "info" );
					if( f )
					{
						boost::python::dict info = extract<boost::python::dict>( f() );
						boost::python::list pythonNames = info.keys();
						boost::python::container_utils::extend_container( names, pythonNames );
						return;
					}
				}
				catch( const error_already_set &e )
				{
					ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::propertyNames( names, canceller  );
		}

		IECore::ConstRunTimeTypedPtr property( const IECore::InternedString &name, const IECore::Canceller *canceller = nullptr ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "property" );
					if( f )
					{
						return extract<IECore::ConstRunTimeTypedPtr>( f( name.c_str(), boost::python::ptr( canceller ) ) );
					}
					// fall back to emulating properties using the deprecated python info() method.
					f = this->methodOverride( "info" );
					if( f )
					{
						boost::python::dict info = extract<boost::python::dict>( f() );
						boost::python::object a = info.get( name.c_str() );
						if( a )
						{
							return extract<IECore::ConstRunTimeTypedPtr>( a );
						}
						return nullptr;
					}
				}
				catch( const error_already_set &e )
				{
					ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::property( name, canceller );
		}

		PathPtr copy() const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "copy" );
					if( f )
					{
						return extract<PathPtr>( f() );
					}
					else
					{
						throw IECore::Exception( "Path.copy() not implemented." );
					}
				}
				catch( const error_already_set &e )
				{
					ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::copy();
		}

		const Plug *cancellationSubject() const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "cancellationSubject" );
					if( f )
					{
						return extract<Plug *>( f() );
					}
				}
				catch( const error_already_set &e )
				{
					ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::cancellationSubject();
		}

		void doChildren( std::vector<PathPtr> &children, const IECore::Canceller *canceller = nullptr ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "_children" );
					if( f )
					{
						list l = extract<list>( f( boost::python::ptr( canceller ) ) );
						boost::python::container_utils::extend_container( children, l );
						return;
					}
				}
				catch( const error_already_set &e )
				{
					ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::doChildren( children, canceller );
		}

		void pathChangedSignalCreated() override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "_pathChangedSignalCreated" );
					if( f )
					{
						f();
						return;
					}
				}
				catch( const error_already_set &e )
				{
					ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::pathChangedSignalCreated();
		}

		// Defined here rather than in the containing namespace
		// because it needs access to the protected method.
		void pathChangedSignalCreatedWrapper()
		{
			WrappedType::pathChangedSignalCreated();
		}

};

const char *rootWrapper( Path &p )
{
	return p.root().c_str();
}

list childrenWrapper( Path &p, const IECore::Canceller *canceller )
{
	std::vector<PathPtr> c;
	p.children( c, canceller );
	list result;
	for( std::vector<PathPtr>::const_iterator it = c.begin(), eIt = c.end(); it != eIt; ++it )
	{
		result.append( *it );
	}
	return result;
}

size_t pathLength( Path &p )
{
	return p.names().size();
}

std::string pathRepr( PathPtr p )
{
	object o( p );
	std::string className = extract<std::string>( o.attr( "__class__" ).attr( "__name__" ) );
	return className + "( '" + p->string() + "' )";
}

const char *getItem( Path &p, long index )
{
	const Path::Names &items = p.names();
	const long size = items.size();

	if( index < 0 )
	{
		index += size;
	}

	if( index >= size || index < 0 )
	{
		PyErr_SetString( PyExc_IndexError, "Index out of range" );
		boost::python::throw_error_already_set();
	}

	return items[index].c_str();
}

list getSlice( Path &p, boost::python::slice s )
{
	const Path::Names &items = p.names();

	Py_ssize_t start, stop, step, length;
	if( PySlice_GetIndicesEx( s.ptr(), items.size(), &start, &stop, &step, &length ) )
	{
		boost::python::throw_error_already_set();
	}

	boost::python::list result;
	for( Py_ssize_t i = start; i < stop; i++ )
	{
		result.append( items[i].c_str() );
	}
	return result;
}

void setSlice( Path &p, boost::python::slice s, boost::python::list l )
{
	Py_ssize_t start, stop, step, length;
	if( PySlice_GetIndicesEx( s.ptr(), p.names().size(), &start, &stop, &step, &length ) )
	{
		boost::python::throw_error_already_set();
	}

	p.set( start, stop, listToInternedStringVector( l ) );
}

void delItem( Path &p, long index )
{
	const long size = p.names().size();

	if( index < 0 )
	{
		index += size;
	}

	if( index >= size || index < 0 )
	{
		PyErr_SetString( PyExc_IndexError, "Index out of range" );
		boost::python::throw_error_already_set();
	}

	p.remove( index );
}

void delSlice( Path &p, boost::python::slice s )
{
	Py_ssize_t start, stop, step, length;
	if( PySlice_GetIndicesEx( s.ptr(), p.names().size(), &start, &stop, &step, &length ) )
	{
		boost::python::throw_error_already_set();
	}

	p.remove( start, stop );
}

struct PathChangedSlotCaller
{
	void operator()( boost::python::object slot, PathPtr p )
	{
		slot( p );
	}
};

PathFilterPtr createStandardFilter( object pythonExtensions, const std::string &extensionsLabel, bool includeSequences )
{
	std::vector<std::string> extensions;
	boost::python::container_utils::extend_container( extensions, pythonExtensions );
	return FileSystemPath::createStandardFilter( extensions, extensionsLabel, includeSequences );
}

// Interoperability between `std::filesystem::path` and `pathlib.Path`

struct StdPathFromPathlibPath
{

	StdPathFromPathlibPath()
	{
		boost::python::converter::registry::push_back(
			&convertible,
			&construct,
			boost::python::type_id<std::filesystem::path>()
		);
	}

	static void *convertible( PyObject *obj )
	{
		if( PyUnicode_Check( obj ) )
		{
			return obj;
		}

		object pathlibPathClass = import( "pathlib" ).attr( "Path" );
		if( PyObject_IsInstance( obj, pathlibPathClass.ptr() ) )
		{
			return obj;
		}

		return nullptr;
	}

	static void construct( PyObject *obj, boost::python::converter::rvalue_from_python_stage1_data *data )
	{
		void *storage = ( ( converter::rvalue_from_python_storage<std::filesystem::path> * ) data )->storage.bytes;
		std::filesystem::path *path = new( storage ) std::filesystem::path;
		data->convertible = storage;

		object o( handle<>( borrowed( obj ) ) );
		if( !PyUnicode_Check( obj ) )
		{
			o = o.attr( "__str__" )();
		}
		const std::string s = extract<std::string>( o );
		*path = s;
	}

};

struct StdPathToPathlibPath
{
	static PyObject *convert( const std::filesystem::path &path )
	{
		const std::string s = path.string();
		object result;
		if( s.empty() )
		{
			// This is highly unsatisfactory - `pathlib.Path` has no way of
			// representing an empty path, so the best we can do is to return
			// `None`.
			result = object();
		}
		else
		{
			result = import( "pathlib" ).attr( "Path" )( s );
		}
		Py_INCREF( result.ptr() );
		return result.ptr();
	}
};


} // namespace

void GafferModule::bindPath()
{
	using Wrapper = PathWrapper<Path>;

	{
		scope s = PathClass<Path, Wrapper>()
			.def(
				init<const object &, object, PathFilterPtr>( (
					arg( "path" ) = object(),
					arg( "root" ) = "/",
					arg( "filter" ) = object()
				) )
			)
			.def(
				init<const std::string &, object, PathFilterPtr>( (
					arg( "path" ),
					arg( "root" ) = "/",
					arg( "filter" ) = object()
				) )
			)
			.def(
				init<boost::python::list, const IECore::InternedString &, PathFilterPtr>( (
					arg( "path" ),
					arg( "root" ) = "/",
					arg( "filter" ) = object()
				) )
			)
			.def( "root", &rootWrapper )
			.def( "isEmpty", &Path::isEmpty )
			.def( "parent", &Path::parent )
			.def( "children", &childrenWrapper, arg( "canceller" ) = object() )
			.def( "setFilter", &Path::setFilter )
			.def( "getFilter", (PathFilter *(Path::*)())&Path::getFilter, return_value_policy<CastToIntrusivePtr>() )
			.def( "pathChangedSignal", &Path::pathChangedSignal, return_internal_reference<1>() )
			.def( "setFromPath", &Path::setFromPath )
			.def( "setFromString", &Path::setFromString, return_self<>() )
			.def( "append", &Path::append, return_self<>() )
			.def( "truncateUntilValid", &Path::truncateUntilValid, return_self<>() )
			.def( "__str__", &Path::string )
			.def( "__repr__", &pathRepr )
			.def( "__len__", &pathLength )
			.def( "__getitem__", &getItem )
			.def( "__getitem__", &getSlice )
			.def( "__setitem__", (void (Path::*)( size_t, const IECore::InternedString &))&Path::set )
			.def( "__setitem__", &setSlice )
			.def( "__delitem__", &delItem )
			.def( "__delitem__", &delSlice )
			.def( self == self )
			.def( self != self )
			.def( "_emitPathChanged", &Path::emitPathChanged )
			.def( "_pathChangedSignalCreated", &Wrapper::pathChangedSignalCreatedWrapper )
			.def( "_havePathChangedSignal", &Path::havePathChangedSignal )
		;

		SignalClass<Path::PathChangedSignal, DefaultSignalCaller<Path::PathChangedSignal>, PathChangedSlotCaller>( "PathChangedSignal" );

	}

	PathClass<FileSystemPath>()
		.def(
			init<PathFilterPtr, bool>( (
				arg( "filter" ) = object(),
				arg( "includeSequences" ) = false
			) )
		)
		.def(
			init<const std::string &, PathFilterPtr, bool>( (
				arg( "path" ),
				arg( "filter" ) = object(),
				arg( "includeSequences" ) = false
			) )
		)
		.def( "getIncludeSequences", &FileSystemPath::getIncludeSequences )
		.def( "setIncludeSequences", &FileSystemPath::setIncludeSequences )
		.def( "isFileSequence", &FileSystemPath::isFileSequence )
		.def( "fileSequence", &FileSystemPath::fileSequence )
		.def( "createStandardFilter", &createStandardFilter, (
				arg( "extensions" ) = list(),
				arg( "extensionsLabel" ) = "",
				arg( "includeSequenceFilter" ) = false
			)
		)
		.def( "nativeString", &FileSystemPath::nativeString )
		.staticmethod( "createStandardFilter" )
	;

	StdPathFromPathlibPath();
	to_python_converter<std::filesystem::path, StdPathToPathlibPath>();

}
