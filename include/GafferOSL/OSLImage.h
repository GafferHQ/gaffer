//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, John Haddon. All rights reserved.
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/FlatImageProcessor.h"

#include "GafferScene/ShaderPlug.h"

#include "GafferOSL/TypeIds.h"

namespace GafferOSL
{

class OSLImage : public GafferImage::FlatImageProcessor
{

	public :

		OSLImage( const std::string &name=defaultName<OSLImage>() );
		virtual ~OSLImage();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferOSL::OSLImage, OSLImageTypeId, GafferImage::FlatImageProcessor );

		GafferScene::ShaderPlug *shaderPlug();
		const GafferScene::ShaderPlug *shaderPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		virtual bool acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const;

		virtual bool enabled() const;

		// Reimplemented to throw. Because they are connected as direct pass-throughs these methods should never be called.
		virtual void hashFlatDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashFlatMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual Imath::Box2i computeFlatDataWindow( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeFlatMetadata( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const;

		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashFlatChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashFlatChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;
		virtual IECore::ConstStringVectorDataPtr computeFlatChannelNames( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const;
		virtual IECore::ConstFloatVectorDataPtr computeFlatChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const;

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
