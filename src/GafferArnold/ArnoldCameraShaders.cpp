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

#include "GafferArnold/ArnoldCameraShaders.h"

#include "GafferArnold/ArnoldShader.h"

#include "IECoreScene/ShaderNetwork.h"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferArnold;

namespace
{

IECore::InternedString g_filterMapAttributeName( "ai:filtermap" );
IECore::InternedString g_uvRemapAttributeName( "ai:uv_remap" );
IECore::InternedString g_inputShaderAttributeNames[] = { "osl:shader", "ai:surface" };

} // namespace

GAFFER_NODE_DEFINE_TYPE( ArnoldCameraShaders );

size_t ArnoldCameraShaders::g_firstPlugIndex = 0;

ArnoldCameraShaders::ArnoldCameraShaders( const std::string &name )
	:	Shader( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ShaderPlug( "filterMap" ) );
	addChild( new ShaderPlug( "uvRemap" ) );
	addChild( new Plug( "out", Plug::Out ) );
}

ArnoldCameraShaders::~ArnoldCameraShaders()
{
}

GafferScene::ShaderPlug *ArnoldCameraShaders::filterMapPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

const GafferScene::ShaderPlug *ArnoldCameraShaders::filterMapPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

GafferScene::ShaderPlug *ArnoldCameraShaders::uvRemapPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 1 );
}

const GafferScene::ShaderPlug *ArnoldCameraShaders::uvRemapPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 1 );
}

Gaffer::Plug *ArnoldCameraShaders::outPlug()
{
	return getChild<Plug>( g_firstPlugIndex + 2 );
}

const Gaffer::Plug *ArnoldCameraShaders::outPlug() const
{
	return getChild<Plug>( g_firstPlugIndex + 2 );
}

bool ArnoldCameraShaders::affectsAttributes( const Gaffer::Plug *input ) const
{
	return
		Shader::affectsAttributes( input ) ||
		input == filterMapPlug() ||
		input == uvRemapPlug()
	;
}

void ArnoldCameraShaders::attributesHash( const Gaffer::Plug *output, IECore::MurmurHash &h ) const
{
	h.append( typeId() );
	if( !enabledPlug()->getValue() )
	{
		return;
	}
	h.append( filterMapPlug()->attributesHash() );
	h.append( uvRemapPlug()->attributesHash() );
}

IECore::ConstCompoundObjectPtr ArnoldCameraShaders::attributes( const Gaffer::Plug *output ) const
{
	CompoundObjectPtr result = new CompoundObject;
	if( !enabledPlug()->getValue() )
	{
		return result;
	}

	ConstCompoundObjectPtr filterMapAttributes = filterMapPlug()->attributes();
	ConstCompoundObjectPtr uvRemapAttributes = uvRemapPlug()->attributes();

	CompoundObject::ObjectMap &m = result->members();
	for( const auto &name : g_inputShaderAttributeNames )
	{
		if( auto s = filterMapAttributes->member<ShaderNetwork>( name ) )
		{
			m[g_filterMapAttributeName] = const_cast<ShaderNetwork *>( s );
		}
		if( auto s = uvRemapAttributes->member<ShaderNetwork>( name ) )
		{
			m[g_uvRemapAttributeName] = const_cast<ShaderNetwork *>( s );
		}
	}

	return result;
}

bool ArnoldCameraShaders::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !Shader::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( !inputPlug )
	{
		return true;
	}

	if( plug == filterMapPlug() || plug == uvRemapPlug() )
	{
		if( const GafferScene::Shader *shader = runTimeCast<const GafferScene::Shader>( inputPlug->source()->node() ) )
		{
			return runTimeCast<const ArnoldShader>( shader ) || shader->isInstanceOf( "GafferOSL::OSLShader" );
		}
	}

	return true;
}
