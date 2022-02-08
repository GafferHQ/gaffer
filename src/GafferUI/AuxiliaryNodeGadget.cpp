//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/AuxiliaryNodeGadget.h"
#include "GafferUI/Style.h"
#include "GafferUI/GraphGadget.h"

#include "Gaffer/Metadata.h"

#include "boost/bind/bind.hpp"

using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace GafferUI;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( AuxiliaryNodeGadget );

AuxiliaryNodeGadget::NodeGadgetTypeDescription<AuxiliaryNodeGadget> AuxiliaryNodeGadget::g_nodeGadgetTypeDescription( Gaffer::Node::staticTypeId() );

static IECore::InternedString g_labelKey( "auxiliaryNodeGadget:label" );
static IECore::InternedString g_colorKey( "nodeGadget:color" );

AuxiliaryNodeGadget::AuxiliaryNodeGadget( Gaffer::NodePtr node )
	:	StandardNodeGadget( node, true ), m_label( "" ), m_radius( 1.0 )
{
	Gaffer::Metadata::nodeValueChangedSignal( node.get() ).connect( boost::bind( &AuxiliaryNodeGadget::nodeMetadataChanged, this, ::_2 ) );

	updateLabel();
	setContents( nullptr );
}

AuxiliaryNodeGadget::~AuxiliaryNodeGadget()
{
}

Imath::Box3f AuxiliaryNodeGadget::bound() const
{
	return Box3f( V3f( -m_radius, -m_radius, 0 ), V3f( m_radius, m_radius, 0 ) );
}

void AuxiliaryNodeGadget::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	StandardNodeGadget::renderLayer( layer, style, reason );
	if( layer != GraphLayer::Nodes )
	{
		return;
	}

	Imath::Box3f bound = style->textBound( Style::LabelText, m_label );
	Imath::V3f offset = bound.size() / 2.0;

	glPushMatrix();
		glTranslatef( -offset.x, -offset.y, 0.0f );
		style->renderText( Style::LabelText, m_label );
	glPopMatrix();
}

void AuxiliaryNodeGadget::nodeMetadataChanged( IECore::InternedString key )
{
	if( key == g_labelKey )
	{
		if( updateLabel() )
		{
			dirty( DirtyType::Render );
		}
	}
}

bool AuxiliaryNodeGadget::updateLabel()
{
	std::string l;
	if( IECore::ConstStringDataPtr d = Gaffer::Metadata::value<IECore::StringData>( node(), g_labelKey ) )
	{
		l = d->readable();
	}

	if( l == m_label )
	{
		return false;
	}

	m_label = l;
	return true;
}
