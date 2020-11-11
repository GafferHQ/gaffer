//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "Gaffer/Random.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "OpenEXR/ImathColorAlgo.h"
#include "OpenEXR/ImathRandom.h"

#include "boost/functional/hash.hpp"

using namespace Gaffer;
using namespace Imath;

GAFFER_NODE_DEFINE_TYPE( Random );

size_t Random::g_firstPlugIndex = 0;

Random::Random( const std::string &name )
	:	ComputeNode( name )
{

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "seed", Plug::In, 0, 0 ) );
	addChild( new StringPlug( "contextEntry" ) );

	addChild( new V2fPlug( "floatRange", Plug::In, V2f( 0, 1 ) ) );
	addChild( new FloatPlug( "outFloat", Plug::Out ) );

	addChild( new Color3fPlug( "baseColor", Plug::In, Color3f( 0.712f, 0.704f, 0.666f ) ) );
	addChild( new FloatPlug( "hue", Plug::In, 0.2, 0.0, 1.0 ) );
	addChild( new FloatPlug( "saturation", Plug::In, 0.2, 0.0, 1.0 ) );
	addChild( new FloatPlug( "value", Plug::In, 0.2, 0.0, 1.0 ) );
	addChild( new Color3fPlug( "outColor", Plug::Out ) );

}

Random::~Random()
{
}

IntPlug *Random::seedPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const IntPlug *Random::seedPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

StringPlug *Random::contextEntryPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *Random::contextEntryPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

V2fPlug *Random::floatRangePlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

const V2fPlug *Random::floatRangePlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

FloatPlug *Random::outFloatPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const FloatPlug *Random::outFloatPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

Color3fPlug *Random::baseColorPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 4 );
}

const Color3fPlug *Random::baseColorPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 4 );
}

FloatPlug *Random::huePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

const FloatPlug *Random::huePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

FloatPlug *Random::saturationPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 6 );
}

const FloatPlug *Random::saturationPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 6 );
}

FloatPlug *Random::valuePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 7 );
}

const FloatPlug *Random::valuePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 7 );
}

Color3fPlug *Random::outColorPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 8 );
}

const Color3fPlug *Random::outColorPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 8 );
}

void Random::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == seedPlug() || input == contextEntryPlug() )
	{
		outputs.push_back( outFloatPlug() );
		for( ValuePlug::Iterator componentIt( outColorPlug() ); !componentIt.done(); ++componentIt )
		{
			outputs.push_back( componentIt->get() );
		}
	}
	else if( input->parent<Plug>() == floatRangePlug() )
	{
		outputs.push_back( outFloatPlug() );
	}
	else if(
		input->parent<Plug>() == baseColorPlug() ||
		input == huePlug() ||
		input == saturationPlug() ||
		input == valuePlug()
	)
	{
		for( ValuePlug::Iterator componentIt( outColorPlug() ); !componentIt.done(); ++componentIt )
		{
			outputs.push_back( componentIt->get() );
		}
	}
}

void Random::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == outFloatPlug() )
	{
		hashSeed( context, h );
		floatRangePlug()->hash( h );
	}
	else if( output->parent<Plug>() == outColorPlug() )
	{
		hashSeed( context, h );
		baseColorPlug()->hash( h );
		huePlug()->hash( h );
		saturationPlug()->hash( h );
		valuePlug()->hash( h );
	}
}

void Random::compute( ValuePlug *output, const Context *context ) const
{
	if( output == outFloatPlug() )
	{
		Rand48 random( computeSeed( context ) );
		V2f range = floatRangePlug()->getValue();
		static_cast<FloatPlug *>( output )->setValue( lerp( range[0], range[1], random.nextf() ) );
		return;
	}
	else if( output->parent<Plug>() == outColorPlug() )
	{
		Color3f c = randomColor( computeSeed( context ) );

		float result = 0;
		if( output == outColorPlug()->getChild( 0 ) )
		{
			result = c[0];
		}
		else if( output == outColorPlug()->getChild( 1 ) )
		{
			result = c[1];
		}
		else
		{
			result = c[2];
		}

		static_cast<FloatPlug *>( output )->setValue( result );
		return;
	}
	ComputeNode::compute( output, context );
}

Imath::Color3f Random::randomColor( unsigned long int seed ) const
{
	Rand48 random( seed );
	Color3f baseColor = baseColorPlug()->getValue();
	Color3f hsv = rgb2hsv( baseColor );

	hsv[0] += huePlug()->getValue() * random.nextf( -1.0f, 1.0f );
	if( hsv[0] < 0.0f )
	{
		hsv[0] += 1.0f;
	}
	else if( hsv[0] > 1.0f )
	{
		hsv[0] -= 1.0f;
	}

	hsv[1] *= 1.0f + saturationPlug()->getValue() * random.nextf( -1.0f, 1.0f );
	hsv[2] *= 1.0f + valuePlug()->getValue() * random.nextf( -1.0f, 1.0f );

	Color3f rgb = hsv2rgb( hsv );
	return rgb;
}

void Random::hashSeed( const Context *context, IECore::MurmurHash &h ) const
{
	seedPlug()->hash( h );
	std::string contextEntry = contextEntryPlug()->getValue();
	if( contextEntry.size() )
	{
		h.append( context->variableHash( contextEntry ).h1() );
	}
}

unsigned long int Random::computeSeed( const Context *context ) const
{
	unsigned long int seed = seedPlug()->getValue();
	std::string contextEntry = contextEntryPlug()->getValue();
	if( contextEntry.size() )
	{
		// \todo:  It is wasteful to call getAsData, allocating a fresh data here.
		// We should be able to just use `seed += context->variableHash( contextEntry ).h1()`,
		// however this would yield inconsistent hashes due to variableHash including the
		// entry name as the address of an internal string.  If we come up with a way to do
		// fast consistent hashes of InternedString ( ie. the proposal of storing a hash in
		// the InternedString table ) then we should switch this to the less wasteful version
		IECore::DataPtr contextData = context->getAsData( contextEntry, nullptr );
		if( contextData )
		{
			IECore::MurmurHash hash = contextData->Object::hash();
			/// \todo It'd be nice if there was a way of getting the hash folded into an
			/// int so we could avoid this jiggery pokery.
			std::string s = hash.toString();
			seed += boost::hash<std::string>()( s );
		}
	}
	return seed;
}
