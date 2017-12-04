//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
#include "GafferUI/AuxiliaryConnectionGadget.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/Style.h"

#include "Gaffer/Plug.h"
#include "Gaffer/ScriptNode.h"

using namespace GafferUI;
using namespace Imath;

AuxiliaryConnectionGadget::AuxiliaryConnectionGadget( const NodeGadget *srcGadget, const NodeGadget *dstGadget )
	: Gadget(), m_srcGadget(srcGadget), m_dstGadget(dstGadget), m_toolTipValid(false)
{
}

AuxiliaryConnectionGadget::~AuxiliaryConnectionGadget()
{
}

Imath::Box3f AuxiliaryConnectionGadget::bound() const
{
	Box3f result;

	result.extendBy( V3f( 0 ) * m_srcGadget->fullTransform() );
	result.extendBy( V3f( 0 ) * m_dstGadget->fullTransform() );

	return result;
}

void AuxiliaryConnectionGadget::doRenderLayer( Layer layer, const Style *style ) const
{
	if( layer != GraphLayer::Connections )
	{
		return;
	}

	// Compute endpoint of line
	V3f source = V3f( 0 ) * m_srcGadget->fullTransform();
	V3f destination = V3f( 0 ) * m_dstGadget->fullTransform();
	V3f diff = source - destination;

	// Put the direction indicator on an ellipse encompassing the target NodeGadget
	// \todo The ellipse code should potentially live somewhere a little more global.
	Box3f targetBound = m_dstGadget->bound();
	V3f sizeOverTwo = (targetBound.max - targetBound.min ) * 0.5;

	float theta = atan2( diff.y, diff.x );

	float xRadius = sizeOverTwo.x * 1.25; // \todo Magic number that can be played with
	float wOverRadius = sizeOverTwo.x / xRadius;
	float yRadius = sizeOverTwo.y / sqrt( 1 - wOverRadius*wOverRadius  );

	// \todo There's some potential for further optimization here by ripping out the trig bits
	float tanTheta = tan( theta );
	float x = ( xRadius*yRadius ) / ( sqrt( yRadius*yRadius + xRadius*xRadius * ( tanTheta*tanTheta ) ) );
	float piOverTwo = M_PI * 0.5;
	x = -piOverTwo < theta && theta < piOverTwo ? x : -x;
	float y = x * tanTheta;

	x += destination.x;
	y += destination.y;

	style->renderAuxiliaryConnection( IECore::LineSegment3f( source, destination ), V2f( x, y ) );

}

int AuxiliaryConnectionGadget::removeConnection( const Gaffer::Plug *dstPlug )
{
	if( m_representedConnections.erase( dstPlug ) > 0 )
	{
		m_toolTipValid = false;
	}
	return m_representedConnections.size();
}

int AuxiliaryConnectionGadget::removeConnection( const Gaffer::Plug *srcPlug, const Gaffer::Plug *dstPlug )
{
	auto it = m_representedConnections.find( dstPlug );

	if( it == m_representedConnections.end() || (*it).second != srcPlug )
	{
		return m_representedConnections.size();
	}

	return removeConnection( dstPlug );
}

void AuxiliaryConnectionGadget::addConnection( const Gaffer::Plug *srcPlug, const Gaffer::Plug *dstPlug )
{
	if( !srcPlug || !m_srcGadget->node() || !m_srcGadget->node()->isAncestorOf( srcPlug ) )
	{
		// \todo throw? error?
		return;
	}

	if( !dstPlug || !m_dstGadget->node() || !m_dstGadget->node()->isAncestorOf( dstPlug ) )
	{
		// \todo throw? error?
		return;
	}

	// \todo Double check if these are actually living on the represented nodes.

	m_toolTipValid = false;
	m_representedConnections[dstPlug] = srcPlug;
}

bool AuxiliaryConnectionGadget::hasConnection( const Gaffer::Plug *srcPlug, const Gaffer::Plug *dstPlug ) const
{
	auto it = m_representedConnections.find( dstPlug );
	if( it != m_representedConnections.end() )
	{
		return (*it).second == srcPlug;
	}
	return false;
}

bool AuxiliaryConnectionGadget::empty() const
{
	return m_representedConnections.empty();
}

std::string AuxiliaryConnectionGadget::getToolTip( const IECore::LineSegment3f &position ) const
{
	if( m_toolTipValid )
	{
		return m_toolTip;
	}

	const Gaffer::ScriptNode *script = m_srcGadget->node()->ancestor<const Gaffer::ScriptNode>();

	m_toolTip = "<b>Connections</b>\n";
	for( const auto &pair : m_representedConnections )
	{
		m_toolTip += pair.second->relativeName( script ) + "->" + pair.first->relativeName( script ) + "\n";
	}
	m_toolTipValid = true;
	return m_toolTip;
}
