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

#include "Gaffer/EditScope.h"
#include "Gaffer/TransformPlug.h"

#include "GafferScene/ScenePlug.h"

namespace GafferScene
{

namespace EditScopeAlgo
{

// Pruning
// =======

GAFFERSCENE_API void setPruned( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, bool pruned );
GAFFERSCENE_API void setPruned( Gaffer::EditScope *scope, const IECore::PathMatcher &paths, bool pruned );
GAFFERSCENE_API bool getPruned( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path );

// Transforms
// ==========
//
// These methods manipulate edits to the local transform of a location.

struct GAFFERSCENE_API TransformEdit
{
	const Gaffer::V3fPlugPtr translate;
	const Gaffer::V3fPlugPtr rotate;
	const Gaffer::V3fPlugPtr scale;
	const Gaffer::V3fPlugPtr pivot;
	Imath::M44f matrix() const;
};

GAFFERSCENE_API bool hasTransformEdit( const Gaffer::EditScope *scope, const ScenePlug::ScenePath &path );
GAFFERSCENE_API boost::optional<TransformEdit> acquireTransformEdit( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, bool createIfNecessary = true );
GAFFERSCENE_API void removeTransformEdit( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path );

} // namespace EditScopeAlgo

} // namespace GafferScene

#endif // GAFFERSCENE_EDITSCOPEALGO_H
