//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/MetadataAlgo.h"

#include "Gaffer/GraphComponent.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"
#include "Gaffer/ScriptNode.h"

#include "IECore/SimpleTypedData.h"

#include <boost/regex.hpp> 

using namespace std;
using namespace IECore;

namespace
{

InternedString g_readOnlyName( "readOnly" );
InternedString g_childNodesAreReadOnlyName( "childNodesAreReadOnly" );
InternedString g_bookmarkedName( "bookmarked" );
InternedString g_numericBookmarkBaseName( "numericBookmark" );

size_t findNth( const std::string &s, char c, int n )
{
	size_t result = 0;
	while( n-- && result != string::npos )
	{
		result = s.find( c, result );
	}

	return result;
}

IECore::InternedString g_connectionColorKey( "connectionGadget:color" );
IECore::InternedString g_noduleColorKey( "nodule:color" );

void copy( const Gaffer::GraphComponent *src , Gaffer::GraphComponent *dst , IECore::InternedString key , bool overwrite )
{
	if ( !overwrite && Gaffer::Metadata::value<IECore::Data>( dst, key ) )
	{
		return;
	}

	if( IECore::ConstDataPtr data = Gaffer::Metadata::value<IECore::Data>( src, key ) )
	{
		Gaffer::Metadata::registerValue(dst, key, data, /* persistent =*/ true);
	}
}

IECore::InternedString numericBookmarkMetadataName( int bookmark )
{
	if( bookmark < 1 || bookmark > 9 )
	{
		throw IECore::Exception( "Values for numeric bookmarks need to be in {1, ..., 9}." );
	}

	return g_numericBookmarkBaseName.string() + std::to_string( bookmark );
}

} // namespace

namespace Gaffer
{

namespace MetadataAlgo
{

void setReadOnly( GraphComponent *graphComponent, bool readOnly, bool persistent )
{
	Metadata::registerValue( graphComponent, g_readOnlyName, new BoolData( readOnly ), persistent );
}

bool getReadOnly( const GraphComponent *graphComponent )
{
	ConstBoolDataPtr d = Metadata::value<BoolData>( graphComponent, g_readOnlyName );
	return d ? d->readable() : false;
}

void setChildNodesAreReadOnly( Node *node, bool readOnly, bool persistent )
{
	Metadata::registerValue( node, g_childNodesAreReadOnlyName, new BoolData( readOnly ), persistent );
}

bool getChildNodesAreReadOnly( const Node *node )
{
	ConstBoolDataPtr d = Metadata::value<BoolData>( node, g_childNodesAreReadOnlyName );
	return d ? d->readable() : false;
}

bool readOnly( const GraphComponent *graphComponent )
{
	bool haveNodeDescendants = false;

	while( graphComponent )
	{
		const Node *node = runTimeCast<const Node>( graphComponent );

		if( getReadOnly( graphComponent ) || ( node && haveNodeDescendants && getChildNodesAreReadOnly( node ) ) )
		{
			return true;
		}

		if( !haveNodeDescendants && node )
		{
			haveNodeDescendants = true;
		}

		graphComponent = graphComponent->parent();
	}
	return false;
}

bool readOnlyAffectedByChange( const GraphComponent *graphComponent, IECore::TypeId changedNodeTypeId, const IECore::StringAlgo::MatchPattern &changedPlugPath, const IECore::InternedString &changedKey, const Gaffer::Plug *changedPlug )
{
	if( changedKey != g_readOnlyName )
	{
		return false;
	}

	auto plug = runTimeCast<const Plug>( graphComponent );
	if( !plug )
	{
		return false;
	}

	if( affectedByChange( plug, changedNodeTypeId, changedPlugPath, changedPlug ) )
	{
		return true;
	}
	if( ancestorAffectedByChange( plug, changedNodeTypeId, changedPlugPath, changedPlug ) )
	{
		return true;
	}

	return false;
}

bool readOnlyAffectedByChange( const GraphComponent *graphComponent, IECore::TypeId changedNodeTypeId, const IECore::InternedString &changedKey, const Gaffer::Node *changedNode )
{
	if( changedKey == g_readOnlyName )
	{
		if( auto node = runTimeCast<const Node>( graphComponent ) )
		{
			if( affectedByChange( node, changedNodeTypeId, changedNode ) )
			{
				return true;
			}
		}
		if( ancestorAffectedByChange( graphComponent, changedNodeTypeId, changedNode ) )
		{
			return true;
		}
	}
	else if( changedKey == g_childNodesAreReadOnlyName )
	{
		return ancestorAffectedByChange( graphComponent, changedNodeTypeId, changedNode );
	}
	return false;
}

bool readOnlyAffectedByChange( const IECore::InternedString &changedKey )
{
	return changedKey == g_readOnlyName || changedKey == g_childNodesAreReadOnlyName;
}

void setBookmarked( Node *node, bool bookmarked, bool persistent /* = true */ )
{
	if( bookmarked )
	{
		Metadata::registerValue( node, g_bookmarkedName, new BoolData( true ), persistent );
	}
	else
	{
		Metadata::deregisterValue( node, g_bookmarkedName );
	}
}

bool getBookmarked( const Node *node )
{
	ConstBoolDataPtr d = Metadata::value<BoolData>( node, g_bookmarkedName );
	return d ? d->readable() : false;
}

bool bookmarkedAffectedByChange( const IECore::InternedString &changedKey )
{
	return changedKey == g_bookmarkedName;
}

void bookmarks( const Node *node, std::vector<NodePtr> &bookmarks )
{
	bookmarks.clear();

	for( NodeIterator it( node ); !it.done(); ++it )
	{
		if( getBookmarked( it->get() ) )
		{
			bookmarks.push_back( *it );
		}
	}
}

void setNumericBookmark( ScriptNode *scriptNode, int bookmark, Node *node )
{
	// No other node can have the same bookmark value assigned
	IECore::InternedString metadataName( numericBookmarkMetadataName( bookmark ) );
	for( Node *nodeWithMetadata : Metadata::nodesWithMetadata( scriptNode, metadataName, /* instanceOnly = */ true ) )
	{
		Metadata::deregisterValue( nodeWithMetadata, metadataName );
	}

	if( !node )
	{
		return;
	}

	// Replace a potentially existing value with the one that is to be assigned.
	int currentValue = numericBookmark( node );
	if( currentValue )
	{
		Metadata::deregisterValue( node, numericBookmarkMetadataName( currentValue) );
	}

	Metadata::registerValue( node, metadataName, new BoolData( true ), /* persistent = */ false );
}

Node *getNumericBookmark( ScriptNode *scriptNode, int bookmark )
{
	// Return the first one we find. There should only ever be just one matching node.
	for( Node *nodeWithMetadata : Metadata::nodesWithMetadata( scriptNode, numericBookmarkMetadataName( bookmark ), /* instanceOnly = */ true ) )
	{
		return nodeWithMetadata;
	}

	return nullptr;
}

int numericBookmark( const Node *node )
{
	// Return the first one we find. There should only ever be just one matching value.
	for( int bookmark = 1; bookmark < 10; ++bookmark )
	{
		if( Metadata::value<BoolData>( node, numericBookmarkMetadataName( bookmark ) ) )
		{
			return bookmark;
		}
	}

	return 0;
}

bool numericBookmarkAffectedByChange( const IECore::InternedString &changedKey )
{
	boost::regex expr{ g_numericBookmarkBaseName.string() + "[1-9]" };
	return boost::regex_match( changedKey.string(), expr );
}

bool affectedByChange( const Plug *plug, IECore::TypeId changedNodeTypeId, const IECore::StringAlgo::MatchPattern &changedPlugPath, const Gaffer::Plug *changedPlug )
{
	if( changedPlug )
	{
		return plug == changedPlug;
	}

	const Node *node = plug->node();
	if( !node || !node->isInstanceOf( changedNodeTypeId ) )
	{
		return false;
	}

	if( StringAlgo::match( plug->relativeName( node ), changedPlugPath ) )
	{
		return true;
	}

	return false;
}

bool childAffectedByChange( const GraphComponent *parent, IECore::TypeId changedNodeTypeId, const IECore::StringAlgo::MatchPattern &changedPlugPath, const Gaffer::Plug *changedPlug )
{
	if( changedPlug )
	{
		return parent == changedPlug->parent();
	}

	const Node *node = runTimeCast<const Node>( parent );
	if( !node )
	{
		node = parent->ancestor<Node>();
	}

	if( !node || !node->isInstanceOf( changedNodeTypeId ) )
	{
		return false;
	}

	if( parent == node )
	{
		return changedPlugPath.find( '.' ) == string::npos;
	}

	const string parentName = parent->relativeName( node );
	const size_t n = count( parentName.begin(), parentName.end(), '.' ) + 1;
	const size_t parentMatchPatternEnd = findNth( changedPlugPath, '.', n );

	if( parentMatchPatternEnd == string::npos )
	{
		return false;
	}

	return StringAlgo::match( parentName, changedPlugPath.substr( 0, parentMatchPatternEnd ) );
}

bool childAffectedByChange( const GraphComponent *parent, IECore::TypeId changedNodeTypeId, const Gaffer::Node *changedNode )
{
	if( changedNode )
	{
		return parent == changedNode->parent();
	}

	for( NodeIterator it( parent ); !it.done(); ++it )
	{
		if( (*it)->isInstanceOf( changedNodeTypeId ) )
		{
			return true;
		}
	}

	return false;
}

bool ancestorAffectedByChange( const Plug *plug, IECore::TypeId changedNodeTypeId, const IECore::StringAlgo::MatchPattern &changedPlugPath, const Gaffer::Plug *changedPlug )
{
	if( changedPlug )
	{
		return changedPlug->isAncestorOf( plug );
	}

	while( ( plug = plug->parent<Plug>() ) )
	{
		if( affectedByChange( plug, changedNodeTypeId, changedPlugPath, changedPlug ) )
		{
			return true;
		}
	}

	return false;
}

bool ancestorAffectedByChange( const GraphComponent *graphComponent, IECore::TypeId changedNodeTypeId, const Gaffer::Node *changedNode )
{
	if( changedNode )
	{
		return changedNode->isAncestorOf( graphComponent );
	}

	while( ( graphComponent = graphComponent->parent<GraphComponent>() ) )
	{
		if( auto node = runTimeCast<const Node>( graphComponent ) )
		{
			if( affectedByChange( node, changedNodeTypeId, changedNode ) )
			{
				return true;
			}
		}
	}
	return false;
}

bool affectedByChange( const Node *node, IECore::TypeId changedNodeTypeId, const Gaffer::Node *changedNode )
{
	if( changedNode )
	{
		return node == changedNode;
	}

	return node->isInstanceOf( changedNodeTypeId );
}

void copy( const GraphComponent *from, GraphComponent *to, const IECore::StringAlgo::MatchPattern &exclude, bool persistentOnly, bool persistent )
{
	vector<IECore::InternedString> keys;
	Metadata::registeredValues( from, keys, /* instanceOnly = */ false, /* persistentOnly = */ persistentOnly );
	for( vector<IECore::InternedString>::const_iterator it = keys.begin(), eIt = keys.end(); it != eIt; ++it )
	{
		if( StringAlgo::matchMultiple( it->string(), exclude ) )
		{
			continue;
		}
		Metadata::registerValue( to, *it, Metadata::value<IECore::Data>( from, *it ), persistent );
	}

	for( GraphComponent::ChildIterator it = from->children().begin(), eIt = from->children().end(); it != eIt; ++it )
	{
		if( GraphComponent *childTo = to->getChild( (*it)->getName() ) )
		{
			copy( it->get(), childTo, exclude, persistentOnly, persistent );
		}
	}
}

void copyColors( const Gaffer::Plug *srcPlug , Gaffer::Plug *dstPlug, bool overwrite )
{
	::copy(srcPlug, dstPlug, g_connectionColorKey, overwrite);
	::copy(srcPlug, dstPlug, g_noduleColorKey, overwrite);
}

} // namespace MetadataAlgo

} // namespace Gaffer
