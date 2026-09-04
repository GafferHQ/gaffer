//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//       *Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//       *Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//       *Neither the name of John Haddon nor the names of
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

#include "GafferScene/VisibilityQuery.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

const InternedString g_sceneVisible( "scene:visible" );

} // namespace

size_t VisibilityQuery::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( VisibilityQuery );

VisibilityQuery::VisibilityQuery( const std::string &name )
	:	Gaffer::ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "scene" ) );
	addChild( new Gaffer::StringPlug( "location" ) );
	addChild( new Gaffer::BoolPlug( "visible", Gaffer::Plug::Out, false ) );
	addChild( new Gaffer::StringVectorDataPlug( "invisibleAncestors", Gaffer::Plug::Out ) );
	addChild( new Gaffer::BoolVectorDataPlug( "__ancestorVisibility", Gaffer::Plug::Out ) );
}

VisibilityQuery::~VisibilityQuery()
{
}

ScenePlug *VisibilityQuery::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *VisibilityQuery::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *VisibilityQuery::locationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *VisibilityQuery::locationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *VisibilityQuery::visiblePlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *VisibilityQuery::visiblePlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringVectorDataPlug *VisibilityQuery::invisibleAncestorsPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringVectorDataPlug *VisibilityQuery::invisibleAncestorsPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 3 );
}

Gaffer::BoolVectorDataPlug *VisibilityQuery::ancestorVisibilityPlug()
{
	return getChild<BoolVectorDataPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::BoolVectorDataPlug *VisibilityQuery::ancestorVisibilityPlug() const
{
	return getChild<BoolVectorDataPlug>( g_firstPlugIndex + 4 );
}

void VisibilityQuery::affects( const Gaffer::Plug *const input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( affectsAncestorVisibility( input ) )
	{
		outputs.push_back( ancestorVisibilityPlug() );
	}

	if( affectsVisible( input ) )
	{
		outputs.push_back( visiblePlug() );
	}

	if( affectsInvisibleAncestors( input ) )
	{
		outputs.push_back( invisibleAncestorsPlug() );
	}
}

void VisibilityQuery::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == ancestorVisibilityPlug() )
	{
		hashAncestorVisibility( context, h );
	}
	else if( output == visiblePlug() )
	{
		hashVisible( context, h );
	}
	else if( output == invisibleAncestorsPlug() )
	{
		hashInvisibleAncestors( context, h );
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void VisibilityQuery::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == ancestorVisibilityPlug() )
	{
		static_cast<BoolVectorDataPlug *>( output )->setValue( computeAncestorVisibility( context ) );
	}
	else if( output == visiblePlug() )
	{
		static_cast<BoolPlug *>( output )->setValue( computeVisible( context ) );
	}
	else if( output == invisibleAncestorsPlug() )
	{
		static_cast<StringVectorDataPlug *>( output )->setValue( computeInvisibleAncestors( context ) );
	}
	else
	{
		ComputeNode::compute( output, context );
	}
}


bool VisibilityQuery::affectsAncestorVisibility( const Gaffer::Plug *input ) const
{
	return input == scenePlug()->attributesPlug();
}

void VisibilityQuery::hashAncestorVisibility( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const auto &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	if( !path.size() )
	{
		h = ancestorVisibilityPlug()->defaultHash();
		return;
	}

	ComputeNode::hash( ancestorVisibilityPlug(), context, h );

	{
		ScenePlug::ScenePath ancestorPath = path;
		ancestorPath.pop_back();
		ScenePlug::PathScope ancestorScope( context, &ancestorPath );
		ancestorVisibilityPlug()->hash( h );
	}

	scenePlug()->attributesPlug()->hash( h );
}

IECore::ConstBoolVectorDataPtr VisibilityQuery::computeAncestorVisibility( const Gaffer::Context *context ) const
{
	const auto &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	if( !path.size() )
	{
		return ancestorVisibilityPlug()->defaultValue();
	}

	BoolVectorDataPtr result;
	{
		ScenePlug::ScenePath ancestorPath = path;
		ancestorPath.pop_back();
		ScenePlug::PathScope ancestorScope( context, &ancestorPath );
		result = ancestorVisibilityPlug()->getValue()->copy();
	}

	ConstCompoundObjectPtr attributes = scenePlug()->attributesPlug()->getValue();
	const auto *visibleData = attributes->member<BoolData>( g_sceneVisible );
	result->writable().push_back( !visibleData || visibleData->readable() );

	return result;
}

bool VisibilityQuery::affectsAncestorVisibilityForLocation( const Gaffer::Plug *input ) const
{
	return
		input == locationPlug() ||
		input == scenePlug()->existsPlug() ||
		input == ancestorVisibilityPlug()
	;
}

void VisibilityQuery::hashAncestorVisibilityForLocation( const Gaffer::Context *context, IECore::MurmurHash &h, std::string *locationOut ) const
{
	const string location = locationPlug()->getValue();
	if( locationOut )
	{
		*locationOut = location;
	}

	if( location.empty() )
	{
		return;
	}

	auto path = ScenePlug::stringToPath( location );
	ScenePlug::PathScope scope( context, &path );
	if( !scenePlug()->existsPlug()->getValue() )
	{
		return;
	}

	ancestorVisibilityPlug()->hash( h );
}

ConstBoolVectorDataPtr VisibilityQuery::ancestorVisibilityForLocation( const Gaffer::Context *context, std::string *locationOut ) const
{
	const string location = locationPlug()->getValue();
	if( locationOut )
	{
		*locationOut = location;
	}

	if( location.empty() )
	{
		return nullptr;
	}

	auto path = ScenePlug::stringToPath( location );
	ScenePlug::PathScope scope( context, &path );
	if( !scenePlug()->existsPlug()->getValue() )
	{
		return nullptr;
	}

	return ancestorVisibilityPlug()->getValue();
}


bool VisibilityQuery::affectsVisible( const Gaffer::Plug *input ) const
{
	return affectsAncestorVisibilityForLocation( input );
}

void VisibilityQuery::hashVisible( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( visiblePlug(), context, h );
	hashAncestorVisibilityForLocation( context, h );
}

bool VisibilityQuery::computeVisible( const Gaffer::Context *context ) const
{
	ConstBoolVectorDataPtr v = ancestorVisibilityForLocation( context );
	return v && std::all_of(
		v->readable().begin(), v->readable().end(),
		[]( bool x ) { return x; }
	);
}

bool VisibilityQuery::affectsInvisibleAncestors( const Gaffer::Plug *input ) const
{
	return affectsAncestorVisibilityForLocation( input );
}

void VisibilityQuery::hashInvisibleAncestors( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( invisibleAncestorsPlug(), context, h );
	string location;
	hashAncestorVisibilityForLocation( context, h, &location );
	h.append( location );
}

IECore::ConstStringVectorDataPtr VisibilityQuery::computeInvisibleAncestors( const Gaffer::Context *context ) const
{
	string location;
	ConstBoolVectorDataPtr ancestorVisibilityData = ancestorVisibilityForLocation( context, &location );
	if( !ancestorVisibilityData )
	{
		return invisibleAncestorsPlug()->defaultValue();
	}

	const vector<bool> &ancestorVisibility = ancestorVisibilityData->readable();

	StringVectorDataPtr resultData = new StringVectorData;
	auto &result = resultData->writable();

	auto path = ScenePlug::stringToPath( location );
	string ancestor;

	assert( path.size() == ancestorVisibility.size() );
	for( size_t i = 0; i < path.size(); ++i )
	{
		ancestor += "/" + path[i].string();
		if( !ancestorVisibility[i] )
		{
			result.push_back( ancestor );
		}
	}

	return resultData;
}
