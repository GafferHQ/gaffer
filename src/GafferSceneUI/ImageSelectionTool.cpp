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

namespace {

std::pair< std::string, int > findSideCarMetadata( const ImagePlug *image )
{
	std::string resultPath;
	std::string resultIdentifier;
	ConstStringVectorDataPtr views = image->viewNames();

	for( const std::string &view : views->readable() )
	{
		GafferImage::ImagePlug::ViewScope viewScope( Context::current() );
		viewScope.setViewName( &view );
		ConstCompoundDataPtr metadata = image->metadata();
		const StringData *filePathData = metadata->member<StringData>( "gaffer:idManifestFilePath" );
		if( filePathData )
		{
			int identifier = 0;

			const IntData *identifierData = metadata->member<IntData>( "gaffer:idManifestIdentifier" );
			if( identifierData )
			{
				identifier = identifierData->readable();
			}

			return std::make_pair( filePathData->readable(), identifier );
		}
	}

	return std::make_pair( "", 0 );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ImageSelectionTool implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( ImageSelectionTool );

size_t ImageSelectionTool::g_firstPlugIndex = 0;
ImageSelectionTool::ToolDescription<ImageSelectionTool, ImageView> ImageSelectionTool::g_imageToolDescription;

ImageSelectionTool::ImageSelectionTool( View *view, const std::string &name )
	:	Tool( view, name ), m_renderManifestStorage()
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
	ig->mouseMoveSignal().connect( boost::bind( &ImageSelectionTool::mouseMove, this, ::_2 ) );

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
		// TODO - probably need to respond to this by updating the manifest ( and corresponding ids ) if necessary
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
	// TODO - skip checking leaves? TODO???

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

	// Const cast is safe here since source scene only needs a non-const input in order to return a non-const
	// result, and we treat the result as const.
	const ScenePlug *scenePlug = SceneAlgo::sourceScene( const_cast<ImagePlug*>( image ) );

	if( scenePlug )
	{
		const InteractiveRender *interactiveRenderNode = IECore::runTimeCast<const InteractiveRender>( scenePlug->node() );
		if( interactiveRenderNode )
		{
			m_renderManifest = interactiveRenderNode->renderManifest();
			return;
		}
	}

	const auto& [ sideCarManifestPath, sideCarManifestIdentifier ] = findSideCarMetadata( image );

	if( sideCarManifestPath == "" )
	{
		message = "No source InteractiveRender node or gaffer:idManifestFilePath metadata found. Selection not supported without id manifest.";
		return;
	}

	if( m_sideCarManifestPath == sideCarManifestPath && m_sideCarManifestIdentifier == sideCarManifestIdentifier )
	{
		// We're using a manifest file, and it hasn't changed since we last updated m_renderManifestStorage
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
	m_sideCarManifestIdentifier = sideCarManifestIdentifier;
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
	// TODO : In addition to supporting clicks, we should probably support all selection interactions
	// from the viewport ( like dragging for rectangle selection? )

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

bool ImageSelectionTool::leaveSignal( const GafferUI::ButtonEvent &event )
{
	imageGadget()->setHighlightId( 0 );
	setStatus( "", false );
	view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	return false;
}
