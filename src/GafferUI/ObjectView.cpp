//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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

#include "boost/bind.hpp"

#include "IECore/NullObject.h"

#include "IECoreGL/State.h"

#include "Gaffer/Context.h"

#include "GafferUI/ObjectView.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

IE_CORE_DEFINERUNTIMETYPED( ObjectView );

ObjectView::ViewDescription<ObjectView> ObjectView::g_viewDescription( ObjectPlug::staticTypeId() );

ObjectView::ObjectView( const std::string &name )
	:	View3D( name, new ObjectPlug( "in", Plug::In, NullObject::defaultNullObject() ) ),
		m_renderableGadget( new RenderableGadget )
{
	viewportGadget()->setChild( m_renderableGadget );

	baseStateChangedSignal().connect( boost::bind( &ObjectView::baseStateChanged, this ) );
}

void ObjectView::update()
{
	ConstVisibleRenderablePtr renderable = 0;
	{
		Context::Scope context( getContext() );
		renderable = runTimeCast<const VisibleRenderable>( View3D::preprocessedInPlug<ObjectPlug>()->getValue() );
	}

	bool hadRenderable = m_renderableGadget->getRenderable();
	m_renderableGadget->setRenderable( renderable );
	if( !hadRenderable && renderable )
	{
		viewportGadget()->frame( m_renderableGadget->bound() );
	}
}

void ObjectView::baseStateChanged()
{
	m_renderableGadget->baseState()->add( const_cast<IECoreGL::State *>( baseState() ) );
	m_renderableGadget->renderRequestSignal()( m_renderableGadget );
}
