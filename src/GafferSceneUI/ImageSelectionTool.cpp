//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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

#include "GafferSceneUI/Private/ImageSelectionTool.h"

#include "GafferImageUI/ImageGadget.h"

#include "GafferSceneUI/SceneView.h"
#include "GafferSceneUI/ScriptNodeAlgo.h"

#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"

#include "GafferScene/InteractiveRender.h"
#include "GafferScene/ScenePlug.h"

#include "GafferScene/Private/RendererAlgo.h"

#include "GafferImage/ImageAlgo.h"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/Sampler.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"

#include "boost/bind/bind.hpp"

#include <regex>

using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;
using namespace GafferImage;
using namespace GafferImageUI;

namespace
{

const InternedString g_idChannelName( "id" );
const InternedString g_instanceIDChannelName( "instanceID" );
const InternedString g_cryptoIDChannelName( "crypto_object00.R" );
const InternedString g_noChannelName( "" );

const InternedString idChannelName( const std::vector<std::string> &channelNames, bool instance )
{
	if( instance  )
	{
		if( ImageAlgo::channelExists( channelNames, g_instanceIDChannelName ) )
		{
			return g_instanceIDChannelName;
		}
		else
		{
			return g_noChannelName;
		}
	}

	if( ImageAlgo::channelExists( channelNames, g_idChannelName ) )
	{
		return g_idChannelName;
	}
	else if( ImageAlgo::channelExists( channelNames, g_cryptoIDChannelName ) )
	{
		return g_cryptoIDChannelName;
	}
	else
	{
		return g_noChannelName;
	}
}

const InternedString g_isRenderingMetadataName = "gaffer:isRendering";

static IECore::InternedString g_dragOverlayName( "__imageSelectionToolDragOverlay" );

// Logic copied from ImageGadget, in order to avoid exposing a plane normal in the API
std::tuple< bool, Imath::V2f, Imath::V2f > effectiveWipePlane( const ImageGadget *imageGadget )
{
	if( !imageGadget->getWipeEnabled() )
	{
		return std::make_tuple( false, V2f(), V2f() );
	}

	float radians = imageGadget->getWipeAngle() * M_PI / 180.0f;
	return std::make_tuple( true, imageGadget->getWipePosition(), V2f( cosf( radians ), sinf( radians ) ) );
}

} // namespace

class ImageSelectionTool::DragOverlay : public GafferUI::Gadget
{

	public :

		DragOverlay()
			: Gadget()
		{
		}

		Imath::Box3f bound() const override
		{
			// we draw in raster space so don't have a sensible bound
			return Box3f();
		}

		void setStartPosition( const V3f &p )
		{
			if( m_startPosition == p )
			{
				return;
			}
			m_startPosition = p;
			dirty( DirtyType::Render );
		}

		const V3f &getStartPosition() const
		{
			return m_startPosition;
		}

		void setEndPosition( const V3f &p )
		{
			if( m_endPosition == p )
			{
				return;
			}
			m_endPosition = p;
			dirty( DirtyType::Render );
		}

		const V3f &getEndPosition() const
		{
			return m_endPosition;
		}

	protected :

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override
		{
			assert( layer == Layer::MidFront );

			if( isSelectionRender( reason ) )
			{
				return;
			}

			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			ViewportGadget::RasterScope rasterScope( viewportGadget );

			Box2f b;
			b.extendBy( viewportGadget->gadgetToRasterSpace( m_startPosition, this ) );
			b.extendBy( viewportGadget->gadgetToRasterSpace( m_endPosition, this ) );

			style->renderSelectionBox( b );
		}

		unsigned layerMask() const override
		{
			return (unsigned)Layer::MidFront;
		}

		Imath::Box3f renderBound() const override
		{
			// we draw in raster space so don't have a sensible bound
			Box3f b;
			b.makeInfinite();
			return b;
		}

	private :

		Imath::V3f m_startPosition;
		Imath::V3f m_endPosition;

};

//////////////////////////////////////////////////////////////////////////
// ImageSelectionTool implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( ImageSelectionTool );

size_t ImageSelectionTool::g_firstPlugIndex = 0;
ImageSelectionTool::ToolDescription<ImageSelectionTool, ImageView> ImageSelectionTool::g_imageToolDescription;

ImageSelectionTool::ImageSelectionTool( View *view, const std::string &name )
	:	Tool( view, name ), m_manifestDirty( true )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "selectMode", Plug::In, "standard" ) );
	addChild( new ImagePlug( "__image", Plug::In ) );
	imagePlug()->setInput( view->inPlug<ImagePlug>() );

	view->viewportGadget()->preRenderSignal().connect( boost::bind( &ImageSelectionTool::preRender, this ) );
	plugDirtiedSignal().connect( boost::bind( &ImageSelectionTool::plugDirtied, this, ::_1 ) );

	view->viewportGadget()->keyPressSignal().connect( boost::bind( &ImageSelectionTool::keyPress, this, ::_2 ) );

	ImageGadget *ig = imageGadget();
	ig->buttonPressSignal().connect( boost::bind( &ImageSelectionTool::buttonPress, this, ::_2 ) );
	ig->buttonReleaseSignal().connect( boost::bind( &ImageSelectionTool::buttonRelease, this, ::_2 ) );
	ig->dragBeginSignal().connect( boost::bind( &ImageSelectionTool::dragBegin, this, ::_1, ::_2 ) );
	ig->dragEnterSignal().connect( boost::bind( &ImageSelectionTool::dragEnter, this, ::_1, ::_2 ) );
	ig->dragMoveSignal().connect( boost::bind( &ImageSelectionTool::dragMove, this, ::_2 ) );
	ig->dragEndSignal().connect( boost::bind( &ImageSelectionTool::dragEnd, this, ::_2 ) );
	ig->mouseMoveSignal().connect( boost::bind( &ImageSelectionTool::mouseMove, this, ::_2 ) );
	ig->leaveSignal().connect( boost::bind( &ImageSelectionTool::leave, this, ::_2 ) );

	m_selectedPathsChangedConnection = ScriptNodeAlgo::selectedPathsChangedSignal( view->scriptNode() ).connect( boost::bind( &ImageSelectionTool::selectedPathsChanged, this ) );

	m_manifestError = "";
	m_infoStatus = "";
	statusChangedSignal()( *this );
}

ImageSelectionTool::~ImageSelectionTool()
{
}

std::string ImageSelectionTool::status() const
{
	Context::Scope scopedContext( view()->context() );
	const bool instanceSelection = selectModePlug()->getValue() == "instance";

	std::string channelName;
	try
	{
		channelName = idChannelName( imagePlug()->channelNames()->readable(), instanceSelection );
	}
	catch( ... )
	{
		return "error:No valid image";
	}

	if( channelName == "" )
	{
		if( instanceSelection )
		{
			return "error:No instanceID channel";
		}
		else
		{
			return "error:No id channel";
		}
	}
	else if( m_manifestError.size() && !instanceSelection )
	{
		return "error:" + m_manifestError;
	}
	else if( m_infoStatus.size() )
	{
		return "info:" + m_infoStatus;
	}
	else
	{
		if( instanceSelection )
		{
			return "info:Hover instance to show id";
		}
		else
		{
			return "info:Hover object to show path";
		}
	}
}

ImageSelectionTool::StatusChangedSignal &ImageSelectionTool::statusChangedSignal()
{
	return m_statusChangedSignal;
}

Gaffer::StringPlug *ImageSelectionTool::selectModePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *ImageSelectionTool::selectModePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

GafferImage::ImagePlug *ImageSelectionTool::imagePlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 1 );
}

const GafferImage::ImagePlug *ImageSelectionTool::imagePlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 1 );
}

ImageGadget *ImageSelectionTool::imageGadget()
{
	return runTimeCast<ImageGadget>( view()->viewportGadget()->getPrimaryChild() );
}

void ImageSelectionTool::updateRenderManifest()
{
	if( selectModePlug()->getValue() == "instance" )
	{
		// We could clear m_renderManifest here ... we won't need it while we're doing instance picking.
		// But maybe it's better to leave it in memory, in case the user is about to switch back to it?
		// ( Unless the manifest is excessively large, it won't matter either way ... if it is
		// excessively large, it will take some memory, but also it could take a while to reload ).

		statusChangedSignal()( *this );
		return;
	}

	// We want to reset the render manifest now, so we don't keep using a stale manifest if this function fails.
	// But it's important we don't release the existing manifest until this function exits ( otherwise we could
	// drop the current manifest from the cache, while it's still valid based on the filepath and mod time ).
	std::shared_ptr<const RenderManifest> renderManifestKeepAlive = m_renderManifest;
	m_renderManifest.reset();
	m_manifestError.clear();

	if( !activePlug()->getValue() )
	{
		// Don't need to track the current manifest while we aren't active.
		return;
	}

	Context::Scope scopedContext( view()->context() );
	const ImagePlug *image = imagePlug();

	ConstCompoundDataPtr metadata;

	try
	{
		metadata = image->metadata();
	}
	catch( ... )
	{
		m_manifestError = "No valid image";
		return;
	}

	ConstBoolDataPtr isRenderingData = metadata->member<BoolData>( g_isRenderingMetadataName );
	if( isRenderingData && isRenderingData->readable() )
	{
		// Const cast is safe here since source scene only needs a non-const input in order to return a non-const
		// result, and we treat the result as const.
		const ScenePlug *scenePlug = SceneAlgo::sourceScene( const_cast<ImagePlug*>( image ) );

		if( scenePlug )
		{
			const InteractiveRender *interactiveRenderNode = IECore::runTimeCast<const InteractiveRender>( scenePlug->node() );
			if( interactiveRenderNode )
			{
				m_renderManifest = interactiveRenderNode->renderManifest();
			}
		}

		return;
	}

	static const std::string g_cryptoLayerName( "crypto_object" );

	try
	{
		// \todo : This should be done on a background thread.
		// There should be a status message and spinner on the status bar while the compute is happening
		// ( though it should probably only show up if the compute is slow to avoid flicker ). While the
		// compute is happening, no interaction with the image selection tool should be allowed, and
		// selection from ScriptNodeAlgo::getSelectedPaths should be synced to the selected ids when
		// the background compute finishes.
		//
		// This would be very valuable, to avoid UI freezes if the manifest is large ... but also sounds
		// a bit complicated, so we're not addressing it yet.
		m_renderManifest = RenderManifest::loadFromImageMetadata( metadata.get(), g_cryptoLayerName );
	}
	catch( std::exception &e )
	{
		m_manifestError = e.what();
	}

	selectedPathsChanged();
	statusChangedSignal()( *this );
}

void ImageSelectionTool::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == activePlug() )
	{
		updateRenderManifest();
	}
	else if( plug == imagePlug()->metadataPlug() )
	{
		// Note that we intentionally don't check whether the file paths we're using from the metadata
		// plug have actually changed ... even if the paths haven't changed, getting a metadata update
		// could indicate that the file on disk has been updated. loadFromImageMetadata will check the
		// mod time of the file on disk, and reuse it from a cache if it hasn't changed ( as long as
		// we hold a pointer to it so it doesn't get evicted ).
		updateRenderManifest();
	}
	else if( plug == selectModePlug() )
	{
		if( selectModePlug()->getValue() == "instance" )
		{
			// When selecting objects, when the manifest changes, we synchronize the current set of
			// selected objects from ScriptNodeAlgo::getSelectedPaths in selectedPathsChanged. But
			// there's no storage of selected ids instance ids outside this tool, so when switching
			// modes to instance selection, we just clear the selection.
			m_selectedIDs.clear();
			imageGadget()->setSelectedIDs( m_selectedIDs );
		}

		updateRenderManifest();
	}
	else if( plug == imagePlug()->channelNamesPlug() )
	{
		statusChangedSignal()( *this );
	}

}

IECore::PathMatcher ImageSelectionTool::pathsForIDs( const std::vector<uint32_t> &ids )
{
	if( !ids.size() )
	{
		return IECore::PathMatcher();
	}
	else if( !m_renderManifest )
	{
		return PathMatcher();
	}

	return m_renderManifest->pathsForIDs( ids );
}

void ImageSelectionTool::idsForPaths( const IECore::PathMatcher &paths, std::vector<uint32_t> &result )
{
	if( !paths.size() )
	{
		result.clear();
		return;
	}
	else if( !m_renderManifest )
	{
		result.clear();
		return;
	}

	// \todo - would it be worth saving an allocation by passing in `result` here?
	result = m_renderManifest->idsForPaths( paths );
}

std::optional<uint32_t> ImageSelectionTool::pixelID( const Imath::V2i &pixel, bool instance )
{
	const auto [ wipeEnabled, wipePosition, wipeDirection ] = effectiveWipePlane( imageGadget() );

	if( wipeEnabled && ( Imath::V2f( pixel ) + Imath::V2f( 0.5f ) - wipePosition ).dot( wipeDirection ) > 0 )
	{
		return std::nullopt;
	}

	Context::Scope scopedContext( view()->context() );

	try
	{
		std::string chanName = idChannelName( imagePlug()->channelNames()->readable(), instance );

		if( !chanName.size() )
		{
			return std::nullopt;
		}

		GafferImage::Sampler sampler( imagePlug(), chanName, Box2i( pixel, pixel + V2i( 1 ) ) );
		float floatID = sampler.sample( pixel.x, pixel.y );
		uint32_t id;
		memcpy( &id, &floatID, 4 );

		if( id == 0 )
		{
			return std::nullopt;
		}

		// If there is a valid value here, and we're dealing with instance IDs, we offset it here.
		// We apply this offsetting when writing and reading instance IDs so we can store 0 ( which
		// is a valid instance ID ).
		if( instance )
		{
			id--;
		}

		return id;
	}
	catch( ... )
	{
		// If the input image is invalid, there should be other warnings on screen, so it's OK to silently
		// return nothing here.
		return std::nullopt;
	}
}

std::unordered_set<uint32_t> ImageSelectionTool::rectIDs( const Imath::Box2i &rect, bool instance )
{
	Context::Scope scopedContext( view()->context() );
	const Imath::Box2i validRect = BufferAlgo::intersection( rect, imagePlug()->dataWindow() );

	std::unordered_set<uint32_t> result;
	if( BufferAlgo::empty( validRect ) )
	{
		return result;
	}

	const auto [ wipeEnabled, wipePosition, wipeDirection ] = effectiveWipePlane( imageGadget() );

	try
	{
		std::string chanName = idChannelName( imagePlug()->channelNames()->readable(), instance );

		if( !chanName.size() )
		{
			return result;
		}

		GafferImage::Sampler sampler( imagePlug(), chanName, validRect );

		uint32_t prevIntValue = 0;

		// Note the weird workaround here of doing init-capture of the wipe parameters, since we can't lambda capture
		// structured bindings until C++20
		sampler.visitPixels(
			validRect,
			[&result, &prevIntValue, &wipeEnabled = wipeEnabled, &wipePosition = wipePosition, &wipeDirection = wipeDirection, &instance] ( float value, int x, int y )
			{
				if( wipeEnabled && ( Imath::V2f( x, y ) + Imath::V2f( 0.5f ) - wipePosition ).dot( wipeDirection ) > 0 )
				{
					return;
				}

				uint32_t intValue;
				memcpy( &intValue, &value, 4 );

				if( intValue == 0 || intValue == prevIntValue )
				{
					return;
				}

				prevIntValue = intValue;

				result.insert( intValue - ( instance ? 1 : 0 ) );
			}
		);
	}
	catch( ... )
	{
		// If the input image is invalid, there should be other warnings on screen, so it's OK to silently
		// return nothing here.
	}

	return result;
}

void ImageSelectionTool::selectedPathsChanged()
{
	if( selectModePlug()->getValue() == "instance" )
	{
		return;
	}

	idsForPaths( ScriptNodeAlgo::getSelectedPaths( view()->scriptNode() ), m_selectedIDs );

	std::sort( m_selectedIDs.begin(), m_selectedIDs.end() );

	imageGadget()->setSelectedIDs( m_selectedIDs );

	view()->viewportGadget()->renderRequestSignal()(
		view()->viewportGadget()
	);
}

void ImageSelectionTool::updateSelectedIDs()
{
	bool instanceSelection = selectModePlug()->getValue() == "instance";

	if( instanceSelection )
	{
		std::vector<uint32_t> selectedIDsPluseOne = m_selectedIDs;
		for( uint32_t &i : selectedIDsPluseOne )
		{
			i++;
		}
		imageGadget()->setSelectedIDs( selectedIDsPluseOne );
	}
	else
	{
		imageGadget()->setSelectedIDs( m_selectedIDs );
	}

	view()->viewportGadget()->renderRequestSignal()(
		view()->viewportGadget()
	);


	if( instanceSelection )
	{
		return;
	}

	// \todo - in a worst case scenario, where every pixel has a separate id, and you've dragged a rect around all
	// of them, converting millions of ids to paths could take a couple of seconds, and it could be worth making the
	// call to pathsForIDs asynchronous ( setSelectedPaths would still need to be called on the UI thread ). Doesn't
	// seem like it's too likely to be a big problem in practice.
	Signals::BlockedConnection selectedPathsBlocker( m_selectedPathsChangedConnection );
	ScriptNodeAlgo::setSelectedPaths( view()->scriptNode(), pathsForIDs( m_selectedIDs ) );
}

void ImageSelectionTool::preRender()
{
	Context::Scope scopedContext( view()->context() );
	bool active = activePlug()->getValue();

	std::string idChan = "";
	if( active )
	{
		try
		{
			bool instanceSelection = selectModePlug()->getValue() == "instance";
			idChan = idChannelName( imagePlug()->channelNames()->readable(), instanceSelection );
		}
		catch( ... )
		{
			// The only way to fail to determine if there is a channel name is if the input image is invalid,
			// in which case there will be plenty of other warnings, so we just turn off the id channel on the
			// imageGadget.
		}
	}
	imageGadget()->setIDChannel( idChan );
}

// \todo - share somehow with SelectionTool?
ImageSelectionTool::DragOverlay *ImageSelectionTool::dragOverlay()
{
	// All instances of SelectionTool share a single drag overlay - this
	// allows SelectionTool to be subclassed for the creation of other tools.
	DragOverlay *result = view()->viewportGadget()->getChild<DragOverlay>( g_dragOverlayName );
	if( !result )
	{
		result = new DragOverlay;
		view()->viewportGadget()->setChild( g_dragOverlayName, result );
		result->setVisible( false );
	}
	return result;
}

bool ImageSelectionTool::keyPress( const KeyEvent &event )
{
	if( const auto hotkey = Gaffer::Metadata::value<StringData>( this, "viewer:shortCut" ) )
	{
		if( event.key == hotkey->readable() && event.modifiers == KeyEvent::Modifiers::Alt )
		{
			const bool newState = !activePlug()->getValue();

			activePlug()->setValue( newState );
		}
	}
	return false;
}

bool ImageSelectionTool::buttonPress( const GafferUI::ButtonEvent &event )
{
	m_acceptedButtonPress = false;
	m_initiatedDrag = false;

	if( event.buttons != ButtonEvent::Left )
	{
		return false;
	}

	if( !activePlug()->getValue() )
	{
		return false;
	}

	ImageGadget *ig = imageGadget();

	Imath::V2f pixel = ig->pixelAt( event.line );
	bool instanceSelection = selectModePlug()->getValue() == "instance";
	std::optional<uint32_t> id = pixelID( pixel, instanceSelection );

	const bool shiftHeld = event.modifiers & ButtonEvent::Shift;
	const bool controlHeld = event.modifiers & ButtonEvent::Control;
	if( !id.has_value() )
	{
		// background click - clear the selection unless a modifier is held, in
		// which case we might be starting a drag to add more or remove some.
		if( !shiftHeld && !controlHeld )
		{
			m_selectedIDs.clear();
			updateSelectedIDs();
		}
	}
	else
	{
		auto searchIt = std::lower_bound( m_selectedIDs.begin(), m_selectedIDs.end(), id.value() );

		if( searchIt != m_selectedIDs.end() && *searchIt == id.value() )
		{
			if( controlHeld )
			{
				m_selectedIDs.erase( searchIt );
				updateSelectedIDs();
			}
		}
		else
		{
			if( !controlHeld && !shiftHeld )
			{
				m_selectedIDs.clear();
				m_selectedIDs.push_back( id.value() );
			}
			else
			{
				m_selectedIDs.insert( searchIt, id.value() );
			}
			updateSelectedIDs();
		}
	}

	m_acceptedButtonPress = true;
	return true;
}

bool ImageSelectionTool::buttonRelease( const GafferUI::ButtonEvent &event )
{
	m_acceptedButtonPress = false;
	m_initiatedDrag = false;
	return false;
}

IECore::RunTimeTypedPtr ImageSelectionTool::dragBegin( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	// Derived classes may wish to override the handling of buttonPress. To
	// consume the event, they must return true from it. This also tells the
	// drag system that they may wish to start a drag later, and so it will
	// then call 'dragBegin'. If they have no interest in actually performing
	// a drag (as maybe they just wanted to do something on click) this is a
	// real pain as now they also have to implement dragBegin to prevent the
	// code below from doing its thing. To avoid this boilerplate overhead,
	// we only start our own drag if we know we were the one who returned
	// true from buttonPress. We also track whether we initiated a drag so
	// the other drag methods can early-out accordingly.
	m_initiatedDrag = false;
	if( !m_acceptedButtonPress )
	{
		return nullptr;
	}
	m_acceptedButtonPress = false;

	bool instanceSelection = selectModePlug()->getValue() == "instance";
	std::optional<uint32_t> curID = pixelID( V2i( floor( event.line.p1.x ), floor( event.line.p1.y ) ), instanceSelection );
	if( !curID.has_value() )
	{
		// drag to select
		dragOverlay()->setStartPosition( event.line.p1 );
		dragOverlay()->setEndPosition( event.line.p1 );
		dragOverlay()->setVisible( true );
		m_initiatedDrag = true;
		return gadget;
	}
	else
	{
		if( std::binary_search( m_selectedIDs.begin(), m_selectedIDs.end(), curID.value() ) )
		{
			if( !instanceSelection )
			{
				PathMatcher selectedPaths = pathsForIDs( m_selectedIDs );

				IECore::StringVectorDataPtr dragData = new IECore::StringVectorData();
				selectedPaths.paths( dragData->writable() );

				Pointer::setCurrent( "objects" );
				m_initiatedDrag = true;
				return dragData;
			}
			else
			{
				IECore::UIntVectorDataPtr dragData = new IECore::UIntVectorData();
				dragData->writable() = m_selectedIDs;

				Pointer::setCurrent( "objects" );
				m_initiatedDrag = true;
				return dragData;
			}
		}
	}

	return nullptr;
}

bool ImageSelectionTool::dragEnter( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	return m_initiatedDrag && event.sourceGadget == gadget && event.data == gadget;
}

bool ImageSelectionTool::dragMove( const GafferUI::DragDropEvent &event )
{
	if( !m_initiatedDrag )
	{
		return false;
	}

	dragOverlay()->setEndPosition( event.line.p1 );
	return true;
}

bool ImageSelectionTool::dragEnd( const GafferUI::DragDropEvent &event )
{
	if( !m_initiatedDrag )
	{
		return false;
	}

	Pointer::setCurrent( "" );
	if( !dragOverlay()->getVisible() )
	{
		return false;
	}

	bool instanceSelection = selectModePlug()->getValue() == "instance";

	dragOverlay()->setVisible( false );

	ImageGadget *ig = imageGadget();
	// TODO - it's a bit ugly that imageGadget::pixelAt can't directly take a 2D position.
	// All it does is divide x by pixelAspect, would it be better to do that manually?
	Imath::V2f startPixel = ig->pixelAt( IECore::LineSegment3f( V3f( dragOverlay()->getStartPosition().x, dragOverlay()->getStartPosition().y, 0 ), dragOverlay()->getStartPosition() ) );
	Imath::V2f endPixel = ig->pixelAt( IECore::LineSegment3f( V3f( dragOverlay()->getEndPosition().x, dragOverlay()->getEndPosition().y, 0 ), dragOverlay()->getEndPosition() ) );

	Imath::Box2i region;
	region.extendBy( startPixel );
	region.extendBy( endPixel );

	std::unordered_set<uint32_t> idsSet = rectIDs( region, instanceSelection );

	if( idsSet.size() )
	{
		PathMatcher selection = ScriptNodeAlgo::getSelectedPaths( view()->scriptNode() );
		if( event.modifiers & DragDropEvent::Control )
		{
			m_selectedIDs.erase(
				std::remove_if( m_selectedIDs.begin(), m_selectedIDs.end(), [ &idsSet ]( uint32_t id ){ return idsSet.count( id ); } ),
				m_selectedIDs.end()
			);
		}
		else
		{
			bool existingIDs = m_selectedIDs.size();
			for( uint32_t id : idsSet )
			{
				m_selectedIDs.push_back( id );
			}

			std::sort( m_selectedIDs.begin(), m_selectedIDs.end() );

			if( existingIDs )
			{
				m_selectedIDs.erase(
					std::unique( m_selectedIDs.begin(), m_selectedIDs.end() ),
					m_selectedIDs.end()
				);
			}
		}

		updateSelectedIDs();
	}

	return true;
}

bool ImageSelectionTool::mouseMove( const GafferUI::ButtonEvent &event )
{
	if( !activePlug()->getValue() )
	{
		return false;
	}

	ImageGadget *ig = imageGadget();

	Imath::V2f pixel = ig->pixelAt( event.line );

	bool instanceSelection = selectModePlug()->getValue() == "instance";
	std::optional<uint32_t> id = pixelID( pixel, instanceSelection );

	if( !id.has_value() )
	{
		imageGadget()->setHighlightID( 0 );
	}
	else if( instanceSelection )
	{
		// The image gadget doesn't know that we store instance ids offset by one,
		// because 0 is a valid instance id.
		imageGadget()->setHighlightID( id.value() + 1 );
	}
	else
	{
		imageGadget()->setHighlightID( id.value() );
	}

	m_infoStatus = "";

	if( !id.has_value() )
	{
		statusChangedSignal()( *this );
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
		return false;
	}

	if( instanceSelection )
	{
		m_infoStatus = fmt::format( "{}", id.value() );
	}
	else
	{
		std::vector<uint32_t> ids = { id.value() };
		PathMatcher paths = pathsForIDs( ids );

		if( paths.size() )
		{
			m_infoStatus = GafferScene::ScenePlug::pathToString( *PathMatcher::Iterator( paths.begin() ) );
		}
	}

	statusChangedSignal()( *this );
	view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );

	return false;
}

bool ImageSelectionTool::leave( const GafferUI::ButtonEvent &event )
{
	imageGadget()->setHighlightID( 0 );
	m_infoStatus = "";
	statusChangedSignal()( *this );
	view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	return false;
}
