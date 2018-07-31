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

#include "IECoreGL/Selector.h"

#include "IECore/InternedString.h"
#include "IECore/NullObject.h"

#include "boost/algorithm/string.hpp"
#include "boost/bind.hpp"

#include "math.h"

using namespace Gaffer;
using namespace GafferUI;
using namespace Imath;

namespace
{

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

// \todo: Use actual fps setting. For now, we always use 24 fps
template<typename T>
T frameToTime( T frame )
{
	return frame / 24.0;
}

template<typename T>
T timeToFrame( T time )
{
	return time * 24.0;
}

// \todo: Consider making the colorForAxes function in StandardStyle public?
//        Include names for plugs representing color? (foo.r, foo.g, foo.b)
void colorFromName( std::string name, Imath::Color3f &color )
{
	if( boost::ends_with( name, ".x" ) )
	{
		color = Imath::Color3f( 0.73, 0.17, 0.17 );
	}

	if( boost::ends_with( name, ".y" ) )
	{
		color = Imath::Color3f( 0.2, 0.57, 0.2 );
	}

	if( boost::ends_with( name, ".z" ) )
	{
		color = Imath::Color3f( 0.2, 0.36, 0.74 );
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

void computeGrid( const ViewportGadget *viewportGadget, AxisDefinition &x, AxisDefinition &y )
{
	Imath::V2i resolution = viewportGadget->getViewport();

	IECore::LineSegment3f min, max;
	min = viewportGadget->rasterToWorldSpace( V2f( 0 ) );
	max = viewportGadget->rasterToWorldSpace( V2f( resolution.x, resolution.y ) );
	Imath::Box2f viewportBounds = Box2f( V2f( min.p0.x, min.p0.y ), V2f( max.p0.x, max.p0.y ) );

	Box2f viewportBoundsFrames( timeToFrame( viewportBounds.min ), timeToFrame( viewportBounds.max ) );
	V2i labelMinSize( 50, 20 );
	int xStride = 1;
	float yStride = 1;

	// \todo the box's size() is unrealiable because it considers the box empty for the inverted coords we seem to have here
	V2f pxPerUnit = V2f(
		resolution.x / abs( viewportBoundsFrames.min.x - viewportBoundsFrames.max.x ),
		resolution.y / abs( viewportBounds.min.y - viewportBounds.max.y ) );

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
		float time = frameToTime( static_cast<float>( i ) );
		x.main.push_back( std::make_pair( viewportGadget->worldToRasterSpace( V3f( time, 0, 0 ) ).x, i ) );

		float subStride = frameToTime( xStride / 5.0 );
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

IE_CORE_DEFINERUNTIMETYPED( AnimationGadget );

AnimationGadget::AnimationGadget()
	: m_context( nullptr ), m_visiblePlugs( new StandardSet() ), m_editablePlugs( new StandardSet() ), m_dragStartPosition( 0 ), m_lastDragPosition( 0 ), m_dragMode( DragMode::None ), m_moveAxis( MoveAxis::Both ), m_snappingClosestKey( nullptr ), m_highlightedKey( nullptr ), m_highlightedCurve( nullptr ), m_mergeGroupId( 0 ), m_kKeyPressed( false ), m_keyPreview( false ), m_keyPreviewLocation( 0 ), m_xMargin( 60 ), m_yMargin( 20 ), m_textScale( 10 ), m_labelPadding( 5 )
{
	// parentChangedSignal().connect( boost::bind( &AnimationGadget::parentChanged, this, ::_1, ::_2 ) );

	buttonPressSignal().connect( boost::bind( &AnimationGadget::buttonPress, this, ::_1,  ::_2 ) );
	buttonReleaseSignal().connect( boost::bind( &AnimationGadget::buttonRelease, this, ::_1,  ::_2 ) );

	keyPressSignal().connect( boost::bind( &AnimationGadget::keyPress, this, ::_1,  ::_2 ) );
	keyReleaseSignal().connect( boost::bind( &AnimationGadget::keyRelease, this, ::_1,  ::_2 ) );

	mouseMoveSignal().connect( boost::bind( &AnimationGadget::mouseMove, this, ::_1, ::_2 ) );
	dragBeginSignal().connect( boost::bind( &AnimationGadget::dragBegin, this, ::_1, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &AnimationGadget::dragEnter, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &AnimationGadget::dragMove, this, ::_1, ::_2 ) );
	dragEndSignal().connect( boost::bind( &AnimationGadget::dragEnd, this, ::_1, ::_2 ) );

	m_editablePlugs->memberAcceptanceSignal().connect( boost::bind( &AnimationGadget::plugSetAcceptor, this, ::_1, ::_2 ) );
	m_editablePlugs->memberAddedSignal().connect( boost::bind( &AnimationGadget::editablePlugAdded, this, ::_1, ::_2 ) );
	m_editablePlugs->memberRemovedSignal().connect( boost::bind( &AnimationGadget::editablePlugRemoved, this, ::_1, ::_2 ) );

	m_visiblePlugs->memberAcceptanceSignal().connect( boost::bind( &AnimationGadget::plugSetAcceptor, this, ::_1, ::_2 ) );
	m_visiblePlugs->memberAddedSignal().connect( boost::bind( &AnimationGadget::visiblePlugAdded, this, ::_1, ::_2 ) );
	m_visiblePlugs->memberRemovedSignal().connect( boost::bind( &AnimationGadget::visiblePlugRemoved, this, ::_1, ::_2 ) );

}

AnimationGadget::~AnimationGadget()
{
}

void AnimationGadget::doRenderLayer( Layer layer, const Style *style ) const
{
	Gadget::doRenderLayer( layer, style );

	glDisable( GL_DEPTH_TEST );

	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	Imath::V2i resolution = viewportGadget->getViewport();

	ViewportGadget::RasterScope rasterScope( viewportGadget );

	switch ( layer )
	{

	case AnimationLayer::Grid :
	{
		AxisDefinition xAxis, yAxis;
		computeGrid( viewportGadget, xAxis, yAxis );

		Imath::Color3f axesColor( 60.0 / 255, 60.0 / 255, 60.0 / 255 );

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

		for( auto &runtimeTyped : *m_editablePlugs )
		{
			Animation::CurvePlug *curvePlug = IECore::runTimeCast<Animation::CurvePlug>( &runtimeTyped );

			for( Animation::Key &key : *curvePlug )
			{
				bool isHighlighted = m_highlightedKey && key == *m_highlightedKey;
				bool isSelected = m_selectedKeys.count( Animation::KeyPtr( &key ) ) > 0;
				V2f keyPosition = viewportGadget->worldToRasterSpace( V3f( key.getTime(), key.getValue(), 0 ) );
				style->renderAnimationKey( keyPosition, isSelected || isHighlighted ? Style::HighlightedState : Style::NormalState, isHighlighted ? 3.0 : 2.0, &black );
			}
		}
		break;
	}

	case AnimationLayer::Axes :
	{
		AxisDefinition xAxis, yAxis;
		computeGrid( viewportGadget, xAxis, yAxis );

		renderFrameIndicator( style );

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
	requestRender();
}

std::string AnimationGadget::getToolTip( const IECore::LineSegment3f &line ) const
{
	if( const Animation::ConstKeyPtr key = keyAt( line ) )
	{
		return boost::str( boost::format( "%f -> %f" ) % key->getTime() % key->getValue() );
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

	float snappedTime = frameToTime( round( timeToFrame( time ) ) );

	if( !curvePlug->closestKey( snappedTime, 0.004 ) ) // \todo: use proper ticks
	{
		float value = curvePlug->evaluate( snappedTime );
		curvePlug->addKey( new Animation::Key( snappedTime, value ) );
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

	for( const auto &keyPtr : m_selectedKeys )
	{
		Animation::CurvePlug *parent = keyPtr->parent();
		if( parent )
		{
			parent->removeKey( keyPtr );
		}
	}

	m_selectedKeys.clear();
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

	// Compute snapping offset used for all keys
	float xSnappingCurrentOffset = 0;
	if( m_moveAxis != MoveAxis::Y )
	{
		float dragOffset = currentDragPosition.x - m_dragStartPosition.x;
		xSnappingCurrentOffset = dragOffset;
		if( m_snappingClosestKey )
		{
			float unsnappedFrame = timeToFrame( m_snappingClosestKey->getTime() + xSnappingCurrentOffset );
			xSnappingCurrentOffset = frameToTime( round( unsnappedFrame ) ) - m_snappingClosestKey->getTime();
		}
	}

	for( auto &key : m_selectedKeys )
	{
		// Apply offset for key's value
		if( m_moveAxis != MoveAxis::X )
		{
			key->setValue( key->getValue() + currentDragPosition.y - m_lastDragPosition.y );
		}

		// Apply offset for key's time
		if( m_moveAxis != MoveAxis::Y )
		{
			float dragStartPosition = key->getTime() - m_xSnappingPreviousOffset;
			float newTime = dragStartPosition + xSnappingCurrentOffset;

			// If a key already exists on the new frame, we overwrite it, but
			// store it for reinserting should the drag continue and the frame
			// free up again.
			Animation::KeyPtr clashingKey = key->parent()->closestKey( newTime, 0.004 );
			if( clashingKey && clashingKey != key )
			{
				m_overwrittenKeys.emplace( clashingKey, clashingKey->parent() );
				clashingKey->parent()->removeKey( clashingKey );
			}

			key->setTime( newTime );
		}
	}

	// Check if any of the previously overwritten keys can be inserted back into the curve
	for( auto it = m_overwrittenKeys.begin(); it != m_overwrittenKeys.end(); )
	{
		Animation::KeyPtr clashingKey = it->second->closestKey( it->first->getTime(), 0.004 ); // \todo: use proper ticks

		if( clashingKey )
		{
			++it;
		}
		else
		{
			it->second->addKey( it->first );
			it = m_overwrittenKeys.erase( it );
		}
	}

	if( m_moveAxis != MoveAxis::Y )
	{
		m_xSnappingPreviousOffset = xSnappingCurrentOffset;
	}
}

void AnimationGadget::frame()
{
	Box3f b;

	// trying to frame to selected keys first
	if( !m_selectedKeys.empty() )
	{
		for( const auto &key : m_selectedKeys )
		{
			b.extendBy( V3f( key->getTime(), key->getValue(), 0 ) );
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
				b.extendBy( V3f( key.getTime(), key.getValue(), 0 ) );
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
				b.extendBy( V3f( key.getTime(), key.getValue(), 0 ) );
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

	// Move current frame
	if( event.button == ButtonEvent::Left && m_kKeyPressed )
	{
		m_context->setFrame( round( timeToFrame( i.x ) ) );
		requestRender();
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
			m_selectedKeys.clear();
			m_selectedKeys.insert( key );
		}
		else
		{
			// toggle selection
			auto it = m_selectedKeys.find( key );
			if( it != m_selectedKeys.end() )
			{
				m_selectedKeys.erase( key );
			}
			else
			{
				m_selectedKeys.insert( key );
			}
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
				for( Animation::Key &key : *curvePlug )
				{
					m_selectedKeys.emplace( &key );
				}
			}
			else // try to make it editable
			{
				bool shiftHeld = event.modifiers & DragDropEvent::Shift;
				if( !shiftHeld )
				{
					m_editablePlugs->clear();
				}

				m_editablePlugs->add( curvePlug.get() );
			}
		}
	}
	else // background
	{
		m_selectedKeys.clear();
	}

	requestRender();

	return true;
}

IECore::RunTimeTypedPtr AnimationGadget::dragBegin( GadgetPtr gadget, const DragDropEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return nullptr;
	}

	switch ( event.buttons )
	{

	case ButtonEvent::Left :
	{
		if( Animation::KeyPtr key = keyAt( event.line ) )
		{
			// If dragging an unselected Key, the assumption is that only this Key
			// should be moved. On the other hand, if the key was selected, we will
			// move the entire selection.
			if( m_selectedKeys.count( key ) == 0 )
			{
				m_selectedKeys.clear();
			}

			m_selectedKeys.insert( key );
			m_dragMode = DragMode::Moving;
		}
		else if( m_kKeyPressed || frameIndicatorUnderMouse( event.line ) )
		{
			m_dragMode = DragMode::MoveFrame;
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

	// There's different ways to initiate a drag, but we need to do some
	// additional work for all of them.
	if( m_dragMode == DragMode::Moving )
	{
		bool shiftHeld = event.modifiers & DragDropEvent::Shift;
		if( shiftHeld )
		{
			m_moveAxis = MoveAxis::Undefined;
		}

		m_snappingClosestKey = nullptr;
		m_xSnappingPreviousOffset = 0;

		// Clean up selection so that we operate on valid Keys only
		for( auto &key : m_selectedKeys )
		{
			if( !key->parent() )
			{
				m_selectedKeys.erase( key );
				continue;
			}
		}
	}

	m_dragStartPosition = m_lastDragPosition = V2f( i.x, i.y );

	requestRender();
	return IECore::NullObject::defaultNullObject();
}

bool AnimationGadget::mouseMove( GadgetPtr gadget, const ButtonEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}

	if( Animation::KeyPtr key = keyAt( event.line ) )
	{
		m_highlightedKey = key;
		m_highlightedCurve = nullptr;
	}
	else
	{
		if( m_highlightedKey )
		{
			m_highlightedKey = nullptr;
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
	requestRender();

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
	requestRender();
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
			if( abs( i.x - m_dragStartPosition.x ) >= abs ( i.y - m_dragStartPosition.y ) )
			{
				m_moveAxis = MoveAxis::X;
				Pointer::setCurrent( "moveHorizontally" );
			}
			else
			{
				m_moveAxis = MoveAxis::Y;
				Pointer::setCurrent( "moveVertically" );
			}
		}

		if( m_moveAxis != MoveAxis::Y && !m_snappingClosestKey )
		{
			// determine position of selected keyframe that is closest to pointer
			// \todo: move into separate function, ideally consolidate with Animation::CurvePlug::closestKey?
			auto rightIt = m_selectedKeys.lower_bound( Animation::KeyPtr( new Animation::Key(i.x, 0) ) );

			if( rightIt == m_selectedKeys.end() )
			{
				m_snappingClosestKey = *m_selectedKeys.rbegin();
			}
			else if( (*rightIt)->getTime() == i.x || rightIt == m_selectedKeys.begin() )
			{
				m_snappingClosestKey = *rightIt;
			}
			else
			{
				auto leftIt = std::prev( rightIt );
				m_snappingClosestKey = fabs( i.x - (*leftIt)->getTime() ) < fabs( i.x - (*rightIt)->getTime() ) ? *leftIt : *rightIt;
			}
		}

		moveKeyframes( V2f( i.x, i.y ) );
	}

	if( m_dragMode == DragMode::MoveFrame )
	{
			m_context->setFrame( round( timeToFrame( i.x ) ) );
	}

	m_lastDragPosition = V2f( i.x, i.y );

	requestRender();
	return true;
}

bool AnimationGadget::dragEnd( GadgetPtr gadget, const DragDropEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}

	switch (m_dragMode)
	{

	case DragMode::Selecting :
	{

		Box2f b;
		b.extendBy( V2f( m_dragStartPosition.x, m_dragStartPosition.y ) );
		b.extendBy( V2f( m_lastDragPosition.x, m_lastDragPosition.y ) );

		bool shiftHeld = event.modifiers & ButtonEvent::Shift;
		if( !shiftHeld )
		{
			m_selectedKeys.clear();
		}

		for( auto &member : *m_editablePlugs )
		{
			Animation::CurvePlug *curvePlug = IECore::runTimeCast<Animation::CurvePlug>( &member );

			for( Animation::Key &key : *curvePlug )
			{
				if( b.intersects( V2f( key.getTime(), key.getValue() ) ) )
				{
					m_selectedKeys.emplace( &key );
				}
			}
		}

		break;
	}
	case DragMode::Moving :
	{
		m_overwrittenKeys.clear();
		m_mergeGroupId++;
		break;
	}

	default :
		break;

	}

	m_dragMode = DragMode::None;
	m_moveAxis = MoveAxis::Both;
	Pointer::setCurrent( "" );

	requestRender();

	return true;
}

bool AnimationGadget::keyPress( GadgetPtr gadget, const KeyEvent &event )
{
	if( event.key == "I" )
	{
		insertKeyframes();
		m_mergeGroupId++;
		requestRender();
		return true;
	}

	if( event.key == "F" )
	{
		frame();
		return true;
	}

	if( event.key == "K" )
	{
		m_kKeyPressed = true;
		return true;
	}

	if( event.key == "Control" )
	{
		if( m_highlightedCurve )
		{
			m_keyPreview = true;
			requestRender();
		}
		return true;
	}

	if( event.key == "Delete" || event.key == "Backspace" )
	{
		removeKeyframes();
		m_mergeGroupId++;
		requestRender();
		return true;
	}

	return false;
}

bool AnimationGadget::keyRelease( GadgetPtr gadget, const KeyEvent &event )
{

	if( event.key == "K" )
	{
		m_kKeyPressed = false;
	}

	if( event.key == "Control" )
	{
		m_keyPreview = false;
		requestRender();
	}

	return false;
}

std::string AnimationGadget::undoMergeGroup() const
{
	return boost::str( boost::format( "AnimationGadget%1%%2%" ) % this % m_mergeGroupId );
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
		renderFrameIndicator( style, /* lineWidth = */ 4.0 );
	}

	return !hits.empty();
}

void AnimationGadget::setContext( Context *context )
{
	m_context = context;
	requestRender();
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

	requestRender();
}

void AnimationGadget::visiblePlugRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	requestRender();
}

void AnimationGadget::editablePlugAdded( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	requestRender();
}

void AnimationGadget::editablePlugRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	requestRender();
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
		V2f keyPosition = viewportGadget->worldToRasterSpace( V3f( key.getTime(), key.getValue(), 0 ) );

		if( previousKey )
		{
			// \todo: needs tangent computation/hand-off as soon as we support more interpolation modes
			//        consider passing interpolation into renderCurveSegment to handle all drawing there

			Imath::Color3f userColor( 1.0 ); // curves render white per default
			colorFromName( drivenPlugName( curvePlug ), userColor );

			if( key.getType() == Gaffer::Animation::Linear )
			{
				style->renderAnimationCurve( previousKeyPosition, keyPosition, /* inTangent */ V2f( 0 ), /* outTangent */ V2f( 0 ), isHighlighted ? Style::HighlightedState : Style::NormalState, &userColor );
			}
			else if( key.getType() == Gaffer::Animation::Step )
			{
				// \todo: replace with linear curve segment to get highlighting
				style->renderLine( IECore::LineSegment3f( V3f( previousKeyPosition.x, previousKeyPosition.y, 0 ), V3f( keyPosition.x, previousKeyPosition.y, 0) ), 0.5, &userColor );
				style->renderLine( IECore::LineSegment3f( V3f( keyPosition.x, previousKeyPosition.y, 0 ), V3f( keyPosition.x, keyPosition.y, 0 ) ), 0.5, &userColor );
			}
		}

		previousKey = &key;
		previousKeyPosition = keyPosition;
	}
}

void AnimationGadget::renderFrameIndicator( const Style *style, float lineWidth ) const
{
	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	Imath::V2i resolution = viewportGadget->getViewport();
	ViewportGadget::RasterScope rasterScope( viewportGadget );

	Imath::Color3f frameIndicatorColor( 240 / 255.0, 220 / 255.0, 40 / 255.0 );
	Imath::Color3f frameLabelColor( 60.0 / 255, 60.0 / 255, 60.0 / 255 );

	int currentFrameRasterPosition = viewportGadget->worldToRasterSpace( V3f( m_context->getTime(), 0, 0 ) ).x;
	style->renderLine( IECore::LineSegment3f( V3f( currentFrameRasterPosition, 0, 0 ), V3f( currentFrameRasterPosition, resolution.y, 0 ) ), lineWidth, &frameIndicatorColor );

	Box3f frameLabelBound = style->textBound( Style::BodyText, std::to_string( static_cast<int>( m_context->getFrame() ) ) );
	style->renderSolidRectangle( Box2f( V2f( currentFrameRasterPosition, resolution.y - m_yMargin ), V2f( currentFrameRasterPosition + frameLabelBound.size().x * m_textScale + 2*m_labelPadding, resolution.y - m_yMargin - frameLabelBound.size().y * m_textScale - 2*m_labelPadding ) ) );

	glPushMatrix();
		glTranslatef( currentFrameRasterPosition + m_labelPadding, resolution.y - m_yMargin - m_labelPadding, 0 ); // \todo
		glScalef( m_textScale, -m_textScale, m_textScale );
		style->renderText( Style::BodyText, std::to_string( static_cast<int>( m_context->getFrame() ) ), Style::NormalState, &frameLabelColor );
	glPopMatrix();
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

	float snappedTime = frameToTime( round( timeToFrame( time ) ) );
	float value = curvePlug->evaluate( snappedTime );
	m_keyPreviewLocation = V3f( snappedTime, value, 0 );
}
