//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
#include "boost/python/tuple.hpp"


#include "SceneGadgetBinding.h"

#include "GafferSceneUI/SceneGadget.h"

#include "GafferUIBindings/GadgetBinding.h"

#include "GafferBindings/SignalBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI;
using namespace GafferBindings;

namespace
{

void setScene( SceneGadget &g, ScenePlug &scene )
{
	ScopedGILRelease gilRelease;
	g.setScene( &scene );
}

GafferScene::ScenePlugPtr getScene( SceneGadget &g )
{
	return const_cast<GafferScene::ScenePlug *>( g.getScene() );
}

void setContext( SceneGadget &g, Context &context )
{
	ScopedGILRelease gilRelease;
	g.setContext( &context );
}

void setVisibleSet( SceneGadget &g, const GafferScene::VisibleSet &visibleSet )
{
	ScopedGILRelease gilRelease;
	g.setVisibleSet( visibleSet );
}

void setMinimumExpansionDepth( SceneGadget &g, size_t depth )
{
	ScopedGILRelease gilRelease;
	g.setMinimumExpansionDepth( depth );
}

void setPaused( SceneGadget &g, bool paused )
{
	ScopedGILRelease gilRelease;
	g.setPaused( paused );
}

void waitForCompletion( SceneGadget &g )
{
	ScopedGILRelease gilRelease;
	g.waitForCompletion();
}

struct SceneGadgetSlotCaller
{
	void operator()( boost::python::object slot, SceneGadgetPtr g )
	{
		try
		{
			slot( g );
		}
		catch( const error_already_set &e )
		{
			ExceptionAlgo::translatePythonException();
		}
	}
};

void setRenderer( SceneGadget &g, IECore::InternedString name )
{
	ScopedGILRelease gilRelease;
	g.setRenderer( name );
}

std::string getRenderer( SceneGadget &g )
{
	return g.getRenderer().string();
}

IECore::CompoundObjectPtr getOpenGLOptions( const SceneGadget &g )
{
	return g.getOpenGLOptions()->copy();
}

IECore::StringVectorDataPtr getSelectionMask( const SceneGadget &g )
{
	const IECore::StringVectorData *d = g.getSelectionMask();
	return d ? d->copy() : nullptr;
}

IECore::InternedStringVectorDataPtr objectAt( SceneGadget &g, IECore::LineSegment3f &l )
{
	ScopedGILRelease gilRelease;
	IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData;
	if( g.objectAt( l, result->writable() ) )
	{
		return result;
	}
	return nullptr;
}

tuple objectAndIntersectionAt( SceneGadget &g, IECore::LineSegment3f &l )
{
	IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData;
	Imath::V3f hitPos( 0.0f );

	{
		ScopedGILRelease gilRelease;
		if( !g.objectAt( l, result->writable(), hitPos ) )
		{
			result = nullptr;
		}
	}

	return boost::python::make_tuple( result, hitPos );
}

size_t objectsAt( SceneGadget &g, const Imath::V3f &corner0InGadgetSpace, const Imath::V3f &corner1InGadgetSpace, IECore::PathMatcher &paths )
{
	ScopedGILRelease gilRelease;
	return g.objectsAt( corner0InGadgetSpace, corner1InGadgetSpace, paths );
}

Imath::Box3f selectionBound( SceneGadget &g )
{
	ScopedGILRelease gilRelease;
	return g.selectionBound();
}

Imath::Box3f bound( SceneGadget &g, bool selected, const IECore::PathMatcher *omitted )
{
	ScopedGILRelease gilRelease;
	return g.bound( selected, omitted );
}

} // namespace

void GafferSceneUIModule::bindSceneGadget()
{

	scope s = GafferUIBindings::GadgetClass<SceneGadget>()
		.def( init<>() )
		.def( "setScene", &setScene )
		.def( "getScene", &getScene )
		.def( "setContext", &setContext )
		.def( "getContext", (Gaffer::Context *(SceneGadget::*)())&SceneGadget::getContext, return_value_policy<CastToIntrusivePtr>() )
		.def( "setVisibleSet", &setVisibleSet )
		.def( "getVisibleSet", &SceneGadget::getVisibleSet, return_value_policy<copy_const_reference>() )
		.def( "setMinimumExpansionDepth", &setMinimumExpansionDepth )
		.def( "getMinimumExpansionDepth", &SceneGadget::getMinimumExpansionDepth )
		.def( "getPaused", &SceneGadget::getPaused )
		.def( "setPaused", &setPaused )
		.def( "state", &SceneGadget::state )
		.def( "stateChangedSignal", &SceneGadget::stateChangedSignal, return_internal_reference<1>() )
		.def( "waitForCompletion", &waitForCompletion )
		.def( "setRenderer", &setRenderer )
		.def( "getRenderer", &getRenderer )
		.def( "setOpenGLOptions", &SceneGadget::setOpenGLOptions )
		.def( "getOpenGLOptions", &getOpenGLOptions )
		.def( "setLayer", &SceneGadget::setLayer )
		.def( "getLayer", &SceneGadget::getLayer )
		.def( "setSelectionMask", &SceneGadget::setSelectionMask )
		.def( "getSelectionMask", &getSelectionMask )
		.def( "objectAt", &objectAt )
		.def( "objectAndIntersectionAt", &objectAndIntersectionAt )
		.def( "objectsAt", &objectsAt )
		.def( "setSelection", &SceneGadget::setSelection )
		.def( "getSelection", &SceneGadget::getSelection, return_value_policy<copy_const_reference>() )
		.def( "selectionBound", &selectionBound )
		.def( "bound", &bound, ( arg( "selected" ), arg( "omitted" ) = object() ) )
	;

	enum_<SceneGadget::State>( "State" )
		.value( "Paused", SceneGadget::Paused )
		.value( "Running", SceneGadget::Running )
		.value( "Complete", SceneGadget::Complete )
	;

	SignalClass<SceneGadget::SceneGadgetSignal, DefaultSignalCaller<SceneGadget::SceneGadgetSignal>, SceneGadgetSlotCaller>( "ImageGadgetSignal" );


}
