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

#include "GafferSceneUI/Private/BasicInspector.h"

#include "Gaffer/ParallelAlgo.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"

using namespace boost::placeholders;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI::Private;


//////////////////////////////////////////////////////////////////////////
// History cache for BasicInspector
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
		const ScenePlug::ScenePath *path = Context::current()->getIfExists<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
		return path ? SceneAlgo::history( key.plug, *path ) : SceneAlgo::history( key.plug );
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
// BasicInspector
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( BasicInspector )

BasicInspector::~BasicInspector()
{
}

void BasicInspector::init()
{
	if( !m_plug->parent<ScenePlug>() )
	{
		throw IECore::Exception( fmt::format( "Plug \"{}\" is not a child of a ScenePlug", m_plug->fullName() ) );
	}

	m_plug->node()->plugDirtiedSignal().connect(
		boost::bind( &BasicInspector::plugDirtied, this, ::_1 )
	);
}

GafferScene::SceneAlgo::History::ConstPtr BasicInspector::history() const
{
	const auto scenePlug = m_plug->parent<ScenePlug>();
	if( m_plug != scenePlug->globalsPlug() && m_plug != scenePlug->setNamesPlug() && m_plug != scenePlug->setPlug() )
	{
		if( !scenePlug->existsPlug()->getValue() )
		{
			return nullptr;
		}
	}
	return g_historyCache.get( HistoryCacheKey( m_plug.get() ), Context::current()->canceller() );
}

IECore::ConstObjectPtr BasicInspector::value( const GafferScene::SceneAlgo::History *history ) const
{
	/// \todo We want this to be cancellable, but the API currently doesn't allow that.
	/// Perhaps the Inspector base class should always scope `history->context` and an
	/// appropriate canceller for us before calling `value()`?
	Context::Scope scope( history->context.get() );
	return m_valueFunction( history->scene->getChild<ValuePlug>( m_plug->getName() ) );
}

void BasicInspector::plugDirtied( Gaffer::Plug *plug )
{
	if( plug == m_plug )
	{
		dirtiedSignal()( this );
	}
}
