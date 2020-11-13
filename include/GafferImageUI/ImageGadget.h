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

#include "GafferImageUI/Export.h"
#include "GafferImageUI/TypeIds.h"

#include "GafferImage/Clamp.h"
#include "GafferImage/DeepState.h"
#include "GafferImage/Format.h"
#include "GafferImage/Grade.h"
#include "GafferImage/ImageProcessor.h"

#include "GafferUI/Gadget.h"

#include "Gaffer/ParallelAlgo.h"

#include "IECore/Canceller.h"
#include "IECore/MurmurHash.h"
#include "IECore/VectorTypedData.h"
#include "IECoreGL/Shader.h"

#include "OpenColorIO/OpenColorIO.h"

#include "tbb/concurrent_unordered_map.h"
#include "tbb/spin_mutex.h"

#include <array>

#include <chrono>

namespace IECoreGL
{

IE_CORE_FORWARDDECLARE( Texture )

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

class GAFFERIMAGEUI_API ImageGadget : public GafferUI::Gadget
{

	public :

		ImageGadget();
		~ImageGadget() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImageUI::ImageGadget, ImageGadgetTypeId, Gadget );

		Imath::Box3f bound() const override;

		void setImage( GafferImage::ImagePlugPtr image );
		const GafferImage::ImagePlug *getImage() const;

		void setContext( Gaffer::ContextPtr context );
		Gaffer::Context *getContext();
		const Gaffer::Context *getContext() const;

		typedef std::array<IECore::InternedString, 4> Channels;
		/// Chooses which 4 channels to display as RGBA.
		/// For instance, to display Z as a greyscale image
		/// with black alpha you would pass { "Z", "Z", "Z", "" }.
		void setChannels( const Channels &channels );
		const Channels &getChannels() const;

		typedef boost::signal<void (ImageGadget *)> ImageGadgetSignal;
		ImageGadgetSignal &channelsChangedSignal();

		/// Chooses a channel to show in isolation.
		/// Indices are in the range 0-3 to choose
		/// which of the RGBA channels is soloed, or
		/// -1 to show a colour image as usual.
		void setSoloChannel( int index );
		int getSoloChannel() const;

		void setClipping( bool clipping );
		bool getClipping() const;

		void setExposure( float exposure );
		float getExposure() const;

		void setGamma( float gamma );
		float getGamma() const;

		void setDisplayTransform( GafferImage::ImageProcessorPtr displayTransform );
		GafferImage::ConstImageProcessorPtr getDisplayTransform() const;

		void setUseGPU( bool useGPU );
		bool getUseGPU() const;

		void setLabelsVisible( bool visible );
		bool getLabelsVisible() const;

		void setPaused( bool paused );
		bool getPaused() const;

		static uint64_t tileUpdateCount();
		static void resetTileUpdateCount();

		enum State
		{
			Paused,
			Running,
			Complete
		};

		State state() const;
		ImageGadgetSignal &stateChangedSignal();

		Imath::V2f pixelAt( const IECore::LineSegment3f &lineInGadgetSpace ) const;

	protected :

		void doRenderLayer( Layer layer, const GafferUI::Style *style ) const override;

	private :

		// Image and context. We must monitor these so
		// that dirtying of the plug or changes to the context
		// can be used to trigger a render request.

		void plugDirtied( const Gaffer::Plug *plug );
		void contextChanged( const IECore::InternedString &name );

		GafferImage::ImagePlugPtr m_image;
		Gaffer::ContextPtr m_context;

		boost::signals::scoped_connection m_plugDirtiedConnection;
		boost::signals::scoped_connection m_contextChangedConnection;

		// Settings to control how the image is displayed.

		void displayTransformPlugDirtied( const Gaffer::Plug *plug );
		bool usingGPU() const;

		Channels m_rgbaChannels;
		int m_soloChannel;
		ImageGadgetSignal m_channelsChangedSignal;

		bool m_clipping;
		float m_exposure;
		float m_gamma;

		GafferImage::DeepStatePtr m_deepStateNode;
		GafferImage::ClampPtr m_clampNode;
		GafferImage::GradePtr m_gradeNode;
		GafferImage::ImageProcessorPtr m_displayTransform;

		bool m_useGPU;
		bool m_labelsVisible;
		bool m_paused;
		ImageGadgetSignal m_stateChangedSignal;

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

		void dirty( unsigned flags );
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

			Tile() = default;
			Tile( const Tile &other );

			struct Update
			{
				Tile *tile;
				IECore::ConstFloatVectorDataPtr channelData;
				const IECore::MurmurHash channelDataHash;
			};

			// Called from a background thread with the context
			// already set up appropriately for the tile.
			Update computeUpdate( const GafferImage::ImagePlug *image );
			// Applies previously computed updates for several tiles
			// such that they become visible to the UI thread together.
			static void applyUpdates( const std::vector<Update> &updates );

			// Called from the UI thread.
			const IECoreGL::Texture *texture( bool &active );

			private :

				IECore::MurmurHash m_channelDataHash;
				IECore::ConstFloatVectorDataPtr m_channelDataToConvert;
				IECoreGL::TexturePtr m_texture;
				bool m_active;
				std::chrono::steady_clock::time_point m_activeStartTime;
				typedef tbb::spin_mutex Mutex;
				Mutex m_mutex;

		};

		typedef tbb::concurrent_unordered_map<TileIndex, Tile> Tiles;
		mutable Tiles m_tiles;

		friend size_t tbb_hasher( const ImageGadget::TileIndex &tileIndex );

		// Tile update. We update tiles asynchronously from background
		// threads.

		void updateTiles();
		void removeOutOfBoundsTiles() const;

		std::unique_ptr<Gaffer::BackgroundTask> m_tilesTask;
		std::atomic_bool m_renderRequestPending;

		// Rendering.

		void visibilityChanged();
		void renderTiles() const;
		void renderText( const std::string &text, const Imath::V2f &position, const Imath::V2f &alignment, const GafferUI::Style *style ) const;

		IE_CORE_FORWARDDECLARE( TileShader )
		TileShader *shader() const;
		mutable TileShaderPtr m_shader;
		mutable bool m_shaderDirty;

		// Track index of the max tile that got updated last render.  This may not be the max tile in
		// the dataWindow, if the last render was cancelled.
		std::atomic<int> m_maxTileUpdated;

};

IE_CORE_DECLAREPTR( ImageGadget )

size_t tbb_hasher( const ImageGadget::TileIndex &tileIndex );

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<ImageGadget> > ImageGadgetIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<ImageGadget> > RecursiveImageGadgetIterator;

} // namespace GafferImageUI

#endif // GAFFERIMAGEUI_IMAGEGADGET_H
