//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Matti Gruner. All rights reserved.
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

#include "GafferUI/AnimationGadget.h"

#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "Gaffer/Animation.h"
#include "Gaffer/Context.h"
#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/UndoScope.h"
#include "Gaffer/Private/ScopedValue.h"

#include "IECoreGL/Selector.h"

#include "IECore/InternedString.h"
#include "IECore/NullObject.h"

#include "boost/algorithm/string.hpp"
#include "boost/bind.hpp"

#include <cmath>

using namespace Gaffer;
using namespace GafferUI;
using namespace Imath;

namespace
{
void tieModeToBools( const Animation::Tangent::TieMode mode, bool& tieSlope, bool& tieAccel )
{
	tieSlope = false;
	tieAccel = false;
	switch( mode )
	{
		case Animation::Tangent::TieMode::Manual:
			break;
		case Animation::Tangent::TieMode::Slope:
			tieSlope = true;
			break;
		case Animation::Tangent::TieMode::SlopeAndAccel:
			tieSlope = true;
			tieAccel = true;
			break;
		default:
			break;
	}
}

/// Aliases that define the intended use of each
/// Gadget::Layer by the AnimationGadget components.
namespace AnimationLayer
{
	constexpr Gadget::Layer Grid = Gadget::Layer::Back;
	constexpr Gadget::Layer Curves = Gadget::Layer::MidBack;
	constexpr Gadget::Layer Keys = Gadget::Layer::Main;
	constexpr Gadget::Layer Axes = Gadget::Layer::MidFront;
	constexpr Gadget::Layer Overlay = Gadget::Layer::Front;
};

template<typename T>
T frameToTime( float fps, T frame )
{
	return frame / fps;
}

template<typename T>
T timeToFrame( float fps, T time )
{
	return time * fps;
}

// \todo: Consider making the colorForAxes function in StandardStyle public?
//        Include names for plugs representing color? (foo.r, foo.g, foo.b)
Color3f colorFromName( std::string name )
{
	if( boost::ends_with( name, ".x" ) )
	{
		return Imath::Color3f( 0.73, 0.17, 0.17 );
	}
	else if( boost::ends_with( name, ".y" ) )
	{
		return Imath::Color3f( 0.2, 0.57, 0.2 );
	}
	else if( boost::ends_with( name, ".z" ) )
	{
		return Imath::Color3f( 0.2, 0.36, 0.74 );
	}
	else
	{
		return Color3f( 1 );
	}
}

// Compute grid line locations. Note that positions are given in raster space so
// that lines can get drawn directly.
// For the time-dimension we limit the computed locations to multiples of one
// frame plus one level of unlabeled dividing lines. Resulting at a minimum
// distance between lines of a fifth of a frame when zoomed in all the way.
// For the value dimension we allow sub-steps as small as 0.001.
struct AxisDefinition
{
	std::vector<std::pair<float, float> > main;
	std::vector<float> secondary;
};

void computeGrid( const ViewportGadget *viewportGadget, float fps, AxisDefinition &x, AxisDefinition &y )
{
	Imath::V2i resolution = viewportGadget->getViewport();

	IECore::LineSegment3f min, max;
	min = viewportGadget->rasterToWorldSpace( V2f( 0 ) );
	max = viewportGadget->rasterToWorldSpace( V2f( resolution.x, resolution.y ) );
	Imath::Box2f viewportBounds = Box2f( V2f( min.p0.x, min.p0.y ), V2f( max.p0.x, max.p0.y ) );

	Box2f viewportBoundsFrames( timeToFrame( fps, viewportBounds.min ), timeToFrame( fps, viewportBounds.max ) );
	V2i labelMinSize( 50, 20 );
	int xStride = 1;
	float yStride = 1;

	// \todo the box's size() is unrealiable because it considers the box empty for the inverted coords we seem to have here
	V2f pxPerUnit = V2f(
		resolution.x / std::abs( viewportBoundsFrames.min.x - viewportBoundsFrames.max.x ),
		resolution.y / std::abs( viewportBounds.min.y - viewportBounds.max.y ) );

	// Compute the stride to use for the time dimension.
	if( pxPerUnit.x < labelMinSize.x )
	{
		xStride = 5;
		pxPerUnit.x *= 5;

		// If there's not enough space for this zoom level, try using every 10th frame.
		while( pxPerUnit.x < labelMinSize.x && pxPerUnit.x != 0 )
		{
			xStride *= 10;
			pxPerUnit.x *= 10;
		}
	}

	// Compute the stride to use for the value dimension.
	if( pxPerUnit.y < labelMinSize.y )
	{
		yStride = 5;
		pxPerUnit.y *= 5;

		// If there's not enough space for this zoom level, increase the spacing
		// between values to be drawn.
		while( pxPerUnit.y < labelMinSize.y && pxPerUnit.y != 0 )
		{
			yStride *= 10;
			pxPerUnit.y *= 10;
		}
	}
	else
	{
		// If we actually have too much space between values, progressively
		// decrease the stride to show smaller value deltas.
		float scale = 1;
		while( pxPerUnit.y / 10.0 > labelMinSize.y && scale > 0.001 )
		{
			yStride *= 0.1;
			pxPerUnit /= 10.0;
			scale /= 10.0;
		}
	}

	// Compute line locations based on bounds and strides in both dimensions.
	int lowerBoundX = std::floor( viewportBoundsFrames.min.x / xStride ) * xStride - xStride;
	int upperBoundX = std::ceil( viewportBoundsFrames.max.x );
	for( int i = lowerBoundX; i < upperBoundX; i += xStride )
	{
		float time = frameToTime( fps, static_cast<float>( i ) );
		x.main.push_back( std::make_pair( viewportGadget->worldToRasterSpace( V3f( time, 0, 0 ) ).x, i ) );

		float subStride = frameToTime( fps, xStride / 5.0 );
		for( int s = 1; s < 5; ++s )
		{
			x.secondary.push_back( viewportGadget->worldToRasterSpace( V3f( time + s * subStride, 0, 0 ) ).x );
		}
	}

	float lowerBoundY = std::floor( viewportBounds.max.y / yStride ) * yStride - yStride;
	float upperBoundY = viewportBounds.min.y + yStride;
	for( float j = lowerBoundY; j < upperBoundY; j += yStride )
	{
			y.main.push_back( std::make_pair( viewportGadget->worldToRasterSpace( V3f( 0, j, 0 ) ).y, j ) );
	}
}

std::string drivenPlugName( const Animation::CurvePlug *curvePlug )
{
	const FloatPlug *out = curvePlug->outPlug();

	auto outputs = out->outputs();
	if( outputs.empty() )
	{
		return "";
	}

	const ScriptNode *scriptNode = out->ancestor<ScriptNode>();
	if( !scriptNode )
	{
		return "";
	}

	// Assuming that we only drive a single plug with this curve
	return outputs.front()->relativeName( scriptNode );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// AnimationGadget implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( AnimationGadget );

AnimationGadget::AnimationGadget()
	: m_context( nullptr )
	, m_visiblePlugs( new StandardSet() )
	, m_editablePlugs( new StandardSet() )
	, m_editablePlugsConnections()
	, m_selectedKeys()
	, m_selectedKeysChangedSignal()
	, m_originalKeyValues()
	, m_dragTangent( nullptr, Animation::Tangent::Direction::Into )
	, m_dragTangentOriginalSlope( 0.0 )
	, m_dragTangentOriginalAccel( 0.0 )
	, m_dragStartPosition( 0 )
	, m_lastDragPosition( 0 )
	, m_dragMode( DragMode::None )
	, m_moveAxis( MoveAxis::Both )
	, m_snappingClosestKey( nullptr )
	, m_highlightedKey( nullptr )
	, m_highlightedCurve( nullptr )
	, m_highlightedTangent( nullptr, Animation::Tangent::Direction::Into )
	, m_overwrittenKeys()
	, m_mergeGroupId( 0 )
	, m_keyPreview( false )
	, m_keyPreviewLocation( 0 )
	, m_xMargin( 60 )
	, m_yMargin( 20 )
	, m_textScale( 10 )
	, m_labelPadding( 5 )
	, m_frameIndicatorPreviewFrame( boost::none )
{
	buttonPressSignal().connect( boost::bind( &AnimationGadget::buttonPress, this, ::_1,  ::_2 ) );
	buttonReleaseSignal().connect( boost::bind( &AnimationGadget::buttonRelease, this, ::_1,  ::_2 ) );

	keyPressSignal().connect( boost::bind( &AnimationGadget::keyPress, this, ::_1,  ::_2 ) );
	keyReleaseSignal().connect( boost::bind( &AnimationGadget::keyRelease, this, ::_1,  ::_2 ) );

	mouseMoveSignal().connect( boost::bind( &AnimationGadget::mouseMove, this, ::_1, ::_2 ) );
	dragBeginSignal().connect( boost::bind( &AnimationGadget::dragBegin, this, ::_1, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &AnimationGadget::dragEnter, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &AnimationGadget::dragMove, this, ::_1, ::_2 ) );
	dragEndSignal().connect( boost::bind( &AnimationGadget::dragEnd, this, ::_1, ::_2 ) );
	leaveSignal().connect( boost::bind( &AnimationGadget::leave, this ) );

	m_editablePlugs->memberAcceptanceSignal().connect( boost::bind( &AnimationGadget::plugSetAcceptor, this, ::_1, ::_2 ) );
	m_editablePlugs->memberAddedSignal().connect( boost::bind( &AnimationGadget::editablePlugAdded, this, ::_1, ::_2 ) );
	m_editablePlugs->memberRemovedSignal().connect( boost::bind( &AnimationGadget::editablePlugRemoved, this, ::_1, ::_2 ) );

	m_visiblePlugs->memberAcceptanceSignal().connect( boost::bind( &AnimationGadget::plugSetAcceptor, this, ::_1, ::_2 ) );
	m_visiblePlugs->memberAddedSignal().connect( boost::bind( &AnimationGadget::visiblePlugAdded, this, ::_1, ::_2 ) );
	m_visiblePlugs->memberRemovedSignal().connect( boost::bind( &AnimationGadget::visiblePlugRemoved, this, ::_1, ::_2 ) );
}

AnimationGadget::~AnimationGadget()
{
	// disconnect any remaining connections to editable plugs

	for( CurvePlugConnectionMap::iterator it = m_editablePlugsConnections.begin(), itEnd = m_editablePlugsConnections.end(); it != itEnd; ++it )
	{
		( *it ).second.disconnect();
	}
}

bool AnimationGadget::onTimeAxis( const Imath::V2i& rasterPosition ) const
{
	return onTimeAxis( rasterPosition.y );
}

bool AnimationGadget::onValueAxis( const Imath::V2i& rasterPosition ) const
{
	return onValueAxis( rasterPosition.x );
}

bool AnimationGadget::isSelectedKey( const Animation::KeyPtr& key ) const
{
	return m_selectedKeys.count( key ) > static_cast< SelectedKeys::size_type >( 0 );
}

AnimationGadget::SelectedKeyIterator AnimationGadget::selectedKeysBegin()
{
	return AnimationGadget::SelectedKeyIterator( m_selectedKeys.begin() );
}

AnimationGadget::SelectedKeyIterator AnimationGadget::selectedKeysEnd()
{
	return AnimationGadget::SelectedKeyIterator( m_selectedKeys.end() );
}

AnimationGadget::ConstSelectedKeyIterator AnimationGadget::selectedKeysBegin() const
{
	return AnimationGadget::ConstSelectedKeyIterator( m_selectedKeys.begin() );
}

AnimationGadget::ConstSelectedKeyIterator AnimationGadget::selectedKeysEnd() const
{
	return AnimationGadget::ConstSelectedKeyIterator( m_selectedKeys.end() );
}

AnimationGadget::AnimationGadgetSignal& AnimationGadget::selectedKeysChangedSignal()
{
	return m_selectedKeysChangedSignal;
}

void AnimationGadget::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	glDisable( GL_DEPTH_TEST );

	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	Imath::V2i resolution = viewportGadget->getViewport();

	ViewportGadget::RasterScope rasterScope( viewportGadget );

	switch ( layer )
	{

	case AnimationLayer::Grid :
	{
		AxisDefinition xAxis, yAxis;
		computeGrid( viewportGadget, m_context->getFramesPerSecond(), xAxis, yAxis );

		Imath::Color4f axesColor( 60.0 / 255, 60.0 / 255, 60.0 / 255, 1.0f );

		// drawing base grid
		for( const auto &x : xAxis.main )
		{
			style->renderLine( IECore::LineSegment3f( V3f( x.first, 0, 0 ), V3f( x.first, resolution.y, 0 ) ), x.second == 0.0f ? 3.0 : 2.0, &axesColor );
		}

		for( const auto &y : yAxis.main )
		{
			style->renderLine( IECore::LineSegment3f( V3f( 0, y.first, 0 ), V3f( resolution.x, y.first, 0 ) ), y.second == 0.0f ? 3.0 : 2.0, &axesColor );
		}

		// drawing sub grid for frames
		for( float x : xAxis.secondary )
		{
			style->renderLine( IECore::LineSegment3f( V3f( x, 0, 0 ), V3f( x, resolution.y, 0 ) ), 1.0, &axesColor );
		}

		break;
	}

	case AnimationLayer::Curves :
	{
		for( const auto &member : *m_visiblePlugs )
		{
			const Animation::CurvePlug *curvePlug = IECore::runTimeCast<const Animation::CurvePlug>( &member );
			renderCurve( curvePlug, style );
		}

		break;
	}

	case AnimationLayer::Keys :
	{
		Imath::Color3f black( 0, 0, 0 );

		bool selecting = m_dragMode == DragMode::Selecting;
		Box2f b;
		if( selecting )
		{
			b.extendBy( V2f( m_dragStartPosition.x, m_dragStartPosition.y ) );
			b.extendBy( V2f( m_lastDragPosition.x, m_lastDragPosition.y ) );
		}

		for( auto &runtimeTyped : *m_editablePlugs )
		{
			Animation::CurvePlug *curvePlug = IECore::runTimeCast<Animation::CurvePlug>( &runtimeTyped );

			const Imath::Color3f color3 = colorFromName( drivenPlugName( curvePlug ) );
			const Imath::Color4f color4( color3.x, color3.y, color3.z, 1.0 );

			Animation::Key* previousKey = 0;
			V2f previousKeyPosition = V2f( 0 );
			bool previousKeySelected = false;
			for( Animation::Key &key : *curvePlug )
			{
				bool isHighlighted = ( m_highlightedKey && key == *m_highlightedKey ) || ( selecting && b.intersects( V2f( key.getTime().getSeconds(), key.getValue() ) ));
				bool isSelected = m_selectedKeys.count( Animation::KeyPtr( &key ) ) > 0;
				V2f keyPosition = viewportGadget->worldToRasterSpace( V3f( key.getTime().getSeconds(), key.getValue(), 0 ) );
				style->renderAnimationKey( keyPosition, isSelected || isHighlighted ? Style::HighlightedState : Style::NormalState, isHighlighted ? 3.0 : 2.0, &black );

				// draw the tangents
				//
				// NOTE : only draw if they are used by span interpolator and key or adjacent key is selected

				if( previousKey )
				{
					const Animation::Interpolator::Hints hints = previousKey->getInterpolator()->getHints();

					if( ( isSelected || previousKeySelected ) && (
							hints.test( Animation::Interpolator::Hint::UseSlopeLo ) ||
							hints.test( Animation::Interpolator::Hint::UseAccelLo ) ) )
					{
						bool tieSlope, tieAccel;
						tieModeToBools( previousKey->getTieMode(), tieSlope, tieAccel );
						const Animation::Tangent& from = previousKey->getTangent( Animation::Tangent::Direction::From );
						const V2d fromPosKey = from.getPosition( Animation::Tangent::Space::Key, false );
						const V2f fromPosRas = viewportGadget->worldToRasterSpace( V3f( fromPosKey.x, fromPosKey.y, 0 ) );
						const bool isFromHighlighted = ( ( m_highlightedTangent.first == previousKey ) &&  m_highlightedTangent.second == Animation::Tangent::Direction::From );
						const double fromSize = isFromHighlighted ? 4.0 : 2.0;
						const Box2f fromBox( fromPosRas - V2f( fromSize ), fromPosRas + V2f( fromSize ) );
						style->renderLine( IECore::LineSegment3f( V3f( fromPosRas.x, fromPosRas.y, 0 ), V3f( previousKeyPosition.x, previousKeyPosition.y, 0 ) ),
							tieSlope ? 2.0 : 1.0, &color4 );
						( tieAccel ) ? style->renderSolidRectangle( fromBox ) : style->renderRectangle( fromBox );
					}

					if( ( isSelected || previousKeySelected ) && (
						hints.test( Animation::Interpolator::Hint::UseSlopeHi ) ||
						hints.test( Animation::Interpolator::Hint::UseAccelHi ) ) )
					{
						bool tieSlope, tieAccel;
						tieModeToBools( key.getTieMode(), tieSlope, tieAccel );
						const Animation::Tangent& into = key.getTangent( Animation::Tangent::Direction::Into );
						const V2d intoPosKey = into.getPosition( Animation::Tangent::Space::Key, false );
						const V2f intoPosRas = viewportGadget->worldToRasterSpace( V3f( intoPosKey.x, intoPosKey.y, 0 ) );
						const bool isIntoHighlighted = ( ( m_highlightedTangent.first == &key ) &&  m_highlightedTangent.second == Animation::Tangent::Direction::Into );
						const double intoSize = isIntoHighlighted ? 4.0 : 2.0;
						const Box2f intoBox( intoPosRas - V2f( intoSize ), intoPosRas + V2f( intoSize ) );
						style->renderLine( IECore::LineSegment3f( V3f( intoPosRas.x, intoPosRas.y, 0 ), V3f( keyPosition.x, keyPosition.y, 0 ) ),
							tieSlope ? 2.0 : 1.0, &color4 );
						( tieAccel ) ? style->renderSolidRectangle( intoBox ) : style->renderRectangle( intoBox );
					}
				}

				previousKey = & key;
				previousKeyPosition = keyPosition;
				previousKeySelected = isSelected;
			}
		}
		break;
	}

	case AnimationLayer::Axes :
	{
		AxisDefinition xAxis, yAxis;
		computeGrid( viewportGadget, m_context->getFramesPerSecond(), xAxis, yAxis );

		if( m_frameIndicatorPreviewFrame )
		{
			renderFrameIndicator( m_frameIndicatorPreviewFrame.get(), style, /* preview = */ true );
		}

		renderFrameIndicator( static_cast<int>( m_context->getFrame() ), style );

		// draw axes on top of everything.
		Imath::Color4f axesColor( 60.0 / 255, 60.0 / 255, 60.0 / 255, 1.0 );
		IECoreGL::glColor( axesColor ); // \todo: maybe renderSolidRectangle() should accept a userColor
		style->renderSolidRectangle( Box2f( V2f( 0 ) , V2f( m_xMargin, resolution.y - m_yMargin ) ) );
		style->renderSolidRectangle( Box2f( V2f( 0, resolution.y - m_yMargin ) , V2f( resolution.x, resolution.y ) ) );

		boost::format formatX( "%.2f" );
		boost::format formatY( "%.3f" );

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

	case AnimationLayer::Overlay :
	{
		if( m_dragMode == DragMode::Selecting )
		{
			Box2f b;
			b.extendBy( viewportGadget->gadgetToRasterSpace( V3f( m_dragStartPosition.x, m_dragStartPosition.y, 0 ), this ) );
			b.extendBy( viewportGadget->gadgetToRasterSpace( V3f( m_lastDragPosition.x, m_lastDragPosition.y, 0 ), this ) );
			style->renderSelectionBox( b );
		}

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

unsigned AnimationGadget::layerMask() const
{
	return
		AnimationLayer::Grid |
		AnimationLayer::Curves |
		AnimationLayer::Keys |
		AnimationLayer::Axes |
		AnimationLayer::Overlay;
}

Imath::Box3f AnimationGadget::renderBound() const
{
	// We render an infinite grid
	Box3f b;
	b.makeInfinite();
	return b;
}

Gaffer::StandardSet *AnimationGadget::visiblePlugs()
{
	return m_visiblePlugs.get();
}

const Gaffer::StandardSet *AnimationGadget::visiblePlugs() const
{
	return m_visiblePlugs.get();
}

Gaffer::StandardSet *AnimationGadget::editablePlugs()
{
	return m_editablePlugs.get();
}

const Gaffer::StandardSet *AnimationGadget::editablePlugs() const
{
	return m_editablePlugs.get();
}

void AnimationGadget::plugDirtied( Gaffer::Plug *plug )
{
	dirty( DirtyType::Render );
}

std::string AnimationGadget::getToolTip( const IECore::LineSegment3f &line ) const
{
	std::pair< Gaffer::Animation::ConstKeyPtr, Gaffer::Animation::Tangent::Direction > keyTangent = tangentAt( line );
	if( keyTangent.first )
	{
		const Gaffer::Animation::Tangent& tangent = keyTangent.first->getTangent( keyTangent.second );
		std::ostringstream os;
		os.precision( std::min( 4, std::numeric_limits< double >::max_digits10 ) );
		os << "Direction: ";
		switch( tangent.getDirection() )
		{
			case Gaffer::Animation::Tangent::Direction::Into:
				os << "Into";
				break;
			case Gaffer::Animation::Tangent::Direction::From:
				os << "From";
				break;
			default:
				os << "Unknown";
		}
		os << "<br>Slope: " << tangent.getSlope( Gaffer::Animation::Tangent::Space::Key );
		os << "<br>Accel: " << tangent.getAccel( Gaffer::Animation::Tangent::Space::Span );
		return os.str();
	}
	else if( const Animation::ConstKeyPtr key = keyAt( line ) )
	{
		const Gaffer::ScriptNode* const scriptNode =
			IECore::assertedStaticCast< const Gaffer::ScriptNode >( key->parent()->ancestor( (IECore::TypeId) Gaffer::ScriptNodeTypeId ) );

		std::ostringstream os;
		os.precision( std::min( 4, std::numeric_limits< double >::max_digits10 ) );
		os.setf( std::ios::boolalpha );
		os << "Frame: " << key->getTime().getReal( scriptNode->framesPerSecondPlug()->getValue() );
		os << "<br>Value: " << key->getValue();
		os << "<br>Interpolator: " << key->getInterpolator()->getName();
		os << "<br>Tie Mode: " << Animation::toString( key->getTieMode() );
		return os.str();
	}
	else if( Animation::ConstCurvePlugPtr curvePlug = curveAt( line ) )
	{
		return drivenPlugName( curvePlug.get() );
	}

	return "";
}

void AnimationGadget::insertKeyframe( Animation::CurvePlug *curvePlug, float time )
{
	ScriptNode *scriptNode = curvePlug->ancestor<ScriptNode>();
	UndoScope undoEnabled( scriptNode, UndoScope::Enabled, undoMergeGroup() );

	Animation::Time snappedTime( time, Animation::Time::Units::Seconds );
	snappedTime.snap( m_context->getFramesPerSecond() );

	if( !curvePlug->closestKey( snappedTime, 0.004 ) ) // \todo: use proper ticks
	{
		curvePlug->insertKey( snappedTime );
	}
}

void AnimationGadget::insertKeyframes()
{
	if( m_editablePlugs->size() == 0 )
	{
		return;
	}

	for( auto &runtimeTyped : *m_editablePlugs )
	{
		insertKeyframe( IECore::runTimeCast<Animation::CurvePlug>( &runtimeTyped ), m_context->getTime() );
	}
}

void AnimationGadget::removeKeyframes()
{
	if( m_selectedKeys.empty() )
	{
		return;
	}

	auto first = m_editablePlugs->member( 0 );
	ScriptNode *scriptNode = IECore::runTimeCast<Animation::CurvePlug>( first )->ancestor<ScriptNode>();
	UndoScope undoEnabled( scriptNode, UndoScope::Enabled, undoMergeGroup() );

	// NOTE : all selected keys should be parented by curves in the editable plugs set we have connected
	//        to the keyRemoved signal of the parent curves, we do not want to remove the keys from the
	//        selected keys in keyRemoved as that would invalidate our iterators and would result in a
	//        flurry of selectedKeysChanged signal calls so set flag to disable keyRemoved.

	{
		Private::ScopedValue< DragMode > guard( m_dragMode, DragMode::Moving );

		for( const auto &keyPtr : m_selectedKeys )
		{
			Animation::CurvePlug *parent = keyPtr->parent();
			if( parent )
			{
				assert( m_editablePlugs->contains( parent ) );
				parent->removeKey( keyPtr );
			}
		}
	}

	m_selectedKeys.clear();
	m_selectedKeysChangedSignal( this );
}

void AnimationGadget::moveKeyframes( const V2f currentDragPosition )
{
	if( m_selectedKeys.empty() )
	{
		return;
	}

	auto first = m_editablePlugs->member( 0 );
	ScriptNode *scriptNode = IECore::runTimeCast<Animation::CurvePlug>( first )->ancestor<ScriptNode>();
	UndoScope undoEnabled( scriptNode, UndoScope::Enabled, undoMergeGroup() );

	const float valueOffset = currentDragPosition.y - m_dragStartPosition.y;
	Animation::Time timeOffset( currentDragPosition.x - m_dragStartPosition.x, Animation::Time::Units::Seconds );

	// Compute snapping offset used for all keys
	if( m_moveAxis != MoveAxis::Y )
	{
		// Update offset to make sure that the closest key ends up on an integer frame
		const Animation::Time originalTime = m_originalKeyValues[m_snappingClosestKey.get()].first;
		timeOffset += originalTime;
		timeOffset.snap( m_context->getFramesPerSecond() );
		timeOffset -= originalTime;
	}

	// copy selected keys to move list
	std::list< Animation::Key* > moveList;
	for( SelectedKeys::iterator it = m_selectedKeys.begin(), itEnd = m_selectedKeys.end(); it != itEnd; ++it )
	{
		moveList.push_back( ( *it ).get() );
	}

	while( ! moveList.empty() )
	{
		Animation::Key *key = moveList.front();
		moveList.pop_front();

		if( m_moveAxis != MoveAxis::X )
		{
			key->setValue( m_originalKeyValues[key].second + valueOffset );
		}

		// Compute new time and make sure that we eliminate floating point precision
		// issues that could cause keys landing a little bit off integer frames for
		// keys that are meant to snap to frames.
		Animation::Time newTime = m_originalKeyValues[key].first + timeOffset;
		newTime.snap( m_context->getFramesPerSecond() );

		if( m_moveAxis != MoveAxis::Y && newTime != key->getTime() )
		{
			assert( key->parent() || m_overwrittenKeys.count( key ) );
			Animation::CurvePlug* const curvePlug = ( key->parent() )
				? key->parent()
				: ( *( m_overwrittenKeys.find( key ) ) ).second.get();
			assert( curvePlug );

			// If a key already exists on the new frame, we overwrite it, but
			// store it for reinserting should the drag continue and the frame
			// free up again.
			Animation::KeyPtr clashingKey = curvePlug->getKey( newTime );
			if( clashingKey && clashingKey != key )
			{
				m_overwrittenKeys[ clashingKey ] = clashingKey->parent();
				clashingKey->parent()->removeKey( clashingKey );

				// if clashing key is selected then add it to the back of move list
				if( m_selectedKeys.count( clashingKey ) )
				{
					moveList.push_back( clashingKey.get() );
				}
			}

			// set the new time for the key
			key->setTime( newTime );

			// ensure the key is added to its curve
			if( ! key->parent() )
			{
				assert( ! curvePlug->getKey( newTime ) );
				curvePlug->addKey( key );
				m_overwrittenKeys.erase( key );
			}
		}
	}

	// Check if any of the previously overwritten (unselected) keys can be inserted back into the curve
	for( OverwrittenKeys::iterator it = m_overwrittenKeys.begin(); it != m_overwrittenKeys.end(); )
	{
		if( it->second->getKey( ( *it ).first->getTime() ) )
		{
			assert( ! m_selectedKeys.count( ( *it ).first ) );
			++it;
		}
		else
		{
			it->second->addKey( ( *it ).first );
			it = m_overwrittenKeys.erase( it );
		}
	}
}

void AnimationGadget::moveTangent( const Imath::V2f currentDragOffset )
{
	if( !( m_dragTangent.first ) || ( m_moveAxis == MoveAxis::Undefined ) )
	{
		return;
	}

	Animation::Tangent& tangent = m_dragTangent.first->getTangent( m_dragTangent.second );

	// NOTE : get interpolator that affects tangent

	Animation::Key* const key =
		( tangent.getDirection() == Animation::Tangent::Direction::From )
			? ( m_dragTangent.first.get() )
			: ( m_dragTangent.first->prevKey() );

	if( ! key )
	{
		return;
	}

	// NOTE : check interpolator usage hints

	const Animation::Interpolator::Hints hints = key->getInterpolator()->getHints();

	MoveAxis axis = m_moveAxis;

	if( ( axis == MoveAxis::X ) && (
		( ( tangent.getDirection() == Animation::Tangent::Direction::From ) &&
			! hints.test( Animation::Interpolator::Hint::UseAccelLo ) ) ||
		( ( tangent.getDirection() == Animation::Tangent::Direction::Into ) &&
			! hints.test( Animation::Interpolator::Hint::UseAccelHi ) ) ) )
	{
		return;
	}
	else if( ( axis == MoveAxis::Y ) && (
		( ( tangent.getDirection() == Animation::Tangent::Direction::From ) &&
			! hints.test( Animation::Interpolator::Hint::UseSlopeLo ) ) ||
		( ( tangent.getDirection() == Animation::Tangent::Direction::Into ) &&
			! hints.test( Animation::Interpolator::Hint::UseSlopeHi ) ) ) )
	{
		return;
	}
	else if( ( axis == MoveAxis::Both ) && (
		( ( tangent.getDirection() == Animation::Tangent::Direction::From ) && (
			! hints.test( Animation::Interpolator::Hint::UseSlopeLo ) &&
			! hints.test( Animation::Interpolator::Hint::UseAccelLo ) ) ) ||
		( ( tangent.getDirection() == Animation::Tangent::Direction::Into ) && (
			! hints.test( Animation::Interpolator::Hint::UseSlopeHi ) &&
			! hints.test( Animation::Interpolator::Hint::UseAccelHi ) ) ) ) )
	{
		return;
	}

	// NOTE : create undo scope and move the tangent

	auto first = m_editablePlugs->member( 0 );
	ScriptNode *scriptNode = IECore::runTimeCast<Animation::CurvePlug>( first )->ancestor<ScriptNode>();
	UndoScope undoEnabled( scriptNode, UndoScope::Enabled, undoMergeGroup() );

	switch( m_moveAxis )
	{
		case MoveAxis::X:
			tangent.setPositionWithSlope( currentDragOffset, m_dragTangentOriginalSlope, Animation::Tangent::Space::Key, false );
			break;
		case MoveAxis::Y:
			tangent.setPositionWithAccel( currentDragOffset, m_dragTangentOriginalAccel, Animation::Tangent::Space::Key, false );
			break;
		case MoveAxis::Both:
			if( ( ( tangent.getDirection() == Animation::Tangent::Direction::From ) &&
				! hints.test( Animation::Interpolator::Hint::UseAccelLo ) ) ||
				( ( tangent.getDirection() == Animation::Tangent::Direction::Into ) &&
				! hints.test( Animation::Interpolator::Hint::UseAccelHi ) ) )
			{
				tangent.setPositionWithAccel( currentDragOffset, m_dragTangentOriginalAccel, Animation::Tangent::Space::Key, false );
			}
			else
			if( ( ( tangent.getDirection() == Animation::Tangent::Direction::From ) &&
				! hints.test( Animation::Interpolator::Hint::UseSlopeLo ) ) ||
				( ( tangent.getDirection() == Animation::Tangent::Direction::Into ) &&
				! hints.test( Animation::Interpolator::Hint::UseSlopeHi ) ) )
			{
				tangent.setPositionWithSlope( currentDragOffset, m_dragTangentOriginalSlope, Animation::Tangent::Space::Key, false );
			}
			else
			{
				tangent.setPosition( currentDragOffset, Animation::Tangent::Space::Key, false );
			}
			break;
		case MoveAxis::Undefined:
		default:
			// NOTE : do nothing unless move axis is defined
			break;
	};
}

void AnimationGadget::frame()
{
	Box3f b;

	// trying to frame to selected keys first
	if( !m_selectedKeys.empty() )
	{
		for( const auto &key : m_selectedKeys )
		{
			b.extendBy( V3f( key->getTime().getSeconds(), key->getValue(), 0 ) );
		}
	}
	// trying to frame to editable curves next
	else if( !( m_editablePlugs->size() == 0 ) )
	{
		for( const auto &runtimeTyped : *m_editablePlugs )
		{
			const Animation::CurvePlug *curvePlug = IECore::runTimeCast<const Animation::CurvePlug>( &runtimeTyped );

			for( const auto &key : *curvePlug )
			{
				b.extendBy( V3f( key.getTime().getSeconds(), key.getValue(), 0 ) );
			}
		}
	}
	// trying to frame to visible curves next
	else if( !( m_visiblePlugs->size() == 0 ) )
	{
		for( const auto &runtimeTyped : *m_visiblePlugs )
		{
			const Animation::CurvePlug *curvePlug = IECore::runTimeCast<const Animation::CurvePlug>( &runtimeTyped );

			for( const auto &key : *curvePlug )
			{
				b.extendBy( V3f( key.getTime().getSeconds(), key.getValue(), 0 ) );
			}
		}
	}
	// setting default framing as last resort
	else
	{
		b = Box3f( V3f( -1, -1, 0), V3f( 1, 1, 0 ) );
	}

	// add some padding in case only a single key was selected
	Box3f bound( b.min - V3f( .1 ), b.max + V3f( .1 ) );

	// scale bounding box so there's some space between keys and the axis
	V3f center = bound.center();
	bound.min = center + ( bound.min - center ) * 1.2;
	bound.max = center + ( bound.max - center ) * 1.2;

	ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	// \todo: we might have to compensate for the axis we're drawing
	viewportGadget->frame( bound );

	return;
}

bool AnimationGadget::buttonPress( GadgetPtr gadget, const ButtonEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}

	if( event.button == ButtonEvent::Left && m_frameIndicatorPreviewFrame )
	{
		m_context->setFrame( m_frameIndicatorPreviewFrame.get() );
		m_frameIndicatorPreviewFrame = boost::none;
	}

	return true;
}

bool AnimationGadget::buttonRelease( GadgetPtr gadget, const ButtonEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}

	if( event.button != ButtonEvent::Left )
	{
		return false;
	}

	if( Animation::KeyPtr key = keyAt( event.line ) )
	{
		bool shiftHeld = event.modifiers & DragDropEvent::Shift;

		// replacing selection
		if( !shiftHeld )
		{
			if( ( m_selectedKeys.size() != static_cast< SelectedKeys::size_type >( 1 ) ) ||
				( *( m_selectedKeys.begin() ) != key ) )
			{
				m_selectedKeys.clear();
				m_selectedKeys.insert( key );
				m_selectedKeysChangedSignal( this );
			}
		}
		else
		{
			// toggle selection
			if( m_selectedKeys.count( key ) )
			{
				m_selectedKeys.erase( key );
			}
			else
			{
				m_selectedKeys.insert( key );
			}

			m_selectedKeysChangedSignal( this );
		}
	}
	else if( Animation::CurvePlugPtr curvePlug = curveAt( event.line ) )
	{
		bool controlHeld = event.modifiers & DragDropEvent::Control;

		if( controlHeld ) // insert a keyframe
		{
			insertKeyframe( curvePlug.get(), i.x );
			m_keyPreview = false;
		}
		else
		{
			if( m_editablePlugs->contains( curvePlug.get() ) ) // select all its keys
			{
				const std::size_t count = m_selectedKeys.size();

				for( Animation::Key &key : *curvePlug )
				{
					m_selectedKeys.emplace( &key );
				}

				if( m_selectedKeys.size() != count )
				{
					m_selectedKeysChangedSignal( this );
				}
			}
			else // try to make it editable
			{
				bool shiftHeld = event.modifiers & DragDropEvent::Shift;
				if( !shiftHeld )
				{
					m_editablePlugs->clear();

					if( ! m_selectedKeys.empty() )
					{
						m_selectedKeys.clear();
						m_selectedKeysChangedSignal( this );
					}
				}

				m_editablePlugs->add( curvePlug.get() );
			}
		}
	}
	else // background
	{
		if( ! m_selectedKeys.empty() )
		{
			m_selectedKeys.clear();
			m_selectedKeysChangedSignal( this );
		}
	}

	dirty( DirtyType::Render );

	return true;
}

IECore::RunTimeTypedPtr AnimationGadget::dragBegin( GadgetPtr gadget, const DragDropEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return nullptr;
	}

	ViewportGadget *viewportGadget = ancestor<ViewportGadget>();

	switch ( event.buttons )
	{

	case ButtonEvent::Left :
	{
		Imath::V2f mouseRasterPosition = viewportGadget->worldToRasterSpace( i );

		std::pair<Animation::KeyPtr, Animation::Tangent::Direction> tangent = tangentAt( event.line );

		if( tangent.first )
		{
			Animation::Tangent& t = tangent.first->getTangent( tangent.second );
			m_dragTangentOriginalSlope = t.getSlope( Animation::Tangent::Space::Span );
			m_dragTangentOriginalAccel = t.getAccel( Animation::Tangent::Space::Span );
			m_dragTangent = tangent;
			m_dragMode = DragMode::MoveTangent;
			if(
				( event.modifiers & DragDropEvent::Control ) &&
				( ( event.modifiers & DragDropEvent::Shift ) == DragDropEvent::None ) )
			{
				m_moveAxis = MoveAxis::Y;
			}
			else if(
				( event.modifiers & DragDropEvent::Shift ) &&
				( ( event.modifiers & DragDropEvent::Control ) == DragDropEvent::None ) )
			{
				m_moveAxis = MoveAxis::X;
			}
			else
			{
				m_moveAxis = MoveAxis::Both;
			}
		}
		else if( Animation::KeyPtr key = keyAt( event.line ) )
		{
			// If dragging an unselected Key, the assumption is that only this Key
			// should be moved. On the other hand, if the key was selected, we will
			// move the entire selection.
			if( ! m_selectedKeys.count( key ) )
			{
				m_selectedKeys.clear();
				m_selectedKeys.insert( key );
				m_selectedKeysChangedSignal( this );
			}
			m_dragMode = DragMode::Moving;
		}
		else if( ( onTimeAxis( mouseRasterPosition.y ) && !onValueAxis( mouseRasterPosition.x ) ) || frameIndicatorUnderMouse( event.line ) )
		{
			m_dragMode = DragMode::MoveFrame;
			m_frameIndicatorPreviewFrame = boost::none;
		}
		else // treating everything else as background and start selection
		{
			m_dragMode = DragMode::Selecting;
		}

		break;
	}

	case ButtonEvent::Middle :
	{
		m_dragMode = DragMode::Moving;
		break;
	}

	default:
	{
	}

	}

	bool shiftHeld = event.modifiers & DragDropEvent::Shift;

	// There's different ways to initiate dragging keys, but we need to do some
	// additional work for all of them.
	if( m_dragMode == DragMode::Moving )
	{
		if( shiftHeld )
		{
			m_moveAxis = MoveAxis::Undefined;
		}

		m_snappingClosestKey = nullptr;

		// Store current positions so that updating during drag can be done without many small incremental updates.
		for( SelectedKeys::const_iterator it = m_selectedKeys.begin(), itEnd = m_selectedKeys.end(); it != itEnd; ++it )
		{
			const Animation::Key* const key = ( *it ).get();

			assert( key );
			assert( key->parent() );
			assert( m_editablePlugs->contains( key->parent() ) );

			m_originalKeyValues[ key ] = std::make_pair( key->getTime(), key->getValue() );
		}
	}

	if( m_dragMode == DragMode::Selecting )
	{
		if( !shiftHeld )
		{
			if( ! m_selectedKeys.empty() )
			{
				m_selectedKeys.clear();
				m_selectedKeysChangedSignal( this );
			}
		}
	}

	if( m_dragMode == DragMode::MoveFrame )
	{
		viewportGadget->setDragTracking( ViewportGadget::DragTracking::XDragTracking );
	}

	m_dragStartPosition = m_lastDragPosition = V2f( i.x, i.y );

	dirty( DirtyType::Render );
	return IECore::NullObject::defaultNullObject();
}

bool AnimationGadget::mouseMove( GadgetPtr gadget, const ButtonEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}

	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	Imath::V2f mouseRasterPosition = viewportGadget->worldToRasterSpace( i );

	if( onTimeAxis( mouseRasterPosition.y ) && !onValueAxis( mouseRasterPosition.x ) )
	{
		m_frameIndicatorPreviewFrame = static_cast<int>( round( timeToFrame( m_context->getFramesPerSecond(), i.x ) ) );
	}
	else
	{
		m_frameIndicatorPreviewFrame = boost::none;
	}

	std::pair<Gaffer::Animation::KeyPtr, Gaffer::Animation::Tangent::Direction> tangent = tangentAt( event.line );

	if( tangent.first )
	{
		m_highlightedTangent = tangent;
		m_highlightedKey = nullptr;
		m_highlightedCurve = nullptr;
	}
	else if( Animation::KeyPtr key = keyAt( event.line ) )
	{
		m_highlightedKey = key;
		m_highlightedTangent.first = nullptr;
		m_highlightedCurve = nullptr;
	}
	else
	{
		if( m_highlightedKey )
		{
			m_highlightedKey = nullptr;
		}

		if( m_highlightedTangent.first )
		{
			m_highlightedTangent.first = nullptr;
		}

		if( Animation::CurvePlugPtr curvePlug = curveAt( event.line ) )
		{
			m_highlightedCurve = curvePlug;

			bool controlHeld = event.modifiers & DragDropEvent::Control;
			if( controlHeld )
			{
				m_keyPreview = true;
			}
		}
		else
		{
			if( m_highlightedCurve )
			{
				m_highlightedCurve = nullptr;
				m_keyPreview = false;
			}
		}
	}

	updateKeyPreviewLocation( m_highlightedCurve.get(), i.x );
	dirty( DirtyType::Render );

	return true;
}

bool AnimationGadget::dragEnter( GadgetPtr gadget, const DragDropEvent &event )
{
	if( event.sourceGadget != this )
	{
		return false;
	}

	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}

	m_lastDragPosition = V2f( i.x, i.y );
	dirty( DirtyType::Render );
	return true;
}

bool AnimationGadget::dragMove( GadgetPtr gadget, const DragDropEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}

	if( m_dragMode == DragMode::Moving && !m_selectedKeys.empty() )
	{
		if( m_moveAxis == MoveAxis::Undefined )
		{
			ViewportGadget *viewportGadget = ancestor<ViewportGadget>();

			if( std::abs( i.x - m_dragStartPosition.x ) >= std::abs ( i.y - m_dragStartPosition.y ) )
			{
				m_moveAxis = MoveAxis::X;
				Pointer::setCurrent( "moveHorizontally" );
				viewportGadget->setDragTracking( ViewportGadget::DragTracking::XDragTracking );
			}
			else
			{
				m_moveAxis = MoveAxis::Y;
				Pointer::setCurrent( "moveVertically" );
				viewportGadget->setDragTracking( ViewportGadget::DragTracking::YDragTracking );
			}
		}
	}

	if( m_dragMode == DragMode::Moving && !m_selectedKeys.empty() )
	{
		if( m_moveAxis != MoveAxis::Y && !m_snappingClosestKey )
		{
			// determine position of selected keyframe that is closest to pointer
			// \todo: move into separate function, ideally consolidate with Animation::CurvePlug::closestKey?
			const Animation::Time time( i.x, Animation::Time::Units::Seconds );
			auto rightIt = m_selectedKeys.lower_bound( Animation::KeyPtr( new Animation::Key(time, 0) ) );

			if( rightIt == m_selectedKeys.end() )
			{
				m_snappingClosestKey = *m_selectedKeys.rbegin();
			}
			else if( (*rightIt)->getTime() == time || rightIt == m_selectedKeys.begin() )
			{
				m_snappingClosestKey = *rightIt;
			}
			else
			{
				auto leftIt = std::prev( rightIt );
				m_snappingClosestKey = abs( time - (*leftIt)->getTime() ) < abs( time - (*rightIt)->getTime() ) ? *leftIt : *rightIt;
			}
		}

		moveKeyframes( V2f( i.x, i.y ) );
	}

	if( m_dragMode == DragMode::MoveTangent && m_dragTangent.first )
	{
		moveTangent( V2f( i.x, i.y ) );
	}

	if( m_dragMode == DragMode::MoveFrame )
	{
		m_context->setFrame( round( timeToFrame( m_context->getFramesPerSecond(), i.x ) ) );
	}

	m_lastDragPosition = V2f( i.x, i.y );

	dirty( DirtyType::Render );
	return true;
}

bool AnimationGadget::dragEnd( GadgetPtr gadget, const DragDropEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}

	switch( m_dragMode )
	{

	case DragMode::Selecting :
	{

		Box2f b;
		b.extendBy( V2f( m_dragStartPosition.x, m_dragStartPosition.y ) );
		b.extendBy( V2f( m_lastDragPosition.x, m_lastDragPosition.y ) );

		for( auto &member : *m_editablePlugs )
		{
			Animation::CurvePlug *curvePlug = IECore::runTimeCast<Animation::CurvePlug>( &member );

			for( Animation::Key &key : *curvePlug )
			{
				if( b.intersects( V2f( key.getTime().getSeconds(), key.getValue() ) ) )
				{
					m_selectedKeys.emplace( &key );
				}
			}
		}

		// NOTE : the selection is cleared at the start of the drag select and notified so if
		//        selection non empty at end of drag select we need to notify selected key change

		if( ! m_selectedKeys.empty() )
		{
			m_selectedKeysChangedSignal( this );
		}

		break;
	}
	case DragMode::Moving :
	{
		m_overwrittenKeys.clear();
		m_originalKeyValues.clear();
		m_mergeGroupId++;
		break;
	}
	case DragMode::MoveTangent :
	{
		m_dragTangent.first.reset();
		m_dragTangentOriginalSlope = 0.0;
		m_dragTangentOriginalAccel = 0.0;
		m_mergeGroupId++;
		break;
	}

	default :
		break;

	}

	ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	viewportGadget->setDragTracking( ViewportGadget::DragTracking::XDragTracking | ViewportGadget::DragTracking::YDragTracking );

	m_dragMode = DragMode::None;
	m_moveAxis = MoveAxis::Both;
	Pointer::setCurrent( "" );

	dirty( DirtyType::Render );

	return true;
}

bool AnimationGadget::leave()
{
	if( m_frameIndicatorPreviewFrame )
	{
		m_frameIndicatorPreviewFrame = boost::none;
		dirty( DirtyType::Render );
	}
	return true;
}

bool AnimationGadget::keyPress( GadgetPtr gadget, const KeyEvent &event )
{
	if( event.key == "I" )
	{
		insertKeyframes();
		m_mergeGroupId++;
		dirty( DirtyType::Render );
		return true;
	}

	if( event.key == "F" )
	{
		frame();
		return true;
	}

	if( event.key == "Control" )
	{
		if( m_highlightedCurve )
		{
			m_keyPreview = true;
			dirty( DirtyType::Render );
		}
		return true;
	}

	if( event.key == "Delete" || event.key == "Backspace" )
	{
		removeKeyframes();
		m_mergeGroupId++;
		dirty( DirtyType::Render );
		return true;
	}

	return false;
}

bool AnimationGadget::keyRelease( GadgetPtr gadget, const KeyEvent &event )
{
	if( event.key == "Control" )
	{
		m_keyPreview = false;
		dirty( DirtyType::Render );
	}

	return false;
}

std::string AnimationGadget::undoMergeGroup() const
{
	return boost::str( boost::format( "AnimationGadget%1%%2%" ) % this % m_mergeGroupId );
}

bool AnimationGadget::onTimeAxis( int y ) const
{
	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	Imath::V2i resolution = viewportGadget->getViewport();

	return y >= resolution.y - m_yMargin;
}

bool AnimationGadget::onValueAxis( int x ) const
{
	return x <= m_xMargin;
}

Animation::KeyPtr AnimationGadget::keyAt( const IECore::LineSegment3f &position )
{
	Animation::ConstKeyPtr k = const_cast<const AnimationGadget*>( this )->keyAt( position );
	return const_cast<Animation::Key*>( k.get() );
}

Animation::ConstKeyPtr AnimationGadget::keyAt( const IECore::LineSegment3f &position ) const
{
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
				V2f keyPosition = viewportGadget->worldToRasterSpace( V3f( key.getTime().getSeconds(), key.getValue(), 0 ) );
				style->renderAnimationKey( keyPosition, Style::NormalState, 4.0 ); // slightly bigger for easier selection
			}
		}
	}

	if( selection.empty() )
	{
		return nullptr;
	}

	return keys[selection[0].name-1];
}

std::pair<Gaffer::Animation::KeyPtr, Gaffer::Animation::Tangent::Direction> AnimationGadget::tangentAt( const IECore::LineSegment3f &position )
{
	const std::pair<Animation::ConstKeyPtr, Animation::Tangent::Direction> result =
		static_cast< const AnimationGadget* >( this )->tangentAt( position );
	return std::pair<Animation::KeyPtr, Animation::Tangent::Direction>(
		const_cast< Animation::Key* >( result.first.get() ), result.second );
}

std::pair<Gaffer::Animation::ConstKeyPtr, Gaffer::Animation::Tangent::Direction> AnimationGadget::tangentAt( const IECore::LineSegment3f &position ) const
{
	std::pair<Animation::ConstKeyPtr, Animation::Tangent::Direction> result( 0, Animation::Tangent::Direction::Into );

	std::vector<IECoreGL::HitRecord> selection;
	std::vector<Animation::ConstKeyPtr> keys;

	{
		ViewportGadget::SelectionScope selectionScope( position, this, selection, IECoreGL::Selector::IDRender );
		IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector();
		const Style *style = this->style();
		style->bind();
		GLuint name = 0;

		const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
		ViewportGadget::RasterScope rasterScope( viewportGadget );

		for( auto &member : *m_editablePlugs )
		{
			Animation::CurvePlug *curvePlug = IECore::runTimeCast<Animation::CurvePlug>( &member );

			++name; // NOTE : Name 0 is invalid, so start at 1, for each curve this skips into tangent of first key

			const Animation::Key* previousKey = 0;
			bool previousKeySelected = false;
			for( Animation::Key &key : *curvePlug )
			{
				const bool isSelected = m_selectedKeys.count( Animation::KeyPtr( &key ) ) > 0;
				keys.emplace_back( &key );

				if( previousKey )
				{
					const Animation::Interpolator::Hints hints = previousKey->getInterpolator()->getHints();

					if( ( isSelected || previousKeySelected ) && (
							hints.test( Animation::Interpolator::Hint::UseSlopeLo ) ||
							hints.test( Animation::Interpolator::Hint::UseAccelLo ) ) )
					{
						const Animation::Tangent& from = previousKey->getTangent( Animation::Tangent::Direction::From );
						const V2d fromPosKey = from.getPosition( Animation::Tangent::Space::Key, false );
						const V2f fromPosRas = viewportGadget->worldToRasterSpace( V3f( fromPosKey.x, fromPosKey.y, 0 ) );
						selector->loadName( name );
						style->renderSolidRectangle( Box2f( fromPosRas - V2f( 4.0 ), fromPosRas + V2f( 4.0 ) ) ); // slightly bigger for easier selection
					}

					++name;

					if( ( isSelected || previousKeySelected ) && (
						hints.test( Animation::Interpolator::Hint::UseSlopeHi ) ||
						hints.test( Animation::Interpolator::Hint::UseAccelHi ) ) )
					{
						const Animation::Tangent& into = key.getTangent( Animation::Tangent::Direction::Into );
						const V2d intoPosKey = into.getPosition( Animation::Tangent::Space::Key, false );
						const V2f intoPosRas = viewportGadget->worldToRasterSpace( V3f( intoPosKey.x, intoPosKey.y, 0 ) );
						selector->loadName( name );
						style->renderSolidRectangle( Box2f( intoPosRas - V2f( 4.0 ), intoPosRas + V2f( 4.0 ) ) ); // slightly bigger for easier selection
					}

					++name;
				}

				previousKey = & key;
				previousKeySelected = isSelected;
			}

			++name; // NOTE : for each curve this skips from tangent of last key
		}
	}

	if( ! selection.empty() )
	{
		result.first = keys[ ( selection[0].name ) / 2 ];
		result.second = static_cast< Animation::Tangent::Direction >( ( selection[0].name ) % 2 );
	}

	return result;
}

Animation::CurvePlugPtr AnimationGadget::curveAt( const IECore::LineSegment3f &position )
{
	Animation::ConstCurvePlugPtr c = const_cast<const AnimationGadget*>( this )->curveAt( position );
	return const_cast<Animation::CurvePlug *>( c.get() );
}

Animation::ConstCurvePlugPtr AnimationGadget::curveAt( const IECore::LineSegment3f &position ) const
{
	std::vector<IECoreGL::HitRecord> selection;
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

	return curves[selection[0].name-1];
}

bool AnimationGadget::frameIndicatorUnderMouse( const IECore::LineSegment3f &position ) const
{
	std::vector<IECoreGL::HitRecord> hits;

	{
		ViewportGadget::SelectionScope selectionScope( position, this, hits, IECoreGL::Selector::IDRender );
		IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector();
		const Style *style = this->style();
		style->bind();
		GLuint name = 1; // Name 0 is invalid, so we start at 1

		selector->loadName( name );

		renderFrameIndicator( static_cast<int>( m_context->getFrame() ), style, /* preview = */ false, /* lineWidth = */ 4.0 );
	}

	return !hits.empty();
}

void AnimationGadget::setContext( Context *context )
{
	m_context = context;
	dirty( DirtyType::Render );
}

Context *AnimationGadget::getContext() const
{
	return m_context;
}

void AnimationGadget::visiblePlugAdded( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	Animation::CurvePlug *curvePlug = IECore::runTimeCast<Animation::CurvePlug>( member );

	// \todo: should only connect if we don't monitor this node yet
	if( Node *node = curvePlug->node() )
	{
		node->plugDirtiedSignal().connect( boost::bind( &AnimationGadget::plugDirtied, this, ::_1 ) );
	}

	dirty( DirtyType::Render );
}

void AnimationGadget::visiblePlugRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	dirty( DirtyType::Render );
}

void AnimationGadget::editablePlugAdded( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	Animation::CurvePlug* const curvePlug = IECore::runTimeCast< Animation::CurvePlug >( member );

	if( curvePlug )
	{
		CurvePlugConnectionMap::iterator it = m_editablePlugsConnections.find( curvePlug );
		if( it == m_editablePlugsConnections.end() )
		{
			m_editablePlugsConnections[ curvePlug ] =
				curvePlug->keyRemovedSignal().connect( boost::bind( &AnimationGadget::keyRemoved, this, ::_1, ::_2 ) );
		}

		dirty( DirtyType::Render );
	}
}

void AnimationGadget::editablePlugRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	Animation::CurvePlug* const curvePlug = IECore::runTimeCast< Animation::CurvePlug >( member );

	if( curvePlug )
	{
		CurvePlugConnectionMap::iterator it = m_editablePlugsConnections.find( curvePlug );
		if( it != m_editablePlugsConnections.end() )
		{
			( *it ).second.disconnect();
			m_editablePlugsConnections.erase( it );
		}

		// NOTE : check if any of the curve's keys are selected and deselect them then notify.

		bool selectionChanged = false;
		for( Animation::KeyIterator it = curvePlug->begin(), itEnd = curvePlug->end(); it != itEnd; ++it )
		{
			SelectedKeys::iterator sit = m_selectedKeys.find( &( *it ) );
			if( sit != m_selectedKeys.end() )
			{
				m_selectedKeys.erase( sit );
				selectionChanged = true;
			}
		}

		if( selectionChanged )
		{
			m_selectedKeysChangedSignal( this );
		}

		dirty( DirtyType::Render );
	}
}

void AnimationGadget::keyRemoved( Animation::CurvePlug* const curvePlug, Animation::Key* const key )
{
	// NOTE : Connect to key removed signal so that we can ensure that selected keys only
	//        contains keys that are in a curve, however whilst drag moving keys, selected keys may
	//        be removed temporarily from their parent curve, they should be added back if all
	//        selected keys are moved by the same amount so no need to notify selection change.

	if( m_dragMode != DragMode::Moving )
	{
		SelectedKeys::iterator it = m_selectedKeys.find( key );
		if( it != m_selectedKeys.end() )
		{
			m_selectedKeys.erase( it );
			m_selectedKeysChangedSignal( this );
		}
	}
}

void AnimationGadget::renderCurve( const Animation::CurvePlug *curvePlug, const Style *style ) const
{
	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	ViewportGadget::RasterScope rasterScope( viewportGadget );

	Animation::ConstKeyPtr previousKey = nullptr;
	V2f previousKeyPosition = V2f( 0 );

	bool isHighlighted = curvePlug == m_highlightedCurve;

	for( const auto &key : *curvePlug )
	{
		V2f keyPosition = viewportGadget->worldToRasterSpace( V3f( key.getTime().getSeconds(), key.getValue(), 0 ) );

		if( previousKey )
		{
			// \todo: needs tangent computation/hand-off as soon as we support more interpolation modes
			//        consider passing interpolation into renderCurveSegment to handle all drawing there

			const Imath::Color3f color3 = colorFromName( drivenPlugName( curvePlug ) );

			if( previousKey->getInterpolator()->getName() == "Step" )
			{
				style->renderAnimationCurve( previousKeyPosition, V2f( keyPosition.x, previousKeyPosition.y ), V2f( 0 ), V2f( 0 ), isHighlighted ? Style::HighlightedState : Style::NormalState, &color3 );
				style->renderAnimationCurve( V2f( keyPosition.x, previousKeyPosition.y ), keyPosition, V2f( 0 ), V2f( 0 ), isHighlighted ? Style::HighlightedState : Style::NormalState, &color3 );
			}
			else if( previousKey->getInterpolator()->getName() == "StepNext" )
			{
				style->renderAnimationCurve( previousKeyPosition, V2f( previousKeyPosition.x, keyPosition.y ), V2f( 0 ), V2f( 0 ), isHighlighted ? Style::HighlightedState : Style::NormalState, &color3 );
				style->renderAnimationCurve( V2f( previousKeyPosition.x, keyPosition.y ), keyPosition, V2f( 0 ), V2f( 0 ), isHighlighted ? Style::HighlightedState : Style::NormalState, &color3 );
			}
			else if( previousKey->getInterpolator()->getName() == "Linear" )
			{
				style->renderAnimationCurve( previousKeyPosition, keyPosition, V2f( 0 ), V2f( 0 ), isHighlighted ? Style::HighlightedState : Style::NormalState, &color3 );
			}
			else
			{
				V2f p0 = previousKeyPosition;
				const double range = ( key.getTime() - previousKey->getTime() ).getSeconds();

				for( int i = 1; i < 50; ++ i )
				{
					const double scale = static_cast< double >( i ) / 50.0;
					Animation::Time time = previousKey->getTime() + Animation::Time( range * scale, Animation::Time::Units::Seconds );
					double value = curvePlug->evaluate( time );
					V2f p1 = viewportGadget->worldToRasterSpace( V3f( time.getSeconds(), value, 0 ) );
					style->renderAnimationCurve( p0, p1, V2f( 0 ), V2f( 0 ), isHighlighted ? Style::HighlightedState : Style::NormalState, &color3 );
					p0 = p1;
				}

				style->renderAnimationCurve( p0, keyPosition, V2f( 0 ), V2f( 0 ), isHighlighted ? Style::HighlightedState : Style::NormalState, &color3 );
			}
		}

		previousKey = &key;
		previousKeyPosition = keyPosition;
	}
}

void AnimationGadget::renderFrameIndicator( int frame, const Style *style, bool preview, float lineWidth ) const
{
	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	Imath::V2i resolution = viewportGadget->getViewport();
	ViewportGadget::RasterScope rasterScope( viewportGadget );

	const Imath::Color4f frameIndicatorColor = preview ? Imath::Color4f( 120 / 255.0f, 120 / 255.0f, 120 / 255.0f, 1.0f ) : Imath::Color4f( 240 / 255.0, 220 / 255.0, 40 / 255.0, 1.0f );

	int currentFrameRasterPosition = viewportGadget->worldToRasterSpace( V3f( frameToTime<float>( m_context->getFramesPerSecond(), frame ), 0, 0 ) ).x;
	style->renderLine( IECore::LineSegment3f( V3f( currentFrameRasterPosition, 0, 0 ), V3f( currentFrameRasterPosition, resolution.y, 0 ) ), lineWidth, &frameIndicatorColor );

	if( !preview )
	{
		Imath::Color4f frameLabelColor( 60.0 / 255, 60.0 / 255, 60.0 / 255, 1.0 );

		Box3f frameLabelBound = style->textBound( Style::BodyText, std::to_string( frame ) );
		style->renderSolidRectangle( Box2f( V2f( currentFrameRasterPosition, resolution.y - m_yMargin ), V2f( currentFrameRasterPosition + frameLabelBound.size().x * m_textScale + 2*m_labelPadding, resolution.y - m_yMargin - frameLabelBound.size().y * m_textScale - 2*m_labelPadding ) ) );

		glPushMatrix();
			glTranslatef( currentFrameRasterPosition + m_labelPadding, resolution.y - m_yMargin - m_labelPadding, 0 ); // \todo
			glScalef( m_textScale, -m_textScale, m_textScale );
			style->renderText( Style::BodyText, std::to_string( frame ), Style::NormalState, &frameLabelColor );
		glPopMatrix();
	}
}

bool AnimationGadget::plugSetAcceptor( const Set *s, const Set::Member *m )
{
	const Animation::CurvePlug *cp = IECore::runTimeCast<const Animation::CurvePlug>( m );
	if( !cp )
	{
		return false;
	}

	return true;
}

void AnimationGadget::updateKeyPreviewLocation( const Gaffer::Animation::CurvePlug *curvePlug, float time )
{
	if( !curvePlug )
	{
		m_keyPreviewLocation = V3f( 0 );
		return;
	}

	Animation::Time snappedTime( time, Animation::Time::Units::Seconds );
	snappedTime.snap( m_context->getFramesPerSecond() );

	float value = curvePlug->evaluate( snappedTime );
	m_keyPreviewLocation = V3f( snappedTime.getSeconds(), value, 0 );
}
