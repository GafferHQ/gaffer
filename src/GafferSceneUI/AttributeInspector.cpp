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

#include "GafferSceneUI/Private/AttributeInspector.h"

#include "GafferScene/Attributes.h"
#include "GafferScene/AttributeTweaks.h"
#include "GafferScene/Camera.h"
#include "GafferScene/EditScopeAlgo.h"
#include "GafferScene/Light.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/SceneNode.h"

#include "Gaffer/Private/IECorePreview/LRUCache.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/NameValuePlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/ParallelAlgo.h"
#include "Gaffer/ValuePlug.h"

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

struct AttributeHistoryCacheKey : public HistoryCacheKey
{
	AttributeHistoryCacheKey() {};
	AttributeHistoryCacheKey( const ScenePlug *plug, IECore::InternedString attribute )
		:	HistoryCacheKey( plug->attributesPlug() ), attribute( attribute )
	{
	}

	bool operator==( const AttributeHistoryCacheKey &rhs ) const
	{
		return HistoryCacheKey::operator==( rhs ) && attribute == rhs.attribute;
	}

	IECore::InternedString attribute;
};

size_t hash_value( const AttributeHistoryCacheKey &key )
{
	size_t result = 0;
	boost::hash_combine( result, static_cast<const HistoryCacheKey &>( key ) );
	boost::hash_combine( result, key.attribute.c_str() );
	return result;
}

using AttributeHistoryCache = IECorePreview::LRUCache<AttributeHistoryCacheKey, SceneAlgo::History::ConstPtr>;

AttributeHistoryCache g_attributeHistoryCache(
	// Getter
	[] ( const AttributeHistoryCacheKey &key, size_t &cost, const IECore::Canceller *canceller ) -> SceneAlgo::History::ConstPtr {
		assert( canceller == Context::current()->canceller() );
		cost = 1;
		SceneAlgo::History::ConstPtr attributesHistory = g_historyCache.get( key, canceller );
		if( auto h = SceneAlgo::attributeHistory( attributesHistory.get(), key.attribute ) )
		{
			return h;
		}
		else
		{
			// The specific attribute doesn't exist. But we return the history for the
			// whole CompoundObject so we get a chance to discover nodes that could
			// _create_ the attribute.
			return attributesHistory;
		}
	},
	// Max cost
	1000,
	// Removal callback
	[] ( const AttributeHistoryCacheKey &key, const SceneAlgo::History::ConstPtr &history ) {
		// See comment in g_historyCache
		ParallelAlgo::callOnUIThread(
			[history] () {}
		);
	}

);

Gaffer::ValuePlugPtr attributePlug( const Gaffer::CompoundDataPlug *parentPlug, const std::string &attributeName )
{
	for( const auto &plug : Gaffer::NameValuePlug::Range( *parentPlug ) )
	{
		if(plug->namePlug()->getValue() == attributeName )
		{
			return plug;
		}
	}
	return nullptr;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// AttributeInspector
//////////////////////////////////////////////////////////////////////////

AttributeInspector::AttributeInspector(
	const GafferScene::ScenePlugPtr &scene,
	const Gaffer::PlugPtr &editScope,
	IECore::InternedString attribute,
	const std::string &name,
	const std::string &type
) :
Inspector( type, name == "" ? attribute.string() : name, editScope ),
m_scene( scene ),
m_attribute( attribute )
{
	m_scene->node()->plugDirtiedSignal().connect(
		boost::bind( &AttributeInspector::plugDirtied, this, ::_1 )
	);

	Metadata::plugValueChangedSignal().connect( boost::bind( &AttributeInspector::plugMetadataChanged, this, ::_3, ::_4 ) );
	Metadata::nodeValueChangedSignal().connect( boost::bind( &AttributeInspector::nodeMetadataChanged, this, ::_2, ::_3 ) );
}

GafferScene::SceneAlgo::History::ConstPtr AttributeInspector::history() const
{
	if( !m_scene->exists() )
	{
		return nullptr;
	}

	return g_attributeHistoryCache.get( AttributeHistoryCacheKey( m_scene.get(), m_attribute ), Context::current()->canceller() );
}

IECore::ConstObjectPtr AttributeInspector::value( const GafferScene::SceneAlgo::History *history ) const
{
	if( auto attributeHistory = dynamic_cast<const SceneAlgo::AttributeHistory *>( history ) )
	{
		return attributeHistory->attributeValue;
	}
	// Attribute doesn't exist.
	return nullptr;
}

Gaffer::ValuePlugPtr AttributeInspector::source( const GafferScene::SceneAlgo::History *history, std::string &editWarning ) const
{
	auto sceneNode = runTimeCast<SceneNode>( history->scene->node() );
	if( !sceneNode || history->scene != sceneNode->outPlug() )
	{
		return nullptr;
	}

	if( auto light = runTimeCast<Light>( sceneNode ) )
	{
		return attributePlug( light->visualiserAttributesPlug(), m_attribute );
	}

	else if( auto camera = runTimeCast<GafferScene::Camera>( sceneNode ) )
	{
		return attributePlug( camera->visualiserAttributesPlug(), m_attribute );
	}

	else if( auto attributes = runTimeCast<GafferScene::Attributes>( sceneNode ) )
	{
		if( !(attributes->filterPlug()->match( attributes->inPlug() ) & PathMatcher::ExactMatch ) )
		{
			return nullptr;
		}

		for( const auto &plug : NameValuePlug::Range( *attributes->attributesPlug() ) )
		{
			if(
				plug->namePlug()->getValue() == m_attribute.string() &&
				plug->enabledPlug()->getValue()
			)
			{
				/// \todo This is overly conservative. We should test to see if there is more than
				/// one filter match (but make sure to early-out once two are found, rather than test
				/// the rest of the scene).
				editWarning = boost::str(
					boost::format( "Edits to \"%s\" may affect other locations in the scene." )
						% m_attribute.string()
				);
				return plug;
			}
		}
	}

	else if( auto attributeTweaks = runTimeCast<AttributeTweaks>( sceneNode ) )
	{
		if( !( attributeTweaks->filterPlug()->match( attributeTweaks->inPlug() ) & PathMatcher::ExactMatch ) )
		{
			return nullptr;
		}

		for( const auto &tweak : TweakPlug::Range( *attributeTweaks->tweaksPlug() ) )
		{
			if(
				tweak->namePlug()->getValue() == m_attribute.string() &&
				tweak->enabledPlug()->getValue()
			)
			{
				return tweak;
			}
		}
	}

	return nullptr;
}

Inspector::EditFunctionOrFailure AttributeInspector::editFunction( Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history ) const
{
	InternedString attributeName = m_attribute;
	if( auto attributeHistory = dynamic_cast<const SceneAlgo::AttributeHistory *>( history ) )
	{
		attributeName = attributeHistory->attributeName;
	}

	const GraphComponent *readOnlyReason = EditScopeAlgo::attributeEditReadOnlyReason(
		editScope,
		history->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ),
		attributeName
	);

	if( readOnlyReason )
	{
		// If we don't have an edit and the scope is locked, we error,
		// as we can't add an edit. Other cases where we already _have_
		// an edit will have been found by `source()`.
		return boost::str(
			boost::format( "%s is locked." ) % readOnlyReason->relativeName( readOnlyReason->ancestor<ScriptNode>() )
		);
	}
	else
	{
		return [
			editScope = EditScopePtr( editScope ),
			attributeName,
			context = history->context
		] () {
			Context::Scope scope( context.get() );
			return EditScopeAlgo::acquireAttributeEdit(
				editScope.get(),
				context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ),
				attributeName
			);
		};
	}
}

void AttributeInspector::plugDirtied( Gaffer::Plug *plug )
{
	if( plug == m_scene->attributesPlug() )
	{
		dirtiedSignal()( this );
	}
}

void AttributeInspector::plugMetadataChanged( IECore::InternedString key, const Gaffer::Plug *plug )
{
	if( !plug )
	{
		// Assume readOnly metadata is only registered on instances.
		return;
	}
	nodeMetadataChanged( key, plug->node() );
}

void AttributeInspector::nodeMetadataChanged( IECore::InternedString key, const Gaffer::Node *node )
{
	if( !node )
	{
		// Assume readOnly metadata is only registered on instances.
		return;
	}

	EditScope *scope = targetEditScope();
	if( !scope )
	{
		return;
	}

	if(
		MetadataAlgo::readOnlyAffectedByChange( scope, node, key ) ||
		( MetadataAlgo::readOnlyAffectedByChange( key ) && scope->isAncestorOf( node ) )
	)
	{
		// Might affect `EditScopeAlgo::attributeEditReadOnlyReason()`
		// which we call in `editFunction()`.
		/// \todo Can we ditch the signal processing and call `attributeEditReadOnlyReason()`
		/// just-in-time from `editable()`? In the past that wasn't possible
		/// because editability changed the appearance of the UI, but it isn't
		/// doing that currently.
		dirtiedSignal()( this );
	}
}

bool AttributeInspector::attributeExists() const
{

	if( !m_scene->existsPlug()->getValue() )
	{
		return false;
	}

	ConstCompoundObjectPtr attributes = m_scene->attributesPlug()->getValue();
	auto m = attributes->members();
	return m.find( m_attribute ) != m.end();

}
