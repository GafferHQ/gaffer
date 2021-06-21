//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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


#include "OpenImageIO/filter.h"


namespace GafferImage
{

inline Imath::Box2f FilterAlgo::filterSupport( const Imath::V2f &p, float dx, float dy, float filterWidth )
{
	return Imath::Box2f (
		p - 0.5f * filterWidth * Imath::V2f( dx, dy ),
		p + 0.5f * filterWidth * Imath::V2f( dx, dy ) );

}

inline Imath::V2f FilterAlgo::derivativesToAxisAligned( const Imath::V2f &p, const Imath::V2f &dpdx, const Imath::V2f &dpdy )
{
	float dxLength = dpdx.length();
	float dyLength = dpdy.length();

	float minLength;
	Imath::V2f majorVector;
	if( dxLength == 0 && dyLength == 0 )
	{
		minLength = 1.0f;
		majorVector = Imath::V2f(0.0f);
	}
	else if( dxLength > dyLength )
	{
		minLength = std::max( dyLength, 1.0f );
		majorVector = ( dpdx / dxLength ) * std::max( 0.0f, dxLength - minLength );
	}
	else
	{
		minLength = std::max( dxLength, 1.0f );
		majorVector = ( dpdy / dyLength ) * std::max( 0.0f, dyLength - minLength );
	}

	return Imath::V2f( minLength ) + Imath::V2f( fabs( majorVector.x ), fabs( majorVector.y ) );
}

}
