//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "PrimitivesBinding.h"

#include "GafferScene/Camera.h"
#include "GafferScene/ClippingPlane.h"
#include "GafferScene/CoordinateSystem.h"
#include "GafferScene/Cube.h"
#include "GafferScene/ExternalProcedural.h"
#include "GafferScene/Grid.h"
#include "GafferScene/Light.h"
#include "GafferScene/ObjectToScene.h"
#include "GafferScene/Plane.h"
#include "GafferScene/Sphere.h"
#include "GafferScene/Text.h"

#include "GafferBindings/DependencyNodeBinding.h"

using namespace std;
using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;

void GafferSceneModule::bindPrimitives()
{

	GafferBindings::DependencyNodeClass<ObjectSource>();
	GafferBindings::DependencyNodeClass<Plane>();
	GafferBindings::DependencyNodeClass<Cube>();
	GafferBindings::DependencyNodeClass<Text>();
	GafferBindings::DependencyNodeClass<ObjectToScene>();
	GafferBindings::DependencyNodeClass<Camera>();
	GafferBindings::DependencyNodeClass<ClippingPlane>();
	GafferBindings::DependencyNodeClass<CoordinateSystem>();
	GafferBindings::DependencyNodeClass<ExternalProcedural>();
	GafferBindings::DependencyNodeClass<Grid>();
	GafferBindings::DependencyNodeClass<Light>();

	{
		scope s = GafferBindings::DependencyNodeClass<Sphere>();

		enum_<Sphere::Type>( "Type" )
			.value( "Primitive", Sphere::Primitive )
			.value( "Mesh", Sphere::Mesh )
		;
	}

}
