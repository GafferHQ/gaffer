//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/ReflectionConstraint.h"

#include "Gaffer/StringPlug.h"

#include "IECore/AngleConversion.h"

#include "Imath/ImathMatrixAlgo.h"
#include "Imath/ImathVecAlgo.h"

using namespace std;
using namespace Imath;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( ReflectionConstraint );

size_t ReflectionConstraint::g_firstPlugIndex = 0;

ReflectionConstraint::ReflectionConstraint( const std::string &name )
	:	Constraint( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "camera" ) );
	addChild( new IntPlug( "distanceMode", Plug::In, (int)DistanceMode::Camera, (int)DistanceMode::Camera, (int)DistanceMode::Constant ) );
	addChild( new FloatPlug( "distance", Plug::In, 1.0f ) );
	addChild( new BoolPlug( "aimEnabled" ) );
	addChild( new V3fPlug( "aim", Plug::In, V3f( 0, 0, -1 ) ) );
	addChild( new V3fPlug( "up", Plug::In, V3f( 0, 1, 0 ) ) );
	addChild( new FloatPlug( "twist" ) );
}

ReflectionConstraint::~ReflectionConstraint()
{
}

Gaffer::StringPlug *ReflectionConstraint::cameraPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *ReflectionConstraint::cameraPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *ReflectionConstraint::distanceModePlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *ReflectionConstraint::distanceModePlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::FloatPlug *ReflectionConstraint::distancePlug()
{
	return getChild<Gaffer::FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *ReflectionConstraint::distancePlug() const
{
	return getChild<Gaffer::FloatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *ReflectionConstraint::aimEnabledPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *ReflectionConstraint::aimEnabledPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 3 );
}

Gaffer::V3fPlug *ReflectionConstraint::aimPlug()
{
	return getChild<Gaffer::V3fPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::V3fPlug *ReflectionConstraint::aimPlug() const
{
	return getChild<Gaffer::V3fPlug>( g_firstPlugIndex + 4 );
}

Gaffer::V3fPlug *ReflectionConstraint::upPlug()
{
	return getChild<Gaffer::V3fPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::V3fPlug *ReflectionConstraint::upPlug() const
{
	return getChild<Gaffer::V3fPlug>( g_firstPlugIndex + 5 );
}

Gaffer::FloatPlug *ReflectionConstraint::twistPlug()
{
	return getChild<Gaffer::FloatPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::FloatPlug *ReflectionConstraint::twistPlug() const
{
	return getChild<Gaffer::FloatPlug>( g_firstPlugIndex + 6 );
}

bool ReflectionConstraint::affectsConstraint( const Gaffer::Plug *input ) const
{
	return
		input == cameraPlug() ||
		input == inPlug()->existsPlug() ||
		input == inPlug()->transformPlug() ||
		input == distanceModePlug() ||
		input == distancePlug() ||
		input == aimEnabledPlug() ||
		input->parent() == aimPlug() ||
		input->parent() == upPlug() ||
		input == twistPlug()
	;
}

void ReflectionConstraint::hashConstraint( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const string camera = cameraPlug()->getValue();
	if( camera.empty() )
	{
		return;
	}

	ScenePlug::ScenePath cameraPath = ScenePlug::stringToPath( camera );
	if( !inPlug()->exists( cameraPath ) )
	{
		ignoreMissingTargetPlug()->hash( h );
		return;
	}

	h.append( inPlug()->fullTransformHash( cameraPath ) );
	distanceModePlug()->hash( h );
	distancePlug()->hash( h );
	aimEnabledPlug()->hash( h );
	aimPlug()->hash( h );
	upPlug()->hash( h );
	twistPlug()->hash( h );
}

Imath::M44f ReflectionConstraint::computeConstraint( const Imath::M44f &fullTargetTransform, const Imath::M44f &fullInputTransform, const Imath::M44f &inputTransform ) const
{
	// Get camera position

	const string camera = cameraPlug()->getValue();
	if( camera.empty() )
	{
		return fullTargetTransform;
	}

	ScenePlug::ScenePath cameraPath = ScenePlug::stringToPath( camera );
	if( !inPlug()->exists( cameraPath ) )
	{
		if( ignoreMissingTargetPlug()->getValue() )
		{
			return fullTargetTransform;
		}
		throw IECore::Exception( fmt::format( "Camera \"{}\" does not exist. Error may be suppressed using `ignoreMissingTarget`.", camera ) );
	}

	const M44f fullCameraTransform = inPlug()->fullTransform( cameraPath );

	// Get normal for the target.

	M44f normalTransform = fullTargetTransform.inverse();
	normalTransform.transpose();
	V3f targetNormal;
	normalTransform.multDirMatrix( V3f( 0, 1, 0 ), targetNormal );
	targetNormal.normalize();

	// Get reflected position

	const V3f viewVector = fullCameraTransform.translation() - fullTargetTransform.translation();
	V3f reflectionVector = reflect( viewVector, targetNormal );
	if( (DistanceMode)distanceModePlug()->getValue() == DistanceMode::Constant )
	{
		reflectionVector = reflectionVector.normalized() * distancePlug()->getValue();
	}
	const V3f translation = fullTargetTransform.translation() + reflectionVector;

	// Build constrained matrix.

	M44f result;
	if( !aimEnabledPlug()->getValue() )
	{
		// Aim off. Just clobber translation.
		result = fullInputTransform;
		result[3][0] = translation.x;
		result[3][1] = translation.y;
		result[3][2] = translation.z;
		return result;
	}
	else
	{
		// Aim enabled. Decompose input matrix and rebuild it
		// with the new translation and rotation.
		V3f s( 1 ), h( 0 ), r( 0 ), t( 0 );
		Imath::extractSHRT( fullInputTransform, s, h, r, t );
		const M44f rotationMatrix = rotationMatrixWithUpDir( aimPlug()->getValue(), -reflectionVector.normalized(), upPlug()->getValue() );
		result.translate( translation );
		result.shear( h );
		result = M44f().setAxisAngle( reflectionVector.normalized(), IECore::degreesToRadians( twistPlug()->getValue() ) ) * result;
		result = rotationMatrix * result;
		result.scale( s );
	}

	return result;
}
