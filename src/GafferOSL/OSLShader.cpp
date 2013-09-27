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

#include "oslquery.h"

#include "IECore/MessageHandler.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundNumericPlug.h"

#include "GafferOSL/OSLShader.h"

using namespace std;
using namespace IECore;
using namespace OSL;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferOSL;

IE_CORE_DEFINERUNTIMETYPED( OSLShader );

OSLShader::OSLShader( const std::string &name )
	:	GafferScene::Shader( name )
{
}

OSLShader::~OSLShader()
{
}

//////////////////////////////////////////////////////////////////////////
// shader loading code
//////////////////////////////////////////////////////////////////////////

template<typename PlugType>
void transferConnectionOrValue( PlugType *sourcePlug, PlugType *destinationPlug )
{
	if( !sourcePlug )
	{
		return;
	}
	
	if( sourcePlug->template getInput<Plug>() )
	{
		destinationPlug->setInput( sourcePlug->template getInput<Plug>() );
	}
	else
	{
		destinationPlug->setValue( sourcePlug->getValue() );
	}
}

static Plug *loadStringParameter( const OSLQuery::Parameter *parameter, Gaffer::CompoundPlug *parent )
{
	string defaultValue;
	if( parameter->sdefault.size() )
	{
		defaultValue = parameter->sdefault[0];
	}
	
	StringPlug *existingPlug = parent->getChild<StringPlug>( parameter->name );
	if(	existingPlug && existingPlug->defaultValue() == defaultValue )
	{
		return existingPlug;
	}
	
	StringPlugPtr plug = new StringPlug( parameter->name, parent->direction(), defaultValue, Plug::Default | Plug::Dynamic );
	
	transferConnectionOrValue( existingPlug, plug.get() );
	
	parent->setChild( parameter->name, plug );
	
	return plug;
}

template<typename PlugType>
static Plug *loadNumericParameter( const OSLQuery::Parameter *parameter, Gaffer::CompoundPlug *parent )
{
	typename PlugType::ValueType defaultValue( 0 );
	if( parameter->idefault.size() )
	{
		defaultValue = parameter->idefault[0];
	}
	else if( parameter->fdefault.size() )
	{
		defaultValue = parameter->fdefault[0];
	}

	/// \todo Get from metadata
	typename PlugType::ValueType minValue( Imath::limits<float>::min() );
	typename PlugType::ValueType maxValue( Imath::limits<float>::max() );

	PlugType *existingPlug = parent->getChild<PlugType>( parameter->name );
	if(	
		existingPlug &&
		existingPlug->defaultValue() == defaultValue &&
		existingPlug->minValue() == minValue &&
		existingPlug->maxValue() == maxValue 
	)
	{
		return existingPlug;
	}
	
	typename PlugType::Ptr plug = new PlugType( parameter->name, parent->direction(), defaultValue, minValue, maxValue, Plug::Default | Plug::Dynamic );
	
	transferConnectionOrValue( existingPlug, plug.get() );
	
	parent->setChild( parameter->name, plug );
	
	return plug;
}

template <typename PlugType>
static Plug *loadCompoundNumericParameter( const OSLQuery::Parameter *parameter, Gaffer::CompoundPlug *parent )
{	
	typename PlugType::ValueType defaultValue( 0 );
	if( parameter->idefault.size() )
	{
		for( size_t i = 0; i < PlugType::ValueType::dimensions(); ++i )
		{
			defaultValue[i] = parameter->idefault[i];	
		}
	}
	else if( parameter->fdefault.size() )
	{
		for( size_t i = 0; i < PlugType::ValueType::dimensions(); ++i )
		{
			defaultValue[i] = parameter->fdefault[i];	
		}
	}
	
	/// \todo Get from metadata
	typename PlugType::ValueType minValue( Imath::limits<float>::min() );
	typename PlugType::ValueType maxValue( Imath::limits<float>::max() );
	
	PlugType *existingPlug = parent->getChild<PlugType>( parameter->name );
	if(
		existingPlug &&
		existingPlug->defaultValue() == defaultValue &&
		existingPlug->minValue() == minValue &&
		existingPlug->maxValue() == maxValue 
	)
	{
		return existingPlug;
	}
	
	typename PlugType::Ptr plug = new PlugType( parameter->name, parent->direction(), defaultValue, minValue, maxValue, Plug::Default | Plug::Dynamic );
		
	if( existingPlug )
	{
		typedef typename PlugType::ChildType ChildType;
		for( size_t i = 0, e = existingPlug->children().size(); i < e; ++i )
		{
			transferConnectionOrValue(
				existingPlug->template GraphComponent::getChild<ChildType>( i ),
				plug->template GraphComponent::getChild<ChildType>( i )
			);
		}
	}
	
	parent->setChild( parameter->name, plug );
	return plug;
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
		
		const Plug *plug = NULL;
		if( parameter->type.arraylen == 0 )
		{
			if( parameter->type.basetype == TypeDesc::FLOAT || parameter->type.basetype == TypeDesc::INT )
			{
				// numeric in some way
				if( parameter->type.aggregate == TypeDesc::SCALAR )
				{
					if( parameter->type.basetype == TypeDesc::FLOAT )
					{
						plug = loadNumericParameter<FloatPlug>( parameter, parametersPlug );
					}
					else
					{
						plug = loadNumericParameter<IntPlug>( parameter, parametersPlug );
					}
				}
				else if( parameter->type.aggregate == TypeDesc::VEC3 )
				{
					if( parameter->type.basetype == TypeDesc::FLOAT )
					{
						if( parameter->type.vecsemantics == TypeDesc::COLOR )
						{
							plug = loadCompoundNumericParameter<Color3fPlug>( parameter, parametersPlug );						
						}
						else
						{
							plug = loadCompoundNumericParameter<V3fPlug>( parameter, parametersPlug );
						}
					}
					else
					{
						plug = loadCompoundNumericParameter<V3iPlug>( parameter, parametersPlug );
					}
				}
			}
			else if( parameter->type.basetype == TypeDesc::STRING )
			{
				plug = loadStringParameter( parameter, parametersPlug );
			}
		}
		else
		{
			// array parameter
		}

		if( plug )
		{
			validPlugNames.insert( parameter->name );
		}
		else
		{
			msg( Msg::Warning, "OSLShader::loadShader", boost::format( "Parameter \"%s\" has unsupported type" ) % parameter->name );
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
	typePlug()->setValue( "osl:" + query.shadertype() );
}


bool OSLShader::acceptsInput( const Plug *plug, const Plug *inputPlug ) const
{
	if( !Shader::acceptsInput( plug, inputPlug ) )
	{
		return false;
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
		}		
	}
	
	return true;
}
