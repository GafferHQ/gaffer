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

#include "Gaffer/Plug.h"
#include "Gaffer/Node.h"

#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/MetadataBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

void PlugSerialiser::moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const
{
	Serialiser::moduleDependencies( graphComponent, modules, serialisation );
	metadataModuleDependencies( static_cast<const Plug *>( graphComponent ), modules );
}

std::string PlugSerialiser::constructor( const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation ) const
{
	return repr( static_cast<const Plug *>( graphComponent ), Plug::All & ~Plug::ReadOnly );
}

std::string PlugSerialiser::postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
{
	const Plug *plug = static_cast<const Plug *>( graphComponent );
	if( plug->getFlags( Plug::Serialisable ) )
	{
		std::string result;
		std::string inputIdentifier = serialisation.identifier( plug->getInput() );
		if( inputIdentifier.size() )
		{
			result += identifier + ".setInput( " + inputIdentifier + " )\n";
		}
		if( plug->getFlags( Plug::ReadOnly ) )
		{
			result += identifier + ".setFlags( Gaffer.Plug.Flags.ReadOnly, True )\n";
		}

		result += metadataSerialisation( plug, identifier );

		return result;
	}
	return "";
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
	static const Plug::Flags values[] = { Plug::Dynamic, Plug::Serialisable, Plug::AcceptsInputs, Plug::PerformsSubstitutions, Plug::Cacheable, Plug::ReadOnly, Plug::AcceptsDependencyCycles, Plug::None };
	static const char *names[] = { "Dynamic", "Serialisable", "AcceptsInputs", "PerformsSubstitutions", "Cacheable", "ReadOnly", "AcceptsDependencyCycles", nullptr };

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

