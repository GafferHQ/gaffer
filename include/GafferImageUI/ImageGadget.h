//////////////////////////////////////////////////////////////////////////
//
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

#ifndef GAFFERIMAGEUI_IMAGEGADGET_H
#define GAFFERIMAGEUI_IMAGEGADGET_H

#include "tbb/concurrent_unordered_map.h"

#include "IECore/MurmurHash.h"
#include "IECore/VectorTypedData.h"

#include "GafferUI/Gadget.h"

#include "GafferImage/Format.h"

#include "GafferImageUI/TypeIds.h"

namespace IECoreGL
{

IE_CORE_FORWARDDECLARE( LuminanceTexture )

} // namespace IECoreGL

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Plug )
IE_CORE_FORWARDDECLARE( Context )

} // namespace Gaffer

namespace GafferImage
{

IE_CORE_FORWARDDECLARE( ImagePlug )

} // namespace GafferImage

namespace GafferImageUI
{

class ImageGadget : public GafferUI::Gadget
{

	public :

		ImageGadget();
		virtual ~ImageGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImageUI::ImageGadget, ImageGadgetTypeId, Gadget );

		virtual Imath::Box3f bound() const;

		void setImage( GafferImage::ConstImagePlugPtr image );
		const GafferImage::ImagePlug *getImage() const;

		void setContext( Gaffer::ContextPtr context );
		Gaffer::Context *getContext();
		const Gaffer::Context *getContext() const;

		/// Chooses a channel to show in isolation.
		/// Indices are in the range 0-3 to choose
		/// which of the RGBA channels is soloed, or
		/// -1 to show a colour image as usual.
		void setSoloChannel( int index );
		int getSoloChannel() const;

		Imath::V2f pixelAt( const IECore::LineSegment3f &lineInGadgetSpace ) const;

	protected :

		virtual void doRender( const GafferUI::Style *style ) const;

	private :

		// Image and context. We must monitor these so
		// that dirtying of the plug or changes to the context
		// can be used to trigger a render request.

		void plugDirtied( const Gaffer::Plug *plug );
		void contextChanged( const IECore::InternedString &name );

		GafferImage::ConstImagePlugPtr m_image;
		Gaffer::ContextPtr m_context;

		boost::signals::scoped_connection m_plugDirtiedConnection;
		boost::signals::scoped_connection m_contextChangedConnection;

		// Settings to control how the image is displayed.

		boost::array<IECore::InternedString, 4> m_rgbaChannels;
		int m_soloChannel;

		// Image access.
		//
		// We only pull on the m_image plug lazily when
		// we need something, and store the result for later
		// use. These flags and the member variables below
		// are used to implement this caching. Note that the
		// access functions do nothing to handle errors during
		// computation, so exceptions must be handled by the
		// caller.
		enum DirtyFlags
		{
			NothingDirty = 0,
			FormatDirty = 1,
			DataWindowDirty = 2,
			ChannelNamesDirty = 4,
			TilesDirty = 8,
			AllDirty = FormatDirty | DataWindowDirty | ChannelNamesDirty | TilesDirty
		};

		const GafferImage::Format &format() const;
		const Imath::Box2i &dataWindow() const;
		const std::vector<std::string> &channelNames() const;

		mutable unsigned m_dirtyFlags;
		mutable GafferImage::Format m_format;
		mutable Imath::Box2i m_dataWindow;
		mutable std::vector<std::string> m_channelNames;

		// Tile storage.
		//
		// We store the image to draw as individual textures
		// representing each channel of each tile. These are
		// stored in a concurrent_unordered_map so they can
		// be inserted/updated in parallel in a multithreaded
		// update step.

		struct TileIndex
		{
			TileIndex( const Imath::V2i &tileOrigin, IECore::InternedString channelName )
				:	tileOrigin( tileOrigin ), channelName( channelName )
			{
			}

			bool operator == ( const TileIndex &rhs ) const
			{
				return tileOrigin == rhs.tileOrigin && channelName == rhs.channelName;
			}

			Imath::V2i tileOrigin;
			IECore::InternedString channelName;
		};

		struct Tile
		{
			IECore::MurmurHash channelDataHash;
			// Updated in parallel when the hash has changed.
			IECore::ConstFloatVectorDataPtr channelDataToConvert;
			// Created from channelDataToConvert in a serial process,
			// because we can only to OpenGL work on the main thread.
			IECoreGL::TexturePtr texture;
		};

		void updateTiles() const;
		void removeOutOfBoundsTiles() const;

		typedef tbb::concurrent_unordered_map<TileIndex, Tile> Tiles;
		mutable Tiles m_tiles;

		friend size_t tbb_hasher( const ImageGadget::TileIndex &tileIndex );

		struct TileFunctor;

		// Rendering.

		void renderTiles() const;
		void renderText( const std::string &text, const Imath::V2f &position, const Imath::V2f &alignment, const GafferUI::Style *style ) const;

};

size_t tbb_hasher( const ImageGadget::TileIndex &tileIndex );

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<ImageGadget> > ImageGadgetIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<ImageGadget> > RecursiveImageGadgetIterator;

} // namespace GafferImageUI

#endif // GAFFERIMAGEUI_IMAGEGADGET_H
