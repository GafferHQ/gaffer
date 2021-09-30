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

#ifndef GAFFERBINDINGS_PATHBINDING_INL
#define GAFFERBINDINGS_PATHBINDING_INL

#include "GafferBindings/DataBinding.h"

#include "Gaffer/Path.h"
#include "Gaffer/Plug.h"

namespace GafferBindings
{

namespace Detail
{

template<typename T>
bool isValid( const T &p, const IECore::Canceller *canceller )
{
	IECorePython::ScopedGILRelease gilRelease;
	return p.T::isValid( canceller );
}

template<typename T>
bool isLeaf( const T &p, const IECore::Canceller *canceller )
{
	IECorePython::ScopedGILRelease gilRelease;
	return p.T::isLeaf( canceller );
}

template<typename T>
boost::python::list propertyNames( const T &p, const IECore::Canceller *canceller )
{
	std::vector<IECore::InternedString> n;
	{
		IECorePython::ScopedGILRelease gilRelease;
		p.T::propertyNames( n, canceller );
	}

	boost::python::list result;
	for( std::vector<IECore::InternedString>::const_iterator it = n.begin(), eIt = n.end(); it != eIt; ++it )
	{
		result.append( it->c_str() );
	}
	return result;
}

GAFFERBINDINGS_API boost::python::object propertyToPython( IECore::ConstRunTimeTypedPtr a );

template<typename T>
boost::python::object property( const T &p, const IECore::InternedString &name, const IECore::Canceller *canceller )
{
	IECore::ConstRunTimeTypedPtr property;
	{
		IECorePython::ScopedGILRelease gilRelease;
		property = p.T::property( name, canceller );
	}
	return propertyToPython( property );
}

template<typename T>
boost::python::object info( boost::python::object o )
{
	const T &p = boost::python::extract<const T &>( o );
	if( !p.isValid() )
	{
		return boost::python::object();
	}

	// Our aim here is to emulate the old deprecated Path.info()
	// Python method using the new propertyNames() and property()
	// API defined in C++. We want to collect all properties and
	// return them in a dictionary.
	//
	// There are two cases we must deal with :
	//
	// 1. Where the actual info() method has *not* been overridden
	//    in Python. This is the case when the Python instance is
	//    not of a Python-derived class, or where it is, but the
	//    derived class implements the new property API rather
	//    then the old info one. In this case we want to use the
	//    virtual property methods, so that we return the complete
	//    info.
	//
	// 2. Where the info() method has been overridden by a Python
	//    derived class. In this case, we're being called when
	//    the Python implementation calls the base class method.
	//    We are only responsible for filling in the properties
	//    that T implements, as the derived implementation will
	//    fill in the rest.
	//
	// We use PyFunction_Check to determine if the most-derived
	// implementation of info() is a python function (case 2), if
	// not then we assume it's a boost::python function (case 1).
	boost::python::object infoMethod = o.attr( "info" );
	const PyObject *infoFunction = PyMethod_Function( infoMethod.ptr() );
	const bool infoImplementedInPython = PyFunction_Check( infoFunction );

	std::vector<IECore::InternedString> propertyNames;
	if( infoImplementedInPython )
	{
		p.T::propertyNames( propertyNames );
	}
	else
	{
		p.propertyNames( propertyNames );
	}

	boost::python::dict result;
	for( std::vector<IECore::InternedString>::const_iterator it = propertyNames.begin(), eIt = propertyNames.end(); it != eIt; ++it )
	{
		IECore::ConstRunTimeTypedPtr a;
		if( infoImplementedInPython )
		{
			a = p.T::property( *it );
		}
		else
		{
			a = p.property( *it );
		}
		result[it->c_str()] = propertyToPython( a );
	}

	return std::move( result );
}

template<typename T>
Gaffer::PathPtr copy( const T &p )
{
	return p.T::copy();
}

template<typename T>
Gaffer::PlugPtr cancellationSubject( const T &p )
{
	return const_cast<Gaffer::Plug *>( p.T::cancellationSubject() );
}

} // namespace Detail

template<typename T, typename TWrapper>
PathClass<T, TWrapper>::PathClass( const char *docString )
	:	IECorePython::RunTimeTypedClass<T, TWrapper>( docString )
{
	this->def( "isValid", &Detail::isValid<T>, boost::python::arg( "canceller" ) = boost::python::object() );
	this->def( "isLeaf", &Detail::isLeaf<T>, boost::python::arg( "canceller" ) = boost::python::object() );
	this->def( "propertyNames", &Detail::propertyNames<T>, boost::python::arg( "canceller" ) = boost::python::object() );
	this->def( "property", &Detail::property<T>, ( boost::python::arg( "name" ), boost::python::arg( "canceller" ) = boost::python::object() ) );
	this->def( "cancellationSubject", &Detail::cancellationSubject<T> );
	// Backwards compatibility with deprecated Path.info()
	// method from original python implementation.
	/// \todo Remove this in due course.
	this->def( "info", &Detail::info<T> );
	this->def( "copy", &Detail::copy<T> );
}

} // namespace GafferBindings

#endif // GAFFERBINDINGS_PATHBINDING_INL
