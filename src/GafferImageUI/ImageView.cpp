//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include <math.h>

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"
#include "boost/format.hpp"
#include "boost/lexical_cast.hpp"

#include "OpenEXR/ImathColorAlgo.h"

#include "IECore/FastFloat.h"
#include "IECore/BoxOps.h"
#include "IECore/BoxAlgo.h"

#include "IECoreGL/ToGLTextureConverter.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/Texture.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/Shader.h"
#include "IECoreGL/IECoreGL.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/BlockedConnection.h"

#include "GafferUI/Gadget.h"
#include "GafferUI/Style.h"
#include "GafferUI/StandardStyle.h"
#include "GafferUI/Pointer.h"

#include "GafferImage/Format.h"
#include "GafferImage/Grade.h"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/ImageStats.h"
#include "GafferImage/Clamp.h"
#include "GafferImage/ImageSampler.h"

#include "GafferImageUI/ImageGadget.h"
#include "GafferImageUI/ImageView.h"

using namespace boost;
using namespace IECoreGL;
using namespace IECore;
using namespace Imath;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferImage;
using namespace GafferImageUI;


namespace
{
    float EPSILON = 0.5f;
    float roundUpToEven(float a)
    {
        return ceil(a * .5) * 2;
    }

    float roundDownToEven(float a)
    {
        return floor(a * .5) * 2;
    }

    bool cmpf(float A, float B, float epsilon = EPSILON)
    { 
        return (fabs(A - B) < epsilon);
    }
}
//////////////////////////////////////////////////////////////////////////
/// Implementation of ImageView::ColorInspector
//////////////////////////////////////////////////////////////////////////

class ImageView::ColorInspector : public boost::signals::trackable
{

	public :

		ColorInspector( ImageView *view )
			:	m_view( view ),
				m_sampler( new ImageSampler )
		{
			PlugPtr plug = new Plug( "colorInspector" );
			view->addChild( plug );

			plug->addChild( new V2iPlug( "pixel" ) );
			plug->addChild( new Color4fPlug( "color" ) );

			// We want to sample the image before the display transforms
			// are applied. We can't simply get this image from inPlug()
			// because derived classes may have called insertConverter(),
			// so we take it from the input to the display transform chain.
			ImagePlug *image = view->getPreprocessor<Node>()->getChild<Clamp>( "__clamp" )->inPlug();
			m_sampler->imagePlug()->setInput( image );

			plug->getChild<Color4fPlug>( "color" )->setInput( m_sampler->colorPlug() );

			m_view->viewportGadget()->mouseMoveSignal().connect( boost::bind( &ColorInspector::mouseMove, this, ::_2 ) );
			m_view->viewportGadget()->getPrimaryChild()->buttonPressSignal().connect( boost::bind( &ColorInspector::buttonPress, this,  ::_2 ) );
			m_view->viewportGadget()->getPrimaryChild()->dragBeginSignal().connect( boost::bind( &ColorInspector::dragBegin, this, ::_2 ) );
			m_view->viewportGadget()->getPrimaryChild()->dragEndSignal().connect( boost::bind( &ColorInspector::dragEnd, this, ::_2 ) );
		}

	private :

		Plug *plug()
		{
			return m_view->getChild<Plug>( "colorInspector" );
		}

		bool mouseMove( const ButtonEvent &event )
		{
			ImageGadget *imageGadget = static_cast<ImageGadget *>( m_view->viewportGadget()->getPrimaryChild() );
			const LineSegment3f l = m_view->viewportGadget()->rasterToGadgetSpace( V2f( event.line.p0.x, event.line.p0.y ), imageGadget );
			const V2f pixel = imageGadget->pixelAt( l );
			const V2f pixelOrigin = V2f( floor( pixel.x ), floor( pixel.y ) );
			m_sampler->pixelPlug()->setValue( pixelOrigin + V2f( 0.5 ) );
			plug()->getChild<V2iPlug>( "pixel" )->setValue( pixelOrigin );
			return false;
		}

		bool buttonPress( const ButtonEvent &event )
		{
			if( event.buttons != ButtonEvent::Left || event.modifiers )
			{
				return false;
			}

			return true; // accept press so we get dragBegin()
		}

		IECore::DataPtr dragBegin( const ButtonEvent &event )
		{
			if( event.buttons != ButtonEvent::Left || event.modifiers )
			{
				return NULL;
			}

			Color4f color;
			try
			{
				Context::Scope scopedContext( m_view->getContext() );
				color = plug()->getChild<Color4fPlug>( "color" )->getValue();
			}
			catch( ... )
			{
				// If there's an error computing the image, we can't
				// start a drag.
				return NULL;
			}

			Pointer::setCurrent( "rgba" );

			return new Color4fData( color );
		}

		bool dragEnd( const ButtonEvent &event )
		{
			Pointer::setCurrent( "" );
			return true;
		}

		ImageView *m_view;
		ImageSamplerPtr m_sampler;

};

//////////////////////////////////////////////////////////////////////////
/// Implementation of ImageView
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ImageView );

ImageView::ViewDescription<ImageView> ImageView::g_viewDescription( GafferImage::ImagePlug::staticTypeId() );

ImageView::ImageView( const std::string &name )
	:	View( name, new GafferImage::ImagePlug() ),
		m_imageGadget( new ImageGadget() ),
		m_framed( false )
{

	// build the preprocessor we use for applying colour
	// transforms, and the stats node we use for displaying stats.

	NodePtr preprocessor = new Node;
	ImagePlugPtr preprocessorInput = new ImagePlug( "in" );
	preprocessor->addChild( preprocessorInput );

	ClampPtr clampNode = new Clamp();
	preprocessor->setChild(  "__clamp", clampNode );
	clampNode->inPlug()->setInput( preprocessorInput );
	clampNode->enabledPlug()->setValue( false );
	clampNode->minClampToEnabledPlug()->setValue( true );
	clampNode->maxClampToEnabledPlug()->setValue( true );
	clampNode->minClampToPlug()->setValue( Color4f( 1.0f, 1.0f, 1.0f, 0.0f ) );
	clampNode->maxClampToPlug()->setValue( Color4f( 0.0f, 0.0f, 0.0f, 1.0f ) );

	addChild( new FloatPlug( "zoomLevel", Plug::In, 1.0f, 0.001, 100, Plug::Default & ~Plug::AcceptsInputs ) );

	BoolPlugPtr clippingPlug = new BoolPlug( "clipping" );
	clippingPlug->setFlags( Plug::AcceptsInputs, false );
	addChild( clippingPlug );

	GradePtr gradeNode = new Grade;
	preprocessor->setChild( "__grade", gradeNode );
	gradeNode->inPlug()->setInput( clampNode->outPlug() );

	FloatPlugPtr exposurePlug = new FloatPlug( "exposure" );
	exposurePlug->setFlags( Plug::AcceptsInputs, false );
	addChild( exposurePlug ); // dealt with in plugSet()

	PlugPtr gammaPlug = gradeNode->gammaPlug()->getChild( 0 )->createCounterpart( "gamma", Plug::In );
	gammaPlug->setFlags( Plug::AcceptsInputs, false );
	addChild( gammaPlug );

	addChild( new StringPlug( "displayTransform", Plug::In, "Default", Plug::Default & ~Plug::AcceptsInputs ) );

	ImagePlugPtr preprocessorOutput = new ImagePlug( "out", Plug::Out );
	preprocessor->addChild( preprocessorOutput );
	preprocessorOutput->setInput( gradeNode->outPlug() );

	// tell the base class about all the preprocessing we want to do

	setPreprocessor( preprocessor );

	// connect up to some signals

	plugSetSignal().connect( boost::bind( &ImageView::plugSet, this, ::_1 ) );
	viewportGadget()->keyPressSignal().connect( boost::bind( &ImageView::keyPress, this, ::_2 ) );
	viewportGadget()->preRenderSignal().connect( boost::bind( &ImageView::preRender, this ) );

	// get our display transform right

	insertDisplayTransform();

	// Now we can connect up our ImageGadget, which will do the
	// hard work of actually displaying the image.

	m_imageGadget->setImage( preprocessedInPlug<ImagePlug>() );
	m_imageGadget->setContext( getContext() );
	viewportGadget()->setPrimaryChild( m_imageGadget );

	m_colorInspector = shared_ptr<ColorInspector>( new ColorInspector( this ) );

	m_zoomLevelChangedConnection = zoomLevelChangedSignal().connect( boost::bind( &ImageView::setZoomLevel, this, ::_1) );
	viewportGadget()->cameraChangedSignal().connect( boost::bind( &ImageView::updateZoomLevelPlug, this ) );
}

void ImageView::insertConverter( Gaffer::NodePtr converter )
{
	PlugPtr converterInput = converter->getChild<Plug>( "in" );
	if( !converterInput )
	{
		throw IECore::Exception( "Converter has no Plug named \"in\"" );
	}
	ImagePlugPtr converterOutput = converter->getChild<ImagePlug>( "out" );
	if( !converterOutput )
	{
		throw IECore::Exception( "Converter has no ImagePlug named \"out\"" );
	}

	PlugPtr newInput = converterInput->createCounterpart( "in", Plug::In );
	setChild( "in", newInput );

	NodePtr preprocessor = getPreprocessor<Node>();
	Plug::OutputContainer outputsToRestore = preprocessor->getChild<ImagePlug>( "in" )->outputs();

	PlugPtr newPreprocessorInput = converterInput->createCounterpart( "in", Plug::In );
	preprocessor->setChild( "in", newPreprocessorInput );
	newPreprocessorInput->setInput( newInput );

	preprocessor->setChild( "__converter", converter );
	converterInput->setInput( newPreprocessorInput );

	for( Plug::OutputContainer::const_iterator it = outputsToRestore.begin(), eIt = outputsToRestore.end(); it != eIt; ++it )
	{
		(*it)->setInput( converterOutput );
	}
}

ImageView::~ImageView()
{
}

Gaffer::FloatPlug *ImageView::zoomLevelPlug()
{
	return getChild<FloatPlug>( "zoomLevel" );
}

const Gaffer::FloatPlug *ImageView::zoomLevelPlug() const
{
	return getChild<FloatPlug>( "zoomLevel" );
}

Gaffer::BoolPlug *ImageView::clippingPlug()
{
	return getChild<BoolPlug>( "clipping" );
}

const Gaffer::BoolPlug *ImageView::clippingPlug() const
{
	return getChild<BoolPlug>( "clipping" );
}

Gaffer::FloatPlug *ImageView::exposurePlug()
{
	return getChild<FloatPlug>( "exposure" );
}

const Gaffer::FloatPlug *ImageView::exposurePlug() const
{
	return getChild<FloatPlug>( "exposure" );
}

Gaffer::FloatPlug *ImageView::gammaPlug()
{
	return getChild<FloatPlug>( "gamma" );
}

const Gaffer::FloatPlug *ImageView::gammaPlug() const
{
	return getChild<FloatPlug>( "gamma" );
}

Gaffer::StringPlug *ImageView::displayTransformPlug()
{
	return getChild<StringPlug>( "displayTransform" );
}

const Gaffer::StringPlug *ImageView::displayTransformPlug() const
{
	return getChild<StringPlug>( "displayTransform" );
}

GafferImage::Clamp *ImageView::clampNode()
{
	return getPreprocessor<Node>()->getChild<Clamp>( "__clamp" );
}

const GafferImage::Clamp *ImageView::clampNode() const
{
	return getPreprocessor<Node>()->getChild<Clamp>( "__clamp" );
}

GafferImage::Grade *ImageView::gradeNode()
{
	return getPreprocessor<Node>()->getChild<Grade>( "__grade" );
}

const GafferImage::Grade *ImageView::gradeNode() const
{
	return getPreprocessor<Node>()->getChild<Grade>( "__grade" );
}

void ImageView::setContext( Gaffer::ContextPtr context )
{
	View::setContext( context );
	m_imageGadget->setContext( context );
}

void ImageView::plugSet( Gaffer::Plug *plug )
{
	if( plug == clippingPlug() )
	{
		clampNode()->enabledPlug()->setValue( clippingPlug()->getValue() );
	}
	else if( plug == exposurePlug() )
	{
		const float m = pow( 2.0f, exposurePlug()->getValue() );
		gradeNode()->multiplyPlug()->setValue( Color3f( m ) );
	}
	else if( plug == gammaPlug() )
	{
		gradeNode()->gammaPlug()->setValue( Color3f( gammaPlug()->getValue() ) );
	}
	else if( plug == displayTransformPlug() )
	{
		insertDisplayTransform();
	}
	else if( plug == zoomLevelPlug() )
	{
        zoomLevelChangedSignal()(zoomLevelPlug()->getValue());
	}
}

bool ImageView::keyPress( const GafferUI::KeyEvent &event )
{
	if( !event.modifiers )
	{
		const char *rgba[4] = { "R", "G", "B", "A" };
		for( int i = 0; i < 4; ++i )
		{
			if( event.key == rgba[i] )
			{
				m_imageGadget->setSoloChannel(
					m_imageGadget->getSoloChannel() == i ? -1 : i
				);
				return true;
			}
			if(event.key == "Home")
			{
				
				V2i viewport = viewportGadget()->getViewport();
				V2i viewportCenter(viewport.x / 2, viewport.y / 2);
				Box3f bound = m_imageGadget->bound();
				V2i imageCenter((bound.max.x - bound.min.x) / 2, (bound.max.y - bound.min.y) / 2);
				Box3f frame(
					Imath::V3f(imageCenter.x - viewportCenter.x, imageCenter.y - viewportCenter.y, 0),
					Imath::V3f(imageCenter.x + viewportCenter.x, imageCenter.y + viewportCenter.y, 0)
				);
				viewportGadget()->frame(frame);
				return true;
			}
		if(event.key == "Plus")
		{
			float zoomLevel = computeZoomLevel();
			float roundLevel;

			if((zoomLevel + EPSILON) < 1.f)
			{
				zoomLevel = std::min(100.f, 1 / zoomLevel);
				roundLevel = roundDownToEven(zoomLevel);
			    
				if(cmpf(zoomLevel, roundLevel, zoomLevel * .1))
				{
					roundLevel = roundLevel * .5;
				}
				roundLevel = 1 / roundLevel;
			}
			else
			{
				roundLevel = roundUpToEven(zoomLevel);
				if(cmpf(zoomLevel, roundLevel, zoomLevel * .1))
				{
					round(roundLevel = roundLevel * 2);
				}
			}
			zoomLevelPlug()->setValue(roundLevel) ;
					
			return true;

		}
		if(event.key == "Minus")
		{
			float zoomLevel = computeZoomLevel();
			float roundLevel;
			if((zoomLevel - EPSILON) < 1.f)
			{
				zoomLevel = std::min(1000.0, round(1 / zoomLevel));
				roundLevel = roundUpToEven(zoomLevel);
				if(cmpf(zoomLevel, roundLevel, zoomLevel * .1))
				{
					roundLevel = roundLevel * 2;
				}
				roundLevel = 1 / roundLevel;
			}
			else
			{
				roundLevel = roundDownToEven(round(zoomLevel));
				if(cmpf(zoomLevel, roundLevel, zoomLevel * .1))
				{
					round(roundLevel = roundLevel * .5);
				}
			}
			zoomLevelPlug()->setValue(roundLevel) ;

			return true;
		    }
		}
		if(event.key == "Home")
		{
			V2i viewport = viewportGadget()->getViewport();
			V3f halfViewportSize(viewport.x / 2, viewport.y / 2, 0);
			V3f imageCenter = m_imageGadget->bound().center();
			viewportGadget()->frame(
				Box3f(
					V3f(imageCenter.x - halfViewportSize.x, imageCenter.y - halfViewportSize.y, 0),
					V3f(imageCenter.x + halfViewportSize.x, imageCenter.y + halfViewportSize.y, 0)
				)
			);
			return true;
		}
	}

	return false;
}

ImageView::ImageViewSignal &ImageView::zoomLevelChangedSignal()
{
	return m_zoomLevelChanged;
}

void ImageView::preRender()
{
	if( m_framed )
	{
		return;
	}

	const Box3f b = m_imageGadget->bound();
	if( b.isEmpty() )
	{
		return;
	}

	viewportGadget()->frame( b );
	m_framed = true;
    float zoomLevel = computeZoomLevel();
    zoomLevelPlug()->setValue(zoomLevel);
}

void ImageView::insertDisplayTransform()
{
	const std::string name = displayTransformPlug()->getValue();

	ImageProcessorPtr displayTransform;
	DisplayTransformMap::const_iterator it = m_displayTransforms.find( name );
	if( it != m_displayTransforms.end() )
	{
		displayTransform = it->second;
	}
	else
	{
		DisplayTransformCreatorMap &m = displayTransformCreators();
		DisplayTransformCreatorMap::const_iterator it = m.find( displayTransformPlug()->getValue() );
		if( it != m.end() )
		{
			displayTransform = it->second();
		}
		if( displayTransform )
		{
			m_displayTransforms[name] = displayTransform;
			getPreprocessor<Node>()->addChild( displayTransform );
		}
	}

	if( displayTransform )
	{
		displayTransform->inPlug()->setInput( gradeNode()->outPlug() );
		getPreprocessor<Node>()->getChild<Plug>( "out" )->setInput( displayTransform->outPlug() );
	}
	else
	{
		getPreprocessor<Node>()->getChild<Plug>( "out" )->setInput( gradeNode()->outPlug() );
	}
}

float ImageView::computeZoomLevel()
{
	const Box3f b = m_imageGadget->bound();
	const V2f imageSize = V2f(b.max.x - b.min.x, b.max.y - b.min.y);
	const V2f c0 = viewportGadget()->gadgetToRasterSpace( b.min, m_imageGadget.get() );
	const V2f c1 = viewportGadget()->gadgetToRasterSpace( b.max, m_imageGadget.get() );
	const V2f rasterSize = c1 - c0;
	return rasterSize.x / imageSize.x;
}

void ImageView::updateZoomLevelPlug()
{
	BlockedConnection blockedConnection( m_zoomLevelChangedConnection );
	float zoomLevel = computeZoomLevel();
	zoomLevelPlug()->setValue(zoomLevel);
}

void ImageView::setZoomLevel(float zoomLevel)
{
	V2f viewport = V2f(viewportGadget()->getViewport() ) * (1 / zoomLevel) ;
	V2i viewportCenter(viewport.x / 2, viewport.y / 2);
	Box3f bound = m_imageGadget->bound();
	V2i imageCenter((bound.max.x - bound.min.x) / 2, (bound.max.y - bound.min.y) / 2);
	Box3f frame(
		Imath::V3f(imageCenter.x - viewportCenter.x, imageCenter.y - viewportCenter.y, 0),
		Imath::V3f(imageCenter.x + viewportCenter.x, imageCenter.y + viewportCenter.y, 0)
	);
	viewportGadget()->frame(frame);
	return;
}
void ImageView::registerDisplayTransform( const std::string &name, DisplayTransformCreator creator )
{
	displayTransformCreators()[name] = creator;
}

void ImageView::registeredDisplayTransforms( std::vector<std::string> &names )
{
	const DisplayTransformCreatorMap &m = displayTransformCreators();
	names.clear();
	for( DisplayTransformCreatorMap::const_iterator it = m.begin(), eIt = m.end(); it != eIt; ++it )
	{
		names.push_back( it->first );
	}
}

ImageView::DisplayTransformCreatorMap &ImageView::displayTransformCreators()
{
	static DisplayTransformCreatorMap g_creators;
	return g_creators;
}


