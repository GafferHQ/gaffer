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

#include "GafferUI/Gadget.h"
#include "GafferUI/Style.h"

#include "IECore/SimpleTypedData.h"

#include "OpenEXR/ImathBoxAlgo.h"

using namespace GafferUI;
using namespace Imath;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( Gadget );

Gadget::Gadget( const std::string &name )
	:	GraphComponent( name ), m_style( Style::getDefaultStyle() ), m_toolTip( "" )
{
}

Gadget::~Gadget()
{
}

bool Gadget::acceptsChild( Gaffer::ConstGraphComponentPtr potentialChild ) const
{
	return false;
}

bool Gadget::acceptsParent( const Gaffer::GraphComponent *potentialParent ) const
{
	return potentialParent->isInstanceOf( staticTypeId() );
}

ConstStylePtr Gadget::getStyle() const
{
	return m_style;
}

void Gadget::setStyle( ConstStylePtr style )
{
	if( style!=m_style )
	{
		m_style = style;
		renderRequestSignal()( this );
	}
}

void Gadget::setTransform( const Imath::M44f &matrix )
{
	if( matrix!=m_transform )
	{
		m_transform = matrix;
		renderRequestSignal()( this );
	}	
}

const Imath::M44f &Gadget::getTransform() const
{
	return m_transform;
}

Imath::M44f Gadget::fullTransform( ConstGadgetPtr ancestor ) const
{
	M44f result;
	const Gadget *g = this;
	do
	{
		result *= g->m_transform;
		g = g->parent<Gadget>();
	} while( g && g!=ancestor );
	
	return result;
}

void Gadget::render( IECore::RendererPtr renderer ) const
{
	renderer->attributeBegin();
		renderer->concatTransform( m_transform );
		renderer->setAttribute( "name", new IECore::StringData( fullName() ) );
		doRender( renderer );
	renderer->attributeEnd();
}

Imath::Box3f Gadget::transformedBound() const
{
	Box3f b = bound();
	return transform( b, getTransform() );
}

Imath::Box3f Gadget::transformedBound( ConstGadgetPtr ancestor ) const
{
	Box3f b = bound();
	return transform( b, fullTransform( ancestor ) );
}

Gadget::RenderRequestSignal &Gadget::renderRequestSignal()
{
	return m_renderRequestSignal;
}

std::string Gadget::getToolTip() const
{
	return m_toolTip;
}

void Gadget::setToolTip( const std::string &toolTip )
{
	m_toolTip = toolTip;
}

Gadget::ButtonSignal &Gadget::buttonPressSignal()
{
	return m_buttonPressSignal;
}

Gadget::ButtonSignal &Gadget::buttonReleaseSignal()
{
	return m_buttonReleaseSignal;
}

Gadget::DragBeginSignal &Gadget::dragBeginSignal()
{
	return m_dragBeginSignal;
}

Gadget::DragDropSignal &Gadget::dragUpdateSignal()
{
	return m_dragUpdateSignal;
}

Gadget::DragDropSignal &Gadget::dropSignal()
{
	return m_dropSignal;
}

Gadget::DragDropSignal &Gadget::dragEndSignal()
{
	return m_dragEndSignal;
}
		
Gadget::KeySignal &Gadget::keyPressSignal()
{
	return m_keyPressSignal;
}

Gadget::KeySignal &Gadget::keyReleaseSignal()
{
	return m_keyReleaseSignal;
}
