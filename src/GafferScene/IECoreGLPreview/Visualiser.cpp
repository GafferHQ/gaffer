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

#include "GafferScene/Private/IECoreGLPreview/Visualiser.h"

using namespace IECoreGLPreview;

Visualisation::Visualisation( const IECoreGL::ConstRenderablePtr &renderable, Scale scale, Category category, bool affectsFramingBound, ColorSpace colorSpace )
	: renderable( renderable ), scale( scale ), category( category ), affectsFramingBound( affectsFramingBound ), colorSpace( colorSpace )
{
}

Visualisation Visualisation::createGeometry( const IECoreGL::ConstRenderablePtr &renderable, ColorSpace colorSpace )
{
	Visualisation v( renderable );
	v.colorSpace = colorSpace;
	return v;
}

Visualisation Visualisation::createOrnament( const IECoreGL::ConstRenderablePtr &renderable, bool affectsFramingBounds, ColorSpace colorSpace )
{
	Visualisation v( renderable );
	v.scale = Visualisation::Scale::Visualiser;
	v.affectsFramingBound = affectsFramingBounds;
	v.colorSpace = colorSpace;
	return v;
}

Visualisation Visualisation::createFrustum( const IECoreGL::ConstRenderablePtr &renderable, Scale scale, ColorSpace colorSpace )
{
	Visualisation v( renderable );
	v.affectsFramingBound = false;
	v.category = Visualisation::Category::Frustum;
	v.scale = scale;
	v.colorSpace = colorSpace;
	return v;
}
