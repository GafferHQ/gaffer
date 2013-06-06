//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENE_SHADER_H
#define GAFFERSCENE_SHADER_H

#include "IECore/ObjectVector.h"
#include "IECore/Shader.h"

#include "Gaffer/DependencyNode.h"
#include "Gaffer/CompoundPlug.h"
#include "Gaffer/TypedPlug.h"

#include "GafferScene/TypeIds.h"

namespace GafferScene
{

class Shader : public Gaffer::DependencyNode
{

	public :

		Shader( const std::string &name=defaultName<Shader>() );
		virtual ~Shader();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::Shader, ShaderTypeId, Gaffer::DependencyNode );
		
		/// A plug defining the name of the shader.
		Gaffer::StringPlug *namePlug();
		const Gaffer::StringPlug *namePlug() const;
		
		/// A plug defining the type of the shader.
		Gaffer::StringPlug *typePlug();
		const Gaffer::StringPlug *typePlug() const;
		
		/// Plug under which the shader parameters are defined.
		Gaffer::CompoundPlug *parametersPlug();
		const Gaffer::CompoundPlug *parametersPlug() const;
		
		/// Plug which defines the shader's output - this should
		/// be connected to a ShaderAssignment::shaderPlug() or
		/// in the case of shaders which support networking it may
		/// be connected to a parameter plug of another shader.
		Gaffer::Plug *outPlug();
		const Gaffer::Plug *outPlug() const;
		
		/// Implemented so that the children of parametersPlug() affect
		/// outPlug().
		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;
		
		IECore::MurmurHash stateHash() const;
		void stateHash( IECore::MurmurHash &h ) const;
		/// Returns a series of IECore::StateRenderables suitable for specifying this
		/// shader (and it's inputs) to an IECore::Renderer.
		IECore::ObjectVectorPtr state() const;
			
	protected :
		
		class NetworkBuilder
		{
		
			public :
			
				IECore::Shader *shader( const Shader *shaderNode );
				const std::string &shaderHandle( const Shader *shaderNode ); 
			
			private :
				
				NetworkBuilder();
				
				IECore::ObjectVectorPtr m_state;
				typedef std::map<const Shader *, IECore::Shader *> ShaderMap;
				ShaderMap m_shaders;
		
				friend class Shader;
				
		};
		
		virtual void shaderHash( IECore::MurmurHash &h ) const;
		/// \todo Try to implement this here in a way that can be shared by
		/// the derived classes.
		virtual IECore::ShaderPtr shader( NetworkBuilder &network ) const = 0;	

	private :
	
		static size_t g_firstPlugIndex;
		
};

} // namespace GafferScene

#endif // GAFFERSCENE_SHADER_H
