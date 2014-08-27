//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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
#include "boost/python/suite/indexing/container_utils.hpp"

#include "GafferBindings/DependencyNodeBinding.h"

#include "GafferScene/Outputs.h"
#include "GafferScene/DeleteOutputs.h"

#include "GafferSceneBindings/OutputsBinding.h"

using namespace std;
using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;

static Gaffer::CompoundPlugPtr addOutputWrapper1( Outputs &outputs, const std::string &name )
{
	return outputs.addOutput( name );
}

static Gaffer::CompoundPlugPtr addOutputWrapper2( Outputs &outputs, const std::string &name, const IECore::Display *d )
{
	return outputs.addOutput( name, d );
}

static tuple registeredOutputsWrapper()
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

void GafferSceneBindings::bindOutputs()
{
	DependencyNodeClass<Outputs>()
		.def( "addOutput", &addOutputWrapper1 )
		.def( "addOutput", &addOutputWrapper2 )
		.def( "registerOutput", &Outputs::registerOutput ).staticmethod( "registerOutput" )
		.def( "registeredOutputs", &registeredOutputsWrapper ).staticmethod( "registeredOutputs" )
	;

	DependencyNodeClass<DeleteOutputs>();

}
