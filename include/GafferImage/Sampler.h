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
//      * Neither the name of Image Engine Design nor the names of
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

#ifndef GAFFERIMAGE_SAMPLER_H
#define GAFFERIMAGE_SAMPLER_H

#include <vector>
#include "GafferImage/ImagePlug.h"

namespace GafferImage
{

///\todo: 
/// Add a hash() method to the sampler that accumulates the hashes of all tiles within m_sampleWindow.
/// Currently anything that uses the sampler to gather data from across an area could potentially
/// have an incorrect hash if one of the tiles that it is sampling which isn't the one being output
/// changes. For example, if our sampler is accessing 4 tiles to produce an output for one tile and a node
/// upstream changes just one of them and passes the hashes of the other through, the output hash  will
/// be wrong and not update. This has not been an issue yet as we don't have any nodes that do that!
	
/// A utility class for pixel access of an image plug.
class Sampler
{

public : 
	
	/// Sampler Constructor
	/// @param plug The image plug to sample from.
	/// @param channelName The channel to sample.
	/// @param The bounds which we wish to sample from. The actual sample area includes all valid tiles that sampleWindow contains or intersects.
	Sampler( const GafferImage::ImagePlug *plug, const std::string &channelName, const Imath::Box2i &sampleWindow );

	/// Samples a colour value from the channel at x, y. The result is clamped the the sampleWindow.	
	float sample( int x, int y );

private:

	const ImagePlug *m_plug;
	const std::string &m_channelName;
	Imath::Box2i m_sampleWindow;
	std::vector< IECore::ConstFloatVectorDataPtr > m_dataCache;
	bool m_valid;

};

}; // namespace GafferImage

#endif

