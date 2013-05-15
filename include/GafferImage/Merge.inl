//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

template< typename F >
IECore::ConstFloatVectorDataPtr Merge::doMergeOperation( F f, std::vector< IECore::ConstFloatVectorDataPtr > &inData, std::vector< IECore::ConstFloatVectorDataPtr > &inAlpha, const Imath::V2i &tileOrigin ) const
{
	// Allocate the new tile
	Imath::Box2i tile( tileOrigin, Imath::V2i( tileOrigin.x + ImagePlug::tileSize() - 1, tileOrigin.y + ImagePlug::tileSize() - 1 ) );
	IECore::FloatVectorDataPtr outDataPtr = inData.back()->copy();
	std::vector<float> &outData = outDataPtr->writable();

	// Allocate a temporary tile that will hold the intermediate values of the alpha channel.
	IECore::FloatVectorDataPtr aOut = inAlpha.back()->copy();
	std::vector<float> &outAlpha = aOut->writable();
	
	// Perform the operation.
	unsigned int nIterations( inData.size() -1 );
	for( unsigned int i = nIterations; i > 0; --i )
	{
		for( int y = tile.min.y; y<=tile.max.y; y++ )
		{
			// Compute the data values and afterwards, the intermediate alpha values.
			const float *dIn1 = &(outData[0]) + ( y - tileOrigin.y ) * ImagePlug::tileSize() + (tile.min.x - tileOrigin.x);
			const float *dIn2 = &(inData[i-1]->readable()[0]) + (y - tileOrigin.y) * ImagePlug::tileSize() + (tile.min.x - tileOrigin.x);	
			const float *aIn1 = &(outAlpha[0]) + ( y - tileOrigin.y ) * ImagePlug::tileSize() + (tile.min.x - tileOrigin.x);
			const float *aIn2 = &(inAlpha[i-1]->readable()[0]) + (y - tileOrigin.y) * ImagePlug::tileSize() + (tile.min.x - tileOrigin.x);

			float *dOut = &(outData[0]) + ( y - tileOrigin.y ) * ImagePlug::tileSize() + (tile.min.x - tileOrigin.x);
			float *aOut = &(outAlpha[0]) + ( y - tileOrigin.y ) * ImagePlug::tileSize() + (tile.min.x - tileOrigin.x);

			const float *END = dOut+(tile.max.x-tile.min.x)+1;
			while( dOut != END )
			{
				*dOut++ = f( *dIn1++, *dIn2++, *aIn1, *aIn2 );
				*aOut++ = f( *aIn1, *aIn2, *aIn1, *aIn2 );
				++aIn1;
				++aIn2;
			}	
		}
	}
	return outDataPtr;
}

