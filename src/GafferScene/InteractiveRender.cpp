//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/InteractiveRender.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/SceneNode.h"
#include "GafferScene/SceneProcessor.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"

#include "IECoreScene/Transform.h"
#include "IECoreScene/VisibleRenderable.h"

#include "IECore/MessageHandler.h"
#include "IECore/NullObject.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

static InternedString g_rendererContextName( "scene:renderer" );

size_t InteractiveRender::g_firstPlugIndex = 0;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( InteractiveRender );

InteractiveRender::InteractiveRender( const std::string &name )
	:	InteractiveRender( /* rendererType = */ InternedString(), name )
{
}

InteractiveRender::InteractiveRender( const IECore::InternedString &rendererType, const std::string &name )
	:	Node( name ),
		m_state( Stopped )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in" ) );
	addChild( new StringPlug( rendererType.string().empty() ? "renderer" : "__renderer", Plug::In, rendererType.string() ) );
	addChild( new IntPlug( "state", Plug::In, Stopped, Stopped, Paused, Plug::Default & ~Plug::Serialisable ) );
	addChild( new ScenePlug( "out", Plug::Out, Plug::Default & ~Plug::Serialisable ) );
	addChild( new ScenePlug( "__adaptedIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	SceneProcessorPtr adaptors = RendererAlgo::createAdaptors();
	setChild( "__adaptors", adaptors );
	adaptors->inPlug()->setInput( inPlug() );
	adaptedInPlug()->setInput( adaptors->outPlug() );

	outPlug()->setInput( inPlug() );

	plugDirtiedSignal().connect( boost::bind( &InteractiveRender::plugDirtied, this, ::_1 ) );
}

InteractiveRender::~InteractiveRender()
{
	stop();
}

ScenePlug *InteractiveRender::inPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *InteractiveRender::inPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *InteractiveRender::rendererPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *InteractiveRender::rendererPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *InteractiveRender::statePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *InteractiveRender::statePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

ScenePlug *InteractiveRender::outPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 3 );
}

const ScenePlug *InteractiveRender::outPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 3 );
}

ScenePlug *InteractiveRender::adaptedInPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 4 );
}

const ScenePlug *InteractiveRender::adaptedInPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 4 );
}

Gaffer::Context *InteractiveRender::getContext()
{
	return m_context.get();
}

const Gaffer::Context *InteractiveRender::getContext() const
{
	return m_context.get();
}

void InteractiveRender::setContext( Gaffer::ContextPtr context )
{
	if( m_context == context )
	{
		return;
	}
	m_context = context;
	if( m_controller )
	{
		m_controller->setContext( effectiveContext() );
	}
}

void InteractiveRender::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == rendererPlug() || plug == statePlug() )
	{
		try
		{
			update();
		}
		catch( const std::exception &e )
		{
			errorSignal()( plug, plug, e.what() );
		}
	}
}

void InteractiveRender::update()
{
	const State requiredState = (State)statePlug()->getValue();

	// Stop the current render if we've been asked to, or if
	// there is no real input scene.

	if( requiredState == Stopped || inPlug()->source()->direction() != Plug::Out )
	{
		stop();
		return;
	}

	// If we've got this far, we know we want to be running or paused.
	// Start a render if we don't have one.

	if( !m_renderer )
	{
		m_renderer = IECoreScenePreview::Renderer::create(
			rendererPlug()->getValue(),
			IECoreScenePreview::Renderer::Interactive
		);
		m_controller.reset(
			new RenderController( adaptedInPlug(), effectiveContext(), m_renderer )
		);
		m_controller->setMinimumExpansionDepth( limits<size_t>::max() );
		m_controller->updateRequiredSignal().connect(
			boost::bind( &InteractiveRender::update, this )
		);
	}

	// We need to pause to make edits, even if we want to
	// be running in the end.
	m_renderer->pause();
	if( requiredState == Paused )
	{
		m_state = requiredState;
		return;
	}

	// We want to be running, so update the scene
	// and kick off a render.
	assert( requiredState == Running );

	m_controller->update();

	m_state = requiredState;
	m_renderer->render();
}

Gaffer::ConstContextPtr InteractiveRender::effectiveContext()
{
	if( m_context )
	{
		return m_context.get();
	}
	else if( ScriptNode *n = ancestor<ScriptNode>() )
	{
		return n->context();
	}
	else
	{
		return new Context();
	}
}

void InteractiveRender::stop()
{
	m_controller.reset();
	m_renderer.reset();
	m_state = Stopped;
}
