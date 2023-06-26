//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//	  * Redistributions of source code must retain the above
//		copyright notice, this list of conditions and the following
//		disclaimer.
//
//	  * Redistributions in binary form must reproduce the above
//		copyright notice, this list of conditions and the following
//		disclaimer in the documentation and/or other materials provided with
//		the distribution.
//
//	  * Neither the name of John Haddon nor the names of
//		any other contributors to this software may be used to endorse or
//		promote products derived from this software without specific prior
//		written permission.
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

#include "GafferImage/LookTransform.h"

#include "GafferImage/OpenColorIOAlgo.h"

#include "Gaffer/StringPlug.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( LookTransform );

size_t LookTransform::g_firstPlugIndex = 0;

LookTransform::LookTransform( const std::string &name )
		:   OpenColorIOTransform( name, true )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "look" ) );
	addChild( new IntPlug( "direction" ) );
}

LookTransform::~LookTransform()
{
}

Gaffer::StringPlug *LookTransform::lookPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *LookTransform::lookPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *LookTransform::directionPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *LookTransform::directionPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

bool LookTransform::affectsTransform( const Gaffer::Plug *input ) const
{
	return ( input == lookPlug() || input == directionPlug() );
}

void LookTransform::hashTransform( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	lookPlug()->hash( h );
	h.append( OpenColorIOAlgo::getWorkingSpace( context ) );
	directionPlug()->hash( h );
}

OCIO_NAMESPACE::ConstTransformRcPtr LookTransform::transform() const
{
	const string look( lookPlug()->getValue() );
	if( look.empty() )
	{
		return OCIO_NAMESPACE::ColorSpaceTransformRcPtr();
	}

	const std::string &workingSpace = OpenColorIOAlgo::getWorkingSpace( Context::current() );

	OCIO_NAMESPACE::LookTransformRcPtr transform = OCIO_NAMESPACE::LookTransform::Create();
	transform->setSrc( workingSpace.c_str() );
	transform->setLooks( look.c_str() );
	transform->setDst( workingSpace.c_str() );
	transform->setDirection( directionPlug()->getValue() == Forward ? OCIO_NAMESPACE::TRANSFORM_DIR_FORWARD : OCIO_NAMESPACE::TRANSFORM_DIR_INVERSE );

	return transform;
}
