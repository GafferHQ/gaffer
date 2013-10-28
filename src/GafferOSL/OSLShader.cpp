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

static std::string plugName( const OSLQuery::Parameter *parameter )
{
	size_t i = parameter->name.find( "." );
	if( i != string::npos )
	{
		return parameter->name.substr( i + 1 );
	}
	return parameter->name;
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
		defaultValue = parameter->sdefault[0];
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
		typedef typename PlugType::ChildType ChildType;
		for( size_t i = 0, e = existingPlug->children().size(); i < e; ++i )
		{
			transferConnectionOrValue(
				existingPlug->template GraphComponent::getChild<ChildType>( i ),
				plug->template GraphComponent::getChild<ChildType>( i )
			);
		}
	}
	
	parent->setChild( name, plug );
	return plug;
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
	
	return plug;
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
	
	for( vector<string>::const_iterator it = parameter->fields.begin(), eIt = parameter->fields.end(); it != eIt; ++it )
	{
		std::string fieldName = parameter->name + "." + *it;
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
		msg( Msg::Warning, "OSLShader::loadShader", boost::format( "Parameter \"%s\" has unsupported type" ) % parameter->name );
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
			validPlugNames.insert( parameter->name );
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
