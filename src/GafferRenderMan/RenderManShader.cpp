//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "boost/lexical_cast.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/spirit/include/qi.hpp"
#include "boost/fusion/adapted/struct.hpp"
#include "boost/tokenizer.hpp"

#include "IECore/CachedReader.h"
#include "IECore/VectorTypedData.h"
#include "IECore/MessageHandler.h"

#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/SplinePlug.h"
#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Box.h"

#include "GafferScene/ShaderSwitch.h"

#include "GafferRenderMan/RenderManShader.h"

using namespace std;
using namespace boost;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferRenderMan;

namespace qi = boost::spirit::qi;
namespace ascii = boost::spirit::ascii;

IE_CORE_DEFINERUNTIMETYPED( RenderManShader );

RenderManShader::RenderManShader( const std::string &name )
	:	GafferScene::Shader( name )
{
	addChild( new Plug( "out", Plug::Out ) );
}

RenderManShader::~RenderManShader()
{
}

Gaffer::Plug *RenderManShader::correspondingInput( const Gaffer::Plug *output )
{
	// better to do a few harmless casts than manage a duplicate implementation
	return const_cast<Gaffer::Plug *>(
		const_cast<const RenderManShader *>( this )->correspondingInput( output )
	);
}

const Gaffer::Plug *RenderManShader::correspondingInput( const Gaffer::Plug *output ) const
{
	if( output != outPlug() )
	{
		return Shader::correspondingInput( output );
	}

	ConstCompoundDataPtr ann = annotations();
	if( !ann )
	{
		return 0;
	}
	
	const StringData *primaryInput = ann->member<StringData>( "primaryInput" );
	if( !primaryInput )
	{
		return 0;
	}
	
	const Plug *result = parametersPlug()->getChild<Plug>( primaryInput->readable() );
	if( !result )
	{
		IECore::msg( IECore::Msg::Error, "RenderManShader::correspondingInput", boost::format( "Parameter \"%s\" does not exist" ) % primaryInput->readable() );
		return 0;
	}
	
	if( result->typeId() != Gaffer::Plug::staticTypeId() )
	{
		IECore::msg( IECore::Msg::Error, "RenderManShader::correspondingInput", boost::format( "Parameter \"%s\" is not of type shader" ) % primaryInput->readable() );
		return 0;
	}
	
	return result;
}

void RenderManShader::loadShader( const std::string &shaderName, bool keepExistingValues )
{
	IECore::ConstShaderPtr shader = runTimeCast<const IECore::Shader>( shaderLoader()->read( shaderName + ".sdl" ) );
	loadShaderParameters( shader, parametersPlug(), keepExistingValues );
	namePlug()->setValue( shaderName );
	typePlug()->setValue( "ri:" + shader->getType() );
}

bool RenderManShader::acceptsInput( const Plug *plug, const Plug *inputPlug ) const
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
		
		if( plug->typeId() == Plug::staticTypeId() )
		{
			// coshader parameter - source must be another
			// renderman shader hosting a coshader, or a box
			// or shader switch with a currently dangling connection.
			// in the latter cases, we will be called again when the
			// box or switch is connected to something, so we can check
			// that the indirect connection is to our liking.
			const Node* sourceNode = sourcePlug->node();
			
			if(
				runTimeCast<const Box>( sourceNode ) ||
				runTimeCast<const ShaderSwitch>( sourceNode )
			)
			{
				return true;
			}
			
			const RenderManShader *inputShader = sourcePlug->parent<RenderManShader>();
			if(
				!inputShader ||
				sourcePlug != inputShader->outPlug() ||
				inputShader->typePlug()->getValue() != "ri:shader"
			)
			{
				return false;
			}
			// so far all is good, but we also need to check that
			// the coshaderType annotations match if present.
			ConstCompoundDataPtr dstAnnotations = annotations();
			if( !dstAnnotations )
			{
				return true;
			}
			InternedString parameterName = plug->getName();
			if( plug->parent<GraphComponent>() != parametersPlug() )
			{
				// array parameter
				parameterName = plug->parent<GraphComponent>()->getName();
			}
			const StringData *dstType = dstAnnotations->member<StringData>( parameterName.string() + ".coshaderType" );
			if( !dstType )
			{
				return true;
			}
			ConstCompoundDataPtr srcAnnotations = inputShader->annotations();
			if( !srcAnnotations )
			{
				return false;
			}
			const StringData *srcType = srcAnnotations->member<StringData>( "coshaderType" );
			if( !srcType )
			{
				return false;
			}
			
			// we accept a space (or comma) separated list of source types, so that a coshader
			// can belong to multiple types.
			typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
			Tokenizer srcTypes( srcType->readable(), boost::char_separator<char>( " ," ) );
			return find( srcTypes.begin(), srcTypes.end(), dstType->readable() ) != srcTypes.end();
		}
		else
		{
			// standard parameter - input must not be the
			// output of another shader.
			const Shader *inputShader = sourcePlug->ancestor<Shader>();
			return !inputShader || sourcePlug != inputShader->outPlug();
		}
	}
	
	return true;
}

void RenderManShader::parameterHash( const Gaffer::Plug *parameterPlug, NetworkBuilder &network, IECore::MurmurHash &h ) const
{
	if( parameterPlug->isInstanceOf( ArrayPlug::staticTypeId() ) )
	{
		// coshader array parameter
		for( InputPlugIterator cIt( parameterPlug ); cIt != cIt.end(); ++cIt )
		{
			Shader::parameterHash( cIt->get(), network, h );
		}
	}
	else
	{
		Shader::parameterHash( parameterPlug, network, h );
	}
}

IECore::DataPtr RenderManShader::parameterValue( const Gaffer::Plug *parameterPlug, NetworkBuilder &network ) const
{
	if( parameterPlug->typeId() == Plug::staticTypeId() )
	{
		// coshader parameter
		const Plug *inputPlug = parameterPlug->source<Plug>();
		if( inputPlug && inputPlug != parameterPlug )
		{
			const RenderManShader *inputShader = inputPlug->parent<RenderManShader>();
			if( inputShader )
			{
				const std::string &handle = network.shaderHandle( inputShader );
				if( handle.size() )
				{
					return new StringData( handle );
				}
			}
		}
	}
	else if( parameterPlug->isInstanceOf( ArrayPlug::staticTypeId() ) )
	{
		// coshader array parameter
		StringVectorDataPtr value = new StringVectorData();
		for( InputPlugIterator cIt( parameterPlug ); cIt != cIt.end(); ++cIt )
		{
			const Plug *inputPlug = (*cIt)->source<Plug>();
			const RenderManShader *inputShader = inputPlug && inputPlug != *cIt ? inputPlug->parent<RenderManShader>() : 0;
			if( inputShader )
			{
				value->writable().push_back( network.shaderHandle( inputShader ) );
			}
			else
			{
				value->writable().push_back( "" );
			}
		}
		return value;
	}
	
	return Shader::parameterValue( parameterPlug, network );
}

const IECore::ConstCompoundDataPtr RenderManShader::annotations() const
{
	std::string shaderName = namePlug()->getValue();
	if( !shaderName.size() )
	{
		return NULL;
	}
	
	IECore::ConstShaderPtr shader = NULL;
	try
	{
		shader = runTimeCast<const IECore::Shader>( shaderLoader()->read( shaderName + ".sdl" ) );
	}
	catch( const std::exception &e )
	{
		IECore::msg( IECore::Msg::Error, "RenderManShader::annotations", e.what() );
		return NULL;
	}
	
	return shader->blindData()->member<CompoundData>( "ri:annotations" );
}

//////////////////////////////////////////////////////////////////////////
// Loading code
//////////////////////////////////////////////////////////////////////////

IECore::CachedReader *RenderManShader::shaderLoader()
{
	static CachedReaderPtr g_loader;
	if( !g_loader )
	{
		const char *sp = getenv( "DL_SHADERS_PATH" );
		sp = sp ? sp : "";
		g_loader = new CachedReader( SearchPath( sp, ":" ) );
	}
	return g_loader.get();
}

template <typename PlugType>
static void loadParameter( Gaffer::CompoundPlug *parametersPlug, const std::string &name, const typename PlugType::ValueType &defaultValue )
{
	PlugType *existingPlug = parametersPlug->getChild<PlugType>( name );
	if( existingPlug && existingPlug->defaultValue() == defaultValue )
	{
		return;
	}
	
	typename PlugType::Ptr plug = new PlugType( name, Plug::In, defaultValue, Plug::Default | Plug::Dynamic );
	if( existingPlug )
	{
		if( existingPlug->template getInput<PlugType>() )
		{
			plug->setInput( existingPlug->template getInput<PlugType>() );
		}
		else
		{
			plug->setValue( existingPlug->getValue() );
		}
	}
	
	parametersPlug->setChild( name, plug );
}

static void loadCoshaderParameter( Gaffer::CompoundPlug *parametersPlug, const std::string &name )
{
	Plug *existingPlug = parametersPlug->getChild<Plug>( name );
	if( existingPlug && existingPlug->typeId() == Plug::staticTypeId() )
	{
		return;
	}
	
	PlugPtr plug = new Plug( name, Plug::In, Plug::Default | Plug::Dynamic );
	if( existingPlug && existingPlug->getInput<Plug>() )
	{
		plug->setInput( existingPlug->getInput<Plug>() );
	}
	
	parametersPlug->setChild( name, plug );
}

static void loadCoshaderArrayParameter( Gaffer::CompoundPlug *parametersPlug, const std::string &name, const StringVectorData *defaultValue )
{
	const size_t minSize = std::max( defaultValue->readable().size(), (size_t)1 );
	const size_t maxSize = defaultValue->readable().size() ? defaultValue->readable().size() : Imath::limits<size_t>::max();
	
	PlugPtr existingPlug = parametersPlug->getChild<Plug>( name );
	ArrayPlug *existingArrayPlug = runTimeCast<ArrayPlug>( existingPlug );
	if( existingArrayPlug && existingArrayPlug->minSize() == minSize && existingArrayPlug->maxSize() == maxSize )
	{
		return;
	}

	std::string elementName = name;
	if( isdigit( *elementName.rbegin() ) )
	{
		elementName += "_0";
	}
	else
	{
		elementName += "0";		
	}
	
	ArrayPlugPtr plug = new ArrayPlug( name, Plug::In, new Plug( elementName ), minSize, maxSize, Plug::Default | Plug::Dynamic );
	parametersPlug->setChild( name, plug );
	
	if( existingPlug )
	{
		for( size_t i = 0, e = std::min( existingPlug->children().size(), maxSize ); i < e; ++i )
		{
			if( i < plug->children().size() )
			{
				plug->getChild<Plug>( i )->setInput( existingPlug->getChild<Plug>( i )->getInput<Plug>() );
			}
			else
			{
				plug->addChild( existingPlug->getChild<Plug>( i ) );
			}
		}
	}
}

template <typename PlugType>
static void loadNumericParameter( Gaffer::CompoundPlug *parametersPlug, const std::string &name, typename PlugType::ValueType defaultValue, const CompoundData *annotations )
{	
	typename PlugType::ValueType minValue( Imath::limits<typename PlugType::ValueType>::min() );
	typename PlugType::ValueType maxValue( Imath::limits<typename PlugType::ValueType>::max() );
	
	const StringData *minValueData = annotations->member<StringData>( name + ".min" );
	if( minValueData )
	{
		minValue = typename PlugType::ValueType( boost::lexical_cast<typename PlugType::ValueType>( minValueData->readable() ) );
	}
	
	const StringData *maxValueData = annotations->member<StringData>( name + ".max" );
	if( maxValueData )
	{
		maxValue = typename PlugType::ValueType( boost::lexical_cast<typename PlugType::ValueType>( maxValueData->readable() ) );
	}
	
	PlugType *existingPlug = parametersPlug->getChild<PlugType>( name );
	if(	
		existingPlug &&
		existingPlug->defaultValue() == defaultValue &&
		existingPlug->minValue() == minValue &&
		existingPlug->maxValue() == maxValue 
	)
	{
		return;
	}
	
	typename PlugType::Ptr plug = new PlugType( name, Plug::In, defaultValue, minValue, maxValue, Plug::Default | Plug::Dynamic );
		
	if( existingPlug )
	{
		if( existingPlug->template getInput<Plug>() )
		{
			plug->setInput( existingPlug->template getInput<Plug>() );
		}
		else
		{
			plug->setValue( existingPlug->getValue() );
		}
	}
	
	parametersPlug->setChild( name, plug );
}

static void loadNumericParameter( Gaffer::CompoundPlug *parametersPlug, const std::string &name, float defaultValue, const CompoundData *annotations )
{
	const StringData *typeData = annotations->member<StringData>( name + ".type" );
	if( typeData && typeData->readable() == "float" )
	{
		loadNumericParameter<FloatPlug>( parametersPlug, name, defaultValue, annotations );
	}
	else if( typeData && typeData->readable() == "int" )
	{
		loadNumericParameter<IntPlug>( parametersPlug, name, static_cast<int>( defaultValue ), annotations );
	}
	else if( typeData && typeData->readable() == "bool" )
	{
		loadParameter<BoolPlug>( parametersPlug, name, static_cast<bool>( defaultValue ) );
	}
	else
	{
		if( typeData )
		{
			msg(
				Msg::Warning, "RenderManShader::loadShaderParameters",
				boost::format( "Type annotation for parameter \"%s\" specifies unsupported type \"%s\"" ) % name % typeData->readable()
			);
		}
		loadNumericParameter<FloatPlug>( parametersPlug, name, defaultValue, annotations );
	}
}

template <typename PlugType>
static void loadCompoundNumericParameter( Gaffer::CompoundPlug *parametersPlug, const std::string &name, const typename PlugType::ValueType &defaultValue, const CompoundData *annotations )
{	
	typename PlugType::ValueType minValue( Imath::limits<float>::min() );
	typename PlugType::ValueType maxValue( Imath::limits<float>::max() );
	
	const StringData *minValueData = annotations->member<StringData>( name + ".min" );
	if( minValueData )
	{
		minValue = typename PlugType::ValueType( boost::lexical_cast<float>( minValueData->readable() ) );
	}
	
	const StringData *maxValueData = annotations->member<StringData>( name + ".max" );
	if( maxValueData )
	{
		maxValue = typename PlugType::ValueType( boost::lexical_cast<float>( maxValueData->readable() ) );
	}
	
	PlugType *existingPlug = parametersPlug->getChild<PlugType>( name );
	if(
		existingPlug &&
		existingPlug->defaultValue() == defaultValue &&
		existingPlug->minValue() == minValue &&
		existingPlug->maxValue() == maxValue 
	)
	{
		return;
	}
	
	typename PlugType::Ptr plug = new PlugType( name, Plug::In, defaultValue, minValue, maxValue, Plug::Default | Plug::Dynamic );
		
	if( existingPlug )
	{
		for( size_t i = 0, e = existingPlug->children().size(); i < e; i++ )
		{
			FloatPlug *existingComponentPlug = existingPlug->template GraphComponent::getChild<FloatPlug>( i );
			if( existingComponentPlug->getInput<Plug>() )
			{
				plug->template GraphComponent::getChild<FloatPlug>( i )->setInput( existingComponentPlug->getInput<Plug>() );
			}
			else
			{
				plug->template GraphComponent::getChild<FloatPlug>( i )->setValue( existingComponentPlug->getValue() );
			}
		}
	}
	
	parametersPlug->setChild( name, plug );
}

template<typename PlugType>
static void loadArrayParameter( Gaffer::CompoundPlug *parametersPlug, const std::string &name, const Data *defaultValue, const CompoundData *annotations )
{
	const typename PlugType::ValueType *typedDefaultValue = static_cast<const typename PlugType::ValueType *>( defaultValue );

	PlugType *existingPlug = parametersPlug->getChild<PlugType>( name );
	if( existingPlug && existingPlug->defaultValue()->isEqualTo( defaultValue ) )
	{
		return;
	}
	
	typename PlugType::Ptr plug = new PlugType( name, Plug::In, typedDefaultValue, Plug::Default | Plug::Dynamic );
	if( existingPlug )
	{
		if( existingPlug->template getInput<PlugType>() )
		{
			plug->setInput( existingPlug->template getInput<PlugType>() );
		}
		else
		{
			plug->setValue( existingPlug->getValue() );
		}
	}
	
	parametersPlug->setChild( name, plug );

}

template<typename PlugType>
static void loadSplineParameter( Gaffer::CompoundPlug *parametersPlug, const std::string &name, const FloatVectorData *defaultPositions, const Data *defaultValues )
{	
	PlugType *existingPlug = parametersPlug->getChild<PlugType>( name );
	if( existingPlug )
	{
		return;
	}
	
	typedef typename PlugType::XPlugType::ValueType XValueType;
	typedef typename PlugType::YPlugType::ValueType YValueType;
	typedef std::vector<YValueType> YValueVector;
	typedef TypedData<YValueVector> YValueData;
	
	typename PlugType::ValueType defaultValue;
	
	const YValueData *typedDefaultValues = static_cast<const YValueData *>( defaultValues );
	size_t numPoints = std::min( defaultPositions->readable().size(), typedDefaultValues->readable().size() );
	if( numPoints >= 4 )
	{
		for( size_t i = 0; i < numPoints; ++i )
		{
			defaultValue.points.insert( 
				typename PlugType::ValueType::Point(
					defaultPositions->readable()[i],
					typedDefaultValues->readable()[i]
				)
			);
		}
	}
	else
	{
		if( numPoints )
		{
			// looks like someone attempted to provide a default but didn't provide enough values
			msg(
				Msg::Warning, "RenderManShader::loadShaderParameters",
				boost::format( "Default value for parameter \"%s\" has less than 4 points" ) % name
			);
		}
		defaultValue.points.insert( typename PlugType::ValueType::Point( XValueType( 0 ), YValueType( 0 ) ) );
		defaultValue.points.insert( typename PlugType::ValueType::Point( XValueType( 0 ), YValueType( 0 ) ) );
		defaultValue.points.insert( typename PlugType::ValueType::Point( XValueType( 1 ), YValueType( 1 ) ) );
		defaultValue.points.insert( typename PlugType::ValueType::Point( XValueType( 1 ), YValueType( 1 ) ) );
	}
			
	typename PlugType::Ptr plug = new PlugType( name, Plug::In, defaultValue, Plug::Default | Plug::Dynamic );
	parametersPlug->setChild( name, plug );
}

static IECore::FloatVectorDataPtr parseFloats( const std::string &value )
{
	FloatVectorDataPtr result = new FloatVectorData;

	string::const_iterator first = value.begin();
	bool r = qi::phrase_parse(

		first, value.end(),

		/////////////////
		qi::omit[ -qi::char_( '{' ) ] >>
		(
			qi::float_ % ','
		) >>
		qi::omit[ -qi::char_( '}' ) ]
		,
		/////////////////

		ascii::space,
		result->writable()

	);

	if( !r || first != value.end() )
	{
		return 0;
	}

	return result;
}

BOOST_FUSION_ADAPT_STRUCT(
	Imath::Color3f,
	(float, x)
	(float, y)
	(float, z)
)

template <typename Iterator>
struct ColorGrammar : qi::grammar<Iterator, std::vector<Imath::Color3f>(), ascii::space_type>
{

	ColorGrammar() : ColorGrammar::base_type(start)
	{

		color1 %=
			qi::lit("color")
			>> '('
			>>  qi::float_
			>>  ')'
		;

		color3 %=
			qi::lit("color")
			>> '('
			>>  qi::float_ >> ','
			>>  qi::float_ >> ','
			>>  qi::float_
			>>  ')'
		;

		color = qi::float_ | color1 | color3;

		start %=
			qi::omit[ -qi::char_( '{' ) ] >>
				color % "," >>
			qi::omit[ -qi::char_( '}' ) ]
		;
	}

	qi::rule<Iterator, Imath::Color3f(), ascii::space_type> color1;
	qi::rule<Iterator, Imath::Color3f(), ascii::space_type> color3;
	qi::rule<Iterator, Imath::Color3f(), ascii::space_type> color;

	qi::rule<Iterator, std::vector<Imath::Color3f>(), ascii::space_type> start;

};

static IECore::Color3fVectorDataPtr parseColors( const std::string &value )
{
	Color3fVectorDataPtr result = new Color3fVectorData;

	ColorGrammar<string::const_iterator> grammar;

	std::string::const_iterator first = value.begin();
	bool r = qi::phrase_parse( first, value.end(), grammar, ascii::space, result->writable() );

	if( !r || first != value.end() )
	{
		return 0;
	}
	return result;
}

void RenderManShader::loadShaderParameters( const IECore::Shader *shader, Gaffer::CompoundPlug *parametersPlug, bool keepExistingValues )
{	
	const CompoundData *typeHints = shader->blindData()->member<CompoundData>( "ri:parameterTypeHints", true );
	
	const StringVectorData *orderedParameterNamesData = shader->blindData()->member<StringVectorData>( "ri:orderedParameterNames", true );
	const vector<string> &orderedParameterNames = orderedParameterNamesData->readable();
	
	const StringVectorData *outputParameterNamesData = shader->blindData()->member<StringVectorData>( "ri:outputParameterNames", true );
	const vector<string> &outputParameterNames = outputParameterNamesData->readable();
	
	const CompoundData *annotations = shader->blindData()->member<CompoundData>( "ri:annotations", true );
	
	// if we're not preserving existing values then remove all existing parameter plugs - the various
	// plug creators above know that if a plug exists then they should preserve its values.
	
	if( !keepExistingValues )
	{
		for( int i = parametersPlug->children().size() - 1; i >= 0; --i )
		{
			parametersPlug->removeChild( parametersPlug->getChild<GraphComponent>( i ) );
		}
	}
	
	// make sure we have a plug to represent each parameter, reusing plugs wherever possible.
	
	set<string> validPlugNames;
	for( vector<string>::const_iterator it = orderedParameterNames.begin(), eIt = orderedParameterNames.end(); it != eIt; it++ )
	{
		if( std::find( outputParameterNames.begin(), outputParameterNames.end(), *it ) != outputParameterNames.end() )
		{
			continue;
		}
	
		// splines are represented by two parameters matched by a naming convention, and we map
		// those two parameters to a single SplinePlug.
	
		const bool endsWithValues = ends_with( *it, "Values" );
		const bool endsWithPositions = ends_with( *it, "Positions" );
		if( endsWithPositions || endsWithValues )
		{
			string plugName( *it, 0, it->size() - ( endsWithValues ? 6 : 9 ) );
			if( validPlugNames.find( plugName ) != validPlugNames.end() )
			{
				continue;
			}
			
			// must use a smart pointers here because we may assign the data the parser creates (and which we therefore own)
			ConstFloatVectorDataPtr positions = shader->parametersData()->member<FloatVectorData>( plugName + "Positions" );
			ConstDataPtr values = shader->parametersData()->member<Data>( plugName + "Values" );
			
			if( positions && values )
			{
				const StringData *defaultValuesAnnotation = annotations->member<StringData>( plugName + "Values.defaultValue" );
				const StringData *defaultPositionsAnnotation = annotations->member<StringData>( plugName + "Positions.defaultValue" );

				if( defaultValuesAnnotation )
				{
					DataPtr parsedValues;
					if( values->isInstanceOf( Color3fVectorData::staticTypeId() ) )
					{
						parsedValues = parseColors( defaultValuesAnnotation->readable() );
					}
					else
					{
						parsedValues = parseFloats( defaultValuesAnnotation->readable() );
					}

					if( parsedValues )
					{
						values = parsedValues;
					}
					else
					{
						msg(
							Msg::Warning, "RenderManShader::loadShaderParameters",
							boost::format( "Unable to parse default value \"%s\" for parameter \"%s\"" ) % defaultValuesAnnotation->readable() % ( plugName + "Values" )
						);
					}
				}

				if( defaultPositionsAnnotation )
				{
					FloatVectorDataPtr parsedPositions = parseFloats( defaultPositionsAnnotation->readable() );
					if( parsedPositions )
					{
						positions = parsedPositions;
					}
					else
					{
						msg(
							Msg::Warning, "RenderManShader::loadShaderParameters",
							boost::format( "Unable to parse default value \"%s\" for parameter \"%s\"" ) % defaultPositionsAnnotation->readable() % ( plugName + "Positions" )
						);
					}
				}

				switch( values->typeId() )
				{
					case FloatVectorDataTypeId  :
						loadSplineParameter<SplineffPlug>( parametersPlug, plugName, positions, values );
						break;
					case Color3fVectorDataTypeId :
						loadSplineParameter<SplinefColor3fPlug>( parametersPlug, plugName, positions, values );
						break;
					default :
						msg(
							Msg::Warning, "RenderManShader::loadShaderParameters",
							boost::format( "Spline \"%s\" has unsupported value type \"%s\"" ) % plugName % values->typeName()
						);
				}
				validPlugNames.insert( plugName );
				continue;
			}
			
		}
	
		// the other parameter types map more simply to a single plug each.
	
		const StringData *typeHint = typeHints->member<StringData>( *it, false );
		const Data *defaultValue = shader->parametersData()->member<Data>( *it );
		switch( defaultValue->typeId() )
		{
			case StringDataTypeId :
				if( typeHint && typeHint->readable() == "shader" )
				{
					loadCoshaderParameter( parametersPlug, *it );
				}
				else
				{
					loadParameter<StringPlug>( parametersPlug, *it, static_cast<const StringData *>( defaultValue )->readable() );
				}
				break;
			case FloatDataTypeId :
				loadNumericParameter( parametersPlug, *it, static_cast<const FloatData *>( defaultValue )->readable(), annotations );
				break;
			case Color3fDataTypeId :
				loadCompoundNumericParameter<Color3fPlug>( parametersPlug, *it, static_cast<const Color3fData *>( defaultValue )->readable(), annotations );
				break;
			case V3fDataTypeId :
				loadCompoundNumericParameter<V3fPlug>( parametersPlug, *it, static_cast<const V3fData *>( defaultValue )->readable(), annotations );
				break;
			case StringVectorDataTypeId :
				if( typeHint && typeHint->readable() == "shader" )
				{
					loadCoshaderArrayParameter( parametersPlug, *it, static_cast<const StringVectorData *>( defaultValue ) );
				}
				else
				{
					loadArrayParameter<StringVectorDataPlug>( parametersPlug, *it, defaultValue, annotations );
				}
				break;
			case FloatVectorDataTypeId :
				loadArrayParameter<FloatVectorDataPlug>( parametersPlug, *it, defaultValue, annotations );
				break;
			case Color3fVectorDataTypeId :
				loadArrayParameter<Color3fVectorDataPlug>( parametersPlug, *it, defaultValue, annotations );
				break;
			case V3fVectorDataTypeId :
				loadArrayParameter<V3fVectorDataPlug>( parametersPlug, *it, defaultValue, annotations );
				break;		
			default :
				msg(
					Msg::Warning, "RenderManShader::loadShaderParameters",
					boost::format( "Parameter \"%s\" has unsupported type \"%s\"" ) % *it % defaultValue->typeName()
				);
		}
		
		validPlugNames.insert( *it );
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


