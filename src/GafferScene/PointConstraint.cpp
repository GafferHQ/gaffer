//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/PointConstraint.h"

#include "OpenEXR/ImathMatrixAlgo.h"

using namespace Imath;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( PointConstraint );

size_t PointConstraint::g_firstPlugIndex = 0;

PointConstraint::PointConstraint( const std::string &name )
	:	Constraint( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new V3fPlug( "offset", Plug::In, V3f( 0, 0, 0 ) ) );
	addChild( new BoolPlug( "xEnabled", Plug::In, true ) );
	addChild( new BoolPlug( "yEnabled", Plug::In, true ) );
	addChild( new BoolPlug( "zEnabled", Plug::In, true ) );
}

PointConstraint::~PointConstraint()
{
}

Gaffer::V3fPlug *PointConstraint::offsetPlug()
{
	return getChild<Gaffer::V3fPlug>( g_firstPlugIndex );
}

const Gaffer::V3fPlug *PointConstraint::offsetPlug() const
{
	return getChild<Gaffer::V3fPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *PointConstraint::xEnabledPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *PointConstraint::xEnabledPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *PointConstraint::yEnabledPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *PointConstraint::yEnabledPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *PointConstraint::zEnabledPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *PointConstraint::zEnabledPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 3 );
}

bool PointConstraint::affectsConstraint( const Gaffer::Plug *input ) const
{
	return
		input->parent<Plug>() == offsetPlug() ||
		input == xEnabledPlug() ||
		input == yEnabledPlug() ||
		input == zEnabledPlug();
}

void PointConstraint::hashConstraint( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	offsetPlug()->hash( h );
	xEnabledPlug()->hash( h );
	yEnabledPlug()->hash( h );
	zEnabledPlug()->hash( h );
}

Imath::M44f PointConstraint::computeConstraint( const Imath::M44f &fullTargetTransform, const Imath::M44f &fullInputTransform, const Imath::M44f &inputTransform ) const
{
	const V3f worldPosition = fullTargetTransform.translation() + offsetPlug()->getValue();
	M44f result = fullInputTransform;

	if( xEnabledPlug()->getValue() )
	{
		result[3][0] = worldPosition[0];
	}

	if( yEnabledPlug()->getValue() )
	{
		result[3][1] = worldPosition[1];
	}

	if( zEnabledPlug()->getValue() )
	{
		result[3][2] = worldPosition[2];
	}

	return result;
}
