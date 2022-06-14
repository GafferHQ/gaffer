//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

#ifndef GAFFERSCENE_EDITSCOPEALGO_H
#define GAFFERSCENE_EDITSCOPEALGO_H

#include "GafferScene/ScenePlug.h"
#include "GafferScene/TweakPlug.h"

#include "Gaffer/EditScope.h"
#include "Gaffer/TransformPlug.h"

#include "IECoreScene/ShaderNetwork.h"

namespace GafferScene
{

namespace EditScopeAlgo
{

// 'readOnlyReason' methods
// ========================
// If is often necessary to determine the cause of the read-only state of an
// edit, or whether an edit can be added to any given scope. These methods
// return the outward-most GraphComponent that is causing any given edit (or
// potential edit creation) to be read-only. Tools that create edits within a
// scope should first check this returns null before calling any 'acquire'
// method to avoid incorrectly modifying locked nodes/plugs.

// Pruning
// =======

GAFFERSCENE_API void setPruned( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, bool pruned );
GAFFERSCENE_API void setPruned( Gaffer::EditScope *scope, const IECore::PathMatcher &paths, bool pruned );
GAFFERSCENE_API bool getPruned( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path );
GAFFERSCENE_API const Gaffer::GraphComponent *prunedReadOnlyReason( const Gaffer::EditScope *scope );

// Transforms
// ==========
//
// These methods manipulate edits to the local transform of a location.

struct GAFFERSCENE_API TransformEdit
{

	TransformEdit(
		const Gaffer::V3fPlugPtr &translate,
		const Gaffer::V3fPlugPtr &rotate,
		const Gaffer::V3fPlugPtr &scale,
		const Gaffer::V3fPlugPtr &pivot
	);
	TransformEdit( const TransformEdit &rhs ) = default;

	Gaffer::V3fPlugPtr translate;
	Gaffer::V3fPlugPtr rotate;
	Gaffer::V3fPlugPtr scale;
	Gaffer::V3fPlugPtr pivot;

	Imath::M44f matrix() const;

	bool operator == ( const TransformEdit &rhs ) const;
	bool operator != ( const TransformEdit &rhs ) const;

	TransformEdit &operator=( const TransformEdit &rhs ) = default;

};

GAFFERSCENE_API bool hasTransformEdit( const Gaffer::EditScope *scope, const ScenePlug::ScenePath &path );
GAFFERSCENE_API std::optional<TransformEdit> acquireTransformEdit( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, bool createIfNecessary = true );
GAFFERSCENE_API void removeTransformEdit( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path );
GAFFERSCENE_API const Gaffer::GraphComponent *transformEditReadOnlyReason( const Gaffer::EditScope *scope, const ScenePlug::ScenePath &path );

// Shaders
// =======
//
// These methods edit shader parameters for a particular location.

GAFFERSCENE_API bool hasParameterEdit( const Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter );
GAFFERSCENE_API TweakPlug *acquireParameterEdit( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter, bool createIfNecessary = true );
GAFFERSCENE_API void removeParameterEdit( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter );
GAFFERSCENE_API const Gaffer::GraphComponent *parameterEditReadOnlyReason( const Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter );

} // namespace EditScopeAlgo

} // namespace GafferScene

#endif // GAFFERSCENE_EDITSCOPEALGO_H
