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

#include "GafferBindings/NodeBinding.h"

#include "GafferScene/Displays.h"

#include "GafferSceneBindings/DisplaysBinding.h"

using namespace std;
using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;

static Gaffer::CompoundPlugPtr addDisplayWrapper1( Displays &displays, const std::string &label )
{
	return displays.addDisplay( label );
}

static Gaffer::CompoundPlugPtr addDisplayWrapper2( Displays &displays, const std::string &label, const IECore::Display *d )
{
	return displays.addDisplay( label, d );
}

static tuple registeredDisplaysWrapper()
{
	vector<string> labels;
	Displays::registeredDisplays( labels );
	boost::python::list l;
	for( vector<string>::const_iterator it = labels.begin(); it!=labels.end(); it++ )
	{
		l.append( *it );
	}
	return boost::python::tuple( l );
}

void GafferSceneBindings::bindDisplays()
{
	NodeClass<Displays>()
		.def( "addDisplay", &addDisplayWrapper1 )
		.def( "addDisplay", &addDisplayWrapper2 )
		.def( "registerDisplay", &Displays::registerDisplay ).staticmethod( "registerDisplay" )
		.def( "registeredDisplays", &registeredDisplaysWrapper ).staticmethod( "registeredDisplays" )
	;
}
