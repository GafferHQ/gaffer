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

#include "GafferImage/Sampler.h"

namespace GafferImage
{

template< typename F >
void Reformat::reformat( const std::string &channelName, const Imath::V2i &tileOrigin, std::vector<float> &out ) const
{
	Imath::Box2i tile( tileOrigin, Imath::V2i( tileOrigin.x + ImagePlug::tileSize() - 1, tileOrigin.y + ImagePlug::tileSize() - 1 ) );
	Format inFormat( inPlug()->formatPlug()->getValue() );
	Format outFormat( formatPlug()->getValue() );
	Imath::V2i inWH = Imath::V2i( inFormat.getDisplayWindow().max ) + Imath::V2i(1);
	Imath::V2i outWH = Imath::V2i( outFormat.getDisplayWindow().max ) + Imath::V2i(1);
	Imath::V2d scale( double( outWH.x ) / ( inWH.x ), double( outWH.y ) / inWH.y );
	
	Imath::Box2d inputBoxd(
		Imath::V2d( double( tile.min.x ) / scale.x, double( tile.min.y ) / scale.y ),
		Imath::V2d( double( tile.max.x ) / scale.x, double( tile.max.y ) / scale.y )
	);
	
	Sampler sampler( inPlug(), channelName );
	
	F filter( scale.x < 1. ? 1./scale.x : 1. );
	
	// Filter in the x direction first.
	double stepX = 1./scale.x;
	double stepY = 1./scale.y;
	double ty = inputBoxd.min.y+.5;
	for( int y = tile.min.y; y <= tile.max.y; y++, ty += stepY )
	{
		float *dOut = &(out[0]) + ( y - tileOrigin.y ) * ImagePlug::tileSize() + (tile.min.x - tileOrigin.x);
		double tx = inputBoxd.min.x+.5;
		for ( int x = tile.min.x; x <= tile.max.x; x++, tx += stepX )
		{
			*dOut++ = sampler.sample( filter, float(tx), float(ty) );
		}	
	}
}

}; // namespace GafferImage

