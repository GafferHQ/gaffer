//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFEROSL_GRADEUTILS_H
#define GAFFEROSL_GRADEUTILS_H

float floatBias( float bias, float c )
{
	float clamped = clamp( c, 0, 1 );
	float b = clamp( bias, 1e-4, 1 - 1e-4 );
    return clamped / ( ( 1 / b - 2 ) * (1 - clamped) + 1 );
}

color colorBias( color bias, color c )
{
	color clamped = clamp( c, 0, 1 );
	color b = clamp( bias, 1e-4, 1 - 1e-4 );
    return clamped / ( ( 1 / b - 2 ) * (1 - clamped) + 1 );
}

float floatGain( float gain, float t )
{
    float clampedGain = clamp(gain, .0001, .9999);
    float subCalc = ( 1 / clampedGain - 2 ) * ( 1 - 2 * t );
    if( t < .5 )
    {
        return t / (subCalc + 1);
    }
    else
    {
        return (subCalc - t) / (subCalc - 1);
    }
}

color colorGain( color gain, color c )
{
    return color(
        floatGain( gain[0], c[0] ),
        floatGain( gain[1], c[1] ),
        floatGain( gain[2], c[2] ) );
}

float floatBiasGain( float bias, float gain, float c )
{
    return floatGain( gain, floatBias(bias, clamp( c, 0, 1 ) ) );
}

color colorBiasGain( color bias, color gain, color c )
{
    return colorGain( gain, colorBias(bias, clamp( c, 0, 1 ) ) );
}

color colorRemap( color minIn, color maxIn, color minOut, color maxOut, color c )
{
    return (c - minIn) * (maxOut - minOut) / (maxIn - minIn) + minOut;
}

float floatRemap( float minIn, float maxIn, float minOut, float maxOut, float c )
{
    return (c - minIn) * (maxOut - minOut) / (maxIn - minIn) + minOut;
}

color colorSaturation( float sat, color c )
{
	float monochrome = ( c[0] + c[1] + c[2] ) * ( 1.0 / 3.0 );
	return ( c - monochrome ) * sat + monochrome;
}

#endif // GAFFEROSL_GRADEUTILS_H
