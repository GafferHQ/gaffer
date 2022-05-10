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

#ifndef IECORECYCLES_SPHEREALGO_H
#define IECORECYCLES_SPHEREALGO_H

#include "GafferCycles/IECoreCyclesPreview/Export.h"

#include "IECoreScene/SpherePrimitive.h"

#include <vector>

// Cycles
#include "scene/object.h"

namespace IECoreCycles
{

namespace SphereAlgo
{

/// Converts the specified IECoreScene::SpherePrimitive into a ccl::Object.
IECORECYCLES_API ccl::Object *convert( const IECoreScene::SpherePrimitive *sphere, const std::string &nodeName, ccl::Scene *scene = nullptr );
/// As above, but converting a moving object. If no motion converter
/// is available, the first sample is converted instead.
IECORECYCLES_API ccl::Object *convert( const std::vector<const IECoreScene::SpherePrimitive *> &points, const std::vector<float> &times, const int frameIdx, const std::string &nodeName, ccl::Scene *scene = nullptr );

} // namespace SphereAlgo

} // namespace IECoreCycles

#endif // IECORECYCLES_SPHEREALGO_H
