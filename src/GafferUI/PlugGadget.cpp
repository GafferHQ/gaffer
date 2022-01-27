//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferUI/PlugGadget.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"

#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace boost::placeholders;
using namespace GafferUI;
using namespace Gaffer;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( PlugGadget );

PlugGadget::PlugGadget( Gaffer::PlugPtr plug )
	:	ContainerGadget( defaultName<PlugGadget>() ), m_plug( nullptr )
{
	setPlug( plug );
}

PlugGadget::~PlugGadget()
{
}

void PlugGadget::setPlug( Gaffer::PlugPtr plug )
{
	if( plug == m_plug )
	{
		return;
	}

	m_plug = plug;

	Node *node = m_plug->node();

	m_plugDirtiedConnection = node->plugDirtiedSignal().connect( boost::bind( &PlugGadget::plugDirtied, this, ::_1 ) );
	m_plugInputChangedConnection = node->plugInputChangedSignal().connect( boost::bind( &PlugGadget::plugInputChanged, this, ::_1 ) );

	m_context = node->scriptNode()->context();
	updateContextConnection();
	updateFromPlug();
}

void PlugGadget::setContext( Gaffer::ContextPtr context )
{
	if( context == m_context )
	{
		return;
	}

	m_context = context;
	updateContextConnection();
	updateFromPlug();
}

Gaffer::Context *PlugGadget::getContext()
{
	return m_context.get();
}

void PlugGadget::updateFromPlug()
{
}

void PlugGadget::plugDirtied( Gaffer::Plug *plug )
{
	if( plug == m_plug )
	{
		updateFromPlug();
	}
}

void PlugGadget::plugInputChanged( Gaffer::Plug *plug )
{
	if( plug == m_plug )
	{
		updateContextConnection();
		updateFromPlug();
	}
}

void PlugGadget::contextChanged( const Gaffer::Context *context, const IECore::InternedString &name )
{
	updateFromPlug();
}

void PlugGadget::updateContextConnection()
{
	Context *context = m_context.get();
	if( !m_plug->getInput() )
	{
		// we only want to be notified of context changes if the plug has an incoming
		// connection. otherwise context changes are irrelevant and we'd just be slowing
		// things down by asking for notifications.
		context = nullptr;
	}

	if( context )
	{
		m_contextChangedConnection = context->changedSignal().connect( boost::bind( &PlugGadget::contextChanged, this, ::_1, ::_2 ) );
	}
	else
	{
		m_contextChangedConnection.disconnect();
	}
}
