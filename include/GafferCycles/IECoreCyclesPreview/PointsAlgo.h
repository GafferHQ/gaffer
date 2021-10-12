//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Alex Fuller. All rights reserved.
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
//     * Neither the name of Alex Fuller nor the names of any
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

#ifndef IECORECYCLES_POINTSALGO_H
#define IECORECYCLES_POINTSALGO_H

#ifdef WITH_CYCLES_POINTCLOUD

#include "GafferCycles/IECoreCyclesPreview/Export.h"

#include "IECoreScene/PointsPrimitive.h"

#include <vector>

// Cycles
#include "render/object.h"

namespace IECoreCycles
{

namespace PointsAlgo
{

/// Converts the specified IECoreScene::PointsPrimitive into a ccl::Object.
IECORECYCLES_API ccl::Object *convert( const IECoreScene::PointsPrimitive *points, const std::string &nodeName, ccl::Scene *scene = nullptr );
/// As above, but converting a moving object. If no motion converter
/// is available, the first sample is converted instead.
IECORECYCLES_API ccl::Object *convert( const std::vector<const IECoreScene::PointsPrimitive *> &points, const std::vector<float> &times, const int frameIdx, const std::string &nodeName, ccl::Scene *scene = nullptr );

} // namespace PointsAlgo

} // namespace IECoreCycles

#endif // WITH_CYCLES_POINTCLOUD

#endif // IECORECYCLES_POINTSALGO_H
