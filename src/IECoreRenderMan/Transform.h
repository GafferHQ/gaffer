//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#pragma once

#include "Imath/ImathMatrix.h"

#include "Riley.h"

namespace IECoreRenderMan
{

/// Utility to aid in passing a static transform to Riley.
struct StaticTransform : riley::Transform
{

	/// Caution : `m` is referenced directly, and must live until the
	/// StaticTransform is passed to Riley.
	StaticTransform( const Imath::M44f &m )
		:	m_time( 0 )
	{
		samples = 1;
		matrix = &reinterpret_cast<const RtMatrix4x4 &>( m );
		time = &m_time;
	}

	private :

		float m_time;

};

/// Utility to aid in passing an animated transform to Riley.
struct AnimatedTransform : riley::Transform
{

	/// Caution : `transformSamples` and `sampleTimes` are referenced
	/// directly, and must live until the AnimatedTransform is passed to Riley.
	AnimatedTransform( const std::vector<Imath::M44f> &transformSamples, const std::vector<float> &sampleTimes )
	{
		samples = transformSamples.size();
		matrix = reinterpret_cast<const RtMatrix4x4 *>( transformSamples.data() );
		time = sampleTimes.data();
	}

};

/// Utility for passing an identity transform to Riley.
struct IdentityTransform : riley::Transform
{

	IdentityTransform()
		:	m_time( 0.0f )
	{
		samples = 1;
		matrix = reinterpret_cast<const RtMatrix4x4 *>( m_matrix.getValue() );
		time = &m_time;
	}

	private :

		const float m_time;
		const Imath::M44f m_matrix;

};


} // namespace IECoreRenderMan
