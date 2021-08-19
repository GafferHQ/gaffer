//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferArnold/ArnoldDisplacement.h"

#include "GafferArnold/ArnoldShader.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferArnold;

GAFFER_NODE_DEFINE_TYPE( ArnoldDisplacement );

size_t ArnoldDisplacement::g_firstPlugIndex = 0;
static IECore::InternedString g_mapAttributeName = "ai:disp_map";
static IECore::InternedString g_paddingAttributeName = "ai:disp_padding";
static IECore::InternedString g_heightAttributeName = "ai:disp_height";
static IECore::InternedString g_zeroValueAttributeName = "ai:disp_zero_value";
static IECore::InternedString g_autoBumpAttributeName = "ai:disp_autobump";
static IECore::InternedString g_mapInputAttributeNames[] = { "ai:surface", "osl:shader", "" } ;

ArnoldDisplacement::ArnoldDisplacement( const std::string &name )
	:	Shader( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ShaderPlug( "map" ) );
	addChild( new FloatPlug( "height", Plug::In, 1.0f ) );
	addChild( new FloatPlug( "padding", Plug::In, 0.0f, 0.0f ) );
	addChild( new FloatPlug( "zeroValue" ) );
	addChild( new BoolPlug( "autoBump" ) );
	addChild( new Plug( "out", Plug::Out ) );
}

ArnoldDisplacement::~ArnoldDisplacement()
{
}

GafferScene::ShaderPlug *ArnoldDisplacement::mapPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

const GafferScene::ShaderPlug *ArnoldDisplacement::mapPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *ArnoldDisplacement::heightPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *ArnoldDisplacement::heightPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

Gaffer::FloatPlug *ArnoldDisplacement::paddingPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *ArnoldDisplacement::paddingPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::FloatPlug *ArnoldDisplacement::zeroValuePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::FloatPlug *ArnoldDisplacement::zeroValuePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

Gaffer::BoolPlug *ArnoldDisplacement::autoBumpPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::BoolPlug *ArnoldDisplacement::autoBumpPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

Gaffer::Plug *ArnoldDisplacement::outPlug()
{
	return getChild<Plug>( g_firstPlugIndex + 5 );
}

const Gaffer::Plug *ArnoldDisplacement::outPlug() const
{
	return getChild<Plug>( g_firstPlugIndex + 5 );
}

bool ArnoldDisplacement::affectsAttributes( const Gaffer::Plug *input ) const
{
	return
		Shader::affectsAttributes( input ) ||
		input == mapPlug() ||
		input == heightPlug() ||
		input == paddingPlug() ||
		input == zeroValuePlug() ||
		input == autoBumpPlug()
	;
}

void ArnoldDisplacement::attributesHash( const Gaffer::Plug *output, IECore::MurmurHash &h ) const
{
	h.append( typeId() );
	if( !enabledPlug()->getValue() )
	{
		return;
	}

	h.append( mapPlug()->attributesHash() );
	heightPlug()->hash( h );
	paddingPlug()->hash( h );
	zeroValuePlug()->hash( h );
	autoBumpPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr ArnoldDisplacement::attributes( const Gaffer::Plug *output ) const
{
	CompoundObjectPtr result = new CompoundObject;
	if( !enabledPlug()->getValue() )
	{
		return result;
	}

	CompoundObject::ObjectMap &m = result->members();
	m = mapPlug()->attributes()->members();

	for( InternedString *n = g_mapInputAttributeNames; *n != InternedString(); ++n )
	{
		CompoundObject::ObjectMap::iterator it = m.find( *n );
		if( it != m.end() )
		{
			m[g_mapAttributeName] = it->second;
			m.erase( it );
			break;
		}
	}

	m[g_heightAttributeName] = new FloatData( heightPlug()->getValue() );
	m[g_paddingAttributeName] = new FloatData( paddingPlug()->getValue() );
	m[g_zeroValueAttributeName] = new FloatData( zeroValuePlug()->getValue() );
	if ( !autoBumpPlug()->isSetToDefault() )
	{
		m[g_autoBumpAttributeName] = new BoolData( autoBumpPlug()->getValue() );
	}
	return result;
}

bool ArnoldDisplacement::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
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
