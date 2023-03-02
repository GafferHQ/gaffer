//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine. All rights reserved.
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

#include "GafferScene/Private/IECoreGLPreview/Visualiser.h"

#include "IECoreGL/Renderable.h"

#include "IECore/CompoundObject.h"

namespace IECoreGLPreview
{

IE_CORE_FORWARDDECLARE( AttributeVisualiser )

class GAFFERSCENE_API AttributeVisualiser : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( AttributeVisualiser )
		~AttributeVisualiser() override;

		virtual Visualisations visualise(
			const IECore::CompoundObject *attributes,
			IECoreGL::ConstStatePtr &state
		) const = 0;

		/// Registers an attribute visualiser
		static void registerVisualiser( ConstAttributeVisualiserPtr visualiser );

		/// Get all registered visualisations for the given attributes, by
		/// returning a map of renderable groups and some extra state. The
		/// return value may be left empty and/or the state may left null if no
		/// registered visualisers do anything with these attributes.
		static Visualisations allVisualisations(
			const IECore::CompoundObject *attributes,
			IECoreGL::ConstStatePtr &state
		);

	protected :

		AttributeVisualiser();

		template<typename VisualiserType>
		struct AttributeVisualiserDescription
		{

			AttributeVisualiserDescription()
			{
				registerVisualiser( new VisualiserType );
			}

		};
};

IE_CORE_DECLAREPTR( AttributeVisualiser )

} // namespace IECoreGLPreview
