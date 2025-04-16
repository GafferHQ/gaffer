//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "IECorePython/RunTimeTypedBinding.h"

#include "ObjectMatrixBinding.h"

#include "Gaffer/ObjectMatrix.h"

#include "boost/python/suite/indexing/container_utils.hpp"

#include "fmt/format.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;

namespace
{

static ObjectMatrixPtr constructFromSequence( size_t width, size_t height, object o )
{
	if( (size_t)boost::python::len( o ) != width * height )
	{
		PyErr_SetString( PyExc_ValueError, "List length does not match matrix size" );
		throw_error_already_set();
	}
	ObjectMatrixPtr result = new ObjectMatrix( width, height );
	result->members().resize( 0 );
	container_utils::extend_container( result->members(), o );

	return result;
}

static size_t convertIndex( const ObjectMatrix &m, tuple xy )
{
	int64_t x = extract<int64_t>( xy[0] );
	if( x < 0 )
	{
		x += m.width();
	}
	if( x >= (int64_t)m.width() || x < 0 )
	{
		PyErr_SetString( PyExc_IndexError, "Index out of range" );
		throw_error_already_set();
	}

	int64_t y = extract<int64_t>( xy[1] );
	if( y < 0 )
	{
		y += m.height();
	}
	if( y >= (int64_t)m.height() || y < 0 )
	{
		PyErr_SetString( PyExc_IndexError, "Index out of range" );
		throw_error_already_set();
	}

	return y * m.width() + x;
}

std::string repr( const ObjectMatrix &m )
{
	std::stringstream s;

	s << fmt::format( "Gaffer.ObjectMatrix( {}, {},", m.width(), m.height() );

	if( m.members().size() )
	{
		s << " [ ";

		for( size_t i = 0, e = m.members().size(); i < e; i++ )
		{
			object item( m.members()[i] );
			std::string v = call_method< std::string >( item.ptr(), "__repr__" );
			s << v << ", ";
		}

		s << "] ";
	}

	s << ")";

	return s.str();
}

IECore::ObjectPtr getItem( const ObjectMatrix &m, tuple xy )
{
	return m.members()[ convertIndex( m, xy ) ];
}

void setItem( ObjectMatrix &m, tuple xy, IECore::ObjectPtr value )
{
	if( !value )
	{
		PyErr_SetString( PyExc_ValueError, "Invalid Object pointer" );
		throw_error_already_set();
	}

	m.members()[ convertIndex( m, xy ) ] = value;
}

} // namespace

void GafferModule::bindObjectMatrix()
{
	RunTimeTypedClass<ObjectMatrix>()
		.def( init< size_t, size_t >() )
		.def( "__init__", make_constructor( &constructFromSequence ) )
		.def( "__len__", &ObjectMatrix::height )
		.def( "__repr__", &repr )
		.def( "__getitem__", &getItem )
		.def( "__setitem__", &setItem )
		.def( "width", &ObjectMatrix::width )
		.def( "height", &ObjectMatrix::height )
		.def( "value", &ObjectMatrix::value )
	;
}
