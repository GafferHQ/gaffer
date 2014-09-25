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

#include "tbb/mutex.h"

#include "OSL/oslquery.h"

#include "IECore/MessageHandler.h"
#include "IECore/AttributeBlock.h"
#include "IECore/LRUCache.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundNumericPlug.h"

#include "GafferOSL/OSLShader.h"
#include "GafferOSL/OSLRenderer.h"

using namespace std;
using namespace IECore;
using namespace OSL;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferOSL;

//////////////////////////////////////////////////////////////////////////
// LRUCache of ShadingEngines
//////////////////////////////////////////////////////////////////////////

namespace
{

struct ShadingEngineCacheKey
{

	ShadingEngineCacheKey()
		:	shader( NULL )
	{
	}

	ShadingEngineCacheKey( const OSLShader *s )
		:	shader( s ), hash( s->stateHash() )
	{
	}

	bool operator == ( const ShadingEngineCacheKey &other ) const
	{
		return hash == other.hash;
	}

	bool operator != ( const ShadingEngineCacheKey &other ) const
	{
		return hash != other.hash;
	}

	bool operator < ( const ShadingEngineCacheKey &other ) const
	{
		return hash < other.hash;
	}

	mutable const OSLShader *shader;
	MurmurHash hash;

};

inline size_t tbb_hasher( const ShadingEngineCacheKey &cacheKey )
{
	return tbb_hasher( cacheKey.hash );
}

OSLRenderer::ConstShadingEnginePtr getter( const ShadingEngineCacheKey &key, size_t &cost )
{
	cost = 1;

	ConstObjectVectorPtr state = key.shader->state();
	key.shader = NULL; // there's no guarantee the node would even exist after this call, so zero it out to avoid temptation

	if( !state->members().size() )
	{
		return NULL;
	}

	static OSLRendererPtr g_renderer;
	static tbb::mutex g_rendererMutex;

	tbb::mutex::scoped_lock lock( g_rendererMutex );

	if( !g_renderer )
	{
		g_renderer = new OSLRenderer;
		if( const char *searchPath = getenv( "OSL_SHADER_PATHS" ) )
		{
			g_renderer->setOption( "osl:searchpath:shader", new StringData( searchPath ) );
			g_renderer->setOption( "osl:lockgeom", new IntData( 1 ) );
		}
		g_renderer->worldBegin();
	}

	IECore::AttributeBlock attributeBlock( g_renderer );

	for( ObjectVector::MemberContainer::const_iterator it = state->members().begin(), eIt = state->members().end(); it != eIt; it++ )
	{
		const StateRenderable *s = runTimeCast<const StateRenderable>( it->get() );
		if( s )
		{
			s->render( g_renderer.get() );
		}
	}

	return g_renderer->shadingEngine();
}

typedef LRUCache<ShadingEngineCacheKey, OSLRenderer::ConstShadingEnginePtr> ShadingEngineCache;
ShadingEngineCache g_shadingEngineCache( getter, 10000 );

} // namespace

//////////////////////////////////////////////////////////////////////////
// OSLShader
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( OSLShader );

OSLShader::OSLShader( const std::string &name )
	:	GafferScene::Shader( name )
{
}

OSLShader::~OSLShader()
{
}

OSLRenderer::ConstShadingEnginePtr OSLShader::shadingEngine() const
{
	return g_shadingEngineCache.get( ShadingEngineCacheKey( this ) );
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
		const Plug *sourcePlug = inputPlug->source<Plug>();
		const GafferScene::Shader *sourceShader = runTimeCast<const GafferScene::Shader>( sourcePlug->node() );
		const Plug *sourceShaderOutPlug = sourceShader ? sourceShader->outPlug() : NULL;

		if( sourceShaderOutPlug && ( sourceShaderOutPlug == inputPlug || sourceShaderOutPlug->isAncestorOf( inputPlug ) ) )
		{
			// source is the output of a shader node, so it'd better be
			// a generic osl shader.
			if( !sourceShader->isInstanceOf( staticTypeId() ) )
			{
				return false;
			}
			if( sourceShader->typePlug()->getValue() != "osl:shader" )
			{
				return false;
			}
			// osl disallows the connection of vectors to colours
			if( plug->isInstanceOf( Color3fPlug::staticTypeId() ) && inputPlug->isInstanceOf( V3fPlug::staticTypeId() ) )
			{
				return false;
			}
			// and we can only connect closures into closures
			if( plug->typeId() == Plug::staticTypeId() && inputPlug->typeId() != Plug::staticTypeId() )
			{
				return false;
			}
		}
	}

	return true;
}

//////////////////////////////////////////////////////////////////////////
// shader loading code
//////////////////////////////////////////////////////////////////////////

static std::string plugName( const OSLQuery::Parameter *parameter )
{
	size_t i = parameter->name.find( "." );
	if( i != string::npos )
	{
		return parameter->name.substr( i + 1 ).c_str();
	}
	return parameter->name.c_str();
}

static void transferConnectionOrValue( Plug *sourcePlug, Plug *destinationPlug )
{
	if( !sourcePlug )
	{
		return;
	}

	if( Plug *input = sourcePlug->getInput<Plug>() )
	{
		destinationPlug->setInput( input );
	}
	else
	{
		ValuePlug *sourceValuePlug = runTimeCast<ValuePlug>( sourcePlug );
		ValuePlug *destinationValuePlug = runTimeCast<ValuePlug>( destinationPlug );
		if( destinationValuePlug && sourceValuePlug )
		{
			destinationValuePlug->setFrom( sourceValuePlug );
		}
	}
}

static Plug *loadStringParameter( const OSLQuery::Parameter *parameter, Gaffer::CompoundPlug *parent )
{
	string defaultValue;
	if( parameter->sdefault.size() )
	{
		defaultValue = parameter->sdefault[0].c_str();
	}

	const string name = plugName( parameter );
	StringPlug *existingPlug = parent->getChild<StringPlug>( name );
	if(	existingPlug && existingPlug->defaultValue() == defaultValue )
	{
		return existingPlug;
	}

	StringPlugPtr plug = new StringPlug( name, parent->direction(), defaultValue, Plug::Default | Plug::Dynamic );

	transferConnectionOrValue( existingPlug, plug.get() );

	parent->setChild( name, plug );

	return plug.get();
}

template<typename PlugType>
static Plug *loadNumericParameter( const OSLQuery::Parameter *parameter, Gaffer::CompoundPlug *parent )
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

	/// \todo Get from metadata
	ValueType minValue( Imath::limits<ValueType>::min() );
	ValueType maxValue( Imath::limits<ValueType>::max() );

	const string name = plugName( parameter );
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

	typename PlugType::Ptr plug = new PlugType( name, parent->direction(), defaultValue, minValue, maxValue, Plug::Default | Plug::Dynamic );

	transferConnectionOrValue( existingPlug, plug.get() );

	parent->setChild( name, plug );

	return plug.get();
}

template <typename PlugType>
static Plug *loadCompoundNumericParameter( const OSLQuery::Parameter *parameter, Gaffer::CompoundPlug *parent )
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

	const string name = plugName( parameter );
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

	typename PlugType::Ptr plug = new PlugType( name, parent->direction(), defaultValue, minValue, maxValue, Plug::Default | Plug::Dynamic );

	if( existingPlug )
	{
		for( size_t i = 0, e = existingPlug->children().size(); i < e; ++i )
		{
			transferConnectionOrValue(
				existingPlug->getChild( i ),
				plug->getChild( i )
			);
		}
	}

	parent->setChild( name, plug );
	return plug.get();
}

static Plug *loadClosureParameter( const OSLQuery::Parameter *parameter, Gaffer::CompoundPlug *parent )
{
	const string name = plugName( parameter );
	Plug *existingPlug = parent->getChild<Plug>( name );
	if(	existingPlug && existingPlug->typeId() == Plug::staticTypeId() )
	{
		return existingPlug;
	}

	PlugPtr plug = new Plug( name, parent->direction(), Plug::Default | Plug::Dynamic );

	transferConnectionOrValue( existingPlug, plug.get() );

	parent->setChild( name, plug );

	return plug.get();
}

// forward declaration so loadStructParameter() can call it.
static Plug *loadShaderParameter( const OSLQuery &query, const OSLQuery::Parameter *parameter, Gaffer::CompoundPlug *parent, bool keepExistingValues );

static Plug *loadStructParameter( const OSLQuery &query, const OSLQuery::Parameter *parameter, Gaffer::CompoundPlug *parent, bool keepExistingValues )
{
	CompoundPlug *result = NULL;

	const string name = plugName( parameter );
	CompoundPlug *existingPlug = parent->getChild<CompoundPlug>( name );
	if( existingPlug )
	{
		if( !keepExistingValues )
		{
			existingPlug->clearChildren();
		}
		result = existingPlug;
	}
	else
	{
		result = new CompoundPlug( name, parent->direction(), Plug::Default | Plug::Dynamic );
	}

#if OSL_LIBRARY_VERSION_CODE > 10500
	typedef OIIO::ustring String;
#else
	typedef std::string String;
#endif

	for( vector<String>::const_iterator it = parameter->fields.begin(), eIt = parameter->fields.end(); it != eIt; ++it )
	{
		std::string fieldName = std::string( parameter->name.c_str() ) + "." + it->c_str();
		loadShaderParameter( query, query.getparam( fieldName ), result, keepExistingValues );
	}

	// remove any old plugs which it turned out we didn't need

	if( keepExistingValues )
	{
		for( int i = result->children().size() - 1; i >= 0; --i )
		{
			GraphComponent *child = result->getChild<GraphComponent>( i );
			if( std::find( parameter->fields.begin(), parameter->fields.end(), child->getName().string() ) == parameter->fields.end() )
			{
				result->removeChild( child );
			}
		}
	}

	parent->setChild( name, result );

	return result;
}

static Plug *loadShaderParameter( const OSLQuery &query, const OSLQuery::Parameter *parameter, Gaffer::CompoundPlug *parent, bool keepExistingValues )
{
	Plug *result = NULL;

	if( parameter->isstruct )
	{
		result = loadStructParameter( query, parameter, parent, keepExistingValues );
	}
	else if( parameter->isclosure )
	{
		result = loadClosureParameter( parameter, parent );
	}
	else if( parameter->type.arraylen == 0 )
	{
		if( parameter->type.basetype == TypeDesc::FLOAT || parameter->type.basetype == TypeDesc::INT )
		{
			// numeric in some way
			if( parameter->type.aggregate == TypeDesc::SCALAR )
			{
				if( parameter->type.basetype == TypeDesc::FLOAT )
				{
					result = loadNumericParameter<FloatPlug>( parameter, parent );
				}
				else
				{
					result = loadNumericParameter<IntPlug>( parameter, parent );
				}
			}
			else if( parameter->type.aggregate == TypeDesc::VEC3 )
			{
				if( parameter->type.basetype == TypeDesc::FLOAT )
				{
					if( parameter->type.vecsemantics == TypeDesc::COLOR )
					{
						result = loadCompoundNumericParameter<Color3fPlug>( parameter, parent );
					}
					else
					{
						result = loadCompoundNumericParameter<V3fPlug>( parameter, parent );
					}
				}
				else
				{
					result = loadCompoundNumericParameter<V3iPlug>( parameter, parent );
				}
			}
		}
		else if( parameter->type.basetype == TypeDesc::STRING )
		{
			result = loadStringParameter( parameter, parent );
		}
	}
	else
	{
		/// \todo support array parameters
	}

	if( !result )
	{
		msg( Msg::Warning, "OSLShader::loadShader", boost::format( "Parameter \"%s\" has unsupported type" ) % parameter->name.c_str() );
	}

	return result;
}

static void loadShaderParameters( const OSLQuery &query, Gaffer::CompoundPlug *parametersPlug, bool keepExistingValues )
{

	// if we're not preserving existing values then remove all existing parameter plugs - the various
	// plug creators above know that if a plug exists then they should preserve its values.

	if( !keepExistingValues )
	{
		parametersPlug->clearChildren();
	}

	// make sure we have a plug to represent each parameter, reusing plugs wherever possible.

	set<string> validPlugNames;
	for( size_t i = 0; i < query.nparams(); ++i )
	{
		const OSLQuery::Parameter *parameter = query.getparam( i );
		const Plug::Direction direction = parameter->isoutput ? Plug::Out : Plug::In;
		if( direction != parametersPlug->direction() )
		{
			continue;
		}

		if( parameter->name.find( "." ) != string::npos )
		{
			// member of a struct - will be loaded when the struct is loaded
			continue;
		}

		const Plug *plug = loadShaderParameter( query, parameter, parametersPlug, keepExistingValues );

		if( plug )
		{
			validPlugNames.insert( parameter->name.c_str() );
		}
	}

	// remove any old plugs which it turned out we didn't need

	if( keepExistingValues )
	{
		for( int i = parametersPlug->children().size() - 1; i >= 0; --i )
		{
			GraphComponent *child = parametersPlug->getChild<GraphComponent>( i );
			if( validPlugNames.find( child->getName().string() ) == validPlugNames.end() )
			{
				parametersPlug->removeChild( child );
			}
		}
	}

}

void OSLShader::loadShader( const std::string &shaderName, bool keepExistingValues )
{
	const char *searchPath = getenv( "OSL_SHADER_PATHS" );

	OSLQuery query;
	if( !query.open( shaderName, searchPath ? searchPath : "" ) )
	{
		throw Exception( query.error() );
	}

	loadShaderParameters( query, parametersPlug(), keepExistingValues );

	if( query.shadertype() == "shader" )
	{
		CompoundPlug *existingOut = getChild<CompoundPlug>( "out" );
		if( !existingOut || existingOut->typeId() != CompoundPlug::staticTypeId() )
		{
			CompoundPlugPtr outPlug = new CompoundPlug( "out", Plug::Out, Plug::Default | Plug::Dynamic );
			setChild( "out", outPlug );
		}
		loadShaderParameters( query, getChild<CompoundPlug>( "out" ), keepExistingValues );
	}
	else
	{
		Plug *existingOut = getChild<Plug>( "out" );
		if( !existingOut || existingOut->typeId() != Plug::staticTypeId() )
		{
			PlugPtr outPlug = new Plug( "out", Plug::Out, Plug::Default | Plug::Dynamic );
			setChild( "out", outPlug );
		}
	}

	namePlug()->setValue( shaderName );
	typePlug()->setValue( std::string( "osl:" ) + query.shadertype().c_str() );

	m_metadata = NULL;
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

	return NULL;
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
		return NULL;
	}

	const char *searchPath = getenv( "OSL_SHADER_PATHS" );
	OSLQuery query;
	if( !query.open( key, searchPath ? searchPath : "" ) )
	{
		throw Exception( query.error() );
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
			parameterMetadata->writable()[parameter->name.c_str()] = convertMetadata( parameter->metadata );
		}
	}

	return metadata;
}

typedef LRUCache<std::string, IECore::ConstCompoundDataPtr> MetadataCache;
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
		return NULL;
	}
	return m->member<IECore::CompoundData>( "shader" )->member<IECore::Data>( key );
}

const IECore::Data *OSLShader::parameterMetadata( const Gaffer::Plug *plug, const IECore::InternedString &key ) const
{
	const IECore::CompoundData *m = metadata();
	if( !m )
	{
		return NULL;
	}

	if( plug->parent<Plug>() != parametersPlug() )
	{
		return NULL;
	}

	const IECore::CompoundData *p = m->member<IECore::CompoundData>( "parameter" )->member<IECore::CompoundData>( plug->getName() );
	if( !p )
	{
		return NULL;
	}
	return p->member<IECore::Data>( key );
}
