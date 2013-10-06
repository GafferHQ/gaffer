//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#ifndef GAFFEROSL_OSLIMAGE_H
#define GAFFEROSL_OSLIMAGE_H

#include "GafferImage/ImageProcessor.h"

#include "GafferOSL/TypeIds.h"
#include "GafferOSL/OSLRenderer.h"

namespace GafferOSL
{

class OSLImage : public GafferImage::ImageProcessor
{

	public :

		OSLImage( const std::string &name=defaultName<OSLImage>() );
		virtual ~OSLImage();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferOSL::OSLImage, OSLImageTypeId, GafferImage::ImageProcessor );
		
		Gaffer::Plug *shaderPlug();
		const Gaffer::Plug *shaderPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

		/// Exposed for access by OSLObject.
		static OSLRenderer::ConstShadingEnginePtr shadingEngine( const Gaffer::Plug *shaderPlug );
	
	protected :
	
		virtual bool acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const;

		virtual bool enabled() const;
		
		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashFormatPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashDataWindowPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelNamesPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;
		virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const;
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const;
		virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const;
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const;

	private :
	
		// computeChannelData() is called for individual channels at a time, but when we run a
		// shader we get all the outputs at once. we therefore use this plug to compute (and
		// automatically cache) the shading and then access it from computeChannelData(), which
		// simply extracts the right part of the data.
		/// \todo Investigate turning off caching for the channelData plug, since we're currently
		/// caching once there and once in the shadingPlug.
		Gaffer::ObjectPlug *shadingPlug();
		const Gaffer::ObjectPlug *shadingPlug() const;
	
		void hashShading( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		IECore::ConstCompoundDataPtr computeShading( const Gaffer::Context *context ) const;

		static size_t g_firstPlugIndex;
					
};

} // namespace GafferOSL

#endif // GAFFEROSL_OSLIMAGE_H
