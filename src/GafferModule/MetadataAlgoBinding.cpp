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

#include "boost/python.hpp"

#include "MetadataAlgoBinding.h"

#include "Gaffer/GraphComponent.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"
#include "Gaffer/ScriptNode.h"

#include "IECorePython/ScopedGILLock.h"
#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace Gaffer;
using namespace Gaffer::MetadataAlgo;

namespace
{

void setReadOnlyWrapper( GraphComponent &graphComponent, bool readOnly, bool persistent )
{
	IECorePython::ScopedGILRelease gilRelease;
	setReadOnly( &graphComponent, readOnly, persistent );
}

void setChildNodesAreReadOnlyWrapper( Node &node, bool readOnly, bool persistent )
{
	IECorePython::ScopedGILRelease gilRelease;
	setChildNodesAreReadOnly( &node, readOnly, persistent );
}

bool readOnlyWrapper( GraphComponent &g )
{
	return readOnly( &g );
}

GraphComponentPtr readOnlyReasonWrapper( GraphComponent &g )
{
	return const_cast<GraphComponent *>( readOnlyReason( &g ) );
}

void setBookmarkedWrapper( Node &node, bool bookmarked, bool persistent )
{
	IECorePython::ScopedGILRelease gilRelease;
	setBookmarked( &node, bookmarked, persistent );
}

boost::python::list bookmarksWrapper( const Node *node )
{
	std::vector<NodePtr> bookmarks;
	MetadataAlgo::bookmarks( node, bookmarks );

	boost::python::list result;
	for( std::vector<NodePtr>::const_iterator it = bookmarks.begin(), endIt = bookmarks.end(); it != endIt; ++it )
	{
		result.append( *it );
	}

	return result;
}

void setNumericBookmarkWrapper( ScriptNode &scriptNode, int bookmark, NodePtr node )
{
	IECorePython::ScopedGILRelease gilRelease;
	setNumericBookmark( &scriptNode, bookmark, node.get() );
}

NodePtr getNumericBookmarkWrapper( ScriptNode &scriptNode, int bookmark )
{
	return getNumericBookmark( &scriptNode, bookmark );
}

boost::python::list numericBookmarksWrapper( Node &node )
{
	std::vector<int> bookmarks = numericBookmarks( &node );
	boost::python::list result;
	for( const auto &i : bookmarks )
	{
		result.append( i );
	}
	return result;
}

void setFocusNodeWrapper( ScriptNode &scriptNode, Node &node )
{
	IECorePython::ScopedGILRelease gilRelease;
	setFocusNode( &scriptNode, &node );
}

NodePtr getFocusNodeWrapper( ScriptNode &scriptNode )
{
	return getFocusNode( &scriptNode );
}

bool nodeIsFocusedWrapper( Node &node )
{
	return nodeIsFocused( &node );
}

void deprecatedCopyWrapper( const GraphComponent &from, GraphComponent &to, const IECore::StringAlgo::MatchPattern &exclude, bool persistentOnly, bool persistent )
{
	IECorePython::ScopedGILRelease gilRelease;
	copy( &from, &to, exclude, persistentOnly, persistent );
}

void copyWrapper( const GraphComponent &from, GraphComponent &to, bool persistent )
{
	IECorePython::ScopedGILRelease gilRelease;
	copy( &from, &to, persistent );
}

void copyIfWrapper( const GraphComponent &from, GraphComponent &to, object predicate, bool persistent )
{
	IECorePython::ScopedGILRelease gilRelease;
	copyIf(
		&from, &to,
		[&predicate] ( const GraphComponent *from, const GraphComponent *to, IECore::InternedString name ) {
			IECorePython::ScopedGILLock gilLock;
			return (bool)predicate(
				GraphComponentPtr( const_cast<GraphComponent *>( from ) ),
				GraphComponentPtr( const_cast<GraphComponent *>( to ) ),
				name.string()
			);
		},
		persistent
	);
}

void copyColorsWrapper( const Gaffer::Plug &srcPlug, Gaffer::Plug &dstPlug, bool overwrite )
{
	IECorePython::ScopedGILRelease gilRelease;
	copyColors( &srcPlug, &dstPlug, overwrite );
}

} // namespace

void GafferModule::bindMetadataAlgo()
{
	object module( borrowed( PyImport_AddModule( "Gaffer.MetadataAlgo" ) ) );
	scope().attr( "MetadataAlgo" ) = module;
	scope moduleScope( module );

	def( "setReadOnly", &setReadOnlyWrapper, ( arg( "graphComponent" ), arg( "readOnly"), arg( "persistent" ) = true ) );
	def( "getReadOnly", &getReadOnly );
	def( "setChildNodesAreReadOnly", &setChildNodesAreReadOnlyWrapper, ( arg( "node" ), arg( "readOnly"), arg( "persistent" ) = true ) );
	def( "getChildNodesAreReadOnly", &getChildNodesAreReadOnly );
	def( "readOnly", &readOnlyWrapper );
	def( "readOnlyReason", &readOnlyReasonWrapper );
	def(
		"readOnlyAffectedByChange",
		(bool (*)( const GraphComponent *, IECore::TypeId, const IECore::StringAlgo::MatchPattern &, const IECore::InternedString &, const Gaffer::Plug * ))&readOnlyAffectedByChange,
		( arg( "graphComponent" ), arg( "changedNodeTypeId"), arg( "changedPlugPath" ), arg( "changedKey" ), arg( "changedPlug" ) )
	);
	def(
		"readOnlyAffectedByChange",
		(bool (*)( const GraphComponent *, IECore::TypeId, const IECore::InternedString &, const Gaffer::Node * ))&readOnlyAffectedByChange,
		( arg( "graphComponent" ), arg( "changedNodeTypeId"), arg( "changedKey" ), arg( "changedNode" ) )
	);
	def(
		"readOnlyAffectedByChange",
		(bool (*)( const IECore::InternedString & ))&readOnlyAffectedByChange,
		( arg( "changedKey" ) )
	);

	def( "setBookmarked", &setBookmarkedWrapper, ( arg( "graphComponent" ), arg( "bookmarked"), arg( "persistent" ) = true ) );
	def( "getBookmarked", &getBookmarked );
	def( "bookmarkedAffectedByChange", &bookmarkedAffectedByChange );
	def( "bookmarks", &bookmarksWrapper );

	def( "setNumericBookmark", &setNumericBookmarkWrapper, ( arg( "scriptNode" ), arg( "bookmark" ), arg( "node" ) ) );
	def( "getNumericBookmark", &getNumericBookmarkWrapper, ( arg( "scriptNode" ), arg( "bookmark" ) ) );
	def( "numericBookmarks", &numericBookmarksWrapper, ( arg( "node" ) ) );
	def( "numericBookmarkAffectedByChange", &numericBookmarkAffectedByChange, ( arg( "changedKey" ) ) );

	def( "setFocusNode", &setFocusNodeWrapper, ( arg( "scriptNode" ), arg( "node" ) ) );
	def( "getFocusNode", &getFocusNodeWrapper, ( arg( "scriptNode" ) ) );
	def( "nodeIsFocused", &nodeIsFocusedWrapper, ( arg( "node" ) ) );
	def( "focusNodeAffectedByChange", &focusNodeAffectedByChange, ( arg( "changedKey" ) ) );

	def(
		"affectedByChange",
		(bool (*)( const Plug *, IECore::TypeId, const IECore::StringAlgo::MatchPattern &, const Plug * ))&affectedByChange,
		( arg( "plug" ), arg( "changedNodeTypeId"), arg( "changedPlugPath" ), arg( "changedPlug" ) )
	);
	def(
		"affectedByChange",
		(bool (*)( const Node *node, IECore::TypeId changedNodeTypeId, const Node *changedNode ))&affectedByChange,
		( arg( "node" ), arg( "changedNodeTypeId"), arg( "changedNode" ) )
	);

	def(
		"childAffectedByChange",
		(bool (*)( const GraphComponent *, IECore::TypeId, const IECore::StringAlgo::MatchPattern &, const Gaffer::Plug * ))&childAffectedByChange,
		( arg( "parent" ), arg( "changedNodeTypeId"), arg( "changedPlugPath" ), arg( "changedPlug" ) )
	);
	def(
		"childAffectedByChange",
		(bool (*)( const GraphComponent *, IECore::TypeId, const Gaffer::Node * ))&childAffectedByChange,
		( arg( "parent" ), arg( "changedNodeTypeId"), arg( "changedNode" ) )
	);

	def(
		"ancestorAffectedByChange",
		(bool (*)( const Plug *, IECore::TypeId, const IECore::StringAlgo::MatchPattern &, const Gaffer::Plug * ))&ancestorAffectedByChange,
		( arg( "plug" ), arg( "changedNodeTypeId"), arg( "changedPlugPath" ), arg( "changedPlug" ) )
	);

	def(
		"ancestorAffectedByChange",
		(bool (*)( const GraphComponent *, IECore::TypeId, const Gaffer::Node * ))&ancestorAffectedByChange,
		( arg( "graphComponent" ), arg( "changedNodeTypeId"), arg( "changedNode" ) )
	);

	def( "copy", &deprecatedCopyWrapper, ( arg( "from" ), arg( "to" ), arg( "exclude" ) = "", arg( "persistentOnly" ) = true, arg( "persistent" ) = true ) );
	def( "copy", &copyWrapper, ( arg( "from" ), arg( "to" ), arg( "persistent" ) ) );
	def( "copyIf", &copyIfWrapper, ( arg( "from" ), arg( "to" ), arg( "predicate" ), arg( "persistent" ) = true ) );

	def( "copyColors", &copyColorsWrapper,  (arg( "srcPlug" ), arg( "dstPlug" ), arg( "overwrite") ));

}
