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

#include "boost/algorithm/string/split.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/classification.hpp"

#include "OSL/oslclosure.h"
#include "OSL/genclosure.h"
#include "OSL/oslversion.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

#include "GafferOSL/OSLRenderer.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace OSL;
using namespace GafferOSL;

//////////////////////////////////////////////////////////////////////////
// Utility for converting IECore::Data types to OSL::TypeDesc types.
//////////////////////////////////////////////////////////////////////////

TypeDesc::VECSEMANTICS vecSemanticsFromGeometricInterpretation( GeometricData::Interpretation interpretation )
{
	switch( interpretation )
	{
		case GeometricData::Point :
			return TypeDesc::POINT;
		case GeometricData::Normal :
			return TypeDesc::NORMAL;
		case GeometricData::Vector :
			return TypeDesc::VECTOR;
		case GeometricData::Color :
			return TypeDesc::COLOR;
		default :
			return TypeDesc::NOXFORM;
	}
}

GeometricData::Interpretation geometricInterpretationFromVecSemantics( TypeDesc::VECSEMANTICS semantics )
{
	switch( semantics )
	{
		case TypeDesc::NOXFORM :
			return GeometricData::Numeric;
		case TypeDesc::COLOR :
			return GeometricData::Color;
		case TypeDesc::POINT :
			return GeometricData::Point;
		case TypeDesc::VECTOR :
			return GeometricData::Vector;
		case TypeDesc::NORMAL :
			return GeometricData::Normal;
		default :
			return GeometricData::Numeric;
	}
}

TypeDesc typeDescFromData( const Data *data, const void *&basePointer )
{
	switch( data->typeId() )
	{
		// simple data
		
		case FloatDataTypeId :
			basePointer = static_cast<const FloatData *>( data )->baseReadable();
			return TypeDesc::TypeFloat;
		case IntDataTypeId :
			basePointer = static_cast<const IntData *>( data )->baseReadable();
			return TypeDesc::TypeInt;
		case V3fDataTypeId :
			basePointer = static_cast<const V3fData *>( data )->baseReadable();
			return TypeDesc(
				TypeDesc::FLOAT,
				TypeDesc::VEC3,
				vecSemanticsFromGeometricInterpretation( static_cast<const V3fData *>( data )->getInterpretation() )
			);
		case Color3fDataTypeId :
			basePointer = static_cast<const Color3fData *>( data )->baseReadable();
			return TypeDesc::TypeColor;
		case StringDataTypeId :					
			basePointer = &(static_cast<const StringData *>( data )->readable() );
			return TypeDesc::TypeString;
			
		// vector data
		
		case FloatVectorDataTypeId :
			basePointer = static_cast<const FloatVectorData *>( data )->baseReadable();
			return TypeDesc( TypeDesc::FLOAT, static_cast<const FloatVectorData *>( data )->readable().size() );
		case IntVectorDataTypeId :
			basePointer = static_cast<const IntVectorData *>( data )->baseReadable();
			return TypeDesc( TypeDesc::INT, static_cast<const IntVectorData *>( data )->readable().size() );
		case Color3fVectorDataTypeId :
			basePointer = static_cast<const Color3fVectorData *>( data )->baseReadable();
			return TypeDesc( TypeDesc::FLOAT, TypeDesc::VEC3, TypeDesc::COLOR, static_cast<const IntVectorData *>( data )->readable().size() );
			
		default :
			return TypeDesc();
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
	result->setInterpretation( geometricInterpretationFromVecSemantics( (TypeDesc::VECSEMANTICS)type.vecsemantics ) );
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

//////////////////////////////////////////////////////////////////////////
// OSLRenderer::RenderState
//////////////////////////////////////////////////////////////////////////

class OSLRenderer::RenderState
{
	
	public :
		
		RenderState( const IECore::CompoundData *shadingPoints )
			:	m_pointIndex( 0 )
		{
			for( CompoundDataMap::const_iterator it = shadingPoints->readable().begin(),
				 eIt = shadingPoints->readable().end(); it != eIt; ++it )
			{
				UserData userData;
				userData.typeDesc = typeDescFromData( it->second.get(), userData.basePointer );
				if( userData.basePointer )
				{
					userData.name = it->first;
					if( userData.typeDesc.arraylen )
					{
						// we unarray the TypeDesc so we can use it directly with
						// convert_value() in get_userdata().
						userData.typeDesc.unarray();
						userData.array = true;
					}
					m_userData.push_back( userData );
				}
			}
			
			sort( m_userData.begin(), m_userData.end() );
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
			
			const char *src = static_cast<const char *>( it->basePointer );
			if( it->array )
			{
				src += m_pointIndex * it->typeDesc.elementsize();
			}
			
			return ShadingSystem::convert_value( value, type, src, it->typeDesc );
		}
		
		void incrementPointIndex()
		{
			m_pointIndex++;
		}

	private :
			
		size_t m_pointIndex;
		
		struct UserData
		{
			UserData()
				:	basePointer( NULL ), array( false )
			{
			}
		
			ustring name;
			const void *basePointer;
			TypeDesc typeDesc;
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

//////////////////////////////////////////////////////////////////////////
// OSLRenderer::RendererServices
//////////////////////////////////////////////////////////////////////////

class OSLRenderer::RendererServices : public OSL::RendererServices
{

	public :
		
		RendererServices()
		{
		}
		
		virtual bool get_matrix( OSL::Matrix44 &result, TransformationPtr xform, float time )
		{
			return false;
		}

		virtual bool get_matrix( OSL::Matrix44 &result, TransformationPtr xform )
		{
			return false;		
		}

		virtual bool get_matrix( OSL::Matrix44 &result, ustring from, float time )
		{
			return false;
		}

		virtual bool get_matrix( OSL::Matrix44 &result, ustring from )
		{
			return false;
		}

		virtual bool get_attribute( void *renderState, bool derivatives, ustring object, TypeDesc type, ustring name, void *value )
		{
			if( !renderState )
			{
				return false;
			}
			// fall through to get_userdata - i'm not sure this is the intention of the osl spec, but how else can
			// a shader access a primvar by name? maybe i've overlooked something.
			return get_userdata( derivatives, name, type, renderState, value );
		}

		virtual bool get_array_attribute( void *renderState, bool derivatives, ustring object, TypeDesc type, ustring name, int index, void *value )
		{
			return false;
		}

		virtual bool get_userdata( bool derivatives, ustring name, TypeDesc type, void *rState, void *value )
		{
			if( !rState )
			{
				return false;
			}
			const RenderState *renderState = static_cast<RenderState *>( rState );
			return renderState->userData( name, type, value );
		}

		virtual bool has_userdata( ustring name, TypeDesc type, void *rState )
		{
			if( !rState )
			{
				return false;
			}
			const RenderState *renderState = static_cast<RenderState *>( rState );
			return renderState->userData( name, type, NULL );
		}

};

//////////////////////////////////////////////////////////////////////////
// OSLRenderer::State
//////////////////////////////////////////////////////////////////////////

OSLRenderer::State::State()
	:	surfaceShader( new IECore::Shader( "surface", "defaultsurface" ) )
{
}

OSLRenderer::State::State( const State &other )
	:	shaders( other.shaders ), surfaceShader( other.surfaceShader )
{
}

OSLRenderer::State::~State()
{
}

//////////////////////////////////////////////////////////////////////////
// OSLRenderer
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( OSLRenderer );

struct OSLRenderer::EmissionParameters
{
};

struct OSLRenderer::DebugParameters
{
	ustring name;
};

OSLRenderer::OSLRenderer()
	:	m_shadingSystem( ShadingSystem::create( new OSLRenderer::RendererServices ), ShadingSystem::destroy )
{
	struct ClosureDefinition{
		const char *name;
		int id;
		ClosureParam parameters[32];
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
				CLOSURE_STRING_KEYPARAM( "type" ),
				CLOSURE_FINISH_PARAM( DebugParameters )
			}
		},
		// end marker
		{ NULL, 0, {} }
	};
	
	for( int i = 0; closureDefinitions[i].name; ++i )
	{
		m_shadingSystem->register_closure(
			closureDefinitions[i].name,
			closureDefinitions[i].id,
			closureDefinitions[i].parameters,
			NULL,
			NULL
#if OSL_LIBRARY_VERSION_MAJOR == 1 && OSL_LIBRARY_VERSION_MINOR <= 4
			,NULL
#endif
		);
	}
}

OSLRenderer::~OSLRenderer()
{
}

void OSLRenderer::setOption( const std::string &name, IECore::ConstDataPtr value )
{
	if( boost::starts_with( name, "osl:" ) )
	{
		const void *data = 0;
		TypeDesc typeDesc = typeDescFromData( value.get(), data );
		if( data )
		{
			m_shadingSystem->attribute( name.c_str() + 4, typeDesc, data );
		}
		else
		{
			msg( Msg::Warning, "OSLRenderer::setOption", boost::format( "Option \"%s\" has unsupported type \"%s\"" ) % name % value->typeName() );
		}
	}
	else if( boost::starts_with( name, "user:" ) || name.find( ':' ) == string::npos )
	{
		msg( Msg::Warning, "OSLRenderer::setOption", boost::format( "Unsupported option \"%s\"" ) % name );		
	}
	else
	{
		// option is for another renderer and can be ignored.	
	}
}

IECore::ConstDataPtr OSLRenderer::getOption( const std::string &name ) const
{
	return NULL;
}

void OSLRenderer::camera( const std::string &name, const IECore::CompoundDataMap &parameters )
{
}

void OSLRenderer::display( const std::string &name, const std::string &type, const std::string &data, const IECore::CompoundDataMap &parameters )
{
}

void OSLRenderer::worldBegin()
{
	if( m_stateStack.size() )
	{
		msg( Msg::Warning, "OSLRenderer::worldBegin", "Bad nesting" );				
		return;
	}
	m_stateStack.push( State() );
}

void OSLRenderer::worldEnd()
{
	if( m_stateStack.size() != 1 )
	{
		msg( Msg::Warning, "OSLRenderer::worldEnd", "Bad nesting" );					
		return;
	}
	m_stateStack.pop();
}

void OSLRenderer::transformBegin()
{
}

void OSLRenderer::transformEnd()
{
}

void OSLRenderer::setTransform( const Imath::M44f &m )
{
}

void OSLRenderer::setTransform( const std::string &coordinateSystem )
{
}

Imath::M44f OSLRenderer::getTransform() const
{
	return M44f();
}

Imath::M44f OSLRenderer::getTransform( const std::string &coordinateSystem ) const
{
	return M44f();
}

void OSLRenderer::concatTransform( const Imath::M44f &m )
{
}

void OSLRenderer::coordinateSystem( const std::string &name )
{
}

void OSLRenderer::attributeBegin()
{
	if( !m_stateStack.size() )
	{
		msg( Msg::Warning, "OSLRenderer::attributeBegin", "Not in world block" );					
		return;
	}
	m_stateStack.push( State( m_stateStack.top() ) );
}

void OSLRenderer::attributeEnd()
{
	if( !m_stateStack.size() )
	{
		msg( Msg::Warning, "OSLRenderer::attributeEnd", "Bad nesting" );					
		return;
	}
	m_stateStack.pop();
}

void OSLRenderer::setAttribute( const std::string &name, IECore::ConstDataPtr value )
{
}

IECore::ConstDataPtr OSLRenderer::getAttribute( const std::string &name ) const
{
	return NULL;
}

void OSLRenderer::shader( const std::string &type, const std::string &name, const IECore::CompoundDataMap &parameters )
{
	if( type=="surface" || type=="osl:surface" )
	{
		m_stateStack.top().surfaceShader = new Shader( name, "surface", parameters );
	}
	else if( type=="shader" || type=="osl:shader" )
	{
		m_stateStack.top().shaders.push_back( new Shader( name, "shader", parameters ) );
	}
	else if( type.find( "osl:" ) == 0 || type.find_first_of( ":" ) == string::npos )
	{
		msg( Msg::Warning, "OSLRenderer::shader", boost::format( "Unsupported shader type \"%s\"." ) % type );	
	}	
}

void OSLRenderer::light( const std::string &name, const std::string &handle, const IECore::CompoundDataMap &parameters )
{
}

void OSLRenderer::illuminate( const std::string &lightHandle, bool on )
{
}

void OSLRenderer::motionBegin( const std::set<float> &times )
{
}

void OSLRenderer::motionEnd()
{
}

void OSLRenderer::points( size_t numPoints, const IECore::PrimitiveVariableMap &primVars )
{
}

void OSLRenderer::disk( float radius, float z, float thetaMax, const IECore::PrimitiveVariableMap &primVars )
{
}

void OSLRenderer::curves( const IECore::CubicBasisf &basis, bool periodic, IECore::ConstIntVectorDataPtr numVertices, const IECore::PrimitiveVariableMap &primVars )
{
}

void OSLRenderer::text( const std::string &font, const std::string &text, float kerning, const IECore::PrimitiveVariableMap &primVars )
{
}

void OSLRenderer::sphere( float radius, float zMin, float zMax, float thetaMax, const IECore::PrimitiveVariableMap &primVars )
{
}

void OSLRenderer::image( const Imath::Box2i &dataWindow, const Imath::Box2i &displayWindow, const IECore::PrimitiveVariableMap &primVars )
{
}

void OSLRenderer::mesh( IECore::ConstIntVectorDataPtr vertsPerFace, IECore::ConstIntVectorDataPtr vertIds, const std::string &interpolation, const IECore::PrimitiveVariableMap &primVars )
{
}

void OSLRenderer::nurbs( int uOrder, IECore::ConstFloatVectorDataPtr uKnot, float uMin, float uMax, int vOrder, IECore::ConstFloatVectorDataPtr vKnot, float vMin, float vMax, const IECore::PrimitiveVariableMap &primVars )
{
}

void OSLRenderer::patchMesh( const IECore::CubicBasisf &uBasis, const IECore::CubicBasisf &vBasis, int nu, bool uPeriodic, int nv, bool vPeriodic, const IECore::PrimitiveVariableMap &primVars )
{
}

void OSLRenderer::geometry( const std::string &type, const IECore::CompoundDataMap &topology, const IECore::PrimitiveVariableMap &primVars )
{
}

void OSLRenderer::procedural( IECore::Renderer::ProceduralPtr proc )
{
}

void OSLRenderer::instanceBegin( const std::string &name, const IECore::CompoundDataMap &parameters )
{
}

void OSLRenderer::instanceEnd()
{
}

void OSLRenderer::instance( const std::string &name )
{
}

IECore::DataPtr OSLRenderer::command( const std::string &name, const IECore::CompoundDataMap &parameters )
{
	return NULL;
}

void OSLRenderer::editBegin( const std::string &editType, const IECore::CompoundDataMap &parameters )
{
}

void OSLRenderer::editEnd()
{
}

static void declareParameters( const CompoundDataMap &parameters, ShadingSystem *shadingSystem )
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
		
		const void *basePointer = 0;
		const TypeDesc typeDesc = typeDescFromData( it->second.get(), basePointer );
		if( basePointer )
		{
			shadingSystem->Parameter( it->first.c_str(), typeDesc, basePointer );
		}
		else
		{
			msg( Msg::Warning, "OSLRenderer", boost::format( "Parameter \"%s\" has unsupported type \"%s\"" ) % it->first.string() % it->second->typeName() );
		}
	}
}

static void declareConnections( const std::string &shaderHandle, const CompoundDataMap &parameters, ShadingSystem *shadingSystem )
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
				msg( Msg::Warning, "OSLRenderer", boost::format( "Parameter \"%s\" has unexpected value \"%s\" - expected value of the form \"link:sourceShader.sourceParameter" ) % it->first.string() % value );
				continue;
			}
			
			shadingSystem->ConnectShaders(
				splitValue[0].c_str() + 5, splitValue[1].c_str(),
				shaderHandle.c_str(), it->first.c_str()
			);
		}
	}	
}
						
OSLRenderer::ShadingEnginePtr OSLRenderer::shadingEngine() const
{
	const State &state = m_stateStack.top();

	m_shadingSystem->ShaderGroupBegin();

		for( vector<ConstShaderPtr>::const_iterator it = state.shaders.begin(), eIt = state.shaders.end(); it != eIt; ++it )
		{
			declareParameters( (*it)->parameters(), m_shadingSystem.get() );
			const StringData *handle = (*it)->parametersData()->member<StringData>( "__handle" );
			m_shadingSystem->Shader( "surface", (*it)->getName().c_str(), handle ? handle->readable().c_str() : NULL  );
			if( handle )
			{
				declareConnections( handle->readable(), (*it)->parameters(), m_shadingSystem.get() );
			}
		}

		declareParameters( state.surfaceShader->parameters(), m_shadingSystem.get() );
		m_shadingSystem->Shader( "surface", state.surfaceShader->getName().c_str(), "oslRenderer:surface" );
		declareConnections( "oslRenderer:surface", state.surfaceShader->parameters(), m_shadingSystem.get() );

	m_shadingSystem->ShaderGroupEnd();

	return new ShadingEngine( this, m_shadingSystem->state() );
}

//////////////////////////////////////////////////////////////////////////
// OSLRenderer::ShadingResults
//////////////////////////////////////////////////////////////////////////

class OSLRenderer::ShadingResults
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
				switch( closure->type )
				{
					case ClosureColor::COMPONENT :
					{
						const ClosureComponent *closureComponent = static_cast<const ClosureComponent*>( closure );
						Color3f closureWeight = weight;
#ifdef OSL_SUPPORTS_WEIGHTED_CLOSURE_COMPONENTS
						closureWeight *= closureComponent->w;
#endif						
						switch( closureComponent->id )
						{
							case EmissionClosureId :
								addEmission( pointIndex, closureComponent, closureWeight );
								break;
							case DebugClosureId :
								addDebug( pointIndex, closureComponent, closureWeight );
								break;
						}
						break;
					}
					case ClosureColor::MUL :
						addResult(
							pointIndex,
							static_cast<const ClosureMul *>( closure )->closure,
							weight * static_cast<const ClosureMul *>( closure )->weight
						);
						break;
					case ClosureColor::ADD :
						addResult( pointIndex, static_cast<const ClosureAdd *>( closure )->closureA, weight );
						addResult( pointIndex, static_cast<const ClosureAdd *>( closure )->closureB, weight );
						break;
				}
			}
		}
		
		void addEmission( size_t pointIndex, const ClosureComponent *closure, const Color3f &weight )
		{
			(*m_ci)[pointIndex] += weight;
		}
		
		void addDebug( size_t pointIndex, const ClosureComponent *closure, const Color3f &weight )
		{
			const DebugParameters *parameters = static_cast<const DebugParameters *>( closure->data() );
			vector<DebugResult>::iterator it = lower_bound(
				m_debugResults.begin(),
				m_debugResults.end(),
				parameters->name
			);
			
			if( it == m_debugResults.end() || it->name != parameters->name )
			{
				DebugResult result;
				result.name = parameters->name;
				result.type = TypeDesc::TypeColor;
				if( closure->nattrs )
				{
					result.type = TypeDesc( closure->attrs()[0].str().c_str() );
				}
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
			
			char *dst = static_cast<char *>( it->basePointer );
			dst += pointIndex * it->type.elementsize();
			ShadingSystem::convert_value(
				dst,
				it->type,
				&weight,
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

//////////////////////////////////////////////////////////////////////////
// OSLRenderer::ShadingEngine
//////////////////////////////////////////////////////////////////////////

OSLRenderer::ShadingEngine::ShadingEngine( ConstOSLRendererPtr renderer, OSL::ShadingAttribStateRef shadingState )
	:	m_renderer( renderer ), m_shadingState( shadingState )
{
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

IECore::CompoundDataPtr OSLRenderer::ShadingEngine::shade( const IECore::CompoundData *points ) const
{
	// get the data for "P" - this determines the number of points to be shaded.
	
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
	
	// create ShaderGlobals, and fill it with any uniform values that have
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
	
	// add a RenderState to the ShaderGlobals. this will
	// get passed to our RendererServices queries.
	
	RenderState renderState( points );
	shaderGlobals.renderstate = &renderState;
	
	// get pointers to varying data, we'll use these to
	// update the shaderGlobals as we iterate over our points.
	
	const float *u = varyingValue<float>( points, "u" );
	const float *v = varyingValue<float>( points, "v" );
	const V3f *n = varyingValue<V3f>( points, "N" );
		
	/// \todo Get the other globals - match the uniform list
	
	// allocate data for the result
	
	ShadingResults results( numPoints );
	
	// iterate over the input points, doing the shading as we go

	ShadingContext *shadingContext = m_renderer->m_shadingSystem->get_context();
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
		
		m_renderer->m_shadingSystem->execute( *shadingContext, *m_shadingState, shaderGlobals );
		results.addResult( i, shaderGlobals.Ci );
		renderState.incrementPointIndex();
	}
	
	m_renderer->m_shadingSystem->release_context( shadingContext );
	
	return results.results();
}
