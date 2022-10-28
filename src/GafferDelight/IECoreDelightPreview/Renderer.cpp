//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
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

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "GafferDelight/IECoreDelightPreview/NodeAlgo.h"
#include "GafferDelight/IECoreDelightPreview/ParameterList.h"

#include "IECoreScene/Shader.h"
#include "IECoreScene/ShaderNetwork.h"
#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/MessageHandler.h"
#include "IECore/SearchPath.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "tbb/concurrent_hash_map.h"

#include <unordered_map>

#include <nsi.h>

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreDelight;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

template<typename T>
T *reportedCast( const IECore::RunTimeTyped *v, const char *type, const IECore::InternedString &name )
{
	T *t = IECore::runTimeCast<T>( v );
	if( t )
	{
		return t;
	}

	IECore::msg( IECore::Msg::Warning, "IECoreDelight::Renderer", boost::format( "Expected %s but got %s for %s \"%s\"." ) % T::staticTypeName() % v->typeName() % type % name.c_str() );
	return nullptr;
}

template<typename T>
T parameter( const IECore::CompoundDataMap &parameters, const IECore::InternedString &name, const T &defaultValue )
{
	IECore::CompoundDataMap::const_iterator it = parameters.find( name );
	if( it == parameters.end() )
	{
		return defaultValue;
	}

	using DataType = IECore::TypedData<T>;
	if( const DataType *d = reportedCast<const DataType>( it->second.get(), "parameter", name ) )
	{
		return d->readable();
	}
	else
	{
		return defaultValue;
	}
}

std::string shaderCacheGetter( const std::string &shaderName, size_t &cost, const IECore::Canceller *canceller )
{
	cost = 1;
	const char *oslShaderPaths = getenv( "OSL_SHADER_PATHS" );
	SearchPath searchPath( oslShaderPaths ? oslShaderPaths : "" );
	boost::filesystem::path path = searchPath.find( shaderName + ".oso" );
	if( path.empty() )
	{
		return shaderName;
	}
	else
	{
		return path.generic_string();
	}
}

using ShaderSearchPathCache = IECorePreview::LRUCache<std::string, std::string>;
ShaderSearchPathCache g_shaderSearchPathCache( shaderCacheGetter, 10000 );

} // namespace

//////////////////////////////////////////////////////////////////////////
// DelightHandle
//////////////////////////////////////////////////////////////////////////

namespace
{

class DelightHandle
{

	public :

		enum Ownership
		{
			Unowned,
			Owned,
		};

		DelightHandle()
			: 	m_context( NSI_BAD_CONTEXT ), m_ownership( Unowned )
		{
		}

		DelightHandle( NSIContext_t context, const std::string &name, Ownership ownership )
			:	m_context( context ), m_name( name ), m_ownership( ownership )
		{
		}

		DelightHandle(
			NSIContext_t context,
			const std::string &name,
			Ownership ownership,
			const char *type,
			const ParameterList &parameters = ParameterList()
		)	: DelightHandle( context, name, ownership )
		{
			NSICreate( context, m_name.c_str(), type, 0, nullptr );
			if( parameters.size() )
			{
				NSISetAttribute( context, m_name.c_str(), parameters.size(), parameters.data() );
			}
		}

		DelightHandle( DelightHandle &&h )
			:	DelightHandle()
		{
			m_context = h.m_context;
			m_name = h.m_name;
			m_ownership = h.m_ownership;
			h.release();
		}

		~DelightHandle()
		{
			reset();
		}

		DelightHandle &operator=( DelightHandle &&h )
		{
			m_context = h.m_context;
			m_name = h.m_name;
			m_ownership = h.m_ownership;
			h.release();
			return *this;
		}

		NSIContext_t context() const
		{
			return m_context;
		}

		const char *name() const
		{
			return m_name.c_str();
		}

		Ownership ownership() const
		{
			return m_ownership;
		}

		void reset()
		{
			if( m_ownership == Owned && m_context != NSI_BAD_CONTEXT )
			{
				NSIDelete( m_context, m_name.c_str(), 0, nullptr );
			}
			release();
		}

	private :

		void release()
		{
			m_context = NSI_BAD_CONTEXT;
			m_name = "";
			m_ownership = Unowned;
		}

		NSIContext_t m_context;
		std::string m_name;
		Ownership m_ownership;

};

using DelightHandleSharedPtr = std::shared_ptr<DelightHandle>;
using DelightHandleWeakPtr = std::weak_ptr<DelightHandle>;

} // namespace

//////////////////////////////////////////////////////////////////////////
// DelightOutput
//////////////////////////////////////////////////////////////////////////

namespace
{

class DelightOutput : public IECore::RefCounted
{

	public :

		DelightOutput( NSIContext_t context, const std::string &name, const IECoreScene::Output *output, DelightHandle::Ownership ownership )
			:	m_context( context )
		{
			// Driver

			const char *typePtr = output->getType().c_str();
			const char *namePtr = output->getName().c_str();

			ParameterList driverParams( output->parameters() );
			driverParams.add( { "drivername", &typePtr, NSITypeString, 0, 1, 0 } );
			driverParams.add( { "imagefilename", &namePtr, NSITypeString, 0, 1, 0 } );

			m_driverHandle = DelightHandle( context, "outputDriver:" + name, ownership, "outputdriver", driverParams );

			// Layer

			string variableName;
			string variableSource;
			string layerType;
			string layerName;
			int withAlpha = 0;

			vector<string> tokens;
			IECore::StringAlgo::tokenize( output->getData(), ' ', tokens );
			if( tokens.size() == 1 )
			{
				if( tokens[0] == "rgb" || tokens[0] == "rgba" )
				{
					variableName = "Ci";
					variableSource = "shader";
					layerType = "color";
					withAlpha = tokens[0] == "rgba" ? 1 : 0;
				}
				else if( tokens[0] == "z" || tokens[0] == "a" )
				{
					variableName = tokens[0] == "a" ? "alpha" : tokens[0];
					variableSource = "builtin";
					layerType = "scalar";
				}
			}
			else if( tokens.size() == 2 )
			{
				if( tokens[0] == "float" )
				{
					layerType = "scalar";
				}
				else if( tokens[0] == "point" )
				{
					layerType = "vector";
				}
				else
				{
					layerType = tokens[0];
				}

				vector<string> nameTokens;
				IECore::StringAlgo::tokenize( tokens[1], ':', nameTokens );
				if( nameTokens.size() == 1 )
				{
					variableName = nameTokens[0];
					variableSource = "shader";
				}
				else if( nameTokens.size() == 2 )
				{
					variableName = nameTokens[1];
					variableSource = nameTokens[0];
				}
				layerName = variableName;
			}

			ParameterList layerParams;

			layerParams.add( "variablename", variableName );
			layerParams.add( "variablesource", variableSource );
			layerParams.add( "layertype", layerType );
			layerParams.add( "layername", layerName );
			layerParams.add( { "withalpha", &withAlpha, NSITypeInteger, 0, 1, 0 } );

			const string scalarFormat = this->scalarFormat( output );
			const string colorProfile = scalarFormat == "float" ? "linear" : "sRGB";
			layerParams.add( "scalarformat", scalarFormat );
			layerParams.add( "colorprofile", colorProfile );

			m_layerHandle = DelightHandle( context, "outputLayer:" + name, ownership, "outputlayer", layerParams );

			NSIConnect(
				m_context,
				m_driverHandle.name(), "",
				m_layerHandle.name(), "outputdrivers",
				0, nullptr
			);
		}

		const DelightHandle &layerHandle() const
		{
			return m_layerHandle;
		}

	private :

		const char *scalarFormat( const IECoreScene::Output *output ) const
		{
			// Map old-school "quantize" setting to scalarformat. Maybe
			// we should have a standard more suitable for mapping to modern
			// renderers and display drivers? How would we request half outputs
			// for instance?
			const vector<int> quantize = parameter<vector<int>>( output->parameters(), "quantize", { 0, 0, 0, 0 } );
			if( quantize == vector<int>( { 0, 255, 0, 255 } ) )
			{
				return "uint8";
			}
			else if( quantize == vector<int>( { 0, 65536, 0, 65536 } ) )
			{
				return "uint16";
			}
			else
			{
				return "float";
			}
		}

		NSIContext_t m_context;
		DelightHandle m_driverHandle;
		DelightHandle m_layerHandle;

};

IE_CORE_DECLAREPTR( DelightOutput )

} // namespace

//////////////////////////////////////////////////////////////////////////
// DelightShader
//////////////////////////////////////////////////////////////////////////

namespace
{

class DelightShader : public IECore::RefCounted
{

	public :

		DelightShader( NSIContext_t context, const IECoreScene::ShaderNetwork *shaderNetwork, DelightHandle::Ownership ownership )
		{
			const string name = "shader:" + shaderNetwork->Object::hash().toString();
			ShaderNetworkAlgo::depthFirstTraverse(
				shaderNetwork,
				[this, &name, &context, &ownership] ( const ShaderNetwork *shaderNetwork, const InternedString &handle ) {

					// Create node

					const Shader *shader = shaderNetwork->getShader( handle );
					const string nodeName = name + ":" + handle.string();

					NSICreate(
						context,
						nodeName.c_str(),
						"shader",
						0, nullptr
					);

					m_handles.emplace_back( context, nodeName, ownership );

					// Set parameters

					ParameterList parameterList;
					std::string shaderFileName = g_shaderSearchPathCache.get( shader->getName() );
					parameterList.add( "shaderfilename", shaderFileName );

					for( const auto &parameter : shader->parameters() )
					{
						parameterList.add( parameter.first.c_str(), parameter.second.get() );
					}

					NSISetAttribute(
						context,
						nodeName.c_str(),
						parameterList.size(),
						parameterList.data()
					);

					// Make connections

					for( const auto &c : shaderNetwork->inputConnections( handle ) )
					{
						const string sourceHandle = name + ":" + c.source.shader.string();
						NSIConnect(
							context,
							sourceHandle.c_str(),
							c.source.name.c_str(),
							nodeName.c_str(),
							c.destination.name.c_str(),
							0, nullptr
						);
					}
				}
			);

		}

		const DelightHandle &handle() const
		{
			return m_handles.back();
		}

	private :

		std::vector<DelightHandle> m_handles;

};

IE_CORE_DECLAREPTR( DelightShader )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ShaderCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class ShaderCache : public IECore::RefCounted
{

	public :

		ShaderCache( NSIContext_t context, DelightHandle::Ownership ownership )
			:	m_context( context ), m_ownership( ownership )
		{
		}

		// Can be called concurrently with other get() calls.
		DelightShaderPtr get( const IECoreScene::ShaderNetwork *shader, const IECore::CompoundObject *attributes )
		{
			IECore::MurmurHash h;
			IECore::MurmurHash hSubst;
			if( shader )
			{
				h = shader->Object::hash();
				if( attributes )
				{
					shader->hashSubstitutions( attributes, hSubst );
					h.append( hSubst );
				}
			}

			Cache::accessor a;
			m_cache.insert( a, h );
			if( !a->second )
			{
				if( shader )
				{
					if( hSubst != IECore::MurmurHash() )
					{
						IECoreScene::ShaderNetworkPtr substitutedShader = shader->copy();
						substitutedShader->applySubstitutions( attributes );
						a->second = new DelightShader( m_context, substitutedShader.get(), m_ownership );
					}
					else
					{
						a->second = new DelightShader( m_context, shader, m_ownership );
					}
				}
				else
				{
					ShaderNetworkPtr defaultSurfaceNetwork = new ShaderNetwork;
					/// \todo Use a shader that comes with 3delight, and provide
					/// the expected "defaultsurface" facing ratio shading. The
					/// closest available at present is the samplerInfo shader, but
					/// that spews errors about a missing "mayaCamera" coordinate
					/// system.
					ShaderPtr defaultSurfaceShader = new Shader( "Surface/Constant", "surface" );
					defaultSurfaceNetwork->addShader( "surface", std::move( defaultSurfaceShader ) );
					defaultSurfaceNetwork->setOutput( { "surface" } );
					a->second = new DelightShader( m_context, defaultSurfaceNetwork.get(), m_ownership );
				}
			}
			return a->second;
		}

		DelightShaderPtr defaultSurface()
		{
			return get( nullptr, nullptr );
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			vector<IECore::MurmurHash> toErase;
			for( Cache::iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second->refCount() == 1 )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// shader.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_cache.erase( *it );
			}
		}

	private :

		NSIContext_t m_context;
		DelightHandle::Ownership m_ownership;

		using Cache = tbb::concurrent_hash_map<IECore::MurmurHash, DelightShaderPtr>;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( ShaderCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// DelightAttributes
//////////////////////////////////////////////////////////////////////////

namespace
{

// List of attributes where we look for an OSL shader, in order of priority.
// Although 3delight only really has surface shaders (lights are just emissive
// surfaces), we support "light" attributes as well for compatibility with
// other renderers and some specific workflows in Gaffer.
std::array<IECore::InternedString, 4> g_shaderAttributeNames = { {
	"osl:light",
	"light",
	"osl:surface",
	"surface",
} };

IECore::InternedString g_setsAttributeName( "sets" );

class DelightAttributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		DelightAttributes( NSIContext_t context, const IECore::CompoundObject *attributes, ShaderCache *shaderCache, DelightHandle::Ownership ownership )
			:	m_handle( context, "attributes:" + attributes->Object::hash().toString(), ownership, "attributes", {} )
		{
			for( const auto &name : g_shaderAttributeNames )
			{
				if( const Object *o = attributes->member<const Object>( name ) )
				{
					if( const ShaderNetwork *shader = reportedCast<const ShaderNetwork>( o, "attribute", name ) )
					{
						m_shader = shaderCache->get( shader, attributes );
					}
					break;
				}
			}

			ParameterList params;
			for( const auto &m : attributes->members() )
			{
				if( m.first == g_setsAttributeName )
				{
					if( const InternedStringVectorData *d = reportedCast<const InternedStringVectorData>( m.second.get(), "attribute", m.first ) )
					{
						if( d->readable().size() )
						{
							msg( Msg::Warning, "DelightRenderer", "Attribute \"sets\" not supported" );
						}
					}
				}
				else if( boost::starts_with( m.first.string(), "dl:" ) )
				{
					if( const Data *d = reportedCast<const IECore::Data>( m.second.get(), "attribute", m.first ) )
					{
						params.add( m.first.c_str() + 3, d );
					}
				}
				else if( boost::starts_with( m.first.string(), "render:" ) )
				{
					msg( Msg::Warning, "DelightRenderer", boost::format( "Render attribute \"%s\" not supported" ) % m.first.string() );
				}
				else if( boost::starts_with( m.first.string(), "user:" ) )
				{
					msg( Msg::Warning, "DelightRenderer", boost::format( "User attribute \"%s\" not supported" ) % m.first.string() );
				}
				else if( boost::contains( m.first.string(), ":" ) )
				{
					// Attribute for another renderer - ignore
				}
				else
				{
					msg( Msg::Warning, "DelightRenderer", boost::format( "Attribute \"%s\" not supported" ) % m.first.string() );
				}
			}

			NSISetAttribute( m_handle.context(), m_handle.name(), params.size(), params.data() );

			if( !m_shader )
			{
				m_shader = shaderCache->defaultSurface();
			}

			NSIConnect(
				context,
				m_shader->handle().name(), "",
				m_handle.name(), "surfaceshader",
				0, nullptr
			);
		}

		const DelightHandle &handle() const
		{
			return m_handle;
		}

	private :

		DelightHandle m_handle;
		ConstDelightShaderPtr m_shader;

};

IE_CORE_DECLAREPTR( DelightAttributes )

} // namespace

//////////////////////////////////////////////////////////////////////////
// AttributesCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class AttributesCache : public IECore::RefCounted
{

	public :

		AttributesCache( NSIContext_t context, DelightHandle::Ownership ownership )
			:	m_context( context ), m_ownership( ownership ), m_shaderCache( new ShaderCache( context, ownership ) )
		{
		}

		// Can be called concurrently with other get() calls.
		DelightAttributesPtr get( const IECore::CompoundObject *attributes )
		{
			Cache::accessor a;
			m_cache.insert( a, attributes->Object::hash() );
			if( !a->second )
			{
				a->second = new DelightAttributes( m_context, attributes, m_shaderCache.get(), m_ownership );
			}
			return a->second;
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			vector<IECore::MurmurHash> toErase;
			for( Cache::iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second->refCount() == 1 )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// attributes.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_cache.erase( *it );
			}

			m_shaderCache->clearUnused();
		}

	private :

		NSIContext_t m_context;
		DelightHandle::Ownership m_ownership;

		ShaderCachePtr m_shaderCache;

		using Cache = tbb::concurrent_hash_map<IECore::MurmurHash, DelightAttributesPtr>;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( AttributesCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// InstanceCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class InstanceCache : public IECore::RefCounted
{

	public :

		InstanceCache( NSIContext_t context, DelightHandle::Ownership ownership )
			:	m_context( context ), m_ownership( ownership )
		{
		}

		// Can be called concurrently with other get() calls.
		DelightHandleSharedPtr get( const IECore::Object *object )
		{
			const IECore::MurmurHash hash = object->Object::hash();

			Cache::accessor a;
			m_cache.insert( a, hash );
			if( !a->second )
			{
				const std::string &name = "instance:" + hash.toString();
				if( NodeAlgo::convert( object, m_context, name.c_str() ) )
				{
					a->second = make_shared<DelightHandle>( m_context, name, m_ownership );
				}
				else
				{
					a->second = nullptr;
				}
			}

			return a->second;
		}

		// Can be called concurrently with other get() calls.
		DelightHandleSharedPtr get( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times )
		{
			IECore::MurmurHash hash;
			for( std::vector<const IECore::Object *>::const_iterator it = samples.begin(), eIt = samples.end(); it != eIt; ++it )
			{
				(*it)->hash( hash );
			}
			for( std::vector<float>::const_iterator it = times.begin(), eIt = times.end(); it != eIt; ++it )
			{
				hash.append( *it );
			}

			Cache::accessor a;
			m_cache.insert( a, hash );

			if( !a->second )
			{
				const std::string &name = "instance:" + hash.toString();
				if( NodeAlgo::convert( samples, times, m_context, name.c_str() ) )
				{
					a->second = make_shared<DelightHandle>( m_context, name, m_ownership );
				}
				else
				{
					a->second = nullptr;
				}
			}

			return a->second;
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			vector<IECore::MurmurHash> toErase;
			for( Cache::iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second.unique() )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// instance.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_cache.erase( *it );
			}
		}

	private :

		NSIContext_t m_context;
		DelightHandle::Ownership m_ownership;

		using Cache = tbb::concurrent_hash_map<IECore::MurmurHash, DelightHandleSharedPtr>;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( InstanceCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// DelightObject
//////////////////////////////////////////////////////////////////////////

namespace
{

class DelightObject : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		DelightObject( NSIContext_t context, const std::string &name, DelightHandleSharedPtr instance, DelightHandle::Ownership ownership )
			:	m_transformHandle( context, name, ownership, "transform", {} ), m_instance( instance ), m_haveTransform( false )
		{
			NSIConnect(
				m_transformHandle.context(),
				m_instance->name(), "",
				m_transformHandle.name(), "objects",
				0, nullptr
			);

			NSIConnect(
				m_transformHandle.context(),
				m_transformHandle.name(), "",
				NSI_SCENE_ROOT, "objects",
				0, nullptr
			);
		}

		void transform( const Imath::M44f &transform ) override
		{
			if( transform == M44f() && !m_haveTransform )
			{
				return;
			}

			M44d m( transform );
			NSIParam_t param = {
				"transformationmatrix",
				m.getValue(),
				NSITypeDoubleMatrix,
				0, 1, // array length, count
				0 // flags
			};
			NSISetAttribute( m_transformHandle.context(), m_transformHandle.name(), 1, &param );

			m_haveTransform = true;
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			if( m_haveTransform )
			{
				NSIDeleteAttribute( m_transformHandle.context(), m_transformHandle.name(), "transformationmatrix" );
			}

			for( size_t i = 0, e = samples.size(); i < e; ++i )
			{
				M44d m( samples[i] );
				NSIParam_t param = {
					"transformationmatrix",
					m.getValue(),
					NSITypeDoubleMatrix,
					0, 1, // array length, count
					0 // flags
				};
				NSISetAttributeAtTime( m_transformHandle.context(), m_transformHandle.name(), times[i], 1, &param );
			}

			m_haveTransform = true;
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			if( m_attributes )
			{
				if( attributes == m_attributes )
				{
					return true;
				}

				NSIDisconnect(
					m_transformHandle.context(),
					m_attributes->handle().name(), "",
					m_transformHandle.name(), "geometryattributes"
				);
			}

			m_attributes = static_cast<const DelightAttributes *>( attributes );
			NSIConnect(
				m_transformHandle.context(),
				m_attributes->handle().name(), "",
				m_transformHandle.name(), "geometryattributes",
				0, nullptr

			);
			return true;
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
		}

		void assignID( uint32_t id ) override
		{
			/// \todo Implement
		}

	private :

		const DelightHandle m_transformHandle;
		// We keep a reference to the instance and attributes so that they
		// remain alive for at least as long as the object does.
		ConstDelightAttributesPtr m_attributes;
		DelightHandleSharedPtr m_instance;

		bool m_haveTransform;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// DelightRenderer
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString g_frameOptionName( "frame" );
IECore::InternedString g_cameraOptionName( "camera" );
IECore::InternedString g_sampleMotionOptionName( "sampleMotion" );
IECore::InternedString g_oversamplingOptionName( "dl:oversampling" );
const char *g_screenHandle = "ieCoreDelight:defaultScreen";

IE_CORE_FORWARDDECLARE( DelightRenderer )

class DelightRenderer final : public IECoreScenePreview::Renderer
{

	public :

		DelightRenderer( RenderType renderType, const std::string &fileName, const IECore::MessageHandlerPtr &messageHandler )
			:	m_renderType( renderType ), m_frame( 1 ), m_oversampling( 9 ), m_messageHandler( messageHandler )
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			vector<NSIParam_t> params;

			const char *apistream = "apistream";
			const char *fileNamePtr = fileName.c_str();
			if( renderType == SceneDescription )
			{
				params = {
					{ "type", &apistream, NSITypeString, 0, 1, 0 },
					{ "streamfilename", &fileNamePtr, NSITypeString , 0, 1, 0 }
				};
			}

			if( messageHandler )
			{
				void *handler = reinterpret_cast<void *>( &DelightRenderer::nsiErrorHandler );
				void *data = this;
				params.push_back( { "errorhandler",	&handler, NSITypePointer, 0, 1, 0 } );
				params.push_back( { "errorhandlerdata",	&data, NSITypePointer, 0, 1, 0 } );
			}

			m_context = NSIBegin( params.size(), params.data() );
			m_instanceCache = new InstanceCache( m_context, ownership() );
			m_attributesCache = new AttributesCache( m_context, ownership() );

			NSICreate( m_context, g_screenHandle, "screen", 0, nullptr );
		}

		~DelightRenderer() override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			// Delete nodes we own before we destroy context
			stop();
			m_attributesCache.reset();
			m_instanceCache.reset();
			m_outputs.clear();
			m_defaultCamera.reset();
			NSIEnd( m_context );
		}

		IECore::InternedString name() const override
		{
			return "3Delight";
		}

		void option( const IECore::InternedString &name, const IECore::Object *value ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			if( name == g_frameOptionName )
			{
				m_frame = 1;
				if( value )
				{
					if( const IntData *d = reportedCast<const IntData>( value, "option", name ) )
					{
						m_frame = d->readable();
					}
				}
			}
			else if( name == g_cameraOptionName )
			{
				if( value )
				{
					if( const StringData *d = reportedCast<const StringData>( value, "option", name ) )
					{
						if( m_camera != d->readable() )
						{
							stop();
							m_camera = d->readable();
						}
					}
					else
					{
						m_camera = "";
					}
				}
				else
				{
					m_camera = "";
				}
			}
			else if( name == g_oversamplingOptionName )
			{
				if( value )
				{
					if( const IntData *d = reportedCast<const IntData>( value, "option", name ) )
					{
						if( m_oversampling != d->readable() )
						{
							stop();
							m_oversampling = d->readable();
						}
					}
					else
					{
						m_oversampling = 9;
					}
				}
				else
				{
					m_oversampling = 9;
				}
			}
			else if( boost::starts_with( name.string(), "dl:" ) )
			{
				if( value )
				{
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						ParameterList params;
						params.add( name.c_str() + 3, data );
						NSISetAttribute( m_context, NSI_SCENE_GLOBAL, params.size(), params.data() );
					}
					else
					{
						NSIDeleteAttribute( m_context, NSI_SCENE_GLOBAL, name.c_str() + 3 );
					}
				}
				else
				{
					NSIDeleteAttribute( m_context, NSI_SCENE_GLOBAL, name.c_str() + 3 );
				}
			}
			else if( boost::starts_with( name.string(), "user:" ) )
			{
				msg( Msg::Warning, "DelightRenderer::option", boost::format( "User option \"%s\" not supported" ) % name.string() );
			}
			else if( boost::contains( name.c_str(), ":" ) )
			{
				// Ignore options prefixed for some other renderer.
			}
			else
			{
				IECore::msg( IECore::Msg::Warning, "DelightRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
			}
		}

		void output( const IECore::InternedString &name, const Output *output ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			// 3Delight crashes if we don't stop the render before
			// modifying the output chain.
			stop();
			m_outputs.erase( name );
			if( !output )
			{
				return;
			}

			DelightOutputPtr o = new DelightOutput( m_context, name, output, ownership() );
			m_outputs[name] = o;

			NSIConnect(
				m_context,
				o->layerHandle().name(), "",
				g_screenHandle, "outputlayers",
				0, nullptr
			);
		}

		Renderer::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			return m_attributesCache->get( attributes );
		}

		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			const string objectHandle = "camera:" + name;
			if( !NodeAlgo::convert( camera, m_context, objectHandle.c_str() ) )
			{
				return nullptr;
			}

			// Store the camera for later use in updateCamera().
			{
				tbb::spin_mutex::scoped_lock lock( m_camerasMutex );
				m_cameras[objectHandle] = camera;
			}

			DelightHandleSharedPtr cameraHandle(
				new DelightHandle( m_context, objectHandle.c_str(), ownership() ),
				// 3delight doesn't allow edits to cameras or outputs while the
				// render is running, so we must use a custom deleter to stop
				// the render just before the camera is deleted. This also allows
				// us to remove the camera from m_cameras.
				boost::bind( &DelightRenderer::cameraDeleter, DelightRendererPtr( this ), ::_1 )
			);

			ObjectInterfacePtr result = new DelightObject(
				m_context,
				name,
				cameraHandle,
				ownership()
			);
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			return this->object( name, object, attributes );
		}

		ObjectInterfacePtr lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			return nullptr;
		}

		Renderer::ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			if( !object )
			{
				return nullptr;
			}

			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			DelightHandleSharedPtr instance = m_instanceCache->get( object );
			if( !instance )
			{
				return nullptr;
			}

			ObjectInterfacePtr result = new DelightObject( m_context, name, instance, ownership() );
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			DelightHandleSharedPtr instance = m_instanceCache->get( samples, times );
			if( !instance )
			{
				return nullptr;
			}

			ObjectInterfacePtr result = new DelightObject( m_context, name, instance, ownership() );
			result->attributes( attributes );
			return result;
		}

		void render() override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			m_instanceCache->clearUnused();
			m_attributesCache->clearUnused();

			if( m_rendering )
			{
				const char *synchronize = "synchronize";
				vector<NSIParam_t> params = {
					{ "action", &synchronize, NSITypeString, 0, 1, 0 }
				};
				NSIRenderControl(
					m_context,
					params.size(), params.data()
				);
				return;
			}

			updateCamera();

			const int one = 1;
			const char *start = "start";
			vector<NSIParam_t> params = {
				{ "action", &start, NSITypeString, 0, 1, 0 },
				{ "frame", &m_frame, NSITypeInteger, 0, 1, 0 }
			};

			if( m_renderType == Interactive )
			{
				params.push_back( { "interactive", &one, NSITypeInteger, 0, 1, 0 } );
			}

			NSIRenderControl(
				m_context,
				params.size(), params.data()
			);

			m_rendering = true;

			if( m_renderType == Interactive )
			{
				return;
			}

			const char *wait = "wait";
			params = {
				{ "action", &wait, NSITypeString, 0, 1, 0 }
			};

			NSIRenderControl(
				m_context,
				params.size(), params.data()
			);

			m_rendering = false;
		}

		void pause() override
		{
			// In theory we could use NSIRenderControl "suspend"
			// here, but despite documenting it, 3delight does not
			// support it. Instead we let 3delight waste cpu time
			// while we make our edits.
		}

	private :

		DelightHandle::Ownership ownership() const
		{
			return m_renderType == Interactive ? DelightHandle::Owned : DelightHandle::Unowned;
		}

		void stop()
		{
			if( !m_rendering )
			{
				return;
			}

			const char *stop = "stop";
			ParameterList params = {
				{ "action", &stop, NSITypeString, 0, 1, 0 }
			};

			NSIRenderControl(
				m_context,
				params.size(), params.data()
			);

			m_rendering = false;
		}

		void updateCamera()
		{
			// The NSI handle for the camera that we've been told to use.
			std::string cameraHandle = "camera:" + m_camera;

			// If we're in an interactive render, then disconnect the
			// screen from any secondary cameras.
			if( m_renderType == Interactive )
			{
				for( auto &camera : m_cameras )
				{
					if( camera.first != cameraHandle )
					{
						NSIDisconnect(
							m_context,
							g_screenHandle, "",
							camera.first.c_str(), "screens"
						);
					}
				}
			}

			// Check that the camera we want to use exists,
			// and if not, create a default one.

			ConstCameraPtr camera;
			const auto cameraIt = m_cameras.find( cameraHandle );
			if( cameraIt == m_cameras.end() )
			{
				if( !m_camera.empty() )
				{
					IECore::msg(
						IECore::Msg::Warning, "DelightRenderer",
						boost::format( "Camera \"%s\" does not exist" ) % m_camera
					);
				}

				CameraPtr defaultCamera = new Camera;
				camera = defaultCamera;

				cameraHandle = "ieCoreDelight:defaultCamera";
				NodeAlgo::convert( defaultCamera.get(), m_context, cameraHandle.c_str() );

				m_defaultCamera = DelightHandle( m_context, cameraHandle, ownership() );

				NSIConnect(
					m_context,
					cameraHandle.c_str(), "",
					NSI_SCENE_ROOT, "objects",
					0, nullptr
				);
			}
			else
			{
				camera = cameraIt->second;
				m_defaultCamera.reset();
			}

			// Connect the camera to the screen

			NSIConnect(
				m_context,
				g_screenHandle, "",
				cameraHandle.c_str(), "screens",
				0, nullptr
			);

			// Update the screen

			ParameterList screeenParameters = {
				{ "oversampling", &m_oversampling, NSITypeInteger, 0, 1, 0 }
			};

			const V2i &resolution = camera->getResolution();
			screeenParameters.add( { "resolution", resolution.getValue(), NSITypeInteger, 2, 1, NSIParamIsArray } );

			Box2i renderRegion = camera->renderRegion();

			// I can't find any support in 3delight for overscan - and if crop goes outside 0 - 1,
			// it ignores crop.  So we clamp it.
			renderRegion.min.x = std::max( 0, renderRegion.min.x );
			renderRegion.max.x = std::min( resolution.x, renderRegion.max.x );
			renderRegion.min.y = std::max( 0, renderRegion.min.y );
			renderRegion.max.y = std::min( resolution.y, renderRegion.max.y );

			if(
				renderRegion.min.x >= renderRegion.max.x ||
				renderRegion.min.y >= renderRegion.max.y
			)
			{
				// 3delight doesn't support an empty crop, so just render as little as possible
				renderRegion = Box2i( V2i( 0 ), V2i( 1 ) );
			}

			const Box2f crop(
				V2f(
					renderRegion.min.x / float( resolution.x ),
					1 - renderRegion.max.y / float( resolution.y )
				),
				V2f(
					renderRegion.max.x / float( resolution.x ),
					1 - renderRegion.min.y / float( resolution.y )
				)
			);
			screeenParameters.add( { "crop", crop.min.getValue(), NSITypeFloat, 2, 2, NSIParamIsArray } );

			const Box2f &screenWindow = camera->frustum();
			const Box2d screenWindowD( screenWindow.min, screenWindow.max );
			screeenParameters.add( { "screenwindow", screenWindowD.min.getValue(), NSITypeDouble, 2, 2, NSIParamIsArray } );

			const float pixelAspectRatio = camera->getPixelAspectRatio();
			screeenParameters.add( { "pixelaspectratio", &pixelAspectRatio, NSITypeFloat, 0, 1, 0 } );

			NSISetAttribute( m_context, g_screenHandle, screeenParameters.size(), screeenParameters.data() );

			/// \todo Support overscan somehow ( this would currently require modifying the screenwindow
			/// and explicitly overriding the display window metadata on the output image? )

		}

		void cameraDeleter( const DelightHandle *handle )
		{
			if( handle->ownership() != DelightHandle::Unowned )
			{
				stop();
				tbb::spin_mutex::scoped_lock lock( m_camerasMutex );
				m_cameras.erase( handle->name() );
			}
			delete handle;
		}

		NSIContext_t m_context;
		RenderType m_renderType;

		int m_frame;
		string m_camera;
		int m_oversampling;

		bool m_rendering = false;

		InstanceCachePtr m_instanceCache;
		AttributesCachePtr m_attributesCache;

		unordered_map<InternedString, ConstDelightOutputPtr> m_outputs;

		using CameraMap = unordered_map<string, ConstCameraPtr>;
		CameraMap m_cameras;
		tbb::spin_mutex m_camerasMutex;

		DelightHandle m_screen;
		DelightHandle m_defaultCamera;

		IECore::MessageHandlerPtr m_messageHandler;
		static const std::vector<IECore::MessageHandler::Level> g_ieMsgLevels;

		static void nsiErrorHandler( void *userdata, int level, int code, const char *message )
		{
			static_cast<DelightRenderer *>(userdata)->m_messageHandler->handle(
				g_ieMsgLevels[ min( level, 3 ) ],
				"3Delight",
				message
			);
		}

		// Registration with factory

		static Renderer::TypeDescription<DelightRenderer> g_typeDescription;

};

const std::vector<IECore::MessageHandler::Level> DelightRenderer::g_ieMsgLevels = {
	IECore::MessageHandler::Level::Debug,
	IECore::MessageHandler::Level::Info,
	IECore::MessageHandler::Level::Warning,
	IECore::MessageHandler::Level::Error
};

IECoreScenePreview::Renderer::TypeDescription<DelightRenderer> DelightRenderer::g_typeDescription( "3Delight" );

} // namespace
