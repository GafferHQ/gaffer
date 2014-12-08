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

#include "Gaffer/Path.h"

#include "GafferBindings/DataBinding.h"

namespace GafferBindings
{

namespace Detail
{

template<typename T>
bool isValid( const T &p )
{
	return p.T::isValid();
}

template<typename T>
bool isLeaf( const T &p )
{
	return p.T::isLeaf();
}

template<typename T>
boost::python::list attributeNames( const T &p )
{
	std::vector<IECore::InternedString> n;
	p.T::attributeNames( n );
	boost::python::list result;
	for( std::vector<IECore::InternedString>::const_iterator it = n.begin(), eIt = n.end(); it != eIt; ++it )
	{
		result.append( it->c_str() );
	}
	return result;
}

boost::python::object attributeToPython( IECore::ConstRunTimeTypedPtr a );

template<typename T>
boost::python::object attribute( const T &p, const IECore::InternedString &name )
{
	return attributeToPython( p.T::attribute( name ) );
}

template<typename T>
boost::python::object info( const T &p )
{
	if( !p.isValid() )
	{
		return boost::python::object();
	}

	std::vector<IECore::InternedString> attributeNames;
	p.T::attributeNames( attributeNames );

	boost::python::dict result;
	for( std::vector<IECore::InternedString>::const_iterator it = attributeNames.begin(), eIt = attributeNames.end(); it != eIt; ++it )
	{
		IECore::ConstRunTimeTypedPtr a = p.T::attribute( *it );
		result[it->c_str()] = attributeToPython( a );
	}

	return result;
}

template<typename T>
Gaffer::PathPtr copy( const T &p )
{
	return p.T::copy();
}

} // namespace Detail

template<typename T, typename TWrapper>
PathClass<T, TWrapper>::PathClass( const char *docString )
	:	IECorePython::RunTimeTypedClass<T, TWrapper>( docString )
{
	this->def( "isValid", &Detail::isValid<T> );
	this->def( "isLeaf", &Detail::isLeaf<T> );
	this->def( "attributesNames", &Detail::attributeNames<T> );
	this->def( "attribute", &Detail::attribute<T> );
	// Backwards compatibility with old Path.info()
	// method from original python implementation.
	this->def( "info", &Detail::info<T> );
	this->def( "copy", &Detail::copy<T> );
}

} // namespace GafferBindings

#endif // GAFFERBINDINGS_PATHBINDING_INL
