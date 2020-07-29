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

#ifndef GAFFER_METADATAALGO_H
#define GAFFER_METADATAALGO_H

#include "Gaffer/Export.h"
#include "Gaffer/Node.h"

#include "IECore/StringAlgo.h"
#include "IECore/TypeIds.h"

#include <vector>

namespace Gaffer
{

class GraphComponent;
class Plug;

namespace MetadataAlgo
{

/// Read-only-ness
/// ==============
///
/// The Gaffer API itself provides few restrictions about how and when a node graph
/// can be edited. Methods such as `GraphComponent::acceptsChild()` and `Plug::acceptsInput()`
/// do provide protection against the creation of totally invalid graphs, but beyond that
/// all responsibility lies with the user.
///
/// The "readOnly" metadata improves this situation by providing a hint that the user should
/// not be allowed to edit the target plug or node despite this underlying flexibility of the API.
/// It can be set either by implementations to protect their internals, or directly by users
/// to "lock" parts of their graph against modification by others.
///
/// In other words, the API itself provides hard constraints as to what _could_ be edited,
/// and "readOnly" metadata provides a convention as to what _should_ be edited from a user
/// standpoint.
///
/// > Note :
/// >
/// > The primary reason for implementing read-only-ness as a convention rather than a hard API
/// > constraint is that many nodes use the API to modify their internals on the fly, even when
/// > those nodes are read-only from a user perspective. For instance, a switch may modify internal
/// > connections as part of its implementation, and needs to continue to do so even when
/// > hosted inside a Reference (because the index may be promoted). In this scenario, the API
/// > must allow edits, although the UI should not.

/// \undoable
GAFFER_API void setReadOnly( GraphComponent *graphComponent, bool readOnly, bool persistent = true );
GAFFER_API bool getReadOnly( const GraphComponent *graphComponent );

/// The "childNodesAreReadOnly" metadata is similar to the "readOnly" metadata
/// but only indicates the read-only-ness to the internal nodes of a node, and not its own plugs.

/// \undoable
GAFFER_API void setChildNodesAreReadOnly( Node *node, bool readOnly, bool persistent = true );
GAFFER_API bool getChildNodesAreReadOnly( const Node *node );

/// Takes into account the result of `getReadOnly()` and `getChildNodesAreReadOnly()` for ancestors,
/// so that read-only-ness is inherited.
/// This is the method that should be used to determine if a graphComponent should be editable
/// by the user or not.
GAFFER_API bool readOnly( const GraphComponent *graphComponent );
/// Returns the outer-most `GraphComponent` responsible for making `graphComponent` read-only. This may be
/// `graphComponent` itself. Returns `nullptr` if `graphComponent` is not considered read-only.
GAFFER_API const GraphComponent *readOnlyReason( const GraphComponent *graphComponent );

/// Determines if a metadata value change affects the result of `readOnly( graphComponent )`.
GAFFER_API bool readOnlyAffectedByChange( const GraphComponent *graphComponent, IECore::TypeId changedNodeTypeId, const IECore::StringAlgo::MatchPattern &changedPlugPath, const IECore::InternedString &changedKey, const Gaffer::Plug *changedPlug );
GAFFER_API bool readOnlyAffectedByChange( const GraphComponent *graphComponent, IECore::TypeId changedNodeTypeId, const IECore::InternedString &changedKey, const Gaffer::Node *changedNode );
GAFFER_API bool readOnlyAffectedByChange( const IECore::InternedString &changedKey );

/// Bookmarks
/// =========
///
/// Node bookmarks can be used to mark a subset of a complex graph as important to the user.
/// This metadata may be fetched by client code in order to provide convenient mechanisms for
/// accessing the node and/or its plugs.

/// \undoable
GAFFER_API void setBookmarked( Node *node, bool bookmarked, bool persistent = true );
GAFFER_API bool getBookmarked( const Node *node );
GAFFER_API bool bookmarkedAffectedByChange( const IECore::InternedString &changedKey );
GAFFER_API void bookmarks( const Node *node, std::vector<NodePtr> &bookmarks );

/// Numeric Bookmarks
/// =================
///
/// Each script has a set of numeric bookmarks numbered 1-9, each of which can
//  have a single node assigned. Reassigning a numeric bookmark will
/// consequently remove it from another node. Nodes can be assigned to a
/// single numeric bookmark at a time.
/// The following functions throw if given bookmark is not in {1, ..., 9}.

/// \undoable, pass a nullptr to remove the bookmark.
GAFFER_API void setNumericBookmark( ScriptNode *script, int bookmark, Node *node );
GAFFER_API Node *getNumericBookmark( ScriptNode *script, int bookmark );
/// Returns 0 if the node isn't assigned, the bookmark otherwise.
GAFFER_API int numericBookmark( const Node *node );
GAFFER_API bool numericBookmarkAffectedByChange( const IECore::InternedString &changedKey );

/// Utilities
/// =========

/// Determines if a metadata value change (as signalled by `Metadata::plugValueChangedSignal()`
/// or `Metadata:nodeValueChangedSignal()`) affects a given plug or node.
GAFFER_API bool affectedByChange( const Plug *plug, IECore::TypeId changedTypeId, const IECore::StringAlgo::MatchPattern &changedPlugPath, const Gaffer::Plug *changedPlug );
GAFFER_API bool affectedByChange( const Node *node, IECore::TypeId changedNodeTypeId, const Gaffer::Node *changedNode );
/// As above, but determines if any child will be affected.
GAFFER_API bool childAffectedByChange( const GraphComponent *parent, IECore::TypeId changedTypeId, const IECore::StringAlgo::MatchPattern &changedPlugPath, const Gaffer::Plug *changedPlug );
GAFFER_API bool childAffectedByChange( const GraphComponent *parent, IECore::TypeId changedNodeTypeId, const Gaffer::Node *changedNode );
/// As above, but determines if any ancestor will be affected.
GAFFER_API bool ancestorAffectedByChange( const Plug *plug, IECore::TypeId changedTypeId, const IECore::StringAlgo::MatchPattern &changedPlugPath, const Gaffer::Plug *changedPlug );
GAFFER_API bool ancestorAffectedByChange( const GraphComponent *graphComponent, IECore::TypeId changedNodeTypeId, const Gaffer::Node *changedNode );

/// Copies metadata from one target to another. The exclude pattern is used with StringAlgo::matchMultiple().
/// \undoable
GAFFER_API void copy( const GraphComponent *from, GraphComponent *to, const IECore::StringAlgo::MatchPattern &exclude = "", bool persistentOnly = true, bool persistent = true );

/// Copy nodule and noodle color meta data from srcPlug to dstPlug
/// \undoable
GAFFER_API void copyColors( const Gaffer::Plug *srcPlug, Gaffer::Plug *dstPlug, bool overwrite );

} // namespace MetadataAlgo

} // namespace Gaffer

#endif // GAFFER_METADATAALGO_H
