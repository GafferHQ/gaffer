//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "GafferScene/Export.h"

#include "IECoreScene/MeshPrimitive.h"
#include "IECore/Canceller.h"

namespace IECoreScenePreview
{

namespace MeshAlgo
{

enum class SubdivisionScheme
{
	Default,
	Bilinear,
	CatmullClark,
	Loop,

	First = Default,
	Last = Loop
};


// TODO : Should this take a const pointer to the mesh instead of a reference, in order to be consistent
// with existing IECoreScene::MeshAlgo functions? Not sure why they are that way, a reference seems a little cleaner.
// TODO : If one of the next things we're going to do is add apdaptive support, would it be worth preplanning for
// that to avoid an ABI break? We haven't planned yet what the adaptive options would be, but it seems like it
// would almost certainly be reasonable to take an optional pointer to an MeshTessellateAdaptiveOptions struct,
// even if that struct is currently empty.

GAFFERSCENE_API IECoreScene::MeshPrimitivePtr tessellateMesh(
	const IECoreScene::MeshPrimitive &mesh, int divisions, const IECore::Canceller *canceller = nullptr,
	bool calculateNormals = false, bool tessellatePolygons = false,
	SubdivisionScheme scheme = SubdivisionScheme::Default
);

} // namespace MeshAlgo

} // namespace IECoreScenePreview
