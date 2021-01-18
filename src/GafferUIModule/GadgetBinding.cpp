//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "GadgetBinding.h"

#include "GafferUIBindings/GadgetBinding.h"

#include "GafferUI/Gadget.h"
#include "GafferUI/Style.h"

#include "GafferBindings/SignalBinding.h"

#include "IECorePython/ExceptionAlgo.h"

using namespace boost::python;
using namespace GafferUIBindings;
using namespace GafferBindings;
using namespace GafferUI;

namespace
{

struct RenderRequestSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, GadgetPtr g )
	{
		slot( g );
		return boost::signals::detail::unusable();
	}
};

struct ButtonSlotCaller
{
	bool operator()( boost::python::object slot, GadgetPtr g, const ButtonEvent &event )
	{
		try
		{
			return boost::python::extract<bool>( slot( g, event ) )();
		}
		catch( const boost::python::error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // also clears the python error status
			return false;
		}
	}
};

struct EnterLeaveSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, GadgetPtr g, const ButtonEvent &event )
	{
		try
		{
			slot( g, event );
			return boost::signals::detail::unusable();
		}
		catch( const boost::python::error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // also clears the python error status
			return boost::signals::detail::unusable();
		}
	}
};

struct DragBeginSlotCaller
{
	IECore::RunTimeTypedPtr operator()( boost::python::object slot, GadgetPtr g, const DragDropEvent &event )
	{
		try
		{
			return boost::python::extract<IECore::RunTimeTypedPtr>( slot( g, event ) )();
		}
		catch( const boost::python::error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // also clears the python error status
			return nullptr;
		}
	}
};

struct DragDropSlotCaller
{
	bool operator()( boost::python::object slot, GadgetPtr g, const DragDropEvent &event )
	{
		try
		{
			return boost::python::extract<bool>( slot( g, event ) )();
		}
		catch( const boost::python::error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // also clears the python error status
			return false;
		}
	}
};

struct KeySlotCaller
{
	bool operator()( boost::python::object slot, GadgetPtr g, const KeyEvent &event )
	{
		try
		{
			return boost::python::extract<bool>( slot( g, event ) )();
		}
		catch( const boost::python::error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // also clears the python error status
			return false;
		}
	}
};

StylePtr getStyle( Gadget &g )
{
	return const_cast<Style *>( g.getStyle() );
}

StylePtr style( Gadget &g )
{
	return const_cast<Style *>( g.style() );
}

void setVisible( Gadget &g, bool visible )
{
	IECorePython::ScopedGILRelease gilRelease;
	g.setVisible( visible );
}

void setEnabled( Gadget &g, bool enabled )
{
	IECorePython::ScopedGILRelease gilRelease;
	g.setEnabled( enabled );
}

void render( const Gadget &g )
{
	IECorePython::ScopedGILRelease gilRelease;
	g.render();
}

BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS( fullTransformOverloads, fullTransform, 0, 1 );

} // namespace

void GafferUIModule::bindGadget()
{
	typedef GadgetWrapper<Gadget> Wrapper;

	scope s = GadgetClass<Gadget, Wrapper>()
		.def( init<>() )
		.def( init<const std::string &>() )
		.def( "setStyle", &Gadget::setStyle )
		.def( "getStyle", &getStyle )
		.def( "style", &style )
		.def( "setVisible", &setVisible )
		.def( "getVisible", &Gadget::getVisible )
		.def( "visible", &Gadget::visible, ( arg_( "relativeTo" ) = object() ) )
		.def( "visibilityChangedSignal", &Gadget::visibilityChangedSignal, return_internal_reference<1>() )
		.def( "setEnabled", &setEnabled )
		.def( "getEnabled", &Gadget::getEnabled )
		.def( "enabled", &Gadget::enabled, ( arg_( "relativeTo" ) = object() ) )
		.def( "getHighlighted", &Gadget::getHighlighted )
		.def( "getTransform", &Gadget::getTransform, return_value_policy<copy_const_reference>() )
		.def( "setTransform", &Gadget::setTransform )
		.def( "fullTransform", &Gadget::fullTransform, fullTransformOverloads() )
		.def( "transformedBound", (Imath::Box3f (Gadget::*)() const)&Gadget::transformedBound )
		.def( "transformedBound", (Imath::Box3f (Gadget::*)( const Gadget * ) const)&Gadget::transformedBound )
		.def( "render", &render )
		.def( "renderRequestSignal", &Gadget::renderRequestSignal, return_internal_reference<1>() )
		.def( "setToolTip", &Gadget::setToolTip )
		.def( "buttonPressSignal", &Gadget::buttonPressSignal, return_internal_reference<1>() )
		.def( "buttonReleaseSignal", &Gadget::buttonReleaseSignal, return_internal_reference<1>() )
		.def( "buttonDoubleClickSignal", &Gadget::buttonDoubleClickSignal, return_internal_reference<1>() )
		.def( "wheelSignal", &Gadget::wheelSignal, return_internal_reference<1>() )
		.def( "enterSignal", &Gadget::enterSignal, return_internal_reference<1>() )
		.def( "leaveSignal", &Gadget::leaveSignal, return_internal_reference<1>() )
		.def( "mouseMoveSignal", &Gadget::mouseMoveSignal, return_internal_reference<1>() )
		.def( "dragBeginSignal", &Gadget::dragBeginSignal, return_internal_reference<1>() )
		.def( "dragMoveSignal", &Gadget::dragMoveSignal, return_internal_reference<1>() )
		.def( "dragEnterSignal", &Gadget::dragEnterSignal, return_internal_reference<1>() )
		.def( "dragLeaveSignal", &Gadget::dragLeaveSignal, return_internal_reference<1>() )
		.def( "dropSignal", &Gadget::dropSignal, return_internal_reference<1>() )
		.def( "dragEndSignal", &Gadget::dragEndSignal, return_internal_reference<1>() )
		.def( "keyPressSignal", &Gadget::keyPressSignal, return_internal_reference<1>() )
		.def( "keyReleaseSignal", &Gadget::keyReleaseSignal, return_internal_reference<1>() )
		.def( "idleSignal", &Gadget::idleSignal, return_value_policy<reference_existing_object>() )
		.staticmethod( "idleSignal" )
		.def( "_idleSignalAccessedSignal", &Gadget::idleSignalAccessedSignal, return_value_policy<reference_existing_object>() )
		.staticmethod( "_idleSignalAccessedSignal" )
		.def( "_dirty", &Gadget::dirty )
		.def( "_requestRender", &Gadget::requestRender )
		.def( "select", &Gadget::select ).staticmethod( "select" )
	;

	enum_<Gadget::Layer>( "Layer" )
		.value( "Back", Gadget::Layer::Back )
		.value( "OverBack", Gadget::Layer::OverBack )
		.value( "MidBack", Gadget::Layer::MidBack )
		.value( "Main", Gadget::Layer::Main )
		.value( "MidFront", Gadget::Layer::MidFront )
		.value( "Front", Gadget::Layer::Front )
	;

	enum_<Gadget::DirtyType>( "DirtyType" )
		.value( "Render", Gadget::DirtyType::Render )
		.value( "Bound", Gadget::DirtyType::Bound )
		.value( "Layout", Gadget::DirtyType::Layout )
	;

	SignalClass<Gadget::RenderRequestSignal, DefaultSignalCaller<Gadget::RenderRequestSignal>, RenderRequestSlotCaller>( "RenderRequestSignal" );
	SignalClass<Gadget::ButtonSignal, DefaultSignalCaller<Gadget::ButtonSignal>, ButtonSlotCaller>( "ButtonSignal" );
	SignalClass<Gadget::KeySignal, DefaultSignalCaller<Gadget::KeySignal>, KeySlotCaller>( "KeySignal" );
	SignalClass<Gadget::DragBeginSignal, DefaultSignalCaller<Gadget::DragBeginSignal>, DragBeginSlotCaller>( "DragBeginSignal" );
	SignalClass<Gadget::DragDropSignal, DefaultSignalCaller<Gadget::DragDropSignal>, DragDropSlotCaller>( "DragDropSignal" );
	SignalClass<Gadget::EnterLeaveSignal, DefaultSignalCaller<Gadget::EnterLeaveSignal>, EnterLeaveSlotCaller>( "EnterLeaveSignal" );
	SignalClass<Gadget::IdleSignal>( "IdleSignal" );

}
