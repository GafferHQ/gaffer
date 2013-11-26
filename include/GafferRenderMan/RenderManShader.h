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

#ifndef GAFFERRENDERMAN_RENDERMANSHADER_H
#define GAFFERRENDERMAN_RENDERMANSHADER_H

#include "IECore/CachedReader.h"

#include "GafferScene/Shader.h"

#include "GafferRenderMan/TypeIds.h"

namespace GafferRenderMan
{

class RenderManLight;

class RenderManShader : public GafferScene::Shader
{

	public :

		RenderManShader( const std::string &name=defaultName<RenderManShader>() );
		virtual ~RenderManShader();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferRenderMan::RenderManShader, RenderManShaderTypeId, GafferScene::Shader );
			
		/// Implemented for outPlug(), returning the parameter named in the "primaryInput"
		/// shader annotation if it has been specified.
		virtual Gaffer::Plug *correspondingInput( const Gaffer::Plug *output );
		virtual const Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) const;

		/// \undoable.
		/// \todo Make this method virtual and define it on the Shader base class.
		void loadShader( const std::string &shaderName, bool keepExistingValues=false );

		/// The loader used by loadShader() - this is exposed so that the ui
		/// can use it too.
		static IECore::CachedReader *shaderLoader();

	protected :
	
		virtual bool acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const;

		virtual void parameterHash( const Gaffer::Plug *parameterPlug, NetworkBuilder &network, IECore::MurmurHash &h ) const;
		virtual IECore::DataPtr parameterValue( const Gaffer::Plug *parameterPlug, NetworkBuilder &network ) const;

		const IECore::ConstCompoundDataPtr annotations() const;
	
	private :
	
		// RenderMan light is a friend to allow it to share the shader loading code.
		/// \todo Perhaps some other code sharing mechanism makes more sense?
		friend class RenderManLight;
		
		static void loadShaderParameters( const IECore::Shader *shader, Gaffer::CompoundPlug *parametersPlug, bool keepExistingValues=false );
					
};

IE_CORE_DECLAREPTR( RenderManShader )

} // namespace GafferRenderMan

#endif // GAFFERRENDERMAN_RENDERMANSHADER_H
