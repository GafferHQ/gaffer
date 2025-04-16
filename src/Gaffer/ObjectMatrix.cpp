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

#include "Gaffer/ObjectMatrix.h"

#include "IECore/MurmurHash.h"

using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINEOBJECTTYPEDESCRIPTION( ObjectMatrix );

ObjectMatrix::ObjectMatrix( size_t width, size_t height )
	: m_width( width ), m_height( height )
{
	this->members().resize( width * height );
}

ObjectMatrix::~ObjectMatrix()
{
}

IECore::ObjectPtr ObjectMatrix::value( size_t x, size_t y ) const
{
	return this->members()[ y * m_width + x ];
}

size_t ObjectMatrix::width() const
{
	return m_width;
}

size_t ObjectMatrix::height() const
{
	return m_height;
}

void ObjectMatrix::copyFrom( const Object *other, CopyContext *context )
{
	ObjectVector::copyFrom( other, context );
	const ObjectMatrix *tOther = static_cast<const ObjectMatrix *>( other );
	m_width = tOther->m_width;
	m_height = tOther->m_height;
}

void ObjectMatrix::save( IECore::Object::SaveContext *context ) const
{
	Object::save( context );
	throw IECore::NotImplementedException( "ObjectMatrix::save" );
}

void ObjectMatrix::load( IECore::Object::LoadContextPtr context )
{
	Object::load( context );
	throw IECore::NotImplementedException( "ObjectMatrix::load" );
}

bool ObjectMatrix::isEqualTo( const Object *other ) const
{
	if( !ObjectVector::isEqualTo( other ) )
	{
		return false;
	}
	const ObjectMatrix *tOther = static_cast<const ObjectMatrix *>( other );
	if( m_height != tOther->m_height || m_width != tOther->m_width )
	{
		return false;
	}

	return true;
}

void ObjectMatrix::memoryUsage( Object::MemoryAccumulator &a ) const
{
	ObjectVector::memoryUsage( a );
	a.accumulate( sizeof( m_width ) );
	a.accumulate( sizeof( m_height ) );
}

void ObjectMatrix::hash( MurmurHash &h ) const
{
	ObjectVector::hash( h );
	h.append( m_width );
	h.append( m_height );
}
