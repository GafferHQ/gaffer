//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Private/IECoreScenePreview/Geometry.h"

#include "IECore/MessageHandler.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreScenePreview;

const unsigned int Geometry::m_ioVersion = 0;
IE_CORE_DEFINEOBJECTTYPEDESCRIPTION( Geometry );

Geometry::Geometry( const std::string &type, const Imath::Box3f &bound, const IECore::CompoundDataPtr &parameters )
	:	m_type( type ), m_bound( bound ), m_parameters( parameters ? parameters : new CompoundData )
{
}

void Geometry::setType( const std::string &type )
{
	m_type = type;
}

const std::string &Geometry::getType() const
{
	return m_type;
}

void Geometry::setBound( const Imath::Box3f &bound )
{
	m_bound = bound;
}

const Imath::Box3f &Geometry::getBound() const
{
	return m_bound;
}

IECore::CompoundData *Geometry::parameters()
{
	return m_parameters.get();
}

const IECore::CompoundData *Geometry::parameters() const
{
	return m_parameters.get();
}

Imath::Box3f Geometry::bound() const
{
	return m_bound;
}

void Geometry::render( Renderer *renderer ) const
{
	msg( Msg::Warning, "Geometry::render", "Legacy renderers not supported" );
}

bool Geometry::isEqualTo( const IECore::Object *other ) const
{
	if( !VisibleRenderable::isEqualTo( other ) )
	{
		return false;
	}

	const Geometry *geometry = static_cast<const Geometry *>( other );
	return
		m_type == geometry->m_type &&
		m_bound == geometry->m_bound &&
		m_parameters->isEqualTo( geometry->m_parameters.get() )
	;

}

void Geometry::hash( IECore::MurmurHash &h ) const
{
	VisibleRenderable::hash( h );
	h.append( m_type );
	h.append( m_bound );
	m_parameters->hash( h );
}

void Geometry::copyFrom( const IECore::Object *other, IECore::Object::CopyContext *context )
{
	VisibleRenderable::copyFrom( other, context );

	const Geometry *geometry = static_cast<const Geometry *>( other );
	m_type = geometry->m_type;
	m_bound = geometry->m_bound;
	m_parameters = context->copy( geometry->m_parameters.get() );
}

void Geometry::save( IECore::Object::SaveContext *context ) const
{
	VisibleRenderable::save( context );

	IndexedIOPtr container = context->container( staticTypeName(), m_ioVersion );
	container->write( "type", m_type );
	container->write( "bound", m_bound.min.getValue(), 6 );
	context->save( m_parameters.get(), container.get(), "parameters" );
}

void Geometry::load( IECore::Object::LoadContextPtr context )
{
	VisibleRenderable::load( context );

	unsigned int v = m_ioVersion;
	ConstIndexedIOPtr container = context->container( staticTypeName(), v );
	container->read( "type", m_type );
	float *b = m_bound.min.getValue();
	container->read( "bound", b, 6 );
	m_parameters = context->load<CompoundData>( container.get(), "parameters" );
}

void Geometry::memoryUsage( IECore::Object::MemoryAccumulator &accumulator ) const
{
	VisibleRenderable::memoryUsage( accumulator );
	accumulator.accumulate( m_type.capacity() );
	accumulator.accumulate( sizeof( m_bound ) );
	accumulator.accumulate( m_parameters.get() );
}
