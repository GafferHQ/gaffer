//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
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

#include "IECorePython/RefCountedBinding.h"

#include "GafferSceneUI/Visualiser.h"
#include "GafferSceneUIBindings/VisualiserBinding.h"

using namespace GafferSceneUI;

namespace {
	// TODO - An ugly hack I don't entirely understand in order to get the Python binding to work
	// To my understanding, there isn't really such a thing in Python as a const class,
	// so I think if you modify the result of visualise(), this will cause Bad Things to happen
	static IECoreGL::RenderablePtr visualise( const Visualiser &v, const IECore::Object *object )
	{
		return boost::const_pointer_cast<IECoreGL::Renderable>( v.visualise( object ) );
	}
}

void GafferSceneUIBindings::bindVisualiser()
{

	IECorePython::RefCountedClass<Visualiser, IECore::RefCounted>( "Visualiser" )
		.def( "visualise", &visualise )
		.def( "registerVisualiser", &Visualiser::registerVisualiser )
		.staticmethod( "registerVisualiser" )
		.def( "acquire", &Visualiser::acquire, boost::python::return_internal_reference<>() )
		.staticmethod( "acquire" )
	;

}
