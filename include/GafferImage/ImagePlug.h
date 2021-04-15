//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGE_IMAGEPLUG_H
#define GAFFERIMAGE_IMAGEPLUG_H

#include "GafferImage/AtomicFormatPlug.h"
#include "GafferImage/Export.h"
#include "GafferImage/TypeIds.h"

#include "Gaffer/Context.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/TypedPlug.h"

#include "IECoreImage/ImagePrimitive.h"

namespace GafferImage
{

/// The ImagePlug is used to pass images between nodes in the gaffer graph. It is a compound
/// type, with subplugs for different aspects of the image.
///
/// Some notes on the Gaffer Image Space:
/// Images are represented internally to Gaffer with their origin located in the bottom left of the
/// display window with the positive Y axis ascending towards the top of the image. The reasoning
/// behind deviating from the OpenEXR and Cortex representation which, defines the origin in the top
/// left corner of the display window with the positive Y axis pointing downwards, is
/// to make things more intuitive for the user whilst simplifying node development.
/// If images were to follow the OpenEXR convention and have their origin in the top left,
/// values taken from screen space gadgets and plugs such as the Transform2DPlug and Box2iPlug
/// would require their values to be flipped around the top edge of the image's display window
/// to transform them into image space. By using the same coordinate axis for both the screen and
/// image space, the values taken from the transform2DPlug and Box2iPlug can be used directly and
/// independently of the image's format.
///
/// Some notes on Image Metadata:
/// Metadata is loaded into Gaffer following the OpenImageIO standards, but after that point it is
/// considered arbitrary data that flows along with an image. The only image processing nodes that
/// will modify the metadata are the Metadata specific nodes. Other image processing may occur which
/// causes the implied meaning of certain metadata entries to become invalid (such as oiio:ColorSpace)
/// but those nodes will not alter the metadata, nor behave differently based on its value.
///
/// Some notes on color space:
/// GafferImage nodes expect to operate in linear space, with associated alpha. Users are responsible
/// for meeting that expectation (or knowing what they're doing when they don't).
class GAFFERIMAGE_API ImagePlug : public Gaffer::ValuePlug
{

	public :

		ImagePlug( const std::string &name=defaultName<ImagePlug>(), Direction direction=In, unsigned flags=Default );
		~ImagePlug() override;

		GAFFER_PLUG_DECLARE_TYPE( GafferImage::ImagePlug, ImagePlugTypeId, ValuePlug );

		bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const override;
		Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;
		/// Only accepts ImagePlug inputs.
		bool acceptsInput( const Gaffer::Plug *input ) const override;

		/// @name Child plugs
		/// Different aspects of the image are passed through different
		/// child plugs.
		////////////////////////////////////////////////////////////////////
		//@{
		GafferImage::AtomicFormatPlug *formatPlug();
		const GafferImage::AtomicFormatPlug *formatPlug() const;
		Gaffer::AtomicBox2iPlug *dataWindowPlug();
		const Gaffer::AtomicBox2iPlug *dataWindowPlug() const;
		Gaffer::AtomicCompoundDataPlug *metadataPlug();
		const Gaffer::AtomicCompoundDataPlug *metadataPlug() const;
		Gaffer::BoolPlug *deepPlug();
		const Gaffer::BoolPlug *deepPlug() const;
		Gaffer::IntVectorDataPlug *sampleOffsetsPlug();
		const Gaffer::IntVectorDataPlug *sampleOffsetsPlug() const;
		Gaffer::StringVectorDataPlug *channelNamesPlug();
		const Gaffer::StringVectorDataPlug *channelNamesPlug() const;
		Gaffer::FloatVectorDataPlug *channelDataPlug();
		const Gaffer::FloatVectorDataPlug *channelDataPlug() const;
		//@}

		/// @name Context management
		/// Utilities for constructing contexts relevant to the evaluation
		/// of the child plugs above.
		////////////////////////////////////////////////////////////////////
		/// The names used to specify the channel name and tile of
		/// interest via a Context object. You should use these
		/// variables rather than hardcoding string values - it is
		/// both less error prone and quicker than constructing
		/// InternedStrings on every lookup.
		static const IECore::InternedString channelNameContextName;
		static const IECore::InternedString tileOriginContextName;

		/// Utility class to scope a temporary copy of a context,
		/// with tile/channel specific variables removed. This can be used
		/// when evaluating plugs which must be global to the whole image,
		/// and can improve performance by reducing pressure on the hash cache.
		struct GlobalScope : public Gaffer::Context::EditableScope
		{
			GlobalScope( const Gaffer::Context *context );
			GlobalScope( const Gaffer::ThreadState &threadState );
		};

		/// Utility class to scope a temporary copy of a context,
		/// with convenient accessors to set tileOrigin and channelName,
		/// which you often need to do while accessing channelData
		struct ChannelDataScope : public Gaffer::Context::EditableScope
		{
			ChannelDataScope( const Gaffer::Context *context );
			ChannelDataScope( const Gaffer::ThreadState &threadState );

			[[deprecated("Use faster pointer version")]]
			void setTileOrigin( const Imath::V2i &tileOrigin );
			[[deprecated("Use faster pointer version")]]
			void setChannelName( const std::string &channelName );

			// These fast calls take pointers, and it is the caller's
			// responsibility to ensure that the memory pointed to
			// stays valid for the lifetime of the ChannelDataScope
			void setTileOrigin( const Imath::V2i *tileOrigin );
			void setChannelName( const std::string *channelName );
		};
		//@}

		/// @name Convenience accessors
		/// These functions create a GlobalScope or ChannelDataScope
		/// as appropriate, and return the value or hash from one of
		/// the child plugs.
		/// > Note : If you wish to evaluate multiple plugs in the same
		/// > context, you can get improved performance by creating the
		/// > the appropriate scope class manually and then calling
		/// > `getValue()` or `hash()` directly.
		////////////////////////////////////////////////////////////////////
		//@{
		/// Calls `channelDataPlug()->getValue()` using a ChannelDataScope.
		IECore::ConstFloatVectorDataPtr channelData( const std::string &channelName, const Imath::V2i &tileOrigin ) const;
		/// Calls `channelDataPlug()->hash()` using a ChannelDataScope.
		IECore::MurmurHash channelDataHash( const std::string &channelName, const Imath::V2i &tileOrigin ) const;
		/// Calls `formatPlug()->getValue()` using a GlobalScope.
		GafferImage::Format format() const;
		/// Calls `formatPlug()->hash()` using a GlobalScope.
		IECore::MurmurHash formatHash() const;
		/// Calls `dataWindowPlug()->getValue()` using a GlobalScope.
		Imath::Box2i dataWindow() const;
		/// Calls `dataWindowPlug()->hash()` using a GlobalScope.
		IECore::MurmurHash dataWindowHash() const;
		/// Calls `channelNamesPlug()->getValue()` using a GlobalScope.
		IECore::ConstStringVectorDataPtr channelNames() const;
		/// Calls `channelNamesPlug()->hash()` using a GlobalScope.
		IECore::MurmurHash channelNamesHash() const;
		/// Calls `metadataPlug()->getValue()` using a GlobalScope.
		IECore::ConstCompoundDataPtr metadata() const;
		/// Calls `metadataPlug()->hash()` using a GlobalScope.
		IECore::MurmurHash metadataHash() const;
		/// Calls `deepPlug()->getValue()` using a GlobalScope.
		bool deep() const;
		/// Calls `deepPlug()->hash()` using a GlobalScope.
		IECore::MurmurHash deepHash() const;
		/// Calls `sampleOffsetsPlug()->getValue()` using a ChannelDataScope.
		IECore::ConstIntVectorDataPtr sampleOffsets( const Imath::V2i &tileOrigin ) const;
		/// Calls `sampleOffsetsPlug()->hash()` using a ChannelDataScope.
		IECore::MurmurHash sampleOffsetsHash( const Imath::V2i &tileOrigin ) const;
		//@}

		/// @name Tile utilities
		////////////////////////////////////////////////////////////////////
		//@{
		static const IECore::IntVectorData *emptyTileSampleOffsets();
		static const IECore::IntVectorData *flatTileSampleOffsets();
		static const IECore::FloatVectorData *emptyTile();
		static const IECore::FloatVectorData *blackTile();
		static const IECore::FloatVectorData *whiteTile();

		inline static int tileSize() { return 1 << tileSizeLog2(); };
		inline static int tilePixels() { return tileSize() * tileSize(); };

		/// Returns the index of the tile containing a point
		/// This just means dividing by tile size ( always rounding down )
		inline static const Imath::V2i tileIndex( const Imath::V2i &point )
		{
			return Imath::V2i( point.x >> tileSizeLog2(), point.y >> tileSizeLog2() );
		};

		/// Returns the origin of the tile that contains the point.
		inline static Imath::V2i tileOrigin( const Imath::V2i &point )
		{
			return tileIndex( point ) * tileSize();
		}

		/// Returns the unwrapped index of a point within a tile
		inline static int pixelIndex( const Imath::V2i &point, const Imath::V2i &tileOrigin )
		{
			return ( ( point.y - tileOrigin.y ) << tileSizeLog2() ) + point.x - tileOrigin.x;
		};

		/// Returns the pixel corresponding to an unwrapped index
		inline static Imath::V2i indexPixel( int index, const Imath::V2i &tileOrigin )
		{
			int y = index >> tileSizeLog2();
			return Imath::V2i( index - ( y << tileSizeLog2() ) + tileOrigin.x, y + tileOrigin.y );
		};
		//@}

	private :

		static int tileSizeLog2() { return 7; };

		static void compoundObjectToCompoundData( const IECore::CompoundObject *object, IECore::CompoundData *data );

		static size_t g_firstPlugIndex;
};

IE_CORE_DECLAREPTR( ImagePlug );

typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, ImagePlug> > ImagePlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, ImagePlug> > InputImagePlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, ImagePlug> > OutputImagePlugIterator;

typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, ImagePlug>, Gaffer::PlugPredicate<> > RecursiveImagePlugIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, ImagePlug>, Gaffer::PlugPredicate<> > RecursiveInputImagePlugIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, ImagePlug>, Gaffer::PlugPredicate<> > RecursiveOutputImagePlugIterator;

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGEPLUG_H
