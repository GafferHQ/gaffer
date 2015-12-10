//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENEUI_LIGHTVISUALISER_H
#define GAFFERSCENEUI_LIGHTVISUALISER_H

#include "IECore/Light.h"

#include "GafferSceneUI/Visualiser.h"

namespace GafferSceneUI
{

IE_CORE_FORWARDDECLARE( LightVisualiser )

/// Class for visualisation of lights. All lights in Gaffer are represented
/// as IECore::Light objects, but we need to visualise them differently
/// depending on their shader name (accessed using `IECore::Light::getName()`). A
/// factory mechanism is provided to map from this type to a specialised
/// LightVisualiser.
class LightVisualiser : public Visualiser
{

	public :

		IE_CORE_DECLAREMEMBERPTR( LightVisualiser )

		typedef IECore::Light ObjectType;

		LightVisualiser();
		virtual ~LightVisualiser();

		/// Uses a custom visualisation registered via `registerLightVisualiser()` if one
		/// is available, if not falls back to a basic point light visualisation.
		virtual IECoreGL::ConstRenderablePtr visualise( const IECore::Object *object ) const;

		/// Registers a visualiser to use for the specified light type.
		static void registerLightVisualiser( const IECore::InternedString &name, ConstLightVisualiserPtr visualiser );

	protected :

		static VisualiserDescription<LightVisualiser> g_visualiserDescription;

};

} // namespace GafferSceneUI

#endif // GAFFERSCENEUI_LIGHTVISUALISER_H
