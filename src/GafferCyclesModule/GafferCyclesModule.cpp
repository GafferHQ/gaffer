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

#include "GafferCycles/CyclesAttributes.h"
#include "GafferCycles/CyclesOptions.h"
#include "GafferCycles/CyclesLight.h"
#include "GafferCycles/CyclesShader.h"
#include "GafferCycles/CyclesRender.h"
#include "GafferCycles/InteractiveCyclesRender.h"

// Cycles
#include "graph/node.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace GafferDispatchBindings;
using namespace GafferCycles;

namespace
{

boost::python::dict getSocketUINameDict( const ccl::NodeType *nodeType, const bool output )
{
	boost::python::dict result;

	if( output )
	{
		for( const ccl::SocketType socketType : nodeType->outputs )
		{
			result[socketType.ui_name.c_str()] = socketType.name.c_str();
		}
	}
	else
	{
		for( const ccl::SocketType socketType : nodeType->inputs )
		{
			result[socketType.ui_name.c_str()] = socketType.name.c_str();
		}
	}

	return result;
}

boost::python::dict createNodeRegistry()
{
	boost::python::dict result;

	for( const auto& nodeType : ccl::NodeType::types() )
	{
		const ccl::NodeType *cNodeType = ccl::NodeType::find( nodeType.first );
		if( cNodeType )
		{
			boost::python::dict sockets;
			sockets["in"] = getSocketUINameDict( cNodeType, false );
			sockets["out"] = getSocketUINameDict( cNodeType, true );
			result[nodeType.first.c_str()] = sockets;
		}
	}
	return result;
}

} // namespace

BOOST_PYTHON_MODULE( _GafferCycles )
{

	boost::python::scope().attr( "nodeRegistry" ) = createNodeRegistry();

	DependencyNodeClass<CyclesAttributes>();
	DependencyNodeClass<CyclesOptions>();
	DependencyNodeClass<CyclesLight>();
	DependencyNodeClass<CyclesShader>();
	TaskNodeClass<CyclesRender>();
	NodeClass<InteractiveCyclesRender>();

}
