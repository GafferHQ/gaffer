##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import functools

import IECore

import Gaffer
import GafferUI

def commonFunctionMenu( command, activator ) :

	menuDefinition = IECore.MenuDefinition()

	for label, text in [

		( "/Math/Constants/Pi", "M_PI" ),
		( "/Math/Angles/Radians", "radians( angleInDegrees )" ),
		( "/Math/Angles/Degrees", "degrees( angleInRadians )" ),
		( "/Math/Trigonometry/Sin", "sin( angleInRadians )" ),
		( "/Math/Trigonometry/Cosine", "cos( angleInRadians )" ),
		( "/Math/Trigonometry/Tangent", "tan( angleInRadians )" ),
		( "/Math/Trigonometry/Arc Sin", "asin( y )" ),
		( "/Math/Trigonometry/Arc Cosine", "acos( x )" ),
		( "/Math/Trigonometry/Arc Tangent", "atan( yOverX )" ),
		( "/Math/Trigonometry/Arc Tangent 2", "atan2( y, x )" ),
		( "/Math/Exponents/Pow", "pow( x, y )" ),
		( "/Math/Exponents/Exp", "exp( x )" ),
		( "/Math/Exponents/Log", "log( x )" ),
		( "/Math/Exponents/Square Root", "sqrt( x )" ),
		( "/Math/Utility/Abs", "abs( x )" ),
		( "/Math/Utility/Sign", "sign( x )" ),
		( "/Math/Utility/Floor", "floor( x )" ),
		( "/Math/Utility/Ceil", "ceil( x )" ),
		( "/Math/Utility/Round", "round( x )" ),
		( "/Math/Utility/Trunc", "trunc( x )" ),
		( "/Math/Utility/Mod", "mod( x )" ),
		( "/Math/Utility/Min", "min( a, b )" ),
		( "/Math/Utility/Max", "max( a, b )" ),
		( "/Math/Utility/Clamp", "clamp( x, minValue, maxValue )" ),
		( "/Math/Utility/Mix", "mix( a, b, alpha )" ),
		( "/Math/Geometry/Dot", "dot( a, b )" ),

		( "/Geometry/Cross", "cross( a, b )" ),
		( "/Geometry/Length", "length( V )" ),
		( "/Geometry/Length", "distance( p0, p1 )" ),
		( "/Geometry/Normalize", "normalize( V )" ),
		( "/Geometry/Face Forward", "faceforward( N, I )" ),
		( "/Geometry/Reflect", "reflect( I, N )" ),
		( "/Geometry/Refract", "refract( I, N, eta )" ),
		( "/Geometry/Rotate", "rotate( p, angle, p0, p1 )" ),
		( "/Geometry/Transform", "transform( toSpace, p )" ),
		( "/Geometry/Transform", "transform( fromSpace, toSpace, p )" ),

		( "/Color/Luminance", "luminance( c )" ),
		( "/Color/BlackBody", "blackbody( degreesKelvin )" ),
		( "/Color/Wavelength Color", "wavelength_color( wavelengthNm )" ),
		( "/Color/Transform", "transformc( fromSpace, toSpace, c )" ),

		( "/Pattern/Step", "step( edge, x )" ),
		( "/Pattern/Linear Step", "linearstep( edge0, edge1, x )" ),
		( "/Pattern/Smooth Step", "smoothstep( edge0, edge1, x )" ),
		( "/Pattern/Noise", "noise( \"perlin\", p )" ),
		( "/Pattern/Periodic Noise", "noise( \"perlin\", p, period )" ),
		( "/Pattern/Cell Noise", "cellnoise( p )" ),

		( "/String/Length", "strlen( str )" ),
		( "/String/Format", "format( \"\", ... )" ),
		( "/String/Join", "concat( str0, str1 )" ),
		( "/String/Split", "split( str, results )" ),
		( "/String/Starts With", "startswith( str, prefix )" ),
		( "/String/Ends With", "endswith( str, suffix )" ),
		( "/String/Substring", "substr( str, start, length )" ),
		( "/String/Get Char", "getchar( str, n )" ),
		( "/String/Hash", "hash( str )" ),

		( "/Texture/Texture", "texture( filename, s, t )" ),
		( "/Texture/Environment", "environment( filename, R )" ),

		( "/Point Cloud/Search", "pointcloud_search( name, pos, radius, maxPoints /*, [sort,] attr, data, ..., attrN, dataN */ )" ),
		( "/Point Cloud/Get", "pointcloud_get( name, indices, count, attr, data )" ),

		( "/Parameter/Is Connected", "isconnected( parameter )" ),
		( "/Parameter/Is Constant", "isconstant( parameter )" ),

	] :

		menuDefinition.append(
			label,
			{
				"command" : functools.partial( command, text ),
				"active" : functools.partial( activator ),
			},
		)

	return menuDefinition
