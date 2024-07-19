//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferSceneUI/Private/OptionInspector.h"

#include "GafferScene/Options.h"
#include "GafferScene/OptionTweaks.h"
#include "GafferScene/EditScopeAlgo.h"

#include "Gaffer/Private/IECorePreview/LRUCache.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/ParallelAlgo.h"

#include "boost/bind/bind.hpp"

#include "fmt/format.h"

using namespace boost::placeholders;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI::Private;

namespace
{

const std::string g_emptyString( "" );
const std::string g_optionPrefix( "option:" );
const InternedString g_renderPassContextName( "renderPass" );
const InternedString g_defaultValue( "defaultValue" );

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
			key.plug
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

struct OptionHistoryCacheKey : public HistoryCacheKey
{
	OptionHistoryCacheKey() {};
	OptionHistoryCacheKey( const ScenePlug *plug, IECore::InternedString option )
		:	HistoryCacheKey( plug->globalsPlug() ), option( option )
	{
	}

	bool operator==( const OptionHistoryCacheKey &rhs ) const
	{
		return HistoryCacheKey::operator==( rhs ) && option == rhs.option;
	}

	IECore::InternedString option;
};

size_t hash_value( const OptionHistoryCacheKey &key )
{
	size_t result = 0;
	boost::hash_combine( result, static_cast<const HistoryCacheKey &>( key ) );
	boost::hash_combine( result, key.option.c_str() );
	return result;
}

using OptionHistoryCache = IECorePreview::LRUCache<OptionHistoryCacheKey, SceneAlgo::History::ConstPtr>;

OptionHistoryCache g_optionHistoryCache(
	// Getter
	[] ( const OptionHistoryCacheKey &key, size_t &cost, const IECore::Canceller *canceller ) -> SceneAlgo::History::ConstPtr {
		assert( canceller == Context::current()->canceller() );
		cost = 1;
		SceneAlgo::History::ConstPtr globalsHistory = g_historyCache.get( key, canceller );
		if( auto h = SceneAlgo::optionHistory( globalsHistory.get(), key.option ) )
		{
			return h;
		}
		else
		{
			// The specific option doesn't exist. But we return the history for the
			// whole CompoundObject so we get a chance to discover nodes that could
			// _create_ the option.
			return globalsHistory;
		}
	},
	// Max cost
	1000,
	// Removal callback
	[] ( const OptionHistoryCacheKey &key, const SceneAlgo::History::ConstPtr &history ) {
		// See comment in g_historyCache
		ParallelAlgo::callOnUIThread(
			[history] () {}
		);
	}

);

}  // namespace

OptionInspector::OptionInspector(
	const GafferScene::ScenePlugPtr &scene,
	const Gaffer::PlugPtr &editScope,
	IECore::InternedString option
) :
Inspector( "option", option.string(), editScope ),
m_scene( scene ),
m_option( option )
{
	m_scene->node()->plugDirtiedSignal().connect(
		boost::bind( &OptionInspector::plugDirtied, this, ::_1 )
	);

	Metadata::plugValueChangedSignal().connect( boost::bind( &OptionInspector::plugMetadataChanged, this, ::_3, ::_4 ) );
	Metadata::nodeValueChangedSignal().connect( boost::bind( &OptionInspector::nodeMetadataChanged, this, ::_2, ::_3 ) );
}

GafferScene::SceneAlgo::History::ConstPtr OptionInspector::history() const
{
	return g_optionHistoryCache.get( OptionHistoryCacheKey( m_scene.get(), m_option ), Context::current()->canceller() );
}

IECore::ConstObjectPtr OptionInspector::value( const GafferScene::SceneAlgo::History *history ) const
{
	if( auto optionHistory = dynamic_cast<const SceneAlgo::OptionHistory *>( history ) )
	{
		return optionHistory->optionValue;
	}
	// Option doesn't exist.
	return nullptr;
}

IECore::ConstObjectPtr OptionInspector::fallbackValue( const GafferScene::SceneAlgo::History *history ) const
{
	if( const auto defaultValue = Gaffer::Metadata::value( g_optionPrefix + m_option.string(), g_defaultValue ) )
	{
		return defaultValue;
	}

	return nullptr;
}

Gaffer::ValuePlugPtr OptionInspector::source( const GafferScene::SceneAlgo::History *history, std::string &editWarning ) const
{
	auto sceneNode = runTimeCast<SceneNode>( history->scene->node() );
	if( !sceneNode || history->scene != sceneNode->outPlug() )
	{
		return nullptr;
	}

	/// \todo Should we provide an `editWarning` here for render pass specific
	/// edits that may affect other render passes?
	if( auto options = runTimeCast<GafferScene::Options>( sceneNode ) )
	{
		for( const auto &plug : NameValuePlug::Range( *options->optionsPlug() ) )
		{
			if(
				plug->namePlug()->getValue() == m_option.string() &&
				( !plug->enabledPlug() || plug->enabledPlug()->getValue() )
			)
			{
				return plug;
			}
		}
	}
	else if( auto optionTweaks = runTimeCast<OptionTweaks>( sceneNode ) )
	{
		for( const auto &tweak : TweakPlug::Range( *optionTweaks->tweaksPlug() ) )
		{
			if( tweak->namePlug()->getValue() == m_option.string() && tweak->enabledPlug()->getValue() )
			{
				return tweak;
			}
		}
	}

	return nullptr;
}

Inspector::EditFunctionOrFailure OptionInspector::editFunction( Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history ) const
{
	// If our history's context contains a non-empty `renderPass` variable,
	// we'll want to make a specific edit for that render pass.
	const std::string renderPass = history->context->get<std::string>( g_renderPassContextName, g_emptyString );
	if( !renderPass.empty() )
	{
		const GraphComponent *readOnlyReason = EditScopeAlgo::renderPassOptionEditReadOnlyReason(
			editScope,
			renderPass,
			m_option
		);

		if( readOnlyReason )
		{
			// If we don't have an edit and the scope is locked, we error,
			// as we can't add an edit. Other cases where we already _have_
			// an edit will have been found by `source()`.
			return fmt::format(
				"{} is locked.",
				readOnlyReason->relativeName( readOnlyReason->ancestor<ScriptNode>() )
			);
		}
		else
		{
			return [
				editScope = EditScopePtr( editScope ),
				renderPass,
				option = m_option,
				context = history->context
			] () {
				Context::Scope scope( context.get() );
				return EditScopeAlgo::acquireRenderPassOptionEdit(
					editScope.get(),
					renderPass,
					option
				);
			};
		}
	}
	else
	{
		const GraphComponent *readOnlyReason = EditScopeAlgo::optionEditReadOnlyReason(
			editScope,
			m_option
		);

		if( readOnlyReason )
		{
			// If we don't have an edit and the scope is locked, we error,
			// as we can't add an edit. Other cases where we already _have_
			// an edit will have been found by `source()`.
			return fmt::format(
				"{} is locked.",
				readOnlyReason->relativeName( readOnlyReason->ancestor<ScriptNode>() )
			);
		}
		else
		{
			return [
				editScope = EditScopePtr( editScope ),
				option = m_option,
				context = history->context
			] () {
				Context::Scope scope( context.get() );
				return EditScopeAlgo::acquireOptionEdit(
					editScope.get(),
					option
				);
			};
		}
	}
}

void OptionInspector::plugDirtied( Gaffer::Plug *plug )
{
	if( plug == m_scene->globalsPlug() )
	{
		dirtiedSignal()( this );
	}
}

void OptionInspector::plugMetadataChanged( IECore::InternedString key, const Gaffer::Plug *plug )
{
	if( !plug )
	{
		// Assume readOnly metadata is only registered on instances.
		return;
	}
	nodeMetadataChanged( key, plug->node() );
}

void OptionInspector::nodeMetadataChanged( IECore::InternedString key, const Gaffer::Node *node )
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
		// Might affect `EditScopeAlgo::optionEditReadOnlyReason()`
		// which we call in `editFunction()`.
		/// \todo Can we ditch the signal processing and call `optionEditReadOnlyReason()`
		/// just-in-time from `editable()`? In the past that wasn't possible
		/// because editability changed the appearance of the UI, but it isn't
		/// doing that currently.
		dirtiedSignal()( this );
	}
}
