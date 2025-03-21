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

#include "GafferSceneUI/ImagePickTool.h"

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
// ImagePickTool implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( ImagePickTool );

size_t ImagePickTool::g_firstPlugIndex = 0;
ImagePickTool::ToolDescription<ImagePickTool, ImageView> ImagePickTool::g_imageToolDescription;

ImagePickTool::ImagePickTool( View *view, const std::string &name )
	:	Tool( view, name ), m_renderManifestStorage()
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "__image", Plug::In ) );
	imagePlug()->setInput( view->inPlug<ImagePlug>() );

	m_imageSampler = new GafferImage::ImageSampler();
	m_imageSampler->imagePlug()->setInput( imagePlug() );
	m_imageSampler->interpolatePlug()->setValue( false );
	m_imageSampler->channelsPlug()->setValue( new StringVectorData( { "id", "id", "id", "id" } ) );

	view->viewportGadget()->preRenderSignal().connect( boost::bind( &ImagePickTool::preRender, this ) );
	plugDirtiedSignal().connect( boost::bind( &ImagePickTool::plugDirtied, this, ::_1 ) );

	view->viewportGadget()->keyPressSignal().connect( boost::bind( &ImagePickTool::keyPress, this, ::_2 ) );

	ImageGadget *ig = imageGadget();
	ig->buttonPressSignal().connect( boost::bind( &ImagePickTool::buttonPress, this, ::_2 ) );
	ig->mouseMoveSignal().connect( boost::bind( &ImagePickTool::mouseMove, this, ::_2 ) );

	ScriptNodeAlgo::selectedPathsChangedSignal( view->scriptNode() ).connect( boost::bind( &ImagePickTool::selectedPathsChanged, this ) );
}

ImagePickTool::~ImagePickTool()
{
}

std::string ImagePickTool::status() const
{
	return "TEST STATUS MESSAGE";
}

ImagePickTool::StatusChangedSignal &ImagePickTool::statusChangedSignal()
{
	return m_statusChangedSignal;
}

GafferImage::ImagePlug *ImagePickTool::imagePlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *ImagePickTool::imagePlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

ImageGadget *ImagePickTool::imageGadget()
{
	return runTimeCast<ImageGadget>( view()->viewportGadget()->getPrimaryChild() );
}

void ImagePickTool::setOverlayMessage( const std::string &message )
{
	m_overlayMessage = message;
	statusChangedSignal()( *this );
}

void ImagePickTool::setErrorMessage( const std::string &message )
{
	m_errorMessage = message;
	statusChangedSignal()( *this );
}

void ImagePickTool::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == imagePlug()->metadataPlug() )
	{
		// TODO - probably need to respond to this by updating the manifest ( and corresponding ids ) if necessary
	}
}

IECore::PathMatcher ImagePickTool::pathsForIds( const std::vector<uint32_t> &ids, std::string &message )
{
	updateRenderManifest();
	if( !m_renderManifest )
	{
		return PathMatcher();
	}

	return m_renderManifest->pathsForIDs( ids );
}

std::vector<uint32_t> ImagePickTool::idsForPaths( const IECore::PathMatcher &paths, std::string &message )
{
	updateRenderManifest();

	// TODO - skip checking leaves? TODO???

	return m_renderManifest->idsForPaths( paths );
}

uint32_t ImagePickTool::sampleId( const Imath::V2f &pixel )
{
	m_imageSampler->pixelPlug()->setValue( pixel );

	Context::Scope scopedContext( view()->context() );
	float floatId = m_imageSampler->colorPlug()->getChild( 0 )->getValue();

	uint32_t id;
	memcpy( &id, &floatId, 4 );
	return id;
}

void ImagePickTool::selectedPathsChanged()
{
	m_selectionDirty = true;
	view()->viewportGadget()->renderRequestSignal()(
		view()->viewportGadget()
	);
}

void ImagePickTool::updateSelection()
{
	std::string message;
	imageGadget()->setSelectedIds( idsForPaths( ScriptNodeAlgo::getSelectedPaths( view()->scriptNode() ), message ) );
}

void ImagePickTool::updateRenderManifest()
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
		throw IECore::Exception( "TODO" );
	}

	if( m_sideCarManifestPath == sideCarManifestPath && m_sideCarManifestIdentifier == sideCarManifestIdentifier )
	{
		// We're using a manifest file, and it hasn't changed since we last updated m_renderManifestStorage
		m_renderManifest = &m_renderManifestStorage;
		return;
	}

	m_sideCarManifestPath = sideCarManifestPath;
	m_sideCarManifestIdentifier = sideCarManifestIdentifier;

	m_renderManifestStorage.readEXRManifest( m_sideCarManifestPath.c_str() );
	m_renderManifest = &m_renderManifestStorage;
}

void ImagePickTool::preRender()
{
	bool active = activePlug()->getValue();
	imageGadget()->setIdChannel( active ? "id" : "" );

	if( m_selectionDirty )
	{
		updateSelection();
		m_selectionDirty = false;
	}
}

bool ImagePickTool::keyPress( const KeyEvent &event )
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

bool ImagePickTool::buttonPress( const GafferUI::ButtonEvent &event )
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

bool ImagePickTool::mouseMove( const GafferUI::ButtonEvent &event )
{
	ImageGadget *ig = imageGadget();

	Imath::V2f pixel = ig->pixelAt( event.line );

	imageGadget()->setHighlightId( sampleId( pixel ) );

	view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );

	return false;
}
