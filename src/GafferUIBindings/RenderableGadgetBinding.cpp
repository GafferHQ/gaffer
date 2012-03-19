//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

#include "IECoreGL/State.h"

#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/ScopedGILRelease.h"

#include "GafferUIBindings/RenderableGadgetBinding.h"
#include "GafferUIBindings/GadgetBinding.h"
#include "GafferUI/RenderableGadget.h"

using namespace boost::python;
using namespace GafferUIBindings;
using namespace GafferUI;

static IECoreGL::StatePtr baseState( RenderableGadget &g )
{
	return g.baseState();
}

static RenderableGadgetPtr construct( IECore::VisibleRenderablePtr renderable )
{
	// we must release the GIL because the renderable might include a python procedural
	// which might get invoked on a separate thread by the renderer that VisibleRenderable
	// uses internally.
	IECorePython::ScopedGILRelease gilRelease;
	return new RenderableGadget( renderable );
}

static void setRenderable( RenderableGadget &g, IECore::VisibleRenderablePtr renderable )
{
	// we must release the GIL because the renderable might include a python procedural
	// which might get invoked on a separate thread by the renderer that VisibleRenderable
	// uses internally.
	IECorePython::ScopedGILRelease gilRelease;
	g.setRenderable( renderable );
}

void GafferUIBindings::bindRenderableGadget()
{
	IECorePython::RunTimeTypedClass<RenderableGadget>()
		.GAFFERUIBINDINGS_DEFGADGETWRAPPERFNS( RenderableGadget )
		.def( "__init__", make_constructor( construct, default_call_policies(), ( boost::python::arg( "renderable" ) = IECore::VisibleRenderablePtr() ) ) )
		.def( "setRenderable", &setRenderable )
		.def( "getRenderable", (IECore::VisibleRenderablePtr (RenderableGadget::*)())&RenderableGadget::getRenderable )
		.def( "baseState", &baseState )
	;

}
