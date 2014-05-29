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

#include "boost/python.hpp"

#include "Gaffer/Context.h"

#include "GafferBindings/ExecutableNodeBinding.h"

#include "GafferScene/OpenGLRender.h"
#include "GafferScene/InteractiveRender.h"

#include "GafferSceneBindings/RenderBinding.h"

using namespace boost::python;

using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;

class ExecutableRenderWrapper : public ExecutableNodeWrapper<ExecutableRender>
{

	public :
	
		ExecutableRenderWrapper( PyObject *self, const std::string &name )
			:	ExecutableNodeWrapper<ExecutableRender>( self, name )
		{
		}

		virtual IECore::RendererPtr createRenderer() const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "_createRenderer" );
				if( f )
				{
					return extract<IECore::RendererPtr>( f() );
				}
			}
			throw IECore::Exception( "No _createRenderer method defined in Python." );
		}
		
		virtual void outputWorldProcedural( const ScenePlug *scene, IECore::Renderer *renderer ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "_outputWorldProcedural" );
				if( f )
				{
					f( ScenePlugPtr( const_cast<ScenePlug *>( scene ) ), IECore::RendererPtr( renderer ) );
					return;
				}
			}
			return ExecutableRender::outputWorldProcedural( scene, renderer );
		}
		
		virtual std::string command() const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "_command" );
				if( f )
				{
					return extract<std::string>( f() );
				}
			}
			return ExecutableRender::command();
		}

};

IE_CORE_DECLAREPTR( ExecutableRenderWrapper )

static ContextPtr interactiveRenderGetContext( InteractiveRender &r )
{
	return r.getContext();
}

void GafferSceneBindings::bindRender()
{
	
	GafferBindings::ExecutableNodeClass<ExecutableRender, ExecutableRenderWrapperPtr>();
	
	GafferBindings::NodeClass<OpenGLRender>();
	
	scope s = GafferBindings::NodeClass<InteractiveRender>()
		.def( "getContext", &interactiveRenderGetContext )
		.def( "setContext", &InteractiveRender::setContext );
	
	enum_<InteractiveRender::State>( "State" )
		.value( "Stopped", InteractiveRender::Stopped )
		.value( "Running", InteractiveRender::Running )
		.value( "Paused", InteractiveRender::Paused )
	;
	
}
