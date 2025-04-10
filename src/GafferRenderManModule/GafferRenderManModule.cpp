//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, John Haddon. All rights reserved.
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

#include "GafferRenderMan/BXDFPlug.h"
#include "GafferRenderMan/RenderManAttributes.h"
#include "GafferRenderMan/RenderManDisplayFilter.h"
#include "GafferRenderMan/RenderManIntegrator.h"
#include "GafferRenderMan/RenderManLight.h"
#include "GafferRenderMan/RenderManLightFilter.h"
#include "GafferRenderMan/RenderManMeshLight.h"
#include "GafferRenderMan/RenderManOptions.h"
#include "GafferRenderMan/RenderManSampleFilter.h"
#include "GafferRenderMan/RenderManShader.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/PlugBinding.h"

using namespace boost::python;
using namespace GafferRenderMan;

namespace
{

void loadShader( RenderManLight &l, const std::string &shaderName )
{
	IECorePython::ScopedGILRelease gilRelease;
	l.loadShader( shaderName );
}

} // namespace

BOOST_PYTHON_MODULE( _GafferRenderMan )
{
	GafferBindings::PlugClass<BXDFPlug>()
		.def( init<const std::string &, Gaffer::Plug::Direction, unsigned>(
				(
					arg( "name" ) = Gaffer::GraphComponent::defaultName<BXDFPlug>(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "flags" ) = Gaffer::Plug::Default
				)
			)
		)
	;


	GafferBindings::DependencyNodeClass<RenderManLight>()
		.def( "loadShader", &loadShader )
	;
	GafferBindings::DependencyNodeClass<RenderManLightFilter>();
	GafferBindings::DependencyNodeClass<RenderManAttributes>();
	GafferBindings::DependencyNodeClass<RenderManOptions>();
	GafferBindings::DependencyNodeClass<RenderManShader>();
	GafferBindings::DependencyNodeClass<RenderManMeshLight>();
	GafferBindings::DependencyNodeClass<RenderManIntegrator>();

	{
		scope s = GafferBindings::DependencyNodeClass<RenderManOutputFilter>( nullptr, no_init );
		enum_<RenderManOutputFilter::Mode>( "Mode" )
			.value( "Replace", RenderManOutputFilter::Mode::Replace )
			.value( "InsertFirst", RenderManOutputFilter::Mode::InsertFirst )
			.value( "InsertLast", RenderManOutputFilter::Mode::InsertLast )
		;
	}

	GafferBindings::DependencyNodeClass<RenderManSampleFilter>();
	GafferBindings::DependencyNodeClass<RenderManDisplayFilter>();
}
