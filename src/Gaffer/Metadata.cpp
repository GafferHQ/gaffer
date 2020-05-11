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

#include "boost/bind.hpp"
#include "boost/multi_index/member.hpp"
#include "boost/multi_index/ordered_index.hpp"
#include "boost/multi_index/sequenced_index.hpp"
#include "boost/multi_index_container.hpp"
#include "boost/optional.hpp"

#include "tbb/tbb.h"

using namespace std;
using namespace boost;
using namespace tbb;
using namespace IECore;
using namespace Gaffer;

namespace
{

typedef std::pair<InternedString, Metadata::ValueFunction> NamedValue;

typedef multi_index::multi_index_container<
	NamedValue,
	multi_index::indexed_by<
		multi_index::ordered_unique<
			multi_index::member<NamedValue, InternedString, &NamedValue::first>
		>,
		multi_index::sequenced<>
	>
> Values;

typedef std::map<IECore::InternedString, Values> MetadataMap;

MetadataMap &metadataMap()
{
	static auto g_m = new MetadataMap;
	return *g_m;
}

struct GraphComponentMetadata
{

	typedef std::pair<InternedString, Metadata::GraphComponentValueFunction> NamedValue;
	typedef std::pair<InternedString, Metadata::PlugValueFunction> NamedPlugValue;

	typedef multi_index::multi_index_container<
		NamedValue,
		multi_index::indexed_by<
			multi_index::ordered_unique<
				multi_index::member<NamedValue, InternedString, &NamedValue::first>
			>,
			multi_index::sequenced<>
		>
	> Values;

	typedef multi_index::multi_index_container<
		NamedPlugValue,
		multi_index::indexed_by<
			multi_index::ordered_unique<
				multi_index::member<NamedPlugValue, InternedString, &NamedPlugValue::first>
			>,
			multi_index::sequenced<>
		>
	> PlugValues;

	typedef map<StringAlgo::MatchPatternPath, PlugValues> PlugPathsToValues;

	Values values;
	PlugPathsToValues plugPathsToValues;

};

typedef std::map<IECore::TypeId, GraphComponentMetadata> GraphComponentMetadataMap;

GraphComponentMetadataMap &graphComponentMetadataMap()
{
	static auto g_m = new GraphComponentMetadataMap;
	return *g_m;
}

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

typedef multi_index::multi_index_container<
	NamedInstanceValue,
	multi_index::indexed_by<
		multi_index::ordered_unique<
			multi_index::member<NamedInstanceValue, InternedString, &NamedInstanceValue::name>
		>,
		multi_index::sequenced<>
	>
> InstanceValues;

typedef concurrent_hash_map<const GraphComponent *, InstanceValues *> InstanceMetadataMap;

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
		return accessor->second;
	}
	else
	{
		if( createIfMissing )
		{
			m.insert( accessor, instance );
			accessor->second = new InstanceValues();
			return accessor->second;
		}
	}

	return nullptr;
}

// It's valid to register null as an instance value and expect it to override
// any non-null registration. We use OptionalData as a way of distinguishing
// between an explicit registration of null and no registration at all.
typedef boost::optional<ConstDataPtr> OptionalData;

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

	if( Node *node = runTimeCast<Node>( instance ) )
	{
		Metadata::nodeValueChangedSignal()( node->typeId(), key, node );
	}
	else if( Plug *plug = runTimeCast<Plug>( instance ) )
	{
		if( const Node *node = plug->node() )
		{
			Metadata::plugValueChangedSignal()( node->typeId(), plug->relativeName( node ), key, plug );
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

	if( typeId == Node::staticTypeId() || RunTimeTyped::inheritsFrom( typeId, Node::staticTypeId() ) )
	{
		nodeValueChangedSignal()( typeId, key, nullptr );
	}
	else if( typeId == Plug::staticTypeId() || RunTimeTyped::inheritsFrom( typeId, Plug::staticTypeId() ) )
	{
		plugValueChangedSignal()( typeId, "", key, nullptr );
	}
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

	if( typeId == Node::staticTypeId() || RunTimeTyped::inheritsFrom( typeId, Node::staticTypeId() ) )
	{
		nodeValueChangedSignal()( typeId, key, nullptr );
	}
	else if( typeId == Plug::staticTypeId() || RunTimeTyped::inheritsFrom( typeId, Plug::staticTypeId() ) )
	{
		plugValueChangedSignal()( typeId, "", key, nullptr );
	}
}

void Metadata::deregisterValue( IECore::TypeId ancestorTypeId, const StringAlgo::MatchPattern &plugPath, IECore::InternedString key )
{
	auto &m = graphComponentMetadataMap()[ancestorTypeId];
	auto &plugValues = m.plugPathsToValues[StringAlgo::matchPatternPath( plugPath, '.' )];

	auto it = plugValues.find( key );
	if( it == plugValues.end() )
	{
		return;
	}

	plugValues.erase( it );
	plugValueChangedSignal()( ancestorTypeId, plugPath, key, nullptr );
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
		for( RecursiveNodeIterator it( root ); !it.done(); ++it )
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
	auto &graphComponentMetadata = graphComponentMetadataMap()[ancestorTypeId];
	auto &plugValues = graphComponentMetadata.plugPathsToValues[StringAlgo::matchPatternPath( plugPath, '.' )];

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

	plugValueChangedSignal()( ancestorTypeId, plugPath, key, nullptr );
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

Metadata::NodeValueChangedSignal &Metadata::nodeValueChangedSignal()
{
	static NodeValueChangedSignal *s = new NodeValueChangedSignal;
	return *s;
}

Metadata::PlugValueChangedSignal &Metadata::plugValueChangedSignal()
{
	static PlugValueChangedSignal *s = new PlugValueChangedSignal;
	return *s;
}

void Metadata::clearInstanceMetadata( const GraphComponent *graphComponent )
{
	instanceMetadataMap().erase( graphComponent );
}
