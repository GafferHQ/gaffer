//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"

#include "Gaffer/BoxIn.h"
#include "Gaffer/BoxOut.h"
#include "Gaffer/Context.h"
#include "Gaffer/Dot.h"
#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"
#include "Gaffer/Switch.h"

#include "GafferBindings/PlugBinding.h"

#include "GafferBindings/MetadataBinding.h"

using namespace boost::python;
using namespace IECore;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

bool shouldSerialiseInput( const Plug *plug, const Serialisation &serialisation )
{
	if( !plug->getInput() )
	{
		return false;
	}

	if( auto parent = plug->parent<Plug>() )
	{
		if( parent->getInput() && parent != serialisation.parent() )
		{
			// Parent plug's input will have been serialised, so a serialisation
			// for the child would be redundant.
			return false;
		}
	}

	if( !plug->getFlags( Plug::Serialisable ) )
	{
		// Removing the Serialisable flag is a common way of
		// disabling serialisation of a `setInput()` call, but
		// it has problems :
		//
		// - Plug flags get propagated round by `Plug::createCounterpart()`,
		//   often in an unwanted fashion. Our goal should be to remove
		//   them entirely.
		// - It's too blunt an instrument. It disables all serialisation
		//   for the plug, including any metadata that has been registered.
		return false;
	}

	// Because of the problems with using Plug::Serialisable, it seems we
	// need a mechanism for a node to say whether or not an input needs to
	// be serialised. Options might include :
	//
	// 1. Adding a `virtual bool Node::serialiseInput( const Plug * ) const`
	//    method that can be overridden by subclasses. This would be pretty
	//    convenient, but it would blur the separation between the Gaffer
	//    and GafferBindings libraries. Maybe we can justify this because it's
	//    not actually a dependency on Python, and doesn't know anything about
	//    the serialisation format. In other words, maybe it's OK for a node
	//    to know _what_ needs to be serialised, as long as it doesn't know
	//    _how_. It seems that if we had similar `bool GraphComponent::serialiseChild()`
	//    and `bool GraphComponent::serialiseChildConstructor()` methods, we
	//    could actually ditch a fair proportion of custom serialisers, which
	//    might be nice.
	//
	// 2. Adding a `virtual bool NodeSerialiser::serialiseInput( const Plug * )`
	//    method, and finding the registered serialiser for the node in `postHierarchy()`
	//    below. This is purer, but probably a bit more of a faff in practice.
	//
	// 3. Coming up with a sensible rule that doesn't require more API. Perhaps
	//    we only need to serialise internal connections if they come from a
	//    child node which itself is serialised? It sure would be nice to simplify
	//    all this serialisation logic, and if a simple rule allows us to avoid
	//    greater complexity, that would be great.
	//
	// In lieu of a decision on this, for now we just hardcode the end result
	// we want, which is to omit serialisation for the internal connections of
	// the nodes below...

	if( auto boxIn = runTimeCast<const BoxIn>( plug->node() ) )
	{
		if( plug == boxIn->plug() )
		{
			return false;
		}
	}
	else if( runTimeCast<const BoxOut>( plug->node() ) )
	{
		if( plug->getName() == "__out" )
		{
			return false;
		}
	}
	else if( auto dot = runTimeCast<const Dot>( plug->node() ) )
	{
		if( plug == dot->outPlug() )
		{
			return false;
		}
	}
	else if( auto sw = runTimeCast<const Switch>( plug->node() ) )
	{
		if( plug == sw->outPlug() )
		{
			return false;
		}
	}

	return true;
}

const IECore::InternedString g_includeParentPlugMetadata( "plugSerialiser:includeParentPlugMetadata" );

} // namespace

void PlugSerialiser::moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const
{
	Serialiser::moduleDependencies( graphComponent, modules, serialisation );
	metadataModuleDependencies( static_cast<const Plug *>( graphComponent ), modules );
}

std::string PlugSerialiser::constructor( const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation ) const
{
	return repr( static_cast<const Plug *>( graphComponent ) );
}

std::string PlugSerialiser::postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const
{
	const Plug *plug = static_cast<const Plug *>( graphComponent );

	std::string result = Serialiser::postHierarchy( graphComponent, identifier, serialisation );

	if( shouldSerialiseInput( plug, serialisation ) )
	{
		std::string inputIdentifier = serialisation.identifier( plug->getInput() );
		if( inputIdentifier.size() )
		{
			result += identifier + ".setInput( " + inputIdentifier + " )\n";
		}
	}

	bool shouldSerialiseMetadata = true;
	if( plug->node() == serialisation.parent() )
	{
		shouldSerialiseMetadata = Context::current()->get<bool>( g_includeParentPlugMetadata, true );
	}
	if( shouldSerialiseMetadata )
	{
		result += metadataSerialisation( plug, identifier );
	}

	return result;
}

bool PlugSerialiser::childNeedsSerialisation( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const
{
	// cast is safe because of constraints maintained by Plug::acceptsChild().
	const Plug *childPlug = static_cast<const Plug *>( child );
	return childPlug->getFlags( Plug::Serialisable );
}

bool PlugSerialiser::childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const
{
	// cast is safe because of constraints maintained by Plug::acceptsChild().
	const Plug *childPlug = static_cast<const Plug *>( child );
	return childPlug->getFlags( Plug::Dynamic | Plug::Serialisable );
}

std::string PlugSerialiser::directionRepr( Plug::Direction direction )
{
	switch( direction )
	{
		case Plug::In :
			return "Gaffer.Plug.Direction.In";
		case Plug::Out :
			return "Gaffer.Plug.Direction.Out";
		default :
			return "Gaffer.Plug.Direction.Invalid";
	}
}

std::string PlugSerialiser::flagsRepr( unsigned flags )
{
	static const Plug::Flags values[] = { Plug::Dynamic, Plug::Serialisable, Plug::AcceptsInputs, Plug::Cacheable, Plug::AcceptsDependencyCycles, Plug::None };
	static const char *names[] = { "Dynamic", "Serialisable", "AcceptsInputs", "Cacheable", "AcceptsDependencyCycles", nullptr };

	int defaultButOffCount = 0;
	std::string defaultButOff;
	std::string nonDefaultButOn;
	for( int i=0; names[i]; i++ )
	{
		std::string *s = nullptr;
		if( flags & values[i] )
		{
			if( !(values[i] & Plug::Default) )
			{
				s = &nonDefaultButOn;
			}
		}
		else
		{
			if( values[i] & Plug::Default )
			{
				s = &defaultButOff;
				defaultButOffCount += 1;
			}
		}

		if( s )
		{
			if( s->size() )
			{
				*s += " | ";
			}
			*s += std::string( "Gaffer.Plug.Flags." ) + names[i];
		}
	}

	std::string result = "Gaffer.Plug.Flags.Default";
	if( nonDefaultButOn.size() )
	{
		result += " | " + nonDefaultButOn;
		if( defaultButOffCount )
		{
			result = "( " + result + " )";
		}
	}

	if( defaultButOffCount > 1 )
	{
		result += " & ~( " + defaultButOff + " )";
	}
	else if( defaultButOffCount == 1 )
	{
		result += " & ~" + defaultButOff;
	}

	return result;
}

std::string PlugSerialiser::repr( const Plug *plug, unsigned flagsMask )
{
	std::string result = Serialisation::classPath( plug ) + "( \"" + plug->getName().string() + "\", ";

	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + PlugSerialiser::directionRepr( plug->direction() ) + ", ";
	}

	const unsigned flags = plug->getFlags() & flagsMask;
	if( flags != Plug::Default )
	{
		result += "flags = " + PlugSerialiser::flagsRepr( flags ) + ", ";
	}

	result += ")";

	return result;
}

