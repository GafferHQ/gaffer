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

#include "AttributesBinding.h"

#include "GafferScene/AttributeProcessor.h"
#include "GafferScene/AttributeVisualiser.h"
#include "GafferScene/Attributes.h"
#include "GafferScene/CopyAttributes.h"
#include "GafferScene/CustomAttributes.h"
#include "GafferScene/DeleteAttributes.h"
#include "GafferScene/OpenGLAttributes.h"
#include "GafferScene/ShaderAssignment.h"
#include "GafferScene/ShuffleAttributes.h"
#include "GafferScene/StandardAttributes.h"

#include "GafferBindings/DependencyNodeBinding.h"

using namespace boost::python;
using namespace GafferScene;

void GafferSceneModule::bindAttributes()
{

	GafferBindings::DependencyNodeClass<ShaderAssignment>();
	GafferBindings::DependencyNodeClass<Attributes>();
	GafferBindings::DependencyNodeClass<OpenGLAttributes>();
	GafferBindings::DependencyNodeClass<StandardAttributes>();
	GafferBindings::DependencyNodeClass<CustomAttributes>();
	GafferBindings::DependencyNodeClass<AttributeProcessor>();
	GafferBindings::DependencyNodeClass<DeleteAttributes>();
	GafferBindings::DependencyNodeClass<CopyAttributes>();
	GafferBindings::DependencyNodeClass<ShuffleAttributes>();

	scope s = GafferBindings::DependencyNodeClass<AttributeVisualiser>();

	enum_<AttributeVisualiser::Mode>( "Mode" )
		.value( "Color", AttributeVisualiser::Color )
		.value( "FalseColor", AttributeVisualiser::FalseColor )
		.value( "Random", AttributeVisualiser::Random )
		.value( "ShaderNodeColor", AttributeVisualiser::ShaderNodeColor )
	;

}
