//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/TypeIds.h"
#include "GafferImage/Export.h"

#include "GafferDispatch/TaskNode.h"

#include "IECore/CompoundData.h"

#include <functional>

namespace Gaffer
{
	IE_CORE_FORWARDDECLARE( ValuePlug )
	IE_CORE_FORWARDDECLARE( StringPlug )
	IE_CORE_FORWARDDECLARE( ContextQuery )
	IE_CORE_FORWARDDECLARE( FilePathPlug )
} // namespace Gaffer

namespace GafferImage
{

IE_CORE_FORWARDDECLARE( ColorSpace )
IE_CORE_FORWARDDECLARE( ImagePlug )

class GAFFERIMAGE_API ImageWriter : public GafferDispatch::TaskNode
{

	public :

		enum Mode
		{
			Scanline = 0,
			Tile = 1
		};

		ImageWriter( const std::string &name=defaultName<ImageWriter>() );
		~ImageWriter() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::ImageWriter, ImageWriterTypeId, TaskNode );

		Gaffer::FilePathPlug *fileNamePlug();
		const Gaffer::FilePathPlug *fileNamePlug() const;

		GafferImage::ImagePlug *inPlug();
		const GafferImage::ImagePlug *inPlug() const;

		Gaffer::StringPlug *channelsPlug();
		const Gaffer::StringPlug *channelsPlug() const;

		GafferImage::ImagePlug *outPlug();
		const GafferImage::ImagePlug *outPlug() const;

		Gaffer::StringPlug *colorSpacePlug();
		const Gaffer::StringPlug *colorSpacePlug() const;

		Gaffer::StringPlug *layoutPartNamePlug();
		const Gaffer::StringPlug *layoutPartNamePlug() const;

		Gaffer::StringPlug *layoutChannelNamePlug();
		const Gaffer::StringPlug *layoutChannelNamePlug() const;

		Gaffer::BoolPlug *matchDataWindowsPlug();
		const Gaffer::BoolPlug *matchDataWindowsPlug() const;

		Gaffer::ValuePlug *fileFormatSettingsPlug( const std::string &fileFormat );
		const Gaffer::ValuePlug *fileFormatSettingsPlug( const std::string &fileFormat ) const;

		const std::string currentFileFormat() const;

		/// Note that this is intentionally identical to the ImageReader's DefaultColorSpaceFunction
		/// definition, so that the same function can be used with both nodes.
		using DefaultColorSpaceFunction = std::function<const std::string ( const std::string &fileName, const std::string &fileFormat, const std::string &dataType, const IECore::CompoundData *metadata )>;
		static void setDefaultColorSpaceFunction( DefaultColorSpaceFunction f );
		static DefaultColorSpaceFunction getDefaultColorSpaceFunction();

	protected :

		IECore::MurmurHash hash( const Gaffer::Context *context ) const override;
		void execute() const override;

	private :

		std::string colorSpace( const std::string &dataType ) const;

		ColorSpace *colorSpaceNode();
		const ColorSpace *colorSpaceNode() const;

		void createFileFormatOptionsPlugs();

		static size_t g_firstPlugIndex;

		static DefaultColorSpaceFunction &defaultColorSpaceFunction();

		// Friendship for the bindings
		friend struct GafferDispatchBindings::Detail::TaskNodeAccessor;

};

IE_CORE_DECLAREPTR( ImageWriter )

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGEWRITER_H
