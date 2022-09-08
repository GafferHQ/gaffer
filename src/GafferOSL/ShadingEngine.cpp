//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#include "GafferOSL/ShadingEngine.h"

#include "GafferOSL/OSLShader.h"

#include "GafferImage/FilterAlgo.h"
#include "GafferImage/Sampler.h"

#include "Gaffer/Context.h"

#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECoreImage/OpenImageIOAlgo.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/VectorTypedData.h"

#include "OSL/genclosure.h"
#include "OSL/oslclosure.h"
#include "OSL/oslexec.h"
#include "OSL/oslversion.h"

#include "OpenImageIO/ustring.h"

#include "boost/algorithm/string/classification.hpp"
#include "boost/algorithm/string/join.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/split.hpp"
#include "boost/container/flat_map.hpp"
#include "boost/unordered_map.hpp"

#include "tbb/enumerable_thread_specific.h"
#include "tbb/parallel_for.h"
#include "tbb/spin_mutex.h"
#include "tbb/spin_rw_mutex.h"

#include <limits>
#include <unordered_set>

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace OSL;
using namespace GafferOSL;


// keyword matrix parameter macro. reference: OSL/genclosure.h
#define CLOSURE_MATRIX_KEYPARAM(st, fld, key) \
	{ TypeDesc::TypeMatrix44, (int)reckless_offsetof(st, fld), key, fieldsize(st, fld) }

//////////////////////////////////////////////////////////////////////////
// Conversion utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

template<typename T>
struct TypeDescFromType
{
	static TypeDesc typeDesc()
	{
		return TypeDesc( OIIO::BaseTypeFromC<T>::value );
	}
};

template<>
struct TypeDescFromType<Color3f>
{
	static TypeDesc typeDesc()
	{
		return TypeDesc(
			OIIO::BaseTypeFromC<Color3f::BaseType>::value,
			TypeDesc::VEC3,
			TypeDesc::COLOR
		);
	}
};


// required to ensure we construct M44f in vectorDataFromTypeDesc correctly
template<typename T>
void initialiser( T &v )
{
	v = T( 0 );
}

// template specialisation for the M44f case
template<>
void initialiser( Imath::M44f &v )
{
	v = Imath::M44f();
}

void initialiser( std::string& v )
{
	v = std::string();
}


template<typename T>
typename T::Ptr vectorDataFromTypeDesc( TypeDesc type, void *&basePointer )
{
	typename T::Ptr result = new T();
	typename T::ValueType::value_type initialValue;
	initialiser( initialValue );
	result->writable().resize( type.arraylen, initialValue );
	basePointer = result->baseWritable();
	return result;
}

template<typename T>
typename T::Ptr geometricVectorDataFromTypeDesc( TypeDesc type, void *&basePointer )
{
	typename T::Ptr result = vectorDataFromTypeDesc<T>( type, basePointer );
	result->setInterpretation( IECoreImage::OpenImageIOAlgo::geometricInterpretation( ( (TypeDesc::VECSEMANTICS)type.vecsemantics ) ) );
	return result;
}

DataPtr dataFromTypeDesc( TypeDesc type, void *&basePointer )
{
	if( type.arraylen )
	{
		if( type.aggregate == TypeDesc::SCALAR )
		{
			switch( type.basetype )
			{
				case TypeDesc::INT :
					return vectorDataFromTypeDesc<IntVectorData>( type, basePointer );
				case TypeDesc::FLOAT :
					return vectorDataFromTypeDesc<FloatVectorData>( type, basePointer );
				case TypeDesc::STRING :
					return vectorDataFromTypeDesc<StringVectorData>( type, basePointer );
			}
		}
		else if( type.aggregate == TypeDesc::VEC2 )
		{
			switch( type.basetype )
			{
				case TypeDesc::INT :
					return geometricVectorDataFromTypeDesc<V2iVectorData>( type, basePointer );
				case TypeDesc::FLOAT :
					return geometricVectorDataFromTypeDesc<V2fVectorData>( type, basePointer );
			}
		}
		else if( type.aggregate == TypeDesc::VEC3 )
		{
			switch( type.basetype )
			{
				case TypeDesc::INT :
					return geometricVectorDataFromTypeDesc<V3iVectorData>( type, basePointer );
				case TypeDesc::FLOAT :
					if( type.vecsemantics == TypeDesc::COLOR )
					{
						return vectorDataFromTypeDesc<Color3fVectorData>( type, basePointer );
					}
					return geometricVectorDataFromTypeDesc<V3fVectorData>( type, basePointer );
			}
		}
		else if ( type.aggregate == TypeDesc::MATRIX44 )
		{
			if ( type.basetype == TypeDesc::FLOAT )
			{
				return vectorDataFromTypeDesc<M44fVectorData>( type, basePointer );
			}
		}
	}

	return nullptr;
}

// Equivalent to `OSL::ShadingSystem:convert_value()`, but with support for
// additional conversions.
bool convertValue( void *dst, TypeDesc dstType, const void *src, TypeDesc srcType )
{
	if( srcType.aggregate == TypeDesc::VEC2 )
	{
		// OSL doesn't know how to convert these, but it knows how to convert
		// float[2], which has an identical layout.
		srcType.aggregate = TypeDesc::SCALAR;
		srcType.arraylen = 2;
	}

	if(
		( dstType.aggregate == TypeDesc::VEC2 || dstType.aggregate == TypeDesc::VEC3 ) &&
		srcType.aggregate > dstType.aggregate && srcType.aggregate <= TypeDesc::VEC4
	)
	{
		// OSL doesn't know how to do truncating vector conversions, so we
		// encourage it by truncating srcType.
		srcType.aggregate = dstType.aggregate;
	}

	if( ShadingSystem::convert_value( dst, dstType, src, srcType ) )
	{
		// OSL converted successfully
		return true;
	}
	else if( srcType.basetype == dstType.basetype && srcType.aggregate == dstType.arraylen )
	{
		// Convert an aggregate (vec2, vec3, vec4, matrix33, matrix44) to an array with the same base type.
		// Note that the aggregate enum value is the number of elements.
		memcpy( dst, src, dstType.size() );
		return true;
	}
	else if( srcType.basetype == TypeDesc::DOUBLE && srcType.aggregate == TypeDesc::SCALAR )
	{
		double doubleValue = *reinterpret_cast<const double *>( src );
		if( dstType == TypeDesc::FLOAT )
		{
			*((float*)dst) = static_cast<float>( doubleValue );
			return true;
		}
		else if( dstType == TypeDesc::INT )
		{
			*((int*)dst) = static_cast<int>( doubleValue );
			return true;
		}
		return false;
	}

	return false;
}

// Addresses within this buffer are used for texture handle pointer that correspond to Gaffer textures.  The
// data within the buffer isn't used - just the index within the buffer indicates which Gaffer texture is used.
const std::vector< char > g_gafferTextureIndicesBuffer( 1000 );
tbb::spin_mutex g_gafferTextureIndicesMutex;
const container::flat_map<ustring, int> *g_gafferTextureIndices;

// TODO - this mapping is probably kinda hacky - should we pass the actual filter as part of the texture name instead?
std::vector<const OIIO::Filter2D*> setupFiltersForInterpModes()
{
	std::vector<const OIIO::Filter2D*> result( TextureOpt::InterpSmartBicubic ); // Currently SmartBicubic is max value
	result[ TextureOpt::InterpBilinear ] = GafferImage::FilterAlgo::acquireFilter( "box" );
	result[ TextureOpt::InterpBicubic ] = GafferImage::FilterAlgo::acquireFilter( "disk" );
	result[ TextureOpt::InterpSmartBicubic ] = GafferImage::FilterAlgo::acquireFilter( "sharp-gaussian" );
	// Note that for TextureOpt::InterpClosest we go straight to Sampler instead of using a filter at all
	return result;
}
const std::vector<const OIIO::Filter2D*> g_filtersForInterpModes = setupFiltersForInterpModes();

} // namespace

//////////////////////////////////////////////////////////////////////////
// RenderState
//////////////////////////////////////////////////////////////////////////

namespace
{

const std::string g_gafferImagePrefix = "gaffer:";
OIIO::ustring gIndex( "shading:index" );
ustring g_contextVariableAttributeScope( "gaffer:context" );

struct ChannelsRequested
{
	ChannelsRequested( const std::string &gafferTextureName, const ShadingEngine::ImagePlugs &imagePlugs )
	{
		imagePlug = nullptr;

		vector<string> nameTokens;
		boost::split( nameTokens, gafferTextureName.substr( g_gafferImagePrefix.size() ), boost::is_any_of(".") );
		const auto imagePlugIter = imagePlugs.find( nameTokens[0] );
		if( imagePlugIter != imagePlugs.end() )
		{
			imagePlug = imagePlugIter->second;
			ConstStringVectorDataPtr channelNamesData = imagePlug->channelNames( &GafferImage::ImagePlug::defaultViewName ); // TODO view
			const std::vector< std::string > &channelNames = channelNamesData->readable();

			std::string channelOrLayer = boost::join( std::vector< string >( nameTokens.begin() + 1, nameTokens.end() ), "." );
			bool found = false;
			if( std::find( channelNames.begin(), channelNames.end(), channelOrLayer ) != channelNames.end() )
			{
				channels[0] = channels[1] = channels[2] = channels[3] = channelOrLayer;
				found = true;
			}
			else
			{
				for( int i = 0; i < 4; i++ )
				{
					std::string channel = ( channelOrLayer.size() ? channelOrLayer + "." : "" ) + std::string( 1, "RGBA"[i] );
					if( std::find( channelNames.begin(), channelNames.end(), channel ) != channelNames.end() )
					{
						channels[i] = channel;
						found = true;
					}
				}
			}

			if( !found )
			{
				throw IECore::Exception( "Cannot access Gaffer image, cannot find channels matching: " + channelOrLayer + ", available channels are: " + boost::algorithm::join( channelNames, "," ) );
			}
		}
		else
		{
			throw IECore::Exception( "Cannot access Gaffer image, cannot find image plug: " + nameTokens[0] );
		}
	}

	const GafferImage::ImagePlug* imagePlug;
	std::string channels[4];
};

class RenderState
{

	public :

		RenderState(
			const IECore::CompoundData *shadingPoints,
			const ShadingEngine::Transforms &transforms,
			const std::vector<InternedString> &contextVariablesNeeded,
			const Gaffer::Context *context,
			const std::vector< OIIO::ustring > &gafferTexturesRequested,
			const ShadingEngine::ImagePlugs &imagePlugs
		)
		{
			for(
				CompoundDataMap::const_iterator it = shadingPoints->readable().begin(),
				eIt = shadingPoints->readable().end(); it != eIt; ++it
			)
			{
				UserData userData;
				userData.dataView = IECoreImage::OpenImageIOAlgo::DataView( it->second.get(), /* createUStrings = */ true );
				if( userData.dataView.data )
				{
					userData.numValues = std::max( userData.dataView.type.arraylen, 1 );
					if( userData.dataView.type.arraylen )
					{
						// we unarray the TypeDesc so we can use it directly with
						// convertValue() in get_userdata().
						userData.dataView.type.unarray();
					}
					m_userData.insert( make_pair( ustring( it->first.c_str() ), userData ) );
				}
			}

			for( ShadingEngine::Transforms::const_iterator it = transforms.begin(); it != transforms.end(); it++ )
			{
				m_transforms[ OIIO::ustring( it->first.string() ) ] = it->second;
			}

			for( const auto &name : contextVariablesNeeded )
			{
				DataPtr contextEntryData = context->getAsData( name.string(), nullptr );
				m_contextVariables.insert(
					make_pair(
						ustring( name.c_str() ),
						ContextData{
							IECoreImage::OpenImageIOAlgo::DataView( contextEntryData.get(), /* createUStrings = */ true ),
							contextEntryData
						}
					)
				);
			}

			m_gafferTextures.reserve( gafferTexturesRequested.size() );
			Box2i infiniteBound;
			infiniteBound.makeInfinite();
			infiniteBound.min += V2i( 1 ); // Make sure overscan doesn't trigger wraparound
			infiniteBound.max -= V2i( 1 );

			for( const auto &textureName : gafferTexturesRequested )
			{
				size_t textureIndex = m_gafferTextures.size();
				m_gafferTextures.resize( textureIndex + 1 );

				// TODO - should this throw, or should we handle it not matching anything?
				ChannelsRequested cr( textureName.string(), imagePlugs );

				Box2i display = cr.imagePlug->format( &GafferImage::ImagePlug::defaultViewName ).getDisplayWindow();
				m_gafferTextures[ textureIndex ].dataWindowSize = display.size();
				for( int i = 0; i < 4; i++ )
				{
					if( cr.channels[i] != "" )
					{
						// Initialize Sampler
						m_gafferTextures[ textureIndex ].channels[i].emplace( cr.imagePlug, cr.channels[i], infiniteBound, GafferImage::Sampler::BoundingMode::Clamp, true ); // TODO select view TODO choose clamp
					}
				}
			}
		}

		bool contextVariable( ustring name, TypeDesc type, void *value ) const
		{
			auto it = m_contextVariables.find( name );
			if( it == m_contextVariables.end() )
			{
				return false;
			}

			return ShadingSystem::convert_value( value, type, it->second.dataView.data, it->second.dataView.type );
		}

		bool userData( size_t pointIndex, ustring name, TypeDesc type, void *value ) const
		{
			if( name == gIndex )
			{
				// if a 4 byte type has been requested then ensure we fit and cast to narrower type
				// this way f32 reads of shading:index will succeed.
				if( type.size() == sizeof( int ) && pointIndex <= ( (size_t) std::numeric_limits<int>::max() ) )
				{
					int v = (int) pointIndex;
					return ShadingSystem::convert_value( value, type, &v, OIIO::TypeDesc( OIIO::TypeDesc::INT32 ) );
				}
				else
				{
					// OSL language doesn't define UINT64 type so we'll probably never enter this branch.
					return ShadingSystem::convert_value( value, type, &pointIndex, OIIO::TypeDesc( OIIO::TypeDesc::UINT64 ) );
				}
			}

			auto it = m_userData.find( name );
			if( it == m_userData.end() )
			{
				return false;
			}

			const char *src = static_cast<const char *>( it->second.dataView.data );
			src += std::min( pointIndex, it->second.numValues - 1 ) * it->second.dataView.type.elementsize();

			return convertValue( value, type, src,  it->second.dataView.type );
		}

		bool matrixToObject( OIIO::ustring name, Imath::M44f &result ) const
		{
			RenderStateTransforms::const_iterator i = m_transforms.find( name );
			if( i != m_transforms.end() )
			{
				result = i->second.toObjectSpace;
				return true;
			}
			return false;
		}

		bool matrixFromObject( OIIO::ustring name, Imath::M44f &result ) const
		{
			RenderStateTransforms::const_iterator i = m_transforms.find( name );
			if( i != m_transforms.end() )
			{
				result = i->second.fromObjectSpace;
				return true;
			}
			return false;
		}

		bool texture( size_t gafferTextureIndex,
                          TextureOpt& options, float s,
                          float t, float dsdx, float dtdx, float dsdy,
                          float dtdy, int nchannels, float* result,
                          float* dresultds, float* dresultdt,
                          ustring* errormessage ) const
		{
			if( gafferTextureIndex >= m_gafferTextures.size() )
			{
				throw IECore::Exception( "Internal Gaffer error, out of bound texture index" );
			}
					
			const GafferTextureData &tex = m_gafferTextures[ gafferTextureIndex ];
			// TODO - why is nchannels always 4?  It should be 1 or 3
			// TODO - alpha
			memset( result, 0, sizeof( float ) * nchannels );
			try
			{
				V2f p = V2f( s, t ) * tex.dataWindowSize;
				for( int i = 0; i < nchannels; i++ )
				{
					if( tex.channels[i] )
					{
						// TODO - optimize case where someone accidentally accesses channel as layer?
						/*if( i > 0 && tex.channels[i] == tex.channels[i - 1] )
						{
							result[i] = result[i-1];
						}*/
						if( options.interpmode == TextureOpt::InterpClosest )
						{
							// TODO - default floor is incredibly slow - these two calls are actually quite prominent in profiles
							result[i] = tex.channels[i]->sample( int( floor( p[0] ) ), int( floor( p[1] ) ) );
						}
						else if( dsdx == 0 && dtdx == 0 && dsdy == 0 && dtdy == 0 )
						{
							result[i] = tex.channels[i]->sample( p[0], p[1] );
						}
						else if( ( dsdx == 0 && dtdy == 0 ) || ( dtdx == 0 && dsdy == 0 ) )
						{
							result[i] = GafferImage::FilterAlgo::sampleBox( *tex.channels[i], p,
								( dsdx ? dsdx : dtdx ) * tex.dataWindowSize.x, ( dsdy ? dsdy : dtdy ) * tex.dataWindowSize.y,
								g_filtersForInterpModes[ options.interpmode ], m_scratchMemory
							 );
						}
						else
						{
							// TODO - confirm scaling is correct on non-square image
							result[i] = GafferImage::FilterAlgo::sampleParallelogram( *tex.channels[i], p,
								V2f( dsdx, dtdx ) * tex.dataWindowSize.x, V2f( dsdy, dtdy ) * tex.dataWindowSize.y,
								g_filtersForInterpModes[ options.interpmode ]
							);
						}
					}
				}
			}
			catch( IECore::Cancelled const &c )
			{
				// TODO - figure out why letting this exception through causes std::terminate
			}
			catch( std::exception  const &e )
			{
				msg( Msg::Warning, "ShadingEngine", "Error during Gaffer texture() eval: " + std::string( e.what() ) );
			}

			if( dresultds )
			{
				memset( dresultds, 0, sizeof( float ) * nchannels );
			}

			if( dresultdt )
			{
				memset( dresultds, 0, sizeof( float ) * nchannels );
			}

			return true;
		}

	private :

		using RenderStateTransforms = boost::unordered_map< OIIO::ustring, ShadingEngine::Transform, OIIO::ustringHash>;
		RenderStateTransforms m_transforms;

		struct UserData
		{
			IECoreImage::OpenImageIOAlgo::DataView dataView;
			size_t numValues;
		};

		struct ContextData
		{
			IECoreImage::OpenImageIOAlgo::DataView dataView;
			ConstDataPtr dataStorage;
		};

		struct GafferTextureData
		{
			// TODO - mutable doesn't make sense here, but it kind of would make sense if the stuff that
			// updates during a call to sample() was mutable, so sample() on a Sampler could be const
			//
			// TODO - we probably want to share samplers between threads, but currently, Sampler isn't threadsafe?
			mutable std::optional<GafferImage::Sampler> channels[4];
			V2f dataWindowSize;
		};

		container::flat_map<ustring, UserData, OIIO::ustringPtrIsLess> m_userData;
		container::flat_map<ustring, ContextData, OIIO::ustringPtrIsLess> m_contextVariables;

		std::vector<GafferTextureData> m_gafferTextures;

		// Each thread gets its own copy of RenderState, so we can safely put scratch memory here
		mutable std::vector< float > m_scratchMemory;
};

struct ThreadRenderState
{
	ThreadRenderState(const RenderState& renderState) : pointIndex(0), renderState ( renderState ) {}
	size_t pointIndex;
	const RenderState& renderState;
};

int g_gafferTextureHandleMagicNumber = -42;
class GafferTextureHandle
{
public:
	GafferTextureHandle() : m_oiioTexSysRefCount( g_gafferTextureHandleMagicNumber )
	{
	}

	bool isGafferTextureHandle()
	{
		return m_oiioTexSysRefCount == g_gafferTextureHandleMagicNumber;
	}

private:

	
	const OIIO::atomic_int m_oiioTexSysRefCount;
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// RendererServices
//////////////////////////////////////////////////////////////////////////

namespace
{

class RendererServices : public OSL::RendererServices
{

	public :

		RendererServices( OSL::TextureSystem *textureSystem )
			:	OSL::RendererServices( textureSystem )
		{
		}

		bool get_matrix( OSL::ShaderGlobals *sg, OSL::Matrix44 &result, TransformationPtr xform, float time ) override
		{
			return false;
		}

		bool get_matrix( OSL::ShaderGlobals *sg, OSL::Matrix44 &result, TransformationPtr xform ) override
		{
			return false;
		}

		bool get_matrix( OSL::ShaderGlobals *sg, OSL::Matrix44 &result, ustring from, float time ) override
		{
			const ThreadRenderState *threadRenderState = sg ? static_cast<ThreadRenderState *>( sg->renderstate ) : nullptr;
			if( threadRenderState )
			{
				return threadRenderState->renderState.matrixToObject( from, result  );
			}

			return false;
		}

		bool get_inverse_matrix( OSL::ShaderGlobals *sg, OSL::Matrix44 &result, ustring to, float time ) override
		{
			const ThreadRenderState *threadRenderState = sg ? static_cast<ThreadRenderState *>( sg->renderstate ) : nullptr;
			if( threadRenderState )
			{
				return threadRenderState->renderState.matrixFromObject( to, result  );
			}

			return false;
		}

		bool get_matrix( OSL::ShaderGlobals *sg, OSL::Matrix44 &result, ustring from ) override
		{
			return false;
		}

		bool get_attribute( OSL::ShaderGlobals *sg, bool derivatives, ustring object, TypeDesc type, ustring name, void *value ) override
		{
			const ThreadRenderState *threadRenderState = sg ? static_cast<ThreadRenderState *>( sg->renderstate ) : nullptr;
			if( !threadRenderState )
			{
				return false;
			}

			if( object == g_contextVariableAttributeScope )
			{
				if( derivatives )
				{
					memset( (char*)value + type.size(), 0, 2 * type.size() );
				}

				return threadRenderState->renderState.contextVariable( name, type, value );
			}

			// fall through to get_userdata - i'm not sure this is the intention of the osl spec, but how else can
			// a shader access a primvar by name? maybe i've overlooked something.
			return get_userdata( derivatives, name, type, sg, value );
		}

		bool get_array_attribute( OSL::ShaderGlobals *sg, bool derivatives, ustring object, TypeDesc type, ustring name, int index, void *value ) override
		{
			return false;
		}

		bool get_userdata( bool derivatives, ustring name, TypeDesc type, OSL::ShaderGlobals *sg, void *value ) override
		{
			const ThreadRenderState *threadRenderState = sg ? static_cast<ThreadRenderState *>( sg->renderstate ) : nullptr;
			if( !threadRenderState )
			{
				return false;
			}

			if( derivatives )
			{
				memset( (char*)value + type.size(), 0, 2 * type.size() );
			}

			return threadRenderState->renderState.userData( threadRenderState->pointIndex,  name, type, value );
		}

		virtual bool has_userdata( ustring name, TypeDesc type, OSL::ShaderGlobals *sg )
		{
			const ThreadRenderState *threadRenderState = sg ? static_cast<ThreadRenderState *>( sg->renderstate ) : nullptr;
			if( !threadRenderState )
			{
				return false;
			}
			return threadRenderState->renderState.userData( threadRenderState->pointIndex, name, type, nullptr );
		}

		
		TextureHandle * get_texture_handle( ustring filename, ShadingContext *context ) override
		{
			if( boost::starts_with( filename, g_gafferImagePrefix ) )
			{
				if( !g_gafferTextureIndices )
				{
					throw IECore::Exception( "Should not be possible\n" );
				}
				auto i = g_gafferTextureIndices->find( filename );
				if( i == g_gafferTextureIndices->end() )
				{
					throw IECore::Exception( "Cannot access Gaffer image, it was not visible during compilation: " + filename.string() );
				}
				else
				{
					if( i->second > (int)g_gafferTextureIndicesBuffer.size() )
					{
						throw IECore::Exception( "GafferOSL::ShadingEngine Too many unique Gaffer images used." );
					}
					return (TextureHandle*)( &g_gafferTextureIndicesBuffer[ i->second ] );
				}
			}

			return OSL::RendererServices::get_texture_handle( filename, context );

			
			//return texturesys()->get_texture_handle( filename, context->texture_thread_info() );
		}

		bool texture( ustring filename, TextureHandle* texture_handle,
                          TexturePerthread* texture_thread_info,
                          TextureOpt& options, ShaderGlobals* sg, float s,
                          float t, float dsdx, float dtdx, float dsdy,
                          float dtdy, int nchannels, float* result,
                          float* dresultds, float* dresultdt,
                          ustring* errormessage) override
		{
			if( texture_handle )
			{
				size_t gafferTextureIndex = ((char*)texture_handle) - &g_gafferTextureIndicesBuffer[0];

				if( gafferTextureIndex <= g_gafferTextureIndicesBuffer.size() )
				{
					const ThreadRenderState *threadRenderState = sg ? static_cast<ThreadRenderState *>( sg->renderstate ) : nullptr;
					if( threadRenderState->renderState.texture(
						gafferTextureIndex, options, 
						s, t, dsdx, dtdx, dsdy, dtdy,
						nchannels, result, dresultds, dresultdt, errormessage
					) )
					{
						return true;
					}
				}
			}
			else if( boost::starts_with( filename, g_gafferImagePrefix ) )
			{
				throw IECore::Exception( "Cannot access Gaffer image, it was not visible during compilation: " + filename.string() );
			}
			
			return OSL::RendererServices::texture( filename, texture_handle, texture_thread_info, options, sg, s, t, dsdx, dtdx, dsdy, dtdy, nchannels, result, dresultds, dresultdt, errormessage );
		}

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// ShadingSystem
//////////////////////////////////////////////////////////////////////////

namespace
{

enum ClosureId
{
	EmissionClosureId,
	DebugClosureId,
	DeformationClosureId
};

struct EmissionParameters
{
};

struct DebugParameters
{

	ustring name;
	ustring type;
	Color3f value;
	M44f matrixValue;
	ustring stringValue;

	static void prepare( OSL::RendererServices *rendererServices, int id, void *data )
	{
		DebugParameters *debugParameters = static_cast<DebugParameters *>( data );
		debugParameters->name = ustring();
		debugParameters->type = ustring();
		debugParameters->value = Color3f( 1.0f );
		debugParameters->matrixValue = M44f();
		debugParameters->stringValue = ustring();
	}

};

// Must be held in order to modify the shading system.
// Should not be acquired before calling shadingSystem(),
// since shadingSystem() itself will use it.
using ShadingSystemWriteMutex = tbb::spin_mutex;
ShadingSystemWriteMutex g_shadingSystemWriteMutex;

OSL::ShadingSystem *shadingSystem()
{
	ShadingSystemWriteMutex::scoped_lock shadingSystemWriteLock( g_shadingSystemWriteMutex );
	static OSL::TextureSystem *g_textureSystem = nullptr;
	static OSL::ShadingSystem *g_shadingSystem = nullptr;
	if( g_shadingSystem )
	{
		return g_shadingSystem;
	}

	g_textureSystem = OIIO::TextureSystem::create( /* shared = */ false );
	// By default, OIIO considers the image origin to be at the
	// top left. We consider it to be at the bottom left.
	// Compensate.
	g_textureSystem->attribute( "flip_t", 1 );

	g_shadingSystem = new ShadingSystem(
		new RendererServices( g_textureSystem ),
		g_textureSystem
	);

	ClosureParam emissionParams[] = {
		CLOSURE_FINISH_PARAM( EmissionParameters ),
	};


	ClosureParam debugParams[] = {
		CLOSURE_STRING_PARAM( DebugParameters, name ),
		CLOSURE_STRING_KEYPARAM( DebugParameters, type, "type" ),
		CLOSURE_COLOR_KEYPARAM( DebugParameters, value, "value" ),
		CLOSURE_MATRIX_KEYPARAM( DebugParameters, matrixValue, "matrixValue"),
		CLOSURE_STRING_KEYPARAM( DebugParameters, stringValue, "stringValue"),
		CLOSURE_FINISH_PARAM( DebugParameters )
	};

	g_shadingSystem->register_closure(
		/* name */ "emission",
		/* id */ EmissionClosureId,
		/* params */ emissionParams,
		/* prepare */ nullptr,
		/* setup */ nullptr
	);

	g_shadingSystem->register_closure(
		/* name */ "debug",
		/* id */ DebugClosureId,
		/* params */ debugParams,
		/* prepare */ DebugParameters::prepare,
		/* setup */ nullptr
	);

	g_shadingSystem->register_closure(
		/* name */ "deformation",
		/* id */ DeformationClosureId,
		/* params */ debugParams,
		/* prepare */ DebugParameters::prepare,
		/* setup */ nullptr
	);

	if( const char *searchPath = getenv( "OSL_SHADER_PATHS" ) )
	{
		g_shadingSystem->attribute( "searchpath:shader", searchPath );
	}
	g_shadingSystem->attribute( "lockgeom", 1 );

	g_shadingSystem->attribute( "commonspace", "object" );

	return g_shadingSystem;
}

} // namespace


//////////////////////////////////////////////////////////////////////////
// ShadingResults
//////////////////////////////////////////////////////////////////////////

namespace
{

OIIO::ustring g_matrixType( "matrix" );
OIIO::ustring g_stringType( "string" );
OIIO::ustring g_point2Type( "point2" );
OIIO::ustring g_vector2Type( "vector2" );
OIIO::ustring g_normal2Type( "normal2" );
OIIO::ustring g_uvType( "uv" );

class ShadingResults
{

	public :

		ShadingResults( size_t numPoints )
			:	m_results( new CompoundData ), m_ci( nullptr )
		{
			Color3fVectorDataPtr ciData = new Color3fVectorData();
			m_ci = &ciData->writable();
			m_ci->resize( numPoints, Color3f( 0.0f ) );

			CompoundDataPtr result = new CompoundData();
			m_results->writable()["Ci"] = ciData;
		}

		/// \todo This is a lot like the UserData struct above - maybe we should
		/// just have one type we can use for both?
		struct DebugResult
		{
			DebugResult()
				:	basePointer( nullptr )
			{
			}

			TypeDesc type;
			void *basePointer;
		};

		using DebugResultsMap = container::flat_map<ustring, DebugResult, OIIO::ustringPtrIsLess>;

		void addResult( size_t pointIndex, const ClosureColor *result, DebugResultsMap &threadCache )
		{
			addResult( pointIndex, result, Color3f( 1.0f ), threadCache );
		}

		CompoundDataPtr results()
		{
			return m_results;
		}

	private :

		void addResult( size_t pointIndex, const ClosureColor *closure, const Color3f &weight, DebugResultsMap &threadCache )
		{
			if( closure )
			{
				switch( closure->id )
				{
					case ClosureColor::MUL :
						addResult(
							pointIndex,
							closure->as_mul()->closure,
							weight * closure->as_mul()->weight,
							threadCache
						);
						break;
					case ClosureColor::ADD :
						addResult( pointIndex, closure->as_add()->closureA, weight, threadCache );
						addResult( pointIndex, closure->as_add()->closureB, weight, threadCache );
						break;
					case EmissionClosureId :
						addEmission( pointIndex, closure->as_comp()->as<EmissionParameters>(), weight * closure->as_comp()->w );
						break;
					case DeformationClosureId :
					case DebugClosureId :
						addDebug( pointIndex, closure->as_comp()->as<DebugParameters>(), weight * closure->as_comp()->w, threadCache );
						break;
				}
			}
		}

		void addEmission( size_t pointIndex, const EmissionParameters *parameters, const Color3f &weight )
		{
			(*m_ci)[pointIndex] += weight;
		}

		DebugResult acquireDebugResult( const DebugParameters *parameters, DebugResultsMap &threadCache )
		{
			// Try the per-thread cache first.
			auto it = threadCache.find( parameters->name );
			if( it != threadCache.end() )
			{
				return it->second;
			}

			// If it's not there, then we need to look in `m_debugResults`,
			// which requires locking. Start optimistically with a read lock.
			tbb::spin_rw_mutex::scoped_lock rwScopedLock( m_resultsMutex, /* write = */ false  );

			it = m_debugResults.find( parameters->name );
			if( it == m_debugResults.end() )
			{
				// Need to insert the result, so need a write lock.
				rwScopedLock.upgrade_to_writer();
				// But another thread may have got the write lock before us
				// and done the work itself, so check again just in case.
				it = m_debugResults.find( parameters->name );
				if( it == m_debugResults.end() )
				{
					// Create the result.
					DebugResult result;
					result.type = typeDescFromTypeName( parameters->type );
					result.type.arraylen = m_ci->size();

					DataPtr data = dataFromTypeDesc( result.type, result.basePointer );
					if( !data )
					{
						throw IECore::Exception( "Unsupported type specified in debug() closure." );
					}
					if( parameters->type == g_uvType )
					{
						static_cast<V2fVectorData *>( data.get() )->setInterpretation( GeometricData::UV );
					}

					result.type.unarray(); // so we can use convert_value

					m_results->writable()[parameters->name.c_str()] = data;
					it = m_debugResults.insert( make_pair( parameters->name, result ) ).first;
				}
			}

			// Cache so the next lookup on this thread doesn't need a lock.
			return threadCache.insert( *it ).first->second;
		}

		void addDebug( size_t pointIndex, const DebugParameters *parameters, const Color3f &weight, DebugResultsMap &threadCache )
		{
			DebugResult debugResult = acquireDebugResult( parameters, threadCache );

			if( parameters->type == g_matrixType )
			{
				M44f value = parameters->matrixValue;

				char *dst = static_cast<char *>( debugResult.basePointer );
				dst += pointIndex * debugResult.type.elementsize();
				ShadingSystem::convert_value(
					dst, debugResult.type, &value, TypeDesc::TypeMatrix44
				);
			}
			else if( parameters->type == g_stringType )
			{
				std::string *dst = static_cast<std::string*>( debugResult.basePointer );
				dst += pointIndex;
				*dst = parameters->stringValue.string();
			}
			else
			{
				Color3f value = weight * parameters->value;

				char *dst = static_cast<char *>( debugResult.basePointer );
				dst += pointIndex * debugResult.type.elementsize();
				convertValue(
					dst,
					debugResult.type,
					&value,
					debugResult.type.aggregate == TypeDesc::SCALAR ? TypeDesc::TypeFloat : TypeDesc::TypeColor
				);
			}
		}

		OIIO::TypeDesc typeDescFromTypeName( ustring type )
		{
			if( type == g_point2Type )
			{
				return TypeDesc( TypeDesc::FLOAT, TypeDesc::VEC2, TypeDesc::POINT );
			}
			else if( type == g_vector2Type || type == g_uvType )
			{
				return TypeDesc( TypeDesc::FLOAT, TypeDesc::VEC2, TypeDesc::VECTOR );
			}
			else if( type == g_normal2Type )
			{
				return TypeDesc( TypeDesc::FLOAT, TypeDesc::VEC2, TypeDesc::NORMAL );
			}
			return type != ustring() ? TypeDesc( type.c_str() ) : TypeDesc::TypeColor;
		}

		CompoundDataPtr m_results;
		vector<Color3f> *m_ci;
		DebugResultsMap m_debugResults;
		tbb::spin_rw_mutex m_resultsMutex;

};

// Thread specific information needed during shading - this includes both the per-thread result cache,
// and the OSL machinery that needs to be stored per "renderer-thread"
struct ThreadInfo
{
	ThreadInfo()
		: oslThreadInfo( ::shadingSystem()->create_thread_info() ),
		  shadingContext( ::shadingSystem()->get_context( oslThreadInfo ) )
	{
	}

	~ThreadInfo()
	{
		::shadingSystem()->release_context( shadingContext );
		::shadingSystem()->destroy_thread_info( oslThreadInfo );
	}

	ShadingResults::DebugResultsMap debugResults;
	OSL::PerThreadInfo *oslThreadInfo;
	OSL::ShadingContext *shadingContext;
};


} // namespace

//////////////////////////////////////////////////////////////////////////
// ShadingEngine
//////////////////////////////////////////////////////////////////////////

namespace
{

void declareParameters( const CompoundDataMap &parameters, ShadingSystem *shadingSystem )
{
	for( CompoundDataMap::const_iterator it = parameters.begin(), eIt = parameters.end(); it != eIt; ++it )
	{
		IECoreImage::OpenImageIOAlgo::DataView dataView( it->second.get() );
		if( dataView.data )
		{
			if(
				dataView.type.vecsemantics == TypeDesc::NOXFORM &&
				( runTimeCast<V3fData>( it->second.get() ) || runTimeCast<V3fVectorData>( it->second.get() ) )
			)
			{
				// There is no vector type in OSL which has NOXFORM semantics,
				// so VECTOR is a more useful default.
				dataView.type.vecsemantics = TypeDesc::VECTOR;
			}
			shadingSystem->Parameter( it->first.c_str(), dataView.type, dataView.data );
		}
		else
		{
			msg( Msg::Warning, "ShadingEngine", boost::format( "Parameter \"%s\" has unsupported type \"%s\"" ) % it->first.string() % it->second->typeName() );
		}
	}
}

template <typename T>
static T uniformValue( const IECore::CompoundData *points, const char *name )
{
	using DataType = TypedData<T>;
	const DataType *d = points->member<DataType>( name );
	if( d )
	{
		return d->readable();
	}
	else
	{
		return T( 0.0f );
	}
}

template<typename T>
static const T *varyingValue( const IECore::CompoundData *points, const char *name )
{
	using DataType = TypedData<vector<T> >;
	const DataType *d = points->member<DataType>( name );
	if( d )
	{
		return &(d->readable()[0]);
	}
	else
	{
		return nullptr;
	}
}

} // namespace

ShadingEngine::ShadingEngine( const IECoreScene::ShaderNetwork *shaderNetwork )
	:	m_hash( shaderNetwork->Object::hash() ), m_timeNeeded( false ), m_unknownAttributesNeeded( false ), m_hasDeformation( false )
{
	ShaderNetworkPtr networkCopy = shaderNetwork->copy();
	IECoreScene::ShaderNetworkAlgo::convertOSLComponentConnections( networkCopy.get(), OSL_VERSION );
	shaderNetwork = networkCopy.get();

	ShadingSystem *shadingSystem = ::shadingSystem();

	{
		ShadingSystemWriteMutex::scoped_lock shadingSystemWriteLock( g_shadingSystemWriteMutex );
		m_shaderGroupRef = new ShaderGroupRef( shadingSystem->ShaderGroupBegin() );
		std::vector<std::string> invalidShaders;

		ShaderNetworkAlgo::depthFirstTraverse(
			shaderNetwork,
			[shadingSystem, &invalidShaders] ( const ShaderNetwork *shaderNetwork, const InternedString &handle ) {

				// Check for invalid (non-OSL) shaders. We stop declaring shaders if any
				// have been found, but complete the traversal so that we can compile a
				// full list of invalid shaders.

				const Shader *shader = shaderNetwork->getShader( handle );
				if( !boost::starts_with( shader->getType(), "osl:" ) )
				{
					invalidShaders.push_back( shader->getName() + " (" + shader->getType() + ")" );
				}

				if( invalidShaders.size() )
				{
					return;
				}

				// Declare this shader along with its parameters and connections.

				IECore::ConstCompoundDataPtr expandedParameters =
					IECoreScene::ShaderNetworkAlgo::expandSplineParameters(
						shader->parametersData()
					);
				declareParameters( expandedParameters->readable(), shadingSystem );
				shadingSystem->Shader( "surface", shader->getName().c_str(), handle.c_str() );

				for( const auto &c : shaderNetwork->inputConnections( handle ) )
				{
					shadingSystem->ConnectShaders(
						c.source.shader.c_str(), c.source.name.c_str(),
						c.destination.shader.c_str(), c.destination.name.c_str()
					);
				}
			}
		);

		shadingSystem->ShaderGroupEnd();

		if( !invalidShaders.empty() )
		{
			std::string exceptionMessage = "The following shaders can't be used as they are not OSL shaders: ";
			throw Exception( exceptionMessage + boost::algorithm::join( invalidShaders, ", " ) );
		}
	}

	queryShaderGroup();
}

void ShadingEngine::queryShaderGroup()
{
	ShadingSystem *shadingSystem = ::shadingSystem();
	ShaderGroup &shaderGroup = **static_cast<ShaderGroupRef *>( m_shaderGroupRef );

	// Globals

	int numGlobalsNeeded = 0;
	shadingSystem->getattribute( &shaderGroup, "num_globals_needed", numGlobalsNeeded );
	if( numGlobalsNeeded )
	{
		ustring *globalsNames = nullptr;
		shadingSystem->getattribute(  &shaderGroup, "globals_needed", TypeDesc::PTR, &globalsNames );
		for( int i = 0; i < numGlobalsNeeded; ++i )
		{
			if( globalsNames[i] == "time" )
			{
				m_timeNeeded = true;
			}

			m_attributesNeeded.insert( globalsNames[i].string() );
		}
	}

	// Attributes

	int unknownAttributesNeeded = 0;
	shadingSystem->getattribute(  &shaderGroup, "unknown_attributes_needed", unknownAttributesNeeded );
	m_unknownAttributesNeeded = static_cast<bool> (unknownAttributesNeeded);

	int numAttributes = 0;
	shadingSystem->getattribute( &shaderGroup, "num_attributes_needed", numAttributes );
	if( numAttributes )
	{
		ustring *attributeNames = nullptr;
		ustring *scopeNames = nullptr;
		shadingSystem->getattribute(  &shaderGroup, "attributes_needed", TypeDesc::PTR, &attributeNames );
		shadingSystem->getattribute(  &shaderGroup, "attribute_scopes", TypeDesc::PTR, &scopeNames );

		for (int i = 0; i < numAttributes; ++i)
		{
			if( scopeNames[i] == g_contextVariableAttributeScope )
			{
				m_contextVariablesNeeded.push_back( attributeNames[i].string() );
			}
			else
			{
				m_attributesNeeded.insert( attributeNames[i].string()  );
			}
		}
	}

	// Closures

	int unknownClosuresNeeded = 0;
	shadingSystem->getattribute(  &shaderGroup, "unknown_closures_needed", unknownClosuresNeeded );
	if( unknownClosuresNeeded )
	{
		m_hasDeformation = true;
	}

	int numClosures = 0;
	shadingSystem->getattribute( &shaderGroup, "num_closures_needed", numClosures );
	if( numClosures )
	{
		ustring *closureNames = nullptr;
		shadingSystem->getattribute(  &shaderGroup, "closures_needed", TypeDesc::PTR, &closureNames );
		for( int i = 0; i < numClosures; ++i )
		{
			if( closureNames[i] == "deformation" )
			{
				m_hasDeformation = true;
				break;
			}
		}
	}

	int numTextures = 0;
	shadingSystem->getattribute( &shaderGroup, "num_textures_needed", numTextures );
	if( numTextures )
	{
		ustring *textureNames = nullptr;
		shadingSystem->getattribute(  &shaderGroup, "textures_needed", TypeDesc::PTR, &textureNames );
		for( int i = 0; i < numTextures; ++i )
		{
			if( boost::starts_with( textureNames[i], g_gafferImagePrefix ) )
			{
				m_gafferTextureIndices[ textureNames[i] ] = m_gafferTexturesRequested.size();
				m_gafferTexturesRequested.push_back( textureNames[i] );

			}
		}
	}

	
	

}

ShadingEngine::~ShadingEngine()
{
	delete static_cast<ShaderGroupRef *>( m_shaderGroupRef );
}

void ShadingEngine::hash( IECore::MurmurHash &h ) const
{
	h.append( m_hash );
	if( m_timeNeeded || m_contextVariablesNeeded.size() )
	{
		const Gaffer::Context *context = Gaffer::Context::current();
		if( m_timeNeeded )
		{
			h.append( context->getTime() );
		}
		for( const auto &name : m_contextVariablesNeeded )
		{
			h.append( context->variableHash( name ) );
		}
	}
}

IECore::CompoundDataPtr ShadingEngine::shade( const IECore::CompoundData *points, const Transforms &transforms, const ImagePlugs &imagePlugs ) const
{
	// Get the data for "P" - this determines the number of points to be shaded.

	size_t numPoints = 0;

	const OSL::Vec3 *p = nullptr;
	if( const V3fVectorData *pData = points->member<V3fVectorData>( "P" ) )
	{
		numPoints = pData->readable().size();
		p = reinterpret_cast<const OSL::Vec3 *>( &(pData->readable()[0]) );
	}
	else
	{
		throw Exception( "No P data" );
	}

	// Create ShaderGlobals, and fill it with any uniform values that have
	// been provided.

	ShaderGlobals shaderGlobals;
	memset( (void *)&shaderGlobals, 0, sizeof( ShaderGlobals ) );

	const Gaffer::Context *context = Gaffer::Context::current();
	shaderGlobals.time = context->getTime();

	shaderGlobals.dPdx = uniformValue<V3f>( points, "dPdx" );
	shaderGlobals.dPdy = uniformValue<V3f>( points, "dPdy" );
	shaderGlobals.dPdz = uniformValue<V3f>( points, "dPdz" );

	shaderGlobals.I = uniformValue<V3f>( points, "I" );
	shaderGlobals.dIdx = uniformValue<V3f>( points, "dIdx" );
	shaderGlobals.dIdy = uniformValue<V3f>( points, "dIdy" );

	shaderGlobals.N = uniformValue<V3f>( points, "N" );
	shaderGlobals.Ng = uniformValue<V3f>( points, "Ng" );

	shaderGlobals.u = uniformValue<float>( points, "u" );
	shaderGlobals.dudx = uniformValue<float>( points, "dudx" );
	shaderGlobals.dudy = uniformValue<float>( points, "dudy" );

	shaderGlobals.v = uniformValue<float>( points, "v" );
	shaderGlobals.dvdx = uniformValue<float>( points, "dvdx" );
	shaderGlobals.dvdy = uniformValue<float>( points, "dvdy" );

	shaderGlobals.dPdu = uniformValue<V3f>( points, "dPdu" );
	shaderGlobals.dPdv = uniformValue<V3f>( points, "dPdv" );

	// Add a RenderState to the ShaderGlobals. This will
	// get passed to our RendererServices queries.

	RenderState renderState( points, transforms, m_contextVariablesNeeded, context, m_gafferTexturesRequested, imagePlugs );

	// Get pointers to varying data, we'll use these to
	// update the shaderGlobals as we iterate over our points.

	const float *u = varyingValue<float>( points, "u" );
	const float *v = varyingValue<float>( points, "v" );
	const V2f *uv = varyingValue<V2f>( points, "uv" );
	const V3f *n = varyingValue<V3f>( points, "N" );

	/// \todo Get the other globals - match the uniform list

	// Allocate data for the result

	ShadingResults results( numPoints );

	// Iterate over the input points, doing the shading as we go

	tbb::enumerable_thread_specific<ThreadInfo> threadInfoCache;

	const IECore::Canceller *canceller = context->canceller();

	ShadingSystem *shadingSystem = ::shadingSystem();
	ShaderGroup &shaderGroup = **static_cast<ShaderGroupRef *>( m_shaderGroupRef );

	{
		// Do a quick init of the shading system while setting the global map of texture indices
		// to map the correct textures for this ShadingEngine
		tbb::spin_mutex::scoped_lock lock( g_gafferTextureIndicesMutex );
		g_gafferTextureIndices = &m_gafferTextureIndices;
		shadingSystem->execute_init( *threadInfoCache.local().shadingContext, shaderGroup, shaderGlobals, false );
		g_gafferTextureIndices = nullptr;
	}

	auto f = [&shadingSystem, &renderState, &results, &shaderGlobals, &p, &u, &v, &uv, &n, &shaderGroup, &threadInfoCache, canceller]( const tbb::blocked_range<size_t> &r )
	{
		ThreadInfo &threadInfo = threadInfoCache.local();

		ThreadRenderState threadRenderState( renderState );

		ShaderGlobals threadShaderGlobals = shaderGlobals;

		threadShaderGlobals.renderstate = &threadRenderState;

		for( size_t i = r.begin(); i < r.end(); ++i )
		{
			IECore::Canceller::check( canceller );

			threadShaderGlobals.P = p[i];

			if( uv )
			{
				threadShaderGlobals.u = uv[i].x;
				threadShaderGlobals.v = uv[i].y;
			}
			else
			{
				if( u )
				{
					threadShaderGlobals.u = u[i];
				}
				if( v )
				{
					threadShaderGlobals.v = v[i];
				}
			}

			if( n )
			{
				threadShaderGlobals.N = n[i];
			}

			threadShaderGlobals.Ci = nullptr;

			threadRenderState.pointIndex = i;
			shadingSystem->execute( threadInfo.shadingContext, shaderGroup, threadShaderGlobals );

			results.addResult( i, threadShaderGlobals.Ci, threadInfo.debugResults );
		}
	};

	// Use `task_group_context::isolated` to prevent TBB cancellation in outer
	// tasks from propagating down and stopping our tasks from being started.
	// Otherwise we silently return results with black gaps where tasks were omitted.
	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

	// TODO TODO TODO - since we haven't yet figured out how to multithread Sampler, currently we just crash
	// if multiple threads pick up here while we're sampling images.  We can hack around this temporarily
	// since we're only sampling images when processing image tiles, so we can just set the block size larger than
	// an image tile, but this is not at all sustainable.
	tbb::parallel_for( tbb::blocked_range<size_t>( 0, numPoints, 50000 ), f, taskGroupContext );

	return results.results();
}

bool ShadingEngine::needsAttribute( const std::string &name ) const
{
	if( name == "P" )
	{
		return true;
	}

	if( name == "uv" )
	{
		if ( m_attributesNeeded.find( "u" ) != m_attributesNeeded.end() || m_attributesNeeded.find( "v" ) != m_attributesNeeded.end() )
		{
			return true;
		}
	}

	if( m_unknownAttributesNeeded )
	{
		return true;
	}


	return m_attributesNeeded.find(  name  ) != m_attributesNeeded.end();
}

bool ShadingEngine::hasDeformation() const
{
	return m_hasDeformation;
}

bool ShadingEngine::needsImageSamples() const
{
	return m_gafferTexturesRequested.size() > 0;
}

IECore::MurmurHash ShadingEngine::hashPossibleImageSamples( const ImagePlugs &imagePlugs ) const
{
	IECore::MurmurHash h;


	for( const auto &textureName : m_gafferTexturesRequested )
	{
		ChannelsRequested cr( textureName.string(), imagePlugs );
		Box2i dw = cr.imagePlug->dataWindow( &GafferImage::ImagePlug::defaultViewName );
		h.append( dw );
		for( int i = 0; i < 4; i++ )
		{
			if( cr.channels[i] != "" )
			{
				// TODO - parallelize
				for ( int x = dw.min.x; x < dw.max.x; x += GafferImage::ImagePlug::tileSize() )
				{
					for ( int y = dw.min.y; y < dw.max.y; y += GafferImage::ImagePlug::tileSize() )
					{
						h.append( cr.imagePlug->channelDataHash( cr.channels[i], Imath::V2i( x, y ) ) );
					}
				}
			}
		}
	}
	return h;
}
