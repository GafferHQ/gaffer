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

#include "GafferScene/Private/RendererAlgo.h"
#include "GafferScene/ScenePlug.h"

#include "Gaffer/Node.h"

#include "IECore/MessageHandler.h"

#include "boost/bind/bind.hpp"

#include <mutex>
#include <unordered_map>

using namespace boost::placeholders;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

	Gaffer::Context *capsuleContext( const Context &context )
	{
		Gaffer::Context *result = new Gaffer::Context( context );

		// We don't want to include the scenePath of the original location of the capsule
		// as part of the context used downstream to evaluate the insides of the capsule
		result->remove( ScenePlug::scenePathContextName );
		return result;
	}

// Deliberately "leaking" these variables to avoid static destruction order fiasco.
// Capsules may be held in the ValuePlug cache and destroyed during shutdown, and if
// the `RenderOptionsMap` is destroyed first then `~Capsule` will crash attempting
// to access it.
std::mutex *g_renderOptionsMutex = new std::mutex;
using RenderOptionsMap = std::unordered_map<const Capsule *, Private::RendererAlgo::RenderOptions>;
RenderOptionsMap *g_renderOptions = new RenderOptionsMap;

}

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
	:	m_hash( hash ), m_bound( bound ), m_scene( scene ), m_root( root ), m_context( capsuleContext( context ) )
{
}

Capsule::~Capsule()
{
	std::unique_lock renderOptionsLock( *g_renderOptionsMutex );
	g_renderOptions->erase( this );
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
	throwIfNoScene();

	Procedural::hash( h );
	h.append( m_hash );

	if( auto renderOptions = getRenderOptions() )
	{
		// Hash only what affects our rendering, not everything in
		// `RenderOptions::globals`.
		h.append( renderOptions->transformBlur );
		h.append( renderOptions->deformationBlur );
		h.append( renderOptions->shutter );
		renderOptions->includedPurposes->hash( h );
	}
}

void Capsule::copyFrom( const IECore::Object *other, IECore::Object::CopyContext *context )
{
	Procedural::copyFrom( other, context );

	const Capsule *capsule = static_cast<const Capsule *>( other );
	m_hash = capsule->m_hash;
	m_bound = capsule->m_bound;
	m_scene = capsule->m_scene;
	m_root = capsule->m_root;
	m_context = capsule->m_context;
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
	throwIfNoScene();
	return m_bound;
}

void Capsule::render( IECoreScenePreview::Renderer *renderer ) const
{
	throwIfNoScene();
	ScenePlug::GlobalScope scope( m_context.get() );
	const GafferScene::Private::RendererAlgo::RenderOptions renderOpts = renderOptions();
	GafferScene::Private::RendererAlgo::RenderSets renderSets( m_scene );
	GafferScene::Private::RendererAlgo::outputObjects( m_scene, renderOpts, renderSets, /* lightLinks = */ nullptr, renderer, m_root );
}

const ScenePlug *Capsule::scene() const
{
	throwIfNoScene();
	return m_scene;
}

const ScenePlug::ScenePath &Capsule::root() const
{
	throwIfNoScene();
	return m_root;
}

const Gaffer::Context *Capsule::context() const
{
	throwIfNoScene();
	return m_context.get();
}

void Capsule::setRenderOptions( const GafferScene::Private::RendererAlgo::RenderOptions &renderOptions )
{
	// This is not pretty, but it allows the capsule to render with the correct
	// motion blur and `includedPurposes`, taken from the downstream node being
	// rendered rather than from the capsule's own globals.
	std::unique_lock renderOptionsLock( *g_renderOptionsMutex );
	(*g_renderOptions)[this] = renderOptions;
}

std::optional<GafferScene::Private::RendererAlgo::RenderOptions> Capsule::getRenderOptions() const
{
	std::unique_lock renderOptionsLock( *g_renderOptionsMutex );
	auto it = g_renderOptions->find( this );
	if( it != g_renderOptions->end() )
	{
		return it->second;
	}
	return std::nullopt;
}

GafferScene::Private::RendererAlgo::RenderOptions Capsule::renderOptions() const
{
	std::optional<GafferScene::Private::RendererAlgo::RenderOptions> renderOptions = getRenderOptions();
	if( renderOptions )
	{
		return *renderOptions;
	}
	else
	{
		return GafferScene::Private::RendererAlgo::RenderOptions( m_scene );
	}
}

void Capsule::throwIfNoScene() const
{
	if( !m_scene )
	{
		throw IECore::Exception( "No scene" );
	}
}
