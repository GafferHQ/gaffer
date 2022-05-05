//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/Private/IECoreScenePreview/Placeholder.h"

#include "IECore/MessageHandler.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreScenePreview;

const unsigned int Placeholder::m_ioVersion = 0;
IE_CORE_DEFINEOBJECTTYPEDESCRIPTION( Placeholder );

Placeholder::Placeholder( const Imath::Box3f &bound )
	:	m_bound( bound )
{
}

void Placeholder::setBound( const Imath::Box3f &bound )
{
	m_bound = bound;
}

const Imath::Box3f &Placeholder::getBound() const
{
	return m_bound;
}

Imath::Box3f Placeholder::bound() const
{
	return m_bound;
}

void Placeholder::render( Renderer *renderer ) const
{
	msg( Msg::Warning, "Placeholder::render", "Legacy renderers not supported" );
}

bool Placeholder::isEqualTo( const IECore::Object *other ) const
{
	if( !VisibleRenderable::isEqualTo( other ) )
	{
		return false;
	}

	return m_bound == static_cast<const Placeholder *>( other )->m_bound;
}

void Placeholder::hash( IECore::MurmurHash &h ) const
{
	VisibleRenderable::hash( h );
	h.append( m_bound );
}

void Placeholder::copyFrom( const IECore::Object *other, IECore::Object::CopyContext *context )
{
	VisibleRenderable::copyFrom( other, context );
	m_bound = static_cast<const Placeholder *>( other )->m_bound;
}

void Placeholder::save( IECore::Object::SaveContext *context ) const
{
	VisibleRenderable::save( context );

	IndexedIOPtr container = context->container( staticTypeName(), m_ioVersion );
	container->write( "bound", m_bound.min.getValue(), 6 );
}

void Placeholder::load( IECore::Object::LoadContextPtr context )
{
	VisibleRenderable::load( context );

	unsigned int v = m_ioVersion;
	ConstIndexedIOPtr container = context->container( staticTypeName(), v );
	float *b = m_bound.min.getValue();
	container->read( "bound", b, 6 );
}

void Placeholder::memoryUsage( IECore::Object::MemoryAccumulator &accumulator ) const
{
	VisibleRenderable::memoryUsage( accumulator );
	accumulator.accumulate( sizeof( m_bound ) );
}
