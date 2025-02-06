//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023,  Cinesite VFX Ltd. All rights reserved.
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

#include "GafferImage/OpenColorIOConfigPlug.h"

#include "GafferImage/OpenColorIOAlgo.h"

#include "Gaffer/Context.h"

#include "Gaffer/NameValuePlug.h"

#include "boost/bind/bind.hpp"

#include <unordered_set>

using namespace std;
using namespace boost::placeholders;
using namespace Gaffer;
using namespace GafferImage;

namespace
{

const IECore::InternedString g_defaultConfigPlugName( "openColorIO" );

} // namespace

GAFFER_PLUG_DEFINE_TYPE( OpenColorIOConfigPlug );

OpenColorIOConfigPlug::OpenColorIOConfigPlug( const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags )
{
	const unsigned childFlags = flags & ~Dynamic;
	addChild( new StringPlug( "config", direction, "", childFlags ) );
	addChild( new StringPlug( "workingSpace", direction, OCIO_NAMESPACE::ROLE_SCENE_LINEAR, childFlags ) );
	addChild( new ValuePlug( "variables", direction, childFlags ) );
	addChild( new StringPlug( "displayTransform", direction, "__default__", childFlags ) );
}

Gaffer::StringPlug *OpenColorIOConfigPlug::configPlug()
{
	return getChild<StringPlug>( 0 );
}

const Gaffer::StringPlug *OpenColorIOConfigPlug::configPlug() const
{
	return getChild<StringPlug>( 0 );
}

Gaffer::StringPlug *OpenColorIOConfigPlug::workingSpacePlug()
{
	return getChild<StringPlug>( 1 );
}

const Gaffer::StringPlug *OpenColorIOConfigPlug::workingSpacePlug() const
{
	return getChild<StringPlug>( 1 );
}

Gaffer::ValuePlug *OpenColorIOConfigPlug::variablesPlug()
{
	return getChild<ValuePlug>( 2 );
}

const Gaffer::ValuePlug *OpenColorIOConfigPlug::variablesPlug() const
{
	return getChild<ValuePlug>( 2 );
}

Gaffer::StringPlug *OpenColorIOConfigPlug::displayTransformPlug()
{
	return getChild<StringPlug>( 3 );
}

const Gaffer::ValuePlug *OpenColorIOConfigPlug::displayTransformPlug() const
{
	return getChild<StringPlug>( 3 );
}

bool OpenColorIOConfigPlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	return
		ValuePlug::acceptsChild( potentialChild ) &&
		children().size() < 4
	;
}

Gaffer::PlugPtr OpenColorIOConfigPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new OpenColorIOConfigPlug( name, direction, getFlags() );
}

OpenColorIOConfigPlug *OpenColorIOConfigPlug::acquireDefaultConfigPlug( Gaffer::ScriptNode *scriptNode, bool createIfNecessary )
{
	if( auto plug = scriptNode->getChild<OpenColorIOConfigPlug>( g_defaultConfigPlugName ) )
	{
		return plug;
	}

	if( !createIfNecessary )
	{
		return nullptr;
	}

	Ptr plug = new OpenColorIOConfigPlug( g_defaultConfigPlugName, Plug::In, Plug::Default | Plug::Dynamic );
	scriptNode->setChild( g_defaultConfigPlugName, plug );
	return plug.get();
}

void OpenColorIOConfigPlug::parentChanged( Gaffer::GraphComponent *oldParent )
{
	ValuePlug::parentChanged( oldParent );

	m_plugSetConnection.disconnect();
	if( getName() != g_defaultConfigPlugName )
	{
		return;
	}

	if( auto scriptNode = parent<ScriptNode>() )
	{
		// We are the default config plug.
		m_plugSetConnection = scriptNode->plugSetSignal().connect(
			boost::bind( &OpenColorIOConfigPlug::plugSet, this, ::_1 )
		);
		plugSet( this );
	}
}

void OpenColorIOConfigPlug::plugSet( Gaffer::Plug *plug )
{
	if( plug != this )
	{
		return;
	}

	auto *scriptNode = parent<ScriptNode>();
	assert( scriptNode );

	OpenColorIOAlgo::setConfig( scriptNode->context(), configPlug()->getValue() );
	OpenColorIOAlgo::setWorkingSpace( scriptNode->context(), workingSpacePlug()->getValue() );

	// Add variables

	std::unordered_set<string> validVariables;
	for( const auto &variable : NameValuePlug::Range( *variablesPlug() ) )
	{
		if( auto enabledPlug = variable->enabledPlug() )
		{
			if( !enabledPlug->getValue() )
			{
				continue;
			}
		}

		const string name = scriptNode->context()->substitute( variable->namePlug()->getValue() );
		if( name.empty() )
		{
			continue;
		}

		if( auto stringPlug = variable->valuePlug<StringPlug>() )
		{
			OpenColorIOAlgo::addVariable( scriptNode->context(), name, stringPlug->getValue() );
			validVariables.insert( name );
		}
		else
		{
			throw IECore::Exception( fmt::format( "Variable {} is {}, but must be StringPlug", name, variable->valuePlug()->typeName() ) );
		}
	}

	// Remove old variables we don't want. We do this individually rather than clearing all variables
	// and then adding the ones we want, because it minimises the number of changes made to the context.
	// That minimises `Context::changedSignal()` emissions, which minimises the amount of work that
	// observers do.

	for( const auto &name : OpenColorIOAlgo::variables( scriptNode->context() ) )
	{
		if( validVariables.find( name ) == validVariables.end() )
		{
			OpenColorIOAlgo::removeVariable( scriptNode->context(), name );
		}
	}
}
