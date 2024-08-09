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
#include "GafferCycles/CyclesRender.h"
#include "GafferCycles/InteractiveCyclesRender.h"

#include "IECore/CompoundData.h"
#include "IECore/MessageHandler.h"

namespace py = boost::python;
using namespace boost::python;
using namespace GafferBindings;
using namespace GafferDispatchBindings;
using namespace GafferCycles;

namespace
{

py::dict makeDict( const IECore::CompoundData *data, const std::string &name )
{
	py::dict d;
	const IECore::CompoundDataMap &cDataMap = data->readable();
	for( IECore::CompoundDataMap::const_iterator it = cDataMap.begin(), eIt = cDataMap.end(); it != eIt; ++it )
	{
		if( const IECore::FloatData *dt = IECore::runTimeCast<const IECore::FloatData>( it->second.get() ) )
		{
			d[it->first.string()] = dt->readable();
		}
		else if( const IECore::IntData *dt = IECore::runTimeCast<const IECore::IntData>( it->second.get() ) )
		{
			d[it->first.string()] = dt->readable();
		}
		else if( const IECore::BoolData *dt = IECore::runTimeCast<const IECore::BoolData>( it->second.get() ) )
		{
			d[it->first.string()] = dt->readable();
		}
		else if( const IECore::StringData *dt = IECore::runTimeCast<const IECore::StringData>( it->second.get() ) )
		{
			d[it->first.string()] = dt->readable();
		}
		else if( const IECore::CompoundData *dt = IECore::runTimeCast<const IECore::CompoundData>( it->second.get() ) )
		{
			d[it->first.string()] = makeDict( dt, it->first.string() );
		}
		else
		{
			IECore::msg( IECore::Msg::Warning, "GafferCyclesModule::makeDict",
				fmt::format(
					"Type {} is unsupported for binding {}'s \"{}\".",
					it->second->typeName(), name.c_str(), it->first.c_str()
				)
			);
		}
	}
	return d;
}

py::list getDevices()
{
	py::list result;
	const IECore::CompoundDataMap &devices = IECoreCycles::devices()->readable();

	for( IECore::CompoundDataMap::const_iterator it = devices.begin(), eIt = devices.end(); it != eIt; ++it )
	{
		if( const IECore::CompoundData *dt = IECore::runTimeCast<const IECore::CompoundData>( it->second.get() ) )
		{
			result.append( makeDict( dt, "devices" ) );
		}
		else
		{
			IECore::msg( IECore::Msg::Warning, "GafferCyclesModule::getDevices",
				fmt::format(
					"Unexpected type data from IECoreCycles::getDevices {}.",
					it->second->typeName()
				)
			);
		}
	}
	return result;
}

py::dict getNodes()
{
	return makeDict( IECoreCycles::nodes(), "nodes" );
}

py::dict getShaders()
{
	return makeDict( IECoreCycles::shaders(), "shaders" );
}

py::dict getLights()
{
	return makeDict( IECoreCycles::lights(), "lights" );
}

py::dict getPasses()
{
	return makeDict( IECoreCycles::passes(), "passes" );
}

} // namespace

BOOST_PYTHON_MODULE( _GafferCycles )
{

	IECoreCycles::init();

	py::scope().attr( "majorVersion" ) = IECoreCycles::majorVersion();
	py::scope().attr( "minorVersion" ) = IECoreCycles::minorVersion();
	py::scope().attr( "patchVersion" ) = IECoreCycles::patchVersion();
	py::scope().attr( "version" ) = IECoreCycles::versionString();
	py::scope().attr( "devices" ) = getDevices();
	py::scope().attr( "nodes" ) = getNodes();
	py::scope().attr( "shaders" ) = getShaders();
	py::scope().attr( "lights" ) = getLights();
	py::scope().attr( "passes" ) = getPasses();
	py::scope().attr( "hasOpenImageDenoise" ) = IECoreCycles::openImageDenoiseSupported();
	py::scope().attr( "hasOptixDenoise" ) = IECoreCycles::optixDenoiseSupported();

	DependencyNodeClass<CyclesAttributes>();
	DependencyNodeClass<CyclesBackground>();
	DependencyNodeClass<CyclesOptions>();
	DependencyNodeClass<CyclesLight>()
		.def( "loadShader", (void (CyclesLight::*)( const std::string & ) )&CyclesLight::loadShader )
	;
	DependencyNodeClass<CyclesMeshLight>();
	DependencyNodeClass<CyclesShader>();
	TaskNodeClass<CyclesRender>();
	NodeClass<InteractiveCyclesRender>();

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
