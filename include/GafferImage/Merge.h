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

#ifndef GAFFERIMAGE_MERGE_H
#define GAFFERIMAGE_MERGE_H

#include "GafferImage/FlatImageProcessor.h"

#include "Gaffer/NumericPlug.h"

namespace GafferImage
{

/// A node for Merging two or more images. Merge will use the displayWindow and metadata from the first input;
/// expand the dataWindow to the union of all dataWindows from the connected inputs; create a union of
/// channelNames from all the connected inputs, and will merge the channelData according to the operation mode.
/// \todo Optimise. Things to consider :
///
/// - For some operations (multiply for instance) our output data window could be the intersection
///   of all input windows, rather than the union.
/// - For some operations (add for instance) we could entirely skip invalid input tiles, and tiles
///   where channelData == ImagePlug::blackTile().
/// - For some operations we do not need to track the intermediate alpha values at all.
/// - We could improve our masking of invalid pixels with special cases for wholly valid tiles,
///   wholly invalid tiles, and by chunking the work on the valid sections.
class GAFFERIMAGE_API Merge : public FlatImageProcessor
{

	public :

		Merge( const std::string &name=defaultName<Merge>() );
		~Merge() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::Merge, MergeTypeId, FlatImageProcessor );

		enum Operation
		{
			Add,       // A + B
			Atop,      // Ab + B(1-a)
			Divide,    // A / B
			In,        // Ab
			Out,       // A(1-b)
			Mask,      // Ba
			Matte,     // Aa + B(1-a)
			Multiply,  // AB
			Over,      // A + B(1-a)
			Subtract,  // A - B
			Difference,// fabs( A - B )
			Under,     // A(1-b) + B
			Min,       // min( A, B )
			Max        // max( A, B )
		};

		Gaffer::IntPlug *operationPlug();
		const Gaffer::IntPlug *operationPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		/// Reimplemented to hash the connected input plugs
		void hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;

		/// Sets the data window to the union of all of the data windows.
		Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const override;
		/// Creates a union of all of the connected inputs channelNames.
		IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const override;
		/// Implemented to call doMergeOperation according to operationPlug()
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const override;

	private :

		// Performs the merge operation using the functor 'F'.
		template<typename F>
		IECore::ConstFloatVectorDataPtr merge( F f, const std::string &channelName, const Imath::V2i &tileOrigin ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Merge )

} // namespace GafferImage

#endif // GAFFERIMAGE_MERGE_H
