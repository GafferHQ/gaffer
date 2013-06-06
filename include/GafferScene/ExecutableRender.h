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

#ifndef GAFFERSCENE_EXECUTABLERENDER_H
#define GAFFERSCENE_EXECUTABLERENDER_H

#include "Gaffer/Executable.h"

#include "GafferScene/Render.h"

namespace GafferScene
{

/// Base class for Executable nodes which perform a render of some sort
/// in the execute() method.
class ExecutableRender : public Render, public Gaffer::Executable
{

	public :

		ExecutableRender( const std::string &name=defaultName<ExecutableRender>() );
		virtual ~ExecutableRender();
		
		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::ExecutableRender, ExecutableRenderTypeId, Render );
		
		virtual void executionRequirements( const Gaffer::Context *context, Tasks &requirements ) const;
		virtual IECore::MurmurHash executionHash( const Gaffer::Context *context ) const;
		/// Implemented to perform the render.
		virtual void execute( const Contexts &contexts ) const;

	protected :
	
		/// Must be implemented by derived classes to return the renderer that will
		/// be used by execute.
		virtual IECore::RendererPtr createRenderer() const = 0;
		/// May be implemented by derived classes to change the way the procedural that
		/// generates the world is output. We need this method because Cortex has no mechanism for getting
		/// a delayed load procedural into a rib or ass file, and derived classes may want to be
		/// generating just such a file. The default implementation just outputs a SceneProcedural
		/// which is suitable for immediate mode rendering.
		virtual void outputWorldProcedural( const ScenePlug *scene, IECore::Renderer *renderer ) const;
		/// May be implemented to return a shell command which should be run after doing the "render".
		/// This can be useful for nodes which wish to render in two stages by creating a scene file
		/// with the createRenderer() and then rendering it with a command.
		virtual std::string command() const; 
};

IE_CORE_DECLAREPTR( ExecutableRender );

} // namespace GafferScene

#endif // GAFFERSCENE_EXECUTABLERENDER_H
