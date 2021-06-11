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

#include "GafferScene/RendererAlgo.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/SplinePlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECoreScene/ShaderNetwork.h"

#include "IECoreImage/OpenImageIOAlgo.h"

#include "IECore/MessageHandler.h"

#include "OSL/oslquery.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/container/flat_set.hpp"

#include "tbb/mutex.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace OSL;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferOSL;

//////////////////////////////////////////////////////////////////////////
// LRUCache of ShadingEngines
//////////////////////////////////////////////////////////////////////////

namespace
{

struct ShadingEngineCacheGetterKey
{

	ShadingEngineCacheGetterKey()
		:	shader( nullptr )
	{
	}

	ShadingEngineCacheGetterKey( const OSLShader *s )
		:	shader( s ), hash( s->attributesHash() )
	{
	}

	operator const IECore::MurmurHash & () const
	{
		return hash;
	}

	const OSLShader *shader;
	MurmurHash hash;

};

ConstShadingEnginePtr getter( const ShadingEngineCacheGetterKey &key, size_t &cost )
{
	cost = 1;

	ConstCompoundObjectPtr attributes = key.shader->attributes();

	CompoundObject::ObjectMap::const_iterator it = attributes->members().find( "osl:surface" );
	if( it == attributes->members().end() )
	{
		// If we didn't find a surface, check if it's named "osl:shader", since OSL doesn't actually
		// enforce any difference between surfaces and shaders
		it = attributes->members().find( "osl:shader" );
	}

	if( it == attributes->members().end() )
	{
		return nullptr;
	}

	const ShaderNetwork *network = runTimeCast<const ShaderNetwork>( it->second.get() );
	if( !network || !network->size() )
	{
		return nullptr;
	}

	return new ShadingEngine( network );
}

typedef IECorePreview::LRUCache<IECore::MurmurHash, ConstShadingEnginePtr, IECorePreview::LRUCachePolicy::Parallel, ShadingEngineCacheGetterKey> ShadingEngineCache;
ShadingEngineCache g_shadingEngineCache( getter, 10000 );

typedef boost::container::flat_set<IECore::InternedString> ShaderTypeSet;
ShaderTypeSet &compatibleShaders()
{
	static ShaderTypeSet g_compatibleShaders;
	return g_compatibleShaders;
}

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
		[] ( const std::string &shaderName, size_t &cost ) {
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
		IECore::msg( IECore::Msg::Error, "OSLShader::correspondingInput", boost::format( "Parameter \"%s\" does not exist" ) % input->readable() );
		return nullptr;
	}

	return result;
}

ConstShadingEnginePtr OSLShader::shadingEngine() const
{
	return g_shadingEngineCache.get( ShadingEngineCacheGetterKey( this ) );
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

			const IECore::InternedString sourceShaderType = sourceShader->typePlug()->getValue();
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
// Shader loading code
//////////////////////////////////////////////////////////////////////////

namespace
{

Plug *loadStringParameter( const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent )
{
	string defaultValue;
	if( parameter->sdefault.size() )
	{
		defaultValue = parameter->sdefault[0].c_str();
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
			defaultValueDataWritable[i] = parameter->sdefault[i].c_str();
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
	typedef typename PlugType::ValueType ValueType;

	ValueType defaultValue( 0 );
	if( parameter->idefault.size() )
	{
		defaultValue = ValueType( parameter->idefault[0] );
	}
	else if( parameter->fdefault.size() )
	{
		defaultValue = ValueType( parameter->fdefault[0] );
	}

	ValueType minValue( Imath::limits<ValueType>::min() );
	ValueType maxValue( Imath::limits<ValueType>::max() );
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
	typedef typename PlugType::ValueType DataType;
	typedef typename DataType::ValueType ValueType;
	typedef typename ValueType::value_type ElementType;

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
	typedef typename PlugType::ValueType ValueType;
	typedef typename ValueType::BaseType BaseType;

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
	ValueType minValue( Imath::limits<BaseType>::min() );
	ValueType maxValue( Imath::limits<BaseType>::max() );
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
	typedef typename PlugType::ValueType DataType;
	typedef typename DataType::ValueType ValueType;
	typedef typename ValueType::value_type ElementType;
	typedef typename ElementType::BaseType BaseType;

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

void updatePoints( Splineff::PointContainer &points, const OSLQuery::Parameter *positionsParameter, const OSLQuery::Parameter *valuesParameter )
{
	const vector<float> &positions = positionsParameter->fdefault;
	const vector<float> &values = valuesParameter->fdefault;

	for( size_t i = 0; ( i < positions.size() ) && ( i < values.size() ); ++i )
	{
		points.insert( Splineff::Point( positions[i], values[i] ) );
	}
}

void updatePoints( SplinefColor3f::PointContainer &points, const OSLQuery::Parameter *positionsParameter, const OSLQuery::Parameter *valuesParameter )
{
	const vector<float> &positions = positionsParameter->fdefault;
	const vector<float> &values = valuesParameter->fdefault;

	for( size_t i = 0; i < positions.size() && i*3+2 < values.size(); ++i )
	{
		points.insert(
			SplinefColor3f::Point(
				positions[i],
				Color3f(
					values[i*3],
					values[i*3+1],
					values[i*3+2]
				)
			)
		);
	}
}

template <typename PlugType>
Plug *loadSplineParameters( const OSLQuery::Parameter *positionsParameter, const OSLQuery::Parameter *valuesParameter, const OSLQuery::Parameter *basisParameter, const InternedString &name, Gaffer::Plug *parent )
{
	const std::string &basis = basisParameter->sdefault.front().string();

	typename PlugType::ValueType defaultValue;

	defaultValue.interpolation = SplineDefinitionInterpolationCatmullRom;
	if( basis == "bspline" )
	{
		defaultValue.interpolation = SplineDefinitionInterpolationBSpline;
	}
	else if( basis == "linear" )
	{
		defaultValue.interpolation = SplineDefinitionInterpolationLinear;
	}

	updatePoints( defaultValue.points, positionsParameter, valuesParameter );

	// The OSL spline representation includes the need for duplicated end points in order to hit the end.
	// We need to remove these
	if( !defaultValue.trimEndPoints() )
	{
		// Failed to trim end points - the value of the OSL spline can't be represented,
		// so just wipe out the control points
		defaultValue.points.clear();
	}

	PlugType *existingPlug = parent->getChild<PlugType>( name );
	if( existingPlug && existingPlug->defaultValue() == defaultValue )
	{
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( name, parent->direction(), defaultValue, Plug::Default );
	parent->setChild( name, plug );

	return plug.get();
}

bool findSplineParameters( const OSLQuery &query, const OSLQuery::Parameter *parameter, std::string &nameWithoutSuffix, const OSLQuery::Parameter * &positionsParameter, const OSLQuery::Parameter * &valuesParameter, const OSLQuery::Parameter * &basisParameter )
{
	const char *suffixes[] = { "Positions", "Values", "Basis", nullptr };
	const char *suffix = nullptr;
	for( const char **suffixPtr = suffixes; *suffixPtr; ++suffixPtr )
	{
		if( boost::ends_with( parameter->name.c_str(), *suffixPtr ) )
		{
			suffix = *suffixPtr;
			break;
		}
	}

	if( !suffix )
	{
		return false;
	}

	nameWithoutSuffix = parameter->name.string().substr( 0, parameter->name.string().size() - strlen( suffix ) );

	positionsParameter = query.getparam( nameWithoutSuffix + "Positions" );
	if(
		!positionsParameter ||
		!positionsParameter->type.is_array() ||
		positionsParameter->type.basetype != TypeDesc::FLOAT ||
		positionsParameter->type.aggregate != TypeDesc::SCALAR
	)
	{
		return false;
	}

	valuesParameter = query.getparam( nameWithoutSuffix + "Values" );
	if(
		!valuesParameter ||
		!valuesParameter->type.is_array() ||
		valuesParameter->type.basetype != TypeDesc::FLOAT ||
		( valuesParameter->type.aggregate != TypeDesc::SCALAR && valuesParameter->type.vecsemantics != TypeDesc::COLOR )
	)
	{
		return false;
	}

	basisParameter = query.getparam( nameWithoutSuffix + "Basis" );
	if( !basisParameter || basisParameter->type != TypeDesc::TypeString )
	{
		return false;
	}

	return true;
}

Plug *loadSplineParameter( const OSLQuery &query, const OSLQuery::Parameter *parameter, Gaffer::Plug *parent, const std::string &prefix )
{

	string nameWithoutSuffix;
	const OSLQuery::Parameter *positionsParameter;
	const OSLQuery::Parameter *valuesParameter;
	const OSLQuery::Parameter *basisParameter;

	if( !findSplineParameters( query, parameter, nameWithoutSuffix, positionsParameter, valuesParameter, basisParameter ) )
	{
		return nullptr;
	}

	const string name = nameWithoutSuffix.substr( prefix.size() );
	if( valuesParameter->type.vecsemantics == TypeDesc::COLOR )
	{
		return loadSplineParameters<SplinefColor3fPlug>( positionsParameter, valuesParameter, basisParameter, name, parent );
	}
	else
	{
		return loadSplineParameters<SplineffPlug>( positionsParameter, valuesParameter, basisParameter, name, parent );
	}
}

// Forward declaration so loadStructParameter() can call it.
void loadShaderParameters( const OSLQuery &query, Gaffer::Plug *parent, const CompoundData *metadata, const std::string &prefix = "" );

Plug *loadStructParameter( const OSLQuery &query, const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent )
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
			for( PlugIterator it( existingPlug ); !it.done(); ++it )
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
	loadShaderParameters( query, result, nullptr, parameter->name.string() + "." );

	parent->setChild( name, result );

	return result;
}

Plug *loadShaderParameter( const OSLQuery &query, const OSLQuery::Parameter *parameter, const InternedString &name, Gaffer::Plug *parent, const CompoundData *metadata )
{
	Plug *result = nullptr;

	if( parameter->isstruct )
	{
		result = loadStructParameter( query, parameter, name, parent );
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
		msg( Msg::Warning, "OSLShader::loadShader", boost::format( "Parameter \"%s\" has unsupported type" ) % parameter->name.c_str() );
	}

	return result;
}

void loadShaderParameters( const OSLQuery &query, Gaffer::Plug *parent, const CompoundData *metadata, const std::string &prefix )
{

	// Make sure we have a plug to represent each parameter, reusing plugs wherever possible.

	set<const Plug *> validPlugs;
	for( size_t i = 0; i < query.nparams(); ++i )
	{
		const OSLQuery::Parameter *parameter = query.getparam( i );
		const Plug::Direction direction = parameter->isoutput ? Plug::Out : Plug::In;
		if( direction != parent->direction() )
		{
			continue;
		}

		if( !boost::starts_with( parameter->name.c_str(), prefix ) )
		{
			continue;
		}

		const string name = parameter->name.string().substr( prefix.size() );
		if( name.find( "." ) != string::npos )
		{
			// Member of a struct - will be loaded when the struct is loaded
			continue;
		}

		// Spline parameters are a nasty special case because multiple shader
		// parameters become a single plug on the node, so we deal with them
		// outside of `loadShaderParameter()`, which deals exclusively with
		// the one-parameter-at-a-time case.
		Plug *plug = loadSplineParameter( query, parameter, parent, prefix );
		if( !plug )
		{
			const CompoundData *parameterMetadata = nullptr;
			if( metadata )
			{
				parameterMetadata = metadata->member<IECore::CompoundData>( name );
			}


			plug = loadShaderParameter( query, parameter, name, parent, parameterMetadata );
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
	typePlug->source<StringPlug>()->setValue( std::string( "osl:" ) + query->shadertype().c_str() );

	const IECore::CompoundData *metadata = OSLShader::metadata();
	const IECore::CompoundData *parameterMetadata = nullptr;
	if( metadata )
	{
		parameterMetadata = metadata->member<IECore::CompoundData>( "parameter" );
	}

	loadShaderParameters( *query, parametersPlug, parameterMetadata );

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
			for( PlugIterator it( existingOut ); !it.done(); ++it )
			{
				outPlug->addChild( *it );
			}
		}
		setChild( "out", outPlug );
	}

	if( query->shadertype() == "shader" )
	{
		loadShaderParameters( *query, outPlug(), parameterMetadata );
	}
	else
	{
		outPlug()->clearChildren();
	}

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

static IECore::DataPtr convertMetadata( const OSLQuery::Parameter &metadata )
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
		return new IECore::StringData( metadata.sdefault[0].c_str() );
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

	IECore::msg( IECore::Msg::Warning, "OSLShader", string( "Metadata \"" ) + metadata.name.c_str() + "\" has unsupported type" );
	return nullptr;
}

static IECore::CompoundDataPtr convertMetadata( const std::vector<OSLQuery::Parameter> &metadata )
{
	CompoundDataPtr result = new CompoundData;
	for( std::vector<OSLQuery::Parameter>::const_iterator it = metadata.begin(), eIt = metadata.end(); it != eIt; ++it )
	{
		DataPtr data = convertMetadata( *it );
		if( data )
		{
			result->writable()[it->name.c_str()] = data;
		}
	}
	return result;
}

static IECore::ConstCompoundDataPtr metadataGetter( const std::string &key, size_t &cost )
{
	cost = 1;
	if( !key.size() )
	{
		return nullptr;
	}

	const char *searchPath = getenv( "OSL_SHADER_PATHS" );
	OSLQuery query;
	if( !query.open( key, searchPath ? searchPath : "" ) )
	{
		return nullptr;
	}

	CompoundDataPtr metadata = new CompoundData;
	metadata->writable()["shader"] = convertMetadata( query.metadata() );

	CompoundDataPtr parameterMetadata = new CompoundData;
	metadata->writable()["parameter"] = parameterMetadata;
	for( size_t i = 0; i < query.nparams(); ++i )
	{
		const OSLQuery::Parameter *parameter = query.getparam( i );
		if( parameter->metadata.size() )
		{
			string nameWithoutSuffix;
			const OSLQuery::Parameter *positionsParameter;
			const OSLQuery::Parameter *valuesParameter;
			const OSLQuery::Parameter *basisParameter;

			// If this parameter is part of a spline, register the metadata onto the spline plug
			if( findSplineParameters( query, parameter, nameWithoutSuffix, positionsParameter, valuesParameter, basisParameter ) )
			{
				// We merge metadata found on all the parameters that make up the plug, but in no particular order.
				// If you specify conflicting metadata on the different parameters you may get inconsistent results.
				CompoundData *prevData = parameterMetadata->member<CompoundData>( nameWithoutSuffix );
				CompoundDataPtr data = convertMetadata( parameter->metadata );
				if( prevData )
				{
					data->writable().insert( prevData->readable().begin(), prevData->readable().end() );
				}

				parameterMetadata->writable()[nameWithoutSuffix] = data;
			}
			else
			{
				parameterMetadata->writable()[parameter->name.c_str()] = convertMetadata( parameter->metadata );
			}
		}
	}

	return metadata;
}

typedef IECorePreview::LRUCache<std::string, IECore::ConstCompoundDataPtr> MetadataCache;
MetadataCache g_metadataCache( metadataGetter, 10000 );

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

bool OSLShader::registerCompatibleShader( const IECore::InternedString shaderType )
{
	ShaderTypeSet &cs = compatibleShaders();
	return cs.insert( shaderType ).second;
}
