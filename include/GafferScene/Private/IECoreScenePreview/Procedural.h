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

#pragma once

#include "GafferScene/Export.h"

#include "GafferScene/Private/IECoreScenePreview/TypeIds.h"

#include "IECoreScene/VisibleRenderable.h"

#include "IECore/Version.h"

namespace IECoreScenePreview
{

class Renderer;

/// \todo Would it be useful to have a virtual function that returns an
/// ExternalProcedural, for use when serialising scenes?
class GAFFERSCENE_API Procedural : public IECoreScene::VisibleRenderable
{

	public :

		Procedural();
		~Procedural() override;

		IE_CORE_DECLAREEXTENSIONOBJECT( Procedural, IECoreScenePreview::PreviewProceduralTypeId, IECoreScene::VisibleRenderable );

#if CORTEX_COMPATIBILITY_VERSION < MAKE_CORTEX_COMPATIBILITY_VERSION( 10, 6 )
		void render( IECoreScene::Renderer *renderer ) const final {};
#endif
		/// Must be implemented by derived classes.
		virtual void render( Renderer *renderer ) const = 0;

};

IE_CORE_DECLAREPTR( Procedural )

} // namespace IECoreScenePreview
