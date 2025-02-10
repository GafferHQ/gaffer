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

#pragma once

#include "Gaffer/Export.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/Node.h"

#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"
#include "IECore/TypeIds.h"

#include "Imath/ImathColor.h"

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
GAFFER_API bool readOnlyAffectedByChange( const GraphComponent *graphComponent, const Gaffer::GraphComponent *changedGraphComponent, const IECore::InternedString &changedKey );
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

/// Annotations
/// ===========
///
/// Annotations define arbitrary text to be displayed in a coloured area
/// next to a node. Each node can have arbitrary numbers of annotations,
/// with different annotations being distinguished by their `name`.
/// Templates can be used to define defaults for standard annotation types.
/// The text from the template is used as a default when first creating
/// an annotation via the UI, and the colour from the template provides
/// the default colour if one is not specified explicitly by an annotation
/// itself.

struct GAFFER_API Annotation
{

	Annotation() = default;
	Annotation( const std::string &text );
	Annotation( const std::string &text, const Imath::Color3f &color );
	Annotation( const IECore::ConstStringDataPtr &text, const IECore::ConstColor3fDataPtr &color = nullptr );
	Annotation( const Annotation &other ) = default;
	Annotation( Annotation &&other ) = default;

	operator bool() const { return textData.get(); }

	bool operator == ( const Annotation &rhs );
	bool operator != ( const Annotation &rhs ) { return !(*this == rhs); };

	IECore::ConstStringDataPtr textData;
	IECore::ConstColor3fDataPtr colorData;

	const std::string &text() const { return textData ? textData->readable() : g_defaultText; }
	const Imath::Color3f &color() const { return colorData ? colorData->readable() : g_defaultColor; }

	private :

		static std::string g_defaultText;
		static Imath::Color3f g_defaultColor;

};

GAFFER_API void addAnnotation( Node *node, const std::string &name, const Annotation &annotation, bool persistent = true );
GAFFER_API Annotation getAnnotation( const Node *node, const std::string &name, bool inheritTemplate = false );
GAFFER_API void removeAnnotation( Node *node, const std::string &name );
[[deprecated( "Use alternative form with `RegistrationTypes` instead")]]
GAFFER_API void annotations( const Node *node, std::vector<std::string> &names );
GAFFER_API std::vector<std::string> annotations( const Node *node, Metadata::RegistrationTypes types = Metadata::RegistrationTypes::All );

/// Pass `user = false` for annotations not intended for creation directly by the user.
GAFFER_API void addAnnotationTemplate( const std::string &name, const Annotation &annotation, bool user = true );
GAFFER_API Annotation getAnnotationTemplate( const std::string &name );
GAFFER_API void removeAnnotationTemplate( const std::string &name );
/// Pass `userOnly = true` to omit templates registered with `user = false`.
GAFFER_API void annotationTemplates( std::vector<std::string> &names, bool userOnly = false );

GAFFER_API bool annotationsAffectedByChange( const IECore::InternedString &changedKey );

/// Change queries
/// ==============

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

/// Copying
/// =======

/// Copies metadata from one target to another.
/// \undoable
/// \todo Default `persistent` to true after removing the deprecated overload below.
GAFFER_API void copy( const GraphComponent *from, GraphComponent *to, bool persistent );
/// As above, but skipping items where `predicate( const GraphComponent *from, const GraphComponent *to, name )` returns false.
/// \undoable
template<typename Predicate>
void copyIf( const GraphComponent *from, GraphComponent *to, Predicate &&predicate, bool persistent = true );
/// \deprecated Either use the simpler version of `copy()`, or use `copyIf()` to implement exclusions.
GAFFER_API void copy( const GraphComponent *from, GraphComponent *to, const IECore::StringAlgo::MatchPattern &exclude = "", bool persistentOnly = true, bool persistent = true );

/// Copy nodule and noodle color meta data from srcPlug to dstPlug
/// \undoable
GAFFER_API void copyColors( const Gaffer::Plug *srcPlug, Gaffer::Plug *dstPlug, bool overwrite );

/// Promotability
/// =============

/// Returns true if metadata can be promoted from one plug to another.
GAFFER_API bool isPromotable( const GraphComponent *from, const GraphComponent *to, const IECore::InternedString &name );

/// Cleanup
/// =======

/// Removes any redundant metadata registrations from `graphComponent` and all
/// its descendants. By redundant we mean instance-level registrations that have
/// the same value as an exising type-based fallback, so that removing the
/// instance registration has no effect on the composed result.
/// \undoable
GAFFER_API void deregisterRedundantValues( GraphComponent *graphComponent );

} // namespace MetadataAlgo

} // namespace Gaffer

#include "Gaffer/MetadataAlgo.inl"
