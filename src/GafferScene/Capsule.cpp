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

#include "GafferScene/Capsule.h"

#include "GafferScene/RendererAlgo.h"
#include "GafferScene/ScenePlug.h"

#include "Gaffer/Node.h"

#include "IECore/MessageHandler.h"

#include "boost/bind.hpp"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINEOBJECTTYPEDESCRIPTION( Capsule );

Capsule::Capsule()
	:	m_scene( nullptr )
{
}

Capsule::Capsule(
	const ScenePlug *scene,
	const ScenePlug::ScenePath &root,
	const Gaffer::Context &context,
	const IECore::MurmurHash &hash,
	const Imath::Box3f &bound
)
	:	m_hash( hash ), m_bound( bound ), m_scene( nullptr ), m_root( root ), m_context( new Gaffer::Context( context ) )
{
	setScene( scene );
}

Capsule::~Capsule()
{
	// Disconnect from signals
	setScene( nullptr );
}

void Capsule::setScene( const ScenePlug *scene )
{
	assert( !scene || scene->parent() );

	// Connecting to and disconnecting from signals is not threadsafe,
	// and neither is calling `GraphComponent::parentChangedSignal()`
	// (because it constructs signals lazily on demand). Most (all?)
	// other signal access occurs on the UI thread, but capsules are
	// constructed concurrently on background threads when generating
	// scenes. We use a mutex to serialise all signal access performed
	// by capsules, but this is still not safe with respect to signal
	// access that may be performed by UI components on the main thread.
	//
	// Todo : Make this watertight. Possibilities include :
	//
	// - Switching to boost::signals2, which is threadsafe by default,
	//   and making the GraphComponent signal accessors threadsafe.
	// - Writing our own threadsafe signals classes which do exactly what
	//   we need, without the bloat of the boost versions. And making the
	//   GraphComponent signal accessors threadsafe.
	// - Ditching all the signal handling in capsules. It is only used
	//   to track the erroneous usage of "expired" capsules, which can
	//   only arise from bugs elsewhere. I can't recall seeing an expired
	//   capsule yet.
	static tbb::spin_mutex g_signalMutex;
	tbb::spin_mutex::scoped_lock signalLock( g_signalMutex );

	if( const Node *node = m_scene ? m_scene->node() : nullptr )
	{
		const_cast<Node *>( node )->plugDirtiedSignal().disconnect(
			boost::bind( &Capsule::plugDirtied, this, ::_1 )
		);
	}
	if( m_scene )
	{
		const_cast<ScenePlug *>( m_scene )->parentChangedSignal().disconnect(
			boost::bind( &Capsule::parentChanged, this, ::_1 )
		);
	}

	m_scene = scene;

	if( m_scene )
	{
		const_cast<ScenePlug *>( m_scene )->parentChangedSignal().connect(
			boost::bind( &Capsule::parentChanged, this, ::_1 )
		);
	}
	if( const Node *node = m_scene ? m_scene->node() : nullptr )
	{
		const_cast<Node *>( node )->plugDirtiedSignal().connect(
			boost::bind( &Capsule::plugDirtied, this, ::_1 )
		);
	}

}

bool Capsule::isEqualTo( const IECore::Object *other ) const
{
	if( !Procedural::isEqualTo( other ) )
	{
		return false;
	}

	const Capsule *capsule = static_cast<const Capsule *>( other );
	return m_hash == capsule->m_hash;
}

void Capsule::hash( IECore::MurmurHash &h ) const
{
	throwIfExpired();

	Procedural::hash( h );
	h.append( m_hash );
}

void Capsule::copyFrom( const IECore::Object *other, IECore::Object::CopyContext *context )
{
	Procedural::copyFrom( other, context );

	const Capsule *capsule = static_cast<const Capsule *>( other );
	m_hash = capsule->m_hash;
	m_bound = capsule->m_bound;
	m_root = capsule->m_root;
	m_context = capsule->m_context;
	setScene( capsule->m_scene );
}

void Capsule::save( IECore::Object::SaveContext *context ) const
{
	Procedural::save( context );
	/// \todo Can we implement saving by serialising the
	/// Gaffer script into the IndexedIO file?
	msg( Msg::Warning, "Capsule::save", "Not implemented" );
}

void Capsule::load( IECore::Object::LoadContextPtr context )
{
	Procedural::load( context );
	msg( Msg::Warning, "Capsule::load", "Not implemented" );
}

void Capsule::memoryUsage( IECore::Object::MemoryAccumulator &accumulator ) const
{
	Procedural::memoryUsage( accumulator );
	accumulator.accumulate( sizeof( Capsule ) );
}

Imath::Box3f Capsule::bound() const
{
	throwIfExpired();
	return m_bound;
}

void Capsule::render( IECoreScenePreview::Renderer *renderer ) const
{
	throwIfExpired();
	ScenePlug::GlobalScope scope( m_context.get() );
	IECore::ConstCompoundObjectPtr globals = m_scene->globalsPlug()->getValue();
	RendererAlgo::RenderSets renderSets( m_scene );
	RendererAlgo::outputObjects( m_scene, globals.get(), renderSets, /* lightLinks = */ nullptr, renderer, m_root );
}

const ScenePlug *Capsule::scene() const
{
	throwIfExpired();
	return m_scene;
}

const ScenePlug::ScenePath &Capsule::root() const
{
	throwIfExpired();
	return m_root;
}

const Gaffer::Context *Capsule::context() const
{
	throwIfExpired();
	return m_context.get();
}

void Capsule::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug->parent() == m_scene && plug != m_scene->globalsPlug() )
	{
		// Our hash is based on the state of the graph at the
		// moment we were constructed. If the graph has subsequently
		// changed then we are no longer valid. Mark ourselves as
		// expired.
		setScene( nullptr );
	}
}

void Capsule::parentChanged( const Gaffer::GraphComponent *graphComponent )
{
	assert( graphComponent == m_scene );
	setScene( nullptr );
}

void Capsule::throwIfExpired() const
{
	if( !m_scene )
	{
		throw IECore::Exception( "Capsule has expired" );
	}
}

