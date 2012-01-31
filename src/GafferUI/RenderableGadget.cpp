//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#include "IECore/SimpleTypedData.h"
#include "IECore/WorldBlock.h"

#include "IECoreGL/Renderer.h"
#include "IECoreGL/Scene.h"
#include "IECoreGL/Camera.h"
#include "IECoreGL/State.h"

#include "GafferUI/RenderableGadget.h"

using namespace GafferUI;
using namespace Imath;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( RenderableGadget );

RenderableGadget::RenderableGadget( IECore::VisibleRenderablePtr renderable )
	:	Gadget( staticTypeName() ), m_renderable( 0 ), m_scene( 0 ), m_baseState( new IECoreGL::State( true ) )
{
	setRenderable( renderable );
}

RenderableGadget::~RenderableGadget()
{
}

Imath::Box3f RenderableGadget::bound() const
{
	if( m_renderable )
	{
		return m_renderable->bound();
	}
	else
	{
		return Imath::Box3f();
	}
}

void RenderableGadget::doRender( const Style *style ) const
{
	if( m_scene )
	{
		m_scene->render( m_baseState );
	}
}

void RenderableGadget::setRenderable( IECore::VisibleRenderablePtr renderable )
{
	if( renderable!=m_renderable )
	{
		m_renderable = renderable;
		m_scene = 0;
		if( m_renderable )
		{
			IECoreGL::RendererPtr renderer = new IECoreGL::Renderer;
			renderer->setOption( "gl:mode", new IECore::StringData( "deferred" ) );
			{
				IECore::WorldBlock world( renderer );
				m_renderable->render( renderer );
			}	
			m_scene = renderer->scene();
			m_scene->setCamera( 0 );	
		}
		renderRequestSignal()( this );
	}
}

IECore::VisibleRenderablePtr RenderableGadget::getRenderable()
{
	return m_renderable;
}

IECore::ConstVisibleRenderablePtr RenderableGadget::getRenderable() const
{
	return m_renderable;
}

IECoreGL::State *RenderableGadget::baseState()
{
	return m_baseState.get();
}