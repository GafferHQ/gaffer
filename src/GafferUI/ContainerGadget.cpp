//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "GafferUI/ContainerGadget.h"

#include "OpenEXR/ImathBoxAlgo.h"

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace GafferUI;

IE_CORE_DEFINERUNTIMETYPED( ContainerGadget );

ContainerGadget::ContainerGadget( const std::string &name )
	:	Gadget( name )
{
	childAddedSignal().connect( boost::bind( &ContainerGadget::childAdded, this, ::_1, ::_2 ) );
	childRemovedSignal().connect( boost::bind( &ContainerGadget::childRemoved, this, ::_1, ::_2 )  );
}

ContainerGadget::~ContainerGadget()
{
}

bool ContainerGadget::acceptsChild( Gaffer::ConstGraphComponentPtr potentialChild ) const
{
	return potentialChild->isInstanceOf( Gadget::staticTypeId() );
}

Imath::Box3f ContainerGadget::bound() const
{
	Imath::Box3f result;
	for( ChildContainer::const_iterator it=children().begin(); it!=children().end(); it++ )
	{
		// cast is safe because of the guarantees acceptsChild() gives us
		ConstGadgetPtr c = IECore::staticPointerCast<const Gadget>( *it );
		Imath::Box3f b = c->bound();
		b = Imath::transform( b, c->getTransform() );
		result.extendBy( b );
	}
	return result;
}

void ContainerGadget::doRender( IECore::RendererPtr renderer ) const
{
	for( ChildContainer::const_iterator it=children().begin(); it!=children().end(); it++ )
	{
		// cast is safe because of the guarantees acceptsChild() gives us
		ConstGadgetPtr c = IECore::staticPointerCast<const Gadget>( *it );
		c->render( renderer );
	}
}

void ContainerGadget::childAdded( GraphComponent *parent, GraphComponent *child )
{
	assert( parent==this );
	static_cast<Gadget *>( child )->renderRequestSignal().connect( boost::bind( &ContainerGadget::childRenderRequest, this, ::_1 ) );
	renderRequestSignal()( this );
}

void ContainerGadget::childRemoved( GraphComponent *parent, GraphComponent *child )
{
	assert( parent==this );
	static_cast<Gadget *>( child )->renderRequestSignal().disconnect( &ContainerGadget::childRenderRequest );
	renderRequestSignal()( this );
}

void ContainerGadget::childRenderRequest( Gadget *child )
{
	renderRequestSignal()( this );
}
