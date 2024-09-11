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
#include "IECore/Object.h"

namespace IECoreScenePreview
{

namespace PrimitiveAlgo
{

// Transform a primitive by a given matrix. Applies an appropriate transform to any primitive
// variables that have an interpretation of point, vector or normal.
GAFFERSCENE_API void transformPrimitive(
	IECoreScene::Primitive &primitive, Imath::M44f matrix,
	const IECore::Canceller *canceller = nullptr
);

// Merge a list of primitives with matching transforms into a single combined primitive.
// Supports meshes, curves and points ( all primitives in the list must be of a matching
// type ).
GAFFERSCENE_API IECoreScene::PrimitivePtr mergePrimitives(
	const std::vector< std::pair< const IECoreScene::Primitive*, Imath::M44f > > &primitives,
	const IECore::Canceller *canceller = nullptr
);

} // namespace MeshAlgo

} // namespace IECoreScenePreview
