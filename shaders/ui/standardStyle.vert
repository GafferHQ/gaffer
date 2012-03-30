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

uniform bool bezier;
uniform vec3 v0;
uniform vec3 v1;
uniform vec3 v2;
uniform vec3 v3;

void main()
{
	if( bezier )
	{
		mat4 basis = mat4(
			-1,  3, -3,  1,
			 3, -6,  3,  0,
			-3,  3,  0,  0,
			 1,  0,  0,  0
		);
		
		vec4 t = vec4(
			gl_MultiTexCoord0.y * gl_MultiTexCoord0.y * gl_MultiTexCoord0.y,
			gl_MultiTexCoord0.y * gl_MultiTexCoord0.y,
			gl_MultiTexCoord0.y,
			1.0		
		);
		
		vec4 tDeriv = vec4( t[1] * 3.0, t[2] * 2.0, 1.0, 0.0 );
		vec4 w = basis * t;
		vec4 wDeriv = basis * tDeriv;
		
		vec3 p = w.x * v0 + w.y * v1 + w.z * v2 + w.w * v3;
		vec3 vTangent = wDeriv.x * v0 + wDeriv.y * v1 + wDeriv.z * v2 + wDeriv.w * v3;
		
		vec4 camZ = gl_ModelViewMatrixInverse * vec4( 0.0, 0.0, -1.0, 0.0 );
		
		vec3 uTangent = normalize( cross( camZ.xyz, vTangent ) );
		
		p += 0.5 * uTangent * ( gl_MultiTexCoord0.x - 0.5 );
		
		gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * vec4( p, 1 );
	}
	else
	{
		gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;
	}
	gl_FrontColor = gl_Color;
	gl_BackColor = gl_Color;
	gl_TexCoord[0] = gl_MultiTexCoord0;
}
