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

#pragma once

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
		///
		/// In order to evaluate these plugs, you must have appropriate
		/// variables set in the current context.  All plugs besides
		/// view names require the `viewNameContextName` variable to be
		/// set.  It must be one of the names from the value of viewNamesPlug,
		/// unless viewNamesPlug reports that one of the view names is
		/// "default", which means that any view name may be requested,
		/// and the default will be used if it isn't found.
		///
		/// The sampleOffsets plug is only used for deep images, and
		/// returns one tile of data at a time - you must set
		/// `tileOriginContextName` to a V2i where X and Y are multiples
		/// of tileSize() in order to read it.
		///
		/// The channelData plug returns the actual pixel data for one
		/// tile of one channel.  To read it you must set both
		/// `tileOriginContextName` and `channelNameContextName`.
		////////////////////////////////////////////////////////////////////
		//@{
		Gaffer::StringVectorDataPlug *viewNamesPlug();
		const Gaffer::StringVectorDataPlug *viewNamesPlug() const;
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
		/// The names used to specify the view name, channel name
		/// and tile of interest via a Context object. You should
		/// use these variables rather than hardcoding string
		/// values - it is both less error prone and quicker than
		/// constructing InternedStrings on every lookup.
		static const IECore::InternedString viewNameContextName;
		static const IECore::InternedString channelNameContextName;
		static const IECore::InternedString tileOriginContextName;

		/// Utility class to scope a temporary copy of a context,
		/// with tile/channel specific variables removed. This can be used
		/// when evaluating plugs which must be global to a view
		/// and can improve performance by reducing pressure on the hash cache.
		/// Note that when accessing viewNames, you should also remove the view
		/// from the context.
		struct GAFFERIMAGE_API GlobalScope : public Gaffer::Context::EditableScope
		{
			GlobalScope( const Gaffer::Context *context );
			GlobalScope( const Gaffer::ThreadState &threadState );
		};

		/// Utility class to scope a temporary copy of a context,
		/// with convenient accessors to set viewName.  The
		/// viewName must always be set while accessing an image,
		/// it is set to "default" in the script context by
		/// default, which allows accessing single-view images,
		/// but you must set it when accessing multi-view images.
		struct GAFFERIMAGE_API ViewScope : public Gaffer::Context::EditableScope
		{
			ViewScope( const Gaffer::Context *context );
			ViewScope( const Gaffer::ThreadState &threadState );

			// This calls takes a pointer, and it is the caller's
			// responsibility to ensure that the memory pointed to
			// stays valid for the lifetime of the ViewScope
			void setViewName( const std::string *viewName );

			// Same as above, except it throws an exception if the specified view name is not valid
			// for the given viewNames
			void setViewNameChecked( const std::string *viewName, const IECore::StringVectorData *viewNames );
		};

		/// Utility class to scope a temporary copy of a context,
		/// with convenient accessors to set tileOrigin and channelName,
		/// which you often need to do while accessing channelData
		struct GAFFERIMAGE_API ChannelDataScope : public ViewScope
		{
			ChannelDataScope( const Gaffer::Context *context );
			ChannelDataScope( const Gaffer::ThreadState &threadState );

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
		/// If viewName is not specified, then viewName must be set in
		/// the context you are calling with
		////////////////////////////////////////////////////////////////////
		//@{
		/// Calls `channelDataPlug()->getValue()` using a ChannelDataScope.
		IECore::ConstFloatVectorDataPtr channelData( const std::string &channelName, const Imath::V2i &tileOrigin, const std::string *viewName = nullptr ) const;
		/// Calls `channelDataPlug()->hash()` using a ChannelDataScope.
		IECore::MurmurHash channelDataHash( const std::string &channelName, const Imath::V2i &tileOrigin, const std::string *viewName = nullptr ) const;
		/// Calls `viewNamesPlug()->getValue()` using a GlobalScope.
		IECore::ConstStringVectorDataPtr viewNames() const;
		/// Calls `viewNamesPlug()->hash()` using a GlobalScope.
		IECore::MurmurHash viewNamesHash() const;
		/// Calls `formatPlug()->getValue()` using a GlobalScope.
		GafferImage::Format format( const std::string *viewName = nullptr ) const;
		/// Calls `formatPlug()->hash()` using a GlobalScope.
		IECore::MurmurHash formatHash( const std::string *viewName = nullptr ) const;
		/// Calls `dataWindowPlug()->getValue()` using a GlobalScope.
		Imath::Box2i dataWindow( const std::string *viewName = nullptr ) const;
		/// Calls `dataWindowPlug()->hash()` using a GlobalScope.
		IECore::MurmurHash dataWindowHash( const std::string *viewName = nullptr ) const;
		/// Calls `channelNamesPlug()->getValue()` using a GlobalScope.
		IECore::ConstStringVectorDataPtr channelNames( const std::string *viewName = nullptr ) const;
		/// Calls `channelNamesPlug()->hash()` using a GlobalScope.
		IECore::MurmurHash channelNamesHash( const std::string *viewName = nullptr ) const;
		/// Calls `metadataPlug()->getValue()` using a GlobalScope.
		IECore::ConstCompoundDataPtr metadata( const std::string *viewName = nullptr ) const;
		/// Calls `metadataPlug()->hash()` using a GlobalScope.
		IECore::MurmurHash metadataHash( const std::string *viewName = nullptr ) const;
		/// Calls `deepPlug()->getValue()` using a GlobalScope.
		bool deep( const std::string *viewName = nullptr ) const;
		/// Calls `deepPlug()->hash()` using a GlobalScope.
		IECore::MurmurHash deepHash( const std::string *viewName = nullptr ) const;
		/// Calls `sampleOffsetsPlug()->getValue()` using a ChannelDataScope.
		IECore::ConstIntVectorDataPtr sampleOffsets( const Imath::V2i &tileOrigin, const std::string *viewName = nullptr ) const;
		/// Calls `sampleOffsetsPlug()->hash()` using a ChannelDataScope.
		IECore::MurmurHash sampleOffsetsHash( const Imath::V2i &tileOrigin, const std::string *viewName = nullptr ) const;
		//@}

		/// @name View utilities
		////////////////////////////////////////////////////////////////////
		//@{
		static const std::string defaultViewName;
		static const IECore::StringVectorData *defaultViewNames();
		//@}

		/// @name Tile utilities
		////////////////////////////////////////////////////////////////////
		//@{
		static const IECore::IntVectorData *emptyTileSampleOffsets();
		static const IECore::IntVectorData *flatTileSampleOffsets();
		static const IECore::FloatVectorData *emptyTile();
		static const IECore::FloatVectorData *blackTile();
		static const IECore::FloatVectorData *whiteTile();

		static int tileSize() { return 1 << tileSizeLog2(); };
		static int tilePixels() { return tileSize() * tileSize(); };

		/// Returns the index of the tile containing a point
		/// This just means dividing by tile size ( always rounding down )
		static const Imath::V2i tileIndex( const Imath::V2i &point )
		{
			return Imath::V2i( point.x >> tileSizeLog2(), point.y >> tileSizeLog2() );
		};

		/// Returns the origin of the tile that contains the point.
		static Imath::V2i tileOrigin( const Imath::V2i &point )
		{
			return tileIndex( point ) * tileSize();
		}

		/// Returns the unwrapped index of a point within a tile
		static int pixelIndex( const Imath::V2i &point, const Imath::V2i &tileOrigin )
		{
			return ( ( point.y - tileOrigin.y ) << tileSizeLog2() ) + point.x - tileOrigin.x;
		};

		/// Returns the pixel corresponding to an unwrapped index
		static Imath::V2i indexPixel( int index, const Imath::V2i &tileOrigin )
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

} // namespace GafferImage
