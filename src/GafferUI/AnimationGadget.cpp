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
#include "Gaffer/Metadata.h"
#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/UndoScope.h"

#include "IECoreGL/Selector.h"

#include "IECore/InternedString.h"
#include "IECore/NullObject.h"

#include "boost/algorithm/string.hpp"
#include "boost/bind/bind.hpp"
#include "boost/multi_index/ordered_index.hpp"
#include "boost/multi_index/random_access_index.hpp"
#include "boost/multi_index_container.hpp"

#include <cmath>
#include <cassert>
#include <sstream>

using namespace boost::placeholders;
using namespace Gaffer;
using namespace GafferUI;
using namespace Imath;

namespace
{

const IECore::InternedString g_colorMetadata( "animation:color" );

void tieModeToBools( const Animation::TieMode mode, bool& tieSlope, bool& tieScale )
{
	tieSlope = false;
	tieScale = false;
	switch( mode )
	{
		case Animation::TieMode::Manual:
			break;
		case Animation::TieMode::Slope:
			tieSlope = true;
			break;
		case Animation::TieMode::Scale:
			tieSlope = true;
			tieScale = true;
			break;
		default:
			break;
	}
}

void evaluateCurve( const Animation::CurvePlug* const curvePlug,
	const float tStart, const float tEnd, const double unitPerPx,
	const ViewportGadget* const viewportGadget, std::vector< Imath::V2f >& vertices )
{
	// NOTE : When evaluating the extrapolated portions of a curve, evaluation starts at the extrapolation key
	//        to ensure any stipple pattern extends from the extrapolation key, so tEnd may be less than tStart.
	double const sign = ( tEnd < tStart ) ? -1.0 : 1.0;

	// NOTE : evaluate curve with one sample per pixel in time dimension so curve appears smooth at all zoom levels.
	double count;
	const double fract = std::modf( std::abs( tEnd - tStart ) / unitPerPx, & count );
	const int steps = static_cast< int >( count ) + ( ( fract == 0.0 ) ? 0 : 1 );

	if( vertices.empty() )
		vertices.push_back( viewportGadget->worldToRasterSpace( V3f( tStart, curvePlug->evaluate( tStart ), 0 ) ) );

	for( int i = 1; i < steps; ++i )
	{
		const double time = tStart + static_cast< double >( i ) * unitPerPx * sign;
		vertices.push_back( viewportGadget->worldToRasterSpace( V3f( time, curvePlug->evaluate( time ), 0 ) ) );
	}

	vertices.push_back( viewportGadget->worldToRasterSpace( V3f( tEnd, curvePlug->evaluate( tEnd ), 0 ) ) );
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

float snapTimeToFrame( float fps, float time, float threshold=std::numeric_limits<float>::max() )
{
	float frame = timeToFrame( fps, time );
	float rounded = round( frame );

	return frameToTime( fps, std::abs( frame - rounded ) > threshold ? frame : rounded );
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

const Gaffer::Plug* drivenPlug( const Animation::CurvePlug* const curvePlug )
{
	const FloatPlug* const out = curvePlug->outPlug();

	// Assuming that we only drive a single plug with this curve
	auto outputs = out->outputs();
	return ( ! outputs.empty() )
		? outputs.front()
		: nullptr;
}

Gaffer::Plug* drivenPlug( Animation::CurvePlug* const curvePlug )
{
	return const_cast< Gaffer::Plug* >( drivenPlug(
		static_cast< const Animation::CurvePlug* >( curvePlug ) ) );
}

std::string drivenPlugName( const Animation::CurvePlug* const curvePlug )
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

Imath::Color3f drivenPlugColor( const Animation::CurvePlug* const curvePlug )
{
	const Gaffer::Plug* const plug = drivenPlug( curvePlug );
	if( plug )
	{
		const IECore::ConstColor3fDataPtr colorData =
			Gaffer::Metadata::value< IECore::Color3fData >( plug, g_colorMetadata );
		if( colorData )
		{
			return colorData->readable();
		}
	}

	return Imath::Color3f( 1.f );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// AnimationGadget SelectionSet implementation
//////////////////////////////////////////////////////////////////////////

namespace GafferUI
{

struct AnimationGadget::SelectionSet : public Gaffer::Set
{
	SelectionSet();
	~SelectionSet() override;

	bool contains( const Gaffer::Set::Member *member ) const override;
	Gaffer::Set::Member *member( size_t index ) override;
	const Gaffer::Set::Member *member( size_t index ) const override;
	size_t size() const override;

	bool add( Gaffer::Animation::KeyPtr key );
	bool remove( Gaffer::Animation::KeyPtr key );
	void clear();
	void clear( const Gaffer::Animation::CurvePlug* curve );
	bool empty() const;

private:

	friend class AnimationGadget;

	bool removeInternal( const Gaffer::Animation::CurvePlug*, Gaffer::Animation::KeyPtr );

	struct MemberCompare
	{
		using result_type = bool;
		bool operator()( const Gaffer::Set::Member* const lhs, const Gaffer::Animation::KeyPtr& rhs ) const { return lhs < rhs.get(); }
		bool operator()( const Gaffer::Animation::KeyPtr& lhs, const Gaffer::Set::Member* const rhs ) const { return lhs.get() < rhs; }
	};

	using KeyContainer = boost::multi_index::multi_index_container<
		Gaffer::Animation::KeyPtr,
		boost::multi_index::indexed_by<
			boost::multi_index::ordered_unique< boost::multi_index::identity< Gaffer::Animation::KeyPtr > >,
			boost::multi_index::random_access<>
		>
	>;

	struct ConnectionData
	{
		explicit ConnectionData( Signals::Connection connection = Signals::Connection() );
		Signals::Connection m_connection;
		unsigned int m_count;
	};

	using CurveConnectionMap = std::map<
		const Gaffer::Animation::CurvePlug*, ConnectionData
	>;

	KeyContainer m_keys;
	CurveConnectionMap m_connections;
};

} // GafferUI

//////////////////////////////////////////////////////////////////////////
// AnimationGadget::SelectionSet implementation
//////////////////////////////////////////////////////////////////////////

AnimationGadget::SelectionSet::SelectionSet()
: m_keys()
, m_connections()
{}

AnimationGadget::SelectionSet::~SelectionSet()
{
	assert( m_connections.empty() );
}

bool AnimationGadget::SelectionSet::contains( const Gaffer::Set::Member* const member ) const
{
	return ( m_keys.find( member, MemberCompare() ) != m_keys.end() );
}

Gaffer::Set::Member *AnimationGadget::SelectionSet::member( const size_t index )
{
	return const_cast< Gaffer::Set::Member* >(
		static_cast< const AnimationGadget::SelectionSet* >( this )->member( index ) );
}

const Gaffer::Set::Member *AnimationGadget::SelectionSet::member( const size_t index ) const
{
	return m_keys.get< 1 >()[ index ].get();
}

size_t AnimationGadget::SelectionSet::size() const
{
	return static_cast< size_t >( m_keys.size() );
}

bool AnimationGadget::SelectionSet::add( const Gaffer::Animation::KeyPtr key )
{
	if( ! key || ! key->parent() )
	{
		return false;
	}

	if( m_keys.insert( key ).second )
	{
		// connect to curve key removed signal to ensure set only contains parented keys
		std::pair< CurveConnectionMap::iterator, bool > result =
			m_connections.insert( CurveConnectionMap::value_type( key->parent(), ConnectionData() ) );
		if( result.second )
		{
			result.first->second.m_connection = key->parent()->keyRemovedSignal().connect(
				boost::bind( &AnimationGadget::SelectionSet::removeInternal, this, ::_1, ::_2 ) );
		}
		++( result.first->second.m_count );
		memberAddedSignal()( this, key.get() );
		return true;
	}
	return false;
}

bool AnimationGadget::SelectionSet::remove( const Gaffer::Animation::KeyPtr key )
{
	return removeInternal( key->parent(), key );
}

bool AnimationGadget::SelectionSet::removeInternal( const Gaffer::Animation::CurvePlug* const curve, const Gaffer::Animation::KeyPtr key )
{
	KeyContainer::iterator it = m_keys.find( key );
	const bool result = ( it != m_keys.end() );
	if( result )
	{
		// disconnect from curve key removed signal if last selected key of curve is being removed
		CurveConnectionMap::iterator cit = m_connections.find( curve );
		assert( cit != m_connections.end() );
		if( --( cit->second.m_count ) == 0u )
		{
			cit->second.m_connection.disconnect();
			m_connections.erase( cit );
		}
		m_keys.erase( it );
		memberRemovedSignal()( this, key.get() );
	}
	return result;
}

void AnimationGadget::SelectionSet::clear()
{
	// remove keys from selection (signaling member removal)
	for( KeyContainer::iterator it = m_keys.begin(), itEnd = m_keys.end(); it != itEnd; )
	{
		const Gaffer::Animation::KeyPtr key = *( it );
		m_keys.erase( it++ );
		memberRemovedSignal()( this, key.get() );
	}

	// disconnect all curve connections
	for( CurveConnectionMap::iterator it = m_connections.begin(), itEnd = m_connections.end(); it != itEnd; ++it )
	{
		it->second.m_connection.disconnect();
	}
	m_connections.clear();
}

void AnimationGadget::SelectionSet::clear( const Gaffer::Animation::CurvePlug* const curve )
{
	// remove keys from selection (signaling member removal) that are parented to curve
	for( KeyContainer::iterator it = m_keys.begin(), itEnd = m_keys.end(); it != itEnd; )
	{
		if( ( *it )->parent() == curve )
		{
			const Gaffer::Animation::KeyPtr key = *( it );
			m_keys.erase( it++ );
			memberRemovedSignal()( this, key.get() );
		}
		else
		{
			++it;
		}
	}

	// disconnect curve connection
	CurveConnectionMap::iterator cit = m_connections.find( curve );
	if( cit != m_connections.end() )
	{
		cit->second.m_connection.disconnect();
		m_connections.erase( cit );
	}
}

bool AnimationGadget::SelectionSet::empty() const
{
	return m_keys.empty();
}

AnimationGadget::SelectionSet::ConnectionData::ConnectionData( const Signals::Connection connection )
: m_connection( connection )
, m_count( 0u )
{}

//////////////////////////////////////////////////////////////////////////
// AnimationGadget implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( AnimationGadget );

AnimationGadget::AnimationGadget()
: m_context( nullptr )
, m_visiblePlugs( new StandardSet() )
, m_editablePlugs( new StandardSet() )
, m_selectedKeys( new AnimationGadget::SelectionSet() )
, m_originalKeyValues()
, m_dragTangentKey( nullptr )
, m_dragTangentDirection( Animation::Direction::In )
, m_dragTangentOriginalScale( 0.0 )
, m_dragStartPosition( 0 )
, m_lastDragPosition( 0 )
, m_dragMode( DragMode::None )
, m_moveAxis( MoveAxis::Both )
, m_vertices()
, m_snappingClosestKey( nullptr )
, m_highlightedKey( nullptr )
, m_highlightedCurve( nullptr )
, m_highlightedTangentKey( nullptr )
, m_highlightedTangentDirection( Animation::Direction::In )
, m_mergeGroupId( 0 )
, m_keyPreview( false )
, m_keyPreviewLocation( 0 )
, m_xMargin( 60 )
, m_yMargin( 20 )
, m_textScale( 10 )
, m_labelPadding( 5 )
, m_frameIndicatorPreviewFrame( std::nullopt )
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
	m_selectedKeys->clear();
}

Gaffer::Set *AnimationGadget::selectedKeys()
{
	return m_selectedKeys.get();
}

const Gaffer::Set *AnimationGadget::selectedKeys() const
{
	return m_selectedKeys.get();
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

			const Imath::Color3f color3 = drivenPlugColor( curvePlug );
			const Imath::Color4f color4( color3.x, color3.y, color3.z, 1.0 );

			Animation::Key* previousKey = nullptr;
			V2f previousKeyPosition = V2f( 0 );
			bool previousKeySelected = false;

			for( Animation::Key &key : *curvePlug )
			{
				bool isHighlighted = ( & key == m_highlightedKey.get() ) || ( selecting && b.intersects( V2f( key.getTime(), key.getValue() ) ) );
				bool isSelected = m_selectedKeys->contains( &key );
				V2f keyPosition = viewportGadget->worldToRasterSpace( V3f( key.getTime(), key.getValue(), 0 ) );
				style->renderAnimationKey( keyPosition, isSelected || isHighlighted ? Style::HighlightedState : Style::NormalState, isHighlighted ? 3.0 : 2.0, &black );

				// draw the tangents
				//
				// NOTE : only draw if they are unconstrained and key or adjacent key is selected
				//        or opposite tangent is being moved or highlighted. The opposite tangent
				//        is always highlighted whilst being moved so just check highlighting.

				if( previousKey )
				{
					const Animation::Tangent& in = key.tangentIn();
					const Animation::Tangent& out = previousKey->tangentOut();

					bool tieSlopeOut, tieScaleOut;
					tieModeToBools( previousKey->getTieMode(), tieSlopeOut, tieScaleOut );
					const bool isOutHighlighted = ( m_highlightedTangentKey == previousKey ) && (
						( m_highlightedTangentDirection == Animation::Direction::Out ) || tieSlopeOut || tieScaleOut );

					if( ( isSelected || previousKeySelected || isOutHighlighted ) && ( ! out.slopeIsConstrained() || ! out.scaleIsConstrained() ) )
					{
						const V2d outPosKey = out.getPosition();
						const V2f outPosRas = viewportGadget->worldToRasterSpace( V3f( outPosKey.x, outPosKey.y, 0 ) );
						const double outSize = isOutHighlighted ? 4.0 : 2.0;
						const Box2f outBox( outPosRas - V2f( outSize ), outPosRas + V2f( outSize ) );
						style->renderLine( IECore::LineSegment3f( V3f( outPosRas.x, outPosRas.y, 0 ), V3f( previousKeyPosition.x, previousKeyPosition.y, 0 ) ),
							tieSlopeOut ? 2.0 : 1.0, &color4 );
						( tieScaleOut ) ? style->renderSolidRectangle( outBox ) : style->renderRectangle( outBox );
					}

					bool tieSlopeIn, tieScaleIn;
					tieModeToBools( key.getTieMode(), tieSlopeIn, tieScaleIn );
					const bool isInHighlighted = ( ( m_highlightedTangentKey == &key ) && (
						( m_highlightedTangentDirection == Animation::Direction::In ) || tieSlopeIn || tieScaleIn ) );

					if( ( isSelected || previousKeySelected || isInHighlighted ) && ( ! in.slopeIsConstrained() || ! in.scaleIsConstrained() ) )
					{
						const V2d inPosKey = in.getPosition();
						const V2f inPosRas = viewportGadget->worldToRasterSpace( V3f( inPosKey.x, inPosKey.y, 0 ) );
						const double inSize = isInHighlighted ? 4.0 : 2.0;
						const Box2f inBox( inPosRas - V2f( inSize ), inPosRas + V2f( inSize ) );
						style->renderLine( IECore::LineSegment3f( V3f( inPosRas.x, inPosRas.y, 0 ), V3f( keyPosition.x, keyPosition.y, 0 ) ),
							tieSlopeIn ? 2.0 : 1.0, &color4 );
						( tieScaleIn ) ? style->renderSolidRectangle( inBox ) : style->renderRectangle( inBox );
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
			renderFrameIndicator( m_frameIndicatorPreviewFrame.value(), style, /* preview = */ true );
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

void AnimationGadget::plugDirtied( Gaffer::Plug* const plug )
{
	dirty( DirtyType::Render );
}

void AnimationGadget::plugMetadataDirtied( Gaffer::Plug* const plug, const IECore::InternedString key )
{
	if( key == g_colorMetadata )
	{
		Gaffer::ValuePlug* const vplug = IECore::runTimeCast< Gaffer::ValuePlug >( plug );
		if( vplug && Gaffer::Animation::isAnimated( vplug ) )
		{
			const Gaffer::Animation::CurvePlug* const curvePlug = Gaffer::Animation::acquire( vplug );
			if( curvePlug && m_visiblePlugs->contains( curvePlug ) )
			{
				dirty( DirtyType::Render );
			}
		}
	}
}

std::string AnimationGadget::getToolTip( const IECore::LineSegment3f &line ) const
{
	std::pair< Gaffer::Animation::ConstKeyPtr, Gaffer::Animation::Direction > keyTangent = tangentAt( line );
	if( keyTangent.first )
	{
		const Gaffer::Animation::Tangent& tangent = keyTangent.first->tangent( keyTangent.second );
		std::ostringstream os;
		os.precision( 4 );
		os	<< "**" << drivenPlugName( keyTangent.first->parent() ) << "**"
			<< "  \nDirection : " << Gaffer::Animation::toString( tangent.direction() )
			<< "  \nSlope\t : " << tangent.getSlope()
			<< "  \nScale\t : " << tangent.getScale()
			;
		return os.str();
	}
	else if( const Animation::ConstKeyPtr key = keyAt( line ) )
	{
		const Gaffer::ScriptNode* const scriptNode =
			IECore::assertedStaticCast< const Gaffer::ScriptNode >( key->parent()->ancestor( (IECore::TypeId) Gaffer::ScriptNodeTypeId ) );

		std::ostringstream os;
		os.precision( 4 );
		os	<< "**" << drivenPlugName( key->parent() ) << "**"
			<< "  \nFrame : " << std::round( key->getTime() * scriptNode->framesPerSecondPlug()->getValue() )
			<< "  \nValue : " << key->getValue()
			<< "  \nInterpolation : " << Animation::toString( key->getInterpolation() )
			<< "  \nTie Mode : " << Animation::toString( key->getTieMode() )
			;
		return os.str();
	}
	else if( Animation::ConstCurvePlugPtr curvePlug = curveAt( line ) )
	{
		std::ostringstream os;
		os	<< "**" << drivenPlugName( curvePlug.get() ) << "**"
			<< "  \nExtrapolation In : " << Animation::toString( curvePlug->getExtrapolation( Animation::Direction::In ) )
			<< "  \nExtrapolation Out : " << Animation::toString( curvePlug->getExtrapolation( Animation::Direction::Out ) )
			;
		return os.str();
	}

	return "";
}

void AnimationGadget::insertKeyframe( Animation::CurvePlug *curvePlug, float time )
{
	ScriptNode *scriptNode = curvePlug->ancestor<ScriptNode>();
	UndoScope undoEnabled( scriptNode, UndoScope::Enabled, undoMergeGroup() );

	float snappedTime = snapTimeToFrame( m_context->getFramesPerSecond(), time );

	if( !curvePlug->closestKey( snappedTime, 0.004 ) ) // \todo: use proper ticks
	{
		if( const Animation::KeyPtr key = curvePlug->insertKey( snappedTime ) )
		{
			m_selectedKeys->add( key );
		}
	}
}

void AnimationGadget::insertKeyframes()
{
	if( m_editablePlugs->size() == 0 )
	{
		return;
	}

	m_selectedKeys->clear();

	for( auto &runtimeTyped : *m_editablePlugs )
	{
		insertKeyframe( IECore::runTimeCast<Animation::CurvePlug>( &runtimeTyped ), m_context->getTime() );
	}
}

void AnimationGadget::removeKeyframes()
{
	if( m_selectedKeys->empty() )
	{
		return;
	}

	auto first = m_editablePlugs->member( 0 );
	ScriptNode *scriptNode = IECore::runTimeCast<Animation::CurvePlug>( first )->ancestor<ScriptNode>();
	UndoScope undoEnabled( scriptNode, UndoScope::Enabled, undoMergeGroup() );

	for( SelectionSet::KeyContainer::iterator it = m_selectedKeys->m_keys.begin(), itEnd = m_selectedKeys->m_keys.end(); it != itEnd; )
	{
		// NOTE : SelectionSet ensures unparented keys are removed from selection so parent should be valid.
		//        The removal of the unparented key from the selection will invalidate our iterator so pre increment it.
		Animation::CurvePlug* const curve = ( *it )->parent();
		assert( curve != nullptr );
		curve->removeKey( *it++ );
	}
	assert( m_selectedKeys->m_keys.empty() );
	assert( m_selectedKeys->m_connections.empty() );
}

void AnimationGadget::removeInactiveKeyframes()
{
	if( m_selectedKeys->empty() )
	{
		return;
	}

	auto first = m_editablePlugs->member( 0 );
	ScriptNode *scriptNode = IECore::runTimeCast<Animation::CurvePlug>( first )->ancestor<ScriptNode>();
	UndoScope undoEnabled( scriptNode, UndoScope::Enabled, undoMergeGroup() );

	for( Gaffer::StandardSet::Iterator it = m_editablePlugs->begin(), itEnd = m_editablePlugs->end(); it != itEnd; ++it )
	{
		IECore::assertedStaticCast< Animation::CurvePlug >( &( *it ) )->removeInactiveKeys();
	}
}

void AnimationGadget::moveKeyframes( const V2f currentDragPosition )
{
	if( m_selectedKeys->empty() )
	{
		return;
	}

	auto first = m_editablePlugs->member( 0 );
	ScriptNode *scriptNode = IECore::runTimeCast<Animation::CurvePlug>( first )->ancestor<ScriptNode>();
	UndoScope undoEnabled( scriptNode, UndoScope::Enabled, undoMergeGroup() );

	V2f globalOffset = currentDragPosition - m_dragStartPosition;

	// Compute snapping offset used for all keys
	if( m_moveAxis != MoveAxis::Y )
	{
		// Update offset to make sure that the closest key ends up on an integer frame
		float originalTime = m_originalKeyValues[ m_snappingClosestKey.get() ].first;
		globalOffset.x = snapTimeToFrame( m_context->getFramesPerSecond(), originalTime + globalOffset.x ) - originalTime;
	}

	// move selected keys
	for( SelectionSet::KeyContainer::iterator it = m_selectedKeys->m_keys.begin(), itEnd = m_selectedKeys->m_keys.end(); it != itEnd; ++it )
	{
		Animation::KeyPtr key = *it;

		if( m_moveAxis != MoveAxis::X )
		{
			key->setValue( m_originalKeyValues[ key.get() ].second + globalOffset.y );
		}

		// Compute new time and make sure that we eliminate floating point precision
		// issues that could cause keys landing a little bit off integer frames for
		// keys that are meant to snap to frames.
		float newTime = m_originalKeyValues[ key.get() ].first + globalOffset.x;
		newTime = snapTimeToFrame( m_context->getFramesPerSecond(), newTime, 0.004 );

		if( m_moveAxis != MoveAxis::Y )
		{
			key->setTime( newTime );
		}
	}
}

void AnimationGadget::moveTangent( const Imath::V2f currentDragOffset )
{
	if( ! m_dragTangentKey || ( m_moveAxis == MoveAxis::Undefined ) )
	{
		return;
	}

	// check tangent usage
	//
	// NOTE : when the move axis is MoveAxis::X we only change the tangent's scale.
	//        when the move axis is MoveAxis::Y we only change the tangent's slope.
	//
	// NOTE : current interpolators constrain scale or both scale and slope.

	Animation::Tangent& tangent = m_dragTangentKey->tangent( m_dragTangentDirection );

	if( ( m_moveAxis == MoveAxis::X ) && tangent.scaleIsConstrained() )
	{
		return;
	}
	else if( ( m_moveAxis == MoveAxis::Y ) && tangent.slopeIsConstrained() )
	{
		return;
	}
	else if( ( m_moveAxis == MoveAxis::Both ) && tangent.slopeIsConstrained() )
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
		{
			// NOTE : there may be a non-uniform zoom so transform to raster space before projecting
			//        drag offset onto tangent.

			if( tangent.getScale() == 0.0 ){ tangent.setScale( 1.0 ); }
			const Imath::V2d tp = tangent.getPosition();
			const ViewportGadget* const viewportGadget = ancestor<ViewportGadget>();
			const Imath::V2f tpr = viewportGadget->worldToRasterSpace( V3f( tp.x, tp.y, 0 ) );
			const Imath::V2f kpr = viewportGadget->worldToRasterSpace( V3f( tangent.key().getTime(), tangent.key().getValue(), 0 ) );
			const Imath::V2f dpr = viewportGadget->worldToRasterSpace( V3f( currentDragOffset.x, currentDragOffset.y, 0.0 ) );
			const Imath::V2f tvr = ( tpr - kpr ).normalized();

			Imath::V3f dp;
			viewportGadget->rasterToWorldSpace( kpr + ( tvr * ( ( dpr - kpr ) ^ tvr ) ) ).intersect(
				Plane3f( V3f( 0.0, 0.0, 1.0 ), 0.0 ), dp );
			tangent.setScaleFromPosition( Imath::V2d( dp.x, dp.y ) );
			break;
		}
		case MoveAxis::Y:
			tangent.setSlopeFromPosition( currentDragOffset );
			tangent.setScale( m_dragTangentOriginalScale );
			break;
		case MoveAxis::Both:
			( tangent.scaleIsConstrained() )
				? tangent.setSlopeFromPosition( currentDragOffset )
				: tangent.setPosition( currentDragOffset );
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

	// try to frame to selected keys
	for( SelectionSet::KeyContainer::iterator it = m_selectedKeys->m_keys.begin(), itEnd = m_selectedKeys->m_keys.end(); it != itEnd; ++it )
	{
		b.extendBy( V3f( ( *it )->getTime(), ( *it )->getValue(), 0 ) );
	}

	// try to frame to editable curves
	if( b.isEmpty() )
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

	// try to frame to visible curves
	if( b.isEmpty() )
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

	// set default framing as last resort
	if( b.isEmpty() )
	{
		b = Box3f( V3f( -1, -1, 0), V3f( 1, 1, 0 ) );
	}

	assert( ! b.isEmpty() );

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
		m_context->setFrame( m_frameIndicatorPreviewFrame.value() );
		m_frameIndicatorPreviewFrame = std::nullopt;
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
			if( ( m_selectedKeys->size() != static_cast< size_t >( 1 ) ) ||
				( m_selectedKeys->m_keys.get< 1 >()[ 0 ] != key ) )
			{
				m_selectedKeys->clear();
				m_selectedKeys->add( key );
			}
		}
		else
		{
			// toggle selection
			if( ! m_selectedKeys->remove( key ) )
			{
				m_selectedKeys->add( key );
			}
		}
	}
	else if( Animation::CurvePlugPtr curvePlug = curveAt( event.line ) )
	{
		bool controlHeld = event.modifiers & DragDropEvent::Control;

		if( controlHeld ) // insert a keyframe
		{
			m_selectedKeys->clear();
			insertKeyframe( curvePlug.get(), i.x );
			++m_mergeGroupId;
			m_keyPreview = false;
		}
		else
		{
			if( m_editablePlugs->contains( curvePlug.get() ) ) // select all its keys
			{
				for( Animation::Key &key : *curvePlug )
				{
					m_selectedKeys->add( &key );
				}
			}
			else // try to make it editable
			{
				bool shiftHeld = event.modifiers & DragDropEvent::Shift;
				if( !shiftHeld )
				{
					m_editablePlugs->clear();
					m_selectedKeys->clear();
				}

				m_editablePlugs->add( curvePlug.get() );
			}
		}
	}
	else // background
	{
		m_selectedKeys->clear();
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
		std::pair<Animation::KeyPtr, Animation::Direction> tangent = tangentAt( event.line );

		if( tangent.first )
		{
			Animation::Tangent& t = tangent.first->tangent( tangent.second );
			m_dragTangentOriginalScale = t.getScale();
			m_dragTangentKey = tangent.first;
			m_dragTangentDirection = tangent.second;
			m_highlightedTangentKey = m_dragTangentKey;
			m_highlightedTangentDirection = m_dragTangentDirection;
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
			if( ! m_selectedKeys->contains( key.get() ) )
			{
				m_selectedKeys->clear();
				m_selectedKeys->add( key );
			}

			removeInactiveKeyframes();
			m_dragMode = DragMode::Moving;
		}
		else if( ( onTimeAxis( event.line ) && ! onValueAxis( event.line ) ) || frameIndicatorUnderMouse( event.line ) )
		{
			m_dragMode = DragMode::MoveFrame;
			m_frameIndicatorPreviewFrame = std::nullopt;
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
		for( SelectionSet::KeyContainer::iterator it = m_selectedKeys->m_keys.begin(), itEnd = m_selectedKeys->m_keys.end(); it != itEnd; ++it )
		{
			m_originalKeyValues[ ( *it ).get() ] = std::make_pair( ( *it )->getTime(), ( *it )->getValue() );
		}
	}

	if( m_dragMode == DragMode::Selecting )
	{
		if( !shiftHeld )
		{
			m_selectedKeys->clear();
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

	updateHighlightingAndPreview( event );

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

	if( m_dragMode == DragMode::Moving && ! m_selectedKeys->empty() )
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

		if( m_moveAxis != MoveAxis::Y && !m_snappingClosestKey )
		{
			// determine position of selected keyframe that is closest to pointer
			// \todo: move into separate function, ideally consolidate with Animation::CurvePlug::closestKey?
			auto rightIt = m_selectedKeys->m_keys.lower_bound( Animation::KeyPtr( new Animation::Key(i.x, 0) ) );

			if( rightIt == m_selectedKeys->m_keys.end() )
			{
				m_snappingClosestKey = *( m_selectedKeys->m_keys.rbegin() );
			}
			else if( (*rightIt)->getTime() == i.x || rightIt == m_selectedKeys->m_keys.begin() )
			{
				m_snappingClosestKey = *rightIt;
			}
			else
			{
				auto leftIt = std::prev( rightIt );
				m_snappingClosestKey = std::abs( i.x - (*leftIt)->getTime() ) < std::abs( i.x - (*rightIt)->getTime() ) ? *leftIt : *rightIt;
			}
		}

		moveKeyframes( V2f( i.x, i.y ) );
	}

	if( m_dragMode == DragMode::MoveTangent && m_dragTangentKey )
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
				if( b.intersects( V2f( key.getTime(), key.getValue() ) ) )
				{
					m_selectedKeys->add( &key );
				}
			}
		}

		break;
	}
	case DragMode::Moving :
	{
		removeInactiveKeyframes();
		m_originalKeyValues.clear();
		m_mergeGroupId++;
		break;
	}
	case DragMode::MoveTangent :
	{
		m_dragTangentKey.reset();
		m_highlightedTangentKey.reset();
		m_dragTangentOriginalScale = 0.0;
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

	updateHighlightingAndPreview( event );

	dirty( DirtyType::Render );

	return true;
}

bool AnimationGadget::leave()
{
	if( m_frameIndicatorPreviewFrame )
	{
		m_frameIndicatorPreviewFrame = std::nullopt;
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

bool AnimationGadget::onTimeAxis( const IECore::LineSegment3f& line ) const
{
	Imath::V3f i;
	if( ! line.intersect( Imath::Plane3f( Imath::V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}

	const ViewportGadget* const viewportGadget = ancestor<ViewportGadget>();
	return viewportGadget->gadgetToRasterSpace( i, this ).y >= ( viewportGadget->getViewport().y - m_yMargin );
}

bool AnimationGadget::onValueAxis( const IECore::LineSegment3f& line ) const
{
	Imath::V3f i;
	if( ! line.intersect( Imath::Plane3f( Imath::V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}

	const ViewportGadget* const viewportGadget = ancestor<ViewportGadget>();
	return viewportGadget->gadgetToRasterSpace( i, this ).x <= m_xMargin;
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

std::pair<Gaffer::Animation::KeyPtr, Gaffer::Animation::Direction> AnimationGadget::tangentAt( const IECore::LineSegment3f &position )
{
	const std::pair<Animation::ConstKeyPtr, Animation::Direction> result =
		static_cast< const AnimationGadget* >( this )->tangentAt( position );
	return std::pair<Animation::KeyPtr, Animation::Direction>(
		const_cast< Animation::Key* >( result.first.get() ), result.second );
}

std::pair<Gaffer::Animation::ConstKeyPtr, Gaffer::Animation::Direction> AnimationGadget::tangentAt( const IECore::LineSegment3f &position ) const
{
	std::pair<Animation::ConstKeyPtr, Animation::Direction> result( nullptr, Animation::Direction::In );

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

			++name; // NOTE : Name 0 is invalid, so start at 1, for each curve this skips in tangent of first key

			const Animation::Key* previousKey = nullptr;
			bool previousKeySelected = false;
			for( Animation::Key &key : *curvePlug )
			{
				const bool isSelected = m_selectedKeys->contains( &key );
				keys.emplace_back( &key );

				if( previousKey )
				{
					const Animation::Tangent& in = key.tangentIn();
					const Animation::Tangent& out = previousKey->tangentOut();

					if( ( isSelected || previousKeySelected ) && ( ! out.slopeIsConstrained() || ! out.scaleIsConstrained() ) )
					{
						const V2d outPosKey = out.getPosition();
						const V2f outPosRas = viewportGadget->worldToRasterSpace( V3f( outPosKey.x, outPosKey.y, 0 ) );
						selector->loadName( name );
						style->renderSolidRectangle( Box2f( outPosRas - V2f( 4.0 ), outPosRas + V2f( 4.0 ) ) ); // slightly bigger for easier selection
					}

					++name;

					if( ( isSelected || previousKeySelected ) && ( ! in.slopeIsConstrained() || ! in.scaleIsConstrained() ) )
					{
						const V2d inPosKey = in.getPosition();
						const V2f inPosRas = viewportGadget->worldToRasterSpace( V3f( inPosKey.x, inPosKey.y, 0 ) );
						selector->loadName( name );
						style->renderSolidRectangle( Box2f( inPosRas - V2f( 4.0 ), inPosRas + V2f( 4.0 ) ) ); // slightly bigger for easier selection
					}

					++name;
				}

				previousKey = & key;
				previousKeySelected = isSelected;
			}

			++name; // NOTE : for each curve this skips out tangent of last key
		}
	}

	if( ! selection.empty() )
	{
		result.first = keys[ ( selection[0].name ) / 2 ];
		result.second = static_cast< Animation::Direction >( ( selection[0].name ) % 2 );
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
	if( Node* const node = curvePlug->node() )
	{
		node->plugDirtiedSignal().connect( boost::bind( &AnimationGadget::plugDirtied, this, ::_1 ) );
	}

	// \todo: should only connect if we don't monitor this node yet
	if( Node* const node = drivenPlug( curvePlug )->node() )
	{
		Gaffer::Metadata::plugValueChangedSignal( node ).connect(
			boost::bind( &AnimationGadget::plugMetadataDirtied, this, ::_1, ::_2 ) );
	}

	dirty( DirtyType::Render );
}

void AnimationGadget::visiblePlugRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	dirty( DirtyType::Render );
}

void AnimationGadget::editablePlugAdded( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	dirty( DirtyType::Render );
}

void AnimationGadget::editablePlugRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	const Animation::CurvePlug* const curvePlug = IECore::runTimeCast< Animation::CurvePlug >( member );
	if( curvePlug )
	{
		m_selectedKeys->clear( curvePlug );
	}

	dirty( DirtyType::Render );
}

void AnimationGadget::renderCurve( const Animation::CurvePlug *curvePlug, const Style *style ) const
{
	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	ViewportGadget::RasterScope rasterScope( viewportGadget );

	// compute viewport time bounds in gadget space
	const int rx = viewportGadget->getViewport().x;
	const float tmin = viewportGadget->rasterToWorldSpace( V2f( m_xMargin, 0.f ) ).p0.x;
	const float tmax = viewportGadget->rasterToWorldSpace( V2f( rx, 0.f ) ).p0.x;
	const float unitPerPx = ( tmax - tmin ) / ( rx - m_xMargin );

	Animation::ConstKeyPtr previousKey = nullptr;
	V2f previousKeyPosition( 0 );

	const Style::State styleState = ( curvePlug == m_highlightedCurve ) ? Style::HighlightedState : Style::NormalState;
	const Imath::Color3f color3 = drivenPlugColor( curvePlug );

	// draw extrapolated curve (direction in)
	// NOTE : generate vertices starting at extrapolation key, so that any pattern applied
	//        to the curve extends from the extrapolation key.
	const Gaffer::Animation::Key* const keyIn = curvePlug->getExtrapolationKey( Gaffer::Animation::Direction::In );
	if( keyIn && ( keyIn->getTime() > tmin ) )
	{
		m_vertices.clear();
		switch( curvePlug->getExtrapolation( Gaffer::Animation::Direction::In ) )
		{
			case Gaffer::Animation::Extrapolation::Constant:
			case Gaffer::Animation::Extrapolation::Linear:
				m_vertices.push_back( viewportGadget->worldToRasterSpace( V3f( keyIn->getTime(), keyIn->getValue(), 0 ) ) );
				m_vertices.push_back( viewportGadget->worldToRasterSpace( V3f( tmin, curvePlug->evaluate( tmin ), 0 ) ) );
				break;
			default:
				evaluateCurve( curvePlug, std::min( tmax, keyIn->getTime() ), tmin, unitPerPx, viewportGadget, m_vertices );
				break;
		}
		style->renderAnimationCurve( m_vertices, /* inKeyRange = */ false, styleState, &color3 );
	}

	// draw the animation curve between keys
	m_vertices.clear();
	for( const auto &key : *curvePlug )
	{
		V2f keyPosition = viewportGadget->worldToRasterSpace( V3f( key.getTime(), key.getValue(), 0 ) );

		if( previousKey && ( keyPosition.x >= m_xMargin ) && ( previousKeyPosition.x <= rx ) )
		{
			if( m_vertices.empty() )
				m_vertices.push_back( previousKeyPosition );

			switch( previousKey->getInterpolation() )
			{
				case Gaffer::Animation::Interpolation::Constant:
					m_vertices.emplace_back( keyPosition.x, previousKeyPosition.y );
					m_vertices.push_back( keyPosition );
					break;
				case Gaffer::Animation::Interpolation::ConstantNext:
					m_vertices.emplace_back( previousKeyPosition.x, keyPosition.y );
					m_vertices.push_back( keyPosition );
					break;
				case Gaffer::Animation::Interpolation::Linear:
					m_vertices.push_back( keyPosition );
					break;
				default:
					evaluateCurve( curvePlug, std::max( tmin, previousKey->getTime() ), std::min( tmax, key.getTime() ),
						unitPerPx, viewportGadget, m_vertices );
					break;
			}
		}

		previousKey = &key;
		previousKeyPosition = keyPosition;
	}
	style->renderAnimationCurve( m_vertices, /* inKeyRange = */ true, styleState, &color3 );

	// draw extrapolated curve (direction out)
	// NOTE : generate vertices starting at extrapolation key, so that any pattern applied
	//        to the curve extends from the extrapolation key.
	const Gaffer::Animation::Key* const keyOut = curvePlug->getExtrapolationKey( Gaffer::Animation::Direction::Out );
	if( keyOut && ( keyOut->getTime() < tmax ) )
	{
		m_vertices.clear();
		switch( curvePlug->getExtrapolation( Gaffer::Animation::Direction::Out ) )
		{
			case Gaffer::Animation::Extrapolation::Constant:
			case Gaffer::Animation::Extrapolation::Linear:
				m_vertices.push_back( viewportGadget->worldToRasterSpace( V3f( keyOut->getTime(), keyOut->getValue(), 0 ) ) );
				m_vertices.push_back( viewportGadget->worldToRasterSpace( V3f( tmax, curvePlug->evaluate( tmax ), 0 ) ) );
				break;
			default:
				evaluateCurve( curvePlug, std::max( tmin, keyOut->getTime() ), tmax, unitPerPx, viewportGadget, m_vertices );
				break;
		}
		style->renderAnimationCurve( m_vertices, /* inKeyRange = */ false, styleState, &color3 );
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
		m_keyPreview = false;
		return;
	}

	float snappedTime = snapTimeToFrame( m_context->getFramesPerSecond(), time );
	float value = curvePlug->evaluate( snappedTime );
	m_keyPreviewLocation = V3f( snappedTime, value, 0 );
}

void AnimationGadget::updateHighlightingAndPreview( const ButtonEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return;
	}

	if( onTimeAxis( event.line ) && ! onValueAxis( event.line ) )
	{
		m_frameIndicatorPreviewFrame = static_cast<int>( round( timeToFrame( m_context->getFramesPerSecond(), i.x ) ) );
	}
	else
	{
		m_frameIndicatorPreviewFrame = std::nullopt;
	}

	std::pair<Gaffer::Animation::KeyPtr, Gaffer::Animation::Direction> tangent = tangentAt( event.line );

	if( tangent.first )
	{
		m_highlightedTangentKey = tangent.first;
		m_highlightedTangentDirection = tangent.second;
		m_highlightedKey = nullptr;
		m_highlightedCurve = nullptr;
	}
	else if( Animation::KeyPtr key = keyAt( event.line ) )
	{
		m_highlightedKey = key;
		m_highlightedTangentKey = nullptr;
		m_highlightedCurve = nullptr;
	}
	else
	{
		if( m_highlightedKey )
		{
			m_highlightedKey = nullptr;
		}

		if( m_highlightedTangentKey )
		{
			m_highlightedTangentKey = nullptr;
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

	return;
}
