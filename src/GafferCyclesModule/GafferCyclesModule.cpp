//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

#include "GafferBindings/DependencyNodeBinding.h"

#include "GafferDispatchBindings/TaskNodeBinding.h"

#include "GafferCycles/IECoreCyclesPreview/IECoreCycles.h"
#include "GafferCycles/IECoreCyclesPreview/ShaderNetworkAlgo.h"
#include "GafferCycles/CyclesAttributes.h"
#include "GafferCycles/CyclesBackground.h"
#include "GafferCycles/CyclesOptions.h"
#include "GafferCycles/CyclesLight.h"
#include "GafferCycles/CyclesMeshLight.h"
#include "GafferCycles/CyclesShader.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace GafferDispatchBindings;
using namespace GafferCycles;

BOOST_PYTHON_MODULE( _GafferCycles )
{

	IECoreCycles::init();

	scope().attr( "majorVersion" ) = IECoreCycles::majorVersion();
	scope().attr( "minorVersion" ) = IECoreCycles::minorVersion();
	scope().attr( "patchVersion" ) = IECoreCycles::patchVersion();
	scope().attr( "version" ) = IECoreCycles::versionString();
	scope().attr( "devices" ) = IECoreCycles::devices()->copy();
	scope().attr( "nodes" ) = IECoreCycles::nodes()->copy();
	scope().attr( "shaders" ) = IECoreCycles::shaders()->copy();
	scope().attr( "lights" ) = IECoreCycles::lights()->copy();
	scope().attr( "passes" ) = IECoreCycles::passes()->copy();
	scope().attr( "hasOpenImageDenoise" ) = IECoreCycles::openImageDenoiseSupported();
	scope().attr( "hasOptixDenoise" ) = IECoreCycles::optixDenoiseSupported();

	DependencyNodeClass<CyclesAttributes>();
	DependencyNodeClass<CyclesBackground>();
	DependencyNodeClass<CyclesOptions>();
	DependencyNodeClass<CyclesLight>()
		.def( "loadShader", (void (CyclesLight::*)( const std::string & ) )&CyclesLight::loadShader )
	;
	DependencyNodeClass<CyclesMeshLight>();
	DependencyNodeClass<CyclesShader>();

	{
		object ieCoreCyclesModule( borrowed( PyImport_AddModule( "GafferCycles.IECoreCyclesPreview" ) ) );
		scope().attr( "IECoreCyclesPreview" ) = ieCoreCyclesModule;
		scope ieCoreCyclesScope( ieCoreCyclesModule );

		object shaderNetworkAlgoModule( borrowed( PyImport_AddModule( "GafferCycles.IECoreCyclesPreview.ShaderNetworkAlgo" ) ) );
		scope().attr( "ShaderNetworkAlgo" ) = shaderNetworkAlgoModule;
		scope shaderNetworkAlgoScope( shaderNetworkAlgoModule );

		def( "convertUSDShaders", &IECoreCycles::ShaderNetworkAlgo::convertUSDShaders );
	}

}
