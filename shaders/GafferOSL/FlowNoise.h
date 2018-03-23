/// Original notice:
 
/*
 * srdnoise23, Simplex noise with rotating gradients
 * and a true analytic derivative in 2D and 3D.
 *
 * This is version 2 of srdnoise23 written in early 2008.
 * A stupid bug was corrected. Do not use earlier versions.
 *
 * Author: Stefan Gustavson, 2003-2008
 *
 * Contact: stefan.gustavson@gmail.com
 *
 * This code was GPL licensed until February 2011.
 * As the original author of this code, I hereby
 * release it into the public domain.
 * Please feel free to use it for whatever you want.
 * Credit is appreciated where appropriate, and I also
 * appreciate being told where this code finds any use,
 * but you may do as you like.
 */

// This was cobbled together by Daniel Dresser in 2018 from 3 sources,
// all of which are public domain.  These are the original C srdnoise23
// by Stefan Gustavson, the OSL port by Ivan Mavrov ( which nicely cleaned
// things up for OSL, but only ported the 3D version, and introduced a
// bug ), and the OSL port by Michel Anders ( with an API that less suited
// my needs, but included both 2D and 3D versions ).

// Ivan and Michel's header info is below.  The result of mashing together
// these 3 public domain sources is also public domain.

// I also added in some branches for the periodic case - this is a bit
// hacky and unoptimized, but seems to work OK ( with limitations on period
// and some extra skewing ), and it does seem like  there could be some
// cool things to do with periodic flow noise if you ever wanted to bake
// out an animated tiling texture.
 
// ====================================================================== 
/// Translated and modified by Ivan Mavrov, Chaos Group Ltd. 2016
/// Contact: ivan.mavrov@chaosgroup.com

/// OSL port Michel Anders (varkenvarken) 2013-02-04
/// original comment is is left mostly in place, OSL specific comments
/// are preceded by MJA
// ====================================================================== 

#ifndef IERENDERING_FLOWNOISE_H
#define IERENDERING_FLOWNOISE_H

#define DECLARE_PERM int perm[512] = {\
	151,160,137,91,90,15,\
	131,13,201,95,96,53,194,233,7,225,140,36,103,30,69,142,8,99,37,240,21,10,23,\
	190, 6,148,247,120,234,75,0,26,197,62,94,252,219,203,117,35,11,32,57,177,33,\
	88,237,149,56,87,174,20,125,136,171,168, 68,175,74,165,71,134,139,48,27,166,\
	77,146,158,231,83,111,229,122,60,211,133,230,220,105,92,41,55,46,245,40,244,\
	102,143,54, 65,25,63,161, 1,216,80,73,209,76,132,187,208, 89,18,169,200,196,\
	135,130,116,188,159,86,164,100,109,198,173,186, 3,64,52,217,226,250,124,123,\
	5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,16,58,17,182,189,28,42,\
	223,183,170,213,119,248,152, 2,44,154,163, 70,221,153,101,155,167, 43,172,9,\
	129,22,39,253, 19,98,108,110,79,113,224,232,178,185, 112,104,218,246,97,228,\
	251,34,242,193,238,210,144,12,191,179,162,241, 81,51,145,235,249,14,239,107,\
	49,192,214, 31,181,199,106,157,184, 84,204,176,115,121,50,45,127, 4,150,254,\
	138,236,205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180,\
	151,160,137,91,90,15,\
	131,13,201,95,96,53,194,233,7,225,140,36,103,30,69,142,8,99,37,240,21,10,23,\
	190, 6,148,247,120,234,75,0,26,197,62,94,252,219,203,117,35,11,32,57,177,33,\
	88,237,149,56,87,174,20,125,136,171,168, 68,175,74,165,71,134,139,48,27,166,\
	77,146,158,231,83,111,229,122,60,211,133,230,220,105,92,41,55,46,245,40,244,\
	102,143,54, 65,25,63,161, 1,216,80,73,209,76,132,187,208, 89,18,169,200,196,\
	135,130,116,188,159,86,164,100,109,198,173,186, 3,64,52,217,226,250,124,123,\
	5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,16,58,17,182,189,28,42,\
	223,183,170,213,119,248,152, 2,44,154,163, 70,221,153,101,155,167, 43,172,9,\
	129,22,39,253, 19,98,108,110,79,113,224,232,178,185, 112,104,218,246,97,228,\
	251,34,242,193,238,210,144,12,191,179,162,241, 81,51,145,235,249,14,239,107,\
	49,192,214, 31,181,199,106,157,184, 84,204,176,115,121,50,45,127, 4,150,254,\
	138,236,205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180 };

// Returns a flow noise value
// position : position to evaluate at
// flow     : the rotation to evaluate at ( usually connected to time )
// period   : if non-zero, the noise will wrap with this period.  MUST be a multiple of 3.
// dNoise   : returns the derivative of the noise
float simplexFlowNoise3D(point position, float flow, int period, output vector dNoise)
{
	DECLARE_PERM
 
	// Gradient component that leads to a vector of length sqrt(2).
	// float a = sqrt(2)/sqrt(3);
	float a = 0.81649658;
	 
	vector gradientUBase[16] = {
		vector( 1.0,  0.0,  1.0), vector( 0.0,  1.0,  1.0),
		vector(-1.0,  0.0,  1.0), vector( 0.0, -1.0,  1.0),
		vector( 1.0,  0.0, -1.0), vector( 0.0,  1.0, -1.0),
		vector(-1.0,  0.0, -1.0), vector( 0.0, -1.0, -1.0),
		vector( a,  a,  a), vector(-a,  a, -a),
		vector(-a, -a,  a), vector( a, -a, -a),
		vector(-a,  a,  a), vector( a, -a,  a),
		vector( a, -a, -a), vector(-a,  a, -a)
	};
 
	vector gradientVBase[16] = {
		vector(-a,  a,  a), vector(-a, -a,  a),
		vector( a, -a,  a), vector( a,  a,  a),
		vector(-a, -a, -a), vector( a, -a, -a),
		vector( a,  a, -a), vector(-a,  a, -a),
		vector( 1.0, -1.0,  0.0), vector( 1.0,  1.0,  0.0),
		vector(-1.0,  1.0,  0.0), vector(-1.0, -1.0,  0.0),
		vector( 1.0,  0.0,  1.0), vector(-1.0,  0.0,  1.0),
		vector( 0.0,  1.0, -1.0), vector( 0.0, -1.0, -1.0)
	};
	 
	// Helper function to compute the rotated gradient.
	vector getGradient(int index, float sinTheta, float cosTheta) {
		int safeIndex = index % 16;
		vector gradientU = gradientUBase[safeIndex];
		vector gradientV = gradientVBase[safeIndex];
		return cosTheta * gradientU + sinTheta * gradientV;
	}
	 
	// Skewing factors for the 3D simplex grid.
	// float F3 = 1.0 / 3.0;
	// float G3 = 1.0 / 6.0;
	float F3 = 0.333333333;
	float G3 = 0.166666667;
	float G3a = 2.0 * G3;
	float G3b = 3.0 * G3 - 1.0;
 
	// Skew the input space to determine the simplex cell we are in.
	float skew = (position[0] + position[1] + position[2]) * F3;
	point skewedPosition = position + skew;
	point skewedCellOrigin = floor(skewedPosition);
 
	// Unskew the cell origin
	float unskew = (skewedCellOrigin[0] + skewedCellOrigin[1] + skewedCellOrigin[2]) * G3;
	point cellOrigin = skewedCellOrigin - unskew;
	 
	// The offset from the cell's origin a.k.a point 0
	vector offset0 = position - cellOrigin;
 
	// The second point offset from the cell origin in skewed space.
	vector skewedOffset1;
	// The third point offset from the cell origin in skewed space.
	vector skewedOffset2;
 
	if (offset0[0] >= offset0[1]) {
		if (offset0[1] >= offset0[2]) {
			// X Y Z order
			skewedOffset1 = vector(1, 0, 0);
			skewedOffset2 = vector(1, 1, 0);
		} else if (offset0[0] >= offset0[2]) {
			// X Z Y order
			skewedOffset1 = vector(1, 0, 0);
			skewedOffset2 = vector(1, 0, 1);
		} else {
			// Z X Y order
			skewedOffset1 = vector(0, 0, 1);
			skewedOffset2 = vector(1, 0, 1);
		}
	} else {
		if (offset0[1] < offset0[2]) {
			// Z Y X order
			skewedOffset1 = vector(0, 0, 1);
			skewedOffset2 = vector(0, 1, 1);
		} else if (offset0[0] < offset0[2]) {
			// Y Z X order
			skewedOffset1 = vector(0, 1, 0);
			skewedOffset2 = vector(0, 1, 1);
		} else {
			// Y X Z order
			skewedOffset1 = vector(0, 1, 0);
			skewedOffset2 = vector(1, 1, 0);
		}
	}
 
	// A step of (1, 0, 0) in skewed space means a step of (1 - G3, -G3, -G3) in regular space.
	// A step of (0, 1, 0) in skewed space means a step of (-G3, 1 - G3, -G3) in regular space.
	// A step of (0, 0, 1) in skewed space means a step of (-G3, -G3, 1 - G3) in regular space.
 
	// The offset from point 1 in regular space.
	vector offset1 = offset0 - skewedOffset1 + G3;
	 
	// The offset from point 2 in regular space.
	vector offset2 = offset0 - skewedOffset2 + G3a;
 
	// The offset from point 3 in regular space.
	vector offset3 = offset0 + G3b;
 
	// Wrap the integer indices at 256, to avoid indexing perm[] out of bounds.
	int i0 = int(skewedCellOrigin[0]) & 255;
	int j0 = int(skewedCellOrigin[1]) & 255;
	int k0 = int(skewedCellOrigin[2]) & 255;

	int i1 = i0 + int(skewedOffset1[0]);
	int j1 = j0 + int(skewedOffset1[1]);
	int k1 = k0 + int(skewedOffset1[2]);

	int i2 = i0 + int(skewedOffset2[0]);
	int j2 = j0 + int(skewedOffset2[1]);
	int k2 = k0 + int(skewedOffset2[2]);

	int i3 = i0 + 1;
	int j3 = j0 + 1;
	int k3 = k0 + 1;

	if( period )
	{
		// For periodic noise, we need to wrap the cell locations around, by unskewing them, wrapping them,
		// then reskewing them.
		
		float fPeriod = period;

		// Used to make sure that values on the upper border are consistently wrapped down
		float epsilon = 0.00001 * abs( max( max( cellOrigin[0], cellOrigin[1] ), cellOrigin[2] ) );

		point wrappedCellOrigin0 = mod( mod( cellOrigin, fPeriod ), fPeriod - epsilon );
		float reskew0 = dot( 1, wrappedCellOrigin0 ) * F3;
		point skewedWrappedCellOrigin0 = round( wrappedCellOrigin0 + reskew0 );
		i0 = int(skewedWrappedCellOrigin0[0]) & 255;
		j0 = int(skewedWrappedCellOrigin0[1]) & 255;
		k0 = int(skewedWrappedCellOrigin0[2]) & 255;

		point wrappedCellOrigin1 = mod( mod( cellOrigin + ( skewedOffset1 - G3 ), fPeriod ), fPeriod - epsilon );
		float reskew1 = dot( 1, wrappedCellOrigin1 ) * F3;
		point skewedWrappedCellOrigin1 = round( wrappedCellOrigin1 + reskew1 );
		i1 = int(skewedWrappedCellOrigin1[0]) & 255;
		j1 = int(skewedWrappedCellOrigin1[1]) & 255;
		k1 = int(skewedWrappedCellOrigin1[2]) & 255;

		point wrappedCellOrigin2 = mod( mod( cellOrigin + ( skewedOffset2 - G3a ), fPeriod ), fPeriod - epsilon );
		float reskew2 = dot( 1, wrappedCellOrigin2 ) * F3;
		point skewedWrappedCellOrigin2 = round( wrappedCellOrigin2 + reskew2 );
		i2 = int(skewedWrappedCellOrigin2[0]) & 255;
		j2 = int(skewedWrappedCellOrigin2[1]) & 255;
		k2 = int(skewedWrappedCellOrigin2[2]) & 255;

		point wrappedCellOrigin3 = mod( mod( cellOrigin - G3b, fPeriod ), fPeriod - epsilon );
		float reskew3 = dot( 1, wrappedCellOrigin3 ) * F3;
		point skewedWrappedCellOrigin3 = round( wrappedCellOrigin3 + reskew3 );
		i3 = int(skewedWrappedCellOrigin3[0]) & 255;
		j3 = int(skewedWrappedCellOrigin3[1]) & 255;
		k3 = int(skewedWrappedCellOrigin3[2]) & 255;
	}
	 
	// Sine and cosine for the gradient rotation angle.
	float sinTheta = 0.0;
	float cosTheta = 0.0;
	sincos(M_2PI * flow, sinTheta, cosTheta);
	 
	// Calculate the contribution from the four points.
	float t0 = 0.6 - dot(offset0, offset0);
	float t02 = 0.0;
	float t04 = 0.0;
	vector gradient0 = vector(0.0);
	float n0 = 0;
	if (t0 < 0.0) {
		t0 = 0.0;
	} else {
		t02 = t0 * t0;
		t04 = t02 * t02;
		gradient0 = getGradient(perm[i0 + perm[j0 + perm[k0]]], sinTheta, cosTheta);
		n0 = t04 * dot(gradient0, offset0);
	}
 
	float t1 = 0.6 - dot(offset1, offset1);
	float t12 = 0.0;
	float t14 = 0.0;
	vector gradient1 = vector(0.0);
	float n1 = 0;
	if (t1 < 0.0) {
		t1 = 0.0;
	} else {
		t12 = t1 * t1;
		t14 = t12 * t12;
		gradient1 = getGradient(perm[i1 + perm[j1 + perm[k1]]], sinTheta, cosTheta);
		n1 = t14 * dot(gradient1, offset1);
	}
 
	float t2 = 0.6 - dot(offset2, offset2);
	float t22 = 0.0;
	float t24 = 0.0;
	vector gradient2 = vector(0.0);
	float n2 = 0;
	if(t2 < 0.0) {
		t2 = 0.0;
	} else {
		t22 = t2 * t2;
		t24 = t22 * t22;
		gradient2 = getGradient(perm[i2 + perm[j2 + perm[k2]]], sinTheta, cosTheta);
		n2 = t24 * dot(gradient2, offset2);
	}
	 
	float t3 = 0.6 - dot(offset3, offset3);
	float t32 = 0.0;
	float t34 = 0.0;
	vector gradient3 = vector(0.0);
	float n3 = 0;
	if(t3 < 0.0) {
		t32 = 0.0;
	} else {
		t32 = t3 * t3;
		t34 = t32 * t32;
		gradient3 = getGradient(perm[i3 + perm[j3 + perm[k3]]], sinTheta, cosTheta);
		n3 = t34 * dot(gradient3, offset3);
	}
 
	// Accumulate the contributions from each point to get the final noise value.
	// The result is scaled to return values in the range [-1,1].
	float noiseValue = 28.0 * (n0 + n1 + n2 + n3);

	// Compute noise derivative.
	//
	// Daniel : Note that ivan's port applied this multipy by -8 to the final term in the equation as
	// well.  This was not done in Stefan's original, and appears to have been an error
	dNoise  = -8 * t02 * t0 * offset0 * dot(gradient0, offset0) + t04 * gradient0;
	dNoise += -8 * t12 * t1 * offset1 * dot(gradient1, offset1) + t14 * gradient1;
	dNoise += -8 * t22 * t2 * offset2 * dot(gradient2, offset2) + t24 * gradient2;
	dNoise += -8 * t32 * t3 * offset3 * dot(gradient3, offset3) + t34 * gradient3;  
	 
	// Scale noise derivative to match the noise scaling.
	dNoise *= 28.0;
	 
	return noiseValue;
}

// Returns a flow noise value
// position : position to evaluate at
// flow     : the rotation to evaluate at ( usually connected to time )
// period   : if non-zero, the noise will wrap with this period.  Introduces
//            some skew so that a cell center lands on every corner of the
//            periodic region
// dNoise   : returns the derivative of the noise
float simplexFlowNoise2D(point position, float flow, int period, output vector dNoise)
{
	DECLARE_PERM

	// Gradient tables. These could be programmed the Ken Perlin way with
	// some clever bit-twiddling, but this is more clear, and not really slower.
	vector grad2[8] = {
		vector( -1.0, -1.0 , 0.0), vector( 1.0, 0.0 , 0.0) , vector( -1.0, 0.0 , 0.0) , vector( 1.0, 1.0 , 0.0) ,
		vector( -1.0, 1.0 , 0.0) , vector( 0.0, -1.0 , 0.0) , vector( 0.0, 1.0 , 0.0) , vector( 1.0, -1.0 , 0.0)
	};

	// Helper function to compute the rotated gradient.
    vector getGradient2( int hash, float sinTheta, float cosTheta )
    {
        int h = hash & 7;
        vector g = grad2[h];
        return vector ( cosTheta * g[0] - sinTheta * g[1], sinTheta * g[0] + cosTheta * g[1], 0 );
    }

	// Skewing factors for 2D simplex grid:
	// F2 = 0.5*(sqrt(3.0)-1.0)
	// G2 = (3.0-Math.sqrt(3.0))/6.0
	float F2 = 0.366025403;
	float G2 = 0.211324865;



	vector diag = vector( 1, 1, 0 );

	point noisePosition = point( position[0], position[1], 0 );
	float periodicSkewFactor;
	float periodicUnskewFactor;
	if( period != 0 )
	{
		// In order to make the noise periodic, we need the length of the diagonal to be an exact integer
		// number of cells, with the parity matching the parity of the period.
		//
		// We apply an extra pre-skew to the noise coordinates to fit to the closest diagonal length where
		// this is true.  This is a pretty extreme distortion for low periods, but for periods 3 and higher,
		// it's not too bad
		float diagonalCellCount = float( period ) * ( 1 + 2 * F2 );

		float parity = period % 2;
		float roundedCellCount = 2 * round( 0.5 * ( diagonalCellCount - parity ) ) + parity;

		float periodicPreSkew = 0.5 * ( roundedCellCount / diagonalCellCount - 1 );
		noisePosition += diag * periodicPreSkew * ( position[0] + position[1] );

		periodicSkewFactor = F2 + ( 2 * F2 + 1 ) * periodicPreSkew;
		periodicUnskewFactor = 0.5 * ( 2 * periodicSkewFactor / ( 1 + 2 * periodicSkewFactor ) );
	}

	// Skew the input space to determine which simplex cell we're in
	float skew = ( noisePosition[0] + noisePosition[1] ) * F2; // Hairy factor for 2D
	point skewedPosition = noisePosition + skew * diag;

	// Unskew the cell origin
	point skewedCellOrigin = floor( skewedPosition );
	float unskew = ( skewedCellOrigin[0] + skewedCellOrigin[1] ) * G2;
	point cellOrigin = skewedCellOrigin - unskew * diag;

	// The offset from the cell's origin a.k.a point 0
	vector offset0 = noisePosition - cellOrigin;

	// For the 2D case, the simplex shape is an equilateral triangle.
	// Determine which simplex we are in.
	vector skewedOffset;
	if( offset0[0] > offset0[1] )
	{
		// lower triangle, XY order: (0,0)->(1,0)->(1,1)
		skewedOffset = vector( 1, 0, 0 );
	}
	else
	{
		// upper triangle, YX order: (0,0)->(0,1)->(1,1)
		skewedOffset = vector( 0, 1, 0 );
	}

	// A step of (1,0) in skewed space means a step of (1-c,-c) in regular space, and
	// a step of (0,1) in skewed space means a step of (-c,1-c) in regular space, where
	// c = (3-sqrt(3))/6   

	vector offset1 = offset0 - skewedOffset + G2 * diag;
	vector offset2 = offset0 + ( -1 + 2 * G2 ) * diag;


	// Wrap the integer indices at 256, to avoid indexing perm[] out of bounds 
	int i0 = int(skewedCellOrigin[0]) & 255; // MJA was % 256 but OSL mod is not the same as C %
	int j0 = int(skewedCellOrigin[1]) & 255;

	int i1 = i0 + int(skewedOffset[0]);
	int j1 = j0 + int(skewedOffset[1]);

	int i2 = i0 + 1;
	int j2 = j0 + 1;

	if( period )
	{
		// For periodic noise, we need to wrap the cell locations around.  This is a bit painful, because
		// we need to wrap them in the original space, but they have been doubly skewed ( both by the periodic
		// adjustment to align with the boundary, and by the simplex noise skew ).
		// For this reason, we computed periodicUnskewFactor and periodicSkewFactor, now we just have to apply them
		float fPeriod = period;

		// Used to make sure that values on the upper border are consistently wrapped down
		float epsilon = 0.00001;

		point rawCellOrigin0 = skewedCellOrigin - periodicUnskewFactor * dot( diag, skewedCellOrigin ) * diag;
		point wrappedCellOrigin0 = mod( mod( rawCellOrigin0, fPeriod ), fPeriod - epsilon );
		float reskew0 = ( wrappedCellOrigin0[0] + wrappedCellOrigin0[1] ) * periodicSkewFactor;
		point skewedWrappedCellOrigin0 = round( wrappedCellOrigin0 + reskew0 * diag );
		i0 = int(skewedWrappedCellOrigin0[0]) & 255;
		j0 = int(skewedWrappedCellOrigin0[1]) & 255;

		point skewedCellOrigin1 = round( skewedCellOrigin + skewedOffset );
		point rawCellOrigin1 = skewedCellOrigin1 - periodicUnskewFactor * dot( diag, skewedCellOrigin1 ) * diag;
		point wrappedCellOrigin1 = mod( mod( rawCellOrigin1, fPeriod ), fPeriod - epsilon );
		float reskew1 = ( wrappedCellOrigin1[0] + wrappedCellOrigin1[1] ) * periodicSkewFactor;
		point skewedWrappedCellOrigin1 = round( wrappedCellOrigin1 + reskew1 * diag );
		i1 = int(skewedWrappedCellOrigin1[0]) & 255;
		j1 = int(skewedWrappedCellOrigin1[1]) & 255;

		point skewedCellOrigin2 = round( skewedCellOrigin + vector( 1, 1, 0 ) );
		point rawCellOrigin2 = skewedCellOrigin2 - periodicUnskewFactor * dot( diag, skewedCellOrigin2 ) * diag;
		point wrappedCellOrigin2 = mod( mod( rawCellOrigin2, fPeriod ), fPeriod - epsilon );
		float reskew2 = ( wrappedCellOrigin2[0] + wrappedCellOrigin2[1] ) * periodicSkewFactor;
		point skewedWrappedCellOrigin2 = round( wrappedCellOrigin2 + reskew2 * diag );
		i2 = int(skewedWrappedCellOrigin2[0]) & 255;
		j2 = int(skewedWrappedCellOrigin2[1]) & 255;
	}

	// Sine and cosine for the gradient rotation angle.
	float sinTheta = 0.0;
	float cosTheta = 0.0;
	sincos(M_2PI * flow, sinTheta, cosTheta);

	// Calculate the contribution from the three corners 
	float t0 = 0.5 - dot( offset0, offset0 );
	float t20 = 0;
	float t40 = 0;
	vector gradient0 = 0;
	float n0 = 0;
	if( t0 < 0.0 )
	{
		t0 = 0.0; // No influence
	}
	else
	{
		gradient0 = getGradient2( perm[i0 + perm[j0]], sinTheta, cosTheta );
		t20 = t0 * t0;
		t40 = t20 * t20;
		n0 = t40 * dot( gradient0, offset0 );
	}

	float t1 = 0.5 - dot( offset1, offset1 );
	float t21 = 0;
	float t41 = 0;
	vector gradient1 = 0;
	float n1 = 0;
	if( t1 < 0.0 )
	{
		t1 = 0.0; // No influence
	}
	else {
		gradient1 = getGradient2( perm[i1 + perm[j1]], sinTheta, cosTheta );
		t21 = t1 * t1;
		t41 = t21 * t21;
		n1 = t41 * dot( gradient1, offset1 );
	}

	float t2 = 0.5 - dot( offset2, offset2 );
	float t22 = 0;
	float t42 = 0;
	vector gradient2 = 0;
	float n2 = 0;
	if( t2 < 0.0 )
	{
		t2 = 0.0; // No influence
	}
	else {
		gradient2 = getGradient2( perm[i2 + perm[j2]], sinTheta, cosTheta );
		t22 = t2 * t2;
		t42 = t22 * t22;
		n2 = t42 * dot( gradient2, offset2 );
	}

	// Add contributions from each corner to get the final noise value.
	// The result is scaled to return values in the interval [-1,1].
	float noiseValue = 70.0 * ( n0 + n1 + n2 ); // MJA scale factor was 40

	// Compute noise derivative
	dNoise = -8 * t20 * t0 * offset0 * dot( gradient0, offset0 ) + t40 * gradient0;
	dNoise += -8 * t21 * t1 * offset1 * dot( gradient1, offset1 ) + t41 * gradient1;
	dNoise += -8 * t22 * t2 * offset2 * dot( gradient2, offset2 ) + t42 * gradient2;

	dNoise *= 70.0;

	return noiseValue;
}

#endif // IERENDERING_FLOWNOISE_H
