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

#include "boost/lambda/lambda.hpp"

#include "Gaffer/Node.h"

#include "Gaffer/Metadata.h"

using namespace std;
using namespace IECore;

namespace Gaffer
{

namespace Detail
{

struct NodeMetadata
{

	typedef map<InternedString, Metadata::NodeValueFunction> NodeValues;
	typedef map<InternedString, Metadata::PlugValueFunction> PlugValues;
	typedef map<boost::regex, PlugValues> PlugPathsToValues;

	NodeValues nodeValues;
	PlugPathsToValues plugPathsToValues;
	
};

typedef std::map<IECore::TypeId, NodeMetadata> NodeMetadataMap;

static NodeMetadataMap &nodeMetadataMap()
{
	static NodeMetadataMap m;
	return m;
}

} // namespace Detail

void Metadata::registerNodeValue( IECore::TypeId nodeTypeId, IECore::InternedString key, IECore::ConstDataPtr value )
{
	registerNodeValue( nodeTypeId, key, boost::lambda::constant( value ) );
}

void Metadata::registerNodeValue( IECore::TypeId nodeTypeId, IECore::InternedString key, NodeValueFunction value )
{
	Detail::NodeMetadata &nodeMetadata = Detail::nodeMetadataMap()[nodeTypeId];
	nodeMetadata.nodeValues[key] = value;
}

IECore::ConstDataPtr Metadata::nodeValueInternal( const Node *node, IECore::InternedString key, bool inherit )
{
	IECore::TypeId typeId = node->typeId();
	while( typeId != InvalidTypeId )
	{
		Detail::NodeMetadataMap::const_iterator nIt = Detail::nodeMetadataMap().find( typeId );
		if( nIt != Detail::nodeMetadataMap().end() )
		{
			Detail::NodeMetadata::NodeValues::const_iterator vIt = nIt->second.nodeValues.find( key );
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

void Metadata::registerPlugValue( IECore::TypeId nodeTypeId, const boost::regex &plugPath, IECore::InternedString key, IECore::ConstDataPtr value )
{
	registerPlugValue( nodeTypeId, plugPath, key, boost::lambda::constant( value ) );
}

void Metadata::registerPlugValue( IECore::TypeId nodeTypeId, const boost::regex &plugPath, IECore::InternedString key, PlugValueFunction value )
{
	Detail::NodeMetadata &nodeMetadata = Detail::nodeMetadataMap()[nodeTypeId];
	Detail::NodeMetadata::PlugValues &plugValues = nodeMetadata.plugPathsToValues[plugPath];
	plugValues[key] = value; 
}

IECore::ConstDataPtr Metadata::plugValueInternal( const Plug *plug, IECore::InternedString key, bool inherit )
{
	const Node *node = plug->node();
	if( !node )
	{
		return NULL;
	}
	
	const string plugPath = plug->relativeName( node );
	
	IECore::TypeId typeId = node->typeId();
	while( typeId != InvalidTypeId )
	{
		Detail::NodeMetadataMap::const_iterator nIt = Detail::nodeMetadataMap().find( typeId );
		if( nIt != Detail::nodeMetadataMap().end() )
		{
			Detail::NodeMetadata::PlugPathsToValues::const_iterator it, eIt;
			for( it = nIt->second.plugPathsToValues.begin(), eIt = nIt->second.plugPathsToValues.end(); it != eIt; ++it )
			{
				if( boost::regex_match( plugPath, it->first ) )
				{
					Detail::NodeMetadata::PlugValues::const_iterator vIt = it->second.find( key );
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

void Metadata::registerPlugDescription( IECore::TypeId nodeTypeId, const boost::regex &plugPath, const std::string &description )
{
	registerPlugValue( nodeTypeId, plugPath, "description", ConstDataPtr( new StringData( description ) ) );
}

void Metadata::registerPlugDescription( IECore::TypeId nodeTypeId, const boost::regex &plugPath, PlugValueFunction description )
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

} // namespace Gaffer
