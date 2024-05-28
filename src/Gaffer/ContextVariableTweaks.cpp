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

#include "Gaffer/ContextVariableTweaks.h"

#include "IECore/DataAlgo.h"
#include "IECore/ObjectVector.h"

using namespace IECore;
using namespace Gaffer;

GAFFER_NODE_DEFINE_TYPE( ContextVariableTweaks );

size_t ContextVariableTweaks::g_firstPlugIndex = 0;

ContextVariableTweaks::ContextVariableTweaks( const std::string &name ) : ContextProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new BoolPlug( "ignoreMissing", Plug::In, false ) );
	addChild( new TweaksPlug ( "tweaks" ) );
}

ContextVariableTweaks::~ContextVariableTweaks()
{

}

Gaffer::BoolPlug *ContextVariableTweaks::ignoreMissingPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

const Gaffer::BoolPlug *ContextVariableTweaks::ignoreMissingPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

Gaffer::TweaksPlug *ContextVariableTweaks::tweaksPlug()
{
	return getChild<TweaksPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::TweaksPlug *ContextVariableTweaks::tweaksPlug() const
{
	return getChild<TweaksPlug>( g_firstPlugIndex + 1 );
}

bool ContextVariableTweaks::affectsContext( const Plug *input ) const
{
	return tweaksPlug()->isAncestorOf( input ) || input == ignoreMissingPlug();
}

void ContextVariableTweaks::processContext( Context::EditableScope &context, IECore::ConstRefCountedPtr &storage ) const
{
	const TweaksPlug *tweaksPlug = this->tweaksPlug();
	if( tweaksPlug->children().empty() )
	{
		return;
	}

	const bool ignoreMissing = ignoreMissingPlug()->getValue();

	IECore::ConstDataPtr sourceData;
	IECore::ObjectVectorPtr storageVector = new ObjectVector();

	tweaksPlug->applyTweaks(
		[&context, &sourceData]( const std::string &valueName, const bool withFallback )
		{
			DataPtr value = context.context()->getAsData( valueName, nullptr );
			sourceData = value;
			return value.get();
		},
		[&context, &storageVector]( const std::string &valueName, DataPtr newData )
		{
			if( newData == nullptr )
			{
				context.remove( valueName );
				return true;
			}

			context.set( valueName, newData.get() );
			storageVector->members().push_back( newData );

			return true;
		},
		ignoreMissing ? TweakPlug::MissingMode::Ignore : TweakPlug::MissingMode::Error
	);

	storage = storageVector;
}
