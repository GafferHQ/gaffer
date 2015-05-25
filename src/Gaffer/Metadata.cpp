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

#include "tbb/tbb.h"

#include "boost/lambda/lambda.hpp"
#include "boost/bind.hpp"
#include "boost/multi_index_container.hpp"
#include "boost/multi_index/sequenced_index.hpp"
#include "boost/multi_index/ordered_index.hpp"
#include "boost/multi_index/member.hpp"
#include "boost/optional.hpp"

#include "IECore/CompoundData.h"
#include "IECore/SimpleTypedData.h"

#include "Gaffer/Node.h"
#include "Gaffer/Action.h"
#include "Gaffer/Plug.h"

#include "Gaffer/Metadata.h"

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
	static MetadataMap m;
	return m;
}

struct NodeMetadata
{

	typedef std::pair<InternedString, Metadata::NodeValueFunction> NamedNodeValue;
	typedef std::pair<InternedString, Metadata::PlugValueFunction> NamedPlugValue;

	typedef multi_index::multi_index_container<
		NamedNodeValue,
		multi_index::indexed_by<
			multi_index::ordered_unique<
				multi_index::member<NamedNodeValue, InternedString, &NamedNodeValue::first>
			>,
			multi_index::sequenced<>
		>
	> NodeValues;

	typedef multi_index::multi_index_container<
		NamedPlugValue,
		multi_index::indexed_by<
			multi_index::ordered_unique<
				multi_index::member<NamedPlugValue, InternedString, &NamedPlugValue::first>
			>,
			multi_index::sequenced<>
		>
	> PlugValues;
	
	typedef map<MatchPattern, PlugValues> PlugPathsToValues;

	NodeValues nodeValues;
	PlugPathsToValues plugPathsToValues;

};

typedef std::map<IECore::TypeId, NodeMetadata> NodeMetadataMap;

NodeMetadataMap &nodeMetadataMap()
{
	static NodeMetadataMap m;
	return m;
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

	return NULL;
}

// It's valid to register NULL as an instance value and expect it to override
// any non-NULL registration. We use OptionalData as a way of distinguishing
// between an explicit registration of NULL and no registration at all.
typedef boost::optional<ConstDataPtr> OptionalData;

OptionalData instanceValue( const GraphComponent *instance, InternedString key, bool *persistent = NULL )
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
	InstanceValues *m = instanceMetadata( instance, /* createIfMissing = */ value );
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
		boost::bind( &registerInstanceValueAction, instance, key, currentValue, currentPersistent )
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
	registerValue( target, key, boost::lambda::constant( value ) );
}

void Metadata::registerValue( IECore::InternedString target, IECore::InternedString key, ValueFunction value )
{
	metadataMap()[target].insert( NamedValue( key, value ) );
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
		return NULL;
	}

	Values::const_iterator vIt = it->second.find( key );
	if( vIt != it->second.end() )
	{
		return vIt->second();
	}
	return NULL;
}

void Metadata::registerNodeValue( IECore::TypeId nodeTypeId, IECore::InternedString key, IECore::ConstDataPtr value )
{
	registerNodeValue( nodeTypeId, key, boost::lambda::constant( value ) );
}

void Metadata::registerNodeValue( IECore::TypeId nodeTypeId, IECore::InternedString key, NodeValueFunction value )
{
	NodeMetadata::NodeValues &m = nodeMetadataMap()[nodeTypeId].nodeValues;

	NodeMetadata::NamedNodeValue namedValue( key, value );

	NodeMetadata::NodeValues::const_iterator it = m.find( key );
	if( it == m.end() )
	{
		m.insert( namedValue );
	}
	else
	{
		m.replace( it, namedValue );
	}

	nodeValueChangedSignal()( nodeTypeId, key, NULL );
}

void Metadata::registerNodeValue( Node *node, IECore::InternedString key, IECore::ConstDataPtr value, bool persistent )
{
	registerInstanceValue( node, key, value, persistent );
}

void Metadata::registeredNodeValues( const Node *node, std::vector<IECore::InternedString> &keys, bool inherit, bool instanceOnly, bool persistentOnly )
{
	if( !instanceOnly )
	{
		IECore::TypeId typeId = node->typeId();
		while( typeId != InvalidTypeId )
		{
			NodeMetadataMap::const_iterator nIt = nodeMetadataMap().find( typeId );
			if( nIt != nodeMetadataMap().end() )
			{
				const NodeMetadata::NodeValues::nth_index<1>::type &index = nIt->second.nodeValues.get<1>();
				for( NodeMetadata::NodeValues::nth_index<1>::type::const_reverse_iterator vIt = index.rbegin(), veIt = index.rend(); vIt != veIt; ++vIt )
				{
					keys.push_back( vIt->first );
				}
			}
			typeId = inherit ? RunTimeTyped::baseTypeId( typeId ) : InvalidTypeId;
		}
		std::reverse( keys.begin(), keys.end() );
	}

	registeredInstanceValues( node, keys, persistentOnly );
}

IECore::ConstDataPtr Metadata::nodeValueInternal( const Node *node, IECore::InternedString key, bool inherit, bool instanceOnly )
{
	if( OptionalData iv = instanceValue( node, key ) )
	{
		return *iv;
	}

	if( instanceOnly )
	{
		return NULL;
	}

	IECore::TypeId typeId = node->typeId();
	while( typeId != InvalidTypeId )
	{
		NodeMetadataMap::const_iterator nIt = nodeMetadataMap().find( typeId );
		if( nIt != nodeMetadataMap().end() )
		{
			NodeMetadata::NodeValues::const_iterator vIt = nIt->second.nodeValues.find( key );
			if( vIt != nIt->second.nodeValues.end() )
			{
				return vIt->second( node );
			}
		}
		typeId = inherit ? RunTimeTyped::baseTypeId( typeId ) : InvalidTypeId;
	}
	return NULL;
}

void Metadata::deregisterNodeValue( IECore::TypeId nodeTypeId, IECore::InternedString key )
{
	NodeMetadata::NodeValues &m = nodeMetadataMap()[nodeTypeId].nodeValues;

	NodeMetadata::NodeValues::const_iterator it = m.find( key );
	if( it == m.end() )
	{
		return;
	}

	m.erase( it );
	nodeValueChangedSignal()( nodeTypeId, key, NULL );
}

void Metadata::deregisterNodeValue( Node *node, IECore::InternedString key )
{
	registerInstanceValue( node, key, OptionalData(), /* persistent = */ false );
}

void Metadata::registerNodeDescription( IECore::TypeId nodeTypeId, const std::string &description )
{
	registerNodeValue( nodeTypeId, "description", ConstDataPtr( new StringData( description ) ) );
}

void Metadata::registerNodeDescription( IECore::TypeId nodeTypeId, NodeValueFunction description )
{
	registerNodeValue( nodeTypeId, "description", description );
}

std::string Metadata::nodeDescription( const Node *node, bool inherit )
{
	if( ConstStringDataPtr d = nodeValue<StringData>( node, "description", inherit ) )
	{
		return d->readable();
	}
	return "";
}

std::vector<Node*> Metadata::nodesWithMetadata( GraphComponent *root, IECore::InternedString key, bool inherit, bool instanceOnly )
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
		RecursiveNodeIterator it( root );
		for( ; it != it.end(); ++it )
		{
			if( nodeValueInternal( it->get(), key, inherit, instanceOnly ) )
			{
				nodes.push_back( it->get() );
			}
		}
	}
	return nodes;
}


void Metadata::registerPlugValue( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, IECore::InternedString key, IECore::ConstDataPtr value )
{
	registerPlugValue( nodeTypeId, plugPath, key, boost::lambda::constant( value ) );
}

void Metadata::registerPlugValue( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, IECore::InternedString key, PlugValueFunction value )
{
	NodeMetadata &nodeMetadata = nodeMetadataMap()[nodeTypeId];
	NodeMetadata::PlugValues &plugValues = nodeMetadata.plugPathsToValues[plugPath];
	
	NodeMetadata::NamedPlugValue namedValue( key, value );

	NodeMetadata::PlugValues::const_iterator it = plugValues.find( key );
	if( it == plugValues.end() )
	{
		plugValues.insert( namedValue );
	}
	else
	{
		plugValues.replace( it, namedValue );
	}
	
	plugValueChangedSignal()( nodeTypeId, plugPath, key, NULL );
}

void Metadata::registerPlugValue( Plug *plug, IECore::InternedString key, IECore::ConstDataPtr value, bool persistent )
{
	registerInstanceValue( plug, key, value, persistent );
}

void Metadata::registeredPlugValues( const Plug *plug, std::vector<IECore::InternedString> &keys, bool inherit, bool instanceOnly, bool persistentOnly )
{
	const Node *node = plug->node();
	if( node && !instanceOnly )
	{
		const string plugPath = plug->relativeName( node );

		IECore::TypeId typeId = node->typeId();
		while( typeId != InvalidTypeId )
		{
			NodeMetadataMap::const_iterator nIt = nodeMetadataMap().find( typeId );
			if( nIt != nodeMetadataMap().end() )
			{
				NodeMetadata::PlugPathsToValues::const_iterator it, eIt;
				for( it = nIt->second.plugPathsToValues.begin(), eIt = nIt->second.plugPathsToValues.end(); it != eIt; ++it )
				{
					if( match( plugPath, it->first ) )
					{
						const NodeMetadata::PlugValues::nth_index<1>::type &index = it->second.get<1>();
						for( NodeMetadata::PlugValues::nth_index<1>::type::const_reverse_iterator vIt = index.rbegin(), veIt = index.rend(); vIt != veIt; ++vIt )
						{
							keys.push_back( vIt->first );
						}
					}
				}
			}
			typeId = inherit ? RunTimeTyped::baseTypeId( typeId ) : InvalidTypeId;
		}
		std::reverse( keys.begin(), keys.end() );
	}

	registeredInstanceValues( plug, keys, persistentOnly );
}

IECore::ConstDataPtr Metadata::plugValueInternal( const Plug *plug, IECore::InternedString key, bool inherit, bool instanceOnly )
{
	if( OptionalData iv = instanceValue( plug, key ) )
	{
		return *iv;
	}

	if( instanceOnly )
	{
		return NULL;
	}

	const Node *node = plug->node();
	if( !node )
	{
		return NULL;
	}

	const string plugPath = plug->relativeName( node );

	IECore::TypeId typeId = node->typeId();
	while( typeId != InvalidTypeId )
	{
		NodeMetadataMap::const_iterator nIt = nodeMetadataMap().find( typeId );
		if( nIt != nodeMetadataMap().end() )
		{
			// First do a direct lookup using the plug path.
			NodeMetadata::PlugPathsToValues::const_iterator it = nIt->second.plugPathsToValues.find( plugPath );
			const NodeMetadata::PlugPathsToValues::const_iterator eIt = nIt->second.plugPathsToValues.end();
			if( it != eIt )
			{
				NodeMetadata::PlugValues::const_iterator vIt = it->second.find( key );
				if( vIt != it->second.end() )
				{
					return vIt->second( plug );
				}
			}
			// And only if the direct lookups fails, do a full search using
			// wildcard matches.
			for( it = nIt->second.plugPathsToValues.begin(); it != eIt; ++it )
			{
				if( match( plugPath, it->first ) )
				{
					NodeMetadata::PlugValues::const_iterator vIt = it->second.find( key );
					if( vIt != it->second.end() )
					{
						return vIt->second( plug );
					}
				}
			}
		}
		typeId = inherit ? RunTimeTyped::baseTypeId( typeId ) : InvalidTypeId;
	}
	return NULL;
}

void Metadata::deregisterPlugValue( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, IECore::InternedString key )
{
	NodeMetadata &nodeMetadata = nodeMetadataMap()[nodeTypeId];
	NodeMetadata::PlugValues &plugValues = nodeMetadata.plugPathsToValues[plugPath];

	NodeMetadata::PlugValues::const_iterator it = plugValues.find( key );
	if( it == plugValues.end() )
	{
		return;
	}

	plugValues.erase( it );
	plugValueChangedSignal()( nodeTypeId, plugPath, key, NULL );
}

void Metadata::deregisterPlugValue( Plug *plug, IECore::InternedString key )
{
	registerInstanceValue( plug, key, OptionalData(), /* persistent = */ false );
}

void Metadata::registerPlugDescription( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, const std::string &description )
{
	registerPlugValue( nodeTypeId, plugPath, "description", ConstDataPtr( new StringData( description ) ) );
}

void Metadata::registerPlugDescription( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, PlugValueFunction description )
{
	registerPlugValue( nodeTypeId, plugPath, "description", description );
}

std::string Metadata::plugDescription( const Plug *plug, bool inherit )
{
	if( ConstStringDataPtr d = plugValue<StringData>( plug, "description", inherit ) )
	{
		return d->readable();
	}
	return "";
}

std::vector<Plug*> Metadata::plugsWithMetadata( GraphComponent *root, IECore::InternedString key, bool inherit, bool instanceOnly )
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
		FilteredRecursiveChildIterator<TypePredicate<Plug> > it( root );
		for( ; it != it.end(); ++it )
		{
			if( plugValueInternal( it->get(), key, inherit, false ) )
			{
				plugs.push_back( it->get() );
			}
		}
	}
	return plugs;
}

Metadata::ValueChangedSignal &Metadata::valueChangedSignal()
{
	static ValueChangedSignal s;
	return s;
}

Metadata::NodeValueChangedSignal &Metadata::nodeValueChangedSignal()
{
	static NodeValueChangedSignal s;
	return s;
}

Metadata::PlugValueChangedSignal &Metadata::plugValueChangedSignal()
{
	static PlugValueChangedSignal s;
	return s;
}

void Metadata::clearInstanceMetadata( const GraphComponent *graphComponent )
{
	instanceMetadataMap().erase( graphComponent );
}
