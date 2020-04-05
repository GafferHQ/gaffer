//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

#ifndef IECORECYCLES_MESHALGO_H
#define IECORECYCLES_MESHALGO_H

#include "GafferCycles/IECoreCyclesPreview/Export.h"

#include "IECoreScene/MeshPrimitive.h"

#include <vector>

// Cycles
#include "render/object.h"

namespace IECoreCycles
{

namespace MeshAlgo
{

/// Converts the specified IECoreScene::MeshPrimitive into a ccl::Object.
IECORECYCLES_API ccl::Object *convert( const IECoreScene::MeshPrimitive *mesh, const std::string &nodeName, ccl::Scene *scene = nullptr );
/// As above, but converting a moving object. If no motion converter
/// is available, the first sample is converted instead.
IECORECYCLES_API ccl::Object *convert( const std::vector<const IECoreScene::MeshPrimitive *> &samples, const std::vector<float> &times, const int frameIdx, const std::string &nodeName, ccl::Scene *scene = nullptr );
/// Compute tangents.
IECORECYCLES_API void computeTangents( ccl::Mesh *cmesh, const IECoreScene::MeshPrimitive *mesh, bool needsign );

} // namespace MeshAlgo

} // namespace IECoreCycles

#endif // IECORECYCLES_MESHALGO_H
