//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "IECore/CachedReader.h"
#include "IECore/VectorTypedData.h"
#include "IECore/MessageHandler.h"

#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/TypedObjectPlug.h"

#include "GafferRenderMan/RenderManShader.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferRenderMan;

IE_CORE_DEFINERUNTIMETYPED( RenderManShader );

RenderManShader::RenderManShader( const std::string &name )
	:	GafferScene::Shader( name )
{
	addChild( new Plug( "out", Plug::Out ) );
}

RenderManShader::~RenderManShader()
{
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
	
	if( parametersPlug()->isAncestorOf( plug ) )
	{
		if( plug->typeId() == Plug::staticTypeId() )
		{
			// coshader parameter - input must be another
			// renderman shader hosting a coshader.
			const RenderManShader *inputShader = inputPlug->parent<RenderManShader>();
			return inputShader && inputPlug->getName() == "out" && inputShader->typePlug()->getValue() == "ri:shader";
		}
		else
		{
			// standard parameter - input must not be another
			// shader.
			const Shader *inputShader = inputPlug->ancestor<Shader>();
			return !inputShader;
		}
	}
	
	return true;
}

IECore::ShaderPtr RenderManShader::shader( NetworkBuilder &network ) const
{
	ShaderPtr result = new IECore::Shader( namePlug()->getValue(), typePlug()->getValue() );
	for( InputPlugIterator it( parametersPlug() ); it!=it.end(); it++ )
	{
		if( (*it)->typeId() == Plug::staticTypeId() )
		{
			// coshader parameter
			const Plug *inputPlug = (*it)->source<Plug>();
			if( inputPlug && inputPlug != *it )
			{
				const RenderManShader *inputShader = inputPlug->parent<RenderManShader>();
				if( inputShader )
				{
					result->parameters()[(*it)->getName()] = new StringData( network.shaderHandle( inputShader ) );
				}
			}
		}
		else if( (*it)->typeId() == CompoundPlug::staticTypeId() )
		{
			// coshader array parameter
			StringVectorDataPtr value = new StringVectorData();
			for( InputPlugIterator cIt( *it ); cIt != cIt.end(); ++cIt )
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
			result->parameters()[(*it)->getName()] = value;
		}
		else
		{
			// standard shader parameter
			result->parameters()[(*it)->getName()] = CompoundDataPlug::extractDataFromPlug( static_cast<const ValuePlug *>( it->get() ) );
		}
	}
	return result;
}

IECore::CachedReader *RenderManShader::shaderLoader()
{
	static CachedReaderPtr g_loader;
	if( !g_loader )
	{
		const char *sp = getenv( "DL_SHADERS_PATH" );
		sp = sp ? sp : "";
		g_loader = new CachedReader( SearchPath( sp, ":" ), 10 * 1024 * 1024 );
	}
	return g_loader.get();
}

template <typename PlugType>
static void loadParameter( Gaffer::CompoundPlug *parametersPlug, const std::string &name, const Data *defaultValue )
{
	const TypedData<typename PlugType::ValueType> *typedDefaultValue = static_cast<const TypedData<typename PlugType::ValueType> *>( defaultValue );

	PlugType *existingPlug = parametersPlug->getChild<PlugType>( name );
	if( existingPlug && existingPlug->defaultValue() == typedDefaultValue->readable() )
	{
		return;
	}
	
	typename PlugType::Ptr plug = new PlugType( name, Plug::In, typedDefaultValue->readable(), Plug::Default | Plug::Dynamic );
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

static void loadCoshaderArrayParameter( Gaffer::CompoundPlug *parametersPlug, const std::string &name, const Data *defaultValue )
{
	CompoundPlugPtr plug = parametersPlug->getChild<CompoundPlug>( name );
	if( !plug )
	{
		plug = new CompoundPlug( name, Plug::In, Plug::Default | Plug::Dynamic );
		parametersPlug->setChild( name, plug );
	}
		
	const std::vector<std::string> &typedDefaultValue = static_cast<const StringVectorData *>( defaultValue )->readable();
	while( plug->children().size() != typedDefaultValue.size() )
	{
		plug->addChild( new Plug( "in1" , Plug::In, Plug::Default | Plug::Dynamic ) );
	}
}

template <typename PlugType>
static void loadNumericParameter( Gaffer::CompoundPlug *parametersPlug, const std::string &name, const Data *defaultValue, const CompoundData *annotations )
{
	const TypedData<typename PlugType::ValueType> *typedDefaultValue = static_cast<const TypedData<typename PlugType::ValueType> *>( defaultValue );
	
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
	if(	existingPlug &&
	    existingPlug->defaultValue() == typedDefaultValue->readable() &&
		existingPlug->minValue() == minValue &&
		existingPlug->maxValue() == maxValue 
	)
	{
		return;
	}
	
	typename PlugType::Ptr plug = new PlugType( name, Plug::In, typedDefaultValue->readable(), minValue, maxValue, Plug::Default | Plug::Dynamic );
		
	if( existingPlug )
	{
		if( existingPlug->children().size() )
		{
			// CompoundNumericPlug
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
		else
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

void RenderManShader::loadShaderParameters( const IECore::Shader *shader, Gaffer::CompoundPlug *parametersPlug, bool keepExistingValues )
{	
	const CompoundData *typeHints = shader->blindData()->member<CompoundData>( "ri:parameterTypeHints", true );
	
	const StringVectorData *orderedParameterNamesData = shader->blindData()->member<StringVectorData>( "ri:orderedParameterNames", true );
	const vector<string> &orderedParameterNames = orderedParameterNamesData->readable();
	
	const StringVectorData *outputParameterNamesData = shader->blindData()->member<StringVectorData>( "ri:outputParameterNames", true );
	const vector<string> &outputParameterNames = outputParameterNamesData->readable();
	
	const CompoundData *annotations = shader->blindData()->member<CompoundData>( "ri:annotations", true );
	
	// remove plugs we don't need - either because we're not preserving existing values or because
	// the parameter doesn't exist any more.
	
	std::vector<PlugPtr> toRemove;
	for( PlugIterator pIt( parametersPlug->children().begin(), parametersPlug->children().end() ); pIt!=pIt.end(); pIt++ )
	{
		if( !keepExistingValues || !shader->parametersData()->member<Data>( (*pIt)->getName() ) )
		{
			toRemove.push_back( *pIt );
		}
	}
	
	for( std::vector<PlugPtr>::const_iterator pIt = toRemove.begin(), eIt = toRemove.end(); pIt != eIt; pIt++ )
	{
		parametersPlug->removeChild( *pIt );
	}
	
	// make sure we have a plug to represent each parameter, reusing plugs wherever possible.
	
	for( vector<string>::const_iterator it = orderedParameterNames.begin(), eIt = orderedParameterNames.end(); it != eIt; it++ )
	{
		if( std::find( outputParameterNames.begin(), outputParameterNames.end(), *it ) != outputParameterNames.end() )
		{
			continue;
		}
	
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
					loadParameter<StringPlug>( parametersPlug, *it, defaultValue );
				}
				break;
			case FloatDataTypeId :
				loadNumericParameter<FloatPlug>( parametersPlug, *it, defaultValue, annotations );
				break;
			case Color3fDataTypeId :
				loadNumericParameter<Color3fPlug>( parametersPlug, *it, defaultValue, annotations );
				break;
			case V3fDataTypeId :
				loadNumericParameter<V3fPlug>( parametersPlug, *it, defaultValue, annotations );
				break;
			case StringVectorDataTypeId :
				if( typeHint && typeHint->readable() == "shader" )
				{
					loadCoshaderArrayParameter( parametersPlug, *it, defaultValue );
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
	}
}


