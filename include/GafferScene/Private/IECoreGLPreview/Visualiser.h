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

#pragma once

#include "GafferScene/Export.h"

#include "IECoreGL/Renderable.h"

#include <array>

namespace IECoreGLPreview
{

// Visualiser classes return one or more Visualisations.
// A Visualisation holds a single IECoreGL::Renderable. This can be a primitive
// or a group for more complex cases. Visualisers support a number of options
// to control how they respond to the various scaling and visibility controls,
// as well as whether the contribute to the framing bound for a location.

struct GAFFERSCENE_API Visualisation
{
	// Determines how a visualiser reacts to a location's transformation matrix
	// and the visualisation scale control attribute `gl:visualiser:scale`.
	//
	//  - None : No scaling is applied, only the translation/rotation of
	//           the location's transform is inherited.
	//
	//  - Local : The visualisation is considered in 'local space' and it
	//           fully inherits the location's matrix.
	//
	//  - Visualiser : The visualisation inherits the location's
	//           translation/rotation but is scaled by gl:visualiser:scale.
	//
	//  - LocalAndVisualiser : The visualisation inherits the location's
	//           full matrix, and is then additionally scaled by
	//           gl:visualiser:scale.
	//
	enum class Scale
	{
		None,
		Local,
		Visualiser,
		LocalAndVisualiser
	};

	// Categories may be turned on/off by the user. The renderer will omit
	// disabled visualisations during rendering or bounding of a location.
	//
	// Note: This is a bit-mask to make it easier for the renderer
	// to select visualisations. Visualisers should only ever apply
	// a single category to any specific visualisation.
	enum Category
	{
		Generic = 1,
		Frustum = 2
	};

	enum class ColorSpace
	{
		Scene,
		Display
	};

	Visualisation(
		const IECoreGL::ConstRenderablePtr &renderable,
		Scale scale = Scale::Local,
		Category category = Category::Generic,
		bool affectsFramingBound = true,
		ColorSpace colorSpace = ColorSpace::Scene
	);

	IECoreGL::ConstRenderablePtr renderable;
	Scale scale;
	Category category;
	bool affectsFramingBound;
	ColorSpace colorSpace;

	// Convenience constructors for well-known types of visualisation

	// A visualisation representing an object to be rendered as a primitive would.
	static Visualisation createGeometry( const IECoreGL::ConstRenderablePtr &renderable, ColorSpace colorSpace = ColorSpace::Display );
	// An abstract visualisation or other decoration that uses `Scale::Visualiser`.
	static Visualisation createOrnament( const IECoreGL::ConstRenderablePtr &renderable, bool affectsFramingBounds, ColorSpace colorSpace = ColorSpace::Display );
	// Frustums visualisations should be used for cameras or other 'projections'
	// such as spot lights. By default they don't contribute to the framing bound
	// for the location to make scene navigation easier.
	static Visualisation createFrustum( const IECoreGL::ConstRenderablePtr &renderable, Scale scale, ColorSpace colorSpace = ColorSpace::Display );

};


using Visualisations = std::vector<Visualisation>;

} // namespace IECoreGLPreview
