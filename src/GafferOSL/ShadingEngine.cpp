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

#include "IECoreScene/Shader.h"

#include "IECoreImage/OpenImageIOAlgo.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/SplineData.h"
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
#include "boost/unordered_map.hpp"

#include "tbb/enumerable_thread_specific.h"
#include "tbb/parallel_for.h"
#include "tbb/spin_mutex.h"
#include "tbb/spin_rw_mutex.h"

#include <limits>

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
// Utility for converting IECore::Data types to OSL::TypeDesc types.
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

} // namespace

//////////////////////////////////////////////////////////////////////////
// RenderState
//////////////////////////////////////////////////////////////////////////

namespace
{

OIIO::ustring gIndex( "shading:index" );
OIIO::ustring gMatrixType( "matrix" );

class RenderState
{

	public :

		RenderState( const IECore::CompoundData *shadingPoints, const ShadingEngine::Transforms &transforms )
		{
			for( CompoundDataMap::const_iterator it = shadingPoints->readable().begin(),
				 eIt = shadingPoints->readable().end(); it != eIt; ++it )
			{
				UserData userData;
				userData.dataView = IECoreImage::OpenImageIOAlgo::DataView( it->second.get() );
				if( userData.dataView.data )
				{
					userData.name = it->first;
					if( userData.dataView.type.arraylen )
					{
						// we unarray the TypeDesc so we can use it directly with
						// convert_value() in get_userdata().
						userData.dataView.type.unarray();
						userData.array = true;
					}
					m_userData.push_back( userData );
				}
			}

			sort( m_userData.begin(), m_userData.end() );

			for( ShadingEngine::Transforms::const_iterator it = transforms.begin(); it != transforms.end(); it++ )
			{
				m_transforms[ OIIO::ustring( it->first.string() ) ] = it->second;
			}
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

			vector<UserData>::const_iterator it = lower_bound(
				m_userData.begin(),
				m_userData.end(),
				name
			);

			if( it == m_userData.end() || it->name != name )
			{
				return false;
			}

			const char *src = static_cast<const char *>( it->dataView.data );
			if( it->array )
			{
				src += pointIndex * it->dataView.type.elementsize();
			}

			if( ShadingSystem::convert_value( value, type, src, it->dataView.type ) )
			{
				// OSL converted successfully
				return true;
			}
			else if( it->dataView.type.basetype == type.basetype && it->dataView.type.aggregate == type.arraylen )
			{
				// Convert an aggregate (vec2, vec3, vec4, matrix33, matrix44) to an array with the same base type.
				// Note that the aggregate enum value is the number of elements.
				memcpy( value, src, type.size() );
				return true;
			}
			else if( it->dataView.type.aggregate == TypeDesc::VEC2 )
			{
				// OSL doesn't know how to convert these, but it knows how to convert
				// float[2], which has an identical layout.
				TypeDesc t = it->dataView.type;
				t.aggregate = TypeDesc::SCALAR;
				t.arraylen = 2;
				return ShadingSystem::convert_value( value, type, src, t );
			}
			/// \todo Try to get these additional conversions accepted into OSL itself

			return false;
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

	private :

		typedef boost::unordered_map< OIIO::ustring, ShadingEngine::Transform, OIIO::ustringHash > RenderStateTransforms;
		RenderStateTransforms m_transforms;

		struct UserData
		{
			UserData()
				:	array( false )
			{
			}

			ustring name;
			IECoreImage::OpenImageIOAlgo::DataView dataView;
			bool array;

			bool operator < ( const UserData &rhs ) const
			{
				return name.c_str() < rhs.name.c_str();
			}

			bool operator < ( const ustring &rhs ) const
			{
				return name.c_str() < rhs.c_str();
			}
		};

		vector<UserData> m_userData; // sorted on name for quick lookups

};

struct ThreadRenderState
{
	ThreadRenderState(const RenderState& renderState) : pointIndex(0), renderState ( renderState ) {}
	size_t pointIndex;
	const RenderState& renderState;
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
	DebugClosureId
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

	static void prepare( OSL::RendererServices *rendererServices, int id, void *data )
	{
		DebugParameters *debugParameters = static_cast<DebugParameters *>( data );
		debugParameters->name = ustring();
		debugParameters->type = ustring();
		debugParameters->value = Color3f( 1.0f );
		debugParameters->matrixValue = M44f();
	}

};

// Must be held in order to modify the shading system.
// Should not be acquired before calling shadingSystem(),
// since shadingSystem() itself will use it.
typedef tbb::spin_mutex ShadingSystemWriteMutex;
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

	struct ClosureDefinition{
		const char *name;
		int id;
		ClosureParam parameters[32];
		PrepareClosureFunc prepare;
	};

	ClosureDefinition closureDefinitions[] = {
		{
			"emission",
			EmissionClosureId,
			{
				CLOSURE_FINISH_PARAM( EmissionParameters )
			}
		},
		{
			"debug",
			DebugClosureId,
			{
				CLOSURE_STRING_PARAM( DebugParameters, name ),
				CLOSURE_STRING_KEYPARAM( DebugParameters, type, "type" ),
				CLOSURE_COLOR_KEYPARAM( DebugParameters, value, "value" ),
				CLOSURE_MATRIX_KEYPARAM( DebugParameters, matrixValue, "matrixValue"),
				CLOSURE_FINISH_PARAM( DebugParameters )
			},
			DebugParameters::prepare
		},
		// end marker
		{ nullptr, 0, {} }
	};

	for( int i = 0; closureDefinitions[i].name; ++i )
	{
		g_shadingSystem->register_closure(
			closureDefinitions[i].name,
			closureDefinitions[i].id,
			closureDefinitions[i].parameters,
			closureDefinitions[i].prepare,
			nullptr
		);
	}

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

			ustring name;
			TypeDesc type;
			void *basePointer;

			bool operator < ( const DebugResult &rhs ) const
			{
				return name.c_str() < rhs.name.c_str();
			}

			bool operator < ( const ustring &rhs ) const
			{
				return name.c_str() < rhs.c_str();
			}
		};

		typedef vector<DebugResult> DebugResultsContainer;

		void addResult( size_t pointIndex, const ClosureColor *result, DebugResultsContainer& threadCache )
		{
			addResult( pointIndex, result, Color3f( 1.0f ), threadCache );
		}

		CompoundDataPtr results()
		{
			return m_results;
		}

	private :

		void addResult( size_t pointIndex, const ClosureColor *closure, const Color3f &weight, DebugResultsContainer& threadCache )
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


		vector<DebugResult>::iterator search(ustring name, bool& match)
		{
			vector<DebugResult>::iterator it = lower_bound(
				m_debugResults.begin(),
				m_debugResults.end(),
				name
			);

			if (it != m_debugResults.end() && it->name == name)
			{
				match = true;
			}

			return it;
		}

		DebugResult findDebugResult(const DebugParameters *parameters, DebugResultsContainer& threadCache)
		{
			vector<DebugResult>::iterator threadCacheIt = lower_bound(
				threadCache.begin(),
				threadCache.end(),
				parameters->name
			);

			if (threadCacheIt != threadCache.end() && threadCacheIt->name == parameters->name)
			{
				return *threadCacheIt;
			}

			// take a reader lock and attempt to find the DebugResults object
			tbb::spin_rw_mutex::scoped_lock rwScopedLock( m_resultsMutex, /* write = */ false  );

			bool match = false;
			vector<DebugResult>::iterator it = search( parameters->name , match);

			if( match )
			{
				threadCache.insert( threadCacheIt, *it);
				// we've found the object and our reader lock will be released here
				return *it;
			}

			// lets take a writer lock and crate the output data array
			rwScopedLock.upgrade_to_writer();

			match = false;
			it = search( parameters->name, match );

			if( match )
			{
				return *it;
			}

			DebugResult result;
			result.name = parameters->name;
			result.type = parameters->type != ustring() ? TypeDesc( parameters->type.c_str() ) : TypeDesc::TypeColor;
			result.type.arraylen = m_ci->size();
			DataPtr data = dataFromTypeDesc( result.type, result.basePointer );
			if( !data )
			{
				throw IECore::Exception( "Unsupported type specified in debug() closure." );
			}
			result.type.unarray(); // so we can use convert_value

			m_results->writable()[result.name.c_str()] = data;
			m_debugResults.insert( it, result );
			threadCache.insert( threadCacheIt, result);

			return result;
		}

		void addDebug( size_t pointIndex, const DebugParameters *parameters, const Color3f &weight, DebugResultsContainer& threadCache )
		{
			DebugResult debugResult = findDebugResult( parameters, threadCache );

			if ( parameters->type == gMatrixType )
			{
				M44f value = parameters->matrixValue;

				char *dst = static_cast<char *>( debugResult.basePointer );
				dst += pointIndex * debugResult.type.elementsize();
				ShadingSystem::convert_value(
					dst, debugResult.type, &value, TypeDesc::TypeMatrix44
				);
			}
			else
			{
				Color3f value = weight * parameters->value;

				char *dst = static_cast<char *>( debugResult.basePointer );
				dst += pointIndex * debugResult.type.elementsize();
				ShadingSystem::convert_value(
					dst,
					debugResult.type,
					&value,
					debugResult.type.aggregate == TypeDesc::SCALAR ? TypeDesc::TypeFloat : TypeDesc::TypeColor
				);
			}
		}


		CompoundDataPtr m_results;
		vector<Color3f> *m_ci;
		DebugResultsContainer m_debugResults; // sorted on name for quick lookups

		tbb::spin_rw_mutex m_resultsMutex;
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// ShadingEngine
//////////////////////////////////////////////////////////////////////////

namespace
{

template<typename Spline>
void declareSpline( const InternedString &name, const Spline &spline, ShadingSystem *shadingSystem )
{
	vector<typename Spline::XType> positions;
	vector<typename Spline::YType> values;
	positions.reserve( spline.points.size() );
	values.reserve( spline.points.size() );
	for( typename Spline::PointContainer::const_iterator it = spline.points.begin(), eIt = spline.points.end(); it != eIt; ++it )
	{
		positions.push_back( it->first );
		values.push_back( it->second );
	}

	const char *basis = "catmull-rom";
	if( spline.basis == Spline::Basis::bezier() )
	{
		basis = "bezier";
	}
	else if( spline.basis == Spline::Basis::bSpline() )
	{
		basis = "bspline";
	}
	else if( spline.basis == Spline::Basis::linear() )
	{
		basis = "linear";
	}

    OSLShader::prepareSplineCVsForOSL( positions, values, basis );

	TypeDesc positionsType = TypeDescFromType<typename Spline::XType>::typeDesc();
	TypeDesc valuesType = TypeDescFromType<typename Spline::YType>::typeDesc();
	positionsType.arraylen = positions.size();
	valuesType.arraylen = values.size();

	shadingSystem->Parameter( name.string() + "Positions", positionsType, &positions.front() );
	shadingSystem->Parameter( name.string() + "Values", valuesType, &values.front() );
	shadingSystem->Parameter( name.string() + "Basis", TypeDesc::TypeString, &basis );

}

void declareParameters( const CompoundDataMap &parameters, ShadingSystem *shadingSystem )
{
	for( CompoundDataMap::const_iterator it = parameters.begin(), eIt = parameters.end(); it != eIt; ++it )
	{
		if( it->first == "__handle" )
		{
			continue;
		}

		if( it->second->isInstanceOf( StringDataTypeId ) )
		{
			const std::string &value = static_cast<const StringData *>( it->second.get() )->readable();
			if( boost::starts_with( value, "link:" ) )
			{
				// this will be handled in declareConnections()
				continue;
			}
		}

		if( const SplinefColor3fData *spline = runTimeCast<const SplinefColor3fData>( it->second.get() ) )
		{
			declareSpline( it->first, spline->readable(), shadingSystem );
			continue;
		}
		else if( const SplineffData *spline = runTimeCast<const SplineffData>( it->second.get() ) )
		{
			declareSpline( it->first, spline->readable(), shadingSystem );
			continue;
		}

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

void declareConnections( const std::string &shaderHandle, const CompoundDataMap &parameters, ShadingSystem *shadingSystem )
{
	for( CompoundDataMap::const_iterator it = parameters.begin(), eIt = parameters.end(); it != eIt; ++it )
	{
		if( it->second->typeId() != StringDataTypeId )
		{
			continue;
		}
		const std::string &value = static_cast<const StringData *>( it->second.get() )->readable();
		if( boost::starts_with( value, "link:" ) )
		{
			vector<string> splitValue;
			split( splitValue, value, is_any_of( "." ), token_compress_on );
			if( splitValue.size() != 2 )
			{
				msg( Msg::Warning, "ShadingEngine", boost::format( "Parameter \"%s\" has unexpected value \"%s\" - expected value of the form \"link:sourceShader.sourceParameter" ) % it->first.string() % value );
				continue;
			}

			shadingSystem->ConnectShaders(
				splitValue[0].c_str() + 5, splitValue[1].c_str(),
				shaderHandle.c_str(), it->first.c_str()
			);
		}
	}
}

template <typename T>
static T uniformValue( const IECore::CompoundData *points, const char *name )
{
	typedef TypedData<T> DataType;
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
	typedef TypedData<vector<T> > DataType;
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

ShadingEngine::ShadingEngine( const IECore::ObjectVector *shaderNetwork )
	: m_unknownAttributesNeeded( false )
{
	ShadingSystem *shadingSystem = ::shadingSystem();

	std::vector<std::string> invalidShaders;
	{
		ShadingSystemWriteMutex::scoped_lock shadingSystemWriteLock( g_shadingSystemWriteMutex );

		m_shaderGroupRef = new ShaderGroupRef( shadingSystem->ShaderGroupBegin() );

		for( ObjectVector::MemberContainer::const_iterator it = shaderNetwork->members().begin(), eIt = shaderNetwork->members().end(); it != eIt; ++it )
		{
			const Shader *shader = runTimeCast<const Shader>( it->get() );
			if( !shader )
			{
				continue;
			}

			string type = shader->getType();
			if( !boost::starts_with( type, "osl:" ) )
			{
				invalidShaders.push_back( shader->getName() + " (" + type + ")" );
				continue;
			}

			if( !invalidShaders.empty() )
			{
				continue;
			}

			declareParameters( shader->parameters(), shadingSystem );
			const char *handle = nullptr;
			if( const StringData *handleData = shader->parametersData()->member<StringData>( "__handle" ) )
			{
				handle = handleData->readable().c_str();
			}
			else if( it == eIt - 1 )
			{
				handle = "gafferOSL:shadingSystem:root";
			}

			shadingSystem->Shader( "surface", shader->getName().c_str(), handle );
			if( handle )
			{
				declareConnections( handle, shader->parameters(), shadingSystem );
			}
		}

		shadingSystem->ShaderGroupEnd();

		if( !invalidShaders.empty() )
		{
			std::string exceptionMessage = "The following shaders can't be used as they are not OSL shaders: ";
			throw Exception( exceptionMessage + boost::algorithm::join( invalidShaders, ", " ) );
		}
	}

	queryAttributesNeeded();
}

void ShadingEngine::queryAttributesNeeded()
{
	ShadingSystem *shadingSystem = ::shadingSystem();

	ShaderGroup &shaderGroup = **static_cast<ShaderGroupRef *>( m_shaderGroupRef );

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
			m_attributesNeeded.insert(std::make_pair(scopeNames[i].string(), attributeNames[i].string() ) );
		}
	}
}

ShadingEngine::~ShadingEngine()
{
	delete static_cast<ShaderGroupRef *>( m_shaderGroupRef );
}

IECore::CompoundDataPtr ShadingEngine::shade( const IECore::CompoundData *points, const Transforms &transforms ) const
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
	memset( &shaderGlobals, 0, sizeof( ShaderGlobals ) );

	shaderGlobals.dPdx = uniformValue<V3f>( points, "dPdx" );
	shaderGlobals.dPdy = uniformValue<V3f>( points, "dPdy" );
	shaderGlobals.dPdz = uniformValue<V3f>( points, "dPdy" );

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

	RenderState renderState( points, transforms );

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

	ShadingSystem *shadingSystem = ::shadingSystem();
	ShaderGroup &shaderGroup = **static_cast<ShaderGroupRef *>( m_shaderGroupRef );

	struct ThreadContext
	{
		ShadingContext *shadingContext;
		ShadingResults::DebugResultsContainer results;
	};

	typedef tbb::enumerable_thread_specific<ThreadContext> ThreadContextType;
	ThreadContextType contexts;

	auto f = [&shadingSystem, &renderState, &results, &shaderGlobals, &p, &u, &v, &uv, &n, &shaderGroup, &contexts]( const tbb::blocked_range<size_t> &r )
	{
		ThreadContextType::reference context = contexts.local();
		if( !context.shadingContext )
		{
			context.shadingContext = shadingSystem->get_context();
		}

		ThreadRenderState threadRenderState( renderState );

		ShaderGlobals threadShaderGlobals = shaderGlobals;

		threadShaderGlobals.renderstate = &threadRenderState;

		for( size_t i = r.begin(); i < r.end(); ++i )
		{
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
			shadingSystem->execute( context.shadingContext, shaderGroup, threadShaderGlobals );

			results.addResult( i, threadShaderGlobals.Ci, context.results );
		}
	};

	tbb::parallel_for( tbb::blocked_range<size_t>( 0, numPoints, 5000 ), f );

	for( auto &shadingContext : contexts )
	{
		shadingSystem->release_context( shadingContext.shadingContext );
	}

	return results.results();
}

bool ShadingEngine::needsAttribute( const std::string &scope, const std::string &name ) const
{
	if( m_unknownAttributesNeeded )
	{
		return true;
	}

	return m_attributesNeeded.find( std::make_pair( scope, name ) ) != m_attributesNeeded.end();
}
