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

#include "IECore/NullObject.h"
#include "IECore/Shader.h"
#include "IECore/Light.h"
#include "IECore/MessageHandler.h"

#include "Gaffer/StringPlug.h"

#include "GafferScene/Light.h"
#include "GafferScene/PathMatcherData.h"

using namespace Gaffer;
using namespace GafferScene;

static IECore::InternedString g_lightsSetName( "__lights" );

IE_CORE_DEFINERUNTIMETYPED( Light );

size_t Light::g_firstPlugIndex = 0;

Light::Light( const std::string &name )
	:	ObjectSource( name, "light" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Plug( "parameters" ) );
}

Light::~Light()
{
}

Gaffer::Plug *Light::parametersPlug()
{
	return getChild<Plug>( g_firstPlugIndex );
}

const Gaffer::Plug *Light::parametersPlug() const
{
	return getChild<Plug>( g_firstPlugIndex );
}

void Light::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if( parametersPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}

}

void Light::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstObjectPtr Light::computeSource( const Context *context ) const
{
	// The light node now creates a new location in the scene, but just assigns attributes to it,
	// and doesn't create an object here
	return IECore::NullObject::defaultNullObject();
}


void Light::hashAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	hashLight( context, h );
}

IECore::ConstCompoundObjectPtr Light::computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::CompoundObjectPtr result = new IECore::CompoundObject;

	std::string lightAttribute = "light";

	IECore::ObjectVectorPtr lightShaders = computeLight( context );
	if( lightShaders->members().size() )
	{
		if( const IECore::Shader *shader = IECore::runTimeCast<const IECore::Shader>( lightShaders->members().back().get() ) )
		{
			lightAttribute = shader->getType();
		}
		else if( const IECore::Light *light = IECore::runTimeCast<const IECore::Light>( lightShaders->members().back().get() ) )
		{
			/// \todo We are phasing out the use of IECore::Light and replacing
			/// it with IECore::Shader everywhere. Make sure no derived classes
			/// are using it and then remove this special case code.
			IECore::msg( IECore::Msg::Warning, "Light::computeAttributes", "The use of IECore::Light is deprecated - please use IECore::Shader instead." );
			const std::string &lightName = light->getName();
			size_t colon = lightName.find( ":" );
			if( colon != std::string::npos )
			{
				lightAttribute = lightName.substr( 0, colon ) + ":light";
			}
		}
	}

	result->members()[lightAttribute] = lightShaders;

	return result;
}

IECore::ConstInternedStringVectorDataPtr Light::computeStandardSetNames() const
{
	IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData();
	result->writable().push_back( g_lightsSetName );
	return result;
}
