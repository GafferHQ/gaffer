//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "GafferImageUI/DeepSampleGadget.h"

#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "Gaffer/Animation.h"
#include "Gaffer/Context.h"
#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"
#include "Gaffer/ScriptNode.h"

#include "IECoreGL/Selector.h"

#include "IECore/InternedString.h"

#include "boost/algorithm/string.hpp"
#include "boost/bind.hpp"

#include <cmath>

using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferImageUI;
using namespace Imath;

//////////////////////////////////////////////////////////////////////////
// DeepSampleGadget implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( GafferImageUI::DeepSampleGadget );

DeepSampleGadget::DeepSampleGadget()
	: m_visiblePlugs( new StandardSet() ), m_editablePlugs( new StandardSet() ), m_highlightedKey( -1 ), m_highlightedCurve( -1 ), m_keyPreview( false ), m_keyPreviewLocation( 0 ), m_xMargin( 60 ), m_yMargin( 20 ), m_textScale( 10 ), m_labelPadding( 5 ), m_frameIndicatorPreviewFrame( boost::none ), m_autoFrame( true ), m_logarithmic( false )
{
	m_deepSampleDicts = new CompoundData();
	keyPressSignal().connect( boost::bind( &DeepSampleGadget::keyPress, this, ::_1,  ::_2 ) );
	dirty( DirtyType::Render );
}

DeepSampleGadget::~DeepSampleGadget()
{
}

void DeepSampleGadget::setDeepSamples( ConstCompoundDataPtr deepSamples )
{
	m_deepSampleDicts = deepSamples;
	CompoundDataPtr accumDicts = new CompoundData();

	for( auto const &imageData : m_deepSampleDicts->readable() )
	{
		const CompoundData *image = IECore::runTimeCast< CompoundData >( imageData.second.get() );

		ConstFloatVectorDataPtr zData = image->member<FloatVectorData>( "Z" );
		ConstFloatVectorDataPtr zBackData = image->member<FloatVectorData>( "ZBack" );
		ConstFloatVectorDataPtr aData = image->member<FloatVectorData>( "A" );

		if( !zData || !zData->readable().size() )
		{
			continue;
		}

		if( !zBackData )
		{
			zBackData = zData;
		}

		FloatVectorDataPtr accumAlphaData = new FloatVectorData();
		std::vector<float> &accumAlpha = accumAlphaData->writable();
		accumAlpha.resize( zData->readable().size(), 0.0 );
		if( aData )
		{
			float accum = 0;
			const std::vector<float>& alpha = aData->readable();
			for( unsigned int i = 0; i < alpha.size(); i++ )
			{
				accum += alpha[i] - alpha[i] * accum;
				accumAlpha[i] = accum;
			}

			/*
			std::cerr << "A SAMPLES:\n";
			for( unsigned int i = 0; i < alpha.size(); i++ )
			{
				std::cerr << alpha[i] << " ";
			}
			std::cerr << "\n";
			*/
		}

		/*
		std::cerr << "Z SAMPLES:\n";
		for( unsigned int i = 0; i < zData->readable().size(); i++ )
		{
			std::cerr << zData->readable()[i] << " ";
		}
		std::cerr << "\n";

		std::cerr << "ZBack SAMPLES:\n";
		for( unsigned int i = 0; i < zBackData->readable().size(); i++ )
		{
			std::cerr << zBackData->readable()[i] << " ";
			if( zBackData->readable()[i] > 100000 )
			{
				zBackData = zData;
			}
		}
		std::cerr << "\n";
		*/

		CompoundDataPtr newImage = new CompoundData();

		// const cast is OK because the final result m_deepSampleDictsAccumulated is const
		newImage->writable()["Z"] = boost::const_pointer_cast<FloatVectorData>( zData );
		newImage->writable()["ZBack"] = boost::const_pointer_cast<FloatVectorData>( zBackData );
		newImage->writable()["A"] = accumAlphaData;
		for( auto const &channelData : image->readable() )
		{
			if( channelData.first == "Z" || channelData.first == "ZBack" || channelData.first == "A" )
			{
				continue;
			}
			const std::vector<float> &channel = IECore::runTimeCast< FloatVectorData >( channelData.second.get() )->readable();

			FloatVectorDataPtr accumData = new FloatVectorData();
			std::vector<float> &accumVec = accumData->writable();
			accumVec.resize( accumAlpha.size(), 0.0 );
			float accum = 0;
			for( unsigned int i = 0; i < channel.size(); i++ )
			{
				accum += channel[i] - channel[i] * ( i > 0 ? accumAlpha[i-1] : 0 );
				accumVec[i] = accum;
			}
			newImage->writable()[ channelData.first ] = accumData;
		}

		accumDicts->writable()[ imageData.first ] = newImage;
	}
	m_deepSampleDictsAccumulated = accumDicts;
	if( m_autoFrame )
	{
		frame();
	}
	dirty( DirtyType::Render );
}

void DeepSampleGadget::setAutoFrame( bool autoFrame )
{
	m_autoFrame = autoFrame;
}

void DeepSampleGadget::setLogarithmic( bool log )
{
	m_logarithmic = log;
	if( m_autoFrame )
	{
		frame();
	}
	dirty( DirtyType::Render );
}

unsigned DeepSampleGadget::layerMask() const
{
    return (unsigned)(
		Gadget::Layer::Back |
		Gadget::Layer::MidBack |
		Gadget::Layer::Main |
		Gadget::Layer::MidFront |
		Gadget::Layer::Front
	);
}

Imath::Box3f DeepSampleGadget::renderBound() const
{
    // Not worried about culling for perf
    Box3f b;
    b.makeInfinite();
    return b;
}


void DeepSampleGadget::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	Gadget::renderLayer( layer, style, reason );

	glDisable( GL_DEPTH_TEST );

	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	Imath::V2i resolution = viewportGadget->getViewport();

	ViewportGadget::RasterScope rasterScope( viewportGadget );

	switch ( layer )
	{

	case Gadget::Layer::Back :
	{
		AxisDefinition xAxis, yAxis;
		computeGrid( viewportGadget, xAxis, yAxis );

		Imath::Color4f axesColor( 60.0 / 255, 60.0 / 255, 60.0 / 255, 1.0f );

		// drawing base grid
		for( const auto &x : xAxis.main )
		{
			style->renderLine( LineSegment3f( V3f( x.first, 0, 0 ), V3f( x.first, resolution.y, 0 ) ), x.second == 0.0f ? 3.0 : 2.0, &axesColor );
		}

		for( const auto &y : yAxis.main )
		{
			style->renderLine( LineSegment3f( V3f( 0, y.first, 0 ), V3f( resolution.x, y.first, 0 ) ), y.second == 0.0f ? 3.0 : 2.0, &axesColor );
		}

		// drawing sub grid
		for( float x : xAxis.secondary )
		{
			style->renderLine( LineSegment3f( V3f( x, 0, 0 ), V3f( x, resolution.y, 0 ) ), 1.0, &axesColor );
		}

		break;
	}

	case Gadget::Layer::MidBack :
	{
		for( auto const &imageData : m_deepSampleDicts->readable() )
		{
			const CompoundData *image = IECore::runTimeCast< CompoundData >( imageData.second.get() );

			const FloatVectorData *zData = image->member<FloatVectorData>( "Z" );
			const FloatVectorData *zBackData = image->member<FloatVectorData>( "ZBack" );
			const FloatVectorData *aData = image->member<FloatVectorData>( "A" );

			if( !zData || !zData->readable().size() )
			{
				continue;
			}

			if( !zBackData )
			{
				zBackData = zData;
			}

			for( auto const &channelData : image->readable() )
			{
				if( channelData.first == "Z" || channelData.first == "ZBack" )
				{
					continue;
				}
				const FloatVectorData *channel = IECore::runTimeCast< FloatVectorData >( channelData.second.get() );

				Color3f c( 0.8 );
				Color4f c4( c[0], c[1], c[2], 0.0 );
				V2f size( 2.0f );

				//IECoreGL::glColor( c );
				float accum = 0;
				float accumAlpha = 0;
				V2f prevPos = viewportGadget->worldToRasterSpace( V3f( zData->readable()[0], axisMapping( 0 ), 0 ) );
				for( unsigned int i = 0; i < channel->readable().size(); i++ )
				{
					//
					float a = 0;
					if( aData )
					{
						a = aData->readable()[i];
					}
					float z = zData->readable()[i];
					float zBack = zBackData->readable()[i];
					float c = channel->readable()[i];

					int steps = 100;
					for( int i = 0; i < steps; i++ )
					{
						float lerp = float(i) / float( steps - 1 );
						float cur = a == 0.0f ? accum + c * lerp : accum + ( 1 - accumAlpha ) * c * ( 1 - pow( 1 - a, lerp) ) / a;
						//float cur = accum + ( 1 - accumAlpha ) * c;
						V2f pos = viewportGadget->worldToRasterSpace( V3f( z + lerp * ( zBack - z ), axisMapping( cur ), 0 ) );
						//std::cerr << "huh: " << pos << "\n";

						style->renderLine( LineSegment3f( V3f( prevPos.x, prevPos.y, 0 ), V3f( pos.x, pos.y, 0 ) ), 1.0 ); //, &c4 );
						prevPos = pos;
					}
					//style->renderLine( LineSegment3f( V3f( startPosition.x, startPosition.y, 0 ), V3f( endPosition.x, endPosition.y, 0 ) ), 1.0 ); //, &c4 );
					//prevPos = endPosition;

					accum += c - c * accumAlpha;

					accumAlpha += a - a * accumAlpha;
				}
			}
		}

		break;
	}

	case Gadget::Layer::Main :
	{
		for( auto const &imageData : m_deepSampleDicts->readable() )
		{
			const CompoundData *image = IECore::runTimeCast< CompoundData >( imageData.second.get() );

			const FloatVectorData *zData = image->member<FloatVectorData>( "Z" );
			const FloatVectorData *zBackData = image->member<FloatVectorData>( "ZBack" );
			const FloatVectorData *aData = image->member<FloatVectorData>( "A" );

			if( !zData )
			{
				continue;
			}

			if( !zBackData )
			{
				zBackData = zData;
			}

			for( auto const &channelData : image->readable() )
			{
				if( channelData.first == "Z" || channelData.first == "ZBack" )
				{
					continue;
				}
				const FloatVectorData *channel = IECore::runTimeCast< FloatVectorData >( channelData.second.get() );

				Color3f c( 0.7 );
				if( channelData.first == "R" || boost::ends_with( channelData.first.string(), ".R" ) )
				{
					c = Color3f( 1.0f, 0.0f, 0.0f );
				}
				else if( channelData.first == "G" || boost::ends_with( channelData.first.string(), ".G" ) )
				{
					c = Color3f( 0.0f, 1.0f, 0.0f );
				}
				else if( channelData.first == "B" || boost::ends_with( channelData.first.string(), ".B" ) )
				{
					c = Color3f( 0.0f, 0.0f, 1.0f );
				}
				else if( channelData.first == "A" || boost::ends_with( channelData.first.string(), ".A" ) )
				{
					c = Color3f( 1.0f, 1.0f, 1.0f );
				}
				V2f size( 2.0f );

				IECoreGL::glColor( c );
				float accum = 0;
				float accumAlpha = 0;
				for( unsigned int i = 0; i < channel->readable().size(); i++ )
				{
					V2f startPosition = viewportGadget->worldToRasterSpace( V3f( zData->readable()[i], axisMapping( accum ), 0 ) );
					accum += channel->readable()[i] - channel->readable()[i] * accumAlpha;
					if( aData )
					{
						accumAlpha += aData->readable()[i] - aData->readable()[i] * accumAlpha;
					}
					V2f endPosition = viewportGadget->worldToRasterSpace( V3f( zBackData->readable()[i], axisMapping( accum ), 0 ) );
					//std::cerr << "e:" << endPosition << "\n";
					//style->renderSolidRectangle( Box2f( startPosition - size, startPosition + size ) );
					style->renderSolidRectangle( Box2f( endPosition - size, endPosition + size ) );
				}
			}
		}
		/*for( auto &runtimeTyped : *m_editablePlugs )
		{
			Animation::CurvePlug *curvePlug = IECore::runTimeCast<Animation::CurvePlug>( &runtimeTyped );

			for( Animation::Key &key : *curvePlug )
			{
				bool isHighlighted = ( m_highlightedKey && key == *m_highlightedKey ) || ( selecting && b.intersects( V2f( key.getTime(), key.getValue() ) ));
				bool isSelected = m_selectedKeys.count( Animation::KeyPtr( &key ) ) > 0;
				V2f keyPosition = viewportGadget->worldToRasterSpace( V3f( key.getTime(), key.getValue(), 0 ) );
				style->renderAnimationKey( keyPosition, isSelected || isHighlighted ? Style::HighlightedState : Style::NormalState, isHighlighted ? 3.0 : 2.0, &black );
			}
		}*/
		break;
	}

	case Gadget::Layer::MidFront :
	{
		AxisDefinition xAxis, yAxis;
		computeGrid( viewportGadget, xAxis, yAxis );

		// draw axes on top of everything.
		Imath::Color4f axesColor( 60.0 / 255, 60.0 / 255, 60.0 / 255, 1.0 );
		IECoreGL::glColor( axesColor ); // \todo: maybe renderSolidRectangle() should accept a userColor
		style->renderSolidRectangle( Box2f( V2f( 0 ) , V2f( m_xMargin, resolution.y - m_yMargin ) ) );
		style->renderSolidRectangle( Box2f( V2f( 0, resolution.y - m_yMargin ) , V2f( resolution.x, resolution.y ) ) );

		int xPrecision = 3;
		if( xAxis.main.size() >= 2 )
		{
			xPrecision = std::max( 3, int( log10f( xAxis.main.size() / ( xAxis.main.back().second - xAxis.main[0].second ) ) ) );
		}
		boost::format formatX( "%." + std::to_string( xPrecision ) + "f" );

		// \todo: pull matrix stack operations out of the loops.
		for( const auto &x : xAxis.main )
		{
			if( x.first < m_xMargin )
			{
				continue;
			}

			glPushMatrix();

			std::string label = boost::str( formatX % x.second );
			Box3f labelBound = style->textBound( Style::BodyText, label );

			glTranslatef( x.first - labelBound.center().x * m_textScale, resolution.y - m_labelPadding, 0.0f );
			glScalef( m_textScale, -m_textScale, m_textScale );

			style->renderText( Style::BodyText, label );

			glPopMatrix();
		}

		int yPrecision = 3;
		if( yAxis.main.size() >= 2 )
		{
			yPrecision = std::max( 3, int( log10f( yAxis.main.size() / ( yAxis.main.back().second - yAxis.main[0].second ) ) ) );
		}
		boost::format formatY( "%." + std::to_string( yPrecision ) + "f" );
		for( const auto &y : yAxis.main )
		{
			if( y.first > resolution.y - m_yMargin )
			{
				continue;
			}

			glPushMatrix();

			std::string label = boost::str( formatY % y.second );
			Box3f labelBound = style->textBound( Style::BodyText, label );

			glTranslatef( ( m_xMargin - m_labelPadding ) - labelBound.size().x * m_textScale, y.first + labelBound.center().y * m_textScale, 0.0f );
			glScalef( m_textScale, -m_textScale, m_textScale );

			style->renderText( Style::BodyText, label );

			glPopMatrix();
		}

		break;

	}

	case Gadget::Layer::Front :
	{
		if( m_keyPreview )
		{
			V2f keyPosition = viewportGadget->worldToRasterSpace( m_keyPreviewLocation );
			style->renderAnimationKey( keyPosition, Style::HighlightedState, 3.0 );
		}

		break;
	}

	default:
		break;

	}
}

void DeepSampleGadget::plugDirtied( Gaffer::Plug *plug )
{
	dirty( DirtyType::Render );
}

std::string DeepSampleGadget::getToolTip( const LineSegment3f &line ) const
{
	if( int key = keyAt( line ) >= 0 )
	{
		//return boost::str( boost::format( "%f -> %f" ) % key->getTime() % key->getValue() );
		return boost::str( boost::format( "%i" ) % key );
	}

	IECore::InternedString curveName = curveAt( line );
	if( curveName.string().size() )
	{
		return curveName.string();
	}

	return "";
}

void DeepSampleGadget::frame()
{
	Box3f b;

	for( auto const &imageData : m_deepSampleDictsAccumulated->readable() )
	{
		const CompoundData *image = IECore::runTimeCast< CompoundData >( imageData.second.get() );

		float minZ = image->member<FloatVectorData>( "Z" )->readable()[0];
		float maxZ = image->member<FloatVectorData>( "ZBack" )->readable().back();

		float channelMax = 0;
		for( auto const &channelData : image->readable() )
		{
			if( channelData.first == "Z" || channelData.first == "ZBack" )
			{
				continue;
			}
			channelMax = std::max( channelMax,
				IECore::runTimeCast< FloatVectorData >( channelData.second.get() )->readable().back()
			);
		}
		b.extendBy( Box3f( V3f( minZ, axisMapping( 0 ), 0 ), V3f( maxZ, axisMapping( channelMax ), 0 ) ) );
	}

	if( b.isEmpty() )
	{
		b = Box3f( V3f( 0, 0, 0), V3f( 1, 1, 0 ) );
	}

	V3f pad = V3f( std::max( 0.1, b.size()[0] * 0.1 ), std::max( 0.1, b.size()[1] * 0.1 ), 0 );
	Box3f bound( b.min - pad, b.max + pad );

	ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	viewportGadget->frame( bound );
}

bool DeepSampleGadget::keyPress( GadgetPtr gadget, const KeyEvent &event )
{
	if( event.key == "F" )
	{
		frame();
		return true;
	}

	return false;
}

bool DeepSampleGadget::onTimeAxis( int y ) const
{
	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	Imath::V2i resolution = viewportGadget->getViewport();

	return y >= resolution.y - m_yMargin;
}

bool DeepSampleGadget::onValueAxis( int x ) const
{
	return x <= m_xMargin;
}


int DeepSampleGadget::keyAt( const LineSegment3f &position ) const
{
	return -1;
	/*
	std::vector<IECoreGL::HitRecord> selection;
	std::vector<Animation::ConstKeyPtr> keys;

	{
		ViewportGadget::SelectionScope selectionScope( position, this, selection, IECoreGL::Selector::IDRender );
		IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector();
		const Style *style = this->style();
		style->bind();
		GLuint name = 1; // Name 0 is invalid, so we start at 1

		const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
		ViewportGadget::RasterScope rasterScope( viewportGadget );

		for( const auto &member : *m_editablePlugs )
		{
			const Animation::CurvePlug *curvePlug = IECore::runTimeCast<const Animation::CurvePlug>( &member );

			for( const Animation::Key &key : *curvePlug )
			{
				keys.emplace_back( &key );
				selector->loadName( name++ );
				V2f keyPosition = viewportGadget->worldToRasterSpace( V3f( key.getTime(), key.getValue(), 0 ) );
				style->renderAnimationKey( keyPosition, Style::NormalState, 4.0 ); // slightly bigger for easier selection
			}
		}
	}

	if( selection.empty() )
	{
		return nullptr;
	}

	return keys[selection[0].name-1];
	*/
}

IECore::InternedString DeepSampleGadget::curveAt( const LineSegment3f &position ) const
{
	/*std::vector<IECoreGL::HitRecord> selection;
	std::vector<Animation::ConstCurvePlugPtr> curves;

	{
		ViewportGadget::SelectionScope selectionScope( position, this, selection, IECoreGL::Selector::IDRender );
		IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector();
		const Style *style = this->style();
		style->bind();
		GLuint name = 1; // Name 0 is invalid, so we start at 1

		for( const auto &runtimeTyped : *m_visiblePlugs )
		{
			const Animation::CurvePlug *curvePlug = IECore::runTimeCast<const Animation::CurvePlug>( &runtimeTyped );
			curves.emplace_back( curvePlug );
			selector->loadName( name++ );
			renderCurve( curvePlug, style );
		}
	}

	if( selection.empty() )
	{
		return nullptr;
	}

	return curves[selection[0].name-1];*/
	return "";
}



/*void DeepSampleGadget::renderCurve( const Animation::CurvePlug *curvePlug, const Style *style ) const
{
	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	ViewportGadget::RasterScope rasterScope( viewportGadget );

	Animation::ConstKeyPtr previousKey = nullptr;
	V2f previousKeyPosition = V2f( 0 );

	bool isHighlighted = curvePlug == m_highlightedCurve;

	for( const auto &key : *curvePlug )
	{
		V2f keyPosition = viewportGadget->worldToRasterSpace( V3f( key.getTime(), key.getValue(), 0 ) );

		if( previousKey )
		{
			// \todo: needs tangent computation/hand-off as soon as we support more interpolation modes
			//        consider passing interpolation into renderCurveSegment to handle all drawing there

			const Imath::Color3f color3 = colorFromName( drivenPlugName( curvePlug ) );

			if( key.getType() == Gaffer::Animation::Linear )
			{
				style->renderAnimationCurve( previousKeyPosition, keyPosition, /inTangent/   V2f( 0 ), /outTangent/   V2f( 0 ), isHighlighted ? Style::HighlightedState : Style::NormalState, &color3 );
			}
			else if( key.getType() == Gaffer::Animation::Step )
			{
				const Color4f color4( color3[0], color3[1], color3[2], 1.0f );
				// \todo: replace with linear curve segment to get highlighting
				style->renderLine( IECore::LineSegment3f( V3f( previousKeyPosition.x, previousKeyPosition.y, 0 ), V3f( keyPosition.x, previousKeyPosition.y, 0) ), 0.5, &color4 );
				style->renderLine( IECore::LineSegment3f( V3f( keyPosition.x, previousKeyPosition.y, 0 ), V3f( keyPosition.x, keyPosition.y, 0 ) ), 0.5, &color4 );
			}
		}

		previousKey = &key;
		previousKeyPosition = keyPosition;
	}
}
*/

void DeepSampleGadget::computeGrid( const ViewportGadget *viewportGadget, AxisDefinition &x, AxisDefinition &y ) const
{
	Imath::V2i resolution = viewportGadget->getViewport();

	Imath::V2f targetSize( 160, 100 );

	LineSegment3f min, max;
	min = viewportGadget->rasterToWorldSpace( V2f( 0, resolution.y ) );
	max = viewportGadget->rasterToWorldSpace( V2f( resolution.x, 0 ) );
	Imath::Box2f viewportBounds = Box2f( V2f( min.p0.x, std::max( -10.0f, reverseAxisMapping( min.p0.y ) ) ), V2f( max.p0.x, std::min( 10.0f, reverseAxisMapping( max.p0.y ) ) ) );

	if( m_logarithmic && viewportBounds.min.y < 0 )
	{
		viewportBounds.min.y = 0;
	}

	V2i labelMinSize( 50, 20 );
	float xStride = 1;
	float yStride = 1;

	// TODO the box's size() is unreliable because it considers the box empty for the inverted coords we seem to have here
	/*V2f pxPerUnit = V2f(
		resolution.x / std::abs( viewportBounds.min.x - viewportBounds.max.x ),
		resolution.y / std::abs( viewportBounds.min.y - viewportBounds.max.y ) );
	*/

	V2f lowerLeft = viewportGadget->worldToRasterSpace( V3f( viewportBounds.min.x, axisMapping( viewportBounds.min.y ), 0 ) );
	V3f targetOffset = viewportGadget->rasterToWorldSpace( lowerLeft + targetSize ).p0;
	targetOffset.y = reverseAxisMapping( targetOffset.y );

	xStride = std::max( 0.00001, exp10( round( log10( fabs( targetOffset.x - viewportBounds.min.x ) ) ) ) );
	yStride = std::min( 0.1, std::max( 0.00001, exp10( round( log10( fabs( targetOffset.y - viewportBounds.min.y ) ) ) ) ) );

	// Compute line locations based on bounds and strides in both dimensions.
	float lowerBoundX = std::floor( viewportBounds.min.x / xStride ) * xStride - xStride;
	float upperBoundX = viewportBounds.max.x;
	for( int i = 0; lowerBoundX + xStride * i < upperBoundX; i++ )
	{
		float time = lowerBoundX + xStride * i;
		x.main.push_back( std::make_pair( viewportGadget->worldToRasterSpace( V3f( time, 0, 0 ) ).x, time ) );

		float subStride = xStride / 5.0;
		for( int s = 1; s < 5; ++s )
		{
			x.secondary.push_back( viewportGadget->worldToRasterSpace( V3f( time + s * subStride, 0, 0 ) ).x );
		}
	}

	float lowerBoundY = std::floor( viewportBounds.min.y / yStride ) * yStride - yStride;
	if( m_logarithmic && lowerBoundY < 0.0f )
	{
		lowerBoundY = 0.0f;
	}
	float upperBoundY = viewportBounds.max.y;
	float prevRasterPos = viewportGadget->worldToRasterSpace( V3f( 0, axisMapping( lowerBoundY ), 0 ) ).y;
	for( float j = lowerBoundY; j < upperBoundY; j += yStride )
	{
		float rasterPos = viewportGadget->worldToRasterSpace( V3f( 0, axisMapping( j ), 0 ) ).y;
		y.main.push_back( std::make_pair( viewportGadget->worldToRasterSpace( V3f( 0, axisMapping( j ), 0 ) ).y, j ) );

		if( fabs( rasterPos - prevRasterPos ) > targetSize.y && yStride > 0.00001 )
		{
			yStride *= 0.1;
		}
		prevRasterPos = rasterPos;
	}
}
