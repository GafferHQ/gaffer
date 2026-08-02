//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Lucien Fostier. All rights reserved.
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

#include "GafferOFX/Export.h"
#include "GafferOFX/TypeIds.h"
#include "GafferOFX/EffectImageInstance.h"

#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"

#include "GafferImage/ImageProcessor.h"

#include <mutex>
#include <atomic>

namespace GafferOFX
{

class GafferOFXInteractInstance;

class GAFFEROFX_API OFXImageNode : public GafferImage::ImageProcessor
{

	public :

		explicit OFXImageNode( const std::string &name=defaultName<OFXImageNode>() );
		~OFXImageNode() override;
		
		GAFFER_NODE_DECLARE_TYPE( GafferOFX::OFXImageNode, OFXImageNodeTypeId, GafferImage::ImageProcessor );

		bool createPluginInstance();

		Gaffer::StringPlug* pluginIdPlug();
		const Gaffer::StringPlug* pluginIdPlug() const;


		Gaffer::Plug *parametersPlug();
		const Gaffer::Plug *parametersPlug() const;

		/// Renderer preference for GL-capable plugins: Auto (0), CPU (1),
		/// GPU (2).  CPU renders through the software EGL device; GPU
		/// forces the hardware device.
		Gaffer::IntPlug *GLRenderModePlug();
		const Gaffer::IntPlug *GLRenderModePlug() const;


		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		const GafferOFX::EffectImageInstance* effectInstance() const;

		Gaffer::CompoundObjectPlug *ofxRenderBufferPlug();
		const Gaffer::CompoundObjectPlug *ofxRenderBufferPlug() const;

		Gaffer::ObjectPlug *tileBufferPlug();
		const Gaffer::ObjectPlug *tileBufferPlug() const;

	protected :

		void hashViewNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashSampleOffsets( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;

		void hashOfxRenderBuffer( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		void hashTileBuffer( const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

		IECore::ConstStringVectorDataPtr computeViewNames( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;
		GafferImage::Format computeFormat( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;
		Imath::Box2i computeDataWindow( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;
		IECore::ConstCompoundDataPtr computeMetadata( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;
		bool computeDeep( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;
		IECore::ConstIntVectorDataPtr computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;
		IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;

		IECore::ConstCompoundObjectPtr computeOfxRenderBuffer( const Gaffer::Context *context ) const;
		IECore::ConstCompoundObjectPtr computeTileBuffer( const Gaffer::Context *context ) const;


	public :

		bool hasOverlay() const;
		class GafferOFXInteractInstance* getInteract();
		void destroyInteract();

		int rendering() const { return m_rendering; }
		bool settingFromPlugin() const { return m_settingFromPlugin; }
		void setSettingFromPlugin( bool v ) const { m_settingFromPlugin = v; }

		/// Render thread safety level read from plugin descriptor at instantiation.
		enum class RenderSafety { Unknown, FullySafe, InstanceSafe, Unsafe };

	private :

		void plugSet( Gaffer::Plug *plug );
		void removeClipPlugs();
		void createClipPlugs();
		void setAllClipProps();

		static size_t g_firstPlugIndex;
		mutable std::unique_ptr<GafferOFX::EffectImageInstance> m_instance;
		mutable std::atomic<bool> m_glContextAttached = false;
		/// GLContextManager::contextGeneration() at the last contextAttached.
		/// A mismatch means the shared context was rebuilt onto another
		/// device since this node attached — plugin GL state is dead.
		mutable std::atomic<int> m_glContextGeneration = -1;
		mutable std::atomic<int> m_rendering = 0;
		mutable bool m_settingFromPlugin = false;
		mutable bool m_tiledRenderSupported = false;
		mutable RenderSafety m_renderThreadSafety = RenderSafety::Unknown;
		mutable std::mutex m_renderMutex;
		mutable std::mutex m_globalRenderMutex;
		std::vector<std::string> m_clipPlugNames;
		std::unique_ptr<GafferOFXInteractInstance> m_interactInstance;

};

IE_CORE_DECLAREPTR( OFXImageNode )

} // namespace GafferOFX
