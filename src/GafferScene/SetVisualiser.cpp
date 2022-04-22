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

#include "GafferScene/SetVisualiser.h"

#include "GafferScene/SceneAlgo.h"

#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/StringPlug.h"

#include "IECoreScene/Shader.h"
#include "IECoreScene/ShaderNetwork.h"
#include "IECore/StringAlgo.h"

#include "OpenEXR/ImathColorAlgo.h"
#include "OpenEXR/ImathRandom.h"

#include "boost/algorithm/string/predicate.hpp"


using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

bool internedStringCompare( InternedString a, InternedString b )
{
	return a.string() < b.string();
}

using Override = std::pair<StringAlgo::MatchPattern, ConstColor3fDataPtr>;
std::vector<Override> unpackOverrides( const CompoundDataPlug *plug )
{
	std::vector<Override> overrides;

	std::string name;
	for( NameValuePlug::Iterator it( plug ); !it.done(); ++it )
	{
		// This will fail if the member has been disabled, or has no name
		if( ConstDataPtr plugData =  plug->memberDataAndName( it->get(), name ) )
		{
			if( ConstColor3fDataPtr asColor = runTimeCast<const Color3fData>( plugData ) )
			{
				overrides.push_back( Override( name, asColor ) );
			}
			else
			{
				throw IECore::Exception( boost::str( boost::format(
					"Color Override value for \"%s\" is not a Color3f") % name )
				);
			}
		}
	}
	return overrides;
}

Color3f colorForSetName( const InternedString &name, const std::vector<Override> &overrides )
{
	for( auto &override_ : overrides )
	{
		if( StringAlgo::matchMultiple( name, override_.first ) )
		{
			return override_.second->readable();
		}
	}

	// If we didn't have an override, make up a color
	Color3f color( 0.0f );
	Rand32 r( boost::hash<std::string>()( name.string() ) );
	// RGB generation seemed to yield many colours that were close
	// together. HSL seems to give better distribution over smaller
	// sample sizes... and then sometimes it doesn't.
	color[0] = r.nextf();                     // hue
	color[1] = 0.6f + ( r.nextf() * 0.25f );  // saturation
	color[2] = 0.35f + ( r.nextf() * 0.25f ); // lightness
	return hsv2rgb( color );
}

// We're limited in our target GLSL version to fixed size shader array params
size_t g_maxShaderColors = 9;

const StringDataPtr fragmentSource()
{
	static StringDataPtr g_fragmentSource = new IECore::StringData(
		"#if __VERSION__ <= 120\n"
		"#define in varying\n"
		"#endif\n"

		"#include \"IECoreGL/ColorAlgo.h\"\n"

		"uniform vec3 colors[" + std::to_string( g_maxShaderColors ) + "];"
		"uniform int numColors;"
		"uniform float stripeWidth;"

		"in vec3 fragmentN;"
		"in vec3 fragmentI;"

		"void main()"
		"{"
		"	float f = abs( dot( normalize( fragmentI ), normalize( fragmentN ) ) );"
		"	gl_FragColor = vec4( f, f, f, 1.0 );"
		"	if( numColors > 0 )"
		"	{"
		"		float stripeIndex = floor( (gl_FragCoord.x - gl_FragCoord.y) / stripeWidth );"
		"		stripeIndex = mod( stripeIndex, float(numColors) );"
		"		gl_FragColor = ( gl_FragColor * 0.8 + 0.2 ) * vec4( ieLinToSRGB( colors[ int(stripeIndex) ] ), 1.0);"
		"	}"
		"}"
	);
	return g_fragmentSource;
}

ShaderNetworkPtr stripeShader( float stripeWidth, size_t numColorsUsed, const std::vector<Color3f> &colors )
{
	// The shader name isn't used as we provide the src inline
	IECoreScene::ShaderPtr shader = new IECoreScene::Shader( "SetVisualiserSurface", "gl:surface" );
	shader->parameters()["stripeWidth"] = new FloatData( stripeWidth );
	shader->parameters()["numColors"] = new IntData( numColorsUsed );
	shader->parameters()["colors"] = new Color3fVectorData( colors );
	shader->parameters()["gl:fragmentSource"] = fragmentSource();

	ShaderNetworkPtr shaderNetwork = new ShaderNetwork;
	const InternedString handle = shaderNetwork->addShader( "surface", std::move( shader ) );
	shaderNetwork->setOutput( handle );

	return shaderNetwork;
}


} // end anon namespace


GAFFER_NODE_DEFINE_TYPE( SetVisualiser );

size_t SetVisualiser::g_firstPlugIndex = 0;

SetVisualiser::SetVisualiser( const std::string &name )
	: AttributeProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "sets" ) );
	addChild( new BoolPlug( "includeInherited", Plug::In, true ) );
	addChild( new FloatPlug( "stripeWidth", Plug::In, 10.0f, 1.0f /* min */ ) );

	addChild( new CompoundDataPlug( "colorOverrides", Plug::In ) );
	addChild( new AtomicCompoundDataPlug( "__outSets", Plug::Out, new CompoundData() ) );
}

SetVisualiser::~SetVisualiser()
{
}

Gaffer::StringPlug *SetVisualiser::setsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *SetVisualiser::setsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *SetVisualiser::includeInheritedPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *SetVisualiser::includeInheritedPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::FloatPlug *SetVisualiser::stripeWidthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *SetVisualiser::stripeWidthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::CompoundDataPlug *SetVisualiser::colorOverridesPlug()
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::CompoundDataPlug *SetVisualiser::colorOverridesPlug() const
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 3 );
}

Gaffer::AtomicCompoundDataPlug *SetVisualiser::outSetsPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::AtomicCompoundDataPlug *SetVisualiser::outSetsPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 4 );
}

void SetVisualiser::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	AttributeProcessor::affects( input, outputs );

	// Making attributes depend on outSets as much as possible (instead of
	// the input plugs directly) allows us to better take advantage of Gaffers
	// plug value caching and avoid some duplicate set processing work.

	if(
		input == setsPlug() ||
		colorOverridesPlug()->isAncestorOf( input ) ||
		input == inPlug()->setNamesPlug()
	)
	{
		outputs.push_back( outSetsPlug() );
	}
}

void SetVisualiser::hash( const ValuePlug *output, const Context *context, MurmurHash &h ) const
{
	AttributeProcessor::hash( output, context, h );

	if( output == outSetsPlug() )
	{
		setsPlug()->hash( h );
		colorOverridesPlug()->hash( h );
		// We don't care about a set's hash here as we're only computing which
		// sets we will consider and their corresponding colors - which depends
		// solely on their names.
		h.append( inPlug()->setNamesHash() );
	}
}

void SetVisualiser::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == outSetsPlug() )
	{
		const StringAlgo::MatchPattern requestedSetsPattern = setsPlug()->getValue();

		std::vector<InternedString> names;
		std::vector<Color3f> colors;

		if( !requestedSetsPattern.empty() )
		{
			const std::vector<Override> overrides = unpackOverrides( colorOverridesPlug() );

			ConstInternedStringVectorDataPtr allSetNamesData = inPlug()->setNames();

			// Sorting now makes everything easier, otherwise you have to
			// sort parallel arrays later, which is a pain.
			std::vector<InternedString> allNames = allSetNamesData->readable();
			std::sort( allNames.begin(), allNames.end(), internedStringCompare );

			for( auto &name : allNames )
			{
				// Gaffer has some internal sets that begin with the '__'
				// prefix. These are usually Lights, Cameras, etc... We filter
				// these out as they most of their objects don't even draw in
				// the viewer in a meaningful way for visualising set Membership
				if( boost::starts_with( name.string(), "__" ) )
				{
					continue;
				}

				if( StringAlgo::matchMultiple( name, requestedSetsPattern ) )
				{
					names.push_back( name );
					colors.push_back( colorForSetName( name, overrides ) );
				}
			}
		}

		CompoundDataPtr data = new CompoundData();
		data->writable()["names"] = new InternedStringVectorData( names );
		data->writable()["colors"] = new Color3fVectorData( colors );
		static_cast<AtomicCompoundDataPlug *>( output )->setValue( data );
	}
	else
	{
		AttributeProcessor::compute( output, context );
	}
}

bool SetVisualiser::affectsProcessedAttributes( const Gaffer::Plug *input ) const
{
	return
		AttributeProcessor::affectsProcessedAttributes( input ) ||
		input == includeInheritedPlug() ||
		input == stripeWidthPlug() ||
		input == outSetsPlug() ||
		input == inPlug()->setPlug()
	;
}

void SetVisualiser::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, MurmurHash &h ) const
{
	AttributeProcessor::hashProcessedAttributes( path, context, h );

	ConstCompoundDataPtr outSetsData = outSetsPlug()->getValue();

	outSetsData->hash( h );
	includeInheritedPlug()->hash( h );

	// We also need to consider each of our candidate sets membership
	// definition (which we didn't need to when computing outSets).
	// outSetsData is map of names -> colors.
	ConstInternedStringVectorDataPtr setNames = outSetsData->member<InternedStringVectorData>( "names" );
	for( auto &setName : setNames->readable() )
	{
		h.append( inPlug()->setHash( setName ) );
	}

	h.append( path.data(), path.size() );
	stripeWidthPlug()->hash( h );
}

ConstCompoundObjectPtr SetVisualiser::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, const IECore::CompoundObject *inputAttributes ) const
{
	CompoundObjectPtr result = new CompoundObject;

	// Since we're not going to modify any existing members (only add a new one),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->members() = inputAttributes->members();

	ConstCompoundDataPtr outSetsData = outSetsPlug()->getValue();
	const InternedStringVectorData *setNamesData = outSetsData->member<InternedStringVectorData>( "names" );
	const Color3fVectorData *setColorsData = outSetsData->member<Color3fVectorData>( "colors" );

	int matchResult = PathMatcher::ExactMatch;
	if( includeInheritedPlug()->getValue() )
	{
		matchResult |= PathMatcher::AncestorMatch;
	}

	ConstCompoundDataPtr targetSets = SceneAlgo::sets( inPlug(), setNamesData->readable() );
	std::vector<Color3f> shaderColors;

	size_t index = 0;
	for( auto &setName : setNamesData->readable() )
	{
		const PathMatcherData *pathMatchData = targetSets->member<const PathMatcherData>( setName );
		if( pathMatchData->readable().match( path ) & matchResult )
		{
			shaderColors.push_back( setColorsData->readable()[ index ] );
		}
		// We need to pass our colors to the shader as a fixed size array
		if( shaderColors.size() == g_maxShaderColors )
		{
			break;
		}
		++index;
	}

	// Avoids shader compilation errors as its expecting g_maxShaderColors elements
	const size_t numColorsUsed = shaderColors.size();
	shaderColors.resize( g_maxShaderColors );

	result->members()["gl:surface"] = stripeShader( stripeWidthPlug()->getValue(), numColorsUsed, shaderColors );

	return result;
}
