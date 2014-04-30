//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/BackdropNodeGadget.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/Nodule.h"

#include "GafferUIBindings/NodeGadgetBinding.h"
#include "GafferUIBindings/BackdropNodeGadgetBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferUIBindings;

static void frame( BackdropNodeGadget &b, object nodes )
{
	std::vector<Node *> n;
	boost::python::container_utils::extend_container( n, nodes );
	b.frame( n );
}

static list framed( BackdropNodeGadget &b )
{
	std::vector<Node *> n;
	b.framed( n );
	
	list result;
	for( std::vector<Node *>::const_iterator it = n.begin(), eIt = n.end(); it != eIt; ++it )
	{
		result.append( NodePtr( *it ) );
	}
	
	return result;
}

void GafferUIBindings::bindBackdropNodeGadget()
{
	NodeGadgetClass<BackdropNodeGadget>()
		.def( init<Gaffer::NodePtr>() )
		.def( "frame", &frame )
		.def( "framed", &framed )
	;
}
