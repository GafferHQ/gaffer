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

#include "GafferSceneUI/ImageSelectionTool.h"

#include "GafferImageUI/ImageGadget.h"

#include "GafferSceneUI/SceneView.h"
#include "GafferSceneUI/ScriptNodeAlgo.h"

#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"

#include "GafferScene/InteractiveRender.h"
#include "GafferScene/ScenePlug.h"

#include "GafferScene/Private/RendererAlgo.h"

#include "GafferImage/ImagePlug.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"

#include "boost/bind/bind.hpp"

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

std::string g_isRenderingMetadataName = "gaffer:isRendering";

static IECore::InternedString g_dragOverlayName( "__imageSelectionToolDragOverlay" );

}

class ImageSelectionTool::DragOverlay : public GafferUI::Gadget
{

	public :

		DragOverlay()
			:   Gadget()
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
			// TODO - should be MidFront, if we weren't (mis)using that for id selection
			assert( layer == Layer::Front );

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
			return (unsigned)Layer::Front;
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
	:	Tool( view, name ), m_renderManifestStorage(), m_sideCarManifestModTimeDirty( true )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "__image", Plug::In ) );
	imagePlug()->setInput( view->inPlug<ImagePlug>() );

	m_imageSampler = new GafferImage::ImageSampler();
	m_imageSampler->imagePlug()->setInput( imagePlug() );
	m_imageSampler->interpolatePlug()->setValue( false );
	m_imageSampler->channelsPlug()->setValue( new StringVectorData( { "id", "id", "id", "id" } ) );

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

	ScriptNodeAlgo::selectedPathsChangedSignal( view->scriptNode() ).connect( boost::bind( &ImageSelectionTool::selectedPathsChanged, this ) );
}

ImageSelectionTool::~ImageSelectionTool()
{
}

std::string ImageSelectionTool::status() const
{
	return m_status;
}

void ImageSelectionTool::setStatus( const std::string &message, bool error )
{
	m_status = "";

	if( error )
	{
		m_status = "error:" + message;
	}
	else if( message.size() )
	{
		m_status = "info:" + message;
	}
	statusChangedSignal()( *this );
}

ImageSelectionTool::StatusChangedSignal &ImageSelectionTool::statusChangedSignal()
{
	return m_statusChangedSignal;
}

GafferImage::ImagePlug *ImageSelectionTool::imagePlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *ImageSelectionTool::imagePlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

ImageGadget *ImageSelectionTool::imageGadget()
{
	return runTimeCast<ImageGadget>( view()->viewportGadget()->getPrimaryChild() );
}


void ImageSelectionTool::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == imagePlug()->metadataPlug() )
	{
		// We use this dirty signal in a somewhat unconventional way : we don't actually care about whether
		// the metadata has changed, but we assume that if the input image is modified, it will trigger this
		// signal. That gives us a cue that we need to recheck the manifest - even if none of the metadata
		// has changed, if the image was rewritten, the manifest might have been rewritten as well.
		m_sideCarManifestModTimeDirty = true;
		m_selectionDirty = true;
		setStatus( "", false );
	}
}

IECore::PathMatcher ImageSelectionTool::pathsForIds( const std::vector<uint32_t> &ids, std::string &message )
{
	updateRenderManifest( message );
	if( !m_renderManifest )
	{
		return PathMatcher();
	}

	return m_renderManifest->pathsForIDs( ids );
}

std::vector<uint32_t> ImageSelectionTool::idsForPaths( const IECore::PathMatcher &paths, std::string &message )
{
	updateRenderManifest( message );

	if( !m_renderManifest )
	{
		return std::vector<uint32_t>();
	}

	return m_renderManifest->idsForPaths( paths );
}

uint32_t ImageSelectionTool::sampleId( const Imath::V2f &pixel )
{
	m_imageSampler->pixelPlug()->setValue( pixel );

	Context::Scope scopedContext( view()->context() );
	float floatId = m_imageSampler->colorPlug()->getChild( 0 )->getValue();

	uint32_t id;
	memcpy( &id, &floatId, 4 );
	return id;
}

void ImageSelectionTool::selectedPathsChanged()
{
	m_selectionDirty = true;
	view()->viewportGadget()->renderRequestSignal()(
		view()->viewportGadget()
	);
}

void ImageSelectionTool::updateSelection()
{
	std::string message;
	imageGadget()->setSelectedIds( idsForPaths( ScriptNodeAlgo::getSelectedPaths( view()->scriptNode() ), message ) );
}

void ImageSelectionTool::updateRenderManifest( std::string &message )
{
	m_renderManifest = nullptr;

	Context::Scope scopedContext( view()->context() );
	const ImagePlug *image = imagePlug();

	ConstBoolDataPtr isRenderingData = image->metadata()->member<BoolData>( g_isRenderingMetadataName );
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

	std::string sideCarManifestPath;
	for( const std::string &view : image->viewNames()->readable() )
	{
		ConstCompoundDataPtr metadata = image->metadata( &view );
		const StringData *manifestFilePathData = metadata->member<StringData>( "gaffer:idManifestFilePath" );
		if( manifestFilePathData )
		{
			std::filesystem::path rawManifestPath( manifestFilePathData->readable() );
			if( rawManifestPath.is_absolute() )
			{
				sideCarManifestPath = rawManifestPath.generic_string();
			}
			else
			{
				const StringData *filePathData = metadata->member<StringData>( "filePath" );
				if( !filePathData )
				{
					message = "Can't find \"filePath\" metadata to locate relative manifest path. It should have been set by the ImageReader.";
					return;
				}
				sideCarManifestPath = ( std::filesystem::path( filePathData->readable() ).parent_path() / rawManifestPath ).generic_string();
			}
			break;
		}
	}

	if( sideCarManifestPath == "" )
	{
		message = "No source InteractiveRender node or gaffer:idManifestFilePath metadata found. Selection not supported without id manifest.";
		return;
	}


	if( m_sideCarManifestPath == sideCarManifestPath && !m_sideCarManifestModTimeDirty )
	{
		// We're using a manifest file, and there's no reason to think it's changed since we last
		// updated m_renderManifestStorage
		m_renderManifest = &m_renderManifestStorage;
		return;
	}

	// We've received a metadata update - we don't know whether it's changed anything, but we better
	// a least check the mod time of the manifest.
	std::filesystem::file_time_type currentModTime;
	try
	{
		currentModTime = std::filesystem::last_write_time( sideCarManifestPath );
	}
	catch( std::exception &e )
	{
		message = std::string( "Could not find manifest file : " ) + sideCarManifestPath + " : " + e.what();
		return;
	}

	if( m_sideCarManifestPath == sideCarManifestPath && m_sideCarManifestModTime == currentModTime )
	{
		// We're using a manifest file, and the timestamp hasn't changed since we last updated m_renderManifestStorage
		m_renderManifest = &m_renderManifestStorage;
		return;
	}

	try
	{
		m_renderManifestStorage.readEXRManifest( sideCarManifestPath.c_str() );
	}
	catch( std::exception &e )
	{
		message = std::string( "Exception : " ) + e.what();
		return;
	}

	m_renderManifest = &m_renderManifestStorage;

	m_sideCarManifestPath = sideCarManifestPath;
	m_sideCarManifestModTime = currentModTime;
	m_sideCarManifestModTimeDirty = false;
}

void ImageSelectionTool::preRender()
{
	bool active = activePlug()->getValue();
	imageGadget()->setIdChannel( active ? "id" : "" );

	if( m_selectionDirty )
	{
		updateSelection();
		m_selectionDirty = false;
	}
}

// TODO - share somehow with SelectionTool?
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
	uint32_t id = sampleId( pixel );

	std::vector<uint32_t> ids = { id };

	std::string message;
	PathMatcher paths = pathsForIds( ids, message );

	PathMatcher selection = ScriptNodeAlgo::getSelectedPaths( view()->scriptNode() );

	const bool shiftHeld = event.modifiers & ButtonEvent::Shift;
	const bool controlHeld = event.modifiers & ButtonEvent::Control;
	if( paths.isEmpty() )
	{
		// background click - clear the selection unless a modifier is held, in
		// which case we might be starting a drag to add more or remove some.
		if( !shiftHeld && !controlHeld )
		{
			ScriptNodeAlgo::setSelectedPaths( view()->scriptNode(), IECore::PathMatcher() );
		}
	}
	else
	{
		if( paths.size() != 1 )
		{
			return true;
		}


		bool objectSelectedAlready = true;
		for( PathMatcher::Iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
		{
			objectSelectedAlready &= (bool)( selection.match( *it ) & PathMatcher::ExactMatch );
		}

		if( objectSelectedAlready )
		{
			if( controlHeld )
			{
				selection.removePaths( paths );
				ScriptNodeAlgo::setSelectedPaths( view()->scriptNode(), selection );
			}
		}
		else
		{
			if( !controlHeld && !shiftHeld )
			{
				ScriptNodeAlgo::setSelectedPaths( view()->scriptNode(), IECore::PathMatcher() );
			}

			for( PathMatcher::Iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
			{
				ScriptNodeAlgo::setLastSelectedPath( view()->scriptNode(), *it );
			}
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

	//SceneGadget *sg = sceneGadget();
	//ScenePlug::ScenePath objectUnderMouse;

	//if( !sg->objectAt( event.line, objectUnderMouse ) )
	{
		// drag to select
		dragOverlay()->setStartPosition( event.line.p1 );
		dragOverlay()->setEndPosition( event.line.p1 );
		dragOverlay()->setVisible( true );
		m_initiatedDrag = true;
		return gadget;
	}
	// TODO - should we support dragging paths from the image?
	/*else
	{
		const PathMatcher &selection = sg->getSelection();
		if( selection.match( objectUnderMouse ) & PathMatcher::ExactMatch )
		{
			// drag the selection somewhere
			IECore::StringVectorDataPtr dragData = new IECore::StringVectorData();
			selection.paths( dragData->writable() );
			Pointer::setCurrent( "objects" );
			m_initiatedDrag = true;
			return dragData;
		}
	}*/
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

	dragOverlay()->setVisible( false );

	ImageGadget *ig = imageGadget();
	// TODO - ugly
	Imath::V2f startPixel = ig->pixelAt( IECore::LineSegment3f( V3f( dragOverlay()->getStartPosition().x, dragOverlay()->getStartPosition().y, 0 ), dragOverlay()->getStartPosition() ) );
	Imath::V2f endPixel = ig->pixelAt( IECore::LineSegment3f( V3f( dragOverlay()->getEndPosition().x, dragOverlay()->getEndPosition().y, 0 ), dragOverlay()->getEndPosition() ) );

	std::cerr << "PIXELS " << startPixel << ", " << endPixel << "\n";

	Imath::Box2i region;
	region.extendBy( startPixel );
	region.extendBy( endPixel );

	std::unordered_set<uint32_t> idsSet;


	V2i pixel;
	// TODO - off by 1
	for( pixel.y = region.min.y; pixel.y < region.max.y; pixel.y++ )
	{
		for( pixel.x = region.min.x; pixel.x < region.max.x; pixel.x++ )
		{
			// TODO - incredibly slow
			idsSet.insert( sampleId( pixel ) );
		}
	}
	std::vector<uint32_t> ids;
	ids.reserve( idsSet.size() );
	for( uint32_t i : idsSet )
	{
		ids.push_back( i );
	}

	std::string message;
	PathMatcher paths = pathsForIds( ids, message );

	if( paths.size() )
	{
		PathMatcher selection = ScriptNodeAlgo::getSelectedPaths( view()->scriptNode() );
		if( event.modifiers & DragDropEvent::Control )
		{
			selection.removePaths( paths );
		}
		else
		{
			selection.addPaths( paths );
		}

		ScriptNodeAlgo::setSelectedPaths( view()->scriptNode(), selection );
	}

	return true;
}

bool ImageSelectionTool::mouseMove( const GafferUI::ButtonEvent &event )
{
	ImageGadget *ig = imageGadget();

	Imath::V2f pixel = ig->pixelAt( event.line );

	// TODO - catch invalid ids
	uint32_t id = sampleId( pixel );
	imageGadget()->setHighlightId( id );

	if( id == 0 )
	{
		setStatus( "", false );
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	}

	std::vector<uint32_t> ids = { id };
	std::string message;
	PathMatcher paths = pathsForIds( ids, message );

	if( paths.size() )
	{
		setStatus( GafferScene::ScenePlug::pathToString( *PathMatcher::Iterator( paths.begin() ) ), false );
	}
	else if( message.size() )
	{
		setStatus( message, true );
	}

	view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );

	return false;
}

bool ImageSelectionTool::leave( const GafferUI::ButtonEvent &event )
{
	imageGadget()->setHighlightId( 0 );
	setStatus( "", false );
	view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	return false;
}
