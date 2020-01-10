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
//      * Neither the name of Cinesite VFX Ltd. nor the names of
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

#ifndef IECOREGLPREVIEW_VISUALISER_H
#define IECOREGLPREVIEW_VISUALISER_H

#include "IECoreGL/Renderable.h"

#include <array>

namespace IECoreGLPreview
{

enum VisualisationType
{
	Geometry, // Visualisations that inherit a location's transform.
	Ornament, // Visualisations that don't inherit a location's scale and aren't
	          // considered for bounds computation if geometry or a Geometric
	          // visualisation is present.
	Frustum   // Visualisations that inherit a location's transform and
	          // represent some in-world projection of frustum of the object.
};

// A container for renderables grouped by VisualisationType
using Visualisations = std::array<IECoreGL::ConstRenderablePtr, 3>;

namespace Private
{

// Appends any visualisations in source to target. In order to avoid
// over-nesting creating redundant GL state push/pops, it is assumed that target
// is a 'collector' map. And as such, it is safe to append any outer groups in
// source as direct children of the root group of each visualisation type.
void collectVisualisations( const Visualisations &source, Visualisations &target );

} // namespace Private

} // namespace IECoreGLPreview

#endif // IECOREGLPREVIEW_VISUALISER_H
