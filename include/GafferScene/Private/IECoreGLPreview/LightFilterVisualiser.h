//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine. All rights reserved.
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

#ifndef IECOREGLPREVIEW_LIGHTFILTERVISUALISER_H
#define IECOREGLPREVIEW_LIGHTFILTERVISUALISER_H

#include "GafferScene/Export.h"

#include "GafferScene/Private/IECoreGLPreview/Visualiser.h"

#include "IECoreGL/Renderable.h"

#include "IECoreScene/ShaderNetwork.h"

#include "IECore/CompoundObject.h"

namespace IECoreGLPreview
{

IE_CORE_FORWARDDECLARE( LightFilterVisualiser )

/// Class for visualisation of light filters. All light filters in Gaffer are represented
/// as IECore::Shader objects, but we need to visualise them differently
/// depending on their shader name (accessed using `IECore::Shader::getName()`). A
/// factory mechanism is provided to map from this name to a specialised
/// LightFilterVisualiser.
class GAFFERSCENE_API LightFilterVisualiser : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( LightFilterVisualiser )

		LightFilterVisualiser();
		~LightFilterVisualiser() override;

		/// Must be implemented by derived classes to visualise
		/// the light filter contained within `filterShaderNetwork`.
		virtual Visualisations visualise(
			const IECore::InternedString &attributeName,
			const IECoreScene::ShaderNetwork *filterShaderNetwork,
			const IECoreScene::ShaderNetwork *lightShaderNetwork,
			const IECore::CompoundObject *attributes,
			IECoreGL::ConstStatePtr &state
		) const = 0;

		/// Registers a visualiser to visualise a particular type of light filter.
		/// For instance, `registerLightFilterVisualiser( "ai:lightFilter", "gobo", visualiser )`
		/// would register a visualiser for an Arnold gobo light filter.
		static void registerLightFilterVisualiser(
			const IECore::InternedString &attributeName,
			const IECore::InternedString &shaderName,
			ConstLightFilterVisualiserPtr visualiser
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

		template<typename FilterVisualiserType>
		struct LightFilterVisualiserDescription
		{
			LightFilterVisualiserDescription( const IECore::InternedString &attributeName, const IECore::InternedString &shaderName )
			{
				registerLightFilterVisualiser( attributeName, shaderName, new FilterVisualiserType() );
			}
		};
};

} // namespace IECoreGLPreview

#endif // IECOREGLPREVIEW_LIGHTFILTERVISUALISER_H
