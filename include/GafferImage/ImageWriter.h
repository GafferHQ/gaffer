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

#ifndef GAFFERIMAGE_IMAGEWRITER_H
#define GAFFERIMAGE_IMAGEWRITER_H

#include "Gaffer/ExecutableNode.h"
#include "Gaffer/Context.h"
#include "GafferImage/TypeIds.h"
#include "GafferImage/ChannelMaskPlug.h"

namespace GafferImage
{

class ImageWriter : public Gaffer::ExecutableNode
{

	public :

		enum
		{
			Scanline = 0,
			Tile = 1
		};

		ImageWriter( const std::string &name=defaultName<ImageWriter>() );
		virtual ~ImageWriter();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::ImageWriter, ImageWriterTypeId, ExecutableNode );
		
		Gaffer::StringPlug *fileNamePlug();
		const Gaffer::StringPlug *fileNamePlug() const;
		GafferImage::ImagePlug *inPlug();
		const GafferImage::ChannelMaskPlug *channelsPlug() const;
		GafferImage::ChannelMaskPlug *channelsPlug();
		const GafferImage::ImagePlug *inPlug() const;
		Gaffer::IntPlug *writeModePlug();
		const Gaffer::IntPlug *writeModePlug() const;

		// Implemented to specify the requirements which must be satisfied
		// before it is allowed to call execute() with the given context.
		virtual void executionRequirements( const Gaffer::Context *context, Executable::Tasks &requirements ) const;
		
		/// Implemented to set a hash that uniquely represents the
		/// side effects (files created etc) of calling execute with the given context.
		/// If the node returns the default hash it means this node does not compute anything.
		virtual IECore::MurmurHash executionHash( const Gaffer::Context *context ) const;
		
		/// Implemented to execute in all the specified contexts in sequence.
		virtual void execute( const Executable::Contexts &contexts ) const;

	private :
		
		void plugSet( Gaffer::Plug *plug );
	
		static size_t g_firstPlugIndex;
		
};

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGEWRITER_H

