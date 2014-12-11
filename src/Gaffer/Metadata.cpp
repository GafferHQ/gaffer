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

#include "IECore/CompoundData.h"

#include "Gaffer/Node.h"
#include "Gaffer/Action.h"

#include "Gaffer/Metadata.h"

using namespace std;
using namespace boost;
using namespace tbb;
using namespace IECore;
using namespace Gaffer;

namespace
{

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

typedef std::pair<InternedString, ConstDataPtr> NamedInstanceValue;

typedef multi_index::multi_index_container<
	NamedInstanceValue,
	multi_index::indexed_by<
		multi_index::ordered_unique<
			multi_index::member<NamedInstanceValue, InternedString, &NamedInstanceValue::first>
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

const Data *instanceValue( const GraphComponent *instance, InternedString key )
{
	const InstanceValues *m = instanceMetadata( instance, /* createIfMissing = */ false );
	if( !m )
	{
		return NULL;
	}
	
	InstanceValues::const_iterator vIt = m->find( key );
	if( vIt != m->end() )
	{
		return vIt->second.get();
	}
	
	return NULL;
}

void registerInstanceValueAction( const GraphComponent *instance, InternedString key, IECore::ConstDataPtr value )
{
	InstanceValues *m = instanceMetadata( instance, /* createIfMissing = */ value != NULL );
	if( !m )
	{
		return;
	}
	
	NamedInstanceValue namedValue( key, value );
	
	InstanceValues::const_iterator it = m->find( key );
	if( it == m->end() )
	{
		m->insert( namedValue );
	}
	else
	{
		m->replace( it, namedValue );
	}
	
	if( const Node *node = runTimeCast<const Node>( instance ) )
	{
		Metadata::nodeValueChangedSignal()( node->typeId(), key );
	}
	else if( const Plug *plug = runTimeCast<const Plug>( instance ) )
	{
		if( const Node *node = plug->node() )
		{
			Metadata::plugValueChangedSignal()( node->typeId(), plug->relativeName( node ), key );
		}
	}
}

void registerInstanceValue( GraphComponent *instance, IECore::InternedString key, IECore::ConstDataPtr value )
{
	const IECore::Data *currentValue = instanceValue( instance, key );
	if(
		( !currentValue && !value ) ||
		( currentValue && value && currentValue->isEqualTo( value.get() ) )
	)
	{
		return;
	}

	Action::enact(
		instance,
		// ok to bind raw pointers to instance, because enact() guarantees
		// the lifetime of the subject.
		boost::bind( &registerInstanceValueAction, instance, key, value ),
		boost::bind( &registerInstanceValueAction, instance, key, ConstDataPtr( currentValue ) )
	);
}

void registeredInstanceValues( const GraphComponent *graphComponent, std::vector<IECore::InternedString> &keys )
{
	if( const InstanceValues *im = instanceMetadata( graphComponent, /* createIfMissing = */ false ) )
	{
		const InstanceValues::nth_index<1>::type &index = im->get<1>();
		for( InstanceValues::nth_index<1>::type::const_iterator vIt = index.begin(), veIt = index.end(); vIt != veIt; ++vIt )
		{
			keys.push_back( vIt->first );
		}
	}
}

} // namespace

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

	nodeValueChangedSignal()( nodeTypeId, key );
}

void Metadata::registerNodeValue( Node *node, IECore::InternedString key, IECore::ConstDataPtr value )
{
	registerInstanceValue( node, key, value );
}

void Metadata::registeredNodeValues( const Node *node, std::vector<IECore::InternedString> &keys, bool inherit, bool instanceOnly )
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

	registeredInstanceValues( node, keys );
}

IECore::ConstDataPtr Metadata::nodeValueInternal( const Node *node, IECore::InternedString key, bool inherit, bool instanceOnly )
{
	if( const Data *iv = instanceValue( node, key ) )
	{
		return iv;
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
	
	plugValueChangedSignal()( nodeTypeId, plugPath, key );
}

void Metadata::registerPlugValue( Plug *plug, IECore::InternedString key, IECore::ConstDataPtr value )
{
	registerInstanceValue( plug, key, value );
}

void Metadata::registeredPlugValues( const Plug *plug, std::vector<IECore::InternedString> &keys, bool inherit, bool instanceOnly )
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

	registeredInstanceValues( plug, keys );
}

IECore::ConstDataPtr Metadata::plugValueInternal( const Plug *plug, IECore::InternedString key, bool inherit, bool instanceOnly )
{
	if( const Data *iv = instanceValue( plug, key ) )
	{
		return iv;
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
			NodeMetadata::PlugPathsToValues::const_iterator it, eIt;
			for( it = nIt->second.plugPathsToValues.begin(), eIt = nIt->second.plugPathsToValues.end(); it != eIt; ++it )
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
