//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014-2016, John Haddon. All rights reserved.
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

#include "GafferSceneUI/TranslateTool.h"

#include "GafferSceneUI/SceneView.h"

#include "GafferScene/SceneAlgo.h"

#include "GafferUI/Pointer.h"
#include "GafferUI/TranslateHandle.h"

#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/UndoScope.h"

#include "OpenEXR/ImathMatrixAlgo.h"

#include "boost/bind.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( TranslateTool );

TranslateTool::ToolDescription<TranslateTool, SceneView> TranslateTool::g_toolDescription;

size_t TranslateTool::g_firstPlugIndex = 0;

TranslateTool::TranslateTool( SceneView *view, const std::string &name )
	:	TransformTool( view, name )
{

	static Style::Axes axes[] = { Style::X, Style::Y, Style::Z, Style::XY, Style::XZ, Style::YZ, Style::XYZ };
	static const char *handleNames[] = { "x", "y", "z", "xy", "xz", "yz", "xyz" };

	for( int i = 0; i < 7; ++i )
	{
		HandlePtr handle = new TranslateHandle( axes[i] );
		handle->setRasterScale( 75 );
		handles()->setChild( handleNames[i], handle );
		// connect with group 0, so we get called before the Handle's slot does.
		handle->dragBeginSignal().connect( 0, boost::bind( &TranslateTool::handleDragBegin, this ) );
		handle->dragMoveSignal().connect( boost::bind( &TranslateTool::handleDragMove, this, ::_1, ::_2 ) );
		handle->dragEndSignal().connect( boost::bind( &TranslateTool::handleDragEnd, this ) );
	}

	SceneGadget *sg = runTimeCast<SceneGadget>( this->view()->viewportGadget()->getPrimaryChild() );
	sg->keyPressSignal().connect( boost::bind( &TranslateTool::keyPress, this, ::_2 ) );
	sg->keyReleaseSignal().connect( boost::bind( &TranslateTool::keyRelease, this, ::_2 ) );
	sg->leaveSignal().connect( boost::bind( &TranslateTool::sceneGadgetLeave, this, ::_2 ) );
	// We have to insert this before the underlying SelectionTool connections or it starts an object drag.
	sg->buttonPressSignal().connect( 0, boost::bind( &TranslateTool::buttonPress, this, ::_2 ) );

	// We need to track the tool state/view visibility so we don't leave a lingering target cursor
	sg->visibilityChangedSignal().connect( boost::bind( &TranslateTool::visibilityChanged, this, ::_1 ) );
	// We use set not dirtied to make sure we're called synchronously. We're
	// happy to assume that this plug won't ever be connected to anything.
	plugSetSignal().connect( boost::bind( &TranslateTool::plugSet, this, ::_1 ) );

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "orientation", Plug::In, Parent, Local, World ) );
}

TranslateTool::~TranslateTool()
{
}

Gaffer::IntPlug *TranslateTool::orientationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *TranslateTool::orientationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

bool TranslateTool::affectsHandles( const Gaffer::Plug *input ) const
{
	if( TransformTool::affectsHandles( input ) )
	{
		return true;
	}

	return
		input == orientationPlug() ||
		input == scenePlug()->transformPlug();
}

void TranslateTool::updateHandles( float rasterScale )
{
	const Orientation orientation = static_cast<Orientation>( orientationPlug()->getValue() );
	handles()->setTransform(
		selection().back().orientedTransform( orientation )
	);

	// Because we provide multiple orientations, the handles
	// may well not be aligned with the axes of the transform
	// space. So any given handle might affect several components
	// of the target translation. For each handle, check to see
	// if each of the plugs it effects are settable, and if not,
	// disable the handle.
	for( TranslateHandleIterator it( handles() ); !it.done(); ++it )
	{
		bool enabled = true;
		for( const auto &s : selection() )
		{
			if( !Translation( s, orientation ).canApply( (*it)->axisMask() ) )
			{
				enabled = false;
				break;
			}
		}
		(*it)->setEnabled( enabled );
		(*it)->setRasterScale( rasterScale );
	}
}

void TranslateTool::translate( const Imath::V3f &offset )
{
	const Orientation orientation = static_cast<Orientation>( orientationPlug()->getValue() );
	for( const auto &s : selection() )
	{
		Translation( s, orientation ).apply( offset );
	}
}

bool TranslateTool::keyPress( const GafferUI::KeyEvent &event )
{
	if( activePlug()->getValue() && event.key == "V" )
	{
		setTargetedMode( true );
		return true;
	}

	return false;
}

bool TranslateTool::keyRelease( const GafferUI::KeyEvent &event )
{
	if( activePlug()->getValue() && event.key == "V" )
	{
		setTargetedMode( false );
		return true;
	}

	return false;
}

void TranslateTool::sceneGadgetLeave( const GafferUI::ButtonEvent & event )
{
	if( getTargetedMode() )
	{
		// We loose keyRelease events in a variety of scenarios so turn targeted
		// off whenever the mouse leaves the scene view. Key-repeat events will
		// cause it to be re-enabled when the mouse re-enters if the key is still
		// held down at that time.
		setTargetedMode( false );
	}
}

void TranslateTool::plugSet( Gaffer::Plug *plug )
{
	if( plug == activePlug() )
	{
		if( !activePlug()->getValue() && getTargetedMode() )
		{
			setTargetedMode( false );
		}
	}
}

void TranslateTool::visibilityChanged( GafferUI::Gadget *gadget )
{
	if( !gadget->visible() && getTargetedMode() )
	{
		setTargetedMode( false );
	}
}

void TranslateTool::setTargetedMode( bool targeted )
{
	if( targeted == m_targetedMode )
	{
		return;
	}

	m_targetedMode = targeted;

	GafferUI::Pointer::setCurrent( targeted ? "target" : "" );
}


IECore::RunTimeTypedPtr TranslateTool::handleDragBegin()
{
	m_drag.clear();
	const Orientation orientation = static_cast<Orientation>( orientationPlug()->getValue() );
	for( const auto &s : selection() )
	{
		m_drag.push_back( Translation( s, orientation ) );
	}
	TransformTool::dragBegin();
	return nullptr; // let the handle start the drag with the event system
}

bool TranslateTool::handleDragMove( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	UndoScope undoScope( selection().back().editTarget()->ancestor<ScriptNode>(), UndoScope::Enabled, undoMergeGroup() );
	const V3f translation = static_cast<TranslateHandle *>( gadget )->translation( event );
	for( auto &t : m_drag )
	{
		t.apply( translation );
	}
	return true;
}

bool TranslateTool::handleDragEnd()
{
	TransformTool::dragEnd();
	return false;
}

bool TranslateTool::buttonPress( const GafferUI::ButtonEvent &event )
{
	if( event.buttons != ButtonEvent::Left || !activePlug()->getValue() || !getTargetedMode() )
	{
		return false;
	}

	// In targeted mode, we teleport the selection to the clicked point.
	//
	// Our prescribed behaviour is to move the bbox center of the selection
	// to the clicked point. If multiple locations are selected, their combined
	// bounds should be used, so they retain their existing relative spacing.
	//
	// We always return true to prevent the SelectTool defaults.

	if( !selectionEditable() )
	{
		return true;
	}

	GafferScene::ScenePlug::ScenePath _;
	Imath::V3f targetPos;

	const SceneView *sv = static_cast<const SceneView *>( view() );
	const Gadget *g = sv->viewportGadget()->getPrimaryChild();
	const SceneGadget* sg = static_cast<const SceneGadget *>( g );
	if( !sg->objectAt( event.line, _, targetPos ) )
	{
		return true;
	}

	Box3f selectionCentroids;
	for( const auto &s : selection() )
	{
		Context::Scope scopedContext( s.context() );

		const M44f worldTransform = s.scene()->fullTransform( s.path() );
		selectionCentroids.extendBy( s.scene()->bound( s.path() ).center() * worldTransform );
	}

	UndoScope undoScope( selection().back().editTarget()->ancestor<ScriptNode>() );

	const V3f offset = targetPos - selectionCentroids.center();
	for( const auto &s : selection() )
	{
		Translation( s, World ).apply( offset );
	}

	return true;
}

//////////////////////////////////////////////////////////////////////////
// TranslateTool::Translation
//////////////////////////////////////////////////////////////////////////

TranslateTool::Translation::Translation( const Selection &selection, Orientation orientation )
	:	m_selection( selection )
{
	const M44f handlesTransform = selection.orientedTransform( orientation );
	m_gadgetToTransform = handlesTransform * selection.sceneToTransformSpace();
}

bool TranslateTool::Translation::canApply( const Imath::V3f &offset ) const
{
	auto edit = m_selection.acquireTransformEdit( /* createIfNecessary = */ false );
	if( !edit )
	{
		// Plugs will be created on demand in apply(), at which point we know
		// it will be editable.
		return true;
	}

	V3f offsetInTransformSpace;
	m_gadgetToTransform.multDirMatrix( offset, offsetInTransformSpace );

	for( int i = 0; i < 3; ++i )
	{
		if( offsetInTransformSpace[i] != 0.0f )
		{
			if( !canSetValueOrAddKey( edit->translate->getChild( i ) ) )
			{
				return false;
			}
		}
	}

	return true;
}

void TranslateTool::Translation::apply( const Imath::V3f &offset )
{
	V3fPlug *translatePlug = m_selection.acquireTransformEdit()->translate.get();
	if( !m_origin )
	{
		// First call to `apply()`.
		Context::Scope scopedContext( m_selection.context() );
		m_origin = translatePlug->getValue();
	}

	V3f offsetInTransformSpace;
	m_gadgetToTransform.multDirMatrix( offset, offsetInTransformSpace );
	for( int i = 0; i < 3; ++i )
	{
		FloatPlug *plug = translatePlug->getChild( i );
		if( canSetValueOrAddKey( plug ) )
		{
			setValueOrAddKey(
				plug,
				m_selection.context()->getTime(),
				(*m_origin)[i] + offsetInTransformSpace[i]
			);
		}
	}
}
