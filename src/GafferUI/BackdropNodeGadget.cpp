//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/BackdropNodeGadget.h"

#include "GafferUI/GraphGadget.h"
#include "GafferUI/ImageGadget.h"
#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/UndoScope.h"

#include "IECore/BoxOps.h"
#include "IECore/NullObject.h"

#include "boost/algorithm/string.hpp"
#include "boost/bind.hpp"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

namespace
{

void titleAndDescriptionFromPlugs( const StringPlug *titlePlug, const StringPlug *descriptionPlug,
	std::string &title, std::string &description )
{
	const auto script = titlePlug->ancestor<ScriptNode>();
	const Context *context = script ? script->context() : nullptr;
	Context::Scope scope( context );

	title = "ERROR : Getting title";
	try
	{
		title = titlePlug->getValue();
		description = descriptionPlug->getValue();
		if( context )
		{
			title = context->substitute( title );
			description = context->substitute( description );
		}
	}
	catch( const std::exception &e )
	{
		description = std::string( "ERROR:\n" ) + e.what();
	}
}

const float g_margin = 3.0f;
IECore::InternedString g_boundPlugName( "__uiBound" );
IECore::InternedString g_colorKey( "nodeGadget:color" );
Box2f g_defaultBound( V2f( -10 ), V2f( 10 ) );

} // namespace

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( BackdropNodeGadget );

BackdropNodeGadget::NodeGadgetTypeDescription<BackdropNodeGadget> BackdropNodeGadget::g_nodeGadgetTypeDescription( Gaffer::Backdrop::staticTypeId() );

BackdropNodeGadget::BackdropNodeGadget( Gaffer::NodePtr node )
	:	NodeGadget( node ), m_hovered( false ), m_horizontalDragEdge( 0 ), m_verticalDragEdge( 0 ), m_mergeGroupId( 0 )
{
	if( !runTimeCast<Backdrop>( node ) )
	{
		throw Exception( "BackdropNodeGadget requires a Backdrop" );
	}

	node->plugDirtiedSignal().connect( boost::bind( &BackdropNodeGadget::plugDirtied, this, ::_1 ) );
	if( auto *script = node->scriptNode() )
	{
		script->context()->changedSignal().connect(
			boost::bind( &BackdropNodeGadget::contextChanged, this )
		);
	}

	mouseMoveSignal().connect( boost::bind( &BackdropNodeGadget::mouseMove, this, ::_1, ::_2 ) );
	buttonPressSignal().connect( boost::bind( &BackdropNodeGadget::buttonPress, this, ::_1, ::_2 ) );
	dragBeginSignal().connect( boost::bind( &BackdropNodeGadget::dragBegin, this, ::_1, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &BackdropNodeGadget::dragEnter, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &BackdropNodeGadget::dragMove, this, ::_1, ::_2 ) );
	dragEndSignal().connect( boost::bind( &BackdropNodeGadget::dragEnd, this, ::_1, ::_2 ) );
	leaveSignal().connect( boost::bind( &BackdropNodeGadget::leave, this, ::_1, ::_2 ) );

	Metadata::nodeValueChangedSignal( node.get() ).connect( boost::bind( &BackdropNodeGadget::nodeMetadataChanged, this, ::_2 ) );

	updateUserColor();
}

BackdropNodeGadget::~BackdropNodeGadget()
{
}

std::string BackdropNodeGadget::getToolTip( const IECore::LineSegment3f &line ) const
{
	std::string result = Gadget::getToolTip( line );
	if( result.size() )
	{
		return result;
	}

	const Backdrop *backdrop = static_cast<const Backdrop *>( node() );
	std::string title, description;
	titleAndDescriptionFromPlugs( backdrop->titlePlug(), backdrop->descriptionPlug(), title, description );

	if( !title.size() && !description.size() )
	{
		return NodeGadget::getToolTip( line );
	}

	if( title.size() )
	{
		result += "# " + title;
	}
	if( description.size() )
	{
		if( result.size() )
		{
			result += "\n\n";
		}
		result += description;
	}

	return result;
}

void BackdropNodeGadget::setBound( const Imath::Box2f &bound )
{
	acquireBoundPlug()->setValue( bound );
}

Imath::Box2f BackdropNodeGadget::getBound() const
{
	// Cast is OK because we won't make the plug if it's not there,
	// and we don't edit the plug at all if it is.
	if( auto p = const_cast<BackdropNodeGadget *>( this )->acquireBoundPlug( /* createIfMissing = */ false ) )
	{
		return p->getValue();
	}
	return g_defaultBound;
}

void BackdropNodeGadget::frame( const std::vector<Gaffer::Node *> &nodes )
{
	GraphGadget *graph = ancestor<GraphGadget>();
	if( !graph )
	{
		return;
	}

	Box3f b;
	for( std::vector<Node *>::const_iterator it = nodes.begin(), eIt = nodes.end(); it != eIt; ++it )
	{
		NodeGadget *nodeGadget = graph->nodeGadget( *it );
		if( nodeGadget )
		{
			b.extendBy( nodeGadget->transformedBound( nullptr ) );
		}
	}

	if( b.isEmpty() )
	{
		return;
	}

	graph->setNodePosition( node(), V2f( b.center().x, b.center().y ) );

	V2f s( b.size().x / 2.0f, b.size().y / 2.0f );

	setBound(
		Box2f(
			V2f( -s ) - V2f( g_margin ),
			V2f( s ) + V2f( g_margin + 2.0f * g_margin )
		)
	);
}

void BackdropNodeGadget::framed( std::vector<Gaffer::Node *> &nodes ) const
{
	const Node *nodeParent = node()->parent<Node>();
	const GraphGadget *graphGadget = ancestor<GraphGadget>();
	if( !nodeParent || !graphGadget )
	{
		return;
	}

	const Box3f bound3 = transformedBound( graphGadget );
	const Box2f bound2( V2f( bound3.min.x, bound3.min.y ), V2f( bound3.max.x, bound3.max.y ) );

	for( Node::Iterator it( nodeParent ); !it.done(); ++it )
	{
		if( node() == it->get() )
		{
			continue;
		}
		if( const NodeGadget *nodeGadget = graphGadget->nodeGadget( it->get() ) )
		{
			const Box3f nodeBound3 = nodeGadget->transformedBound( graphGadget );
			const Box2f nodeBound2( V2f( nodeBound3.min.x, nodeBound3.min.y ), V2f( nodeBound3.max.x, nodeBound3.max.y ) );
			if( boxContains( bound2, nodeBound2 ) )
			{
				nodes.push_back( it->get() );
			}
		}
	}
}

Imath::Box3f BackdropNodeGadget::bound() const
{
	const Box2f b = getBound();
	return Box3f( V3f( b.min.x, b.min.y, 0.0f ), V3f( b.max.x, b.max.y, 0.0f ) );
}

void BackdropNodeGadget::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	if( layer != GraphLayer::Backdrops )
	{
		return;
	}

	// this is our bound in gadget space
	Box2f bound = getBound();

	// but because we're going to draw our contents at an arbitrary scale,
	// we need to compute a modified bound which will be in the right place
	// following scaling.

	const Backdrop *backdrop = static_cast<const Backdrop *>( node() );
	const float scale = backdrop->scalePlug()->getValue();

	bound.min /= scale;
	bound.max /= scale;

	glPushMatrix();

	glScalef( scale, scale, scale );

	const Box3f titleCharacterBound = style->characterBound( Style::HeadingText );
	const float titleBaseline = bound.max.y - g_margin - titleCharacterBound.max.y;

	if( isSelectionRender( reason ) )
	{
		// when selecting we render in a simplified form.
		// we only draw a thin strip around the edge of the backdrop
		// to allow the edges to be grabbed for dragging, and a strip
		// at the top to allow the title header to be grabbed for moving
		// around. leaving the main body of the backdrop as a hole is
		// necessary to allow the GraphGadget to continue to perform
		// drag selection on the nodes on top of the backdrop.

		const float width = hoverWidth() / scale;

		style->renderSolidRectangle( Box2f( bound.min, V2f( bound.min.x + width, bound.max.y ) ) ); // left
		style->renderSolidRectangle( Box2f( V2f( bound.max.x - width, bound.min.y ), bound.max ) ); // right
		style->renderSolidRectangle( Box2f( bound.min, V2f( bound.max.x, bound.min.y + width ) ) ); // bottom
		style->renderSolidRectangle( Box2f( V2f( bound.min.x, bound.max.y - width ), bound.max ) ); // top
		style->renderSolidRectangle( Box2f( V2f( bound.min.x, titleBaseline - g_margin ), bound.max ) ); // heading
	}
	else
	{
		// normal drawing mode

		style->renderBackdrop( bound, getHighlighted() ? Style::HighlightedState : Style::NormalState, m_userColor.get_ptr() );

		std::string title, description;
		titleAndDescriptionFromPlugs( backdrop->titlePlug(), backdrop->descriptionPlug(), title, description );

		if( title.size() )
		{
			Box3f titleBound = style->textBound( Style::HeadingText, title );
			glPushMatrix();
				glTranslatef( bound.center().x - titleBound.size().x / 2.0f, titleBaseline, 0.0f );
				style->renderText( Style::HeadingText, title );
			glPopMatrix();
		}

		if( m_hovered )
		{
			style->renderHorizontalRule(
				V2f( bound.center().x, titleBaseline - g_margin / 2.0f ),
				bound.size().x - g_margin * 2.0f,
				Style::HighlightedState
			);
		}

		Box2f textBound = bound;
		textBound.min += V2f( g_margin );
		textBound.max = V2f( textBound.max.x - g_margin, titleBaseline - g_margin );
		if( textBound.hasVolume() )
		{
			style->renderWrappedText( Style::BodyText, description, textBound );
		}
	}

	glPopMatrix();
}

unsigned BackdropNodeGadget::layerMask() const
{
	return (unsigned)GraphLayer::Backdrops;
}

Imath::Box3f BackdropNodeGadget::renderBound() const
{
	// This doesn't take into account the possibility that the title sticks out beyond the backdrop,
	// meaning that you could see the part of the title sticking out of a Backdrop disappear when the Backdrop
	// goes off-screen.
	//
	// To fix this, we could either take into account style()->textBound, scaling, and the title text here,
	// or we could just limit the title to only rendering inside the Backdrop

	return bound();
}

void BackdropNodeGadget::contextChanged()
{
	// Title and description may depend on the context
	dirty( DirtyType::Render );
}

void BackdropNodeGadget::plugDirtied( const Gaffer::Plug *plug )
{
	const Backdrop *backdrop = static_cast<const Backdrop *>( node() );
	if(
		plug == backdrop->titlePlug() ||
		plug == backdrop->scalePlug() ||
		plug == backdrop->descriptionPlug()
	)
	{
		dirty( DirtyType::Render );
	}
	else if(
		plug == acquireBoundPlug( /* createIfMissing = */ false )
	)
	{
		dirty( DirtyType::Bound );
	}
}

bool BackdropNodeGadget::mouseMove( Gadget *gadget, const ButtonEvent &event )
{
	if( MetadataAlgo::readOnly( node() ) )
	{
		return false;
	}

	int h, v;
	hoveredEdges( event, h, v );
	if( h && v )
	{
		Pointer::setCurrent( h * v > 0 ? "moveDiagonallyUp" : "moveDiagonallyDown" );
	}
	else if( h )
	{
		Pointer::setCurrent( "moveHorizontally" );
	}
	else if( v )
	{
		Pointer::setCurrent( "moveVertically" );
	}
	else
	{
		Pointer::setCurrent( "" );
	}

	bool newHovered = !(h || v);
	if( newHovered != m_hovered )
	{
		m_hovered = newHovered;
		dirty( DirtyType::Render );
	}

	return true;
}

bool BackdropNodeGadget::buttonPress( Gadget *gadget, const ButtonEvent &event )
{
	if( MetadataAlgo::readOnly( node() ) )
	{
		return false;
	}

	if( event.buttons != ButtonEvent::Left )
	{
		return false;
	}

	hoveredEdges( event, m_horizontalDragEdge, m_verticalDragEdge );

	if( m_horizontalDragEdge || m_verticalDragEdge )
	{
		return true;
	}

	// the GraphGadget will use the click for performing selection
	return false;
}

IECore::RunTimeTypedPtr BackdropNodeGadget::dragBegin( Gadget *gadget, const DragDropEvent &event )
{
	return IECore::NullObject::defaultNullObject();
}

bool BackdropNodeGadget::dragEnter( Gadget *gadget, const DragDropEvent &event )
{
	return event.sourceGadget == this;
}

bool BackdropNodeGadget::dragMove( Gadget *gadget, const DragDropEvent &event )
{
	Box2f b = getBound();

	if( m_horizontalDragEdge == -1 )
	{
		b.min.x = std::min( event.line.p0.x, b.max.x - g_margin * 4.0f );
	}
	else if( m_horizontalDragEdge == 1 )
	{
		b.max.x = std::max( event.line.p0.x, b.min.x + g_margin * 4.0f );
	}

	if( m_verticalDragEdge == -1 )
	{
		b.min.y = std::min( event.line.p0.y, b.max.y - g_margin * 4.0f);
	}
	else if( m_verticalDragEdge == 1 )
	{
		b.max.y = std::max( event.line.p0.y, b.min.y + g_margin * 4.0f);
	}

	const std::string mergeGroup = boost::str( boost::format( "BackdropNodeGadget%1%%2%" ) % this % m_mergeGroupId );
	UndoScope undoScope( node()->scriptNode(), UndoScope::Enabled, mergeGroup );
	setBound( b );
	return true;
}

bool BackdropNodeGadget::dragEnd( Gadget *gadget, const DragDropEvent &event )
{
	Pointer::setCurrent( "" );
	m_mergeGroupId++;
	return true;
}

void BackdropNodeGadget::leave( Gadget *gadget, const ButtonEvent &event )
{
	Pointer::setCurrent( "" );
	m_hovered = false;
	dirty( DirtyType::Render );
}

float BackdropNodeGadget::hoverWidth() const
{
	// we want the selectable strip to be a constant width in raster space
	// rather than in gadget space.
	const ViewportGadget *viewport = ancestor<ViewportGadget>();
	const V3f p0 = viewport->rasterToGadgetSpace( V2f( 0 ), this ).p0;
	const V3f p1 = viewport->rasterToGadgetSpace( V2f( 0, 5.0f ), this ).p0;
	return ( p0 - p1 ).length();
}

void BackdropNodeGadget::hoveredEdges( const ButtonEvent &event, int &horizontal, int &vertical ) const
{
	const Backdrop *backdrop = static_cast<const Backdrop *>( node() );
	const float scale = backdrop->scalePlug()->getValue();

	const Box2f b = getBound();

	const V3f &p = event.line.p0;
	const float width = hoverWidth() * 2.0f;

	horizontal = vertical = 0;

	if( fabs( p.x - b.min.x ) < width )
	{
		horizontal = -1;
	}
	else if( fabs( p.x - b.max.x ) < width )
	{
		horizontal = 1;
	}

	if( fabs( p.y - b.min.y ) < width )
	{
		vertical = -1;
	}
	else if( fabs( p.y - b.max.y ) < std::min( width, 0.25f * g_margin * scale ) )
	{
		vertical = 1;
	}
}

Gaffer::Box2fPlug *BackdropNodeGadget::acquireBoundPlug( bool createIfMissing )
{
	auto existingPlug = node()->getChild<Box2fPlug>( g_boundPlugName );
	if( existingPlug || !createIfMissing )
	{
		return existingPlug;
	}

	Box2fPlugPtr newPlug = new Box2fPlug(
		g_boundPlugName,
		Plug::In,
		g_defaultBound,
		Plug::Default | Plug::Dynamic
	);
	node()->addChild( newPlug );
	return newPlug.get();
}

void BackdropNodeGadget::nodeMetadataChanged( IECore::InternedString key )
{
	if( key == g_colorKey )
	{
		if( updateUserColor() )
		{
			dirty( DirtyType::Render );
		}
	}
}

bool BackdropNodeGadget::updateUserColor()
{
	boost::optional<Color3f> c;
	if( IECore::ConstColor3fDataPtr d = Metadata::value<IECore::Color3fData>( node(), g_colorKey ) )
	{
		c = d->readable();
	}

	if( c == m_userColor )
	{
		return false;
	}

	m_userColor = c;
	return true;
}
