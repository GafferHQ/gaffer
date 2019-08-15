//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/CopyAttributes.h"

#include "Gaffer/ArrayPlug.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( CopyAttributes );

size_t CopyAttributes::g_firstPlugIndex = 0;

CopyAttributes::CopyAttributes( const std::string &name )
	:	FilteredSceneProcessor( name, 2, 2 )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "attributes", Plug::In, "*" ) );
	addChild( new StringPlug( "copyFrom" ) );
	addChild( new BoolPlug( "deleteExisting" ) );

	// Pass through everything except attributes.
	outPlug()->childNamesPlug()->setInput( inPlug()->childNamesPlug() );
	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
	outPlug()->setPlug()->setInput( inPlug()->setPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
}

CopyAttributes::~CopyAttributes()
{
}

Gaffer::StringPlug *CopyAttributes::attributesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *CopyAttributes::attributesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *CopyAttributes::copyFromPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *CopyAttributes::copyFromPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *CopyAttributes::deleteExistingPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *CopyAttributes::deleteExistingPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

void CopyAttributes::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	const ScenePlug *scenePlug = input->parent<ScenePlug>();
	if(
		( scenePlug && scenePlug->parent() == inPlugs() && input == scenePlug->attributesPlug() ) ||
		input == filterPlug() ||
		input == attributesPlug() ||
		input == copyFromPlug() ||
		input == deleteExistingPlug()
	)
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

void CopyAttributes::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( !( filterValue( context ) & IECore::PathMatcher::ExactMatch ) )
	{
		// Pass through
		h = inPlug()->attributesPlug()->hash();
		return;
	}

	FilteredSceneProcessor::hashAttributes( path, context, parent, h );
	if( !deleteExistingPlug()->getValue() )
	{
		inPlug()->attributesPlug()->hash( h );
	}
	const std::string copyFrom = copyFromPlug()->getValue();
	if( copyFrom.empty() )
	{
		inPlugs()->getChild<ScenePlug>( 1 )->attributesPlug()->hash( h );
	}
	else
	{
		ScenePlug::ScenePath copyFromPath;
		ScenePlug::stringToPath( copyFrom, copyFromPath );
		ScenePlug::PathScope pathScope( context, copyFromPath );
		inPlugs()->getChild<ScenePlug>( 1 )->attributesPlug()->hash( h );
	}

	attributesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr CopyAttributes::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( !( filterValue( context ) & IECore::PathMatcher::ExactMatch ) )
	{
		// Pass through
		return inPlug()->attributesPlug()->getValue();
	}

	CompoundObjectPtr result = new CompoundObject;
	if( !deleteExistingPlug()->getValue() )
	{
		result->members() = inPlug()->attributesPlug()->getValue()->members();
	}

	ConstCompoundObjectPtr sourceAttributes;
	const std::string copyFrom = copyFromPlug()->getValue();
	if( copyFrom.empty() )
	{
		sourceAttributes = inPlugs()->getChild<ScenePlug>( 1 )->attributesPlug()->getValue();
	}
	else
	{
		ScenePlug::ScenePath copyFromPath;
		ScenePlug::stringToPath( copyFrom, copyFromPath );
		ScenePlug::PathScope pathScope( context, copyFromPath );
		sourceAttributes = inPlugs()->getChild<ScenePlug>( 1 )->attributesPlug()->getValue();
	}

	const std::string matchPattern = attributesPlug()->getValue();
	for( const auto &attribute : sourceAttributes->members() )
	{
		if( StringAlgo::matchMultiple( attribute.first, matchPattern ) )
		{
			result->members()[attribute.first] = attribute.second;
		}
	}

	return result;
}
