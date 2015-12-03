//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERRENDERMAN_RENDERMANLIGHT_H
#define GAFFERRENDERMAN_RENDERMANLIGHT_H

#include "GafferScene/Light.h"

#include "GafferRenderMan/TypeIds.h"

namespace GafferRenderMan
{

class RenderManLight : public GafferScene::Light
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferRenderMan::RenderManLight, RenderManLightTypeId, GafferScene::Light );

		RenderManLight( const std::string &name=defaultName<RenderManLight>() );
		virtual ~RenderManLight();

		void loadShader( const std::string &shaderName );

	protected :

		virtual void hashLight( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ObjectVectorPtr computeLight( const Gaffer::Context *context ) const;
		virtual IECore::InternedString lightAttribute() const;

	private :

		Gaffer::StringPlug *shaderNamePlug();
		const Gaffer::StringPlug *shaderNamePlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( RenderManLight )

} // namespace GafferRenderMan

#endif // GAFFERRENDERMAN_RENDERMANLIGHT_H
