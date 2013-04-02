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

#include "IECore/CachedReader.h"
#include "IECore/VectorTypedData.h"

#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/TypedPlug.h"

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
	addChild( new StringPlug( "__shaderName" ) );
	addChild( new Plug( "out", Plug::Out ) );
}

RenderManShader::~RenderManShader()
{
}

void RenderManShader::loadShader( const std::string &shaderName )
{
	loadShaderParameters( shaderName, parametersPlug() );
	getChild<StringPlug>( "__shaderName" )->setValue( shaderName );
}

bool RenderManShader::acceptsInput( const Plug *plug, const Plug *inputPlug ) const
{
	if( !Shader::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}
	
	if( plug->parent<Plug>() == parametersPlug() )
	{
		if( plug->typeId() == Plug::staticTypeId() )
		{
			// coshader parameter - input must be another
			// renderman shader.
			const RenderManShader *inputShader = inputPlug->parent<RenderManShader>();
			return inputShader && inputPlug->getName() == "out";
		}
		else
		{
			// standard parameter - input must not be another
			// shader.
			const Shader *inputShader = inputPlug->parent<Shader>();
			return !inputShader;
		}
	}
	
	return true;
}

void RenderManShader::shaderHash( IECore::MurmurHash &h ) const
{
	Shader::shaderHash( h );
	getChild<StringPlug>( "__shaderName" )->hash( h );
}

IECore::ShaderPtr RenderManShader::shader( NetworkBuilder &network ) const
{
	ShaderPtr result = new IECore::Shader( getChild<StringPlug>( "__shaderName" )->getValue(), "ri:surface" );
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

void RenderManShader::loadShaderParameters( const std::string &shaderName, Gaffer::CompoundPlug *parametersPlug )
{
	IECore::ConstShaderPtr shader = runTimeCast<const IECore::Shader>( shaderLoader()->read( shaderName + ".sdl" ) );
	
	const CompoundData *typeHints = shader->blindData()->member<CompoundData>( "ri:parameterTypeHints", true );
	
	const StringVectorData *orderedParameterNamesData = shader->blindData()->member<StringVectorData>( "ri:orderedParameterNames", true );
	const vector<string> &orderedParameterNames = orderedParameterNamesData->readable();
	
	for( vector<string>::const_iterator it = orderedParameterNames.begin(), eIt = orderedParameterNames.end(); it != eIt; it++ )
	{
		const StringData *typeHint = typeHints->member<StringData>( *it, false );
		if( typeHint && typeHint->readable() == "shader" )
		{
			parametersPlug->addChild( new Plug( *it, Plug::In, Plug::Default | Plug::Dynamic ) );
		}
		else
		{
			CompoundDataMap::const_iterator vIt = shader->parameters().find( *it );
			ValuePlugPtr valuePlug = CompoundDataPlug::createPlugFromData(
				*it,
				Plug::In,
				Plug::Default | Plug::Dynamic,
				vIt->second
			);
			parametersPlug->addChild( valuePlug );
		}
	}
}
