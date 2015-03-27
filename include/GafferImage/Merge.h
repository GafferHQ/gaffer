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

#include "Gaffer/Behaviours/InputGenerator.h"

#include "GafferImage/ImageProcessor.h"

namespace GafferImage
{

/// A node for Merging two or more images. Merge will use the displayWindow and metadata from the first input;
/// expand the dataWindow to the union of all dataWindows from the connected inputs; create a union of
/// channelNames from all the connected inputs, and will merge the channelData according to the operation mode.
/// \todo Ideally ImageProcessor will be capable of having multiple inputs via an ArrayPlug called "in", at
/// which point we can remove this custom InputGenerator behaviour.
class Merge : public ImageProcessor
{

	public :

		typedef std::vector<Gaffer::Behaviours::InputGenerator<GafferImage::ImagePlug>::PlugClassPtr> ImagePlugList;

		Merge( const std::string &name=defaultName<Merge>() );
		virtual ~Merge();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Merge, MergeTypeId, ImageProcessor );

		//! @name Operations
		/// The available operations used to merge the channelData.
		//////////////////////////////////////////////////////////////
		//@{
		/// 	Add: A + B
		/// 	Atop: Ab + B(1-a)
		/// 	Divide: A / B
		/// 	In: Ab
		/// 	Out: A(1-b)
		/// 	Mask: Ba
		/// 	Matte: Aa + B(1.-a)
		/// 	Multiply: AB
		/// 	Over: A + B(1-a)
		/// 	Subtract: A - B
		/// 	Under: A(1-b) + B
		enum Operation
		{
			Add,
			Atop,
			Divide,
			In,
			Out,
			Mask,
			Matte,
			Multiply,
			Over,
			Subtract,
			Under
		};
		//@}

		Gaffer::IntPlug *operationPlug();
		const Gaffer::IntPlug *operationPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		/// Reimplementated to check that at least two of the inputs are connected
		virtual bool enabled() const;
		
		// Reimplemented to assign directly from the first input. Format cannot be a direct connection
		// because it needs to update when the default format changes.
		/// \todo: make this a direct pass-through once FormatPlug supports it.
		virtual void hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;
		
		/// Reimplemented to hash the connected input plugs
		virtual void hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		/// Sets the data window to the union of all of the data windows.
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;
		/// Creates a union of all of the connected inputs channelNames.
		virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const;
		/// Implemented to call doMergeOperation according to operationPlug()
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;

		// A helper class that manages our ImagePlug inputs.
		Gaffer::Behaviours::InputGenerator<ImagePlug> m_inputs;

	private :

		// A convenience method to return an index for a channel that can be used to address Color4f plugs.
		inline int channelIndex( const std::string &channelName ) const { return channelName == "R" ? 0 : channelName == "G" ? 1 : channelName == "B" ? 2 : 3; };

		/// Performs the merge operation using the functor 'F'.
		template< typename F >
		IECore::ConstFloatVectorDataPtr doMergeOperation( F f, std::vector< IECore::ConstFloatVectorDataPtr > &inData, std::vector< IECore::ConstFloatVectorDataPtr > &inAlpha, const Imath::V2i &tileOrigin ) const;

		/// A useful method which returns true if the StringVector contains the channel "A".
		inline bool hasAlpha( IECore::ConstStringVectorDataPtr channelNamesData ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Merge )

#include "Merge.inl"

} // namespace GafferImage

#endif // GAFFERIMAGE_MERGE_H
