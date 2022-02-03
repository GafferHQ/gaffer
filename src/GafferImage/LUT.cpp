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

#include "GafferImage/LUT.h"

#include "Gaffer/StringPlug.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( LUT );

size_t LUT::g_firstPlugIndex = 0;

LUT::LUT( const std::string &name )
	:	OpenColorIOTransform( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "fileName" ) );

	addChild( new IntPlug(
		"interpolation", Plug::In,
		Best,
		Best,
		Tetrahedral
	) );

	addChild( new IntPlug(
		"direction", Plug::In,
		Forward,
		Forward,
		Inverse
	) );

}

LUT::~LUT()
{
}

Gaffer::StringPlug *LUT::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *LUT::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *LUT::interpolationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *LUT::interpolationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *LUT::directionPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *LUT::directionPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

size_t LUT::supportedExtensions( std::vector<std::string> &extensions )
{
#if OCIO_VERSION_HEX > 0x02000000
	extensions.reserve( OCIO_NAMESPACE::FileTransform::GetNumFormats() );
	for( int i = 0; i < OCIO_NAMESPACE::FileTransform::GetNumFormats(); ++i )
	{
		extensions.push_back( OCIO_NAMESPACE::FileTransform::GetFormatExtensionByIndex( i ) );
	}
#else
	extensions.reserve( OpenColorIO::FileTransform::getNumFormats() );
	for( int i = 0; i < OpenColorIO::FileTransform::getNumFormats(); ++i )
	{
		extensions.push_back( OCIO_NAMESPACE::FileTransform::getFormatExtensionByIndex( i ) );
	}
#endif

	return extensions.size();
}

bool LUT::affectsTransform( const Gaffer::Plug *input ) const
{
	return ( input == fileNamePlug() || input == directionPlug() || input == interpolationPlug() );
}

void LUT::hashTransform( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( fileNamePlug()->getValue().empty() )
	{
		h = MurmurHash();
		return;
	}

	fileNamePlug()->hash( h );
	directionPlug()->hash( h );
	interpolationPlug()->hash( h );
}

OCIO_NAMESPACE::ConstTransformRcPtr LUT::transform() const
{
	std::string fileName = fileNamePlug()->getValue();

	// no need to run the processor if we don't
	// have a valid LUT file.
	if( fileName.empty() )
	{
		return OCIO_NAMESPACE::FileTransformRcPtr();
	}

	OCIO_NAMESPACE::FileTransformRcPtr result = OCIO_NAMESPACE::FileTransform::Create();
	result->setSrc( fileName.c_str() );

	switch( (Direction)directionPlug()->getValue() )
	{
		case Forward :
		{
			result->setDirection( OCIO_NAMESPACE::TRANSFORM_DIR_FORWARD );
			break;
		}
		case Inverse :
		{
			result->setDirection( OCIO_NAMESPACE::TRANSFORM_DIR_INVERSE );
			break;
		}
	}

	switch( (Interpolation)interpolationPlug()->getValue() )
	{
		case Best :
		{
			result->setInterpolation( OCIO_NAMESPACE::INTERP_BEST );
			break;
		}
		case Nearest :
		{
			result->setInterpolation( OCIO_NAMESPACE::INTERP_NEAREST );
			break;
		}
		case Linear :
		{
			result->setInterpolation( OCIO_NAMESPACE::INTERP_LINEAR );
			break;
		}
		case Tetrahedral :
		{
			result->setInterpolation( OCIO_NAMESPACE::INTERP_TETRAHEDRAL );
			break;
		}
	}

	return result;
}
