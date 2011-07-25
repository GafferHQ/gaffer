//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/CompoundPlug.h"
#include "Gaffer/PlugIterator.h"

#include "GafferUI/ArrayNodule.h"
#include "GafferUI/LinearContainer.h"

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace GafferUI;
using namespace Imath;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( ArrayNodule );

ArrayNodule::ArrayNodule( Gaffer::CompoundPlugPtr plug )
	:	Nodule( plug )
{
	m_row = new LinearContainer( "row", LinearContainer::X, LinearContainer::Centre, 0.0f );
	addChild( m_row );

	plug->childAddedSignal().connect( boost::bind( &ArrayNodule::childAdded, this, ::_1,  ::_2 ) );
	plug->childRemovedSignal().connect( boost::bind( &ArrayNodule::childRemoved, this, ::_1,  ::_2 ) );

	Gaffer::PlugIterator it = Gaffer::PlugIterator( plug->children().begin(), plug->children().end() );
	Gaffer::PlugIterator end = Gaffer::PlugIterator( plug->children().end(), plug->children().end() );
	for( ; it!=end; it++ )
	{
		NodulePtr nodule = Nodule::create( *it );
		if( nodule )
		{
			m_row->addChild( nodule );
		}
	}
	
	m_row->renderRequestSignal().connect( boost::bind( &ArrayNodule::childRenderRequest, this, ::_1 ) );
}

ArrayNodule::~ArrayNodule()
{
}

Imath::Box3f ArrayNodule::bound() const
{
	return m_row->bound();
}

void ArrayNodule::doRender( IECore::RendererPtr renderer ) const
{
	m_row->render( renderer );
}

bool ArrayNodule::acceptsChild( Gaffer::ConstGraphComponentPtr potentialChild ) const
{
	return children().size()==0;
}

NodulePtr ArrayNodule::nodule( Gaffer::ConstPlugPtr plug )
{
	ChildNoduleIterator it = ChildNoduleIterator( m_row->children().begin(), m_row->children().end() );
	ChildNoduleIterator end = ChildNoduleIterator( m_row->children().end(), m_row->children().end() );
	for( ; it!=end; it++ )
	{
		if( (*it)->plug() == plug )
		{
			return *it;
		}
	}
	return 0;
}

ConstNodulePtr ArrayNodule::nodule( Gaffer::ConstPlugPtr plug ) const
{
	// preferring the nasty casts over mainaining two nearly identical implementations
	return const_cast<ArrayNodule *>( this )->nodule( plug );
}
		
void ArrayNodule::childAdded( Gaffer::GraphComponentPtr parent, Gaffer::GraphComponentPtr child )
{
	Gaffer::PlugPtr plug = IECore::runTimeCast<Gaffer::Plug>( child );
	if( !plug )
	{
		return;
	}
	
	NodulePtr nodule = Nodule::create( plug );
	if( nodule )
	{
		m_row->addChild( nodule );
	}
}

void ArrayNodule::childRemoved( Gaffer::GraphComponentPtr parent, Gaffer::GraphComponentPtr child )
{
	Gaffer::PlugPtr plug = IECore::runTimeCast<Gaffer::Plug>( child );
	if( !plug )
	{
		return;
	}
	
	ChildNoduleIterator it = ChildNoduleIterator( m_row->children().begin(), m_row->children().end() );
	ChildNoduleIterator end = ChildNoduleIterator( m_row->children().end(), m_row->children().end() );
	for( ; it!=end; it++ )
	{
		if( (*it)->plug() == plug )
		{
			m_row->removeChild( *it );
			break;
		}
	}	
}

void ArrayNodule::childRenderRequest( Gadget *child )
{
	renderRequestSignal()( this );
}
