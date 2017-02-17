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

#include "tbb/spin_mutex.h"

#include "boost/algorithm/string/split.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/classification.hpp"
#include "boost/unordered_map.hpp"

#include "OSL/oslclosure.h"
#include "OSL/genclosure.h"
#include "OSL/oslversion.h"
#include "OSL/oslexec.h"
#include "OpenImageIO/ustring.h"


#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/VectorTypedData.h"
#include "IECore/Shader.h"
#include "IECore/SplineData.h"

#include "GafferImage/OpenImageIOAlgo.h"

#include "GafferOSL/ShadingEngine.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace OSL;
using namespace GafferImage;
using namespace GafferOSL;

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

template<typename T>
typename T::Ptr vectorDataFromTypeDesc( TypeDesc type, void *&basePointer )
{
	typename T::Ptr result = new T();
	result->writable().resize( type.arraylen, typename T::ValueType::value_type( 0 ) );
	basePointer = result->baseWritable();
	return result;
}

template<typename T>
typename T::Ptr geometricVectorDataFromTypeDesc( TypeDesc type, void *&basePointer )
{
	typename T::Ptr result = vectorDataFromTypeDesc<T>( type, basePointer );
	result->setInterpretation( OpenImageIOAlgo::geometricInterpretation( ( (TypeDesc::VECSEMANTICS)type.vecsemantics ) ) );
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
	}

	return NULL;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// RenderState
//////////////////////////////////////////////////////////////////////////

namespace
{

class RenderState
{

	public :

		RenderState( const IECore::CompoundData *shadingPoints, const ShadingEngine::Transforms &transforms )
			:	m_pointIndex( 0 )
		{
			for( CompoundDataMap::const_iterator it = shadingPoints->readable().begin(),
				 eIt = shadingPoints->readable().end(); it != eIt; ++it )
			{
				UserData userData;
				userData.dataView = OpenImageIOAlgo::DataView( it->second.get() );
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

		bool userData( ustring name, TypeDesc type, void *value ) const
		{
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
				src += m_pointIndex * it->dataView.type.elementsize();
			}

			return ShadingSystem::convert_value( value, type, src, it->dataView.type );
		}

		void incrementPointIndex()
		{
			m_pointIndex++;
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

		size_t m_pointIndex;


		typedef boost::unordered_map< OIIO::ustring, ShadingEngine::Transform, OIIO::ustringHash > RenderStateTransforms;
		RenderStateTransforms m_transforms;

		struct UserData
		{
			UserData()
				:	array( false )
			{
			}

			ustring name;
			OpenImageIOAlgo::DataView dataView;
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

} // namespace

//////////////////////////////////////////////////////////////////////////
// RendererServices
//////////////////////////////////////////////////////////////////////////

namespace
{

class RendererServices : public OSL::RendererServices
{

	public :

		RendererServices()
		{
		}

		virtual bool get_matrix( OSL::ShaderGlobals *sg, OSL::Matrix44 &result, TransformationPtr xform, float time )
		{
			return false;
		}

		virtual bool get_matrix( OSL::ShaderGlobals *sg, OSL::Matrix44 &result, TransformationPtr xform )
		{
			return false;
		}

		virtual bool get_matrix( OSL::ShaderGlobals *sg, OSL::Matrix44 &result, ustring from, float time )
		{
			const RenderState *renderState = sg ? static_cast<RenderState *>( sg->renderstate ) : NULL;
			if( renderState )
			{
				return renderState->matrixToObject( from, result  );
			}

			return false;
		}

		virtual bool get_inverse_matrix( OSL::ShaderGlobals *sg, OSL::Matrix44 &result, ustring to, float time )
		{
			const RenderState *renderState = sg ? static_cast<RenderState *>( sg->renderstate ) : NULL;
			if( renderState )
			{
				return renderState->matrixFromObject( to, result  );
			}

			return false;
		}

		virtual bool get_matrix( OSL::ShaderGlobals *sg, OSL::Matrix44 &result, ustring from )
		{
			return false;
		}

		virtual bool get_attribute( OSL::ShaderGlobals *sg, bool derivatives, ustring object, TypeDesc type, ustring name, void *value )
		{
			const RenderState *renderState = sg ? static_cast<RenderState *>( sg->renderstate ) : NULL;
			if( !renderState )
			{
				return false;
			}
			// fall through to get_userdata - i'm not sure this is the intention of the osl spec, but how else can
			// a shader access a primvar by name? maybe i've overlooked something.
			return get_userdata( derivatives, name, type, sg, value );
		}

		virtual bool get_array_attribute( OSL::ShaderGlobals *sg, bool derivatives, ustring object, TypeDesc type, ustring name, int index, void *value )
		{
			return false;
		}

		virtual bool get_userdata( bool derivatives, ustring name, TypeDesc type, OSL::ShaderGlobals *sg, void *value )
		{
			const RenderState *renderState = sg ? static_cast<RenderState *>( sg->renderstate ) : NULL;
			if( !renderState )
			{
				return false;
			}
			return renderState->userData( name, type, value );
		}

		virtual bool has_userdata( ustring name, TypeDesc type, OSL::ShaderGlobals *sg )
		{
			const RenderState *renderState = sg ? static_cast<RenderState *>( sg->renderstate ) : NULL;
			if( !renderState )
			{
				return false;
			}
			return renderState->userData( name, type, NULL );
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

	static void prepare( OSL::RendererServices *rendererServices, int id, void *data )
	{
		DebugParameters *debugParameters = static_cast<DebugParameters *>( data );
		debugParameters->name = ustring();
		debugParameters->type = ustring();
		debugParameters->value = Color3f( 1.0f );
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
	static OSL::ShadingSystem *s = NULL;
	if( s )
	{
		return s;
	}

	s = new ShadingSystem( new RendererServices );

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
				CLOSURE_FINISH_PARAM( DebugParameters )
			},
			DebugParameters::prepare
		},
		// end marker
		{ NULL, 0, {} }
	};

	for( int i = 0; closureDefinitions[i].name; ++i )
	{
		s->register_closure(
			closureDefinitions[i].name,
			closureDefinitions[i].id,
			closureDefinitions[i].parameters,
			closureDefinitions[i].prepare,
			NULL
		);
	}

	if( const char *searchPath = getenv( "OSL_SHADER_PATHS" ) )
	{
		s->attribute( "searchpath:shader", searchPath );
	}
	s->attribute( "lockgeom", 1 );

	s->attribute( "commonspace", "object" );

	return s;
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
			:	m_results( new CompoundData ), m_ci( NULL )
		{
			Color3fVectorDataPtr ciData = new Color3fVectorData();
			m_ci = &ciData->writable();
			m_ci->resize( numPoints, Color3f( 0.0f ) );

			CompoundDataPtr result = new CompoundData();
			m_results->writable()["Ci"] = ciData;
		}

		void addResult( size_t pointIndex, const ClosureColor *result )
		{
			addResult( pointIndex, result, Color3f( 1.0f ) );
		}

		CompoundDataPtr results()
		{
			return m_results;
		}

	private :

		void addResult( size_t pointIndex, const ClosureColor *closure, const Color3f &weight )
		{
			if( closure )
			{
				switch( closure->id )
				{
					case ClosureColor::MUL :
						addResult(
							pointIndex,
							closure->as_mul()->closure,
							weight * closure->as_mul()->weight
						);
						break;
					case ClosureColor::ADD :
						addResult( pointIndex, closure->as_add()->closureA, weight );
						addResult( pointIndex, closure->as_add()->closureB, weight );
						break;
					case EmissionClosureId :
						addEmission( pointIndex, closure->as_comp()->as<EmissionParameters>(), weight * closure->as_comp()->w );
						break;
					case DebugClosureId :
						addDebug( pointIndex, closure->as_comp()->as<DebugParameters>(), weight * closure->as_comp()->w );
						break;
				}
			}
		}

		void addEmission( size_t pointIndex, const EmissionParameters *parameters, const Color3f &weight )
		{
			(*m_ci)[pointIndex] += weight;
		}

		void addDebug( size_t pointIndex, const DebugParameters *parameters, const Color3f &weight )
		{
			vector<DebugResult>::iterator it = lower_bound(
				m_debugResults.begin(),
				m_debugResults.end(),
				parameters->name
			);

			if( it == m_debugResults.end() || it->name != parameters->name )
			{
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
				it = m_debugResults.insert( it, result );
			}

			Color3f value = weight * parameters->value;

			char *dst = static_cast<char *>( it->basePointer );
			dst += pointIndex * it->type.elementsize();
			ShadingSystem::convert_value(
				dst,
				it->type,
				&value,
				it->type.aggregate == TypeDesc::SCALAR ? TypeDesc::TypeFloat : TypeDesc::TypeColor
			);
		}

		/// \todo This is a lot like the UserData struct above - maybe we should
		/// just have one type we can use for both?
		struct DebugResult
		{
			DebugResult()
				:	basePointer( NULL )
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

		CompoundDataPtr m_results;
		vector<Color3f> *m_ci;
		vector<DebugResult> m_debugResults; // sorted on name for quick lookups

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

		OpenImageIOAlgo::DataView dataView( it->second.get() );
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
		return NULL;
	}
}

} // namespace

ShadingEngine::ShadingEngine( const IECore::ObjectVector *shaderNetwork )
{
	ShadingSystem *shadingSystem = ::shadingSystem();
	ShadingSystemWriteMutex::scoped_lock shadingSystemWriteLock( g_shadingSystemWriteMutex );

	m_shaderGroupRef = new ShaderGroupRef( shadingSystem->ShaderGroupBegin() );

		for( ObjectVector::MemberContainer::const_iterator it = shaderNetwork->members().begin(), eIt = shaderNetwork->members().end(); it != eIt; ++it )
		{
			const Shader *shader = runTimeCast<const Shader>( it->get() );
			if( !shader )
			{
				continue;
			}

			declareParameters( shader->parameters(), shadingSystem );
			const char *handle = NULL;
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
}

ShadingEngine::~ShadingEngine()
{
	delete static_cast<ShaderGroupRef *>( m_shaderGroupRef );
}

IECore::CompoundDataPtr ShadingEngine::shade( const IECore::CompoundData *points, const Transforms &transforms ) const
{
	// Get the data for "P" - this determines the number of points to be shaded.

	size_t numPoints = 0;

	const OSL::Vec3 *p = 0;
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
	shaderGlobals.renderstate = &renderState;

	// Get pointers to varying data, we'll use these to
	// update the shaderGlobals as we iterate over our points.

	const float *u = varyingValue<float>( points, "u" );
	const float *v = varyingValue<float>( points, "v" );
	const V3f *n = varyingValue<V3f>( points, "N" );

	/// \todo Get the other globals - match the uniform list

	// Allocate data for the result

	ShadingResults results( numPoints );

	// Iterate over the input points, doing the shading as we go

	ShadingSystem *shadingSystem = ::shadingSystem();
	ShadingContext *shadingContext = shadingSystem->get_context();
	ShaderGroup &shaderGroup = **static_cast<ShaderGroupRef *>( m_shaderGroupRef );
	for( size_t i = 0; i < numPoints; ++i )
	{
		shaderGlobals.P = *p++;
		if( u )
		{
			shaderGlobals.u = *u++;
		}
		if( v )
		{
			shaderGlobals.v = *v++;
		}
		if( n )
		{
			shaderGlobals.N = *n++;
		}

		shaderGlobals.Ci = NULL;

		shadingSystem->execute( shadingContext, shaderGroup, shaderGlobals );
		results.addResult( i, shaderGlobals.Ci );
		renderState.incrementPointIndex();
	}

	shadingSystem->release_context( shadingContext );

	return results.results();
}

