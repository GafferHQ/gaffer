//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/AttributeTweaks.h"

#include "Gaffer/TweakPlug.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

const ConstStringDataPtr g_linkedLightsDefault = new StringData( "defaultLights" );

} // namespace

GAFFER_NODE_DEFINE_TYPE( AttributeTweaks );

size_t AttributeTweaks::g_firstPlugIndex = 0;

AttributeTweaks::AttributeTweaks( const std::string &name ) : AttributeProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new BoolPlug( "localise", Plug::In, false ) );
	addChild( new BoolPlug( "ignoreMissing", Plug::In, false ) );
	addChild( new TweaksPlug( "tweaks" ) );
}

AttributeTweaks::~AttributeTweaks()
{

}

Gaffer::BoolPlug *AttributeTweaks::localisePlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex );
}

const Gaffer::BoolPlug *AttributeTweaks::localisePlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *AttributeTweaks::ignoreMissingPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *AttributeTweaks::ignoreMissingPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::TweaksPlug *AttributeTweaks::tweaksPlug()
{
	return getChild<Gaffer::TweaksPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::TweaksPlug *AttributeTweaks::tweaksPlug() const
{
	return getChild<Gaffer::TweaksPlug>( g_firstPlugIndex + 2 );
}

bool AttributeTweaks::affectsProcessedAttributes( const Gaffer::Plug *input) const
{
	return
		AttributeProcessor::affectsProcessedAttributes( input ) ||
		tweaksPlug()->isAncestorOf( input ) ||
		input == localisePlug() ||
		input == ignoreMissingPlug()
	;
}

void AttributeTweaks::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( tweaksPlug()->children().empty() )
	{
		h = inPlug()->attributesPlug()->hash();
	}
	else
	{
		AttributeProcessor::hashProcessedAttributes( path, context, h );
		localisePlug()->hash( h );

		if( localisePlug()->getValue() )
		{
			h.append( inPlug()->fullAttributesHash( path ) );
		}

		ignoreMissingPlug()->hash( h );
		tweaksPlug()->hash( h );
	}
}

IECore::ConstCompoundObjectPtr AttributeTweaks::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, const IECore::CompoundObject *inputAttributes ) const
{
	const TweaksPlug *tweaksPlug = this->tweaksPlug();
	if( tweaksPlug->children().empty() )
	{
		return inputAttributes;
	}

	const bool ignoreMissing = ignoreMissingPlug()->getValue();

	CompoundObjectPtr result = new CompoundObject();
	result->members() = inputAttributes->members();

	// We switch our source attributes depending on whether we are
	// localising inherted attributes or just using the ones at the location

	const CompoundObject *source = inputAttributes;

	ConstCompoundObjectPtr fullAttributes;
	if( localisePlug()->getValue() )
	{
		fullAttributes = inPlug()->fullAttributes( path );
		source = fullAttributes.get();
	}

	tweaksPlug->applyTweaks(
		[&source]( const std::string &valueName ) -> const IECore::Data *
		{
			const Data *result = source->member<Data>( valueName );
			if( !result && valueName == "linkedLights" )
			{
				/// \todo Use a registry to provide default values for
				/// all attributes.
				return g_linkedLightsDefault.get();
			}
			return result;
		},
		[&result]( const std::string &valueName, DataPtr newData )
		{
			if( newData == nullptr )
			{
				return result->members().erase( valueName ) > 0;
			}
			result->members()[valueName] = newData;
			return true;
		},
		ignoreMissing ? TweakPlug::MissingMode::Ignore : TweakPlug::MissingMode::Error
	);

	return result;
}
