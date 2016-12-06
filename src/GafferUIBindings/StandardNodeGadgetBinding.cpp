//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Plug.h"

#include "GafferUI/StandardNodeGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/Private/SwitchNodeGadget.h"

#include "GafferUIBindings/StandardNodeGadgetBinding.h"
#include "GafferUIBindings/NodeGadgetBinding.h"

using namespace boost::python;
using namespace GafferUI;
using namespace GafferUI::Private;
using namespace GafferUIBindings;

namespace
{

class StandardNodeGadgetWrapper : public NodeGadgetWrapper<StandardNodeGadget>
{

	public :

		StandardNodeGadgetWrapper( PyObject *self, Gaffer::NodePtr node )
			:	NodeGadgetWrapper<StandardNodeGadget>( self, node )
		{
		}

};

GadgetPtr getContents( StandardNodeGadget &g )
{
	return g.getContents();
}

GadgetPtr getEdgeGadget( StandardNodeGadget &g, StandardNodeGadget::Edge edge )
{
	return g.getEdgeGadget( edge );
}

} // namespace

void GafferUIBindings::bindStandardNodeGadget()
{
	scope s = NodeGadgetClass<StandardNodeGadget, StandardNodeGadgetWrapper>()
		.def( init<Gaffer::NodePtr>( arg( "node" ) ) )
		.def( "setContents", &StandardNodeGadget::setContents )
		.def( "getContents", &getContents )
		.def( "setEdgeGadget", &StandardNodeGadget::setEdgeGadget )
		.def( "getEdgeGadget", &getEdgeGadget )
	;

	enum_<StandardNodeGadget::Edge>( "Edge" )
		.value( "TopEdge", StandardNodeGadget::TopEdge )
		.value( "BottomEdge", StandardNodeGadget::BottomEdge )
		.value( "LeftEdge", StandardNodeGadget::LeftEdge )
		.value( "RightEdge", StandardNodeGadget::RightEdge )
	;

	// Expose private derived classes of StandardNodeGadget as copies of
	// StandardNodeGadget. We don't want to bind them fully because then
	// we'd be exposing a private class, but we need to register them so
	// that they can be returned to Python successfully.
	//
	// See "Boost.Python and slightly more tricky inheritance" at
	// http://lists.boost.org/Archives/boost/2005/09/93017.php for
	// more details.

	objects::copy_class_object( type_id<StandardNodeGadget>(), type_id<SwitchNodeGadget>() );

}
