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

#include "GafferScene/OptionTweaks.h"

#include "Gaffer/TweakPlug.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( OptionTweaks );

const std::string g_namePrefix = "option:";

size_t OptionTweaks::g_firstPlugIndex = 0;

OptionTweaks::OptionTweaks( const std::string &name ) : GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new BoolPlug( "ignoreMissing", Plug::In, false ) );
	addChild( new TweaksPlug( "tweaks" ) );
}

OptionTweaks::~OptionTweaks()
{

}

Gaffer::BoolPlug *OptionTweaks::ignoreMissingPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex );
}

const Gaffer::BoolPlug *OptionTweaks::ignoreMissingPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex );
}

Gaffer::TweaksPlug *OptionTweaks::tweaksPlug()
{
	return getChild<Gaffer::TweaksPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::TweaksPlug *OptionTweaks::tweaksPlug() const
{
	return getChild<Gaffer::TweaksPlug>( g_firstPlugIndex + 1 );
}

void OptionTweaks::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( tweaksPlug()->isAncestorOf( input ) || input == ignoreMissingPlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void OptionTweaks::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( tweaksPlug()->children().empty() )
	{
		h = inPlug()->globalsPlug()->hash();
	}
	else
	{
		ignoreMissingPlug()->hash( h );
		tweaksPlug()->hash( h );
	}
}

IECore::ConstCompoundObjectPtr OptionTweaks::computeProcessedGlobals(
	const Gaffer::Context *context,
	const IECore::ConstCompoundObjectPtr inputGlobals
) const
{
	const TweaksPlug *tweaksPlug = this->tweaksPlug();
	if( tweaksPlug->children().empty() )
	{
		return inputGlobals;
	}

	const bool ignoreMissing = ignoreMissingPlug()->getValue();

	CompoundObjectPtr result = new CompoundObject();
	result->members() = inputGlobals->members();

	const CompoundObject *source = inputGlobals.get();

	tweaksPlug->applyTweaks(
		[&source]( const std::string &valueName )
		{
			return source->member<Data>( g_namePrefix + valueName );
		},
		[&result]( const std::string &valueName, DataPtr newData )
		{
			if( newData == nullptr )
			{
				return result->members().erase( g_namePrefix + valueName ) > 0;
			}
			result->members()[g_namePrefix + valueName] = newData;
			return true;
		},
		ignoreMissing ? TweakPlug::MissingMode::Ignore : TweakPlug::MissingMode::Error
	);

	return result;
}
