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

#include "GafferScene/InteractiveRender.h"

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

	plugInputChangedSignal().connect( boost::bind( &InteractiveRender::plugInputChanged, this, ::_1 ) );
	plugSetSignal().connect( boost::bind( &InteractiveRender::plugSetOrDirtied, this, ::_1 ) );
	plugDirtiedSignal().connect( boost::bind( &InteractiveRender::plugSetOrDirtied, this, ::_1 ) );
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
}

void InteractiveRender::start()
{
	m_renderer = createRenderer();
	m_renderer->setOption( "editable", new BoolData( true ) );
	outputScene( inPlug(), m_renderer.get() );
}

void InteractiveRender::update()
{
	if( updateLightsPlug()->getValue() )
	{
		updateLights();
	}
}

void InteractiveRender::updateLights()
{
	ConstCompoundObjectPtr globals = inPlug()->globalsPlug()->getValue();
	m_renderer->editBegin( "light", CompoundDataMap() );
		outputLights( inPlug(), globals, m_renderer );
	m_renderer->editEnd();
}
