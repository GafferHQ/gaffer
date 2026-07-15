//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/CopyObject.h"

#include "GafferScene/SceneAlgo.h"

#include "IECore/NullObject.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( GafferScene::CopyObject );

size_t CopyObject::g_firstPlugIndex = 0;

CopyObject::CopyObject( const std::string &name )
	:	FilteredSceneProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "source" ) );
	addChild( new StringPlug( "sourceLocation" ) );
	addChild( new BoolPlug( "adjustBounds", Plug::In, false ) );

	outPlug()->childBoundsPlug()->setFlags( Plug::AcceptsDependencyCycles, true );

	// Fast pass-throughs for things we don't modify
	outPlug()->childNamesPlug()->setInput( inPlug()->childNamesPlug() );
	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
	outPlug()->setPlug()->setInput( inPlug()->setPlug() );
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
}

CopyObject::~CopyObject()
{
}

GafferScene::ScenePlug *CopyObject::sourcePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *CopyObject::sourcePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *CopyObject::sourceLocationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *CopyObject::sourceLocationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *CopyObject::adjustBoundsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *CopyObject::adjustBoundsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

void CopyObject::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if(
		input == filterPlug() ||
		input == inPlug()->objectPlug() ||
		input == sourcePlug()->objectPlug() ||
		input == sourcePlug()->existsPlug() ||
		input == sourceLocationPlug()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}

	if(
		input == filterPlug() ||
		input == adjustBoundsPlug() ||
		input == inPlug()->boundPlug() ||
		input == outPlug()->objectPlug() ||
		input == outPlug()->childBoundsPlug()
	)
	{
		outputs.push_back( outPlug()->boundPlug() );
	}
}

void CopyObject::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( !(filterValue( context ) & IECore::PathMatcher::ExactMatch) )
	{
		h = inPlug()->objectPlug()->hash();
		return;
	}

	std::optional<ScenePath> sourceLocationPath;
	const string sourceLocation = sourceLocationPlug()->getValue();
	if( !sourceLocation.empty() )
	{
		ScenePlug::stringToPath( sourceLocation, sourceLocationPath.emplace() );
	}

	if( sourcePlug()->exists( sourceLocationPath ? *sourceLocationPath : path ) )
	{
		h = sourcePlug()->objectHash( sourceLocationPath ? *sourceLocationPath : path );
	}
	else
	{
		h = inPlug()->objectPlug()->hash();
	}
}

IECore::ConstObjectPtr CopyObject::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( !(filterValue( context ) & IECore::PathMatcher::ExactMatch) )
	{
		return inPlug()->objectPlug()->getValue();
	}

	std::optional<ScenePath> sourceLocationPath;
	const string sourceLocation = sourceLocationPlug()->getValue();
	if( !sourceLocation.empty() )
	{
		ScenePlug::stringToPath( sourceLocation, sourceLocationPath.emplace() );
	}

	if( sourcePlug()->exists( sourceLocationPath ? *sourceLocationPath : path ) )
	{
		return sourcePlug()->object( sourceLocationPath ? *sourceLocationPath : path );
	}
	else
	{
		return inPlug()->objectPlug()->getValue();
	}
}

void CopyObject::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( adjustBoundsPlug()->getValue() )
	{
		const IECore::PathMatcher::Result m = filterValue( context );
		if( m & ( IECore::PathMatcher::ExactMatch | IECore::PathMatcher::DescendantMatch ) )
		{
			FilteredSceneProcessor::hashBound( path, context, parent, h );
			outPlug()->childBoundsPlug()->hash( h );
			outPlug()->objectPlug()->hash( h );
			return;
		}
	}
	h = inPlug()->boundPlug()->hash();
}

Imath::Box3f CopyObject::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( adjustBoundsPlug()->getValue() )
	{
		const IECore::PathMatcher::Result m = filterValue( context );
		if( m & ( IECore::PathMatcher::ExactMatch | IECore::PathMatcher::DescendantMatch ) )
		{
			Box3f result = outPlug()->childBoundsPlug()->getValue();
			ConstObjectPtr o = outPlug()->objectPlug()->getValue();
			if( !runTimeCast<const NullObject>( o.get() ) )
			{
				result.extendBy( SceneAlgo::bound( o.get() ) );
			}
			return result;
		}
	}

	return inPlug()->boundPlug()->getValue();
}
