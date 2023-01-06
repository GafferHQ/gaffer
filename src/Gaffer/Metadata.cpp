//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Metadata.h"

#include "Gaffer/Action.h"
#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"

#include "IECore/CompoundData.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"

#include "boost/bind/bind.hpp"
#include "boost/multi_index/member.hpp"
#include "boost/multi_index/ordered_index.hpp"
#include "boost/multi_index/sequenced_index.hpp"
#include "boost/multi_index_container.hpp"

#include "tbb/concurrent_hash_map.h"
#include "tbb/recursive_mutex.h"

#include <unordered_map>

using namespace std;
using namespace boost;
using namespace tbb;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal implementation details
//////////////////////////////////////////////////////////////////////////

namespace
{

// Signals
// =======
//
// We store all our signals in a map indexed by `Node *`. Although we do not
// allow concurrent edits to a node graph, we do allow different node graphs to
// be edited concurrently from different threads. This means that we require
// thread-safety for the operations on the map, but _not_ for the signals
// themselves. `tbb::concurrent_unordered_map` would be ideal for this if it
// provided concurrent erasure, but it doesn't. And in practice we expect
// very little contention anyway, so just use a simple `std::unordered_map`
// protected by a mutex.

struct NodeSignals
{
	Metadata::NodeValueChangedSignal nodeSignal;
	Metadata::PlugValueChangedSignal plugSignal;
};

using SignalsMap = std::unordered_map<Node *, unique_ptr<NodeSignals>>;
using SignalsMapLock = tbb::recursive_mutex::scoped_lock;

// Access to the signals requires the passing of a scoped_lock that
// will be locked for you automatically, and must remain locked while
// the result is used.
SignalsMap &signalsMap( SignalsMapLock &lock )
{
	static SignalsMap *g_signalsMap = new SignalsMap;
	static tbb::recursive_mutex g_signalsMapMutex;
	lock.acquire( g_signalsMapMutex );
	return *g_signalsMap;
}

NodeSignals *nodeSignals( Node *node, bool createIfMissing )
{
	SignalsMapLock lock;
	auto &m = signalsMap( lock );

	auto it = m.find( node );
	if( it == m.end() )
	{
		if( !createIfMissing )
		{
			return nullptr;
		}
		it = m.emplace( node, std::make_unique<NodeSignals>() ).first;
	}
	return it->second.get();
}

void emitValueChangedSignals( IECore::TypeId typeId, IECore::InternedString key, Metadata::ValueChangedReason reason )
{
	if( typeId == Node::staticTypeId() || RunTimeTyped::inheritsFrom( typeId, Node::staticTypeId() ) )
	{
		Metadata::nodeValueChangedSignal()( typeId, key, nullptr );

		SignalsMapLock lock;
		for( const auto &s : signalsMap( lock ) )
		{
			if( s.first->isInstanceOf( typeId ) )
			{
				s.second->nodeSignal( s.first, key, reason );
			}
		}
	}
	else if( typeId == Plug::staticTypeId() || RunTimeTyped::inheritsFrom( typeId, Plug::staticTypeId() ) )
	{
		Metadata::plugValueChangedSignal()( typeId, "", key, nullptr );

		SignalsMapLock lock;
		for( const auto &s : signalsMap( lock ) )
		{
			for( auto &plug : Plug::RecursiveRange( *s.first ) )
			{
				if( plug->isInstanceOf( typeId ) )
				{
					s.second->plugSignal( plug.get(), key, reason );
				}
			}
		}
	}
}

void emitMatchingPlugValueChangedSignals( Metadata::PlugValueChangedSignal &signal, Plug *plug, const vector<InternedString> &path, const StringAlgo::MatchPatternPath &matchPath, IECore::InternedString key, Metadata::ValueChangedReason reason )
{
	/// \todo There is scope for pruning the recursion here early if we
	/// reproduce the logic of StringAlgo::match ourselves. We don't
	/// really expect this code path to be exercised while there are active
	/// signals though, as type-based (rather than instance-based) registrations
	/// are typically only made during startup.
	if( StringAlgo::match( path, matchPath ) )
	{
		signal( plug, key, reason );
	}

	vector<InternedString> childPath = path;
	childPath.push_back( InternedString() ); // Room for child name
	for( const auto &child : Plug::Range( *plug ) )
	{
		childPath.back() = child->getName();
		emitMatchingPlugValueChangedSignals( signal, child.get(), childPath, matchPath, key, reason );
	}
}

// The `matchPatternPath` is passed redundantly rather than derived from `plugPath`
// because in all cases we have already done the work of tokenizing it outside this function.
void emitPlugValueChangedSignals( IECore::TypeId ancestorTypeId, const StringAlgo::MatchPattern &plugPath, const StringAlgo::MatchPatternPath &matchPatternPath, IECore::InternedString key, Metadata::ValueChangedReason reason )
{
	assert( reason == Metadata::ValueChangedReason::StaticRegistration || reason == Metadata::ValueChangedReason::StaticDeregistration );

	Metadata::plugValueChangedSignal()( ancestorTypeId, plugPath, key, nullptr );

	SignalsMapLock lock;
	for( const auto &s : signalsMap( lock ) )
	{
		if( s.first->isInstanceOf( ancestorTypeId ) )
		{
			for( const auto &plug : Plug::Range( *s.first ) )
			{
				emitMatchingPlugValueChangedSignals( s.second->plugSignal, plug.get(), { plug->getName() }, matchPatternPath, key, reason );
			}
		}
		else if( ancestorTypeId == Plug::staticTypeId() || RunTimeTyped::inheritsFrom( ancestorTypeId, Plug::staticTypeId() ) )
		{
			for( const auto &plug : Plug::RecursiveRange( *s.first ) )
			{
				if( plug->isInstanceOf( ancestorTypeId ) )
				{
					emitMatchingPlugValueChangedSignals( s.second->plugSignal, plug.get(), {}, matchPatternPath, key, reason );
				}
			}
		}
	}
}

// Value storage for string targets
// ================================

using NamedValue = std::pair<InternedString, Metadata::ValueFunction>;

using Values = multi_index::multi_index_container<
	NamedValue,
	multi_index::indexed_by<
		multi_index::ordered_unique<
			multi_index::member<NamedValue, InternedString, &NamedValue::first>
		>,
		multi_index::sequenced<>
	>
>;

using MetadataMap = std::map<IECore::InternedString, Values>;

MetadataMap &metadataMap()
{
	static auto g_m = new MetadataMap;
	return *g_m;
}

// Value storage for type-based targets
// ====================================

struct GraphComponentMetadata
{

	using NamedValue = std::pair<InternedString, Metadata::GraphComponentValueFunction>;
	using NamedPlugValue = std::pair<InternedString, Metadata::PlugValueFunction>;

	using Values = multi_index::multi_index_container<
		NamedValue,
		multi_index::indexed_by<
			multi_index::ordered_unique<
				multi_index::member<NamedValue, InternedString, &NamedValue::first>
			>,
			multi_index::sequenced<>
		>
	>;

	using PlugValues = multi_index::multi_index_container<
		NamedPlugValue,
		multi_index::indexed_by<
			multi_index::ordered_unique<
				multi_index::member<NamedPlugValue, InternedString, &NamedPlugValue::first>
			>,
			multi_index::sequenced<>
		>
	>;

	using PlugPathsToValues = map<StringAlgo::MatchPatternPath, PlugValues>;

	Values values;
	PlugPathsToValues plugPathsToValues;

};

using GraphComponentMetadataMap = std::map<IECore::TypeId, GraphComponentMetadata>;

GraphComponentMetadataMap &graphComponentMetadataMap()
{
	static auto g_m = new GraphComponentMetadataMap;
	return *g_m;
}

// Value storage for instance targets
// ==================================

struct NamedInstanceValue
{
	NamedInstanceValue( InternedString n, ConstDataPtr v, bool p )
		:	name( n ), value( v ), persistent( p )
	{
	}

	InternedString name;
	ConstDataPtr value;
	bool persistent;
};

using InstanceValues = multi_index::multi_index_container<
	NamedInstanceValue,
	multi_index::indexed_by<
		multi_index::ordered_unique<
			multi_index::member<NamedInstanceValue, InternedString, &NamedInstanceValue::name>
		>,
		multi_index::sequenced<>
	>
>;

using InstanceMetadataMap = concurrent_hash_map<const GraphComponent *, std::unique_ptr<InstanceValues>>;

InstanceMetadataMap &instanceMetadataMap()
{
	static InstanceMetadataMap m;
	return m;
}

InstanceValues *instanceMetadata( const GraphComponent *instance, bool createIfMissing )
{
	InstanceMetadataMap &m = instanceMetadataMap();

	InstanceMetadataMap::accessor accessor;
	if( m.find( accessor, instance ) )
	{
		return accessor->second.get();
	}
	else
	{
		if( createIfMissing )
		{
			m.insert( accessor, instance );
			accessor->second = std::make_unique<InstanceValues>();
			return accessor->second.get();
		}
	}

	return nullptr;
}

// It's valid to register null as an instance value and expect it to override
// any non-null registration. We use OptionalData as a way of distinguishing
// between an explicit registration of null and no registration at all.
using OptionalData = std::optional<ConstDataPtr>;

OptionalData instanceValue( const GraphComponent *instance, InternedString key, bool *persistent = nullptr )
{
	const InstanceValues *m = instanceMetadata( instance, /* createIfMissing = */ false );
	if( !m )
	{
		return OptionalData();
	}

	InstanceValues::const_iterator vIt = m->find( key );
	if( vIt != m->end() )
	{
		if( persistent )
		{
			*persistent = vIt->persistent;
		}
		return vIt->value;
	}

	return OptionalData();
}

void registerInstanceValueAction( GraphComponent *instance, InternedString key, OptionalData value, bool persistent )
{
	InstanceValues *m = instanceMetadata( instance, /* createIfMissing = */ static_cast<bool>( value ) );
	if( !m )
	{
		return;
	}

	InstanceValues::const_iterator it = m->find( key );
	if( value )
	{
		NamedInstanceValue namedValue( key, *value, persistent );
		if( it == m->end() )
		{
			m->insert( namedValue );
		}
		else
		{
			m->replace( it, namedValue );
		}
	}
	else
	{
		if( it != m->end() )
		{
			m->erase( it );
		}
	}

	const Metadata::ValueChangedReason reason = value ? Metadata::ValueChangedReason::InstanceRegistration : Metadata::ValueChangedReason::InstanceDeregistration;

	if( Node *node = runTimeCast<Node>( instance ) )
	{
		Metadata::nodeValueChangedSignal()( node->typeId(), key, node );
		if( NodeSignals *s = nodeSignals( node, /* createIfMissing = */ false ) )
		{
			s->nodeSignal( node, key, reason );
		}
	}
	else if( Plug *plug = runTimeCast<Plug>( instance ) )
	{
		if( Node *node = plug->node() )
		{
			Metadata::plugValueChangedSignal()( node->typeId(), plug->relativeName( node ), key, plug );
			if( NodeSignals *s = nodeSignals( node, /* createIfMissing = */ false ) )
			{
				s->plugSignal( plug, key, reason );
			}
		}
	}
}

void registerInstanceValue( GraphComponent *instance, IECore::InternedString key, OptionalData value, bool persistent )
{
	bool currentPersistent = true;
	OptionalData currentValue = instanceValue( instance, key, &currentPersistent );
	if( !value && !currentValue )
	{
		// we can early out if we didn't have a value before and we don't
		// want one now.
		return;
	}
	else if( value && currentValue && persistent == currentPersistent )
	{
		// if we already had a value, we can early out if it's the same as
		// the new one.
		if(
			( *currentValue == *value ) ||
			( *currentValue && *value && (*currentValue)->isEqualTo( value->get() ) )
		)
		{
			return;
		}
	}

	Action::enact(
		instance,
		// ok to bind raw pointers to instance, because enact() guarantees
		// the lifetime of the subject.
		boost::bind( &registerInstanceValueAction, instance, key, value, persistent ),
		boost::bind( &registerInstanceValueAction, instance, key, currentValue, currentPersistent ),
		// Metadata may not be used in computation, so cancellation of
		// background tasks isn't necessary.
		false
	);
}

void registeredInstanceValues( const GraphComponent *graphComponent, std::vector<IECore::InternedString> &keys, bool persistentOnly )
{
	if( const InstanceValues *im = instanceMetadata( graphComponent, /* createIfMissing = */ false ) )
	{
		const InstanceValues::nth_index<1>::type &index = im->get<1>();
		for( InstanceValues::nth_index<1>::type::const_iterator vIt = index.begin(), veIt = index.end(); vIt != veIt; ++vIt )
		{
			if( !persistentOnly || vIt->persistent )
			{
				keys.push_back( vIt->name );
			}
		}
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Public implementation
//////////////////////////////////////////////////////////////////////////

void Metadata::registerValue( IECore::InternedString target, IECore::InternedString key, IECore::ConstDataPtr value )
{
	registerValue( target, key, [value]{ return value; } );
}

void Metadata::registerValue( IECore::InternedString target, IECore::InternedString key, ValueFunction value )
{
	NamedValue namedValue( key, value );
	auto &m = metadataMap()[target];
	auto i = m.insert( namedValue );
	if( !i.second )
	{
		m.replace( i.first, namedValue );
	}

	valueChangedSignal()( target, key );
}

void Metadata::deregisterValue( IECore::InternedString target, IECore::InternedString key )
{
	auto &m = metadataMap();
	auto mIt = m.find( target );
	if( mIt == m.end() )
	{
		return;
	}

	auto vIt = mIt->second.find( key );
	if( vIt == mIt->second.end() )
	{
		return;
	}

	mIt->second.erase( vIt );
	valueChangedSignal()( target, key );
}

void Metadata::registeredValues( IECore::InternedString target, std::vector<IECore::InternedString> &keys )
{
	const MetadataMap &m = metadataMap();
	MetadataMap::const_iterator it = m.find( target );
	if( it == m.end() )
	{
		return;
	}

	const Values::nth_index<1>::type &index = it->second.get<1>();
	for( Values::nth_index<1>::type::const_iterator it = index.begin(), eIt = index.end(); it != eIt; ++it )
	{
		keys.push_back( it->first );
	}
}

IECore::ConstDataPtr Metadata::valueInternal( IECore::InternedString target, IECore::InternedString key )
{
	const MetadataMap &m = metadataMap();
	MetadataMap::const_iterator it = m.find( target );
	if( it == m.end() )
	{
		return nullptr;
	}

	Values::const_iterator vIt = it->second.find( key );
	if( vIt != it->second.end() )
	{
		return vIt->second();
	}
	return nullptr;
}

void Metadata::registerValue( IECore::TypeId typeId, IECore::InternedString key, IECore::ConstDataPtr value )
{
	registerValue( typeId, key, [value]( const GraphComponent * ){ return value; } );
}

void Metadata::registerValue( IECore::TypeId typeId, IECore::InternedString key, GraphComponentValueFunction value )
{
	auto &m = graphComponentMetadataMap()[typeId].values;

	GraphComponentMetadata::NamedValue namedValue( key, value );

	auto it = m.find( key );
	if( it == m.end() )
	{
		m.insert( namedValue );
	}
	else
	{
		m.replace( it, namedValue );
	}

	emitValueChangedSignals( typeId, key, Metadata::ValueChangedReason::StaticRegistration );
}

void Metadata::deregisterValue( IECore::TypeId typeId, IECore::InternedString key )
{
	auto &m = graphComponentMetadataMap()[typeId].values;
	auto it = m.find( key );
	if( it == m.end() )
	{
		return;
	}

	m.erase( it );
	emitValueChangedSignals( typeId, key, Metadata::ValueChangedReason::StaticDeregistration );
}

void Metadata::deregisterValue( IECore::TypeId ancestorTypeId, const StringAlgo::MatchPattern &plugPath, IECore::InternedString key )
{
	auto &m = graphComponentMetadataMap()[ancestorTypeId];
	const StringAlgo::MatchPatternPath matchPatternPath = StringAlgo::matchPatternPath( plugPath, '.' );
	auto &plugValues = m.plugPathsToValues[matchPatternPath];

	auto it = plugValues.find( key );
	if( it == plugValues.end() )
	{
		return;
	}

	plugValues.erase( it );

	emitPlugValueChangedSignals( ancestorTypeId, plugPath, matchPatternPath, key, Metadata::ValueChangedReason::StaticDeregistration );
}

void Metadata::deregisterValue( GraphComponent *target, IECore::InternedString key )
{
	registerInstanceValue( target, key, OptionalData(), /* persistent = */ false );
}

std::vector<Node*> Metadata::nodesWithMetadata( GraphComponent *root, IECore::InternedString key, bool instanceOnly )
{
	std::vector<Node*> nodes;
	if( instanceOnly )
	{
		// if we're only looking for instance data, we can improve the performance
		// for large graphs by explicitly iterating through the instanceMetaDataMap:
		InstanceMetadataMap::const_iterator it = instanceMetadataMap().begin();
		InstanceMetadataMap::const_iterator end = instanceMetadataMap().end();
		for( ; it != end; ++it )
		{
			const Node* node = runTimeCast<const Node>( it->first );
			if( !node || !root->isAncestorOf( node ) )
			{
				continue;
			}

			if( it->second->find( key ) != it->second->end() )
			{
				nodes.push_back( const_cast<Node*>( node ) );
			}
		}
	}
	else
	{
		for( Node::RecursiveIterator it( root ); !it.done(); ++it )
		{
			if( valueInternal( it->get(), key, instanceOnly ) )
			{
				nodes.push_back( it->get() );
			}
		}
	}
	return nodes;
}

void Metadata::registerValue( IECore::TypeId ancestorTypeId, const StringAlgo::MatchPattern &plugPath, IECore::InternedString key, IECore::ConstDataPtr value )
{
	registerValue( ancestorTypeId, plugPath, key, [value](const Plug *){ return value; } );
}

void Metadata::registerValue( IECore::TypeId ancestorTypeId, const StringAlgo::MatchPattern &plugPath, IECore::InternedString key, PlugValueFunction value )
{
	auto &m = graphComponentMetadataMap()[ancestorTypeId];
	const StringAlgo::MatchPatternPath matchPatternPath = StringAlgo::matchPatternPath( plugPath, '.' );
	auto &plugValues = m.plugPathsToValues[matchPatternPath];

	GraphComponentMetadata::NamedPlugValue namedValue( key, value );

	auto it = plugValues.find( key );
	if( it == plugValues.end() )
	{
		plugValues.insert( namedValue );
	}
	else
	{
		plugValues.replace( it, namedValue );
	}

	emitPlugValueChangedSignals( ancestorTypeId, plugPath, matchPatternPath, key, Metadata::ValueChangedReason::StaticRegistration );
}

std::vector<Plug*> Metadata::plugsWithMetadata( GraphComponent *root, IECore::InternedString key, bool instanceOnly )
{
	std::vector<Plug*> plugs;
	if( instanceOnly )
	{
		// If we're only looking for instance data, we can improve the performance
		// for large graphs by explicitly iterating through the instanceMetaDataMap.
		// This reduced the time to call this function from 0.1 sec to 1.e-5 sec
		// in my reasonably sized test scene.

		InstanceMetadataMap::const_iterator it = instanceMetadataMap().begin();
		InstanceMetadataMap::const_iterator end = instanceMetadataMap().end();
		for( ; it != end; ++it )
		{
			const Plug* plug = runTimeCast<const Plug>( it->first );
			if( !plug || !root->isAncestorOf( plug ) )
			{
				continue;
			}

			if( it->second->find( key ) != it->second->end() )
			{
				plugs.push_back( const_cast<Plug*>( plug ) );
			}
		}
	}
	else
	{
		for( FilteredRecursiveChildIterator<TypePredicate<Plug> > it( root ); !it.done(); ++it )
		{
			if( valueInternal( it->get(), key, false ) )
			{
				plugs.push_back( it->get() );
			}
		}
	}
	return plugs;
}

void Metadata::registerValue( GraphComponent *target, IECore::InternedString key, IECore::ConstDataPtr value, bool persistent )
{
	registerInstanceValue( target, key, value, persistent );
}

void Metadata::registeredValues( const GraphComponent *target, std::vector<IECore::InternedString> &keys, bool instanceOnly, bool persistentOnly )
{
	if( !instanceOnly )
	{
		IECore::TypeId typeId = target->typeId();
		while( typeId != InvalidTypeId )
		{
			auto nIt = graphComponentMetadataMap().find( typeId );
			if( nIt != graphComponentMetadataMap().end() )
			{
				const auto &index = nIt->second.values.get<1>();
				for( auto vIt = index.rbegin(), veIt = index.rend(); vIt != veIt; ++vIt )
				{
					keys.push_back( vIt->first );
				}
			}
			typeId = RunTimeTyped::baseTypeId( typeId );
		}
		std::reverse( keys.begin(), keys.end() );

		if( const Plug *plug = runTimeCast<const Plug>( target ) )
		{
			vector<InternedString> plugPathKeys;

			const GraphComponent *ancestor = plug->parent();
			vector<InternedString> plugPath( { plug->getName() } );
			while( ancestor )
			{
				IECore::TypeId typeId = ancestor->typeId();
				while( typeId != InvalidTypeId )
				{
					auto nIt = graphComponentMetadataMap().find( typeId );
					if( nIt != graphComponentMetadataMap().end() )
					{
						for( auto it = nIt->second.plugPathsToValues.begin(), eIt = nIt->second.plugPathsToValues.end(); it != eIt; ++it )
						{
							if( StringAlgo::match( plugPath, it->first ) )
							{
								const auto &index = it->second.get<1>();
								for( auto vIt = index.rbegin(), veIt = index.rend(); vIt != veIt; ++vIt )
								{
									plugPathKeys.push_back( vIt->first );
								}
							}
						}
					}
					typeId = RunTimeTyped::baseTypeId( typeId );
				}

				plugPath.insert( plugPath.begin(), ancestor->getName() );
				ancestor = ancestor->parent();
			}
			keys.insert( keys.end(), plugPathKeys.rbegin(), plugPathKeys.rend() );
		}
	}
	registeredInstanceValues( target, keys, persistentOnly );
}

IECore::ConstDataPtr Metadata::valueInternal( const GraphComponent *target, IECore::InternedString key, bool instanceOnly )
{
	// Look for instance values first. These override
	// everything else.

	if( OptionalData iv = instanceValue( target, key ) )
	{
		return *iv;
	}

	if( instanceOnly )
	{
		return nullptr;
	}

	// If the target is a plug, then look for a path-based
	// value. These are more specific than type-based values.

	if( const Plug *plug = runTimeCast<const Plug>( target ) )
	{
		const GraphComponent *ancestor = plug->parent();
		vector<InternedString> plugPath( { plug->getName() } );
		while( ancestor )
		{
			IECore::TypeId typeId = ancestor->typeId();
			while( typeId != InvalidTypeId )
			{
				auto nIt = graphComponentMetadataMap().find( typeId );
				if( nIt != graphComponentMetadataMap().end() )
				{
					// First do a direct lookup using the plug path.
					auto it = nIt->second.plugPathsToValues.find( plugPath );
					const auto eIt = nIt->second.plugPathsToValues.end();
					if( it != eIt )
					{
						auto vIt = it->second.find( key );
						if( vIt != it->second.end() )
						{
							return vIt->second( plug );
						}
					}
					// And only if the direct lookup fails, do a full search using
					// wildcard matches.
					for( it = nIt->second.plugPathsToValues.begin(); it != eIt; ++it )
					{
						if( StringAlgo::match( plugPath, it->first ) )
						{
							auto vIt = it->second.find( key );
							if( vIt != it->second.end() )
							{
								return vIt->second( plug );
							}
						}
					}
				}
				typeId = RunTimeTyped::baseTypeId( typeId );
			}

			plugPath.insert( plugPath.begin(), ancestor->getName() );
			ancestor = ancestor->parent();
		}
	}

	// Finally look for values registered to the type

	IECore::TypeId typeId = target->typeId();
	while( typeId != InvalidTypeId )
	{
		auto nIt = graphComponentMetadataMap().find( typeId );
		if( nIt != graphComponentMetadataMap().end() )
		{
			auto vIt = nIt->second.values.find( key );
			if( vIt != nIt->second.values.end() )
			{
				return vIt->second( target );
			}
		}
		typeId = RunTimeTyped::baseTypeId( typeId );
	}

	return nullptr;
}

Metadata::ValueChangedSignal &Metadata::valueChangedSignal()
{
	static ValueChangedSignal *s = new ValueChangedSignal;
	return *s;
}

Metadata::NodeValueChangedSignal &Metadata::nodeValueChangedSignal( Node *node )
{
	return nodeSignals( node, /* createIfMissing = */ true )->nodeSignal;
}

Metadata::PlugValueChangedSignal &Metadata::plugValueChangedSignal( Node *node )
{
	return nodeSignals( node, /* createIfMissing = */ true )->plugSignal;
}

Metadata::LegacyNodeValueChangedSignal &Metadata::nodeValueChangedSignal()
{
	static LegacyNodeValueChangedSignal *s = new LegacyNodeValueChangedSignal;
	return *s;
}

Metadata::LegacyPlugValueChangedSignal &Metadata::plugValueChangedSignal()
{
	static LegacyPlugValueChangedSignal *s = new LegacyPlugValueChangedSignal;
	return *s;
}

void Metadata::instanceDestroyed( GraphComponent *graphComponent )
{
	instanceMetadataMap().erase( graphComponent );
	if( auto node = runTimeCast<Node>( graphComponent ) )
	{
		SignalsMapLock lock;
		signalsMap( lock ).erase( node );
	}
}
