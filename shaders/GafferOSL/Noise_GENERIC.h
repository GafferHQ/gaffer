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

#include "GafferOSL/FlowNoise.h"

NOISE_TYPE baseNoise( string baseType, int periodic, int dimension, vector manifold, int animated, float animationTime, vector period, float timePeriod, int gaborImpulses )
{

	// We cancel out this scaling factor which is computed in the constructor of GaborParams
	// in liboslnoise/gabornoise.cpp.  Getting rid of it appears to give a more similar visual scale
	// to perlin, and allows periodic mode to line up properly
	if( baseType == "gabor" )
	{
		float gaborBandwidth = 1;
		float TWO_to_bandwidth = pow(2, gaborBandwidth);
		float SQRT_PI_OVER_LN2 = sqrt(M_PI / M_LN2);
		float a = 2.0 * ((TWO_to_bandwidth - 1.0) / (TWO_to_bandwidth + 1.0)) * SQRT_PI_OVER_LN2;
		float Gabor_Truncate = 0.02;
		float radius = sqrt(-log(Gabor_Truncate) / float(M_PI)) / a;
		manifold *= radius;
	}

	if( periodic )
	{
		if( animated == 0 )
		{
			if( dimension == 2 )
			{
				return pnoise( baseType, manifold[0], manifold[1], period[0], period[1], "impulses", gaborImpulses  );
			}
			else
			{
				return pnoise( baseType, manifold, period, "impulses", gaborImpulses );
			}
		}
		else
		{
			if( dimension == 2 )
			{
				return pnoise( baseType, point( manifold[0], manifold[1], animationTime ), vector( period[0], period[1], timePeriod ), "impulses", gaborImpulses );
			}
			else
			{
				return pnoise( baseType, manifold, animationTime, period, timePeriod, "impulses", gaborImpulses );
			}
		}
	}
	else
	{
		if( animated == 0 )
		{
			if( dimension == 2 )
			{
				return noise( baseType, manifold[0], manifold[1], "impulses", gaborImpulses  );
			}
			else
			{
				return noise( baseType, manifold, "impulses", gaborImpulses  );
			}
		}
		else
		{
			if( dimension == 2 )
			{
				return noise( baseType, point( manifold[0], manifold[1], animationTime ), "impulses", gaborImpulses );
			}
			else
			{
				return noise( baseType, manifold, animationTime, "impulses", gaborImpulses );
			}
		}
	}
}

float voronoiFalloff( point a, point b, string metric )
{
	vector disp = a - b;

	if ( metric == "square" )
	{
		// Chebyshev distance
		return 1.25 * max( abs(disp[0]), max( abs(disp[1]), abs(disp[2]) ) );
	}
	else if ( metric == "diamond" )
	{
		// Manhattan distance
		return 0.7 * ( abs(disp[0]) + abs(disp[1]) + abs(disp[2]) );
	}
	return length( disp );
}



NOISE_TYPE baseVoronoi( int dimension, point pos, string mode, string distMetric, string falloff, float jitter, float size, float sizeRandomness, float blur, int periodic, vector period, output float blurredOut )
{
	vector cellOffset = vector ( -0.5, -0.5, -0.5 );
	point baseCenter = point(floor(pos[0]) + 0.5, floor(pos[1]) + 0.5, floor(pos[2]) + 0.5 );

	float scaledBlur = blur * 0.4;
	float blurMult = 1 / max( 0.01, scaledBlur );

	// Our 4 accumulators.  Depending on mode, we use different sets of these
	float accumWeight = 0;
	NOISE_TYPE accumId = 0;
	float maxWeight = 0;
	float accumSimple = 0;

	int kmin = -1;
	int kmax = 1;
	if( dimension == 2 )
	{
		kmin = kmax = 0;
		baseCenter[2] = 0;
		pos[2] = 0;
	}

	for( int k = kmin; k <= kmax; k++ )
	{
		for( int i = -1; i <= 1; i++ )
		{
			for( int j = -1; j <= 1; j++ )
			{
				vector gridOffset = vector( i, j, k );
				point pointToRead = point( baseCenter + gridOffset );
				if( periodic )
				{
					pointToRead = mod( pointToRead, period );
				}
				vector cellPos = 0.5 + ( cellnoise( pointToRead ) - 0.5 ) * jitter;

				vector cellVec = cellPos + cellOffset;
				point cell = point ( baseCenter + gridOffset + cellVec );
				if( dimension == 2 )
				{
					cell[2] = pos[2];
				}
				float currentDist = voronoiFalloff( pos, cell, distMetric );

				if( sizeRandomness > 0 )
				{
					float cellSizeVariant = cellnoise( pointToRead + vector( 142, 765, 345 ) );
					currentDist /= 1 - sizeRandomness * cellSizeVariant;
				}

				if( mode == "centers" )
				{
					currentDist /= size;
					if( falloff == "smooth" )
					{
						currentDist = smoothstep( 0, 1, currentDist );
					}
				}
				else if( mode == "cellCenters" )
				{
					currentDist /= size;
				}

				accumSimple += max( 0, 1 - currentDist );


				float weight = exp( -( currentDist - 0.5 ) * blurMult );

				// Fade out weight as we approach the edge of the cell that this center is visible from
				vector edgeDist = baseCenter + gridOffset - pos;
				float q = max( max( abs( edgeDist[0] ), abs( edgeDist[1] ) ), abs( edgeDist[2] ) );
				weight *= 1 - smoothstep( 1.5 - scaledBlur, 1.5, q );

				if( mode == "cellEdges" && weight > maxWeight)
				{
					// When in cellEdges mode, we store the maxWeight so far separately from the accumulated weight
					accumWeight += maxWeight;
					maxWeight = weight;
				}
				else
				{
					accumWeight += weight;
				}

				if( mode == "cells" )
				{
					NOISE_TYPE cellId = cellnoise( pointToRead + vector( 467, 553, 937 ) );
					accumId += weight * cellId;
				}
			}
		}
	}

	blurredOut = 0;
	if( mode == "cells" )
	{
		return accumId / accumWeight;
	}
	else if( mode == "cellEdges" )
	{
		blurredOut = min( 1, scaledBlur * 4 ); 
		return max( 0, ( log( maxWeight ) - log( accumWeight ) ) / blurMult );
	}
	else if( mode == "cellCenters" )
	{
		return max( 0, ( 1 - min( 1, blur * 0.5 ) ) * ( 1 + log( accumWeight ) / blurMult - 0.5 ) );
	}
	else
	{
		return accumSimple;
	}
}

shader NOISE_NAME
(

string baseType = "perlin" [[
	string widget = "mapper",
	string options = "perlin:perlin|simplex:simplex|gabor (Slow):gabor|voronoi:voronoi|flow:flow",
	int connectable = 0,
	string help = "The type of noise used for each octave.  Perlin and simplex are both smoothly varying continuous noises, but simplex is a bit faster.  Gabor is similar, but with better filtering, and much slower.  Voronoi allows creating shapes based on overlapping points, such as starfields and alligator scales.  Flow noise is similar to simplex or perlin, but animates in a more wavy way.",
	int divider = 1,
]],

/*
`string manifold` : Dropdown with "UV", "PObject", "PWorld", "Pref", "Custom"
`vector customManifold` : Connection for custom manifold. Disabled unless `manifold == "Custom"`
`int dimension` : Dropdown offering "1", "2" or "3". Determines how many dimensions we take from the manifold.
`int animated` : Bool turning the use of time on/off. Effectively adds an extra dimension to the above.
`float time` : Where you plug time in. Disabled unless `animated == 1`.
*/

string manifold = "UV" [[
	string widget = "popup",
	string options = "UV|Pref|PObject|PWorld|Custom",
	int connectable = 0,
	string help = "The manifold defines the space the noise will be computed in.<ul><li>UV : Noise sticks to surface based on texture coordinate, discontinuous over UV seams</li></ul>",
]],

point customManifold = 0 [[
	string widget = "null",
	string help = "When manifold is set to &ldquo;custom&rdquo;, this defines the noise manifold.",
]],
int customDimension = 3 [[
	string widget = "popup",
	string options = "2|3",
	int connectable = 0,
	string help = "When using a custom manifold, defines how many dimensions to use.  If your input manifold has only 2 dimensions ( for example, a custom UV set ), the selecting 2 is a bit faster, and will give slightly higher quality results."
]],
int animated = 0 [[
	string widget = "checkBox",
	string page = "Animation",
	int connectable = 0,
	string help = "When using &ldquo;perlin&rdquo;, &ldquo;simplex&rdquo; or  &ldquo;flow &rdquo; noise, you can optionally change the noise using an additional manifold parameter, time.",
]],
float animationTime = 0 [[
	string page = "Animation",
	string help = "When animated, this defines an extra manifold parameter that varies the noise.  For simplex and perlin noise, this extra dimension behaves the same as the spatial noise dimensions.  For flow noise, this rotates the gradients, creating a wavy effect.",
]],
float animationSpeed = 1 [[
	string page = "Animation",
	int connectable = 0,
	string help = "How many different patterns the noise goes through in a unit of animationTime.",
]],
float flowRate = 2 [[
	string page = "Animation",
	int connectable = 0,
	string help = "When using fractal noise, the difference in animation speed between octaves.",
]],


vector frequency = 10 [[
	vector min = 0,
	int connectable = 0,
	string help = "Number of noise wobbles in unit area."
]],
float scale = 1 [[
	vector min = 0,
	int connectable = 0,
	string help = "Allows scaling the noise larger ( the opposite of increasing frequency )."
]],
vector manifoldOffset = 0 [[
	int connectable = 0,
	string help = "This value is added to the manifold, to make it easy to slide to a different region of noise if you prefer.",
	int divider = 1,
]],
int periodic = 0 [[
	int connectable = 0,
	string widget = "checkBox",
	int divider = 1,
	string help = "Causes the noise to repeat on the 0-1 range.  If animated, also repeats across animationTime 0-1.",
]],

float distortion = 0 [[
	float min = 0,
	int connectable = 0,
	string help = "Deforms the input manifold to warp the shape of the noise.",
]],
vector distortionFrequency = 1 [[
	float min = 0,
	int connectable = 0,
	string help = "The frequency of the distortion deformation.",
]],



string falloffCurve = "smooth" [[ 
	string widget = "popup",
	string options = "smooth|peaks|valleys",
	string page = "Default Shaping",
	string help = "Allows changing the default shape of the noise curves, so that instead of smooth sinusoidal shapes, you get sharp peaks or sharp valleys.",
	int connectable = 0,
]],
float falloffGamma = 1 [[
	float min = 0,
	string page = "Default Shaping",
	int gafferNoduleLayoutVisible = 0,
	string help = "Bend the shape shape of the noise to favour high values or low values.",
]],
int gaborImpulses = 16 [[
	string page = "Default Shaping",
	int connectable = 0,
]],
string voronoiMode = "centers" [[
	string widget = "popup",
	string options = "centers|cellCenters|cellEdges|cells",
	string page = "Voronoi Shaping",
	int connectable = 0,
	string help = "The voronoi noise type can output different patterns based on a network of cells.<ul><li>centers : Outputs a bright spot in the center of each cell</li><li>cellCenters : Bright spot, restricted to edges of the cell</li><li>cellEdges : Dark lines at cell edges</li><li>cells : A different value in each cell</li></ul>",
]],
string voronoiShape = "circle" [[
	string widget = "popup",
	string options = "circle|square|diamond",
	string page = "Voronoi Shaping",
	int connectable = 0,
	string help = "This affects the shape of each cell.  &ldquo;circle&rdquo; produces more natural shapes, like crocodile scales.  &ldquo;square&rdquo; and &ldquo;diamond&rdquo; produce more a technological greebled look."
]],
float voronoiCellJitter = 1 [[
	float min = 0,
	float max = 1,
	string page = "Voronoi Shaping",
	int connectable = 0,
	string help = "The amount of randomness in placing cells.  1 gives completely random placement, 0 gives a regular grid.",
]],
float voronoiSize = 0.75 [[
	string page = "Voronoi Shaping",
	int connectable = 0,
	float min = 0,
	float max = 2,
	string help = "The size of each cell.",
]],
float voronoiSizeRandomness = 0 [[
	float min = 0,
	float max = 1,
	string page = "Voronoi Shaping",
	int connectable = 0,
	string help = "Randomly reduces the size of each cell by up to this fraction.",
]],
float voronoiBoundaryBlur = 0 [[
	float min = 0,
	string page = "Voronoi Shaping",
	int gafferNoduleLayoutVisible = 0,
	string help = "Adds smoothing to the edges between cells.",
]],
string voronoiFalloffCurve = "smooth" [[
	string widget = "popup",
	string options = "smooth|linear",
	string page = "Voronoi Shaping",
	int connectable = 0,
	string help = "Smooth blends out the peaks and edges of individual cells, linear keeps a straighter falloff",
]],
float voronoiFalloffGamma = 1 [[
	float min = 0,
	string page = "Voronoi Shaping",
	int gafferNoduleLayoutVisible = 0,
	string help = "Bend the shape shape of the voronoi noise to favour high values or low values.",
]],


int octaves = 1 [[
	int min = 1,
	string page = "Fractal",
	int connectable = 0,
	string help = "How many different scales of noise will be added together.",
]],
vector lacunarity = 1.92 [[
	vector min = 1,
	string page = "Fractal",
	int connectable = 0,
	string help = "The size scaling factor between each octave.",
]],
float octaveGain = 0.707 [[
	string page = "Fractal",
	int gafferNoduleLayoutVisible = 0,
	string help = "The intensity scaling factor between each octave.",
]],

float flowAdvection = 0 [[
	string page = "Flow",
	int connectable = 0,
	string help = "When using flow noise, how much the derivative of one octave distorts the next octave.",
]],
string flowOutput = "noise" [[
	string page = "Flow",
	string widget = "popup",
	string options = "noise|advection|advectedManifold",
	int connectable = 0,
	string help = "When using noise, you can select whether to output the standard noise, or the advection vector computed from the derivatives, or an advected manifold value ( suitable for plugging straight into another noise or texture ).",
]],

float filterScale = 0.5 [[
	string page = "Filtering",
	int connectable = 0,
	float min = 0,
	string help = "The noise is filtered out and replaced with an average value when the details get too small.  Lowering the filterScale leaves in smaller details, which may look better, but increases render time and noise.",
]],
float filterBlur = 0 [[
	string page = "Filtering",
	int gafferNoduleLayoutVisible = 0,
	float min = 0,
	float max = 1,
	string help = "Driving this with a texture allows removing details from some areas of a fractal noise.",
]],

NOISE_TYPE remapMin = NOISE_DEFAULT_MIN [[
	int connectable = 0,
	string page = "Output Range",
	string help = "The minimum value that the noise is expected to reach - depending on your filtering, shaping, and octaves, it may not actually reach this value.",
]],
NOISE_TYPE remapMax = 1 [[
	int connectable = 0,
	string page = "Output Range",
	string help = "The maximum value that the noise is expected to reach - depending on your filtering, shaping, and octaves, it may not actually reach this value.",
]],
int clampZeroToOne = 0 [[
	string widget = "checkBox",
	int connectable = 0,
	string page = "Output Range",
	string help = "Hard clamp the noise to not go higher than 1 or less than 0.",
]],

output NOISE_TYPE out = 0 [[
	string help = "The noise value.",
]],
output vector outAdvection = 0 [[
	int gafferNoduleLayoutVisible = 0,
	string help = "When using flow noise, you can output the advection to drive another noise.",
]],
output point outAdvectedManifold = 0 [[
	int gafferNoduleLayoutVisible = 0,
	string help = "When using flow noise, this provides the advection applied to the original manifold, ready to plug directly into another noise.",
]],
)
{

	point inputManifold;
	int dimension = 3;
	if( manifold == "UV" )
	{
		inputManifold = vector( u, v, 0 );
		dimension = 2;
	}
	else if( manifold == "PWorld" )
	{
		inputManifold = transform( "world", P );
	}
	else if( manifold == "PObject" )
	{
		inputManifold = transform( "object", P );
	}
	else if( manifold == "Pref" )
	{
		point Pref = 0;
		getattribute( "Pref", Pref );
		inputManifold = Pref;
	}
	else
	{
		dimension = customDimension;
		inputManifold = customManifold;
	}

	point finalManifold = inputManifold + manifoldOffset;

	vector octaveScale = 1;
	float octaveMult = 1;

	float weight = 0;
	vector octaveFrequency = frequency / scale;

	vector effectiveFilterBlur = filterBlur;
	effectiveFilterBlur += filterScale * filterwidth( finalManifold );

	float falloffGammaInv = 1 / max( 0.001, falloffGamma );
	float voronoiFalloffGammaInv = 1 / max( 0.001, voronoiFalloffGamma );

	// In order to fade out in the distance, we use a set of rough heuristics
	// to estimate the total value after applying gammas and averaging across the whole
	// noise distribution
	NOISE_TYPE average = 0;
	if( baseType == "voronoi" )
	{
		float effectiveSize = voronoiSize * ( 1 - 0.4 * voronoiSizeRandomness );
		point averageValueSamplePositions = 0;
		point weights = 1 / 3.0;
		if( voronoiMode == "cells" )
		{
			averageValueSamplePositions = point( 0.3, 0.5, 0.7 );
		}
		else if( voronoiMode == "cellEdges" )
		{
			averageValueSamplePositions = mix( point( 0.1, 0.2, 0.4 ), point( 0.1, 0.4, 0.6 ), voronoiSizeRandomness );
		}
		else if( voronoiMode == "cellCenters" )
		{
			point slopeSamples = max( 0, 1 - 1.1 / effectiveSize * point( 0.15, 0.4, 0.6 ) );
			averageValueSamplePositions = pow( max( 0, slopeSamples + 0.03 ), 3 );
		}
		else
		{
			point slopeSamples = max( 0, 1 - 1.1 / effectiveSize * point( 0.08, 0.2, 0.6 ) );
			weights = point( 0.05, 0.25, 0.7 );
			averageValueSamplePositions = pow( max( 0, slopeSamples + 0.03 ) + 0.6 * max( 0, effectiveSize - 0.4 ) , 3 );
		}

		if( voronoiFalloffGamma < 1 )
		{
			average = dot(
					weights,
					min( averageValueSamplePositions, pow( averageValueSamplePositions, voronoiFalloffGammaInv ) )
				);
		}
		else if( voronoiFalloffGamma > 1 )
		{
			average = dot(
					weights,
					pow( averageValueSamplePositions, voronoiFalloffGammaInv )
				);
		}
		else
		{
			average = dot( weights, averageValueSamplePositions );
		}
	}
	else
	{
		float spread = 0.25;
	
		if( baseType == "simplex" ) spread = 0.35;
		else if( baseType == "gabor" ) spread = 0.15;

		point averageValueSamplePositions = 0;
		if( falloffCurve == "peaks" )
		{
			averageValueSamplePositions = ( 1 - point( 0.2, 0.9, 1.6 ) * spread );
		}
		else if( falloffCurve == "valleys" )
		{
			averageValueSamplePositions = ( point( 0.2, 0.8, 1.6 ) * spread );
		}
		else
		{
			averageValueSamplePositions = spread * point( -1, 0, 1 ) * 0.5 + 0.5;
		}

		if( falloffGamma != 1 )
		{
			average = dot(
					point( 1 / 3.0 ),
					pow( averageValueSamplePositions, falloffGammaInv )
				);
		}
		else
		{
			average = dot( point( 1 / 3.0 ), averageValueSamplePositions );
		}
	}

	float curAnimationSpeed = animationSpeed;
	if( periodic )
	{
		curAnimationSpeed = ceil( curAnimationSpeed );
	}

	// Using some arbitrary offsets here makes it less likely that you will see weird correlations between
	// the base noise and the distortion, or two different octaves
	vector distortionSeed = vector( 314.70, 413.04, 231.62 );
	NOISE_TYPE n = 0;
	vector advectionAccum = 0;
	for( int i = 0; i < octaves; i++ )
	{
		float octaveSpeed = animationSpeed * pow( flowRate, i );
		vector octaveSeed = vector( 423.22, 213.23, 322.54 ) * i;
		vector curFrequency = octaveFrequency;
		if( periodic )
		{
			if( baseType == "flow" )
			{
				// We can't make flow noise periodic if it's anisotropically scaled
				curFrequency = vector( dot( curFrequency, 1 / 3.0 ) );
			}
			curFrequency = ceil( curFrequency );
			octaveSpeed = ceil( octaveSpeed );

			if( baseType == "flow" && dimension == 3 )
			{
				// 3D flow noise only supports periodic for frequencies which are multiples of 3
				curFrequency = 3.0 * ceil( curFrequency / 3.0 );
			}
		}
		float octaveTime = animationTime * octaveSpeed;

		vector octaveBlurVector = effectiveFilterBlur * curFrequency;
		float octaveBlur = max( octaveBlurVector[0], max( octaveBlurVector[1], octaveBlurVector[2] ) );

		weight += octaveMult;
		float fadeWeight = 1 - smoothstep( 0.5, 1.5, octaveBlur );
		NOISE_TYPE octaveValue = 0;
		if( fadeWeight > 0.00001 )
		{

			
			point octaveManifold = ( finalManifold + advectionAccum ) * curFrequency + octaveSeed;

			vector distort = 0;
			if( distortion > 0 )
			{
				vector curDistortionFrequency = octaveFrequency * distortionFrequency;
				if( periodic )
				{
					curDistortionFrequency = ceil( curDistortionFrequency );
				}
				
				vector distortionManifold = curDistortionFrequency * finalManifold + octaveSeed + distortionSeed;
				distort = baseNoise( "perlin", periodic, dimension, distortionManifold, 0 /* animated */, 0, curDistortionFrequency, 0, 0 );
			}

			vector curManifold = octaveManifold + distortion * distort;
			if( baseType == "voronoi" )
			{
				float blurredOut;
				NOISE_TYPE v = baseVoronoi( dimension, curManifold, voronoiMode, voronoiShape, voronoiFalloffCurve, voronoiCellJitter, voronoiSize, voronoiSizeRandomness, octaveBlur + voronoiBoundaryBlur, periodic, curFrequency, blurredOut );
				octaveValue = 2 * v - 1;

				// Don't apply the gamma if the octaveValue contains multiple cells adding to over 1
				// and the gamma would push it higher
				if( voronoiFalloffGamma < 1 )
				{
					octaveValue = 2 * min( octaveValue * 0.5 + 0.5, pow( octaveValue * 0.5 + 0.5, voronoiFalloffGammaInv ) ) - 1;
				}
				else if( voronoiFalloffGamma > 1 )
				{
					octaveValue = 2 * pow( octaveValue * 0.5 + 0.5, voronoiFalloffGammaInv ) - 1;
				}

				// Fill in missing average value as the edge blur overdarkens things otherwise
				octaveValue += 2 * average * blurredOut;
			}
			else
			{
				if( baseType == "flow" )
				{
					float effectiveTime = octaveTime * animated;
					vector dNoise;
					if( dimension == 2 )
					{
						octaveValue = simplexFlowNoise2D( curManifold, effectiveTime, periodic * int( curFrequency[0] ), dNoise );
					}
					else
					{
						octaveValue = simplexFlowNoise3D( curManifold, effectiveTime, periodic * int( curFrequency[0] ), dNoise );
					}

					advectionAccum -= flowAdvection * dNoise / curFrequency;
				}
				else
				{
					octaveValue = baseNoise( baseType, periodic, dimension, curManifold, animated, octaveTime * curAnimationSpeed, curFrequency, curAnimationSpeed, gaborImpulses );
				}
			
				if( falloffCurve == "peaks" )
				{
					octaveValue = 2 * ( 1 - abs( octaveValue ) )  - 1;
				}
				else if( falloffCurve == "valleys" )
				{
					octaveValue = 2 * abs( octaveValue ) - 1;
				}

				if( falloffGamma != 1 )
				{
					octaveValue = 2 * pow( octaveValue * 0.5 + 0.5, falloffGammaInv ) - 1;
				}
			}
		}

		n += mix( average * 2 - 1, octaveValue, fadeWeight ) * octaveMult;
		octaveMult *= octaveGain;
		octaveFrequency *= lacunarity;
	}

	out = mix( remapMin, remapMax, n / weight * 0.5 + 0.5 );

	if( clampZeroToOne )
	{
		out = max( 0, min( 1, out ) );
	}

	outAdvection = advectionAccum;
	outAdvectedManifold = inputManifold + advectionAccum;
}
