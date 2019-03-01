//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "GafferArnold/ArnoldFilterMap.h"

#include "GafferArnold/ArnoldShader.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferArnold;

namespace
{

IECore::InternedString g_filterMapAttributeName( "ai:filtermap" );
IECore::InternedString g_inputShaderAttributeNames[] = { "ai:surface", "osl:shader" } ;

} // namespace

IE_CORE_DEFINERUNTIMETYPED( ArnoldFilterMap );

size_t ArnoldFilterMap::g_firstPlugIndex = 0;

ArnoldFilterMap::ArnoldFilterMap( const std::string &name )
	:	Shader( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ShaderPlug( "map" ) );
	addChild( new Plug( "out", Plug::Out ) );
}

ArnoldFilterMap::~ArnoldFilterMap()
{
}

GafferScene::ShaderPlug *ArnoldFilterMap::mapPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

const GafferScene::ShaderPlug *ArnoldFilterMap::mapPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

Gaffer::Plug *ArnoldFilterMap::outPlug()
{
	return getChild<Plug>( g_firstPlugIndex + 1 );
}

const Gaffer::Plug *ArnoldFilterMap::outPlug() const
{
	return getChild<Plug>( g_firstPlugIndex + 1 );
}

void ArnoldFilterMap::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	Shader::affects( input, outputs );

	if( input == mapPlug() )
	{
		outputs.push_back( outPlug() );
	}
}

void ArnoldFilterMap::attributesHash( const Gaffer::Plug *output, IECore::MurmurHash &h ) const
{
	h.append( typeId() );
	if( !enabledPlug()->getValue() )
	{
		return;
	}
	h.append( mapPlug()->attributesHash() );
}

IECore::ConstCompoundObjectPtr ArnoldFilterMap::attributes( const Gaffer::Plug *output ) const
{
	CompoundObjectPtr result = new CompoundObject;
	if( !enabledPlug()->getValue() )
	{
		return result;
	}

	CompoundObject::ObjectMap &m = result->members();
	m = mapPlug()->attributes()->members();

	for( const auto &name : g_inputShaderAttributeNames )
	{
		CompoundObject::ObjectMap::iterator it = m.find( name );
		if( it != m.end() )
		{
			m[g_filterMapAttributeName] = it->second;
			m.erase( it );
			break;
		}
	}

	return result;
}

bool ArnoldFilterMap::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !Shader::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( !inputPlug )
	{
		return true;
	}

	if( plug == mapPlug() )
	{
		if( const GafferScene::Shader *shader = runTimeCast<const GafferScene::Shader>( inputPlug->source()->node() ) )
		{
			return runTimeCast<const ArnoldShader>( shader ) || shader->isInstanceOf( "GafferOSL::OSLShader" );
		}
	}

	return true;
}
