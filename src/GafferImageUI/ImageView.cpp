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

#include "GafferImageUI/ImageView.h"

#include "GafferImageUI/ImageGadget.h"

#include "GafferImage/Clamp.h"
#include "GafferImage/Format.h"
#include "GafferImage/DeepState.h"
#include "GafferImage/Grade.h"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/ImageSampler.h"

#include "GafferUI/Gadget.h"
#include "GafferUI/Pointer.h"
#include "GafferUI/StandardStyle.h"
#include "GafferUI/Style.h"

#include "Gaffer/Context.h"
#include "Gaffer/DeleteContextVariables.h"
#include "Gaffer/StringPlug.h"

#include "IECoreGL/IECoreGL.h"
#include "IECoreGL/Shader.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/Texture.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/ToGLTextureConverter.h"

#include "IECore/BoxAlgo.h"
#include "IECore/BoxOps.h"
#include "IECore/FastFloat.h"

#include "OpenEXR/ImathColorAlgo.h"

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"
#include "boost/format.hpp"
#include "boost/lexical_cast.hpp"

#include <cmath>

using namespace boost;
using namespace IECoreGL;
using namespace IECore;
using namespace Imath;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferImage;
using namespace GafferImageUI;

//////////////////////////////////////////////////////////////////////////
/// Implementation of ImageView::ChannelChooser
//////////////////////////////////////////////////////////////////////////

class ImageView::ChannelChooser : public boost::signals::trackable
{

	public :

		ChannelChooser( ImageView *view )
			:	m_view( view )
		{
			StringVectorDataPtr channelsDefaultData = new StringVectorData;
			std::vector<std::string> &channelsDefault = channelsDefaultData->writable();
			channelsDefault.push_back( "R" );
			channelsDefault.push_back( "G" );
			channelsDefault.push_back( "B" );
			channelsDefault.push_back( "A" );

			view->addChild( new StringVectorDataPlug( "channels", Plug::In, channelsDefaultData ) );

			view->addChild(
				new IntPlug(
					"soloChannel",
					Plug::In,
					/* defaultValue = */ -1,
					/* minValue = */ -1,
					/* maxValue = */ 3
				)
			);

			m_view->plugSetSignal().connect( boost::bind( &ChannelChooser::plugSet, this, ::_1 ) );
			m_view->viewportGadget()->keyPressSignal().connect( boost::bind( &ChannelChooser::keyPress, this, ::_2 ) );

		}

	private :

		StringVectorDataPlug *channelsPlug()
		{
			return m_view->getChild<StringVectorDataPlug>( "channels" );
		}

		IntPlug *soloChannelPlug()
		{
			return m_view->getChild<IntPlug>( "soloChannel" );
		}

		void plugSet( const Gaffer::Plug *plug )
		{
			if( plug == soloChannelPlug() )
			{
				ImageGadget *imageGadget = static_cast<ImageGadget *>(
					m_view->viewportGadget()->getPrimaryChild()
				);
				imageGadget->setSoloChannel( soloChannelPlug()->getValue() );
			}
			else if( plug == channelsPlug() )
			{
				ConstStringVectorDataPtr channelsData = channelsPlug()->getValue();
				const std::vector<std::string> &channels = channelsData->readable();
				ImageGadget::Channels c;
				for( size_t i = 0; i < std::min( channels.size(), (size_t)4 ); ++i )
				{
					c[i] = channels[i];
				}

				ImageGadget *imageGadget = static_cast<ImageGadget *>(
					m_view->viewportGadget()->getPrimaryChild()
				);
				imageGadget->setChannels( c );
			}
		}

		bool keyPress( const GafferUI::KeyEvent &event )
		{
			if( event.modifiers )
			{
				return false;
			}

			const char *rgba[4] = { "R", "G", "B", "A" };
			for( int i = 0; i < 4; ++i )
			{
				if( event.key == rgba[i] )
				{
					soloChannelPlug()->setValue(
						soloChannelPlug()->getValue() == i ? -1 : i
					);
					return true;
				}
			}

			return false;
		}

		ImageView *m_view;

};

//////////////////////////////////////////////////////////////////////////
/// Implementation of ImageView::ColorInspector
//////////////////////////////////////////////////////////////////////////

namespace
{

class V2fContextVariable : public Gaffer::ComputeNode
{

	public :

		V2fContextVariable( const std::string &name = "V2fContextVariable" )
			:	ComputeNode( name )
		{
			storeIndexOfNextChild( g_firstPlugIndex );
			addChild( new StringPlug( "name" ) );
			addChild( new V2fPlug( "out", Plug::Out ) );
		}

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( V2fContextVariable, V2fContextVariableTypeId, ComputeNode );

		StringPlug *namePlug()
		{
			return getChild<StringPlug>( g_firstPlugIndex );
		}

		const StringPlug *namePlug() const
		{
			return getChild<StringPlug>( g_firstPlugIndex );
		}

		V2fPlug *outPlug()
		{
			return getChild<V2fPlug>( g_firstPlugIndex + 1 );
		}

		const V2fPlug *outPlug() const
		{
			return getChild<V2fPlug>( g_firstPlugIndex + 1 );
		}

		void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override
		{
			ComputeNode::affects( input, outputs );

			if( input == namePlug() )
			{
				outputs.push_back( outPlug()->getChild( 0 ) );
				outputs.push_back( outPlug()->getChild( 1 ) );
			}
		}

	protected :

		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override
		{
			ComputeNode::hash( output, context, h );
			if( output->parent() == outPlug() )
			{
				const std::string name = namePlug()->getValue();
				h.append( context->get<V2f>( name, V2f( 0 ) ) );
			}
		}

		void compute( ValuePlug *output, const Context *context ) const override
		{
			if( output->parent() == outPlug() )
			{
				const std::string name = namePlug()->getValue();
				const V2f value = context->get<V2f>( name, V2f( 0 ) );
				const size_t index = output == outPlug()->getChild( 0 ) ? 0 : 1;
				static_cast<FloatPlug *>( output )->setValue( value[index] );
			}
			else
			{
				ComputeNode::compute( output, context );
			}
		}

	private :

		static size_t g_firstPlugIndex;

};

size_t V2fContextVariable::g_firstPlugIndex = 0;
GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( V2fContextVariable )

IE_CORE_DECLAREPTR( V2fContextVariable )

} // namespace

class ImageView::ColorInspector : public boost::signals::trackable
{

	public :

		ColorInspector( ImageView *view )
			:	m_view( view ),
				m_pixel( new V2fContextVariable ),
				m_deleteContextVariables( new DeleteContextVariables ),
				m_sampler( new ImageSampler )
		{
			PlugPtr plug = new Plug( "colorInspector" );
			view->addChild( plug );
			plug->addChild( new Color4fPlug( "color" ) );

			// We use `m_pixel` to fetch a context variable to transfer
			// the mouse position into `m_sampler`. We could use `mouseMoveSignal()`
			// to instead call `m_sampler->pixelPlug()->setValue()`, but that
			// would cause cancellation of the ImageView background compute every
			// time the mouse was moved. The "colorInspector:pixel" variable is
			// created in ImageViewUI's `_ColorInspectorPlugValueWidget`.
			m_pixel->namePlug()->setValue( "colorInspector:pixel" );

			// And we use a DeleteContextVariables node to make sure that our
			// private context variable doesn't become visible to the upstream
			// graph.
			m_deleteContextVariables->setup( view->inPlug<ImagePlug>() );
			m_deleteContextVariables->variablesPlug()->setValue( "colorInspector:pixel" );

			// We want to sample the image before the display transforms
			// are applied. We can't simply get this image from inPlug()
			// because derived classes may have called insertConverter(),
			// so we take it from the input to the display transform chain.

			ImagePlug *image = view->getPreprocessor()->getChild<ImagePlug>( "out" );
			m_deleteContextVariables->inPlug()->setInput( image );
			m_sampler->imagePlug()->setInput( m_deleteContextVariables->outPlug() );
			m_sampler->pixelPlug()->setInput( m_pixel->outPlug() );

			plug->getChild<Color4fPlug>( "color" )->setInput( m_sampler->colorPlug() );

			ImageGadget *imageGadget = static_cast<ImageGadget *>( m_view->viewportGadget()->getPrimaryChild() );
			imageGadget->channelsChangedSignal().connect( boost::bind( &ColorInspector::channelsChanged, this ) );
		}

	private :

		Plug *plug()
		{
			return m_view->getChild<Plug>( "colorInspector" );
		}

		void channelsChanged()
		{
			ImageGadget *imageGadget = static_cast<ImageGadget *>( m_view->viewportGadget()->getPrimaryChild() );
			m_sampler->channelsPlug()->setValue(
				new StringVectorData( std::vector<std::string>(
					imageGadget->getChannels().begin(),
					imageGadget->getChannels().end()
				) )
			);
		}

		ImageView *m_view;
		V2fContextVariablePtr m_pixel;
		DeleteContextVariablesPtr m_deleteContextVariables;
		ImageSamplerPtr m_sampler;

};

//////////////////////////////////////////////////////////////////////////
/// Implementation of ImageView
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ImageView );

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

	BoolPlugPtr clippingPlug = new BoolPlug( "clipping", Plug::In, false, Plug::Default & ~Plug::AcceptsInputs );
	addChild( clippingPlug );

	FloatPlugPtr exposurePlug = new FloatPlug( "exposure", Plug::In, 0.0f,
		Imath::limits<float>::min(), Imath::limits<float>::max(), Plug::Default & ~Plug::AcceptsInputs
	);
	addChild( exposurePlug ); // dealt with in plugSet()

	PlugPtr gammaPlug = new FloatPlug( "gamma", Plug::In, 1.0f,
		Imath::limits<float>::min(), Imath::limits<float>::max(), Plug::Default & ~Plug::AcceptsInputs
	);
	addChild( gammaPlug );

	addChild( new StringPlug( "displayTransform", Plug::In, "Default", Plug::Default & ~Plug::AcceptsInputs ) );
	addChild( new BoolPlug( "lutGPU", Plug::In, true, Plug::Default & ~Plug::AcceptsInputs ) );

	ImagePlugPtr preprocessorOutput = new ImagePlug( "out", Plug::Out );
	preprocessor->addChild( preprocessorOutput );
	preprocessorOutput->setInput( preprocessorInput );

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

	m_channelChooser.reset( new ChannelChooser( this ) );
	m_colorInspector.reset( new ColorInspector( this ) );
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

	NodePtr preprocessor = getPreprocessor();
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

Gaffer::BoolPlug *ImageView::lutGPUPlug()
{
	return getChild<BoolPlug>( "lutGPU" );
}

const Gaffer::BoolPlug *ImageView::lutGPUPlug() const
{
	return getChild<BoolPlug>( "lutGPU" );
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
		m_imageGadget->setClipping( clippingPlug()->getValue() );
	}
	else if( plug == exposurePlug() )
	{
		m_imageGadget->setExposure( exposurePlug()->getValue() );
	}
	else if( plug == gammaPlug() )
	{
		m_imageGadget->setGamma( gammaPlug()->getValue() );
	}
	else if( plug == displayTransformPlug() )
	{
		insertDisplayTransform();
	}
	else if( plug == lutGPUPlug() )
	{
		m_imageGadget->setUseGPU( lutGPUPlug()->getValue() );
	}
}

bool ImageView::keyPress( const GafferUI::KeyEvent &event )
{
	if( event.key == "F" && !event.modifiers )
	{
		const Box3f b = m_imageGadget->bound();
		if( !b.isEmpty() && viewportGadget()->getCameraEditable() )
		{
			viewportGadget()->frame( b );
			return true;
		}
	}
	else if( event.key == "Home" && !event.modifiers )
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
	else if( event.key == "Escape" )
	{
		m_imageGadget->setPaused( true );
	}
	else if( event.key == "G" && event.modifiers == ModifiableEvent::Modifiers::Alt )
	{
		lutGPUPlug()->setValue( !lutGPUPlug()->getValue() );
	}

	return false;
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
		displayTransform = createDisplayTransform( name );
		if( displayTransform )
		{
			m_displayTransforms[name] = displayTransform;
			// Even though technically the ImageGadget will own `displayTransform`,
			// we must parent it into our preprocessor so that `BackgroundTask::cancelAffectedTasks()`
			// can find the relevant tasks to cancel if plugs on `displayTransform` are edited.
			getPreprocessor()->addChild( displayTransform );
		}
	}

	m_imageGadget->setDisplayTransform( displayTransform );
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

GafferImage::ImageProcessorPtr ImageView::createDisplayTransform( const std::string &name )
{
	const auto &m = displayTransformCreators();
	auto it = m.find( name );
	if( it != m.end() )
	{
		return it->second();
	}
	return nullptr;
}

ImageView::DisplayTransformCreatorMap &ImageView::displayTransformCreators()
{
	static auto g_creators = new DisplayTransformCreatorMap;
	return *g_creators;
}
