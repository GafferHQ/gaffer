//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, John Haddon. All rights reserved.
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

#include "GafferRenderMan/RenderManShader.h"

#include "GafferRenderMan/BXDFPlug.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/StringPlug.h"

#include "IECore/SearchPath.h"
#include "IECore/MessageHandler.h"

#include "boost/algorithm/string.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/property_tree/xml_parser.hpp"

#include <unordered_set>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferRenderMan;

//////////////////////////////////////////////////////////////////////////
// RenderManShader
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( RenderManShader );

RenderManShader::RenderManShader( const std::string &name )
	:	GafferScene::Shader( name )
{
	/// \todo It would be better if the Shader base class added this
	/// output plug, but that means changing ArnoldShader.
	addChild( new Plug( "out", Plug::Out ) );
}

RenderManShader::~RenderManShader()
{
}

//////////////////////////////////////////////////////////////////////////
// Shader-specific overrides
//////////////////////////////////////////////////////////////////////////

namespace
{

using ParameterSet = unordered_set<string>;
static const unordered_map<string, ParameterSet> g_omittedParameters = {
	{
		"PxrPortalLight",
		{
			// These shouldn't be exposed because we are going to
			// derive the values from the dome light and other parameters
			// like `intensityMult`.
			"domeColorMap", "lightColor", "intensity", "exposure", "portalToDome",
			"portalName",
			// These shouldn't be exposed because we are going to inherit the
			// values from the dome light.
			/// \todo We could instead load these as `OptionalValuePlugs` to
			/// allow a portal to override a value from the dome.
			"colorMapGamma", "colorMapSaturation", "enableTemperature",
			"temperature", "specular", "diffuse", "enableShadows",
			"shadowColor", "shadowDistance", "shadowFalloff", "shadowFalloffGamma",
			"shadowSubset", "shadowExcludeSubset", "traceLightPaths", "thinShadow",
			"visibleInRefractionPath", "cheapCaustics", "cheapCausticsExcludeGroup",
			"fixedSampleCount", "lightGroup", "importanceMultiplier", "msApprox",
			"msApproxBleed", "msApproxContribution"
		},
	}
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Shader loading code
//////////////////////////////////////////////////////////////////////////

namespace
{

bool isVStruct( const boost::property_tree::ptree &parameter )
{
	if( auto tags = parameter.get_child_optional( "tags" ) )
	{
		for( const auto &tag : *tags )
		{
			if( tag.second.get<string>( "<xmlattr>.value" ) == "vstruct" )
			{
				return true;
			}
		}
	}
	return false;
}

template<typename PlugType>
PlugPtr acquireNumericParameter( const boost::property_tree::ptree &parameter, IECore::InternedString name, Plug::Direction direction, Plug *candidatePlug )
{
	typedef typename PlugType::ValueType ValueType;

	const ValueType defaultValue = parameter.get( "<xmlattr>.default", ValueType( 0 ) );
	const ValueType minValue = parameter.get( "<xmlattr>.min", numeric_limits<ValueType>::lowest() );
	const ValueType maxValue = parameter.get( "<xmlattr>.max", numeric_limits<ValueType>::max() );

	auto existingPlug = runTimeCast<PlugType>( candidatePlug );
	if(
		existingPlug &&
		existingPlug->defaultValue() == defaultValue &&
		existingPlug->minValue() == minValue &&
		existingPlug->maxValue() == maxValue
	)
	{
		return existingPlug;
	}

	return new PlugType( name, direction, defaultValue, minValue, maxValue );
}

template<typename T>
T parseCompoundNumericValue( const string &s )
{
	typedef typename T::BaseType BaseType;
	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;

	T result( 0 );
	unsigned int i = 0;
	for( auto token : Tokenizer( s, boost::char_separator<char>( " " ) ) )
	{
		if( i >= T::dimensions() )
		{
			break;
		}
		result[i++] = boost::lexical_cast<BaseType>( token );
	}

	return result;
}

template<typename PlugType>
PlugPtr acquireCompoundNumericParameter( const boost::property_tree::ptree &parameter, IECore::InternedString name, Plug::Direction direction, IECore::GeometricData::Interpretation interpretation, Plug *candidatePlug )
{
	typedef typename PlugType::ValueType ValueType;
	typedef typename ValueType::BaseType BaseType;

	const ValueType defaultValue = parseCompoundNumericValue<ValueType>( parameter.get( "<xmlattr>.default", "0 0 0" ) );
	const ValueType minValue( numeric_limits<BaseType>::min() );
	const ValueType maxValue( numeric_limits<BaseType>::max() );

	auto existingPlug = runTimeCast<PlugType>( candidatePlug );
	if(
		existingPlug &&
		existingPlug->defaultValue() == defaultValue &&
		existingPlug->minValue() == minValue &&
		existingPlug->maxValue() == maxValue &&
		existingPlug->interpretation() == interpretation
	)
	{
		return existingPlug;
	}

	return new PlugType( name, direction, defaultValue, minValue, maxValue, Plug::Default, interpretation );
}

PlugPtr acquireStringParameter( const boost::property_tree::ptree &parameter, IECore::InternedString name, Plug::Direction direction, Plug *candidatePlug )
{
	const string defaultValue = parameter.get( "<xmlattr>.default", "" );

	auto existingPlug = runTimeCast<StringPlug>( candidatePlug );
	if(
		existingPlug &&
		existingPlug->defaultValue() == defaultValue
	)
	{
		return existingPlug;
	}

	return new StringPlug( name, direction, defaultValue );
}

PlugPtr acquireMatrixParameter( const boost::property_tree::ptree &parameter, IECore::InternedString name, Plug::Direction direction, Plug *candidatePlug )
{
	auto existingPlug = runTimeCast<M44fPlug>( candidatePlug );
	if( existingPlug )
	{
		return existingPlug;
	}

	return new M44fPlug( name, direction );
}

PlugPtr acquireBXDFParameter( IECore::InternedString name, Plug::Direction direction, Plug *candidatePlug )
{
	auto existingPlug = runTimeCast<BXDFPlug>( candidatePlug );
	if( existingPlug )
	{
		return existingPlug;
	}

	return new BXDFPlug( name, direction );
}

Gaffer::Plug *loadParameter( const boost::property_tree::ptree &parameter, Plug *parent )
{
	if( parameter.get<string>( "<xmlattr>.omitFromRender", "False" ) == "True" )
	{
		// Ignore those pesky "notes" parameters
		return nullptr;
	}

	if( isVStruct( parameter ) )
	{
		// PxrSurface and PxrLayerSurface have funky `inputMaterial` float
		// parameters that represent "virtual structs". These require the host
		// to implement a bunch of extra logic to make a whole bunch of concrete
		// connections dictated by connections to the virtual parameter and some
		// additional metadata. It's not pretty, and the Lama shaders use a
		// completely different mechanism for layering - hopefully we can just
		// deal with the latter.
		return nullptr;
	}

	const string name = parameter.get<string>( "<xmlattr>.name" );

	bool array = false;
	Plug *candidatePlug;
	if( parameter.get<string>( "<xmlattr>.isDynamicArray", "0" ) == "1" )
	{
		if(
			boost::ends_with( name, "_Knots" ) ||
			boost::ends_with( name, "_Floats" ) ||
			boost::ends_with( name, "_Colors" )
		)
		{
			/// \todo Support spline parameters.
			msg(
				IECore::Msg::Debug, "RenderManShader::loadShader",
				fmt::format( "Spline parameter \"{}\" not supported", name )
			);
			return nullptr;
		}

		// There are very few examples of non-spline array parameters
		// in the standard RenderMan shaders. All seem to be used to
		// provide an array of connections rather than values - see
		// `PxrSurface.utilityPattern` for example. So we load as an
		// ArrayPlug rather than as a VectorDataPlug.
		array = true;
		auto arrayPlug = parent->getChild<ArrayPlug>( name );
		candidatePlug = arrayPlug ? const_cast<Plug *>( arrayPlug->elementPrototype() ) : nullptr;
	}
	else
	{
		candidatePlug = parent->getChild<Plug>( name );
	}

	PlugPtr acquiredPlug;
	const string type = parameter.get<string>( "<xmlattr>.type" );
	if( type == "float" )
	{
		acquiredPlug = acquireNumericParameter<FloatPlug>( parameter, name, Plug::In, candidatePlug );
	}
	else if( type == "int" )
	{
		acquiredPlug = acquireNumericParameter<IntPlug>( parameter, name, Plug::In, candidatePlug );
	}
	else if( type == "point" )
	{
		acquiredPlug = acquireCompoundNumericParameter<V3fPlug>( parameter, name, Plug::In, GeometricData::Point, candidatePlug );
	}
	else if( type == "vector" )
	{
		acquiredPlug = acquireCompoundNumericParameter<V3fPlug>( parameter, name, Plug::In, GeometricData::Vector, candidatePlug );
	}
	else if( type == "normal" )
	{
		acquiredPlug = acquireCompoundNumericParameter<V3fPlug>( parameter, name, Plug::In, GeometricData::Normal, candidatePlug );
	}
	else if( type == "color" )
	{
		acquiredPlug = acquireCompoundNumericParameter<Color3fPlug>( parameter, name, Plug::In, GeometricData::None, candidatePlug );
	}
	else if( type == "string" )
	{
		acquiredPlug = acquireStringParameter( parameter, name, Plug::In, candidatePlug );
	}
	else if( type == "matrix" )
	{
		acquiredPlug = acquireMatrixParameter( parameter, name, Plug::In, candidatePlug );
	}
	else if( type == "bxdf" )
	{
		acquiredPlug = acquireBXDFParameter( name, Plug::In, candidatePlug );
	}
	else
	{
		msg(
			IECore::Msg::Warning, "RenderManShader::loadShader",
			fmt::format( "Parameter \"{}\" has unsupported type \"{}\"", name, type )
		);
		return nullptr;
	}

	if( acquiredPlug != candidatePlug )
	{
		if( array )
		{
			acquiredPlug->setName( fmt::format( "{}0", name ) );
			acquiredPlug = new ArrayPlug( name, Plug::In, acquiredPlug );
		}
		PlugAlgo::replacePlug( parent, acquiredPlug );
	}

	return acquiredPlug.get();
}

void loadParameters( const boost::property_tree::ptree &tree, Plug *parent, const ParameterSet *omit, std::unordered_set<const Plug *> &validPlugs )
{
	for( const auto &child : tree )
	{
		if( child.first == "param" )
		{
			if( omit && omit->count( child.second.get<string>( "<xmlattr>.name" ) ) )
			{
				continue;
			}
			if( Plug *p = loadParameter( child.second, parent ) )
			{
				validPlugs.insert( p );
			}
		}
		else if( child.first == "page" )
		{
			loadParameters( child.second, parent, omit, validPlugs );
		}
	}
}

void loadParameters( const boost::property_tree::ptree &tree, Plug *parent, const ParameterSet *omit )
{
	// Load all the parameters

	std::unordered_set<const Plug *> validPlugs;
	loadParameters( tree, parent, omit, validPlugs );

	// Remove any old plugs which it turned out we didn't need.

	for( int i = parent->children().size() - 1; i >= 0; --i )
	{
		Plug *child = parent->getChild<Plug>( i );
		if( validPlugs.find( child ) == validPlugs.end() )
		{
			parent->removeChild( child );
		}
	}
}

Gaffer::Plug *loadOutput( const boost::property_tree::ptree &output, Plug *parent )
{
	const string name = output.get<string>( "<xmlattr>.name" );
	Plug *candidatePlug = parent->getChild<Plug>( name );

	// For some reason, output type is not determined by a `type` attribute
	// like inputs are. Instead tags are used.
	unordered_set<string> tags;
	for( const auto &tag : output.get_child( "tags" ) )
	{
		tags.insert( tag.second.get<string>( "<xmlattr>.value" ) );
	}

	PlugPtr acquiredPlug;
	if( tags.find( "color" ) != tags.end() )
	{
		acquiredPlug = acquireCompoundNumericParameter<Color3fPlug>( output, name, Plug::Out, GeometricData::None, candidatePlug );
	}
	else if( tags.find( "float" ) != tags.end() )
	{
		acquiredPlug = acquireNumericParameter<FloatPlug>( output, name, Plug::Out, candidatePlug );
	}
	else if( tags.find( "vector" ) != tags.end() )
	{
		acquiredPlug = acquireCompoundNumericParameter<V3fPlug>( output, name, Plug::Out, GeometricData::Vector, candidatePlug );
	}
	else
	{
		msg(
			IECore::Msg::Warning, "RenderManShader::loadShader",
			fmt::format( "Output \"{}\" has unsupported tags", name )
		);
		return nullptr;
	}

	if( acquiredPlug != candidatePlug )
	{
		PlugAlgo::replacePlug( parent, acquiredPlug );
	}

	return acquiredPlug.get();
}

const InternedString g_bxdfOut( "bxdf_out" );

void loadOutputs( const boost::property_tree::ptree &tree, Plug *parent, const std::string &shaderName, const std::string &shaderType )
{
	// Load all the outputs.

	std::unordered_set<const Plug *> validPlugs;
	for( const auto &child : tree )
	{
		if( child.first == "output" )
		{
			if( const Plug *p = loadOutput( child.second, parent ) )
			{
				validPlugs.insert( p );
			}
		}
	}

	if( !validPlugs.size() && shaderType == "surface" )
	{
		// For some reason, BXDF outputs aren't declared explicitly in the `.args` files,
		// and are just implicit based on the shader type. So deal with that.
		Plug *candidatePlug = parent->getChild<Plug>( g_bxdfOut );
		if( auto acquiredPlug = acquireBXDFParameter( g_bxdfOut, Plug::Out, candidatePlug ) )
		{
			validPlugs.insert( acquiredPlug.get() );
			if( acquiredPlug != candidatePlug )
			{
				PlugAlgo::replacePlug( parent, acquiredPlug );
			}
		}
	}

	// Remove any old plugs which it turned out we didn't need.

	for( int i = parent->children().size() - 1; i >= 0; --i )
	{
		Plug *child = parent->getChild<Plug>( i );
		if( validPlugs.find( child ) == validPlugs.end() )
		{
			parent->removeChild( child );
		}
	}
}

} // namespace

void RenderManShader::loadShader( const std::string &shaderName, bool keepExistingValues )
{
	const char *pluginPath = getenv( "RMAN_RIXPLUGINPATH" );
	SearchPath searchPath( pluginPath ? pluginPath : "" );

	boost::filesystem::path argsFilename = searchPath.find( "Args/" + shaderName + ".args" );
	if( argsFilename.empty() )
	{
		throw IECore::Exception(
			fmt::format( "Unable to find shader \"{}\" on RMAN_RIXPLUGINPATH", shaderName )
		);
	}

	std::ifstream argsStream( argsFilename.string() );

	boost::property_tree::ptree tree;
	boost::property_tree::read_xml( argsStream, tree );

	namePlug()->source<StringPlug>()->setValue( shaderName );

	string shaderType = tree.get<string>( "args.shaderType.tag.<xmlattr>.value" );
	if( shaderType == "bxdf" )
	{
		shaderType = "surface";
	}

	typePlug()->source<StringPlug>()->setValue( "ri:" + shaderType );

	Plug *parametersPlug = this->parametersPlug()->source<Plug>();
	if( !keepExistingValues )
	{
		parametersPlug->clearChildren();
	}

	auto omit = g_omittedParameters.find( shaderName );
	loadParameters(
		tree.get_child( "args" ), parametersPlug,
		omit != g_omittedParameters.end() ? &omit->second : nullptr
	);

	if( !keepExistingValues )
	{
		outPlug()->clearChildren();
	}

	loadOutputs( tree.get_child( "args" ), outPlug(), shaderName, shaderType );

}
