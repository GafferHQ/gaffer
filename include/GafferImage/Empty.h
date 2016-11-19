//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGE_EMPTY_H
#define GAFFERIMAGE_EMPTY_H

#include "GafferImage/ImageNode.h"
#include "GafferImage/FormatPlug.h"

namespace GafferImage
{

class Empty : public ImageNode
{

    public :

        Empty( const std::string &name=defaultName<Empty>() );
        virtual ~Empty();

        IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Empty, EmptyTypeId, ImageNode );

        GafferImage::FormatPlug *formatPlug();
        const GafferImage::FormatPlug *formatPlug() const;

        virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

    protected :

        virtual void hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
        virtual void hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
        virtual void hashDeepState( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
        virtual void hashSampleOffsets( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
        virtual void hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
        virtual void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

        virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;
        virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;
        virtual IECore::ConstCompoundObjectPtr computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const;
        virtual int computeDeepState( const Gaffer::Context *context, const ImagePlug *parent ) const;
        virtual IECore::ConstIntVectorDataPtr computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;
        virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const;
        virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;

    private :

        static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Empty )

} // namespace GafferImage

#endif // GAFFERIMAGE_EMPTY_H
