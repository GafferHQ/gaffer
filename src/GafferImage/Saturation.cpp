//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/Saturation.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( Saturation );

size_t Saturation::g_firstPlugIndex = 0;

Saturation::Saturation( const std::string &name )
	:	ColorProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FloatPlug( "saturation", Gaffer::Plug::In, 1.0f, 0.0f ) );
}

Saturation::~Saturation()
{
}

Gaffer::FloatPlug *Saturation::saturationPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex );
}

const Gaffer::FloatPlug *Saturation::saturationPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex );
}

bool Saturation::affectsColorProcessor( const Gaffer::Plug *input ) const
{
	return input == saturationPlug();
}

void Saturation::hashColorProcessor( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	saturationPlug()->hash( h );
}

ColorProcessor::ColorProcessorFunction Saturation::colorProcessor( const Gaffer::Context *context ) const
{
	const float saturation = saturationPlug()->getValue();
	if( saturation == 1.0f )
	{
		return ColorProcessorFunction();
	}

	return [saturation] ( IECore::FloatVectorData *rData, IECore::FloatVectorData *gData, IECore::FloatVectorData *bData )
	{
		std::vector<float> &r = rData->writable();
		std::vector<float> &g = gData->writable();
		std::vector<float> &b = bData->writable();

		for( int i = 0; i < ImagePlug::tilePixels(); i++ )
		{
			float lum = r[i] * 0.2126 + g[i] * 0.7152 + b[i] * 0.0722;
			r[i] = ( r[i] - lum ) * saturation + lum;
			g[i] = ( g[i] - lum ) * saturation + lum;
			b[i] = ( b[i] - lum ) * saturation + lum;
		}
	};
}
