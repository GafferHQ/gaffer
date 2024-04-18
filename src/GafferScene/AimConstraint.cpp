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

#include "GafferScene/AimConstraint.h"

#include "Imath/ImathMatrixAlgo.h"

using namespace Imath;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( AimConstraint );

size_t AimConstraint::g_firstPlugIndex = 0;

AimConstraint::AimConstraint( const std::string &name )
	:	Constraint( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new V3fPlug( "aim", Plug::In, V3f( 0, 0, -1 ) ) );
	addChild( new V3fPlug( "up", Plug::In, V3f( 0, 1, 0 ) ) );
}

AimConstraint::~AimConstraint()
{
}

Gaffer::V3fPlug *AimConstraint::aimPlug()
{
	return getChild<Gaffer::V3fPlug>( g_firstPlugIndex );
}

const Gaffer::V3fPlug *AimConstraint::aimPlug() const
{
	return getChild<Gaffer::V3fPlug>( g_firstPlugIndex );
}

Gaffer::V3fPlug *AimConstraint::upPlug()
{
	return getChild<Gaffer::V3fPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::V3fPlug *AimConstraint::upPlug() const
{
	return getChild<Gaffer::V3fPlug>( g_firstPlugIndex + 1 );
}

bool AimConstraint::affectsConstraint( const Gaffer::Plug *input ) const
{
	return aimPlug()->isAncestorOf( input ) || upPlug()->isAncestorOf( input );
}

void AimConstraint::hashConstraint( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	aimPlug()->hash( h );
	upPlug()->hash( h );
}

Imath::M44f AimConstraint::computeConstraint( const Imath::M44f &fullTargetTransform, const Imath::M44f &fullInputTransform, const Imath::M44f &inputTransform ) const
{
	// decompose into scale, shear, rotate and translate
	V3f s( 1 ), h( 0 ), r( 0 ), t( 0 );
	extractSHRT( fullInputTransform, s, h, r, t );

	// figure out the aim matrix
	const V3f toDir = ( fullTargetTransform.translation() - t ).normalized();
	const M44f rotationMatrix = rotationMatrixWithUpDir( aimPlug()->getValue(), toDir, upPlug()->getValue() );

	// rebuild, replacing rotate with the aim matrix
	M44f result;
	result.translate( t );
	result.shear( h );
	result = rotationMatrix * result;
	result.scale( s );

	return result;
}
