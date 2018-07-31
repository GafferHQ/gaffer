//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "ViewportGadgetBinding.h"

#include "GafferUIBindings/GadgetBinding.h"

#include "GafferUI/ViewportGadget.h"

#include "GafferBindings/SignalBinding.h"

#include "IECorePython/RunTimeTypedBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace GafferUI;
using namespace GafferUIBindings;

namespace
{

GadgetPtr getPrimaryChild( ViewportGadget &v )
{
	return v.getPrimaryChild();
}

IECoreScene::CameraPtr getCamera( const ViewportGadget &v )
{
	return v.getCamera()->copy();
}

list gadgetsAt( ViewportGadget &v, const Imath::V2f &position )
{
	std::vector<GadgetPtr> gadgets;
	v.gadgetsAt( position, gadgets );

	boost::python::list result;
	for( std::vector<GadgetPtr>::const_iterator it=gadgets.begin(); it!=gadgets.end(); it++ )
	{
		result.append( *it );
	}
	return result;
}

struct UnarySlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, ViewportGadgetPtr g )
	{
		try
		{
			slot( g );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return boost::signals::detail::unusable();
	}
};

void render( const ViewportGadget &v )
{
	IECorePython::ScopedGILRelease gilRelease;
	v.render();
}

BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS( frameOverloads, frame, 2, 3 );

} // namespace

void GafferUIModule::bindViewportGadget()
{
	scope s = GadgetClass<ViewportGadget>()
		.def( init<>() )
		.def( init<GadgetPtr>() )
		.def( "setPrimaryChild", &ViewportGadget::setPrimaryChild )
		.def( "getPrimaryChild", &getPrimaryChild )
		.def( "getViewport", &ViewportGadget::getViewport, return_value_policy<copy_const_reference>() )
		.def( "setViewport", &ViewportGadget::setViewport )
		.def( "viewportChangedSignal", &ViewportGadget::viewportChangedSignal, return_internal_reference<1>() )
		.def( "getCamera", &getCamera )
		.def( "setCamera", &ViewportGadget::setCamera )
		.def( "getCameraTransform", &ViewportGadget::getCameraTransform, return_value_policy<copy_const_reference>() )
		.def( "setCameraTransform", &ViewportGadget::setCameraTransform )
		.def( "cameraChangedSignal", &ViewportGadget::cameraChangedSignal, return_internal_reference<1>() )
		.def( "getCameraEditable", &ViewportGadget::getCameraEditable )
		.def( "setCameraEditable", &ViewportGadget::setCameraEditable )
		.def( "setCenterOfInterest", &ViewportGadget::setCenterOfInterest )
		.def( "getCenterOfInterest", &ViewportGadget::getCenterOfInterest )
		.def( "setOrthographic3D", &ViewportGadget::setOrthographic3D )
		.def( "getOrthographic3D", &ViewportGadget::getOrthographic3D )
		.def( "frame", (void (ViewportGadget::*)( const Imath::Box3f & ))&ViewportGadget::frame )
		.def( "frame", (void (ViewportGadget::*)( const Imath::Box3f &, const Imath::V3f &, const Imath::V3f & ))&ViewportGadget::frame, frameOverloads() )
		.def( "fitClippingPlanes", &ViewportGadget::fitClippingPlanes )
		.def( "setDragTracking", &ViewportGadget::setDragTracking )
		.def( "getDragTracking", &ViewportGadget::getDragTracking )
		.def( "setVariableAspectZoom", &ViewportGadget::setVariableAspectZoom )
		.def( "getVariableAspectZoom", &ViewportGadget::getVariableAspectZoom )
		.def( "gadgetsAt", &gadgetsAt )
		.def( "rasterToGadgetSpace", &ViewportGadget::rasterToGadgetSpace, ( arg_( "rasterPosition" ), arg_( "gadget" ) ) )
		.def( "gadgetToRasterSpace", &ViewportGadget::gadgetToRasterSpace, ( arg_( "gadgetPosition" ), arg_( "gadget" ) ) )
		.def( "rasterToWorldSpace", &ViewportGadget::rasterToWorldSpace, ( arg_( "rasterPosition" ) ) )
		.def( "worldToRasterSpace", &ViewportGadget::worldToRasterSpace, ( arg_( "worldPosition" ) ) )
		.def( "render", &render )
		.def( "preRenderSignal", &ViewportGadget::preRenderSignal, return_internal_reference<1>() )
	;

	SignalClass<ViewportGadget::UnarySignal, DefaultSignalCaller<ViewportGadget::UnarySignal>, UnarySlotCaller>( "UnarySignal" );

}
