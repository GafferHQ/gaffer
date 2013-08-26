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

#include "boost/lexical_cast.hpp"

#include "OpenEXR/ImathBoxAlgo.h"

#include "IECore/SimpleTypedData.h"

#include "IECoreGL/GL.h"
#include "IECoreGL/NameStateComponent.h"
#include "IECoreGL/Selector.h"

#include "GafferUI/Gadget.h"
#include "GafferUI/Style.h"

using namespace GafferUI;
using namespace Imath;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( Gadget );

Gadget::Gadget( const std::string &name )
	:	GraphComponent( name ), m_style( 0 ), m_toolTip( "" )
{
	std::string n = "__Gaffer::Gadget::" + boost::lexical_cast<std::string>( (size_t)this );
	m_glName = IECoreGL::NameStateComponent::glNameFromName( n, true );
}

GadgetPtr Gadget::select( const std::string &name )
{
	if( name.compare( 0, 18, "__Gaffer::Gadget::" ) )
	{
		return 0;
	}
	std::string address = name.c_str() + 18;
	size_t a = boost::lexical_cast<size_t>( address );
	return reinterpret_cast<Gadget *>( a );
}

Gadget::~Gadget()
{
}

bool Gadget::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	return false;
}

bool Gadget::acceptsParent( const Gaffer::GraphComponent *potentialParent ) const
{
	return potentialParent->isInstanceOf( staticTypeId() );
}

void Gadget::setStyle( ConstStylePtr style )
{
	if( style!=m_style )
	{
		m_style = style;
		renderRequestSignal()( this );
	}
}

const Style *Gadget::getStyle() const
{
	return m_style.get();
}

const Style *Gadget::style() const
{
	const Gadget *g = this;
	while( g )
	{
		if( g->m_style )
		{
			return g->m_style.get();
		}
		g = g->parent<Gadget>();
	}
	return Style::getDefaultStyle().get();
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

void Gadget::render( const Style *currentStyle ) const
{
	glPushMatrix();
	
		glMultMatrixf( m_transform.getValue() );
			
		if( !currentStyle )
		{
			currentStyle = style();
			currentStyle->bind();
		}
		else
		{
			if( m_style )
			{
				m_style->bind();
				currentStyle = m_style;
			}
		}

		if( IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector() )
		{
			selector->loadName( m_glName );
		}
		
		doRender( currentStyle );

	glPopMatrix();
}

void Gadget::doRender( const Style *style ) const
{
}

Imath::Box3f Gadget::bound() const
{
	return Box3f();
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

std::string Gadget::getToolTip( const IECore::LineSegment3f &position ) const
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

Gadget::ButtonSignal &Gadget::buttonDoubleClickSignal()
{
	return m_buttonDoubleClickSignal;
}

Gadget::ButtonSignal &Gadget::wheelSignal()
{
	return m_wheelSignal;
}

Gadget::EnterLeaveSignal &Gadget::enterSignal()
{
	return m_enterSignal;
}

Gadget::EnterLeaveSignal &Gadget::leaveSignal()
{
	return m_leaveSignal;
}

Gadget::ButtonSignal &Gadget::mouseMoveSignal()
{
	return m_mouseMoveSignal;
}

Gadget::DragBeginSignal &Gadget::dragBeginSignal()
{
	return m_dragBeginSignal;
}

Gadget::DragDropSignal &Gadget::dragMoveSignal()
{
	return m_dragMoveSignal;
}

Gadget::DragDropSignal &Gadget::dragEnterSignal()
{
	return m_dragEnterSignal;
}

Gadget::DragDropSignal &Gadget::dragLeaveSignal()
{
	return m_dragLeaveSignal;
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

Gadget::IdleSignal &Gadget::idleSignal()
{
	static IdleSignal g_idleSignal;
	idleSignalAccessedSignal()();
	return g_idleSignal;
}

Gadget::IdleSignal &Gadget::idleSignalAccessedSignal()
{
	static IdleSignal g_idleSignalAccessedSignal;
	return g_idleSignalAccessedSignal;
}
