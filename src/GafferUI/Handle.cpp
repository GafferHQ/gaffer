//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2014, John Haddon. All rights reserved.
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

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include "GafferUI/Handle.h"
#include "GafferUI/Style.h"

using namespace Imath;
using namespace GafferUI;

IE_CORE_DEFINERUNTIMETYPED( Handle );

Handle::Handle( Type type )
	:	Gadget( defaultName<Handle>() ), m_type( type ), m_hovering( false )
{
	enterSignal().connect( boost::bind( &Handle::enter, this ) );
	leaveSignal().connect( boost::bind( &Handle::leave, this ) );
}

Handle::~Handle()
{
}

void Handle::setType( Type type )
{
	if( type == m_type )
	{
		return;
	}
	
	m_type = type;
	renderRequestSignal()( this );
}

Handle::Type Handle::getType() const
{
	return m_type;
}

Imath::Box3f Handle::bound() const
{
	switch( m_type )
	{
		case TranslateX :
			return Box3f( V3f( 0 ), V3f( 1, 0, 0 ) );
		case TranslateY :
			return Box3f( V3f( 0 ), V3f( 0, 1, 0 ) );
		case TranslateZ :
			return Box3f( V3f( 0 ), V3f( 0, 0, 1 ) );
	};
	
	return Box3f();
}

void Handle::doRender( const Style *style ) const
{
	Style::State state = getHighlighted() || m_hovering ? Style::HighlightedState : Style::NormalState;

	switch( m_type )
	{
		case TranslateX :
			style->renderTranslateHandle( 0, state );
			break;
		case TranslateY :
			style->renderTranslateHandle( 1, state );
			break;
		case TranslateZ :
			style->renderTranslateHandle( 2, state );
			break;
	}
}

void Handle::enter()
{
	m_hovering = true;
	renderRequestSignal()( this );
}

void Handle::leave()
{
	m_hovering = false;
	renderRequestSignal()( this );
}
