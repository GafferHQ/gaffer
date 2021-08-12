//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/TextGadget.h"

#include "GafferUI/Style.h"

#include "IECore/SimpleTypedData.h"

using namespace GafferUI;
using namespace IECore;
using namespace boost;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( TextGadget );

TextGadget::TextGadget( const std::string &text )
	:	Gadget( defaultName<TextGadget>() )
{
	setText( text );
}

TextGadget::~TextGadget()
{
}

const std::string &TextGadget::getText() const
{
	return m_text;
}

void TextGadget::setText( const std::string &text )
{
	if( text!=m_text )
	{
		m_text = text;
		m_bound = style()->textBound( Style::LabelText, m_text );
		// we don't want our bounding box in y to change when
		// the text changes, so we base our y bound on the bound of
		// the largest character.
		Imath::Box3f cb = style()->characterBound( Style::LabelText );
		m_bound.min.y = std::min( m_bound.min.y, cb.min.y );
		m_bound.max.y = std::max( m_bound.max.y, cb.max.y );
		dirty( DirtyType::Bound );
	}
}

Imath::Box3f TextGadget::bound() const
{
	return m_bound;
}

void TextGadget::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	if( layer != Layer::Main )
	{
		return;
	}

	style->renderText( Style::LabelText, m_text );
}

unsigned TextGadget::layerMask() const
{
	return (unsigned)Layer::Main;
}

Imath::Box3f TextGadget::renderBound() const
{
	return m_bound;
}
