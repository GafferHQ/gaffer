//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFEROSL_OSLCODE_H
#define GAFFEROSL_OSLCODE_H

#include "GafferOSL/OSLShader.h"

namespace GafferOSL
{

/// \todo It would be better if this node generated the .oso file
/// on disk on demand, during shader network generation. Rejig the
/// generation process to allow for this. Also bear in mind the related
/// todo items in ArnoldDisplacement and ArnoldLight.
class GAFFEROSL_API OSLCode : public OSLShader
{

	public :

		OSLCode( const std::string &name=defaultName<OSLCode>() );
		~OSLCode() override;

		GAFFER_NODE_DECLARE_TYPE( GafferOSL::OSLCode, OSLCodeTypeId, OSLShader );

		Gaffer::StringPlug *codePlug();
		const Gaffer::StringPlug *codePlug() const;

		/// Returns the source to a complete OSL shader created
		/// from this node, optionally specifying a specific name
		/// to give to it.
		std::string source( const std::string shaderName = "" ) const;

		using ShaderCompiledSignal = Gaffer::Signals::Signal<void ()>;
		/// Signal emitted when a shader is compiled successfully.
		/// \todo This exists only so the UI knows when to clear
		/// the error indicator. When we compile shaders on demand,
		/// we can instead use the same `errorSignal()`/`plugDirtiedSignal()`
		/// combo we use everywhere else.
		ShaderCompiledSignal &shaderCompiledSignal();

		// This is implemented to do nothing, because OSLCode node generates the shader from
		// the plugs, and not the other way around.  We don't want to inherit the loading behaviour
		// from OSLShader which tries to match the plugs to a shader on disk
		void loadShader( const std::string &shaderName, bool keepExistingValues=false ) override;

	private :

		void updateShader();
		void plugSet( const Gaffer::Plug *plug );
		void parameterAdded( const Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child );
		void parameterRemoved( const Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child );
		void parameterNameChanged();

		static size_t g_firstPlugIndex;

		ShaderCompiledSignal m_shaderCompiledSignal;
		std::unordered_map<const Gaffer::GraphComponent *, Gaffer::Signals::ScopedConnection> m_nameChangedConnections;

};

IE_CORE_DECLAREPTR( OSLCode )

} // namespace GafferOSL

#endif // GAFFEROSL_OSLCODE_H
