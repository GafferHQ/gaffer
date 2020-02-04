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

#include "IECoreGLPreviewBinding.h"

#include "GafferScene/Private/IECoreGLPreview/Visualiser.h"
#include "GafferScene/Private/IECoreGLPreview/ObjectVisualiser.h"
#include "GafferScene/Private/IECoreGLPreview/AttributeVisualiser.h"
#include "GafferScene/Private/IECoreGLPreview/LightVisualiser.h"

#include "IECorePython/RefCountedBinding.h"

using namespace IECoreGLPreview;
using namespace boost::python;

void GafferSceneModule::bindIECoreGLPreview()
{
	object module( borrowed( PyImport_AddModule( "GafferScene.IECoreScenePreview" ) ) );
	scope().attr( "IECoreScenePreview" ) = module;
	scope moduleScope( module );

	IECorePython::RefCountedClass<ObjectVisualiser, IECore::RefCounted>( "ObjectVisualiser" )
		.def( "registerVisualiser", &ObjectVisualiser::registerVisualiser )
		.staticmethod( "registerVisualiser" )
	;

	IECorePython::RefCountedClass<AttributeVisualiser, IECore::RefCounted>( "AttributeVisualiser" )
		.def( "registerVisualiser", &AttributeVisualiser::registerVisualiser )
		.staticmethod( "registerVisualiser" )
		.def( "allVisualisations", &AttributeVisualiser::allVisualisations )
		.staticmethod( "allVisualisations" )
	;

	IECorePython::RefCountedClass<LightVisualiser, IECore::RefCounted>( "LightVisualiser" )
		.def( "registerLightVisualiser", &LightVisualiser::registerLightVisualiser )
		.staticmethod( "registerLightVisualiser" )
	;

	auto v = class_<Visualisation>( "Visualisation", no_init );
	{
		scope visualisationScope( v );

		enum_<Visualisation::Scale>("Scale")
			.value( "None", Visualisation::Scale::None )
			.value( "Local", Visualisation::Scale::Local )
			.value( "Visualiser", Visualisation::Scale::Visualiser )
			.value( "LocalAndVisualiser", Visualisation::Scale::LocalAndVisualiser )
		;
		enum_<Visualisation::Category>("Category")
			.value( "Generic", Visualisation::Category::Generic )
			.value( "Frustum", Visualisation::Category::Frustum )
		;
	}
	v.def( init<
				IECoreGL::ConstRenderablePtr,
				Visualisation::Scale,
				Visualisation::Category,
				bool
			>(
				(
					arg( "renderable" ),
					arg( "scale" ) = Visualisation::Scale::Local,
					arg( "category" ) = Visualisation::Category::Generic,
					arg( "affectsFramingBound" ) = true
				)
			)
		)
		.def_readwrite( "scale", &Visualisation::scale )
		.def_readwrite( "category", &Visualisation::category )
		.def_readwrite( "affectsFramingBound", &Visualisation::affectsFramingBound )
		.def( "renderable", &Visualisation::renderable, return_value_policy<IECorePython::CastToIntrusivePtr>() )
		.def( "createGeometry", &Visualisation::createGeometry )
		.staticmethod( "createGeometry" )
		.def( "createOrnament", &Visualisation::createOrnament )
		.staticmethod( "createOrnament" )
		.def( "createFrustum", &Visualisation::createFrustum )
		.staticmethod( "createFrustum" )
	;
}
