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

#include "GlobalsBinding.h"

#include "GafferScene/DeleteOutputs.h"
#include "GafferScene/DeleteSets.h"
#include "GafferScene/GlobalShader.h"
#include "GafferScene/Outputs.h"
#include "GafferScene/Set.h"

#include "GafferBindings/DependencyNodeBinding.h"

using namespace std;
using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;

namespace
{

ValuePlugPtr addOutputWrapper( Outputs &o, const std::string &name )
{
	ScopedGILRelease gilRelease;
	return o.addOutput( name );
}

ValuePlugPtr addOutputWrapper2( Outputs &o, const std::string &name, const IECoreScene::Output *output )
{
	ScopedGILRelease gilRelease;
	return o.addOutput( name, output );
}

boost::python::tuple registeredOutputsWrapper()
{
	vector<string> names;
	Outputs::registeredOutputs( names );
	boost::python::list l;
	for( vector<string>::const_iterator it = names.begin(); it!=names.end(); it++ )
	{
		l.append( *it );
	}
	return boost::python::tuple( l );
}

} // namespace

void GafferSceneModule::bindGlobals()
{

	DependencyNodeClass<GlobalsProcessor>();
	DependencyNodeClass<DeleteGlobals>()
		.def( "_namePrefix", &DeleteGlobals::namePrefix )
	;

	DependencyNodeClass<DeleteOutputs>();
	DependencyNodeClass<DeleteSets>();

	DependencyNodeClass<Outputs>()
		.def( "addOutput", &addOutputWrapper )
		.def( "addOutput", &addOutputWrapper2 )
		.def( "registerOutput", &Outputs::registerOutput ).staticmethod( "registerOutput" )
		.def( "deregisterOutput", &Outputs::deregisterOutput ).staticmethod( "deregisterOutput" )
		.def( "registeredOutputs", &registeredOutputsWrapper ).staticmethod( "registeredOutputs" )
	;

	{
		scope s = DependencyNodeClass<GafferScene::Set>();

			enum_<GafferScene::Set::Mode>( "Mode" )
				.value( "Create", GafferScene::Set::Create )
				.value( "Add", GafferScene::Set::Add )
				.value( "Remove", GafferScene::Set::Remove )
			;
	}

	DependencyNodeClass<GlobalShader>();

}
