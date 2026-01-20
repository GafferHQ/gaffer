//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2014, John Haddon. All rights reserved.
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

#include "GafferOSL/OSLShader.h"

#include "GafferOSL/ClosurePlug.h"
#include "GafferOSL/ShadingEngine.h"

#include "GafferScene/ShaderTweakProxy.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/RampPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECoreScene/ShaderNetwork.h"

#include "IECoreImage/OpenImageIOAlgo.h"

#include "IECore/MessageHandler.h"

#include "OSL/oslquery.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/container/flat_set.hpp"

#include "tbb/mutex.h"

#include "fmt/format.h"

#include <filesystem>
#include <unordered_set>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace OSL;
using namespace Gaffer;
using namespace GafferOSL;

//////////////////////////////////////////////////////////////////////////
// LRUCache of ShadingEngines
//////////////////////////////////////////////////////////////////////////

namespace
{

const ShaderNetwork *findOSLShaderNetwork( const CompoundObject *attributes )
{
	static InternedString oslSurfaceName = "osl:surface";
	static InternedString oslShaderName = "osl:shader";
	CompoundObject::ObjectMap::const_iterator it = attributes->members().find( oslSurfaceName );
	if( it == attributes->members().end() )
	{
		// If we didn't find a surface, check if it's named "osl:shader", since OSL doesn't actually
		// enforce any difference between surfaces and shaders
		it = attributes->members().find( oslShaderName );
	}

	if( it == attributes->members().end() )
	{
		return nullptr;
	}

	return runTimeCast<const ShaderNetwork>( it->second.get() );
}

struct ShadingEngineCacheGetterKey
{

	ShadingEngineCacheGetterKey()
		:	shader( nullptr )
	{
	}

	ShadingEngineCacheGetterKey( const OSLShader *s, const CompoundObject *substitutions )
		:	shader( s ), substitutions( substitutions )
	{
		hash = s->attributesHash();
		if( substitutions )
		{
			ConstCompoundObjectPtr attributes = shader->attributes();
			const ShaderNetwork *network = findOSLShaderNetwork( attributes.get() );
			if( network )
			{
				network->hashSubstitutions( substitutions, hash );
			}
		}
	}

	operator const IECore::MurmurHash & () const
	{
		return hash;
	}

	const OSLShader *shader;
	MurmurHash hash;
	const CompoundObject *substitutions;
};

ConstShadingEnginePtr getter( const ShadingEngineCacheGetterKey &key, size_t &cost, const IECore::Canceller *canceller )
{
	cost = 1;

	ConstCompoundObjectPtr attributes = key.shader->attributes();
	const ShaderNetwork *network = findOSLShaderNetwork( attributes.get() );
	if( !network || !network->size() )
	{
		return nullptr;
	}

	ShaderNetworkPtr networkCopy = network->copy();
	if( key.substitutions )
	{
		networkCopy->applySubstitutions( key.substitutions );
	}

	return new ShadingEngine( std::move( networkCopy ) );
}

using ShadingEngineCache = IECorePreview::LRUCache<IECore::MurmurHash, ConstShadingEnginePtr, IECorePreview::LRUCachePolicy::Parallel, ShadingEngineCacheGetterKey>;
ShadingEngineCache g_shadingEngineCache( getter, 10000 );

using ShaderTypeSet = boost::container::flat_set<IECore::InternedString>;
ShaderTypeSet &compatibleShaders()
{
	static ShaderTypeSet g_compatibleShaders;
	return g_compatibleShaders;
}

// Auto-proxies are always allowed to connect, because we don't know what type they will be until we evaluate
// the graph.
const bool g_oslShaderTweakAutoProxyRegistration = OSLShader::registerCompatibleShader( "autoProxy" );

GafferScene::ShaderTweakProxy::ShaderLoaderDescription<OSLShader> g_oslShaderTweakProxyLoaderRegistration( "osl" );

} // namespace

/////////////////////////////////////////////////////////////////////////
// LRUCache of OSLQueries
//////////////////////////////////////////////////////////////////////////

namespace
{

using OSLQueryPtr = shared_ptr<OSLQuery>;
using QueryCache = IECorePreview::LRUCache<string, OSLQueryPtr, IECorePreview::LRUCachePolicy::Parallel>;

QueryCache &queryCache()
{
	static QueryCache g_cache(
		[] ( const std::string &shaderName, size_t &cost, const IECore::Canceller *canceller ) {
			const char *searchPath = getenv( "OSL_SHADER_PATHS" );
			OSLQueryPtr query = make_shared<OSLQuery>();
			if( !query->open( shaderName, searchPath ? searchPath : "" ) )
			{
				throw Exception( query->geterror() );
			}
			cost = 1;
			return query;
		},
		10000
	);
	return g_cache;
}

} // namespace

/////////////////////////////////////////////////////////////////////////
// Type overrides
//////////////////////////////////////////////////////////////////////////

namespace
{

boost::container::flat_map<string, string> g_typeOverrides = {
	{ "vdbVolume", "osl:volume" },
	{ "dlDisplacement", "osl:displacement" },
	{ "PxrDisplace", "osl:displacement" }
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// OSLShader
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( OSLShader );

OSLShader::OSLShader( const std::string &name )
	:	GafferScene::Shader( name )
{
}

OSLShader::~OSLShader()
{
}

Gaffer::Plug *OSLShader::correspondingInput( const Gaffer::Plug *output )
{
	// better to do a few harmless casts than manage a duplicate implementation
	return const_cast<Gaffer::Plug *>(
		const_cast<const OSLShader *>( this )->correspondingInput( output )
	);
}

const Gaffer::Plug *OSLShader::correspondingInput( const Gaffer::Plug *output ) const
{
	const StringData *input = IECore::runTimeCast<const StringData>( OSLShader::parameterMetadata( output, "correspondingInput" ) );
	if( !input )
	{
		return nullptr;
	}

	const Plug *result = parametersPlug()->getChild<Plug>( input->readable() );
	if( !result )
	{
		IECore::msg( IECore::Msg::Error, "OSLShader::correspondingInput", fmt::format( "Parameter \"{}\" does not exist", input->readable() ) );
		return nullptr;
	}

	return result;
}

ConstShadingEnginePtr OSLShader::shadingEngine( const CompoundObject *substitutions ) const
{
	return g_shadingEngineCache.get( ShadingEngineCacheGetterKey( this, substitutions ) );
}

bool OSLShader::acceptsInput( const Plug *plug, const Plug *inputPlug ) const
{
	if( !Shader::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( !inputPlug )
	{
		return true;
	}

	if( parametersPlug()->isAncestorOf( plug ) )
	{
		const Plug *sourcePlug = inputPlug->source();
		const GafferScene::Shader *sourceShader = runTimeCast<const GafferScene::Shader>( sourcePlug->node() );
		const Plug *sourceShaderOutPlug = sourceShader ? sourceShader->outPlug() : nullptr;

		if( sourceShaderOutPlug && ( sourceShaderOutPlug == inputPlug || sourceShaderOutPlug->isAncestorOf( inputPlug ) ) )
		{
			if( sourceShader->isInstanceOf( staticTypeId() ) )
			{
				return true;
			}

			std::string sourceShaderType;
			if( auto shaderTweakProxy = IECore::runTimeCast<const GafferScene::ShaderTweakProxy>( sourceShader ) )
			{
				std::string unusedSourceShaderName;
				shaderTweakProxy->typePrefixAndSourceShaderName( sourceShaderType, unusedSourceShaderName );
			}
			else
			{
				sourceShaderType = sourceShader->typePlug()->getValue();
			}
			const ShaderTypeSet &cs = compatibleShaders();
			if( cs.find( sourceShaderType ) != cs.end() )
			{
				return true;
			}

			return false;
		}
	}

	return true;
}

//////////////////////////////////////////////////////////////////////////
// 3Delight Shader loading code
//////////////////////////////////////////////////////////////////////////

bool is3DelightSplineValueParameter( const OSLQuery::Parameter *parameter )
{
	auto widgetIt = std::find_if(
		parameter->metadata.begin(),
		parameter->metadata.end(),
		[]( const OSLQuery::Parameter &m )
		{
			return m.name == "widget";
		}
	);
	if( widgetIt != parameter->metadata.end() && widgetIt->sdefault.front().find( "Ramp" ) != std::string::npos )
	{
		return true;
	}
	return false;
}

bool is3DelightSplineNonValueParameter( const OSLQuery::Parameter *parameter )
{
	auto relatedWidgetIt = std::find_if(
		parameter->metadata.begin(),
		parameter->metadata.end(),
		[]( const OSLQuery::Parameter &m )
		{
			return m.name == "related_to_widget";
		}
	);
	if( relatedWidgetIt != parameter->metadata.end() && relatedWidgetIt->sdefault.front().find( "Ramp" ) != std::string::npos )
	{
		return true;
	}
	return false;
}

bool find3DelightSplineParametersFromPositions(
	const OSLQuery &query,
	const OSLQuery::Parameter *positionsParameter,
	std::string &nameWithoutSuffix,
	const OSLQuery::Parameter * &valuesParameter,
	const OSLQuery::Parameter * &basisParameter
)
{
	if( !(
		positionsParameter->type.is_array() &&
		positionsParameter->type.basetype == TypeDesc::FLOAT &&
		positionsParameter->type.aggregate == TypeDesc::SCALAR &&
		is3DelightSplineNonValueParameter( positionsParameter )
	) )
	{
		return false;
	}

	// 3Delight's naming convention seems extremly loose, which makes it hard to
	// group the related spline parameters. Maybe it would be better to group based
	// on the "maya_attribute" metadata, which on every 3Delight shader with a spline
	// is set to <something>_Position, except ramp.oso, where it's set to
	// <something>.position
	// Anyway, for now, this list of possible position suffixes seems to cover everything.
	static const std::string possiblePositionSuffixes[] = {
		"_Knots", "_Position", "Positions", "_pos"
	};
	unsigned int suffixLength = 0;
	for( const std::string &suffix : possiblePositionSuffixes )
	{
		if( boost::ends_with( positionsParameter->name.string(), suffix ) )
		{
			suffixLength = suffix.size();
		}
	}

	if( !suffixLength )
	{
		return false;
	}

	nameWithoutSuffix = positionsParameter->name.string().substr( 0, positionsParameter->name.string().size() - suffixLength );

	valuesParameter = nullptr;
	basisParameter = nullptr;

	const OSLQuery::Parameter *perPointInterpolationParameter = nullptr;

	for( size_t i = 0, eI = query.nparams(); i < eI; ++i )
	{
		const OSLQuery::Parameter *p = query.getparam( i );
		if( !boost::starts_with( p->name, nameWithoutSuffix ) || p == positionsParameter )
		{
			continue;
		}
		if( p->type == TypeDesc::STRING )
		{
			basisParameter = p;
		}
		else if( p->type.is_array() && p->type.aggregate == TypeDesc::VEC3 && p->type.vecsemantics == TypeDesc::COLOR )
		{
			valuesParameter = p;
		}
		else if( p->type.is_array() && p->type.basetype == TypeDesc::INT && p->type.aggregate == TypeDesc::SCALAR )
		{
			perPointInterpolationParameter = p;
		}
		else if( p->type.is_array() && p->type.basetype == TypeDesc::FLOAT && p->type.aggregate == TypeDesc::SCALAR )
		{
			if( is3DelightSplineValueParameter( p ) )
			{
				valuesParameter = p;
			}
		}
	}

	basisParameter = basisParameter ? basisParameter : perPointInterpolationParameter;

	return positionsParameter && valuesParameter && basisParameter;
}



//////////////////////////////////////////////////////////////////////////
// Shader loading code
//////////////////////////////////////////////////////////////////////////

namespace
{

Plug *loadStringParameter( const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent )
{
	string defaultValue;
	if( parameter->sdefault.size() )
	{
		defaultValue = parameter->sdefault[0].string();
	}

	StringPlug *existingPlug = parent->getChild<StringPlug>( name );
	if(	existingPlug && existingPlug->defaultValue() == defaultValue )
	{
		return existingPlug;
	}

	StringPlugPtr plug = new StringPlug( name, parent->direction(), defaultValue, Plug::Default );

	if( existingPlug )
	{
		PlugAlgo::replacePlug( parent, plug );
	}
	else
	{
		parent->setChild( name, plug );
	}

	return plug.get();
}

Plug *loadStringArrayParameter( const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent )
{
	StringVectorDataPtr defaultValueData = new StringVectorData();
	std::vector<std::string> &defaultValueDataWritable = defaultValueData->writable();
	if( parameter->sdefault.size() )
	{
		defaultValueDataWritable.resize( parameter->sdefault.size() );
		for( size_t i = 0; i < parameter->sdefault.size(); i++ )
		{
			if( !parameter->sdefault[i].empty() )
			{
				defaultValueDataWritable[i] = parameter->sdefault[i].string();
			}
		}
	}

	StringVectorDataPlug *existingPlug = parent->getChild<StringVectorDataPlug>( name );
	if(	existingPlug && *existingPlug->defaultValue() == *defaultValueData )
	{
		return existingPlug;
	}

	StringVectorDataPlugPtr plug = new StringVectorDataPlug( name, parent->direction(), defaultValueData, Plug::Default );

	if( existingPlug )
	{
		PlugAlgo::replacePlug( parent, plug );
	}
	else
	{
		parent->setChild( name, plug );
	}

	return plug.get();
}

template<typename PlugType>
Plug *loadNumericParameter( const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent, const CompoundData *metadata )
{
	using ValueType = typename PlugType::ValueType;

	ValueType defaultValue( 0 );
	if( parameter->idefault.size() )
	{
		defaultValue = ValueType( parameter->idefault[0] );
	}
	else if( parameter->fdefault.size() )
	{
		defaultValue = ValueType( parameter->fdefault[0] );
	}

	ValueType minValue( std::numeric_limits<ValueType>::lowest() );
	ValueType maxValue( std::numeric_limits<ValueType>::max() );
	if( metadata )
	{
		const TypedData<ValueType> *minMeta = metadata->member< TypedData<ValueType> >( "min" );
		const TypedData<ValueType> *maxMeta = metadata->member< TypedData<ValueType> >( "max" );
		if( minMeta )
		{
			minValue = minMeta->readable();
		}
		if( maxMeta )
		{
			maxValue = maxMeta->readable();
		}
	}

	PlugType *existingPlug = parent->getChild<PlugType>( name );
	if(
		existingPlug &&
		existingPlug->defaultValue() == defaultValue &&
		existingPlug->minValue() == minValue &&
		existingPlug->maxValue() == maxValue
	)
	{
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( name, parent->direction(), defaultValue, minValue, maxValue, Plug::Default );

	if( existingPlug )
	{
		PlugAlgo::replacePlug( parent, plug );
	}
	else
	{
		parent->setChild( name, plug );
	}

	return plug.get();
}

template<typename PlugType>
Plug *loadNumericArrayParameter( const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent, const CompoundData *metadata )
{
	using DataType = typename PlugType::ValueType;
	using ValueType = typename DataType::ValueType;
	using ElementType = typename ValueType::value_type;

	typename DataType::Ptr defaultValueData = new DataType();
	ValueType &defaultValueDataWritable = defaultValueData->writable();
	if( parameter->idefault.size() )
	{
		defaultValueDataWritable.resize( parameter->idefault.size() );
		for( size_t i = 0; i < parameter->idefault.size(); i++ )
		{
			defaultValueDataWritable[i] = ElementType( parameter->idefault[i] );
		}
	}
	else if( parameter->fdefault.size() )
	{
		defaultValueDataWritable.resize( parameter->fdefault.size() );
		for( size_t i = 0; i < parameter->fdefault.size(); i++ )
		{
			defaultValueDataWritable[i] = ElementType( parameter->fdefault[i] );
		}
	}

	PlugType *existingPlug = parent->getChild<PlugType>( name );
	if(
		existingPlug &&
		*existingPlug->defaultValue() == *defaultValueData
	)
	{
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( name, parent->direction(), defaultValueData, Plug::Default );

	if( existingPlug )
	{
		PlugAlgo::replacePlug( parent, plug );
	}
	else
	{
		parent->setChild( name, plug );
	}

	return plug.get();
}

template <typename PlugType>
Plug *loadCompoundNumericParameter( const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent, const CompoundData *metadata )
{
	using ValueType = typename PlugType::ValueType;
	using BaseType = typename ValueType::BaseType;

	ValueType defaultValue( 0 );
	if( parameter->idefault.size() )
	{
		for( size_t i = 0; i < PlugType::ValueType::dimensions(); ++i )
		{
			defaultValue[i] = BaseType( parameter->idefault[i] );
		}
	}
	else if( parameter->fdefault.size() )
	{
		for( size_t i = 0; i < PlugType::ValueType::dimensions(); ++i )
		{
			defaultValue[i] = BaseType( parameter->fdefault[i] );
		}
	}

	/// \todo Get from metadata
	ValueType minValue( std::numeric_limits<BaseType>::lowest() );
	ValueType maxValue( std::numeric_limits<BaseType>::max() );
	if( metadata )
	{
		const TypedData<ValueType> *minMeta = metadata->member< TypedData<ValueType> >( "min" );
		const TypedData<ValueType> *maxMeta = metadata->member< TypedData<ValueType> >( "max" );
		if( minMeta )
		{
			minValue = minMeta->readable();
		}
		if( maxMeta )
		{
			maxValue = maxMeta->readable();
		}
	}

	IECore::GeometricData::Interpretation interpretation = IECoreImage::OpenImageIOAlgo::geometricInterpretation( (TypeDesc::VECSEMANTICS)parameter->type.vecsemantics );

	// we don't set color because we have a dedicated plug type for that.
	if( interpretation == GeometricData::Color )
	{
		interpretation = GeometricData::None;
	}

	PlugType *existingPlug = parent->getChild<PlugType>( name );
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

	typename PlugType::Ptr plug = new PlugType( name, parent->direction(), defaultValue, minValue, maxValue, Plug::Default , interpretation );

	if( existingPlug )
	{
		PlugAlgo::replacePlug( parent, plug );
	}
	else
	{
		parent->setChild( name, plug );
	}

	return plug.get();
}

template <typename PlugType>
Plug *loadCompoundNumericArrayParameter( const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent, const CompoundData *metadata )
{
	using DataType = typename PlugType::ValueType;
	using ValueType = typename DataType::ValueType;
	using ElementType = typename ValueType::value_type;
	using BaseType = typename ElementType::BaseType;

	typename DataType::Ptr defaultValueData = new DataType();
	ValueType &defaultValueDataWritable = defaultValueData->writable();
	if( parameter->idefault.size() )
	{
		defaultValueDataWritable.resize( parameter->idefault.size() / ElementType::dimensions() );
		for( size_t j = 0; j < defaultValueDataWritable.size(); j++ )
		{
			for( size_t i = 0; i < ElementType::dimensions(); ++i )
			{
				defaultValueDataWritable[j][i] = BaseType( parameter->idefault[ j * ElementType::dimensions() + i] );
			}
		}
	}
	else if( parameter->fdefault.size() )
	{
		defaultValueDataWritable.resize( parameter->fdefault.size() / ElementType::dimensions() );
		for( size_t j = 0; j < defaultValueDataWritable.size(); j++ )
		{
			for( size_t i = 0; i < ElementType::dimensions(); ++i )
			{
				defaultValueDataWritable[j][i] = BaseType( parameter->fdefault[ j * ElementType::dimensions() + i] );
			}
		}
	}



	PlugType *existingPlug = parent->getChild<PlugType>( name );
	if(
		existingPlug &&
		*existingPlug->defaultValue() == *defaultValueData
	)
	{
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( name, parent->direction(), defaultValueData, Plug::Default );

	if( existingPlug )
	{
		PlugAlgo::replacePlug( parent, plug );
	}
	else
	{
		parent->setChild( name, plug );
	}

	return plug.get();
}

Plug *loadMatrixParameter( const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent )
{
	const vector<float> &d = parameter->fdefault;
	M44f defaultValue(
		d[0], d[1], d[2], d[3],
		d[4], d[5], d[6], d[7],
		d[8], d[9], d[10], d[11],
		d[12], d[13], d[14], d[15]
	);

	M44fPlug *existingPlug = parent->getChild<M44fPlug>( name );
	if( existingPlug && existingPlug->defaultValue() == defaultValue )
	{
		return existingPlug;
	}

	M44fPlugPtr plug = new M44fPlug( name, parent->direction(), defaultValue, Plug::Default );

	if( existingPlug )
	{
		PlugAlgo::replacePlug( parent, plug );
	}
	else
	{
		parent->setChild( name, plug );
	}

	return plug.get();
}

Plug *loadMatrixArrayParameter( const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent )
{
	const vector<float> &d = parameter->fdefault;

	M44fVectorDataPtr defaultValueData = new M44fVectorData();
	std::vector<Imath::M44f> &defaultValueDataWritable = defaultValueData->writable();
	if( parameter->fdefault.size() )
	{
		defaultValueDataWritable.resize( parameter->fdefault.size() / 16 );
		for( size_t i = 0; i < defaultValueDataWritable.size(); i++ )
		{
			defaultValueDataWritable[i] = M44f(
				d[i*16+0], d[i*16+1], d[i*16+2], d[i*16+3],
				d[i*16+4], d[i*16+5], d[i*16+6], d[i*16+7],
				d[i*16+8], d[i*16+9], d[i*16+10], d[i*16+11],
				d[i*16+12], d[i*16+13], d[i*16+14], d[i*16+15] );
		}
	}

	M44fVectorDataPlug *existingPlug = parent->getChild<M44fVectorDataPlug>( name );
	if( existingPlug && *existingPlug->defaultValue() == *defaultValueData )
	{
		return existingPlug;
	}

	M44fVectorDataPlugPtr plug = new M44fVectorDataPlug( name, parent->direction(), defaultValueData, Plug::Default );

	if( existingPlug )
	{
		PlugAlgo::replacePlug( parent, plug );
	}
	else
	{
		parent->setChild( name, plug );
	}

	return plug.get();
}

Plug *loadClosureParameter( const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent )
{
	Plug *existingPlug = parent->getChild<Plug>( name );
	if( runTimeCast<ClosurePlug>( existingPlug ) )
	{
		return existingPlug;
	}

	ClosurePlugPtr plug = new ClosurePlug( name, parent->direction(), Plug::Default );

	if( existingPlug )
	{
		PlugAlgo::replacePlug( parent, plug );
	}
	else
	{
		parent->setChild( name, plug );
	}

	return plug.get();
}

// From https://gitlab.com/3Delight/3delight-for-houdini/-/blob/master/osl_utilities.cpp
std::string basisStringFrom3DelightInt( int basis )
{
	switch( basis )
	{
		case 0 : return "constant";
		case 1 : return "linear";
		case 2 : return "monotonecubic";
		default : return "catmullrom";
	}
}

struct RampPlugArguments
{
	std::string name;
	std::variant< Rampff, RampfColor3f > defaultValue;
};

template <typename RampType>
RampType loadRampDefault( const OSLQuery::Parameter *positionsParameter, const OSLQuery::Parameter *valuesParameter, const OSLQuery::Parameter *basisParameter, const OSLQuery::Parameter *countParameter, const std::string &name )
{
	RampType defaultValue;

	std::string basisString;
	if( basisParameter->type.basetype == TypeDesc::INT )
	{
		basisString = basisStringFrom3DelightInt( basisParameter->idefault.front() );
	}
	else
	{
		basisString = basisParameter->sdefault.front().string();
	}

	std::vector<typename RampType::XType> positions;
	std::vector<typename RampType::YType> values;
	const vector<float> &rawPositions = positionsParameter->fdefault;
	const vector<float> &rawValues = valuesParameter->fdefault;

	size_t maxSize = std::numeric_limits<size_t>::max();
	if( countParameter )
	{
		maxSize = countParameter->idefault.front();
	}

	if constexpr( std::is_same_v< typename RampType::YType, Color3f > )
	{
		for( size_t i = 0; i < rawPositions.size() && i*3+2 < rawValues.size() && i < maxSize; ++i )
		{
			values.push_back(
				Color3f(
					rawValues[i*3],
					rawValues[i*3+1],
					rawValues[i*3+2]
				)
			);
		}
	}
	else
	{
		for( size_t i = 0; i < rawPositions.size() && i < rawValues.size() && i < maxSize; ++i )
		{
			values.push_back( rawValues[i] );
		}
	}

	for( size_t i = 0; i < rawPositions.size() && i < values.size() && i < maxSize; ++i )
	{
		positions.push_back( rawPositions[i] );
	}

	defaultValue.fromOSL( basisString, positions, values, name );

	return defaultValue;
}

bool findGafferSplineParametersFromPositions( const OSLQuery &query, const OSLQuery::Parameter *positionsParameter, std::string &nameWithoutSuffix, const OSLQuery::Parameter * &valuesParameter, const OSLQuery::Parameter * &basisParameter )
{
	static const std::string positionsSuffix( "Positions" );
	static const std::string valuesSuffix( "Values" );
	static const std::string basisSuffix( "Basis" );

	if( !boost::ends_with( positionsParameter->name.string(), positionsSuffix ) )
	{
		return false;
	}

	if(
		!positionsParameter->type.is_array() ||
		positionsParameter->type.basetype != TypeDesc::FLOAT ||
		positionsParameter->type.aggregate != TypeDesc::SCALAR
	)
	{
		return false;
	}

	nameWithoutSuffix = positionsParameter->name.string().substr( 0, positionsParameter->name.string().size() - positionsSuffix.size() );

	valuesParameter = query.getparam( nameWithoutSuffix + valuesSuffix );
	if(
		!valuesParameter ||
		!valuesParameter->type.is_array() ||
		valuesParameter->type.basetype != TypeDesc::FLOAT ||
		( valuesParameter->type.aggregate != TypeDesc::SCALAR && valuesParameter->type.vecsemantics != TypeDesc::COLOR )
	)
	{
		return false;
	}

	basisParameter = query.getparam( nameWithoutSuffix + basisSuffix );
	if( !basisParameter || basisParameter->type != OIIO::TypeString )
	{
		return false;
	}

	return true;
}

bool findPRManSplineParametersFromPositions( const OSLQuery &query, const OSLQuery::Parameter *positionsParameter, std::string &nameWithoutSuffix, const OSLQuery::Parameter * &valuesParameter, const OSLQuery::Parameter * &basisParameter, const OSLQuery::Parameter * &countParameter )
{
	static const std::string positionsSuffix( "_Knots" );
	static const std::string valuesColorSuffix( "_Colors" );
	static const std::string valuesFloatSuffix( "_Floats" );
	static const std::string basisSuffix( "_Interpolation" );

	if( !boost::ends_with( positionsParameter->name.string(), positionsSuffix ) )
	{
		return false;
	}

	if(
		!positionsParameter->type.is_array() ||
		positionsParameter->type.basetype != TypeDesc::FLOAT ||
		positionsParameter->type.aggregate != TypeDesc::SCALAR
	)
	{
		return false;
	}

	nameWithoutSuffix = positionsParameter->name.string().substr( 0, positionsParameter->name.string().size() - positionsSuffix.size() );

	valuesParameter = query.getparam( nameWithoutSuffix + valuesColorSuffix );
	if(
		!valuesParameter ||
		!valuesParameter->type.is_array() ||
		valuesParameter->type.basetype != TypeDesc::FLOAT ||
		( valuesParameter->type.aggregate != TypeDesc::SCALAR && valuesParameter->type.vecsemantics != TypeDesc::COLOR )
	)
	{
		valuesParameter = query.getparam( nameWithoutSuffix + valuesFloatSuffix );
		if(
			!valuesParameter ||
			!valuesParameter->type.is_array() ||
			valuesParameter->type.basetype != TypeDesc::FLOAT ||
			valuesParameter->type.aggregate != TypeDesc::SCALAR
		)
		{
			return false;
		}
	}

	basisParameter = query.getparam( nameWithoutSuffix + basisSuffix );
	if( !basisParameter || basisParameter->type != OIIO::TypeString )
	{
		return false;
	}

	countParameter = query.getparam( nameWithoutSuffix );
	if( !countParameter || countParameter->type != OIIO::TypeInt )
	{
		return false;
	}

	return true;
}


bool findSplineParametersFromPositions( const std::string &shaderName, const OSLQuery &query, const OSLQuery::Parameter *positionsParameter, std::string &nameWithoutSuffix, const OSLQuery::Parameter * &valuesParameter, const OSLQuery::Parameter * &basisParameter, const OSLQuery::Parameter * &countParameter, std::unordered_set<const OSLQuery::Parameter *> &parametersAlreadyProcessed )
{
	bool success = false;
	// Note that this will fail if the shader is loaded from an explicit path ( in which case the shaderName
	// will be prefixed with a file path ). We've concluded this isn't an issue, because shaders should be found
	// using search paths instead.
	if( boost::starts_with( shaderName, "Pxr" ) ||  boost::starts_with( shaderName, "Lama" ) )
	{
		success = findPRManSplineParametersFromPositions( query, positionsParameter, nameWithoutSuffix, valuesParameter, basisParameter, countParameter );
	}
	else
	{
		countParameter = nullptr;
		success =
			findGafferSplineParametersFromPositions( query, positionsParameter, nameWithoutSuffix, valuesParameter, basisParameter ) ||
			find3DelightSplineParametersFromPositions( query, positionsParameter, nameWithoutSuffix, valuesParameter, basisParameter );
	}

	if( success )
	{
		parametersAlreadyProcessed.insert( valuesParameter );
		parametersAlreadyProcessed.insert( basisParameter );

		if( countParameter )
		{
			parametersAlreadyProcessed.insert( countParameter );
		}
	}

	return success;
}

std::optional<RampPlugArguments> rampPlugArgumentsFromPositions( const std::string &shaderName, const OSLQuery &query, const OSLQuery::Parameter *positionsParameter, const std::string &prefix, std::unordered_set<const OSLQuery::Parameter *> &parametersAlreadyProcessed )
{

	string nameWithoutSuffix;
	const OSLQuery::Parameter *valuesParameter;
	const OSLQuery::Parameter *basisParameter;
	const OSLQuery::Parameter *countParameter;

	RampPlugArguments result;

	if( !findSplineParametersFromPositions( shaderName, query, positionsParameter, nameWithoutSuffix, valuesParameter, basisParameter, countParameter, parametersAlreadyProcessed ) )
	{
		return std::optional<RampPlugArguments>();
	}

	result.name = nameWithoutSuffix.substr( prefix.size() );
	if( valuesParameter->type.vecsemantics == TypeDesc::COLOR )
	{
		result.defaultValue = loadRampDefault<RampfColor3f>( positionsParameter, valuesParameter, basisParameter, countParameter, result.name );
	}
	else
	{
		result.defaultValue = loadRampDefault<Rampff>( positionsParameter, valuesParameter, basisParameter, countParameter, result.name );
	}

	return std::make_optional<RampPlugArguments>( result );
}

// Forward declaration so loadStructParameter() can call it.
void loadShaderParameters( const std::string& shaderName, const OSLQuery &query, Gaffer::Plug *parent, const CompoundData *metadata, const std::string &prefix = "" );

Plug *loadStructParameter( const std::string &shaderName, const OSLQuery &query, const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent )
{
	Plug *result = nullptr;

	Plug *existingPlug = parent->getChild<Plug>( name );
	if( !existingPlug || existingPlug->typeId() != Plug::staticTypeId() )
	{
		// No existing plug, or it was the wrong type (we used to use a CompoundPlug).
		result = new Plug( name, parent->direction(), Plug::Default );
		if( existingPlug )
		{
			// Transfer old plugs onto the replacement.
			for( Plug::Iterator it( existingPlug ); !it.done(); ++it )
			{
				result->addChild( *it );
			}
		}
	}
	else
	{
		result = existingPlug;
	}

	/// \todo Should we support metadata on the children of a struct parameter?
	/// The OSL spec doesn't appear to standardize a way to specify this.
	/// We could attach metadata to the struct, but would it then be named
	/// something like "structElementName_min"?
	loadShaderParameters( shaderName, query, result, nullptr, parameter->name.string() + "." );

	parent->setChild( name, result );

	return result;
}

Plug *loadShaderParameter( const std::string shaderName, const OSLQuery &query, const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent, const CompoundData *metadata )
{
	Plug *result = nullptr;
	if( metadata && metadata->member( "vstructmember" ) && shaderName != "PxrDisplace" )
	{
		// RenderMan "virtual struct" member. This isn't for authoring
		// by users. Instead it will receive a connection or value in the
		// RenderMan backend at render time.
		return result;
	}

	if( parameter->isstruct )
	{
		result = loadStructParameter( shaderName, query, parameter, name, parent );
	}
	else if( parameter->isclosure )
	{
		result = loadClosureParameter( parameter, name, parent );
	}
	else if( parameter->type.arraylen == 0 )
	{
		if( parameter->type.basetype == TypeDesc::FLOAT || parameter->type.basetype == TypeDesc::INT )
		{
			// Numeric in some way.
			if( parameter->type.aggregate == TypeDesc::SCALAR )
			{
				if( parameter->type.basetype == TypeDesc::FLOAT )
				{
					result = loadNumericParameter<FloatPlug>( parameter, name, parent, metadata );
				}
				else
				{
					result = loadNumericParameter<IntPlug>( parameter, name, parent, metadata );
				}
			}
			else if( parameter->type.aggregate == TypeDesc::VEC3 )
			{
				if( parameter->type.basetype == TypeDesc::FLOAT )
				{
					if( parameter->type.vecsemantics == TypeDesc::COLOR )
					{
						result = loadCompoundNumericParameter<Color3fPlug>( parameter, name, parent, metadata );
					}
					else
					{
						result = loadCompoundNumericParameter<V3fPlug>( parameter, name, parent, metadata );
					}
				}
				else
				{
					result = loadCompoundNumericParameter<V3iPlug>( parameter, name, parent, metadata );
				}
			}
			else if( parameter->type.aggregate == TypeDesc::MATRIX44 )
			{
				if( parameter->type.basetype == TypeDesc::FLOAT )
				{
					result = loadMatrixParameter( parameter, name, parent );
				}
			}
		}
		else if( parameter->type.basetype == TypeDesc::STRING )
		{
			result = loadStringParameter( parameter, name, parent );
		}
	}
	else
	{
		// Arrays
		if( parameter->type.basetype == TypeDesc::FLOAT || parameter->type.basetype == TypeDesc::INT )
		{
			// Numeric in some way.
			if( parameter->type.aggregate == TypeDesc::SCALAR )
			{
				if( parameter->type.basetype == TypeDesc::FLOAT )
				{
					result = loadNumericArrayParameter<FloatVectorDataPlug>( parameter, name, parent, metadata );
				}
				else
				{
					result = loadNumericArrayParameter<IntVectorDataPlug>( parameter, name, parent, metadata );
				}
			}
			else if( parameter->type.aggregate == TypeDesc::VEC3 )
			{
				if( parameter->type.basetype == TypeDesc::FLOAT )
				{
					if( parameter->type.vecsemantics == TypeDesc::COLOR )
					{
						result = loadCompoundNumericArrayParameter<Color3fVectorDataPlug>( parameter, name, parent, metadata );
					}
					else
					{
						result = loadCompoundNumericArrayParameter<V3fVectorDataPlug>( parameter, name, parent, metadata );
					}
				}
				else
				{
					result = loadCompoundNumericParameter<V3iPlug>( parameter, name, parent, metadata );
				}
			}
			else if( parameter->type.aggregate == TypeDesc::MATRIX44 )
			{
				if( parameter->type.basetype == TypeDesc::FLOAT )
				{
					result = loadMatrixArrayParameter( parameter, name, parent );
				}
			}
		}
		else if( parameter->type.basetype == TypeDesc::STRING )
		{
			result = loadStringArrayParameter( parameter, name, parent );
		}
	}

	if( !result )
	{
		msg( Msg::Warning, "OSLShader::loadShader", fmt::format( "Parameter \"{}\" has unsupported type", parameter->name.string() ) );
	}

	return result;
}

template <typename PlugType>
Gaffer::Plug *loadRampParameterFromDefault( const InternedString &name, const typename PlugType::ValueType &defaultValue, Gaffer::Plug *parent )
{
	PlugType *existingPlug = parent->getChild<PlugType>( name );
	if( existingPlug && existingPlug->defaultValue() == defaultValue )
	{
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( name, parent->direction(), defaultValue, Plug::Default );

	// Other parameters are loaded using replacePlug if existingPlug is non-null, so existing connections
	// and values are preserved. It might make sense to do that here as well, but there could be
	// inconsistencies if the length of the default value has changed, and the user has only overridden
	// a few control points ... we haven't tested how well replacePlug works on ramps, so for the moment
	// we'll just throw away previous values here ( this currently isn't causing any problems, so we won't
	// change it ).

	parent->setChild( name, plug );

	return plug.get();
}

void loadShaderParameters( const std::string &shaderName, const OSLQuery &query, Gaffer::Plug *parent, const CompoundData *metadata, const std::string &prefix )
{
	// Make sure we have a plug to represent each parameter, reusing plugs wherever possible.

	set<const Plug *> validPlugs;

	// Spline parameters are a nasty special case because multiple shader
	// parameters become a single ramp plug on the node, so we deal with them
	// first, and use this set to record parameters that have already been
	// processed as part of a ramp.

	std::unordered_set<const OSLQuery::Parameter *> parametersAlreadyProcessed;
	std::unordered_map<const OSLQuery::Parameter *, RampPlugArguments > rampPlugArguments;

	for( size_t i = 0; i < query.nparams(); ++i )
	{
		// We will check whether this parameter fits as the positions parameter of a ramp
		const OSLQuery::Parameter *positionsParameter = query.getparam( i );
		const Plug::Direction direction = positionsParameter->isoutput ? Plug::Out : Plug::In;
		if( direction != parent->direction() )
		{
			continue;
		}

		if( !boost::starts_with( positionsParameter->name.string(), prefix ) )
		{
			continue;
		}

		const string name = positionsParameter->name.string().substr( prefix.size() );
		if( name.find( "." ) != string::npos )
		{
			// Member of a struct - will be loaded when the struct is loaded
			continue;
		}

		auto rampP = rampPlugArgumentsFromPositions( shaderName, query, positionsParameter, prefix, parametersAlreadyProcessed );

		if( rampP )
		{
			rampPlugArguments[positionsParameter] = *rampP;
		}
	}

	// Now process all the normal parameters that aren't part of a ramp
	for( size_t i = 0; i < query.nparams(); ++i )
	{
		const OSLQuery::Parameter *parameter = query.getparam( i );
		const Plug::Direction direction = parameter->isoutput ? Plug::Out : Plug::In;
		if( direction != parent->direction() )
		{
			continue;
		}

		if( !boost::starts_with( parameter->name.string(), prefix ) )
		{
			continue;
		}

		const string name = parameter->name.string().substr( prefix.size() );
		if( name.find( "." ) != string::npos )
		{
			// Member of a struct - will be loaded when the struct is loaded
			continue;
		}

		if( parametersAlreadyProcessed.count( parameter ) )
		{
			// Already loaded as part of a ramp
			continue;
		}

		Plug *plug = nullptr;

		auto rampIt = rampPlugArguments.find( parameter );
		if( rampIt != rampPlugArguments.end() )
		{
			// This is the key parameter for the ramp, time to output this ramp
			// ( We need to wait until now to output the ramp so it gets interleaved in proper
			// order with the non-ramp parameters )
			if( std::holds_alternative< RampfColor3f >( rampIt->second.defaultValue ) )
			{
				plug = loadRampParameterFromDefault<RampfColor3fPlug>( rampIt->second.name, std::get<RampfColor3f>( rampIt->second.defaultValue ), parent );
			}
			else
			{
				plug = loadRampParameterFromDefault<RampffPlug>( rampIt->second.name, std::get<Rampff>( rampIt->second.defaultValue ), parent );
			}
		}
		else
		{
			const CompoundData *parameterMetadata = nullptr;
			if( metadata )
			{
				parameterMetadata = metadata->member<IECore::CompoundData>( name );
			}
			plug = loadShaderParameter( shaderName, query, parameter, name, parent, parameterMetadata );
		}

		if( plug )
		{
			plug->setFlags( Gaffer::Plug::Dynamic, false );
			validPlugs.insert( plug );
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

void OSLShader::loadShader( const std::string &shaderName, bool keepExistingValues )
{
	StringPlug *namePlug = this->namePlug()->source<StringPlug>();
	StringPlug *typePlug = this->typePlug()->source<StringPlug>();
	Plug *parametersPlug = this->parametersPlug()->source<Plug>();

	Plug *existingOut = outPlug();
	if( shaderName.empty() )
	{
		parametersPlug->clearChildren();
		namePlug->setValue( "" );
		typePlug->setValue( "" );
		if( existingOut )
		{
			existingOut->clearChildren();
		}
		return;
	}

	OSLQueryPtr query = queryCache().get( shaderName );

	const bool outPlugHadChildren = existingOut ? existingOut->children().size() : false;
	if( !keepExistingValues )
	{
		// If we're not preserving existing values then remove all existing
		// parameter plugs - the various plug creators above know that if a
		// plug exists then they should preserve its values.
		parametersPlug->clearChildren();
		if( existingOut )
		{
			existingOut->clearChildren();
		}
	}

	m_metadata = nullptr;
	namePlug->source<StringPlug>()->setValue( shaderName );
	auto typeIt = g_typeOverrides.find( std::filesystem::path( shaderName ).stem().string() );
	typePlug->source<StringPlug>()->setValue(
		typeIt != g_typeOverrides.end() ?
		typeIt->second :
		std::string( "osl:" ) + ( query->shadertype().string() )
	);

	const IECore::CompoundData *metadata = OSLShader::metadata();
	const IECore::CompoundData *parameterMetadata = nullptr;
	if( metadata )
	{
		parameterMetadata = metadata->member<IECore::CompoundData>( "parameter" );
	}

	loadShaderParameters( shaderName, *query, parametersPlug, parameterMetadata );

	if( existingOut )
	{
		// \todo : This can be removed once old scripts have been updated, and we no longer have
		// old out plugs set to Dynamic lying around
		existingOut->setFlags( Gaffer::Plug::Dynamic, false );
	}

	if( !existingOut || existingOut->typeId() != Plug::staticTypeId() )
	{
		PlugPtr outPlug = new Plug( "out", Plug::Out, Plug::Default );
		if( existingOut )
		{
			// We had an out plug but it was the wrong type (we used
			// to use a CompoundPlug before that was deprecated). Move
			// over any existing child plugs onto our replacement.
			for( Plug::Iterator it( existingOut ); !it.done(); ++it )
			{
				outPlug->addChild( *it );
			}
		}
		setChild( "out", outPlug );
	}

	loadShaderParameters( shaderName, *query, outPlug(), parameterMetadata );

	if( static_cast<bool>( outPlug()->children().size() ) != outPlugHadChildren )
	{
		// OSLShaderUI registers a dynamic metadata entry which depends on whether or
		// not the plug has children, so we must notify the world that the value will
		// have changed.
		Metadata::plugValueChangedSignal( this )( outPlug(), "nodule:type", Metadata::ValueChangedReason::StaticRegistration );
	}
}

//////////////////////////////////////////////////////////////////////////
// Metadata loading code
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::DataPtr convertMetadata( const OSLQuery::Parameter &metadata )
{
	if( metadata.type == TypeDesc::FLOAT )
	{
		return new IECore::FloatData( metadata.fdefault[0] );
	}
	else if( metadata.type == TypeDesc::INT )
	{
		return new IECore::IntData( metadata.idefault[0] );
	}
	else if( metadata.type == TypeDesc::STRING )
	{
		return new IECore::StringData( metadata.sdefault[0].string() );
	}
	else if( metadata.type.aggregate == TypeDesc::VEC3 )
	{
		if( metadata.type.basetype == TypeDesc::FLOAT )
		{
			if( metadata.type.vecsemantics == TypeDesc::COLOR )
			{
				return new IECore::Color3fData( Imath::Color3f(
					metadata.fdefault[0],
					metadata.fdefault[1],
					metadata.fdefault[2]
				) );
			}
			else
			{
				return new IECore::V3fData( Imath::V3f(
					metadata.fdefault[0],
					metadata.fdefault[1],
					metadata.fdefault[2]
				) );
			}
		}
		else
		{
			return new IECore::V3iData( Imath::V3i(
				metadata.idefault[0],
				metadata.idefault[1],
				metadata.idefault[2]
			) );
		}
	}
	else if( metadata.type.arraylen > 0 )
	{
		if( metadata.type.elementtype() == TypeDesc::FLOAT )
		{
			return new FloatVectorData( metadata.fdefault );
		}
		else if( metadata.type.elementtype() == TypeDesc::INT )
		{
			return new IntVectorData( metadata.idefault );
		}
		else if( metadata.type.elementtype() == TypeDesc::STRING )
		{
			StringVectorDataPtr result = new StringVectorData;
			for( vector<ustring>::const_iterator it = metadata.sdefault.begin(), eIt = metadata.sdefault.end(); it != eIt; ++it )
			{
				result->writable().push_back( it->string() );
			}
			return result;
		}
	}

	IECore::msg( IECore::Msg::Warning, "OSLShader", string( "Metadata \"" ) + metadata.name.string() + "\" has unsupported type" );
	return nullptr;
}

IECore::CompoundDataPtr convertMetadata( const std::vector<OSLQuery::Parameter> &metadata )
{
	CompoundDataPtr result = new CompoundData;
	for( std::vector<OSLQuery::Parameter>::const_iterator it = metadata.begin(), eIt = metadata.end(); it != eIt; ++it )
	{
		DataPtr data = convertMetadata( *it );
		if( data )
		{
			result->writable()[it->name.string()] = data;
		}
	}
	return result;
}

IECore::ConstCompoundDataPtr metadataGetter( const std::string &shaderName, size_t &cost, const IECore::Canceller *canceller )
{
	cost = 1;
	if( !shaderName.size() )
	{
		return nullptr;
	}

	const char *searchPath = getenv( "OSL_SHADER_PATHS" );
	OSLQuery query;
	if( !query.open( shaderName, searchPath ? searchPath : "" ) )
	{
		return nullptr;
	}

	CompoundDataPtr metadata = new CompoundData;
	metadata->writable()["shader"] = convertMetadata( query.metadata() );

	CompoundDataPtr parameterMetadata = new CompoundData;
	metadata->writable()["parameter"] = parameterMetadata;

	std::unordered_set<const OSLQuery::Parameter *> parametersAlreadyProcessed;

	// First look for ramps, where any metadata on component parameters should be registered onto the ramp plug
	for( size_t i = 0; i < query.nparams(); ++i )
	{
		// We will check whether this parameter fits as the positions parameter of a ramp
		const OSLQuery::Parameter *positionsParameter = query.getparam( i );

		string nameWithoutSuffix;
		const OSLQuery::Parameter *valuesParameter;
		const OSLQuery::Parameter *basisParameter;
		const OSLQuery::Parameter *countParameter;

		// If this parameter is part of a ramp, register the metadata onto the ramp plug
		if( !findSplineParametersFromPositions( shaderName, query, positionsParameter, nameWithoutSuffix, valuesParameter, basisParameter, countParameter, parametersAlreadyProcessed ) )
		{
			continue;
		}

		CompoundDataPtr data;
		if( countParameter )
		{
			// PRMan splines include a parameter which just contains a point count, and has the base name
			// of the spline. If there is any metadata we should have, we expect to find it there.
			if( countParameter->metadata.size() )
			{
				data = convertMetadata( countParameter->metadata );
			}
		}
		else
		{
			const OSLQuery::Parameter *parameters[] = { valuesParameter, positionsParameter, basisParameter };
			for( const OSLQuery::Parameter *p : parameters )
			{
				if( p->metadata.size() )
				{
					CompoundDataPtr componentData = convertMetadata( p->metadata );
					if( data )
					{
						data->writable().insert( componentData->readable().begin(), componentData->readable().end() );
					}
					else
					{
						data = componentData;
					}
				}
			}
		}

		if( data )
		{
			data->writable().erase( "widget" );
			parameterMetadata->writable()[nameWithoutSuffix] = data;
		}
	}

	for( size_t i = 0; i < query.nparams(); ++i )
	{
		const OSLQuery::Parameter *parameter = query.getparam( i );
		if( parameter->metadata.size() )
		{
			if( !parametersAlreadyProcessed.count( parameter ) )
			{
				const std::string &name = parameter->name.string();
				parameterMetadata->writable()[name] = convertMetadata( parameter->metadata );
			}
		}
	}

	return metadata;
}

using MetadataCache = IECorePreview::LRUCache<std::string, IECore::ConstCompoundDataPtr>;
MetadataCache g_metadataCache( metadataGetter, 10000 );

} // namespace

const IECore::CompoundData *OSLShader::metadata() const
{
	if( m_metadata )
	{
		return m_metadata.get();
	}

	m_metadata = g_metadataCache.get( namePlug()->getValue() );
	return m_metadata.get();
}

const IECore::Data *OSLShader::shaderMetadata( const IECore::InternedString &key ) const
{
	const IECore::CompoundData *m = metadata();
	if( !m )
	{
		return nullptr;
	}
	return m->member<IECore::CompoundData>( "shader" )->member<IECore::Data>( key );
}

const IECore::Data *OSLShader::parameterMetadata( const Gaffer::Plug *plug, const IECore::InternedString &key ) const
{
	const IECore::CompoundData *m = metadata();
	if( !m )
	{
		return nullptr;
	}

	if( plug->parent<Plug>() != parametersPlug() && plug->parent<Plug>() != outPlug() )
	{
		return nullptr;
	}

	const IECore::CompoundData *p = m->member<IECore::CompoundData>( "parameter" )->member<IECore::CompoundData>( plug->getName() );
	if( !p )
	{
		return nullptr;
	}

	return p->member<IECore::Data>( key );
}

void OSLShader::reloadShader()
{
	// Remove any cache entries for the given shader name, allowing
	// them to be reloaded fresh if the shader has changed.
	queryCache().erase( namePlug()->getValue() );
	g_metadataCache.erase( namePlug()->getValue() );
	Shader::reloadShader();
}

namespace GafferOSL
{

// Forward declare function defined in OSLExpressionEngine.cpp. It happens to be easier to implement
// activator expressions in there, but in terms of public API they are more at home on OSLShader.
bool evaluateActivatorExpression( const std::string &expression, const Gaffer::Plug *parameterPlug, const Gaffer::Context *context );

} // namespace GafferOSL

bool OSLShader::evaluateActivatorExpression( const std::string &expression ) const
{
	return GafferOSL::evaluateActivatorExpression( expression, parametersPlug(), Context::current() );
}

bool OSLShader::registerCompatibleShader( const IECore::InternedString shaderType )
{
	ShaderTypeSet &cs = compatibleShaders();
	return cs.insert( shaderType ).second;
}
