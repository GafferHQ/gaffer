//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/FPSGadget.h"

#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

using namespace GafferUI;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( FPSGadget );

FPSGadget::FPSGadget( Imath::V3f defaultPosition )
	:	Gadget( defaultName<FPSGadget>() )
{
	Imath::M44f m;
	m.setTranslation( defaultPosition );
	setTransform( m );
}

FPSGadget::~FPSGadget()
{
}

void FPSGadget::renderLayer( Gadget::Layer layer, const Style *style, Gadget::RenderReason reason ) const
{
	if( layer != Layer::Main )
	{
		return;
	}

	if( isSelectionRender( reason ) )
	{
		return;
	}

	// We keep a queue of times from recent frames that we will average over
	m_timeBuffer.push_back( std::chrono::high_resolution_clock::now() );

	if( m_timeBuffer.size() < 2 )
	{
		return;
	}

	int64_t elapsed = 0;
	while( true )
	{
		elapsed = std::chrono::duration_cast< std::chrono::microseconds >( m_timeBuffer.back() - m_timeBuffer.front() ).count();

		// Discard any time samples older than a second
		if( m_timeBuffer.size() > 2 && elapsed > 1000000 )
		{
			m_timeBuffer.pop_front();
		}
		else
		{
			break;
		}
	}

	// The average frame time is seconds from first measurement to last measurement, divided by number
	// of frames.  Frames happen in between measurements, so the number of frames is 1 less than the
	// size of m_timeBuffer.
	float averageFrameTime = elapsed / ( ( m_timeBuffer.size() - 1 ) * 1000000.0f );

	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	ViewportGadget::RasterScope rasterScope( viewportGadget );

	glMultMatrixf( getTransform().getValue() );
	glScalef( 8.0f, -8.0f, 8.0f );

	style->renderText( Style::LabelText, boost::str( boost::format( "%.1f FPS" ) % ( 1.0f / averageFrameTime ) ) );

}

unsigned FPSGadget::layerMask() const
{
	return (unsigned)Layer::Main;
}


Imath::Box3f FPSGadget::renderBound() const
{
	// we draw in raster space so don't have a sensible bound
	Imath::Box3f b;
	b.makeInfinite();
	return b;
}
