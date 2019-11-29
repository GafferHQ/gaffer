//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

#include "Gaffer/EditScope.h"
#include "Gaffer/BoxIn.h"
#include "Gaffer/BoxOut.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/StringPlug.h"

#include <unordered_map>

using namespace std;
using namespace IECore;
using namespace Gaffer;

// Internals
// =========

namespace
{

using ProcessorMap = std::unordered_map<std::string, EditScope::ProcessorCreator>;
ProcessorMap &processorMap()
{
	static ProcessorMap g_m;
	return g_m;
}

std::vector<std::string> &processorNames()
{
	static std::vector<std::string> g_v;
	return g_v;
}

} // namespace

// EditScope
// =========

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( EditScope );

EditScope::EditScope( const std::string &name )
	:	Box( name )
{
}

EditScope::~EditScope()
{
}

void EditScope::setup( const Plug *plug )
{
	if( inPlug() || outPlug() )
	{
		throw IECore::Exception( "EditScope has been set up already." );
	}

	BoxInPtr boxIn = new BoxIn();
	addChild( boxIn );
	boxIn->namePlug()->setValue( "in" );
	boxIn->setup( plug );

	BoxOutPtr boxOut = new BoxOut();
	addChild( boxOut );
	boxOut->namePlug()->setValue( "out" );
	boxOut->setup( plug );

	boxOut->plug()->setInput( boxIn->plug() );
	boxOut->passThroughPlug()->setInput( boxIn->plug() );
}

std::vector<DependencyNode *> EditScope::processors()
{
	// To be a processor, a node must :
	//
	// - Have "editScope:processorType" metadata
	// - Be on the main path between `outPlug()` and `inPlug()`

	std::vector<DependencyNode *> result;

	const Plug *inPlug = this->inPlug();
	Plug *outPlug = this->outPlug();
	if( !inPlug || !outPlug )
	{
		return result;
	}

	auto *boxOut = this->boxOut();
	if( !boxOut )
	{
		throw IECore::Exception( "BoxOut node not found" );
	}

	Plug *plug = boxOut->plug();
	while( plug && plug != inPlug )
	{
		auto node = runTimeCast<DependencyNode>( plug->node() );
		if( node )
		{
			if( Metadata::value<StringData>( node, "editScope:processorType" ) )
			{
				result.push_back( node );
			}
		}

		if( plug->direction() == Plug::Out )
		{
			plug = node ? node->correspondingInput( plug )->getInput() : plug->getInput();
		}
		else
		{
			plug = plug->getInput();
		}
	}

	if( plug != inPlug )
	{
		throw IECore::Exception( "Output not linked to input" );
	}

	return result;
}

void EditScope::registerProcessor( const std::string &type, ProcessorCreator creator )
{
	auto inserted = processorMap().insert( { type, creator } );
	if( inserted.second )
	{
		processorNames().push_back( type );
	}
	else
	{
		inserted.first->second = creator;
	}
}

void EditScope::deregisterProcessor( const std::string &type )
{
	auto &m = processorMap();
	auto it = m.find( type );
	if( it != m.end() )
	{
		m.erase( it );
		processorNames().erase( std::find( processorNames().begin(), processorNames().end(), type ) );
	}
}

const std::vector<std::string> &EditScope::registeredProcessors()
{
	return processorNames();
}

BoxOut *EditScope::boxOut()
{
	auto out = outPlug();
	if( !out || !out->getInput() )
	{
		return nullptr;
	}
	return out->getInput()->parent<BoxOut>();
}

DependencyNode *EditScope::acquireProcessorInternal( const std::string &type, bool createIfNecessary )
{
	const Plug *inPlug = this->inPlug();
	Plug *outPlug = this->outPlug();
	if( !inPlug || !outPlug )
	{
		throw IECore::Exception( "EditScope has not been set up yet" );
	}

	// See if we already have the processor we want.

	vector<DependencyNode *> processors = this->processors();
	for( auto p : processors )
	{
		if( Metadata::value<StringData>( p, "editScope:processorType" )->readable() == type )
		{
			return p;
		}
	}

	if( !createIfNecessary )
	{
		return nullptr;
	}

	// Didn't find an existing processor. Make a new one.

	const auto &m = processorMap();
	const auto it = m.find( type );
	if( it == m.end() )
	{
		throw IECore::Exception( "Processor type " + type + " not registered" );
	}

	DependencyNodePtr processor = it->second();
	Plug *processorIn = processor->getChild<Plug>( "in" );
	Plug *processorOut = processor->getChild<Plug>( "out" );

	if( !processorIn || !processorOut )
	{
		throw IECore::Exception( "Processor does not have plugs named \"in\" and \"out\"" );
	}

	if( processor->correspondingInput( processorOut ) != processorIn )
	{
		throw IECore::Exception( "Processor does not have pass through between \"in\" and \"out\"" );
	}

	Metadata::registerValue( processor.get(), "editScope:processorType", new StringData( type ) );
	Metadata::registerValue( processor.get(), "icon", new StringData( "editScopeProcessorNode.png" ) );
	Metadata::registerValue( processor.get(), "nodeGadget:color", new Color3fData( Imath::Color3f( 0.1876, 0.3908, 0.6 ) ) );
	addChild( processor );

	processorIn->setInput( boxOut()->plug()->getInput() );
	boxOut()->plug()->setInput( processorOut );

	return processor.get();
}
