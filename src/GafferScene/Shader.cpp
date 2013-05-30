//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "Gaffer/TypedPlug.h"
#include "Gaffer/NumericPlug.h"

#include "GafferScene/Shader.h"

using namespace Imath;
using namespace GafferScene;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( Shader );

size_t Shader::g_firstPlugIndex = 0;

Shader::Shader( const std::string &name )
	:	DependencyNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "name" ) );
	addChild( new StringPlug( "type" ) );
	addChild( new CompoundPlug( "parameters" ) );
}

Shader::~Shader()
{
}

Gaffer::StringPlug *Shader::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Shader::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *Shader::typePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *Shader::typePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::CompoundPlug *Shader::parametersPlug()
{
	return getChild<CompoundPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::CompoundPlug *Shader::parametersPlug() const
{
	return getChild<CompoundPlug>( g_firstPlugIndex + 2 );
}

Gaffer::Plug *Shader::outPlug()
{
	// not getting by index, because it is created by the
	// derived classes in loadShader().
	return getChild<Plug>( "out" );
}

const Gaffer::Plug *Shader::outPlug() const
{
	return getChild<Plug>( "out" );
}
		
IECore::MurmurHash Shader::stateHash() const
{
	IECore::MurmurHash h;
	stateHash( h );
	return h;
}

void Shader::stateHash( IECore::MurmurHash &h ) const
{
	shaderHash( h );
}

IECore::ObjectVectorPtr Shader::state() const
{
	NetworkBuilder networkBuilder;
	networkBuilder.shader( this );
	return networkBuilder.m_state;
}

void Shader::shaderHash( IECore::MurmurHash &h ) const
{
	h.append( typeId() );
	namePlug()->hash( h );
	for( InputValuePlugIterator it( parametersPlug() ); it!=it.end(); it++ )
	{
		const Plug *inputPlug = (*it)->getInput<Plug>();
		if( inputPlug )
		{
			const Shader *n = IECore::runTimeCast<const Shader>( inputPlug->node() );
			if( n )
			{
				n->shaderHash( h );
				continue;
			}
			// fall through to hash plug value
		}
		(*it)->hash( h );
	}
}

void Shader::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	DependencyNode::affects( input, outputs );
		
	if( parametersPlug()->isAncestorOf( input ) )
	{
		const Plug *out = outPlug();
		if( out )
		{
			if( out->isInstanceOf( CompoundPlug::staticTypeId() ) )
			{
				for( RecursiveValuePlugIterator it( out ); it != it.end(); it++ )
				{
					if( !(*it)->isInstanceOf( CompoundPlug::staticTypeId() ) )
					{
						outputs.push_back( it->get() );
					}
				}
			}
			else
			{
				outputs.push_back( out );
			}
		}
	}
}

//////////////////////////////////////////////////////////////////////////
// NetworkBuilder implementation
//////////////////////////////////////////////////////////////////////////

Shader::NetworkBuilder::NetworkBuilder()
	:	m_state( new IECore::ObjectVector )
{
}

IECore::Shader *Shader::NetworkBuilder::shader( const Shader *shaderNode )
{
	ShaderMap::const_iterator it = m_shaders.find( shaderNode );
	if( it != m_shaders.end() )
	{
		return it->second;
	}
	
	IECore::ShaderPtr s = shaderNode->shader( *this );
	m_state->members().push_back( s );
	m_shaders[shaderNode] = s;
	return s;
}

const std::string &Shader::NetworkBuilder::shaderHandle( const Shader *shaderNode )
{
	IECore::Shader *s = shader( shaderNode );
	s->setType( "shader" );
	IECore::StringDataPtr handleData = new IECore::StringData( boost::lexical_cast<std::string>( shaderNode ) );
	s->parameters()["__handle"] = handleData;
	return handleData->readable();
}
