//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/Frame.h"

#include "GafferUI/GraphGadget.h"
#include "GafferUI/Style.h"

#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/MeshPrimitive.h"

#include "IECore/SimpleTypedData.h"

using namespace GafferUI;
using namespace IECore;
using namespace IECoreScene;
using namespace Imath;
using namespace boost;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Frame );

Frame::Frame( GadgetPtr child )
	:	IndividualContainer( child ), m_border( 1 )
{
}

Frame::~Frame()
{
}

Imath::Box3f Frame::bound() const
{
	Imath::Box3f b = IndividualContainer::bound();
	if( b.isEmpty() )
	{
		return b;
	}
	b.max += V3f( m_border, m_border, 0 );
	b.min -= V3f( m_border, m_border, 0 );
	return b;
}

void Frame::doRenderLayer( Layer layer, const Style *style ) const
{
	if( layer != Layer::Main )
	{
		return;
	}

	Imath::Box3f b = IndividualContainer::bound();
	style->renderFrame( Box2f( V2f( b.min.x, b.min.y ), V2f( b.max.x, b.max.y ) ), m_border );
}

unsigned Frame::layerMask() const
{
	return (unsigned)Layer::Main;
}

Imath::Box3f Frame::renderBound() const
{
	return bound();
}
