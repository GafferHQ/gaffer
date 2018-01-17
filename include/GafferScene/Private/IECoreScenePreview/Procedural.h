//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#ifndef IECORESCENEPREVIEW_PROCEDURAL_H
#define IECORESCENEPREVIEW_PROCEDURAL_H

#include "IECoreScene/VisibleRenderable.h"

#include "GafferScene/Export.h"
#include "GafferScene/TypeIds.h"

namespace IECoreScenePreview
{

class Renderer;

/// \todo Would it be useful to have a virtual function that returns an
/// ExternalProcedural, for use when serialising scenes?
class GAFFERSCENE_API Procedural : public IECoreScene::VisibleRenderable
{

	public :

		Procedural();
		~Procedural();

		IE_CORE_DECLAREABSTRACTEXTENSIONOBJECT( Procedural, GafferScene::PreviewProceduralTypeId, IECoreScene::VisibleRenderable );

		/// Legacy inherited from IECore::VisibleRenderable.
		/// Should not be implemented by derived classes.
		void render( IECoreScene::Renderer *renderer ) const final;
		/// Render function for use with new renderer backends.
		/// Must be implemented by derived classes.
		virtual void render( Renderer *renderer ) const = 0;

};

IE_CORE_DECLAREPTR( Procedural )

} // namespace IECoreScenePreview

#endif // IECORESCENEPREVIEW_PROCEDURAL_H
