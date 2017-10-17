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

#include <vector>

#include "IECore/TypeIds.h"

#include "Gaffer/Node.h"
#include "Gaffer/StringAlgo.h"

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

void setReadOnly( GraphComponent *graphComponent, bool readOnly, bool persistent = true );
bool getReadOnly( const GraphComponent *graphComponent );

/// The "childNodesAreReadOnly" metadata is similar to the "readOnly" metadata
/// but only indicates the read-only-ness to the internal nodes of a node, and not its own plugs.

void setChildNodesAreReadOnly( Node *node, bool readOnly, bool persistent = true );
bool getChildNodesAreReadOnly( const Node *node );

/// Takes into account the result of `getReadOnly()` and `getChildNodesAreReadOnly()` for ancestors,
/// so that read-only-ness is inherited.
/// This is the method that should be used to determine if a graphComponent should be editable
/// by the user or not.
bool readOnly( const GraphComponent *graphComponent );

/// Bookmarks
/// =========
///
/// Node bookmarks can be used to mark a subset of a complex graph as important to the user.
/// This metadata may be fetched by client code in order to provide convenient mechanisms for
/// accessing the node and/or its plugs.

void setBookmarked( Node *node, bool bookmarked, bool persistent = true );
bool getBookmarked( const Node *node );
void bookmarks( const Node *node, std::vector<NodePtr> &bookmarks );

/// Utilities
/// =========

/// Determines if a metadata value change (as signalled by `Metadata::plugValueChangedSignal()`
/// or `Metadata:nodeValueChangedSignal()`) affects a given plug or node.
bool affectedByChange( const Plug *plug, IECore::TypeId changedNodeTypeId, const StringAlgo::MatchPattern &changedPlugPath, const Gaffer::Plug *changedPlug );
bool affectedByChange( const Node *node, IECore::TypeId changedNodeTypeId, const Gaffer::Node *changedNode );
/// As above, but determines if any child will be affected.
bool childAffectedByChange( const GraphComponent *parent, IECore::TypeId changedNodeTypeId, const StringAlgo::MatchPattern &changedPlugPath, const Gaffer::Plug *changedPlug );
bool childAffectedByChange( const GraphComponent *parent, IECore::TypeId changedNodeTypeId, const Gaffer::Node *changedNode );
/// As above, but determines if any ancestor plug will be affected. This is particularly useful in conjunction with
/// the `readOnly()` method.
bool ancestorAffectedByChange( const Plug *plug, IECore::TypeId changedNodeTypeId, const StringAlgo::MatchPattern &changedPlugPath, const Gaffer::Plug *changedPlug );

/// Copies metadata from one target to another. The exclude pattern is used with StringAlgo::matchMultiple().
void copy( const GraphComponent *from, GraphComponent *to, const StringAlgo::MatchPattern &exclude = "", bool persistentOnly = true, bool persistent = true );

/// Copy nodule and noodle color meta data from srcPlug to dstPlug
void copyColors( const Gaffer::Plug *srcPlug , Gaffer::Plug *dstPlug, bool overwrite );

} // namespace MetadataAlgo

} // namespace Gaffer

#endif // GAFFER_METADATAALGO_H
