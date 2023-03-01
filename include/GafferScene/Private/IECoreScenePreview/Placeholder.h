//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#pragma once

#include "GafferScene/Export.h"

#include "GafferScene/TypeIds.h"

#include "IECoreScene/VisibleRenderable.h"

namespace IECoreScenePreview
{

/// A renderable placeholder for geometry that hasn't been expanded yet.
class GAFFERSCENE_API Placeholder : public IECoreScene::VisibleRenderable
{

	public :

		Placeholder( const Imath::Box3f &bound = Imath::Box3f() );

		IE_CORE_DECLAREEXTENSIONOBJECT( IECoreScenePreview::Placeholder, GafferScene::PreviewPlaceholderTypeId, IECoreScene::VisibleRenderable );

		void setBound( const Imath::Box3f &bound );
		const Imath::Box3f &getBound() const;

		Imath::Box3f bound() const override;
		void render( IECoreScene::Renderer *renderer ) const override;

	private :

		static const unsigned int m_ioVersion;

		Imath::Box3f m_bound;

};

IE_CORE_DECLAREPTR( Placeholder );

} // namespace IECoreScenePreview
