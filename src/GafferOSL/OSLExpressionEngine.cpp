//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "boost/regex.hpp"
#include "boost/algorithm/string/replace.hpp"
#include "boost/lexical_cast.hpp"

#include "OpenImageIO/errorhandler.h"

#include "OSL/oslcomp.h"
#include "OSL/oslexec.h"

#include "Gaffer/Expression.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringAlgo.h"
#include "Gaffer/Context.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/StringPlug.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace OSL;
using namespace IECore;
using namespace Gaffer;

// We require features from OSL 1.6.8, and if that is not available
// we simply don't build OSLExpressionEngine at all.
#if OSL_LIBRARY_VERSION_CODE >= 10608

namespace
{

//////////////////////////////////////////////////////////////////////////
// Error handler. We use this to capture error messages when
// compiling the OSL shader.
//////////////////////////////////////////////////////////////////////////

class CapturingErrorHandler : public OIIO::ErrorHandler
{

	public :

		CapturingErrorHandler()
		{
		}

		virtual void operator()( int errorCode, const std::string &message )
		{
			if( errorCode >= EH_ERROR )
			{
				if( m_errors.size() && *m_errors.rbegin() != '\n' )
				{
					m_errors += "\n";
				}
				m_errors += message;
			}
		}

		const std::string &errors()
		{
			return m_errors;
		}

	private :

		string m_errors;

};

//////////////////////////////////////////////////////////////////////////
// RenderState. OSL would think of this as representing the object
// currently being shaded, encoding information about primitive variables
// and attributes. But we use it to represent the evaluation context for
// an expression, encoding information about input plugs and context
// variables.
//////////////////////////////////////////////////////////////////////////

struct RenderState
{

	const vector<ustring> *inParameters;
	const Gaffer::Context *context;
	const vector<const Gaffer::ValuePlug *> *inPlugs;

};

//////////////////////////////////////////////////////////////////////////
// RendererServices. OSL uses this class to query information from
// our RenderState.
//////////////////////////////////////////////////////////////////////////

/// \todo Share with OSLRenderer

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

/// \todo Share with OSLRenderer and GafferImage. Perhaps this and the above
/// should actually be provided by GafferImage?

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
		case V3fVectorDataTypeId :
			basePointer = static_cast<const V3fVectorData *>( data )->baseReadable();
			return TypeDesc(
				TypeDesc::FLOAT,
				TypeDesc::VEC3,
				vecSemanticsFromGeometricInterpretation( static_cast<const V3fVectorData *>( data )->getInterpretation() ),
				static_cast<const V3fVectorData *>( data )->readable().size()
			);
		case Color3fVectorDataTypeId :
			basePointer = static_cast<const Color3fVectorData *>( data )->baseReadable();
			return TypeDesc( TypeDesc::FLOAT, TypeDesc::VEC3, TypeDesc::COLOR, static_cast<const IntVectorData *>( data )->readable().size() );

		default :
			return TypeDesc();
	}
};

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

			const Data *data = renderState->context->get<Data>( name.c_str(), NULL );
			if( !data )
			{
				return false;
			}

			const void *contextValuePointer = NULL;
			TypeDesc contextType = typeDescFromData( data, contextValuePointer );
			if( !contextValuePointer )
			{
				return false;
			}
			return ShadingSystem::convert_value( value, type, contextValuePointer, contextType );
		}

		virtual bool get_array_attribute( OSL::ShaderGlobals *sg, bool derivatives, ustring object, TypeDesc type, ustring name, int index, void *value )
		{
			return false;
		}

		// OSL tries to populate shader parameter values per-object by calling this method.
		// So we implement it to search for an appropriate input plug and get its value.
		virtual bool get_userdata( bool derivatives, ustring name, TypeDesc type, OSL::ShaderGlobals *sg, void *value )
		{
			const RenderState *renderState = sg ? static_cast<RenderState *>( sg->renderstate ) : NULL;
			if( !renderState )
			{
				return false;
			}
			vector<ustring>::const_iterator it = find( renderState->inParameters->begin(), renderState->inParameters->end(), name );
			if( it == renderState->inParameters->end() )
			{
				return false;
			}

			if( value )
			{
				const size_t index = it - renderState->inParameters->begin();
				const ValuePlug *plug = (*renderState->inPlugs)[index];
				switch( (Gaffer::TypeId)plug->typeId() )
				{
					case BoolPlugTypeId :
						*(int *)value = static_cast<const BoolPlug *>( plug )->getValue();
						return true;
					case FloatPlugTypeId :
						*(float *)value = static_cast<const FloatPlug *>( plug )->getValue();
						return true;
					case IntPlugTypeId :
						*(int *)value = static_cast<const IntPlug *>( plug )->getValue();
						return true;
					case Color3fPlugTypeId :
						*(Color3f *)value = static_cast<const Color3fPlug *>( plug )->getValue();
						return true;
					case V3fPlugTypeId :
						*(V3f *)value = static_cast<const V3fPlug *>( plug )->getValue();
						return true;
					case StringPlugTypeId :
					{
						InternedString s = static_cast<const StringPlug *>( plug )->getValue();
						*(const char **)value = s.c_str();
						return true;
					}
					default :
						return false;
				}
			}
			return false;
		}

		virtual bool has_userdata( ustring name, TypeDesc type, OSL::ShaderGlobals *sg )
		{
			return get_userdata( false, name, type, sg, NULL );
		}

};

//////////////////////////////////////////////////////////////////////////
// OSLExpressionEngine
//////////////////////////////////////////////////////////////////////////

class OSLExpressionEngine : public Gaffer::Expression::Engine
{

	public :

		IE_CORE_DECLAREMEMBERPTR( OSLExpressionEngine );

		OSLExpressionEngine()
		{
		}

		virtual void parse( Expression *node, const std::string &expression, std::vector<ValuePlug *> &inputs, std::vector<ValuePlug *> &outputs, std::vector<IECore::InternedString> &contextVariables )
		{
			m_inParameters.clear();
			m_outSymbols.clear();
			m_shaderGroup.reset();

			// Find all references to plugs within the expression.
			vector<string> inPlugPaths;
			vector<string> outPlugPaths;
			findPlugPaths( expression, inPlugPaths, outPlugPaths );

			// Find the plugs from their paths, and fill inputs and outputs appropriately.
			for( vector<string>::const_iterator it = inPlugPaths.begin(), eIt = inPlugPaths.end(); it != eIt; ++it )
			{
				inputs.push_back( plug( node, *it ) );
			}
			for( vector<string>::const_iterator it = outPlugPaths.begin(), eIt = outPlugPaths.end(); it != eIt; ++it )
			{
				outputs.push_back( plug( node, *it ) );
			}

			// Create the source code for an OSL shader containing our expression.
			// This will also generate a shader name and parameter names for each
			// of the referenced plug paths. We store the parameter names for use
			// in execute().
			string shaderName;
			vector<ustring> outParameters;
			const string source = shaderSource( expression, inPlugPaths, inputs, outPlugPaths, outputs, shaderName, m_inParameters, outParameters );

			// Create a shader group from the source. We'll use this in execute() to execute the expression.

			m_shaderGroup = shaderGroup( shaderName, source, outParameters );

			// Build the list of all context queries the shader performs.
			// These arrive in the form of getattribute() calls and reads
			// from the global time variable.

			OSL::ShadingSystem *shadingSys = shadingSystem();

			int unknownAttributes = 0;
			shadingSys->getattribute( m_shaderGroup.get(), "unknown_attributes_needed", unknownAttributes );
			if( unknownAttributes )
			{
				throw IECore::Exception( "Unknown attributes requested" );
			}

			int numAttributes = 0;
			shadingSys->getattribute( m_shaderGroup.get(), "num_attributes_needed", numAttributes );
			if( numAttributes )
			{
				ustring *attributeNames = NULL;
				ustring *scopeNames = NULL;
				shadingSys->getattribute( m_shaderGroup.get(), "attributes_needed", TypeDesc::PTR, &attributeNames );
				shadingSys->getattribute( m_shaderGroup.get(), "attribute_scopes", TypeDesc::PTR, &scopeNames );
				for( int i = 0; i < numAttributes; ++i )
				{
					if( scopeNames[i] != "gaffer:context" )
					{
						throw IECore::Exception( "Unsupported attribute requested" );
					}
					contextVariables.push_back( attributeNames[i].c_str() );
				}
			}

			int numGlobals = 0;
			shadingSys->getattribute( m_shaderGroup.get(), "num_globals_needed", numGlobals );
			if( numGlobals )
			{
				ustring *globalNames = NULL;
				shadingSys->getattribute( m_shaderGroup.get(), "globals_needed", TypeDesc::PTR, &globalNames );
				for( int i = 0; i < numGlobals; ++i )
				{
					if( globalNames[i] == "time" )
					{
						contextVariables.push_back( "frame" );
						contextVariables.push_back( "framesPerSecond" );
						break;
					}
				}
			}

			// Grab the symbols for each of the output parameters so we can
			// query their values in execute().
			for( vector<ustring>::const_iterator it = outParameters.begin(), eIt = outParameters.end(); it != eIt; ++it )
			{
				m_outSymbols.push_back( shadingSys->find_symbol( *m_shaderGroup, *it ) );
			}

		}

		virtual IECore::ConstObjectVectorPtr execute( const Gaffer::Context *context, const std::vector<const Gaffer::ValuePlug *> &proxyInputs ) const
		{
			ShadingSystem *s = shadingSystem();
			OSL::ShadingContext *shadingContext = s->get_context();

		    OSL::ShaderGlobals shaderGlobals;
			memset( &shaderGlobals, 0, sizeof( ShaderGlobals ) );

			shaderGlobals.time = context->getTime();

			RenderState renderState;
			renderState.inParameters = &m_inParameters;
			renderState.context = context;
			renderState.inPlugs = &proxyInputs;
			shaderGlobals.renderstate = &renderState;

			s->execute( *shadingContext, *m_shaderGroup, shaderGlobals );

			ObjectVectorPtr result = new ObjectVector;
			result->members().reserve( m_outSymbols.size() );

			for( vector<const OSL::ShaderSymbol *>::const_iterator it = m_outSymbols.begin(), eIt = m_outSymbols.end(); it != eIt; ++it )
			{
				const TypeDesc type = s->symbol_typedesc( *it );
				const void *storage = s->symbol_address( *shadingContext, *it );
				if( type == TypeDesc::TypeFloat )
				{
					result->members().push_back( new FloatData( *(const float *)storage ) );
				}
				else if( type == TypeDesc::TypeInt )
				{
					result->members().push_back( new IntData( *(const int *)storage ) );
				}
				else if( type == TypeDesc::TypeColor )
				{
					const float *f = (const float *)storage;
					result->members().push_back( new Color3fData( Color3f( f[0], f[1], f[2] ) ) );
				}
				else if( type == TypeDesc::TypeVector )
				{
					const float *f = (const float *)storage;
					result->members().push_back( new V3fData( V3f( f[0], f[1], f[2] ) ) );
				}
				else if( type == TypeDesc::TypeString )
				{
					result->members().push_back( new StringData( *(const char **)storage ) );
				}
			}

			s->release_context( shadingContext );
			return result;
		}

		virtual void apply( Gaffer::ValuePlug *proxyOutput, const Gaffer::ValuePlug *topLevelProxyOutput, const IECore::Object *value ) const
		{
			switch( value->typeId() )
			{
				case FloatDataTypeId :
					static_cast<FloatPlug *>( proxyOutput )->setValue( static_cast<const FloatData *>( value )->readable() );
					break;
				case IntDataTypeId :
					if( IntPlug *intPlug = runTimeCast<IntPlug>( proxyOutput ) )
					{
						intPlug->setValue( static_cast<const IntData *>( value )->readable() );
					}
					else
					{
						static_cast<BoolPlug *>( proxyOutput )->setValue( static_cast<const IntData *>( value )->readable() );
					}
					break;
				case Color3fDataTypeId :
				{
					Color3fPlug *colorPlug = proxyOutput->parent<Color3fPlug>();
					for( int i = 0; i < 3; ++i )
					{
						if( proxyOutput == colorPlug->getChild( i ) )
						{
							static_cast<FloatPlug *>( proxyOutput )->setValue( static_cast<const Color3fData *>( value )->readable()[i] );
							break;
						}
					}
					break;
				}
				case V3fDataTypeId :
				{
					V3fPlug *vectorPlug = proxyOutput->parent<V3fPlug>();
					for( int i = 0; i < 3; ++i )
					{
						if( proxyOutput == vectorPlug->getChild( i ) )
						{
							static_cast<FloatPlug *>( proxyOutput )->setValue( static_cast<const V3fData *>( value )->readable()[i] );
							break;
						}
					}
					break;
				}
				case StringDataTypeId :
					static_cast<StringPlug *>( proxyOutput )->setValue( static_cast<const StringData *>( value )->readable() );
					break;
				default :
					// Shouldn't get here, as we've handled all the types
					// that parse() and execute() will accept.
					assert( false );
			}
		}

		virtual std::string identifier( const Expression *node, const ValuePlug *plug ) const
		{
			switch( (Gaffer::TypeId)plug->typeId() )
			{
				case BoolPlugTypeId :
				case FloatPlugTypeId :
				case IntPlugTypeId :
				case Color3fPlugTypeId :
				case V3fPlugTypeId :
				case StringPlugTypeId :
					break;
				default :
					return ""; // Unsupported plug type
			}

			string relativeName;
			if( node->isAncestorOf( plug ) )
			{
				relativeName = plug->relativeName( node );
			}
			else
			{
				relativeName = plug->relativeName( node->parent<Node>() );
			}

			return "parent." + relativeName;
		}

		virtual std::string replace( const Expression *node, const std::string &expression, const std::vector<const ValuePlug *> &oldPlugs, const std::vector<const ValuePlug *> &newPlugs ) const
		{
			string result = expression;
			vector<const ValuePlug *>::const_iterator newIt = newPlugs.begin();
			for( vector<const ValuePlug *>::const_iterator oldIt = oldPlugs.begin(), oldEIt = oldPlugs.end(); oldIt != oldEIt; ++oldIt, ++newIt )
			{
				std::string replacement;
				if( *newIt )
				{
					replacement = identifier( node, *newIt );
				}
				else
				{
					string defaultValue;
					string type = parameterType( *oldIt, defaultValue );
					if( (*oldIt)->direction() == Plug::In )
					{
						replacement = defaultValue;
					}
					else
					{
						type[0] = toupper( type[0] );
						replacement = "_disconnected" + type;
					}
				}
				replace_all( result, identifier( node, *oldIt ), replacement );
			}

			return result;
		}

		virtual std::string defaultExpression( const ValuePlug *output ) const
		{
			const Node *parentNode = output->node() ? output->node()->ancestor<Node>() : NULL;
			if( !parentNode )
			{
				return "";
			}

			string value;
			switch( (Gaffer::TypeId)output->typeId() )
			{
				case BoolPlugTypeId :
					value = lexical_cast<string>( static_cast<int>( static_cast<const BoolPlug *>( output )->getValue() ) );
					break;
				case FloatPlugTypeId :
					value = lexical_cast<string>( static_cast<const FloatPlug *>( output )->getValue() );
					break;
				case IntPlugTypeId :
					value = lexical_cast<string>( static_cast<const IntPlug *>( output )->getValue() );
					break;
				case Color3fPlugTypeId :
				{
					const Color3f c = static_cast<const Color3fPlug *>( output )->getValue();
					value = boost::str( boost::format( "color( %f, %f, %f )" ) % c[0] % c[1] % c[2] );
					break;
				}
				case V3fPlugTypeId :
				{
					const V3f v = static_cast<const V3fPlug *>( output )->getValue();
					value = boost::str( boost::format( "vector( %f, %f, %f )" ) % v[0] % v[1] % v[2] );
					break;
				}
				case StringPlugTypeId :
					value = '"' + static_cast<const StringPlug *>( output )->getValue() + '"';
					break;
				default :
					return ""; // unsupported plug type
			}

			return "parent." + output->relativeName( parentNode ) + " = " + value + ";";
		}

	private :

		static EngineDescription<OSLExpressionEngine> g_engineDescription;

		static OSL::ShadingSystem *shadingSystem()
		{
			static OSL::ShadingSystem *g_s = NULL;
			if( !g_s )
			{
				g_s = ShadingSystem::create( new RendererServices );
				// All our shader parameters are for getting values from
				// plugs, so we must turn off lockgeom so their values are
				// queried from RendererServices::get_userdata().
				g_s->attribute( "lockgeom", 0 );
			}
			return g_s;
		};

		static void findPlugPaths( const string &expression, vector<string> &inPaths, vector<string> &outPaths )
		{
			set<string> visited;
			const regex plugPathRegex( "(parent\\.[A-Za-z_0-9\\.]+)[ \t]*(=?)" );
			for( sregex_iterator it = make_regex_iterator( expression, plugPathRegex ); it != sregex_iterator(); ++it )
			{
				string plugPath( (*it)[1].str().substr( 7 ) );
				if( !visited.insert( plugPath ).second )
				{
					// seen this one before
					continue;
				}

				if( (*it)[2] == "=" )
				{
					outPaths.push_back( plugPath );
				}
				else
				{
					inPaths.push_back( plugPath );
				}
			}
		}

		static ValuePlug *plug( Expression *node, const std::string &plugPath )
		{
			Node *plugScope = node->parent<Node>();
			GraphComponent *descendant = plugScope->descendant<GraphComponent>( plugPath );
			if( !descendant )
			{
				throw IECore::Exception( boost::str( boost::format( "\"%s\" does not exist" ) % plugPath ) );
			}

			ValuePlug *result = runTimeCast<ValuePlug>( descendant );
			if( !result )
			{
				throw IECore::Exception( boost::str( boost::format( "\"%s\" is not a ValuePlug" ) % plugPath ) );
			}

			return result;
		}

		static string parameterType( const ValuePlug *plug, string &defaultValue )
		{
			switch( (Gaffer::TypeId)plug->typeId() )
			{
				case BoolPlugTypeId :
					defaultValue = "0";
					return "int";
				case FloatPlugTypeId :
					defaultValue = "0.0";
					return "float";
				case IntPlugTypeId :
					defaultValue = "0";
					return "int";
				case Color3fPlugTypeId :
					defaultValue = "color( 0.0 )";
					return "color";
				case V3fPlugTypeId :
					defaultValue = "vector( 0.0 )";
					return "vector";
				case StringPlugTypeId :
					defaultValue = "\"\"";
					return "string";
				default :
					throw Exception( string( "Unsupported plug type \"" ) + plug->typeName() + "\"" );
			}
		}

		static string shaderSource(
			const std::string &expression,
			const vector<string> &inPlugPaths, const vector<ValuePlug *> &inPlugs,
			const vector<string> &outPlugPaths, const vector<ValuePlug *> outPlugs,
			std::string &shaderName,
			vector<ustring> &inParameters,
			vector<ustring> &outParameters
		)
		{
			// Start by declaring the shader parameters - these are defined by the
			// input and output plugs. We'll come back later to prepend includes and
			// the shader name, because we want to include a hash of the shader source
			// in the name itself, to keep the names we give to OSL unique.
			string result = "(\n\n";

			for( int i = 0, e = inPlugPaths.size(); i < e; ++i )
			{
				string defaultValue;
				string type = parameterType( inPlugs[i], defaultValue );
				result += "\t" + type + " parent." + inPlugPaths[i] + " = " + defaultValue + ",\n";
			}

			result += "\n";

			for( int i = 0, e = outPlugPaths.size(); i < e; ++i )
			{
				string defaultValue;
				string type = parameterType( outPlugs[i], defaultValue );
				result += "\toutput " + type + " parent." + outPlugPaths[i] + " = " + defaultValue + ",\n";
			}

			result += "\n\t// Dummy parameters we can use as outputs when connections\n";
			result += "\t// are broken and we must keep the expression valid.\n";
			result += "\toutput float _disconnectedFloat = 0.0,\n";
			result += "\toutput int _disconnectedInt = 0,\n";
			result += "\toutput color _disconnectedColor = color( 0.0 ),\n";
			result += "\toutput color _disconnectedVector = vector( 0.0 ),\n";
			result += "\toutput string _disconnectedString = \"\",\n";

			result += "\n)\n";

			// Add on a shader body consisting of the expression itself.

			result += "{\n" + expression;

			if( expression.size() && expression[expression.size()-1] != ';' )
			{
				result += ";";
			}

			result += "\n}\n";

			// Up to this point, our plug references are of the form parent.node.plug,
			// but we want OSL just to see a flat list of parameters. So we must rename
			// the parameters and the references to them.

			for( int i = 0, e = inPlugPaths.size(); i < e; ++i )
			{
				string parameter = "_" + inPlugPaths[i];
				replace_all( parameter, ".", "_" );
				replace_all( result, "parent." + inPlugPaths[i], parameter );
				inParameters.push_back( ustring( parameter ) );
			}

			for( int i = 0, e = outPlugPaths.size(); i < e; ++i )
			{
				string parameter = "_" + outPlugPaths[i];
				replace_all( parameter, ".", "_" );
				replace_all( result, "parent." + outPlugPaths[i], parameter );
				outParameters.push_back( ustring( parameter ) );
			}

			// Now we can generate our unique shader name based on the source, and
			// prepend it to the source.

			shaderName = "oslExpression" + MurmurHash().append( result ).toString();
 			result = "#include \"GafferOSL/Expression.h\"\n\nshader " + shaderName + " " + result;

			return result;
		}

		static OSL::ShaderGroupRef shaderGroup( const string &shaderName, const string &shaderSource, const vector<ustring> &outParameters )
		{

			// If we've already generated this shader group, then
			// just return it. OSL won't let us load the same shader
			// again via LoadMemoryCompiledShader anyway.

			typedef map<string, OSL::ShaderGroupRef> ShaderGroups;
			static ShaderGroups g_shaderGroups;
			const ShaderGroups::const_iterator it = g_shaderGroups.find( shaderName );
			if( it != g_shaderGroups.end() )
			{
				return it->second;
			}

			// Compile the shader source into an in-memory oso buffer.

			CapturingErrorHandler errorHandler;
			OSLCompiler compiler( &errorHandler );

			vector<string> options;
			if( const char *includePaths = getenv( "OSL_SHADER_PATHS" ) )
			{
				tokenize( includePaths, ':', options );
				for( vector<string>::iterator it = options.begin(), eIt = options.end(); it != eIt; ++it )
				{
					it->insert( 0, "-I" );
				}
			}

			string oso;
			if( !compiler.compile_buffer( shaderSource, oso, options ) )
			{
				if( errorHandler.errors().size() )
				{
					throw IECore::Exception( errorHandler.errors() );
				}
				else
				{
					throw IECore::Exception( "Unknown compilation error" );
				}
			}

			// Declare a shader group with the shader in.

			OSL::ShadingSystem *shadingSys = shadingSystem();

			if( !shadingSys->LoadMemoryCompiledShader( shaderName, oso ) )
			{
				throw IECore::Exception( "Failed to load expression shader" );
			}

			OSL::ShaderGroupRef result = shadingSys->ShaderGroupBegin();

				shadingSys->Shader( "surface", shaderName, "" );

			shadingSys->ShaderGroupEnd();

			// Tell OSL that we'll be wanting to query each of the output parameters, so
			// it'd better not go optimising them away.

			if( outParameters.size() )
			{
				shadingSys->attribute(
					result.get(), "renderer_outputs",
					TypeDesc( TypeDesc::STRING, outParameters.size() ),
					&outParameters[0]
				);
			}

			// Store our result so we can reuse it, and return it.

			g_shaderGroups[shaderName] = result;

			return result;
		}

		// Initialised by parse().
		vector<ustring> m_inParameters;
		vector<const OSL::ShaderSymbol *> m_outSymbols;
		OSL::ShaderGroupRef m_shaderGroup;

};

Expression::Engine::EngineDescription<OSLExpressionEngine> OSLExpressionEngine::g_engineDescription( "OSL" );

} // namespace

#endif // OSL_LIBRARY_VERSION_CODE
