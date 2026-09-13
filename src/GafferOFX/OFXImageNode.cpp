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

#ifdef OFX_SUPPORTS_OPENGLRENDER
#include <GL/gl.h>
#include <GL/glext.h>

#include <iostream>

#include "GafferOFX/GLContextManager.h"
#endif

#include "GafferOFX/OFXImageNode.h"
#include "GafferOFX/Host.h"
#include "GafferOFX/ClipInstance.h"
#include "GafferOFX/OFXInteractInstance.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/ArrayPlug.h"
// CompoundObjectPlug provided via OFXImageNode.h which includes Gaffer/TypedObjectPlug.h

#include "GafferImage/ImageAlgo.h"
#include "GafferImage/Sampler.h"

#include "IECore/BoxOps.h"
#include "IECore/NullObject.h"

#ifdef OFX_SUPPORTS_OPENGLRENDER
#include "ofxGPURender.h"
#endif

#include <algorithm>
#include <atomic>
#include <cctype>
#include <chrono>
#include <cstdlib>
#include <exception>
#include <functional>
#include <mutex>
#include <sstream>
#include <thread>
#include <unordered_map>
#include <condition_variable>
#include <vector>

// Instrumentation for tile concurrency measurement.
namespace
{

// Per-thread render depth so nested pulls don't inflate concurrency.
// g_activeThreads counts how many threads have t_tileDepth > 0.
thread_local int t_tileDepth = 0;
std::atomic<int> g_activeThreads{ 0 };
std::atomic<int> g_threadHighWater{ 0 };

// Env-var spin for scaling check: GAFFEROFX_TILE_SPIN_MS
int tileSpinMs()
{
	static int ms = []() {
		const char *env = std::getenv( "GAFFEROFX_TILE_SPIN_MS" );
		return env ? std::atoi( env ) : 0;
	}();
	return ms;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Dedicated render worker thread
//
// All renders are dispatched to a single persistent background thread:
//  - Keeps the main thread responsive (no freeze)
//  - GL plugins reuse their context (no per-tile shader recompilation)
//  - Avoids CPU saturation from concurrent renders
//////////////////////////////////////////////////////////////////////////

class OFXRenderWorker
{
public:

	static OFXRenderWorker &instance()
	{
		static OFXRenderWorker w;
		return w;
	}

	template<typename F>
	void execute( F &&func )
	{
		// Re-entrancy guard: if the worker thread itself calls execute()
		// (e.g. via a Gaffer pull inside renderAction), run inline to
		// avoid self-deadlock on m_mutex.
		if( std::this_thread::get_id() == m_thread.get_id() )
		{
			func();
			return;
		}
		std::unique_lock<std::mutex> lock( m_mutex );
		m_task = std::forward<F>( func );
		m_ready = true;
		m_cv.notify_one();
		m_cv.wait( lock, [this]() { return !m_ready; } );
		if( m_exception )
		{
			auto ex = std::move( m_exception );
			std::rethrow_exception( ex );
		}
	}

	~OFXRenderWorker()
	{
		{
			std::lock_guard<std::mutex> lock( m_mutex );
			m_done = true;
			m_ready = true;
		}
		m_cv.notify_one();
		if( m_thread.joinable() )
		{
			m_thread.join();
		}
	}

private:

	OFXRenderWorker()
	{
		m_thread = std::thread( [this]() { workerLoop(); } );
	}

	void workerLoop()
	{
		std::unique_lock<std::mutex> lock( m_mutex );
		while( !m_done )
		{
			m_cv.wait( lock, [this]() { return m_ready; } );
			if( m_done )
			{
				break;
			}
			try
			{
				m_task();
			}
			catch( ... )
			{
				m_exception = std::current_exception();
			}
			m_ready = false;
			m_cv.notify_one();
		}
	}

	std::thread m_thread;
	std::mutex m_mutex;
	std::condition_variable m_cv;
	std::function<void()> m_task;
	std::exception_ptr m_exception;
	bool m_ready = false;
	bool m_done = false;
};

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;
using namespace GafferOFX;

// RAII guard that increments m_rendering and decrements on scope exit.
// Concurrent tiles each hold their own increment, so m_rendering > 0
// while any tile is rendering.
struct RenderingCounter
{
	std::atomic<int> &counter;
	RenderingCounter( std::atomic<int> &c ) : counter( c ) { ++counter; }
	~RenderingCounter() { --counter; }
};

//////////////////////////////////////////////////////////////////////////
// OFXImageNode implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( OFXImageNode );

size_t OFXImageNode::g_firstPlugIndex = 0;

OFXImageNode::OFXImageNode( const std::string &name )
    : ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "pluginId" ) );
	addChild( new Plug( "parameters", Plug::In, Plug::Default & ~Plug::AcceptsInputs ) );
	IntPlug *GLRenderMode = new IntPlug( "GLRenderMode", Plug::In, 0, 0, 2 );
	addChild( GLRenderMode );
	addChild( new CompoundObjectPlug( "__ofxRenderBuffer", Plug::Out, new CompoundObject, Plug::Default & ~Plug::Serialisable ) );
        addChild( new ObjectPlug( "__ofxTileBuffer", Plug::Out, IECore::NullObject::defaultNullObject(), Plug::Default & ~Plug::Serialisable ) );
	plugSetSignal().connect( [this]( Gaffer::Plug *plug ) { plugSet( plug ); } );
}

void OFXImageNode::plugSet( Gaffer::Plug *plug )
{
	if( plug == pluginIdPlug() )
	{
		destroyInteract();
		if( m_glContextAttached )
		{
			// Marshal detach through worker so the GL context is current.
			// Only dispatch if the old effect instance has GL support.
			OFXRenderWorker::instance().execute( [this]() {
				GLContextManager::instance().makeCurrent();
				m_instance->contextDetachedAction();
			} );
			m_glContextAttached = false;
		}
		m_instance.reset();
		createPluginInstance();
	}
	else if( m_instance && parametersPlug()->isAncestorOf( plug ) )
	{
	if( m_rendering > 0 )
	{
		return;
	}
		if( m_settingFromPlugin )
		{
			return;
		}
		OfxTime time = 0.0;
		if( const Gaffer::Context *ctx = Gaffer::Context::current() )
		{
			time = ctx->getFrame();
		}
		OfxPointD renderScale = { 1.0, 1.0 };
		m_instance->beginInstanceChangedAction( kOfxChangeUserEdited );
		m_instance->paramInstanceChangedAction( plug->getName().string(), kOfxChangeUserEdited, time, renderScale );
		m_instance->endInstanceChangedAction( kOfxChangeUserEdited );
		// Params can legitimately change clip prefs; re-evaluate.
		m_instance->getClipPreferences();
	}
}

OFXImageNode::~OFXImageNode()
{
}

bool OFXImageNode::createPluginInstance()
{
	if( m_instance )
	{
		return true;
	}

	Host& host = Host::instance();
	std::string pluginId = pluginIdPlug()->getValue();
	auto plugin = host.m_pluginCache.getPluginById(pluginId);
	if( plugin )
	{
		// Remove clip plugs from any previous instance
		removeClipPlugs();

		// Use the first available context supported by the plugin
		const std::set<std::string> &contexts = plugin->getContexts();
		std::vector<std::string> contextPriority;
		if( contexts.find( kOfxImageEffectContextFilter ) != contexts.end() )
		{
			contextPriority.push_back( kOfxImageEffectContextFilter );
		}
		if( contexts.find( kOfxImageEffectContextGeneral ) != contexts.end() )
		{
			contextPriority.push_back( kOfxImageEffectContextGeneral );
		}
		if( contexts.find( kOfxImageEffectContextGenerator ) != contexts.end() )
		{
			contextPriority.push_back( kOfxImageEffectContextGenerator );
		}
		for( const auto &c : contexts )
		{
			if( c != kOfxImageEffectContextFilter &&
			    c != kOfxImageEffectContextGeneral &&
			    c != kOfxImageEffectContextGenerator )
			{
				contextPriority.push_back( c );
			}
		}

		if( contextPriority.empty() )
		{
			return false;
		}

		OFX::Host::ImageEffect::Instance *instance = nullptr;
		for( const auto &context : contextPriority )
		{
			instance = plugin->createInstance( context, this );
			if( instance )
			{
				break;
			}
		}

		if( !instance )
		{
			return false;
		}

		m_instance.reset( static_cast<EffectImageInstance*>( instance ) );

		m_instance->createInstanceAction();

		// Verify this plugin supports float pixel depth.  GafferOFX renders
		// everything in 32-bit float and does not perform byte conversion.
		// Query the plugin DESCRIPTOR's property set (not the instance's) —
		// the instance props don't reliably chain for string-property lookups.
		{
			bool supportsFloat = false;
			const auto &dp = m_instance->getPlugin()->getDescriptor().getProps();
			try
			{
				int n = dp.getDimension( kOfxImageEffectPropSupportedPixelDepths );
				for( int i = 0; i < n && !supportsFloat; ++i )
				{
					supportsFloat = dp.getStringProperty( kOfxImageEffectPropSupportedPixelDepths, i ) == kOfxBitDepthFloat;
				}
			}
			catch( const std::exception & ) {}
			if( !supportsFloat )
			{
				std::cerr << "GafferOFX: rejecting plugin \"" << m_instance->getPlugin()->getIdentifier()
				          << "\" — does not advertise kOfxBitDepthFloat in kOfxImageEffectPropSupportedPixelDepths"
				          << std::endl;
				m_instance.reset();
				return false;
			}
		}

		// Give plugins a chance to set up frame-dependent state once at
		// instantiation, not during hashing (which must be side-effect-free).
		m_instance->getClipPreferences();

		// Detect whether this plugin supports tiled rendering.
		// GL plugins always use full-frame (FBO/readback overhead).
		// CPU plugins with SupportsTiles=1 can render per-tile.
		// CImg plugins claim supportsTiles but assert srcRoD.x1 == dstRoD.x1,
		// making them incompatible with tile-sized render windows.
		m_tiledRenderSupported = false;
		{
			bool pluginSupportsGL = false;
			try
			{
				std::string val = m_instance->getPlugin()->getDescriptor().getProps().getStringProperty(
					kOfxImageEffectPropOpenGLRenderSupported
				);
				pluginSupportsGL = ( val == "true" || val == "needed" );
			}
			catch( const std::exception & ) {}
			std::string pluginId = m_instance->getPlugin()->getIdentifier();
			bool isCImg = pluginId.find( "net.sf.cimg." ) == 0 || pluginId.find( "eu.cimg." ) == 0;
			bool supportsTiles = false;
			try { supportsTiles = m_instance->supportsTiles(); } catch( const std::exception & ) {}
			if( !pluginSupportsGL && supportsTiles && !isCImg )
			{
				m_tiledRenderSupported = true;
			}
			std::cerr << "OFXImageNode: tiled=" << m_tiledRenderSupported
			          << " for \"" << pluginId << "\""
			          << " gl=" << pluginSupportsGL
			          << " tiles=" << supportsTiles
			          << " cimg=" << isCImg
			          << std::endl;
		}

		// Determine render thread safety level for tiled rendering.
		m_renderThreadSafety = RenderSafety::InstanceSafe;  // safe default
		if( m_tiledRenderSupported )
		{
			std::string val;
			try
			{
				val = m_instance->getPlugin()->getDescriptor().getProps().getStringProperty(
					kOfxImageEffectPluginRenderThreadSafety
				);
			}
			catch( const std::exception & )
			{
				val = "(no property)";
			}

			// Env override for stress testing.
			if( const char *env = std::getenv( "GAFFEROFX_THREAD_SAFETY" ) )
			{
				val = env;
				std::cerr << "OFXImageNode: env override GAFFEROFX_THREAD_SAFETY=" << env << std::endl;
			}

			if( val == kOfxImageEffectRenderFullySafe || val == "fully" )
			{
				m_renderThreadSafety = RenderSafety::FullySafe;
			}
			else if( val == kOfxImageEffectRenderUnsafe || val == "unsafe" )
			{
				m_renderThreadSafety = RenderSafety::Unsafe;
			}
			else
			{
				m_renderThreadSafety = RenderSafety::InstanceSafe;
			}

			std::cerr << "OFXImageNode: tile render thread safety for \""
			          << m_instance->getPlugin()->getIdentifier() << "\" = "
			          << val << " → "
			          << ( m_renderThreadSafety == RenderSafety::FullySafe ? "FullySafe" :
			               m_renderThreadSafety == RenderSafety::Unsafe ? "Unsafe" : "InstanceSafe" )
			          << std::endl;
		}

		// Set clip pixel depth/component properties once at instantiation
		// instead of every render.  These never change per-tile.
		setAllClipProps();

		// Dynamic getConnected() looks up plug input at call time

		// Create Gaffer plug for each non-Output, non-Source clip
		createClipPlugs();

		return true;
	}
	return false;
}

void OFXImageNode::removeClipPlugs()
{
	for( const auto &name : m_clipPlugNames )
	{
		if( auto *plug = getChild<GafferImage::ImagePlug>( name ) )
		{
			removeChild( plug );
		}
	}
	m_clipPlugNames.clear();
}

void OFXImageNode::createClipPlugs()
{
	if( !m_instance )
	{
		return;
	}

	for( int i = 0; i < m_instance->getNClips(); ++i )
	{
		auto *clip = dynamic_cast<GafferOFX::ClipInstance*>( m_instance->getNthClip( i ) );
		if( !clip )
		{
			continue;
		}

		const std::string &clipName = clip->getName();
		if( clipName == "Output" || clipName == "Source" )
		{
			continue;
		}

		// Derive Gaffer plug name from clip name (lowercase first letter + sanitize)
		std::string plugName = clipName;
		if( !plugName.empty() && isupper( plugName[0] ) )
		{
			plugName[0] = tolower( plugName[0] );
		}
		for( char &c : plugName )
		{
			if( !( ( c >= 'A' && c <= 'Z' ) || ( c >= 'a' && c <= 'z' ) || ( c >= '0' && c <= '9' ) || c == '_' || c == ':' ) )
			{
				c = '_';
			}
		}

		// Reuse existing plug if present (e.g. after scene load or re-creation)
		auto *plug = getChild<GafferImage::ImagePlug>( plugName );
		if( !plug )
		{
			plug = new GafferImage::ImagePlug( plugName, Plug::In );
			addChild( plug );
		}
		m_clipPlugNames.push_back( plugName );

		// Store the plug name on the clip for dynamic getConnected() lookup
		clip->setPlugName( plugName );
	}
}

void OFXImageNode::setAllClipProps()
{
	if( !m_instance )
	{
		return;
	}

	auto setClip = [this]( const char *name )
	{
		auto *clip = dynamic_cast<GafferOFX::ClipInstance*>( m_instance->getClip( name ) );
		if( clip )
		{
			clip->getProps().setStringProperty( kOfxImageEffectPropPixelDepth, kOfxBitDepthFloat );
			clip->getProps().setStringProperty( kOfxImageEffectPropComponents, kOfxImageComponentRGBA );
		}
	};

	setClip( "Output" );
	setClip( "Source" );

	for( const auto &plugName : m_clipPlugNames )
	{
		std::string ofxClipName = plugName;
		if( !ofxClipName.empty() && islower( ofxClipName[0] ) )
		{
			ofxClipName[0] = toupper( ofxClipName[0] );
		}
		setClip( ofxClipName.c_str() );
	}
}

Gaffer::StringPlug* OFXImageNode::pluginIdPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug* OFXImageNode::pluginIdPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::Plug *OFXImageNode::parametersPlug()
{
	return getChild<Plug>( g_firstPlugIndex + 1 );
}

const Gaffer::Plug *OFXImageNode::parametersPlug() const
{
	return getChild<Plug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *OFXImageNode::GLRenderModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *OFXImageNode::GLRenderModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

CompoundObjectPlug *OFXImageNode::ofxRenderBufferPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 3 );
}

const CompoundObjectPlug *OFXImageNode::ofxRenderBufferPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 3 );
}

ObjectPlug *OFXImageNode::tileBufferPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

const ObjectPlug *OFXImageNode::tileBufferPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

void OFXImageNode::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	// Guard against uninitialized inPlug when minInputs=0
	if( !inPlug() )
	{
		return;
	}

	if( input == GLRenderModePlug() )
	{
		outputs.push_back( ofxRenderBufferPlug() );
		outputs.push_back( tileBufferPlug() );
	}

	// Input image data affects the render buffer
	if( input == inPlug()->formatPlug() || input == inPlug()->dataWindowPlug() || input == inPlug()->channelNamesPlug() )
	{
		outputs.push_back( ofxRenderBufferPlug() );
	}

	if( m_tiledRenderSupported && inPlug()->getInput() )
	{
		// ---- Tiled path: per-tile via __ofxTileBuffer ----
		//
		// Input format/dataWindow/channelNames metadata affects the
		// render buffer (used for output format/dataWindow/channelNames).
		if( input == inPlug()->formatPlug() || input == inPlug()->dataWindowPlug() || input == inPlug()->channelNamesPlug() )
		{
			outputs.push_back( ofxRenderBufferPlug() );
		}

		// Input channel data and clip plugs drive __ofxTileBuffer.
		if( input == inPlug()->channelDataPlug() || input == inPlug()->dataWindowPlug() )
		{
			outputs.push_back( tileBufferPlug() );
		}

		for( const auto &name : m_clipPlugNames )
		{
			if( auto *imgPlug = getChild<GafferImage::ImagePlug>( name ) )
			{
				if( input == imgPlug->formatPlug() || input == imgPlug->dataWindowPlug() ||
				    input == imgPlug->channelNamesPlug() )
				{
					outputs.push_back( ofxRenderBufferPlug() );
				}
				if( input == imgPlug->channelDataPlug() || input == imgPlug->dataWindowPlug() )
				{
					outputs.push_back( tileBufferPlug() );
				}
			}
		}

		// Parameters and plugin ID drive both metadata and tile buffer.
		if( input == pluginIdPlug() )
		{
			outputs.push_back( ofxRenderBufferPlug() );
			outputs.push_back( tileBufferPlug() );
		}

		if( parametersPlug()->isAncestorOf( input ) )
		{
			outputs.push_back( ofxRenderBufferPlug() );
			outputs.push_back( tileBufferPlug() );
		}

		// Render buffer affects metadata outputs only (not channelData).
		if( input == ofxRenderBufferPlug() )
		{
			outputs.push_back( outPlug()->formatPlug() );
			outputs.push_back( outPlug()->dataWindowPlug() );
			outputs.push_back( outPlug()->channelNamesPlug() );
		}

		// Tile buffer drives per-tile channel data.
		if( input == tileBufferPlug() )
		{
			outputs.push_back( outPlug()->channelDataPlug() );
		}
	}
	else
	{
		// ---- Full-frame path: everything goes via render buffer ----
		// Input image data affects the render buffer
		if( input == inPlug()->formatPlug() || input == inPlug()->dataWindowPlug() || input == inPlug()->channelNamesPlug() )
		{
			outputs.push_back( ofxRenderBufferPlug() );
		}

		// Input channel data affects the render buffer
		if( input == inPlug()->channelDataPlug() )
		{
			outputs.push_back( ofxRenderBufferPlug() );
		}

		// Dynamic clip plugs (Mask, UV, etc.) affect the render buffer
		for( const auto &name : m_clipPlugNames )
		{
			if( auto *imgPlug = getChild<GafferImage::ImagePlug>( name ) )
			{
				if( input == imgPlug->formatPlug() || input == imgPlug->dataWindowPlug() ||
				    input == imgPlug->channelNamesPlug() || input == imgPlug->channelDataPlug() )
				{
					outputs.push_back( ofxRenderBufferPlug() );
				}
			}
		}

		// Parameters and plugin ID affect the render buffer
		if( input == pluginIdPlug() || parametersPlug()->isAncestorOf( input ) )
		{
			outputs.push_back( ofxRenderBufferPlug() );
		}

		// Render buffer affects all output image properties
		if( input == ofxRenderBufferPlug() )
		{
			outputs.push_back( outPlug()->formatPlug() );
			outputs.push_back( outPlug()->dataWindowPlug() );
			outputs.push_back( outPlug()->channelNamesPlug() );
			outputs.push_back( outPlug()->channelDataPlug() );
		}
	}
}

void OFXImageNode::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == ofxRenderBufferPlug() )
	{
		hashOfxRenderBuffer( context, h );
	}
	else if( output == tileBufferPlug() )
	{
		hashTileBuffer( context, h );
	}
	else
	{
		ImageProcessor::hash( output, context, h );
	}
}

void OFXImageNode::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == ofxRenderBufferPlug() )
	{
		IECore::ConstCompoundObjectPtr renderBuffer = computeOfxRenderBuffer( context );
		static_cast<Gaffer::CompoundObjectPlug *>( output )->setValue( renderBuffer );
	}
	else if( output == tileBufferPlug() )
	{
		IECore::ConstObjectPtr tileBuf = computeTileBuffer( context );
		if( !tileBuf )
		{
			tileBuf = IECore::NullObject::defaultNullObject();
		}
		static_cast<Gaffer::ObjectPlug *>( output )->setValue( tileBuf );
	}
	else
	{
		ImageProcessor::compute( output, context );
	}
}

void OFXImageNode::hashViewNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashViewNames( output, context, h );
}

IECore::ConstStringVectorDataPtr OFXImageNode::computeViewNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::defaultViewNames();
}

void OFXImageNode::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashFormat( output, context, h );
	if( output == outPlug() )
	{
		ofxRenderBufferPlug()->hash( h );
	}
}

GafferImage::Format OFXImageNode::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ImagePlug::GlobalScope globalScope( context );
	IECore::ConstCompoundObjectPtr renderBuffer = ofxRenderBufferPlug()->getValue();
	if( !renderBuffer )
	{
		return inPlug()->formatPlug()->getValue();
	}
	Box2iDataPtr dataWindowData = runTimeCast<Box2iData>(
		const_cast<Data*>( renderBuffer->member<Data>( "dataWindow" ) )
	);
	FloatDataPtr parData = runTimeCast<FloatData>(
		const_cast<Data*>( renderBuffer->member<Data>( "pixelAspect" ) )
	);
	if( dataWindowData && parData )
	{
		const Box2i &dw = dataWindowData->readable();
		return Format( dw.size().x, dw.size().y, parData->readable() );
	}
	return inPlug()->formatPlug()->getValue();
}

void OFXImageNode::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashDataWindow( output, context, h );
	if( output == outPlug() )
	{
		ofxRenderBufferPlug()->hash( h );
	}
}

Imath::Box2i OFXImageNode::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ImagePlug::GlobalScope globalScope( context );
	IECore::ConstCompoundObjectPtr renderBuffer = ofxRenderBufferPlug()->getValue();
	if( !renderBuffer )
	{
		return inPlug()->dataWindowPlug()->getValue();
	}
	Box2iDataPtr dataWindowData = runTimeCast<Box2iData>(
		const_cast<Data*>( renderBuffer->member<Data>( "dataWindow" ) )
	);
	if( dataWindowData )
	{
		return dataWindowData->readable();
	}
	return inPlug()->dataWindowPlug()->getValue();
}

IECore::ConstCompoundDataPtr OFXImageNode::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return outPlug()->metadataPlug()->defaultValue();
}

bool OFXImageNode::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return false;
}

void OFXImageNode::hashSampleOffsets( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = ImagePlug::emptyTileSampleOffsets()->Object::hash();
}

IECore::ConstIntVectorDataPtr OFXImageNode::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::flatTileSampleOffsets();
}

void OFXImageNode::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( output, context, h );
	if( output == outPlug() )
	{
		ofxRenderBufferPlug()->hash( h );
	}
}

IECore::ConstStringVectorDataPtr OFXImageNode::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ImagePlug::GlobalScope globalScope( context );

	if( m_tiledRenderSupported )
	{
		// Tiled path: output is always RGBA.
		vector<string> names = { "R", "G", "B", "A" };
		return new StringVectorData( names );
	}

	IECore::ConstCompoundObjectPtr renderBuffer = ofxRenderBufferPlug()->getValue();
	if( !renderBuffer )
	{
		return inPlug()->channelNamesPlug()->getValue();
	}
	vector<string> names;
	if( renderBuffer->member<Data>( "R" ) )
	{
		names.push_back( "R" );
	}
	if( renderBuffer->member<Data>( "G" ) )
	{
		names.push_back( "G" );
	}
	if( renderBuffer->member<Data>( "B" ) )
	{
		names.push_back( "B" );
	}
	if( renderBuffer->member<Data>( "A" ) )
	{
		names.push_back( "A" );
	}
	if( names.empty() )
	{
		return inPlug()->channelNamesPlug()->getValue();
	}
	return new StringVectorData( names );
}

void OFXImageNode::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( output, context, h );
	if( output == outPlug() )
	{
		if( !m_instance )
		{
			const std::string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
			const Imath::V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
			h.append( inPlug()->channelDataHash( channelName, tileOrigin ) );
		}
		else if( m_tiledRenderSupported )
		{
			// Strip channelName before hashing tileBufferPlug so the
			// tile buffer hash (and all its upstream deps) is computed
			// identically for all four channels at this tile origin.
			// The channelName is appended afterwards for cache-key
			// uniqueness per channel.
			Context::EditableScope tileScope( context );
			tileScope.remove( ImagePlug::channelNameContextName );
			tileBufferPlug()->hash( h );
			h.append( context->get<std::string>( ImagePlug::channelNameContextName ) );
		}
		else
		{
			ofxRenderBufferPlug()->hash( h );
			h.append( context->get<V2i>( ImagePlug::tileOriginContextName ) );
			h.append( context->get<std::string>( ImagePlug::channelNameContextName ) );
		}
	}
}

IECore::ConstFloatVectorDataPtr OFXImageNode::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// Read the full cached render buffer in global scope
	ImagePlug::GlobalScope globalScope( context );

	if( !m_instance )
	{
		return inPlug()->channelData( channelName, tileOrigin );
	}

	if( m_tiledRenderSupported && inPlug()->getInput() )
	{
		// Tiled path: pull __ofxTileBuffer (keyed by tileOrigin, NOT
		// channelName) so all four channels compute once per tile.
		// Use EditableScope to remove channelName from context before
		// pulling, otherwise we'd get distinct cache entries per channel.
		Context::EditableScope tileScope( context );
		tileScope.remove( ImagePlug::channelNameContextName );

		IECore::ConstCompoundObjectPtr tileBuf = IECore::runTimeCast<const IECore::CompoundObject>( tileBufferPlug()->getValue() );

		if( !tileBuf )
		{
			return ImagePlug::emptyTile();
		}

		auto *chData = tileBuf->member<FloatVectorData>( channelName );
		if( !chData )
		{
			return ImagePlug::emptyTile();
		}

		// Return shared data — tile buffer is const once computed,
		// and the convention matches ImagePlug::emptyTile().
		return IECore::ConstFloatVectorDataPtr( chData );
	}

	// ---- Full-frame path (non-tiled plugins) ----
	IECore::ConstCompoundObjectPtr renderBuffer = ofxRenderBufferPlug()->getValue();

	if( !renderBuffer )
	{
		return ImagePlug::emptyTile();
	}

	const std::string channelKey = ( channelName == "R" || channelName == "G" || channelName == "B" || channelName == "A" )
		? channelName : "";

	if( channelKey.empty() )
	{
		return ImagePlug::emptyTile();
	}

	FloatVectorDataPtr channelData = runTimeCast<FloatVectorData>(
		const_cast<Data*>( renderBuffer->member<Data>( channelKey ) )
	);

	Box2iDataPtr dataWindowData = runTimeCast<Box2iData>(
		const_cast<Data*>( renderBuffer->member<Data>( "dataWindow" ) )
	);

	if( !channelData || !dataWindowData )
	{
		return ImagePlug::emptyTile();
	}

	const Box2i &dataWindow = dataWindowData->readable();
	int width = dataWindow.size().x;
	const vector<float> &values = channelData->readable();

	// Extract the 64x64 tile region
	FloatVectorDataPtr tileData = new FloatVectorData();
	vector<float> &tile = tileData->writable();
	tile.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );

	Box2i tileBound(
		V2i( tileOrigin.x, tileOrigin.y ),
		V2i( tileOrigin.x + ImagePlug::tileSize(), tileOrigin.y + ImagePlug::tileSize() )
	);

	for( int y = tileOrigin.y; y < tileOrigin.y + ImagePlug::tileSize(); ++y )
	{
		for( int x = tileOrigin.x; x < tileOrigin.x + ImagePlug::tileSize(); ++x )
		{
			if( dataWindow.intersects( V2i( x, y ) ) )
			{
				int srcIdx = ( y - dataWindow.min.y ) * width + ( x - dataWindow.min.x );
				if( srcIdx < (int)values.size() )
				{
					tile.push_back( values[srcIdx] );
				}
				else
				{
					tile.push_back( 0.0f );
				}
			}
			else
			{
				tile.push_back( 0.0f );
			}
		}
	}

	return tileData;
}


void OFXImageNode::hashTileBuffer( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImagePlug::GlobalScope globalScope( context );

	if( !m_instance )
	{
		pluginIdPlug()->hash( h );
		inPlug()->formatPlug()->hash( h );
		return;
	}

	const Imath::V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const OfxTime frame = context->getFrame();
	const OfxPointD renderScale = { 1.0, 1.0 };

	// Hash identity: tile origin, frame, plugin ID, params.
	h.append( tileOrigin );
	h.append( frame );
	pluginIdPlug()->hash( h );
	GLRenderModePlug()->hash( h );
	for( const auto &child : parametersPlug()->children() )
	{
		if( auto *valuePlug = runTimeCast<const ValuePlug>( child.get() ) )
		{
			valuePlug->hash( h );
		}
	}

	// Data window affects the render box — a window shift inside a tile
	// produces a different pixel boundary even if input pixels are the same.
	inPlug()->dataWindowPlug()->hash( h );

	// Build render box for this tile to determine which input tiles to hash.
	int ts = ImagePlug::tileSize();
	Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
	Box2i tileBound( tileOrigin, tileOrigin + V2i( ts, ts ) );
	Box2i renderBox(
		V2i( std::max( tileBound.min.x, dataWindow.min.x ), std::max( tileBound.min.y, dataWindow.min.y ) ),
		V2i( std::min( tileBound.max.x, dataWindow.max.x ), std::min( tileBound.max.y, dataWindow.max.y ) )
	);
	if( renderBox.size().x <= 0 || renderBox.size().y <= 0 )
	{
		return;
	}

	OfxRectD renderWindowD = { (double)renderBox.min.x, (double)renderBox.min.y,
	                           (double)renderBox.max.x, (double)renderBox.max.y };

	// Get region of interest for this tile to narrow input hashing.
	std::map<OFX::Host::ImageEffect::ClipInstance *, OfxRectD> rois;
	m_instance->getRegionOfInterestAction( frame, renderScale, renderWindowD, rois );

	// Hash input channel data for tiles intersecting each clip's RoI.
	// The inPlug (Source) is always the primary input.
	auto hashInputRegion = [&]( const GafferImage::ImagePlug *plug, const OfxRectD &roiD )
	{
		if( !plug || !plug->getInput() )
		{
			return;
		}
		Box2i roiI(
			V2i( (int)std::floor( roiD.x1 ), (int)std::floor( roiD.y1 ) ),
			V2i( (int)std::ceil(  roiD.x2 ), (int)std::ceil(  roiD.y2 ) )
		);
		// Clamp to the plug's data window — include it in the hash
		// so a window shift inside the RoI invalidates the cache.
		Box2i clipDw = plug->dataWindowPlug()->getValue();
		plug->dataWindowPlug()->hash( h );
		roiI = Box2i(
			V2i( std::max( roiI.min.x, clipDw.min.x ), std::max( roiI.min.y, clipDw.min.y ) ),
			V2i( std::min( roiI.max.x, clipDw.max.x ), std::min( roiI.max.y, clipDw.max.y ) )
		);
		if( roiI.size().x <= 0 || roiI.size().y <= 0 )
		{
			return;
		}

		IECore::ConstStringVectorDataPtr channelNamesData = plug->channelNamesPlug()->getValue();
		const auto &channels = channelNamesData->readable();
		for( int yy = roiI.min.y; yy < roiI.max.y; yy += ImagePlug::tileSize() )
		{
			for( int xx = roiI.min.x; xx < roiI.max.x; xx += ImagePlug::tileSize() )
			{
				V2i srcTileOrigin( xx, yy );
				for( const auto &ch : channels )
				{
					h.append( plug->channelDataHash( ch, srcTileOrigin ) );
				}
			}
		}
	};

	// Source clip
	auto it = rois.find( m_instance->getClip( "Source" ) );
	if( it != rois.end() )
	{
		hashInputRegion( inPlug(), it->second );
	}

	// Extra clip plugs
	for( const auto &plugName : m_clipPlugNames )
	{
		if( auto *imgPlug = getChild<GafferImage::ImagePlug>( plugName ) )
		{
			std::string ofxClipName = plugName;
			if( !ofxClipName.empty() && islower( ofxClipName[0] ) )
			{
				ofxClipName[0] = toupper( ofxClipName[0] );
			}
			auto ci = rois.find( m_instance->getClip( ofxClipName ) );
			if( ci != rois.end() )
			{
				hashInputRegion( imgPlug, ci->second );
			}
		}
	}
}

void OFXImageNode::hashOfxRenderBuffer( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImagePlug::GlobalScope globalScope( context );

	if( !m_instance )
	{
		// No valid OFX instance — pass through input data.
		// Hash input plugs to invalidate cache when input changes.
		pluginIdPlug()->hash( h );
		inPlug()->formatPlug()->hash( h );
		inPlug()->dataWindowPlug()->hash( h );
		inPlug()->channelNamesPlug()->hash( h );
		return;
	}

	// Hash input metadata
	inPlug()->formatPlug()->hash( h );
	inPlug()->dataWindowPlug()->hash( h );
	inPlug()->channelNamesPlug()->hash( h );

	// Renderer preference changes the render path (GL device / CPU).
	GLRenderModePlug()->hash( h );

	if( !m_tiledRenderSupported )
	{
		// Hash all input channel data tiles, since the OFX render
		// processes all channels over the entire data window
		Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
		if( dataWindow.size().x > 0 && dataWindow.size().y > 0 )
		{
			IECore::ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
			const auto &channelNames = channelNamesData->readable();
			for( int y = dataWindow.min.y; y < dataWindow.max.y; y += ImagePlug::tileSize() )
			{
				for( int x = dataWindow.min.x; x < dataWindow.max.x; x += ImagePlug::tileSize() )
				{
					V2i tileOrigin( x, y );
					for( const auto &channel : channelNames )
					{
						h.append( inPlug()->channelDataHash( channel, tileOrigin ) );
					}
				}
			}
		}

		// Hash additional connected clip plugs
		for( const auto &name : m_clipPlugNames )
		{
			if( auto *imgPlug = getChild<GafferImage::ImagePlug>( name ) )
			{
				if( !imgPlug->getInput() )
				{
					continue;
				}
				imgPlug->formatPlug()->hash( h );
				imgPlug->dataWindowPlug()->hash( h );
				imgPlug->channelNamesPlug()->hash( h );
				Box2i clipDw = imgPlug->dataWindowPlug()->getValue();
				if( clipDw.size().x > 0 && clipDw.size().y > 0 )
				{
					IECore::ConstStringVectorDataPtr clipChannels = imgPlug->channelNamesPlug()->getValue();
					for( int yy = clipDw.min.y; yy < clipDw.max.y; yy += ImagePlug::tileSize() )
					{
						for( int xx = clipDw.min.x; xx < clipDw.max.x; xx += ImagePlug::tileSize() )
						{
							V2i tileOrigin( xx, yy );
							for( const auto &ch : clipChannels->readable() )
							{
								h.append( imgPlug->channelDataHash( ch, tileOrigin ) );
							}
						}
					}
				}
			}
		}
	}
	else
	{
		// Tiled path: hash clip metadata only (format/dataWindow/channelNames),
		// not tile-level channel data.  Per-tile pixel hashing is done in
		// hashChannelData.
		for( const auto &name : m_clipPlugNames )
		{
			if( auto *imgPlug = getChild<GafferImage::ImagePlug>( name ) )
			{
				if( !imgPlug->getInput() )
				{
					continue;
				}
				imgPlug->formatPlug()->hash( h );
				imgPlug->dataWindowPlug()->hash( h );
				imgPlug->channelNamesPlug()->hash( h );
			}
		}
	}

	// Hash parameters and plugin ID
	pluginIdPlug()->hash( h );
	for( const auto &child : parametersPlug()->children() )
	{
		if( auto *valuePlug = runTimeCast<const ValuePlug>( child.get() ) )
		{
			valuePlug->hash( h );
		}
	}

	// Include the frame in the hash so that time-varying OFX plugins
	// (whether they declare _frameVarying or not) correctly invalidate
	// the cache across frames.  getClipPreferences is called once during
	// createPluginInstance (not here — hashing must be side-effect-free).
	if( m_instance )
	{
		h.append( context->getFrame() );
	}
}

Gaffer::ValuePlug::CachePolicy OFXImageNode::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == tileBufferPlug() || output == ofxRenderBufferPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ImageProcessor::computeCachePolicy( output );
}

IECore::ConstCompoundObjectPtr OFXImageNode::computeTileBuffer( const Gaffer::Context *context ) const
{
	// Copy the context BEFORE GlobalScope strips tile-level entries.
	// The render invocation needs tileOrigin in its context so that
	// fetchInputImage pulls the correct upstream tiles.
	Gaffer::ConstContextPtr ctxCopy = new Gaffer::Context( *context );

	const Imath::V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

	// Enter GlobalScope so metadata pulls (dataWindow) are NOT
	// fragmented by tileOrigin.
	ImagePlug::GlobalScope globalScope( context );

	OfxTime frame = context->getFrame();
	OfxPointD renderScale = { 1.0, 1.0 };

	int ts = ImagePlug::tileSize();
	Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
	Box2i tileBound( tileOrigin, tileOrigin + V2i( ts, ts ) );
	Box2i renderBox(
		V2i( std::max( tileBound.min.x, dataWindow.min.x ), std::max( tileBound.min.y, dataWindow.min.y ) ),
		V2i( std::min( tileBound.max.x, dataWindow.max.x ), std::min( tileBound.max.y, dataWindow.max.y ) )
	);
	if( renderBox.size().x <= 0 || renderBox.size().y <= 0 )
	{
		// setValue(nullptr) is illegal; the dispatch site substitutes
		// NullObject, but returning null here is cleaner for early exit.
		return nullptr;
	}

	// Build result container with empty tile-sized buffers.
	CompoundObjectPtr result = new CompoundObject();
	int numPixels = ts * ts;
	FloatVectorDataPtr rData = new FloatVectorData();
	FloatVectorDataPtr gData = new FloatVectorData();
	FloatVectorDataPtr bData = new FloatVectorData();
	FloatVectorDataPtr aData = new FloatVectorData();
	rData->writable().resize( numPixels, 0.0f );
	gData->writable().resize( numPixels, 0.0f );
	bData->writable().resize( numPixels, 0.0f );
	aData->writable().resize( numPixels, 0.0f );
	result->members()["R"] = rData;
	result->members()["G"] = gData;
	result->members()["B"] = bData;
	result->members()["A"] = aData;
	result->members()["renderBox"] = new Box2iData( renderBox );

	OfxRectD renderWindowD = { (double)renderBox.min.x, (double)renderBox.min.y,
	                           (double)renderBox.max.x, (double)renderBox.max.y };
	OfxRectI renderWindowI = { renderBox.min.x, renderBox.min.y,
	                           renderBox.max.x, renderBox.max.y };

	// Check if the effect is identity (e.g. FrameHold pass-through at a
	// different frame).  Identity effects never render — the host must
	// copy the identity clip at identityTime into the output instead.
	{
		OfxTime identityTime = frame;
		std::string identityClip;
		if( m_instance->isIdentityAction( identityTime, kOfxImageFieldNone, renderWindowI, renderScale, identityClip ) == kOfxStatOK )
		{
			if( identityClip == "Source" && inPlug()->getInput() )
			{
				// Pull the source at identityTime (whole-tile pulls so the
				// input's own cache handles reuse) and copy the renderBox
				// region into the tile.  Only pull channels the input
				// actually has — readers (e.g. OIIO) raise for missing
				// channels — and inject alpha=1.0 for RGB-only inputs,
				// matching readPlugToRGBA's convention in the render path.
				Gaffer::Context::EditableScope idEdit( context );
				idEdit.setFrame( identityTime );

				IECore::ConstStringVectorDataPtr chNamesData = inPlug()->channelNamesPlug()->getValue();
				const auto &chNames = chNamesData->readable();
				const bool hasA = std::find( chNames.begin(), chNames.end(), "A" ) != chNames.end();

				std::map<std::string, IECore::ConstFloatVectorDataPtr> tiles;
				for( const char *ch : { "R", "G", "B", "A" } )
				{
					if( ch[0] == 'A' && !hasA )
					{
						continue;
					}
					IECore::ConstFloatVectorDataPtr td = inPlug()->channelData( ch, tileOrigin );
					if( !td )
					{
						throw IECore::Exception( "OFX identity: failed to pull input channel " + std::string( ch ) );
					}
					tiles[ch] = td;
				}
				{
					vector<float> &rVec = rData->writable();
					vector<float> &gVec = gData->writable();
					vector<float> &bVec = bData->writable();
					vector<float> &aVec = aData->writable();
					const vector<float> &rSrc = tiles["R"]->readable();
					const vector<float> &gSrc = tiles["G"]->readable();
					const vector<float> &bSrc = tiles["B"]->readable();
					const vector<float> *aSrc = hasA ? &tiles["A"]->readable() : nullptr;
					for( int y = renderBox.min.y; y < renderBox.max.y; ++y )
					{
						int tileRow = ( y - tileOrigin.y ) * ts;
						for( int x = renderBox.min.x; x < renderBox.max.x; ++x )
						{
							int tileIdx = tileRow + ( x - tileOrigin.x );
							rVec[tileIdx] = rSrc[tileIdx];
							gVec[tileIdx] = gSrc[tileIdx];
							bVec[tileIdx] = bSrc[tileIdx];
							aVec[tileIdx] = aSrc ? (*aSrc)[tileIdx] : 1.0f;
						}
					}
					return result;
				}
			}
		}
	}

	// RoI/isIdentity actions stay outside the lock (assumption: pure
	// param math for openfx-misc plugins).
	std::map<OFX::Host::ImageEffect::ClipInstance *, OfxRectD> rois;
	m_instance->getRegionOfInterestAction( frame, renderScale, renderWindowD, rois );

	std::map<std::string, OfxRectD> clipRoIs;
	for( auto &[clipPtr, roi] : rois )
	{
		if( clipPtr )
		{
			clipRoIs[clipPtr->getName()] = roi;
		}
	}

	// All metadata pulls and the RoI action are done.  Now acquire
	// the render lock for the dangerous section (beginRender/render/
	// endRender + output extraction).  FullySafe: no lock.
	// InstanceSafe: per-instance mutex.  Unsafe: global mutex.
	std::unique_lock<std::mutex> renderLock( m_renderMutex, std::defer_lock );
	std::unique_lock<std::mutex> globalLock( m_globalRenderMutex, std::defer_lock );
	if( m_renderThreadSafety == RenderSafety::InstanceSafe )
	{
		renderLock.lock();
	}
	else if( m_renderThreadSafety == RenderSafety::Unsafe )
	{
		globalLock.lock();
	}

	RenderingCounter _rc( m_rendering );

	RenderInvocation inv;
	inv.time = frame;
	inv.renderWindow = renderWindowI;
	inv.renderScale.x = renderScale.x;
	inv.renderScale.y = renderScale.y;
	inv.projectWidth = dataWindow.size().x;
	inv.projectHeight = dataWindow.size().y;
	inv.context = ctxCopy;
	inv.clipRoIs = clipRoIs;

	// Instrumentation: optional spin to make render cost dominate
	{
		int ms = tileSpinMs();
		if( ms > 0 )
		{
			std::this_thread::sleep_for( std::chrono::milliseconds( ms ) );
		}
	}

	OfxStatus renderStatus = kOfxStatOK;
	{
		// Tile concurrency measurement: thread-local depth so
		// nested invocations don't inflate the thread count.
		bool topLevel = ( t_tileDepth++ == 0 );
		if( topLevel )
		{
			int a = ++g_activeThreads;
			for( int hw = g_threadHighWater.load(); a > hw && !g_threadHighWater.compare_exchange_weak( hw, a ); ) {}
		}
		std::cerr << "[tile] " << std::this_thread::get_id()
		          << " " << ( topLevel ? "enter" : "nest" ) << " " << tileOrigin
		          << " threads=" << g_activeThreads.load()
		          << std::endl;

		RenderInvocationGuard guard( inv );
		m_instance->beginRenderAction( frame, frame, 1.0, false, renderScale, true, true );
		renderStatus = m_instance->renderAction( frame, kOfxImageFieldNone, renderWindowI, renderScale, true, true, false );
		m_instance->endRenderAction( frame, frame, 1.0, false, renderScale, true, true );

		std::cerr << "[tile] " << std::this_thread::get_id()
		          << " exit highWater=" << g_threadHighWater.load()
		          << std::endl;
		if( topLevel )
		{
			--g_activeThreads;
		}
		--t_tileDepth;
	}

	// Propagation order: exception first, then status.
	if( inv.exception )
	{
		std::rethrow_exception( inv.exception );
	}
	if( renderStatus != kOfxStatOK && renderStatus != kOfxStatReplyDefault )
	{
		throw IECore::Exception( "OFX renderAction failed" );
	}

	// De-interleave output into result
	auto *outputImg = inv.outputImage;
	if( outputImg )
	{
		OfxRectI ob = outputImg->getBounds();
		if( ob.x2 > ob.x1 && ob.y2 > ob.y1 )
		{
			vector<float> &rVec = rData->writable();
			vector<float> &gVec = gData->writable();
			vector<float> &bVec = bData->writable();
			vector<float> &aVec = aData->writable();

			for( int y = renderBox.min.y; y < renderBox.max.y; ++y )
			{
				int tileRow = ( y - tileOrigin.y ) * ts;
				for( int x = renderBox.min.x; x < renderBox.max.x; ++x )
				{
					if( auto *pixel = static_cast<GafferOFX::Image*>( outputImg )->pixel( x, y ) )
					{
						int tileIdx = tileRow + ( x - tileOrigin.x );
						if( tileIdx >= 0 && tileIdx < numPixels )
						{
							rVec[tileIdx] = pixel->r;
							gVec[tileIdx] = pixel->g;
							bVec[tileIdx] = pixel->b;
							aVec[tileIdx] = pixel->a;
						}
					}
				}
			}
		}
	}

	return result;
}

IECore::ConstCompoundObjectPtr OFXImageNode::computeOfxRenderBuffer( const Gaffer::Context *context ) const
{
	std::lock_guard<std::mutex> lock( m_renderMutex );
	CompoundObjectPtr result = new CompoundObject();

	if( !m_instance )
	{
		return result;
	}

	ImagePlug::GlobalScope globalScope( context );

	GafferOFX::ClipInstance* sourceClip = dynamic_cast<GafferOFX::ClipInstance*>( m_instance->getClip( "Source" ) );
	GafferOFX::ClipInstance* outputClip = dynamic_cast<GafferOFX::ClipInstance*>( m_instance->getClip( "Output" ) );

	OfxTime frame = context->getFrame();
	OfxPointD renderScale = { 1.0, 1.0 };

	Box2i dataWindow;
	Format format;
	const bool hasInput = inPlug()->getInput() != nullptr;

	if( hasInput && sourceClip )
	{
		format = inPlug()->formatPlug()->getValue();
		dataWindow = inPlug()->dataWindowPlug()->getValue();
		if( dataWindow.size().x <= 0 || dataWindow.size().y <= 0 )
		{
			dataWindow = Box2i( V2i( 0, 0 ), V2i( (int)format.width(), (int)format.height() ) );
		}
	}
	else
	{
		OfxRectD rod;
		if( outputClip )
		{
			m_instance->getRegionOfDefinitionAction( frame, renderScale, rod );
		}
		else
		{
			rod.x1 = rod.y1 = 0;
			rod.x2 = rod.y2 = 720;
		}
		dataWindow = Box2i(
			V2i( (int)rod.x1, (int)rod.y1 ),
			V2i( (int)rod.x2, (int)rod.y2 )
		);
		if( dataWindow.size().x <= 0 || dataWindow.size().y <= 0 )
		{
			dataWindow = Box2i( V2i( 0, 0 ), V2i( 1920, 1080 ) );
		}
		format = Format( dataWindow.size().x, dataWindow.size().y );
	}

	// Tiled path: just compute metadata (dataWindow + pixelAspect), no full-frame render.
	if( m_tiledRenderSupported && hasInput )
	{
		Format fmt = hasInput ? inPlug()->formatPlug()->getValue()
		          : Format( dataWindow.size().x, dataWindow.size().y );
		result->members()["dataWindow"] = new Box2iData( dataWindow );
		result->members()["pixelAspect"] = new FloatData( fmt.getPixelAspect() );
		return result;
	}

	OfxRectI renderWindow = {
		dataWindow.min.x, dataWindow.min.y,
		dataWindow.max.x, dataWindow.max.y
	};

	// Check if the effect is identity (e.g. FrameHold pass-through at a different frame)
	{
		OfxTime identityTime = frame;
		std::string identityClip;
		if( m_instance->isIdentityAction( identityTime, kOfxImageFieldNone, renderWindow, renderScale, identityClip ) == kOfxStatOK )
		{
			if( identityClip == "Source" && hasInput && sourceClip )
			{
				// Read source at identityTime and return as output via pull
				Gaffer::Context::EditableScope idEdit( context );
				idEdit.setFrame( identityTime );

				Format idFormat = inPlug()->formatPlug()->getValue();
				Box2i idDw = inPlug()->dataWindowPlug()->getValue();
				int idW = idDw.size().x;
				int idH = idDw.size().y;
				if( idW > 0 && idH > 0 )
				{
					FloatVectorDataPtr rData = new FloatVectorData();
					FloatVectorDataPtr gData = new FloatVectorData();
					FloatVectorDataPtr bData = new FloatVectorData();
					FloatVectorDataPtr aData = new FloatVectorData();
					rData->writable().resize( idW * idH );
					gData->writable().resize( idW * idH );
					bData->writable().resize( idW * idH );
					aData->writable().resize( idW * idH );

					GafferImage::Sampler rSamp( inPlug(), "R", idDw );
					GafferImage::Sampler gSamp( inPlug(), "G", idDw );
					GafferImage::Sampler bSamp( inPlug(), "B", idDw );
					IECore::ConstStringVectorDataPtr chNames = inPlug()->channelNamesPlug()->getValue();
					bool hasA = false;
					for( const auto &c : chNames->readable() ) { if( c == "A" ) { hasA = true; break; } }
					std::unique_ptr<GafferImage::Sampler> aSamp;
					if( hasA )
					{
						aSamp = std::make_unique<GafferImage::Sampler>( inPlug(), "A", idDw );
					}

					vector<float> &rVec = rData->writable();
					vector<float> &gVec = gData->writable();
					vector<float> &bVec = bData->writable();
					vector<float> &aVec = aData->writable();

					for( int y = idDw.min.y; y < idDw.max.y; ++y )
					{
						int row = ( y - idDw.min.y ) * idW;
						for( int x = idDw.min.x; x < idDw.max.x; ++x )
						{
							int idx = row + ( x - idDw.min.x );
							rVec[idx] = rSamp.sample( x, y );
							gVec[idx] = gSamp.sample( x, y );
							bVec[idx] = bSamp.sample( x, y );
							aVec[idx] = aSamp ? aSamp->sample( x, y ) : 1.0f;
						}
					}

					result->members()["R"] = rData;
					result->members()["G"] = gData;
					result->members()["B"] = bData;
					result->members()["A"] = aData;
					result->members()["dataWindow"] = new Box2iData( idDw );
					result->members()["pixelAspect"] = new FloatData( idFormat.getPixelAspect() );
				}
				return result;
			}
		}
	}

	// Get RoI for each clip and build clipRoIs map
	std::map<OFX::Host::ImageEffect::ClipInstance *, OfxRectD> rois;
	OfxRectD regionOfInterest = {
		(double)dataWindow.min.x, (double)dataWindow.min.y,
		(double)dataWindow.max.x, (double)dataWindow.max.y
	};
	m_instance->getRegionOfInterestAction( frame, renderScale, regionOfInterest, rois );

	std::map<std::string, OfxRectD> clipRoIs;
	for( auto &[clipPtr, roi] : rois )
	{
		if( clipPtr )
		{
			clipRoIs[clipPtr->getName()] = roi;
		}
	}

	// Check if the plugin supports GL rendering.  GL-capable plugins
	// are dispatched to the dedicated OFXRenderWorker for context affinity;
	// CPU-only plugins render inline with zero GL interaction.
	bool pluginSupportsGL = false;
	bool glIsNeeded = false;
	try
	{
		std::string val = m_instance->getPlugin()->getDescriptor().getProps().getStringProperty(
			kOfxImageEffectPropOpenGLRenderSupported
		);
		pluginSupportsGL = ( val == "true" || val == "needed" );
		glIsNeeded = ( val == "needed" );
	}
	catch( const std::exception & ) {}

	int w = renderWindow.x2 - renderWindow.x1;
	int h = renderWindow.y2 - renderWindow.y1;

	RenderingCounter _rc( m_rendering );

	Gaffer::ConstContextPtr ctxCopy = new Gaffer::Context( *Gaffer::Context::current() );

	RenderInvocation inv;
	inv.time = frame;
	inv.projectWidth = dataWindow.size().x;
	inv.projectHeight = dataWindow.size().y;
	inv.renderWindow = renderWindow;
	inv.renderScale.x = renderScale.x;
	inv.renderScale.y = renderScale.y;
	inv.context = ctxCopy;
	inv.clipRoIs = clipRoIs;

	// Shared render function used by both CPU (inline) and GL (worker) paths.
	OfxStatus renderStatus = kOfxStatOK;
	auto renderFunc = [&]()
	{
		RenderInvocationGuard guard( inv );
		m_instance->beginRenderAction( frame, frame, 1.0, false, renderScale, true, true );
		renderStatus = m_instance->renderAction( frame, kOfxImageFieldNone, renderWindow, renderScale, true, true, false );
		m_instance->endRenderAction( frame, frame, 1.0, false, renderScale, true, true );
	};

	// Apply the node's renderer preference to the shared GL context.
	// CPU/GPU rebuild the context onto the requested device class (last
	// node to render wins).  CPU requests the software EGL device.  GL-
	// capable plugins always render through GL — their non-GL render path
	// is a plain failure — so the CPU path below is reserved for plugins
	// with no GL support.
	GLContextManager::RenderMode renderMode = GLContextManager::RenderMode::Auto;
	switch( GLRenderModePlug()->getValue() )
	{
		case 1 : renderMode = GLContextManager::RenderMode::CPU; break;
		case 2 : renderMode = GLContextManager::RenderMode::GPU; break;
		default : break;
	}

	GLContextManager::instance().setRenderMode( (int)renderMode );

	if( pluginSupportsGL )
	{
		// GL path: dispatch to dedicated worker for context affinity.
		// Prefetch input images on the compute thread first — the worker
		// must never pull Gaffer directly, as that could deadlock when
		// another thread holds m_renderMutex for a different node.
		// Use clip->getImage() with the full RoI so the resolveFetchRegion
		// floor/ceil + RoD math is consistent between prefetch and render.
		{
			RenderInvocationGuard guard( inv );
			for( const auto &[clipName, roI] : clipRoIs )
			{
				if( clipName == "Output" )
				{
					continue;
				}
				GafferOFX::ClipInstance *clip = dynamic_cast<GafferOFX::ClipInstance*>(
					m_instance->getClip( clipName )
				);
				if( !clip || clipName == "Output" )
				{
					continue;
				}
				const GafferImage::ImagePlug *plug = nullptr;
				if( clipName == "Source" )
				{
					plug = inPlug();
				}
				else if( !clip->plugName().empty() )
				{
					plug = m_instance->node()->getChild<GafferImage::ImagePlug>( clip->plugName() );
				}
				if( !plug || !plug->getInput() )
				{
					continue;
				}
				OfxRectD roiD = roI;
				if( auto *img = static_cast<GafferOFX::Image*>( clip->getImage( frame, &roiD ) ) )
				{
					inv.prefetched[clipName] = img;
				}
			}
			if( inv.exception )
			{
				std::rethrow_exception( inv.exception );
			}
		}

		// The worker owns the EGL context; makeCurrent on any other
		// thread would steal it permanently.
		OFXRenderWorker::instance().execute( [&]()
		{
			GLContextManager &gl = GLContextManager::instance();
			bool useGL = gl.makeCurrent();

			// Require-GL plugins get a hard failure if no context.
			if( glIsNeeded && !useGL )
			{
				throw IECore::Exception(
					"OFX plugin requires OpenGL but no GL context is available"
				);
			}

			if( useGL )
			{
				// A context rebuild (device change via GLRenderMode) invalidates
				// every GL object the plugin cached on the old context.  The
				// render-worker makes the new context current before we get
				// here, so dispatch the full detach/attach cycle to let the
				// plugin tear down dead state and re-initialise on the new
				// device.
				if( m_glContextAttached && m_glContextGeneration != gl.contextGeneration() )
				{
					m_instance->contextDetachedAction();
					m_glContextAttached = false;
				}

				if( !m_glContextAttached )
				{
					m_glContextAttached = true;
					m_glContextGeneration = gl.contextGeneration();
					m_instance->getProps().setIntProperty( kOfxImageEffectPropOpenGLEnabled, 1 );
					m_instance->contextAttachedAction();
				}
			}

			if( useGL )
			{
				unsigned int fbo = 0, tex = 0;
				if( w != (int)gl.outputTexWidth() || h != (int)gl.outputTexHeight() )
				{
					glGenTextures( 1, &tex );
					glBindTexture( GL_TEXTURE_2D, tex );
					glTexImage2D( GL_TEXTURE_2D, 0, GL_RGBA32F, w, h, 0, GL_RGBA, GL_FLOAT, nullptr );
					glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST );
					glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST );
					glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE );
					glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE );

					GLContextManager::glGenFramebuffersF( 1, &fbo );
					GLContextManager::glBindFramebufferF( GL_FRAMEBUFFER, fbo );
					GLContextManager::glFramebufferTexture2DF( GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0 );

					gl.setOutputFBO( fbo, tex, w, h );
				}
				else
				{
					fbo = gl.outputFBO();
					tex = gl.outputTexture();
					GLContextManager::glBindFramebufferF( GL_FRAMEBUFFER, fbo );
				}

				GLContextManager::glCheckFramebufferStatusF( GL_FRAMEBUFFER );

				glViewport( 0, 0, w, h );
				glClearColor( 0.25f, 0.5f, 0.75f, 1.0f );
				glClear( GL_COLOR_BUFFER_BIT );
			}

			// Run render action (on the worker thread — GL context is valid here)
			renderFunc();

			// ---- GL readback (if plugin rendered into our FBO) ----
			if( useGL && pluginSupportsGL )
			{
				GLContextManager::glBindFramebufferF( GL_FRAMEBUFFER, gl.outputFBO() );

				// Sentinel: check if the clear color is still intact.
				// If the plugin rendered into our FBO, pixels should differ.
				float probe[4];
				glReadPixels( 0, 0, 1, 1, GL_RGBA, GL_FLOAT, probe );
				auto approxEq = []( float a, float b, float eps ) {
					return ( a - b ) < eps && ( b - a ) < eps;
				};
				if( !approxEq( probe[0], 0.25f, 0.001f ) ||
				    !approxEq( probe[1], 0.50f, 0.001f ) ||
				    !approxEq( probe[2], 0.75f, 0.001f ) )
				{
					// Plugin rendered to our FBO.  Read pixels directly
					// into result members (inv.outputImage may be NULL
					// if the plugin used loadTexture instead of getImage).
					// NOTE: do NOT also read from inv.outputImage here —
					// the sentinel intact means no GL render, and the CPU
					// de-interleave below handles the CPU-output path.
					glFinish();
					glPixelStorei( GL_PACK_ALIGNMENT, 1 );

					int numPixels = w * h;
					vector<float> pixelBuffer( numPixels * 4 );
					glReadPixels( 0, 0, w, h, GL_RGBA, GL_FLOAT, pixelBuffer.data() );

					FloatVectorDataPtr rData = new FloatVectorData();
					FloatVectorDataPtr gData = new FloatVectorData();
					FloatVectorDataPtr bData = new FloatVectorData();
					FloatVectorDataPtr aData = new FloatVectorData();
					rData->writable().resize( numPixels );
					gData->writable().resize( numPixels );
					bData->writable().resize( numPixels );
					aData->writable().resize( numPixels );

					for( int i = 0; i < numPixels; ++i )
					{
						rData->writable()[i] = pixelBuffer[i * 4];
						gData->writable()[i] = pixelBuffer[i * 4 + 1];
						bData->writable()[i] = pixelBuffer[i * 4 + 2];
						aData->writable()[i] = pixelBuffer[i * 4 + 3];
					}

					result->members()["R"] = rData;
					result->members()["G"] = gData;
					result->members()["B"] = bData;
					result->members()["A"] = aData;
				}
				// Sentinel intact && inv.outputImage means the plugin
				// wrote to getImage(Output) on the CPU — the de-interleave
				// below handles this case.  Do NOT glReadPixels into it.
			}
		} );

	}
	else
	{
		// CPU path: no GL interaction, render inline on the compute thread.
		// Serialized by m_renderMutex; re-entrant via TLS invocation stack.
		// Make sure GL-capable plugins (e.g. Shadertoy) don't see a stale
		// OpenGLEnabled=1 from a previous GL render — they would attempt
		// GL work with no context current on this thread and fail.
		m_instance->getProps().setIntProperty( kOfxImageEffectPropOpenGLEnabled, 0 );
		renderFunc();
	}

	// ---- Propagate cancellation / check render status ----
	// Order is critical: cancellation from a failed Gaffer pull must surface
	// as IECore::Cancelled (silent retry), not as a generic render failure
	// (red node + error dialog on every viewer pan).
	if( inv.exception )
	{
		std::rethrow_exception( inv.exception );
	}

	if( renderStatus != kOfxStatOK && renderStatus != kOfxStatReplyDefault )
	{
		throw IECore::Exception( "OFX renderAction failed" );
	}

	// ---- De-interleave output into result (compute thread, worker is done) ----
	// Skip if GL readback already populated result (sentinel-differed path).
	if( !result->member<FloatVectorData>( "R" ) )
	{
		auto *outputImg = inv.outputImage;
		if( outputImg )
		{
			OfxRectI ob = outputImg->getBounds();
			int ow = ob.x2 - ob.x1;
			int oh = ob.y2 - ob.y1;
			if( ow > 0 && oh > 0 )
			{
				FloatVectorDataPtr rData = new FloatVectorData();
				FloatVectorDataPtr gData = new FloatVectorData();
				FloatVectorDataPtr bData = new FloatVectorData();
				FloatVectorDataPtr aData = new FloatVectorData();
				rData->writable().resize( ow * oh );
				gData->writable().resize( ow * oh );
				bData->writable().resize( ow * oh );
				aData->writable().resize( ow * oh );

				vector<float> &rVec = rData->writable();
				vector<float> &gVec = gData->writable();
				vector<float> &bVec = bData->writable();
				vector<float> &aVec = aData->writable();

				for( int y = ob.y1; y < ob.y2; ++y )
				{
					int row = ( y - ob.y1 ) * ow;
					for( int x = ob.x1; x < ob.x2; ++x )
					{
						if( auto *pixel = static_cast<GafferOFX::Image*>( outputImg )->pixel( x, y ) )
						{
							int idx = row + ( x - ob.x1 );
							rVec[idx] = pixel->r;
							gVec[idx] = pixel->g;
							bVec[idx] = pixel->b;
							aVec[idx] = pixel->a;
						}
					}
				}

				result->members()["R"] = rData;
				result->members()["G"] = gData;
				result->members()["B"] = bData;
				result->members()["A"] = aData;
			}
		}
	}

	result->members()["dataWindow"] = new Box2iData( dataWindow );
	result->members()["pixelAspect"] = new FloatData( format.getPixelAspect() );
	return result;
}

const GafferOFX::EffectImageInstance* OFXImageNode::effectInstance() const
{
	return m_instance.get();
}

bool OFXImageNode::hasOverlay() const
{
	if( !m_instance )
	{
		return false;
	}
	// Calling getOverlayDescriptor() triggers kOfxActionDescribe on the
	// overlay interact via the Context descriptor, which reads the
	// overlay interact main entry from the Context descriptor's
	// properties (set during DescribeInContext by the plugin's
	// setOverlayInteractDescriptor() call).
	OFX::Host::Interact::Descriptor &desc = m_instance->getOverlayDescriptor();
	OFX::Host::Interact::State state = desc.getState();
	return state == OFX::Host::Interact::eDescribed
		|| state == OFX::Host::Interact::eCreated;
}

GafferOFXInteractInstance* OFXImageNode::getInteract()
{
	if( !m_interactInstance && m_instance && hasOverlay() )
	{
		// 32-bit float, hasAlpha=true — matches the float RGBA clips used throughout.
		m_interactInstance = std::make_unique<GafferOFXInteractInstance>( *m_instance, 32, true );
		m_interactInstance->createInstance();
	}
	return m_interactInstance.get();
}

void OFXImageNode::destroyInteract()
{
	m_interactInstance.reset();
}
