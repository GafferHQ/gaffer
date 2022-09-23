//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFEROSL_SPLINE_H
#define GAFFEROSL_SPLINE_H

float floatSpline( float positions[], float values[], string basis, float x )
{
	// When using "constant" as the inverse basis, all the values being searched
	// are the same, so the search moves basically randomly.  In the rare case
	// that it comes within floating point precision of the next step, this can
	// cause us to incorrectly get a value for the next step.  It's a lot more
	// robust if we swap to a linear basis in this case, so we only approach the
	// edges when the X value is actually near the edge.
	string inversebasis = basis != "constant" ? basis : "linear";
	float t = splineinverse( inversebasis, x, positions  );
	return spline( basis, t, values );
}

color colorSpline( float positions[], color values[], string basis, float x )
{
	// As above
	string inversebasis = basis != "constant" ? basis : "linear";
	float t = splineinverse( inversebasis, x, positions  );
	return spline( basis, t, values );
}

#endif // GAFFEROSL_SPLINE_H
