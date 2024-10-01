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

#include "OpenColorIOAlgoBinding.h"

#include "GafferImage/OpenColorIOAlgo.h"

#include "OpenColorIO/OpenColorIO.h"

#include "IECorePython/PyBindConverter.h"
#include "IECorePython/ScopedGILRelease.h"

using namespace GafferImage;

namespace
{

void setConfigWrapper( Gaffer::Context &context, const std::string &configFileName )
{
	IECorePython::ScopedGILRelease gilRelease;
	OpenColorIOAlgo::setConfig( &context, configFileName );
}

const std::string getConfigWrapper( const Gaffer::Context &context )
{
	return OpenColorIOAlgo::getConfig( &context );
}

void setWorkingSpaceWrapper( Gaffer::Context &context, const std::string &colorSpace )
{
	IECorePython::ScopedGILRelease gilRelease;
	OpenColorIOAlgo::setWorkingSpace( &context, colorSpace );
}

const std::string getWorkingSpaceWrapper( const Gaffer::Context &context )
{
	return OpenColorIOAlgo::getWorkingSpace( &context );
}

void addVariableWrapper( Gaffer::Context &context, const std::string &name, const std::string &value )
{
	IECorePython::ScopedGILRelease gilRelease;
	OpenColorIOAlgo::addVariable( &context, name, value );
}

const std::string getVariableWrapper( const Gaffer::Context &context, const std::string &name )
{
	return OpenColorIOAlgo::getVariable( &context, name );
}

void removeVariableWrapper( Gaffer::Context &context, const std::string &name )
{
	IECorePython::ScopedGILRelease gilRelease;
	return OpenColorIOAlgo::removeVariable( &context, name );
}

boost::python::object variablesWrapper( const Gaffer::Context &context )
{
	boost::python::list result;
	for( const auto &variable : OpenColorIOAlgo::variables( &context ) )
	{
		result.append( variable );
	}
	return result;
}

boost::python::object currentConfigAndContextWrapper()
{
	const auto [config, ocioContext] = OpenColorIOAlgo::currentConfigAndContext();
	return boost::python::make_tuple( config, ocioContext );
}

} // namespace

void GafferImageModule::bindOpenColorIOAlgo()
{
	boost::python::object module( boost::python::borrowed( PyImport_AddModule( "GafferImage.OpenColorIOAlgo" ) ) );
	boost::python::scope().attr( "OpenColorIOAlgo" ) = module;
	boost::python::scope moduleScope( module );

	boost::python::def( "setConfig", &setConfigWrapper );
	boost::python::def( "getConfig", &getConfigWrapper );

	boost::python::def( "setWorkingSpace", &setWorkingSpaceWrapper );
	boost::python::def( "getWorkingSpace", &getWorkingSpaceWrapper );

	boost::python::def( "addVariable", &addVariableWrapper );
	boost::python::def( "getVariable", &getVariableWrapper );
	boost::python::def( "removeVariable", &removeVariableWrapper );
	boost::python::def( "variables", &variablesWrapper );

	boost::python::def( "currentConfig", &OpenColorIOAlgo::currentConfig );
	boost::python::def( "currentConfigAndContext", &currentConfigAndContextWrapper );
	boost::python::def( "currentConfigAndContextHash", &OpenColorIOAlgo::currentConfigAndContextHash );

	IECorePython::PyBindConverter<OCIO_NAMESPACE::ConstConfigRcPtr>::registerConverters();
	IECorePython::PyBindConverter<OCIO_NAMESPACE::ConstContextRcPtr>::registerConverters();

}
