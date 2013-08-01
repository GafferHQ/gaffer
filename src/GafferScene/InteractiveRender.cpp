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

#include "boost/bind.hpp"

#include "Gaffer/ScriptNode.h"

#include "GafferScene/InteractiveRender.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( InteractiveRender );

size_t InteractiveRender::g_firstPlugIndex = 0;

InteractiveRender::InteractiveRender( const std::string &name )
	:	Render( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "state", Plug::In, Stopped, Stopped, Paused, Plug::Default & ~Plug::Serialisable ) );
	addChild( new BoolPlug( "updateLights", Plug::In, true ) );
	addChild( new BoolPlug( "updateShaders", Plug::In, true ) );

	plugInputChangedSignal().connect( boost::bind( &InteractiveRender::plugInputChanged, this, ::_1 ) );
	plugSetSignal().connect( boost::bind( &InteractiveRender::plugSetOrDirtied, this, ::_1 ) );
	plugDirtiedSignal().connect( boost::bind( &InteractiveRender::plugSetOrDirtied, this, ::_1 ) );
	parentChangedSignal().connect( boost::bind( &InteractiveRender::parentChanged, this, ::_1, ::_2 ) );
	
	setContext( new Context() );
}

InteractiveRender::~InteractiveRender()
{
}

Gaffer::IntPlug *InteractiveRender::statePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *InteractiveRender::statePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}
		
Gaffer::BoolPlug *InteractiveRender::updateLightsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *InteractiveRender::updateLightsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *InteractiveRender::updateShadersPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *InteractiveRender::updateShadersPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

void InteractiveRender::plugInputChanged( const Gaffer::Plug *plug )
{
	if( plug == inPlug() )
	{
		if( plug->getInput<Plug>() )
		{
			const State s = (State)statePlug()->getValue();
			if( s != Stopped )
			{
				start();
			}
		}
		else
		{
			m_renderer = 0;
		}
	}
}

void InteractiveRender::plugSetOrDirtied( const Gaffer::Plug *plug )
{
	if( plug == statePlug() )
	{
		const State s = (State)statePlug()->getValue();
		if( s == Stopped )
		{
			m_renderer = 0;
		}
		else
		{
			if( inPlug()->getInput<Plug>() )
			{
				// running or paused
				if( !m_renderer )
				{
					// going from stopped to running or paused
					start();
				}
				else if( s == Running )
				{
					// going from paused to running
					update();
				}
			}
		}
	}
	else if( plug == inPlug() )
	{
		if( m_renderer && statePlug()->getValue() == Running )
		{
			update();	
		}
	}
	else if( plug == updateLightsPlug() && updateLightsPlug()->getValue() && m_renderer )
	{
		updateLights();
	}
	else if( plug == updateShadersPlug() && updateShadersPlug()->getValue() && m_renderer )
	{
		updateShaders();
	}
}

void InteractiveRender::parentChanged( GraphComponent *child, GraphComponent *oldParent )
{
	ScriptNode *n = ancestor<ScriptNode>();
	if( n )
	{
		setContext( n->context() );
	}
	else
	{
		setContext( new Context() );
	}
}

void InteractiveRender::start()
{
	m_renderer = createRenderer();
	m_renderer->setOption( "editable", new BoolData( true ) );
	
	Context::Scope scopedContext( m_context );
	
	outputScene( inPlug(), m_renderer.get() );
}

void InteractiveRender::update()
{
	/// \todo Only update lights if objects/transforms have been dirtied,
	/// and only update shaders if attributes have been dirtied.
	if( updateLightsPlug()->getValue() )
	{
		updateLights();
	}
	if( updateShadersPlug()->getValue() )
	{
		updateShaders();
	}
}

void InteractiveRender::updateLights()
{
	Context::Scope scopedContext( m_context );
	
	ConstCompoundObjectPtr globals = inPlug()->globalsPlug()->getValue();
	m_renderer->editBegin( "light", CompoundDataMap() );
		outputLights( inPlug(), globals, m_renderer );
	m_renderer->editEnd();
}

void InteractiveRender::updateShaders( const ScenePlug::ScenePath &path )
{

	Context::Scope scopedContext( m_context );
	
	/// \todo Keep a track of the hashes of the shaders at each path,
	/// and use it to only update the shaders when they've changed.	
	ConstCompoundObjectPtr attributes = inPlug()->attributes( path );
	ConstObjectVectorPtr shader = attributes->member<ObjectVector>( "shader" );
	if( shader )
	{
		std::string name = "";
		for( ScenePlug::ScenePath::const_iterator it = path.begin(), eIt = path.end(); it != eIt; it++ )
		{
			name += "/" + it->string();
		}
		
		CompoundDataMap parameters;
		parameters["scopename"] = new StringData( name );
		m_renderer->editBegin( "attribute", parameters );
		
			for( ObjectVector::MemberContainer::const_iterator it = shader->members().begin(), eIt = shader->members().end(); it != eIt; it++ )
			{
				const StateRenderable *s = runTimeCast<const StateRenderable>( it->get() );
				if( s )
				{
					s->render( m_renderer );
				}
			}

		m_renderer->editEnd();
	}
	
	ConstInternedStringVectorDataPtr childNames = inPlug()->childNames( path );
	ScenePlug::ScenePath childPath = path;
	childPath.push_back( InternedString() ); // for the child name
	for( vector<InternedString>::const_iterator it=childNames->readable().begin(); it!=childNames->readable().end(); it++ )
	{
		childPath[path.size()] = *it;
		updateShaders( childPath );
	}
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
	m_context = context;
}
