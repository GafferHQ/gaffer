//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Murray Stevenson. All rights reserved.
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

#include "DragEditGadget.h"

#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"

#include "IECore/NullObject.h"

#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Group.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/ShaderStateComponent.h"
#include "IECoreGL/TextureLoader.h"

#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace GafferUI;
using namespace Gaffer;
using namespace IECore;
using namespace IECoreGL;
using namespace Imath;
using namespace boost::placeholders;
using namespace std;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

const float g_cutLineRadius = 4.0f;
const Color4f g_cutLineColor = Color4f( 0.7f, 0.2f, 0.1f, 0.375f );

std::vector<ConnectionGadget*> editableConnectionGadgetsAtLine( const ViewportGadget *viewportGadget, const LineSegment2f &line, const float radius, const bool includeEndpoint )
{
	std::unordered_set<Gadget*> gadgets;

	int samples = 1;
	float step = 0.0f;
	// Break long line segments into multiple smaller gadgetsAt tests.
	// If this proves to be expensive for long drags, we could potentially
	// scale the samples based on the line angle.
	const float lineLength = line.length();
	if( lineLength > radius )
	{
		samples = ceil( lineLength / ( radius * 2.0f ) );
		step = 1.0f / (float)samples;
		samples += includeEndpoint;
	}

	const V2f padding = V2f( radius );
	for( int i = 0; i < samples; ++i )
	{
		const V2f p = line( i * step );
		const std::vector<Gadget*> gadgetsAtBox = viewportGadget->gadgetsAt( Box2f( p - padding, p + padding ), GraphLayer::Connections );
		gadgets.insert( gadgetsAtBox.begin(), gadgetsAtBox.end() );
	}

	std::vector<ConnectionGadget*> connectionGadgets;
	for( const auto &gadget : gadgets )
	{
		ConnectionGadget *connectionGadget = runTimeCast<ConnectionGadget>( gadget );
		if( !connectionGadget )
		{
			connectionGadget = gadget->ancestor<ConnectionGadget>();
		}
		if(
			connectionGadget && !Gaffer::MetadataAlgo::readOnly( connectionGadget->dstNodule()->plug() ) &&
			( !connectionGadget->srcNodule() || !Gaffer::MetadataAlgo::readOnly( connectionGadget->srcNodule()->plug() ) )
		)
		{
			connectionGadgets.push_back( connectionGadget );
		}
	}

	return connectionGadgets;
}

const char *translucentConstantFragSource()
{
	return
		"#version 120\n"
		""
		"#if __VERSION__ <= 120\n"
		"#define in varying\n"
		"#endif\n"
		""
		"in vec3 fragmentCs;"
		""
		"void main()"
		"{"
		"	gl_FragColor = vec4( fragmentCs, 0.375 );"
		"}"
	;
}

}

//////////////////////////////////////////////////////////////////////////
// DragEditGadget
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( DragEditGadget );

DragEditGadget::DragEditGadget()
	:	Gadget( "DragEditGadget" ), m_mode( None ), m_editable( false ), m_dragPositions( new V3fVectorData )
{
	buttonPressSignal().connect( boost::bind( &DragEditGadget::buttonPress, this, ::_1, ::_2 ) );
	buttonReleaseSignal().connect( boost::bind( &DragEditGadget::buttonRelease, this, ::_1, ::_2 ) );

	dragBeginSignal().connect( boost::bind( &DragEditGadget::dragBegin, this, ::_1, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &DragEditGadget::dragEnter, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &DragEditGadget::dragMove, this, ::_1, ::_2 ) );
	dragEndSignal().connect( boost::bind( &DragEditGadget::dragEnd, this, ::_1, ::_2 ) );
	leaveSignal().connect( boost::bind( &DragEditGadget::leave, this ) );
}

DragEditGadget::~DragEditGadget()
{
}

bool DragEditGadget::acceptsParent( const GraphComponent *potentialParent ) const
{
	return runTimeCast<const GraphGadget>( potentialParent );
}

void DragEditGadget::parentChanging( Gaffer::GraphComponent *newParent )
{
	m_graphGadgetKeyPressConnection.disconnect();
	m_graphGadgetKeyReleaseConnection.disconnect();

	if( auto graphGadget = runTimeCast<GraphGadget>( newParent ) )
	{
		m_graphGadgetKeyPressConnection = graphGadget->keyPressSignal().connect(
			boost::bind( &DragEditGadget::keyPress, this, ::_1, ::_2 )
		);
		m_graphGadgetKeyReleaseConnection = graphGadget->keyReleaseSignal().connect(
			boost::bind( &DragEditGadget::keyRelease, this, ::_1, ::_2 )
		);
	}
}

void DragEditGadget::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	if( layer != GraphLayer::Overlay || m_mode == None )
	{
		return;
	}

	if( isSelectionRender( reason ) )
	{
		const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
		ViewportGadget::RasterScope rasterScope( viewportGadget );
		// We render a selection overlay over the entire viewport to intercept all events.
		glColor4f( 1.0f, 1.0f, 1.0f, 1.0f );
		style->renderSolidRectangle( Box2f( V2f( 0, 0 ), viewportGadget->getViewport() ) );
		return;
	}

	if( m_dragPositions->readable().size() > 1 )
	{
		// Render a curve to represent the dragged cursor trail.
		State::bindBaseState();
		auto glState = const_cast<State *>( State::defaultState() );

		IECoreGL::GroupPtr group = new IECoreGL::Group();
		group->getState()->add( new IECoreGL::Primitive::DrawWireframe( false ) );
		group->getState()->add( new IECoreGL::Primitive::DrawSolid( true ) );
		group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
		group->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( g_cutLineRadius * 2.0f ) );
		group->getState()->add( new IECoreGL::LineSmoothingStateComponent( true ) );
		group->getState()->add( new IECoreGL::Color( g_cutLineColor ) );
		group->getState()->add(
			new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), "", "", translucentConstantFragSource(), new CompoundObject )
		);

		IntVectorDataPtr vertsPerCurve = new IntVectorData();
		vertsPerCurve->writable().push_back( m_dragPositions->readable().size() );
		IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( CubicBasisf::linear(), false, vertsPerCurve );
		curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, m_dragPositions ) );
		group->addChild( curves );

		group->render( glState );
	}
}

unsigned DragEditGadget::layerMask() const
{
	return (unsigned)GraphLayer::Overlay;
}

Imath::Box3f DragEditGadget::renderBound() const
{
	// This Gadget renders a trail anywhere the cursor is
	// dragged, so we can't give it a tight render bound.
	Box3f b;
	b.makeInfinite();
	return b;
}

GraphGadget *DragEditGadget::graphGadget()
{
	return parent<GraphGadget>();
}

const GraphGadget *DragEditGadget::graphGadget() const
{
	return parent<GraphGadget>();
}

bool DragEditGadget::keyPress( GadgetPtr gadget, const KeyEvent &event )
{
	if( event.key == "X" && !event.modifiers )
	{
		m_mode = Disconnect;
		m_editable = !( Gaffer::MetadataAlgo::readOnly( graphGadget()->getRoot() ) || Gaffer::MetadataAlgo::getChildNodesAreReadOnly( graphGadget()->getRoot() ) );
		Pointer::setCurrent( m_editable ? "cut" : "notEditable" );

		return true;
	}

	return false;
}

bool DragEditGadget::keyRelease( GadgetPtr gadget, const KeyEvent &event )
{
	if( m_mode == Disconnect && event.key == "X" )
	{
		m_mode = None;
		Pointer::setCurrent( "" );
		m_dragPositions->writable().clear();
		dirty( DirtyType::Render );

		return true;
	}

	return false;
}

bool DragEditGadget::buttonPress( GadgetPtr gadget, const ButtonEvent &event )
{
	// We don't need to test `m_mode` here, as we don't get events when `m_mode` is None as
	// no overlay will have been drawn in that case.

	// Accept both left and right button events. We only act on the left, but not accepting
	// the right button results in the NodeMenu appearing while we have a key held.
	if( event.buttons == ButtonEvent::Middle )
	{
		return false;
	}

	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}
	if( event.buttons == ButtonEvent::Left && m_editable )
	{
		m_dragPositions->writable().push_back( i );
	}

	return true;
}

bool DragEditGadget::buttonRelease( GadgetPtr gadget, const ButtonEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}
	if( m_mode == Disconnect && m_editable )
	{
		disconnectConnectionGadgets();
		m_mergeGroupId++;
	}

	m_dragPositions->writable().clear();
	dirty( DirtyType::Render );

	return true;
}

IECore::RunTimeTypedPtr DragEditGadget::dragBegin( GadgetPtr gadget, const DragDropEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return nullptr;
	}
	if( event.buttons == ButtonEvent::Left )
	{
		return IECore::NullObject::defaultNullObject();
	}

	return nullptr;
}

bool DragEditGadget::dragEnter( GadgetPtr gadget, const DragDropEvent &event )
{
	if( event.buttons != ButtonEvent::Left )
	{
		return false;
	}

	return event.sourceGadget == this;
}

bool DragEditGadget::dragMove( GadgetPtr gadget, const DragDropEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}
	if( m_mode != None && m_editable )
	{
		m_dragPositions->writable().push_back( i );
		dirty( DirtyType::Render );
	}

	return true;
}

bool DragEditGadget::dragEnd( GadgetPtr gadget, const DragDropEvent &event )
{
	if( m_mode == Disconnect && m_editable )
	{
		disconnectConnectionGadgets();
		m_mergeGroupId++;
	}

	m_dragPositions->writable().clear();
	dirty( DirtyType::Render );

	return true;
}

void DragEditGadget::leave()
{
	Pointer::setCurrent( "" );
}

std::string DragEditGadget::undoMergeGroup() const
{
	return fmt::format( "DragEditGadget{}{}", (void*)this, m_mergeGroupId );
}

void DragEditGadget::disconnectConnectionGadgets()
{
	if( m_dragPositions->readable().empty() )
	{
		return;
	}

	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	std::vector<LineSegment2f> rasterLines;
	V3f lineStart = m_dragPositions->readable().front();
	for( const auto &lineEnd : m_dragPositions->readable() )
	{
		rasterLines.emplace_back( LineSegment2f(
			viewportGadget->gadgetToRasterSpace( lineStart, graphGadget() ),
			viewportGadget->gadgetToRasterSpace( lineEnd, graphGadget() )
		) );
		lineStart = lineEnd;
	}

	// Overlapping gadgets will only be returned one at a time, so we
	// exhaustively test and remove until no more are found.
	while( true )
	{
		std::unordered_set<ConnectionGadget*> connectionsToDisconnect;
		for( const auto &line : rasterLines )
		{
			const auto connectionsAtLine = editableConnectionGadgetsAtLine( viewportGadget, line, g_cutLineRadius, /* includeEndpoint = */ &line == &rasterLines.back() );
			connectionsToDisconnect.insert( connectionsAtLine.begin(), connectionsAtLine.end() );
		}

		if( connectionsToDisconnect.empty() )
		{
			break;
		}

		ScriptNode *scriptNode = ( *connectionsToDisconnect.begin() )->dstNodule()->plug()->ancestor<ScriptNode>();
		Gaffer::UndoScope undoScope( scriptNode, Gaffer::UndoScope::Enabled, undoMergeGroup() );
		for( const auto &connection : connectionsToDisconnect )
		{
			connection->dstNodule()->plug()->setInput( nullptr );
		}
	}
}
