//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
#include "Gaffer/Plug.h"

#include "IECore/Data.h"
#include "IECore/InternedString.h"
#include "IECore/RefCounted.h"
#include "IECore/StringAlgo.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Context )
IE_CORE_FORWARDDECLARE( GraphComponent )
IE_CORE_FORWARDDECLARE( ValuePlug )

namespace PlugAlgo
{

/// Miscellaneous
/// =============

/// Adds `plug` as a child of `parent`, replacing an identically-named
/// child if it exists. Where possible, existing values and connections
/// are transferred from the original plug to the new one.
GAFFER_API void replacePlug( GraphComponent *parent, PlugPtr plug );

/// Returns `true` if the plug's value is provided by the output
/// of a ComputeNode, and `false` otherwise.
GAFFER_API bool dependsOnCompute( const ValuePlug *plug );

/// Visits the plug and its downstream outputs, returning the first `predicate( plug )`
/// result which evaluates to `true`. Traverses across Spreadsheets to visit the output
/// corresponding to a CellPlug input.
template<typename Predicate>
std::invoke_result_t<Predicate, Plug *> findDestination( Plug *plug, Predicate &&predicate );

/// Visits the plug and its inputs, returing the first `predicate( plug )` result which
/// evaluates to `true`.
template<typename Predicate>
std::invoke_result_t<Predicate, Plug *> findSource( Plug *plug, Predicate &&predicate );

/// Similar to `Plug::source()`, but also traversing upstream through Switch,
/// Spreadsheet, ContextProcessor and Loop nodes, taking into account their
/// operation in the current context. Returns the source plug and also the context
/// it is evaluated in.
///
/// > Note : If the current context contains a Canceller, then the returned context
/// > will reference it too. If the context is stored for later usage, the canceller
/// > should be removed.
GAFFER_API std::tuple<const Plug *, ConstContextPtr> contextSensitiveSource( const Plug *plug );

/// Conversion to and from `IECore::Data`
/// =====================================

/// Creates an appropriate plug to hold the specified data.
GAFFER_API ValuePlugPtr createPlugFromData( const std::string &name, Plug::Direction direction, unsigned flags, const IECore::Data *value );

/// Returns a Data value from a plug.
GAFFER_API IECore::DataPtr getValueAsData( const ValuePlug *plug );

/// Sets the value of an existing plug to the specified data.
/// Returns `true` on success and `false` on failure.
GAFFER_API bool setValueFromData( ValuePlug *plug, const IECore::Data *value );

/// Overload for use in `ComputeNode::compute()` implementations, where values may only
/// be set on leaf plugs.
GAFFER_API bool setValueFromData( const ValuePlug *plug, ValuePlug *leafPlug, const IECore::Data *value );

/// Returns true if the given plug's value can be set from Data.
/// If value is provided, then return true if it can be set from Data with this type id
GAFFER_API bool canSetValueFromData( const ValuePlug *plug, const IECore::Data *value = nullptr );

[[deprecated( "Use `getValueAsData()` instead" )]]
GAFFER_API IECore::DataPtr extractDataFromPlug( const ValuePlug *plug );

/// Promotion
/// =========
///
/// When a node has an internal node graph of its own, it
/// is often useful to expose some internal settings by
/// promoting internal plugs so that they are driven by
/// external plugs. These functions assist in this process.

/// Returns true if a call to `promote( plug, parent )` would
/// succeed, false otherwise.
GAFFER_API bool canPromote( const Plug *plug, const Plug *parent = nullptr );
/// Promotes an internal plug, returning the newly created external plug. By
/// default the external plug is parented directly to the node, but the `parent`
/// argument may specify a plug on that node to be used as parent instead.
/// Metadata is copied to the promoted plug, but copying can be disabled
/// by registering `"<metadataName>:promotable"` metadata with a value of `false`.
/// The `excludeMetadata` argument provides a secondary mechaniscm for the caller
/// to explicitly exclude other metadata from promotion.
/// \undoable
GAFFER_API Plug *promote( Plug *plug, Plug *parent = nullptr, const IECore::StringAlgo::MatchPattern &excludeMetadata = "layout:*" );
/// As `promote` but by providing the name argument, you can skip an additional
/// renaming step after promoting.
/// \undoable
GAFFER_API Plug *promoteWithName( Plug *plug, const IECore::InternedString &name, Plug *parent = nullptr, const IECore::StringAlgo::MatchPattern &excludeMetadata = "layout:*" );
/// Returns true if the plug appears to have been promoted.
GAFFER_API bool isPromoted( const Plug *plug );
/// Unpromotes a previously promoted plug, removing the
/// external plug where possible.
/// \undoable
GAFFER_API void unpromote( Plug *plug );

} // namespace PlugAlgo

} // namespace Gaffer

#include "Gaffer/PlugAlgo.inl"
