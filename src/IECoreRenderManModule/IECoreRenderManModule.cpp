//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "IECoreRenderMan/ShaderNetworkAlgo.h"

#include "prmanapi.h"

using namespace boost::python;
using namespace IECore;
using namespace IECoreRenderMan;

namespace
{

int renderManMajorVersion()
{
	return _PRMANAPI_VERSION_MAJOR_;
}

ShaderNetworkAlgo::VStructAction evaluateVStructConditionalWrapper( const std::string &expression, object valueFunction, object isConnectedFunction )
{
	return ShaderNetworkAlgo::evaluateVStructConditional(
		expression,
		[&valueFunction] ( InternedString parameterName ) {
			return extract<ConstDataPtr>( valueFunction( parameterName.string() ) );
		},
		[&isConnectedFunction] ( InternedString parameterName ) {
			return extract<bool>( isConnectedFunction( parameterName.string() ) );
		}
	);
}

} // namespace

BOOST_PYTHON_MODULE( _IECoreRenderMan )
{

	def( "renderManMajorVersion", renderManMajorVersion );

	object shaderNetworkAlgoModule( borrowed( PyImport_AddModule( "IECoreRenderMan.ShaderNetworkAlgo" ) ) );
	scope().attr( "ShaderNetworkAlgo" ) = shaderNetworkAlgoModule;
	scope shaderNetworkAlgoScope( shaderNetworkAlgoModule );

	def( "convertUSDShaders", &ShaderNetworkAlgo::convertUSDShaders );
	def( "usdLightTransform", &ShaderNetworkAlgo::usdLightTransform );

	{
		scope s = class_<ShaderNetworkAlgo::VStructAction>( "VStructAction" )
			.def_readonly( "type", &ShaderNetworkAlgo::VStructAction::type )
			.def_readonly( "value", &ShaderNetworkAlgo::VStructAction::value )
		;

		enum_<ShaderNetworkAlgo::VStructAction::Type>( "Type" )
			.value( "None_", ShaderNetworkAlgo::VStructAction::Type::None )
			.value( "Connect", ShaderNetworkAlgo::VStructAction::Type::Connect )
			.value( "Set", ShaderNetworkAlgo::VStructAction::Type::Set )
		;
	}

	def( "evaluateVStructConditional", &evaluateVStructConditionalWrapper );
	def( "resolveVStructs", &ShaderNetworkAlgo::resolveVStructs );

}
