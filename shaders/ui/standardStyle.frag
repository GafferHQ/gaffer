//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#include "IECoreGL/FilterAlgo.h"
#include "IECoreGL/ColorAlgo.h"

uniform bool border;
uniform vec2 borderRadius;

uniform bool edgeAntiAliasing;

uniform bool useTexture;
uniform sampler2D texture;
	
void main()
{
	vec4 result = gl_Color;
	
	if( border )
	{
		vec2 v = max( borderRadius - gl_TexCoord[0].xy, vec2( 0.0 ) ) + max( gl_TexCoord[0].xy - vec2( 1.0 ) + borderRadius, vec2( 0.0 ) );
		v /= borderRadius;
		float r = length( v );
	
		result = mix( result, vec4( 0.05, 0.05, 0.05, result.a ), ieFilteredStep( 0.8, r ) );
		result.a *= ( 1.0 - ieFilteredStep( 1.0, r ) );
	}
	
	if( edgeAntiAliasing )
	{
		result.a *= ieFilteredPulse( 0.2, 0.8, gl_TexCoord[0].x );
	}
	
	if( useTexture )
	{
		result = texture2D( texture, gl_TexCoord[0].xy );
		result = vec4( ieLinToSRGB( result.r ), ieLinToSRGB( result.g ), ieLinToSRGB( result.b ), ieLinToSRGB( result.a ) );
	}
	
	gl_FragColor = result;

}

