//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferSceneUI/Private/TransformInspector.h"

#include "GafferScene/Constraint.h"
#include "GafferScene/EditScopeAlgo.h"
#include "GafferScene/FramingConstraint.h"
#include "GafferScene/Grid.h"
#include "GafferScene/Group.h"
#include "GafferScene/ObjectSource.h"
#include "GafferScene/Transform.h"

#include "Gaffer/Private/IECorePreview/LRUCache.h"
#include "Gaffer/ParallelAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/TransformPlug.h"

#include "IECore/AngleConversion.h"

#include "Imath/ImathMatrixAlgo.h"

#include "fmt/format.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI::Private;

//////////////////////////////////////////////////////////////////////////
// History cache
//////////////////////////////////////////////////////////////////////////

namespace
{

// This uses the same strategy that ValuePlug uses for the hash cache,
// using `plug->dirtyCount()` to invalidate previous cache entries when
// a plug is dirtied.
struct HistoryCacheKey
{
	HistoryCacheKey() {};
	HistoryCacheKey( const ValuePlug *plug )
		:	plug( plug ), contextHash( Context::current()->hash() ), dirtyCount( plug->dirtyCount() )
	{
	}

	bool operator==( const HistoryCacheKey &rhs ) const
	{
		return
			plug == rhs.plug &&
			contextHash == rhs.contextHash &&
			dirtyCount == rhs.dirtyCount
		;
	}

	const ValuePlug *plug;
	IECore::MurmurHash contextHash;
	uint64_t dirtyCount;
};

size_t hash_value( const HistoryCacheKey &key )
{
	size_t result = 0;
	boost::hash_combine( result, key.plug );
	boost::hash_combine( result, key.contextHash );
	boost::hash_combine( result, key.dirtyCount );
	return result;
}

using HistoryCache = IECorePreview::LRUCache<HistoryCacheKey, SceneAlgo::History::ConstPtr>;

HistoryCache g_historyCache(
	// Getter
	[] ( const HistoryCacheKey &key, size_t &cost, const IECore::Canceller *canceller ) {
		assert( canceller == Context::current()->canceller() );
		cost = 1;
		return SceneAlgo::history(
			key.plug, Context::current()->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName )
		);
	},
	// Max cost
	1000,
	// Removal callback
	[] ( const HistoryCacheKey &key, const SceneAlgo::History::ConstPtr &history ) {
		// Histories contain PlugPtrs, which could potentially be the sole
		// owners. Destroying plugs can trigger dirty propagation, so as a
		// precaution we destroy the history on the UI thread, where this would
		// be OK.
		ParallelAlgo::callOnUIThread(
			[history] () {}
		);
	}

);

} // namespace

//////////////////////////////////////////////////////////////////////////
// TransformInspector
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( TransformInspector )

TransformInspector::TransformInspector(
	const GafferScene::ScenePlugPtr &scene,
	const Gaffer::PlugPtr &editScope,
	Space space,
	Component component
)
	:	Inspector( { scene->transformPlug() }, "Transform", fmt::format( "{} {}", toString( space ), toString( component ) ), editScope ),
		m_scene( scene ), m_space( space ), m_component( component )
{
}

GafferScene::SceneAlgo::History::ConstPtr TransformInspector::history() const
{
	if( !m_scene->existsPlug()->getValue() )
	{
		return nullptr;
	}

	return g_historyCache.get( HistoryCacheKey( m_scene->transformPlug() ), Context::current()->canceller() );
}

IECore::ConstObjectPtr TransformInspector::value( const GafferScene::SceneAlgo::History *history ) const
{
	const M44f matrix =
		m_space == Space::Local ?
			history->scene->transformPlug()->getValue()
		:
			history->scene->fullTransform( Context::current()->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ) )
	;

	if( m_component == Component::Matrix )
	{
		return new M44fData( matrix );
	}

	V3f s, h, r, t;
	extractSHRT( matrix, s, h, r, t );
	switch( m_component )
	{
		case Component::Translate : return new V3fData( t );
		case Component::Rotate : return new V3fData( IECore::radiansToDegrees( r ) );
		case Component::Scale : return new V3fData( s );
		default : return new V3fData( h );
	}
}

bool TransformInspector::hasEdit( const GafferScene::SceneAlgo::History *history ) const
{
	if( m_space == Space::Local )
	{
		return transformPlug( history ) || Inspector::hasEdit( history );
	}
	else
	{
		// The world space transform is derived from the local transforms of
		// all ancestors, so doesn't have a single source.
		return false;
	}
}

Gaffer::ValuePlugPtr TransformInspector::acquireEdit( const GafferScene::SceneAlgo::History *history, bool createIfNecessary, bool dryRun ) const
{
	if( m_space != Space::Local )
	{
		throw EditDisallowed( "World space transform cannot be edited." );
	}

	if( TransformPlug *transformPlug = this->transformPlug( history ) )
	{
		if( const Transform *transform = runTimeCast<const Transform>( transformPlug->node() ) )
		{
			if( transform->spacePlug()->getValue() != Transform::ResetLocal )
			{
				// Values entered in `transformPlug()` don't directly correspond to the
				// values returned by `value()`, not meeting the user's expectations
				// for an acquired edit.
				return Inspector::acquireEdit( history, createIfNecessary, dryRun );
			}
		}

		switch( m_component )
		{
			case Component::Matrix :
				return transformPlug;
			case Component::Translate :
				return transformPlug->translatePlug();
			case Component::Rotate :
				return transformPlug->rotatePlug();
			case Component::Scale :
				return transformPlug->scalePlug();
			default :
				// No plug for shear.
				break;
		}
	}

	return Inspector::acquireEdit( history, createIfNecessary, dryRun );
}

Gaffer::ValuePlugPtr TransformInspector::acquireEdit( Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history, bool createIfNecessary, bool dryRun ) const
{
	if( m_space != Space::Local )
	{
		throw EditDisallowed( "World space transform cannot be edited." );
	}
	// We'd like to use `EditScopeAlgo::acquireTransformEdit()`, but that makes
	// edits for translate, rotate, and scale all at once. Since we purport to
	// deal with only a single Component, that would be surprising/confusing.
	/// \todo Make this work. One possibility might be this :
	///
	/// 1. We switch `ScenePlug::transformPlug()` to pass data with separate components,
	///    rather than a single matrix.
	/// 2. We then update the Transform node to optionally edit only specific components.
	/// 3. `acquireTransformEdit()` returns plugs including an `enabledPlug()` to let
	///    us edit just one component.
	throw EditDisallowed( "Edit creation not supported yet. Use the transform tools in the Viewer instead." );
}

const char *TransformInspector::toString( Space space )
{
	return space == Space::Local ? "Local" : "World";
}

const char *TransformInspector::toString( Component component )
{
	switch( component )
	{
		case Component::Matrix : return "Matrix";
		case Component::Translate : return "Translate";
		case Component::Rotate : return "Rotate";
		case Component::Scale : return "Scale";
		default : return "Shear";
	}
}

Gaffer::TransformPlug *TransformInspector::transformPlug( const GafferScene::SceneAlgo::History *history ) const
{
	auto sceneNode = runTimeCast<SceneNode>( history->scene->node() );
	if( !sceneNode || history->scene != sceneNode->outPlug() || !sceneNode->enabledPlug()->getValue() )
	{
		return nullptr;
	}

	const ScenePlug::ScenePath &path = history->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );

	if( const ObjectSource *objectSource = runTimeCast<const ObjectSource>( sceneNode ) )
	{
		if( path.size() == 1 )
		{
			return const_cast<TransformPlug *>( objectSource->transformPlug() );
		}
	}
	else if( const Group *group = runTimeCast<const Group>( sceneNode ) )
	{
		if( path.size() == 1 )
		{
			return const_cast<TransformPlug *>( group->transformPlug() );
		}
	}
	else if( const Grid *grid = runTimeCast<const Grid>( sceneNode ) )
	{
		if( path.size() == 1 )
		{
			return const_cast<TransformPlug *>( grid->transformPlug() );
		}
	}
	else if( const Transform *transform = runTimeCast<const Transform>( sceneNode ) )
	{
		if( !( transform->filterPlug()->match( transform->inPlug() ) & PathMatcher::ExactMatch ) )
		{
			return nullptr;
		}
		return const_cast<TransformPlug *>( transform->transformPlug() );
	}

	return nullptr;
}
