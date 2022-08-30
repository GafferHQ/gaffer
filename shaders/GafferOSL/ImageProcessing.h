//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, John Haddon. All rights reserved.
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

#ifndef GAFFEROSL_IMAGEPROCESSING_H
#define GAFFEROSL_IMAGEPROCESSING_H

float inChannel( string channelName, float defaultValue )
{
	float result = defaultValue;
	getattribute( channelName, result );
	return result;
}

closure color outChannel( string channelName, float channelValue )
{
	// we store the value as an internal attribute of the closure, rather
	// than as an external weight, so that values of 0 are not optimised
	// away by OSL.
	return debug( channelName, "type", "float", "value", color( channelValue ) );
}

color inLayer( string layerName, color defaultValue )
{
	string redName = "R";
	string greenName = "G";
	string blueName = "B";
	if( layerName != "" )
	{
		redName = concat( layerName, ".", redName );
		greenName = concat( layerName, ".", greenName );
		blueName = concat( layerName, ".", blueName );
	}
	return color( inChannel( redName, defaultValue[0] ), inChannel( greenName, defaultValue[1] ), inChannel( blueName, defaultValue[2] ) );
}

closure color outLayer( string layerName, color layerColor )
{
	string redName = "R";
	string greenName = "G";
	string blueName = "B";
	if( layerName != "" )
	{
		redName = concat( layerName, ".", redName );
		greenName = concat( layerName, ".", greenName );
		blueName = concat( layerName, ".", blueName );
	}

	return outChannel( redName, layerColor[0] ) + outChannel( greenName, layerColor[1] ) + outChannel( blueName, layerColor[2] );
}


string gafferFilterToOiioFilter( string s )
{
	if( s == "gaussian" )
	{
		return "smartcubic";
	}
	else if( s == "disk" )
	{
		return "cubic";
	}
	else
	{
		return "linear";
	}
}

// TODO - figure out defaultValue
// TODO - figure out alpha
float pixel( string channelName, point p )
{
	return texture( concat( "gaffer:in.", channelName ), p[0] * Dx(u), p[1] * Dy(v), 0, 0, 0, 0, "interp", "closest" );
}

float pixelBilinear( string channelName, point p )
{
	return texture( concat( "gaffer:in.", channelName ), p[0] * Dx(u), p[1] * Dy(v), 0, 0, 0, 0, "interp", "bilinear" );
}

float pixelFiltered( string channelName, point p, float dx, float dy, string filter )
{
	return texture( concat( "gaffer:in.", channelName ), p[0] * Dx(u), p[1] * Dy(v),
		dx * Dx(u), 0, 0, dy * Dy(v), "interp", gafferFilterToOiioFilter( filter )
	);
}

float pixelFilteredWithDirections( string channelName, point p, vector dpdx, vector dpdy, string filter )
{
	return texture( concat( "gaffer:in.", channelName ), p[0] * Dx(u), p[1] * Dy(v),
		dpdx[0] * Dx(u), dpdx[1] * Dx(u), dpdy[0] * Dy(v), dpdy[1] * Dy(v),
		"interp", gafferFilterToOiioFilter( filter )
	);
}

color pixel( string layerName, point p )
{
	return texture( concat( "gaffer:in.", layerName ), p[0] * Dx(u), p[1] * Dy(v), 0, 0, 0, 0, "interp", "closest" );
}

color pixelBilinear( string layerName, point p )
{
	return texture( concat( "gaffer:in.", layerName ), p[0] * Dx(u), p[1] * Dy(v), 0, 0, 0, 0, "interp", "bilinear" );
}

color pixelFiltered( string layerName, point p, float dx, float dy, string filter )
{
	return texture( concat( "gaffer:in.", layerName ), p[0] * Dx(u), p[1] * Dy(v),
		dx * Dx(u), 0, 0, dy * Dy(v), "interp", gafferFilterToOiioFilter( filter )
	);
}

color pixelFilteredWithDirections( string layerName, point p, vector dpdx, vector dpdy, string filter )
{
	return texture( concat( "gaffer:in.", layerName ), p[0] * Dx(u), p[1] * Dy(v),
		dpdx[0] * Dx(u), dpdx[1] * Dx(u), dpdy[0] * Dy(v), dpdy[1] * Dy(v),
		"interp", gafferFilterToOiioFilter( filter )
	);
}

#endif // GAFFEROSL_IMAGEPROCESSING_H
