//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/CDL.h"

#include "Gaffer/StringPlug.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( CDL );

size_t CDL::g_firstPlugIndex = 0;

CDL::CDL( const std::string &name )
	:	OpenColorIOTransform( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Color3fPlug( "slope", Plug::In, Imath::V3f( 1. ) ) );
	addChild( new Color3fPlug( "offset", Plug::In, Imath::V3f( 0. ) ) );
	addChild( new Color3fPlug( "power", Plug::In, Imath::V3f( 1. ) ) );
	addChild( new FloatPlug( "saturation", Plug::In, 1., 0. ) );

	addChild( new IntPlug(
		"direction", Plug::In,
		OCIO_NAMESPACE::TRANSFORM_DIR_FORWARD,
		OCIO_NAMESPACE::TRANSFORM_DIR_FORWARD,
		OCIO_NAMESPACE::TRANSFORM_DIR_INVERSE
	) );
}

CDL::~CDL()
{
}

Gaffer::Color3fPlug *CDL::slopePlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex );
}

const Gaffer::Color3fPlug *CDL::slopePlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex );
}

Gaffer::Color3fPlug *CDL::offsetPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::Color3fPlug *CDL::offsetPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 1 );
}

Gaffer::Color3fPlug *CDL::powerPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::Color3fPlug *CDL::powerPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 2 );
}

Gaffer::FloatPlug *CDL::saturationPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::FloatPlug *CDL::saturationPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

Gaffer::IntPlug *CDL::directionPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::IntPlug *CDL::directionPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 4 );
}

bool CDL::affectsTransform( const Gaffer::Plug *input ) const
{
	return(
		slopePlug()->isAncestorOf( input ) ||
		offsetPlug()->isAncestorOf( input ) ||
		powerPlug()->isAncestorOf( input ) ||
		input == saturationPlug() ||
		input == directionPlug()
	);
}

void CDL::hashTransform( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if(
		slopePlug()->isSetToDefault() &&
		offsetPlug()->isSetToDefault() &&
		powerPlug()->isSetToDefault() &&
		saturationPlug()->isSetToDefault()
	)
	{
		h = MurmurHash();
		return;
	}

	slopePlug()->hash( h );
	offsetPlug()->hash( h );
	powerPlug()->hash( h );
	saturationPlug()->hash( h );
	directionPlug()->hash( h );
}

OCIO_NAMESPACE::ConstTransformRcPtr CDL::transform() const
{
	OCIO_NAMESPACE::CDLTransformRcPtr result = OCIO_NAMESPACE::CDLTransform::Create();

	using Color3d = Imath::Color3<double>;
	result->setSlope( Color3d( slopePlug()->getValue() ).getValue() );
	result->setOffset( Color3d( offsetPlug()->getValue() ).getValue() );
	result->setPower( Color3d( powerPlug()->getValue() ).getValue() );
	result->setSat( saturationPlug()->getValue() );
	result->setDirection( (OCIO_NAMESPACE::TransformDirection)directionPlug()->getValue() );

	return result;
}
