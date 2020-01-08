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

#ifndef IECOREGLPREVIEW_LIGHTVISUALISER_H
#define IECOREGLPREVIEW_LIGHTVISUALISER_H

#include "GafferScene/Export.h"

#include "GafferScene/Private/IECoreGLPreview/Visualiser.h"

#include "IECoreGL/Renderable.h"

#include "IECoreScene/ShaderNetwork.h"

#include "IECore/CompoundObject.h"

namespace IECoreGLPreview
{

IE_CORE_FORWARDDECLARE( LightVisualiser )

/// Class for visualisation of lights. All lights in Gaffer are represented
/// as IECore::Shader objects, but we need to visualise them differently
/// depending on their shader name (accessed using `IECore::Shader::getName()`). A
/// factory mechanism is provided to map from this name to a specialised
/// LightVisualiser.
class GAFFERSCENE_API LightVisualiser : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( LightVisualiser )

		LightVisualiser();
		~LightVisualiser() override;

		/// Must be implemented by derived classes to visualise
		/// the light contained within `shaderNetwork`.
		virtual Visualisations visualise(
			const IECore::InternedString &attributeName,
			const IECoreScene::ShaderNetwork *shaderNetwork,
			const IECore::CompoundObject *attributes,
			IECoreGL::ConstStatePtr &state
		) const = 0;

		/// Registers a visualiser to visualise a particular type of light.
		/// For instance, `registerLightVisualiser( "ai:light", "point_light", visualiser )`
		/// would register a visualiser for an Arnold point light.
		static void registerLightVisualiser(
			const IECore::InternedString &attributeName,
			const IECore::InternedString &shaderName,
			ConstLightVisualiserPtr visualiser
		);

		/// Get all registered visualisations for the given attributes, by
		/// returning a map of renderable groups and some extra state. The
		/// return value may be left empty and/or the state may be left null if
		/// no registered visualisers do anything with these attributes.
		static Visualisations allVisualisations(
			const IECore::CompoundObject *attributes,
			IECoreGL::ConstStatePtr &state
		);

	protected :

		template<typename VisualiserType>
		struct LightVisualiserDescription
		{
			LightVisualiserDescription( const IECore::InternedString &attributeName, const IECore::InternedString &shaderName )
			{
				registerLightVisualiser( attributeName, shaderName, new VisualiserType() );
			};
		};

};

} // namespace IECoreGLPreview

#endif // IECOREGLPREVIEW_LIGHTVISUALISER_H
