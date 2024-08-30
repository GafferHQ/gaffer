//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "GafferSceneUI/CameraTool.h"

#include "GafferSceneUI/SceneView.h"

#include "Gaffer/Animation.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/UndoScope.h"

#include "Gaffer/Private/ScopedAssignment.h"

#include "IECore/AngleConversion.h"

#include "Imath/ImathEuler.h"
#include "Imath/ImathMatrix.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"

#include "fmt/format.h"

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo These are stolen shamelessly from TransformTool. They probably
/// should be moved somewhere they can be shared - perhaps AnimationAlgo
/// of some sort? We would need to generalise to support more than just
/// FloatPlugs, and also consider whether we really expect a non-ui API
/// to be checking for read-onliness.
bool canSetValueOrAddKey( const Gaffer::FloatPlug *plug )
{
	if( Animation::isAnimated( plug ) )
	{
		return !MetadataAlgo::readOnly( plug->source() );
	}

	return plug->settable() && !MetadataAlgo::readOnly( plug );
}

void setValueOrAddKey( Gaffer::FloatPlug *plug, float time, float value )
{
	if( Animation::isAnimated( plug ) )
	{
		Animation::CurvePlug *curve = Animation::acquire( plug );
		curve->insertKey( time, value );
	}
	else
	{
		plug->setValue( value );
	}
}

bool g_editingTransform = false;

} // namespace

//////////////////////////////////////////////////////////////////////////
// CameraTool
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( CameraTool );

CameraTool::ToolDescription<CameraTool, SceneView> CameraTool::g_toolDescription;

size_t CameraTool::g_firstPlugIndex = 0;

CameraTool::CameraTool( SceneView *view, const std::string &name )
	:	SelectionTool( view, name ), m_dragId( 0 )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	connectToViewContext();
	view->contextChangedSignal().connect( boost::bind( &CameraTool::connectToViewContext, this ) );

	view->plugDirtiedSignal().connect( boost::bind( &CameraTool::plugDirtied, this, ::_1 ) );
	plugDirtiedSignal().connect( boost::bind( &CameraTool::plugDirtied, this, ::_1 ) );

	// Snoop on the signals used for interaction with the viewport. We connect at the front
	// so that we are called before everything else.
	view->viewportGadget()->dragBeginSignal().connectFront( boost::bind( &CameraTool::viewportDragBegin, this, ::_2 ) );
	view->viewportGadget()->wheelSignal().connectFront( boost::bind( &CameraTool::viewportWheel, this, ::_2 ) );
	view->viewportGadget()->keyPressSignal().connectFront( boost::bind( &CameraTool::viewportKeyPress, this, ::_2 ) );
	view->viewportGadget()->buttonPressSignal().connectFront( boost::bind( &CameraTool::viewportButtonPress, this, ::_2 ) );
	// Connect to `cameraChangedSignal()` so we can turn the viewport interaction into
	// camera edits in the node graph itself.
	m_viewportCameraChangedConnection = view->viewportGadget()->cameraChangedSignal().connect(
		boost::bind( &CameraTool::viewportCameraChanged, this )
	);

	// Connect to the preRender signal so we can coordinate ourselves with the work
	// that the SceneView::Camera class does to look through the camera we will be editing.
	view->viewportGadget()->preRenderSignal().connectFront( boost::bind( &CameraTool::preRenderBegin, this ) );
	view->viewportGadget()->preRenderSignal().connect( boost::bind( &CameraTool::preRenderEnd, this ) );
}

CameraTool::~CameraTool()
{
}

const GafferScene::ScenePlug *CameraTool::scenePlug() const
{
	return view()->inPlug<ScenePlug>();
}

const Gaffer::BoolPlug *CameraTool::lookThroughEnabledPlug() const
{
	return view()->descendant<BoolPlug>( "camera.lookThroughEnabled" );
}

const Gaffer::StringPlug *CameraTool::lookThroughCameraPlug() const
{
	return view()->descendant<StringPlug>( "camera.lookThroughCamera" );
}

void CameraTool::connectToViewContext()
{
	m_contextChangedConnection = view()->getContext()->changedSignal().connect( boost::bind( &CameraTool::contextChanged, this, ::_2 ) );
}

void CameraTool::contextChanged( const IECore::InternedString &name )
{
	if( !boost::starts_with( name.string(), "ui:" ) )
	{
		m_cameraSelectionDirty = true;
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	}
}

void CameraTool::plugDirtied( const Gaffer::Plug *plug )
{
	if(
		plug == activePlug() ||
		plug == scenePlug()->childNamesPlug() ||
		plug == scenePlug()->transformPlug() ||
		plug == scenePlug()->globalsPlug() ||
		plug == lookThroughEnabledPlug() ||
		plug == lookThroughCameraPlug() ||
		plug == view()->editScopePlug()
	)
	{
		if( !g_editingTransform )
		{
			m_cameraSelectionDirty = true;
		}
		else
		{
			// If the scene is dirtied as a result of an edit we make,
			// we do not expect it to invalidate our selection. Nor do we
			// want the performance hit of selection updates during dragging,
			// so we simply don't dirty the selection.
		}
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	}
}

GafferScene::ScenePlug::ScenePath CameraTool::cameraPath() const
{
	if( !activePlug()->getValue() )
	{
		return ScenePlug::ScenePath();
	}

	if( !lookThroughEnabledPlug()->getValue() )
	{
		return ScenePlug::ScenePath();
	}

	string cameraPath = lookThroughCameraPlug()->getValue();
	if( cameraPath.empty() )
	{
		Context::Scope scopedContext( view()->getContext() );
		IECore::ConstCompoundObjectPtr globals = view()->inPlug<ScenePlug>()->globals();
		if( auto *cameraData = globals->member<StringData>( "option:render:camera" ) )
		{
			cameraPath = cameraData->readable();
		}
	}

	ScenePlug::ScenePath result;
	ScenePlug::stringToPath( cameraPath, result );
	return result;
}

const TransformTool::Selection &CameraTool::cameraSelection()
{
	if( !m_cameraSelectionDirty )
	{
		return m_cameraSelection;
	}

	m_cameraSelection = TransformTool::Selection();
	ScenePlug::ScenePath cameraPath = this->cameraPath();
	if( !cameraPath.empty() )
	{
		TransformTool::Selection candidateSelection(
			scenePlug(),
			cameraPath,
			view()->getContext(),
			view()->editScope()
		);
		// TransformTool::Selection will fall back to editing
		// a parent path if it can't edit the `cameraPath`.
		// Parent edits are not suitable for the camera tool, so
		// we reject them.
		if( candidateSelection.path() == cameraPath )
		{
			m_cameraSelection = candidateSelection;
		}
	}

	m_cameraSelectionDirty = false;
	return m_cameraSelection;
}

void CameraTool::preRenderBegin()
{
	// The SceneView::Camera class updates the viewport camera
	// in `preRender()`, and we don't want to cause feedback by
	// trying to reflect that update back into the graph.
	/// \todo Should we have a more explicit synchronisation between
	/// SceneView::Camera and CameraTool?
	m_viewportCameraChangedConnection.setBlocked( true );
}

void CameraTool::preRenderEnd()
{
	const TransformTool::Selection &selection = cameraSelection();
	bool selectionEditable = false;
	if( selection.editable() )
	{
		selectionEditable = true;
		if( auto edit = selection.acquireTransformEdit( /* createIfNecessary = */ false ) )
		{
			for( auto &p : FloatPlug::Range( *edit->translate ) )
			{
				if( !canSetValueOrAddKey( p.get() ) )
				{
					selectionEditable = false;
					break;
				}
			}

			for( auto &p : FloatPlug::Range( *edit->rotate ) )
			{
				if( !canSetValueOrAddKey( p.get() ) )
				{
					selectionEditable = false;
					break;
				}
			}
		}
	}

	const bool lookThroughEnabled = lookThroughEnabledPlug()->getValue();
	view()->viewportGadget()->setCameraEditable( !lookThroughEnabled || selectionEditable );
	// We can't "dolly" an orthographic camera because that modifies the aperture,
	// and we can't currently reflect aperture edits into the node graph.
	view()->viewportGadget()->setDollyingEnabled(
		!lookThroughEnabled || view()->viewportGadget()->getCamera()->getProjection() == "perspective"
	);

	if( selectionEditable )
	{
		view()->viewportGadget()->setCenterOfInterest(
			getCameraCenterOfInterest( selection.path() )
		);
		m_viewportCameraChangedConnection.setBlocked( false );
	}
}

IECore::RunTimeTypedPtr CameraTool::viewportDragBegin( const GafferUI::DragDropEvent &event )
{
	// The viewport may be performing a camera drag. Set up our undo group
	// so that all the steps of the drag will be collapsed into a single undoable
	// block.
	m_undoGroup = fmt::format( "CameraTool{}Drag{}", fmt::ptr( this ), m_dragId++ );
	return nullptr;
}

bool CameraTool::viewportWheel( const GafferUI::ButtonEvent &event )
{
	// Merge all wheel events into a single undo.
	m_undoGroup = fmt::format( "CameraTool{}Wheel", fmt::ptr( this ) );
	return false;
}

bool CameraTool::viewportKeyPress( const GafferUI::KeyEvent &event )
{
	// Make sure we don't merge any edits into previous drag/wheel edits.
	m_undoGroup = "";
	return false;
}

bool CameraTool::viewportButtonPress( const GafferUI::ButtonEvent &event )
{
	// Make sure we don't merge any edits into previous drag/wheel edits.
	m_undoGroup = "";
	return false;
}

void CameraTool::viewportCameraChanged()
{
	const TransformTool::Selection &selection = cameraSelection();
	if( !selection.editable() )
	{
		return;
	}

	if( !view()->viewportGadget()->getCameraEditable() )
	{
		return;
	}

	// Figure out the offset from where the camera is in the scene
	// to where the user has just moved the viewport camera.
	// Note: The ViewportGadget will have removed any scale/shear from
	// the matrix.

	const M44f viewportCameraTransform = view()->viewportGadget()->getCameraTransform();
	M44f cameraTransform;
	{
		Context::Scope scopedContext( selection.context() );
		cameraTransform = selection.scene()->fullTransform( selection.path() );
	}

	if( cameraTransform == viewportCameraTransform )
	{
		return;
	}

	const M44f offset = cameraTransform.inverse() * viewportCameraTransform;

	// This offset is measured in the downstream world space.
	// Transform it into the space the transform is applied in.
	// This requires a "change of basis" because it is a transformation
	// matrix.

	const M44f sceneToTransformSpace = selection.sceneToTransformSpace();
	const M44f transformSpaceOffset = sceneToTransformSpace.inverse() * offset * sceneToTransformSpace;

	// Now apply this offset to the current value on the transform plug.

	Gaffer::Private::ScopedAssignment<bool> editingScope( g_editingTransform, true );
	UndoScope undoScope( view()->scriptNode(), UndoScope::Enabled, m_undoGroup );
	auto edit = selection.acquireTransformEdit();

	M44f plugTransform;
	{
		Context::Scope scopedContext( selection.upstreamContext() );
		plugTransform = edit->matrix();
	}
	plugTransform = plugTransform * transformSpaceOffset;
	const V3f t = plugTransform.translation();

	Eulerf e; e.extract( plugTransform );
	e.makeNear( degreesToRadians( edit->rotate->getValue() ) );
	const V3f r = radiansToDegrees( V3f( e ) );

	for( int i = 0; i < 3; ++i )
	{
		setValueOrAddKey( edit->rotate->getChild( i ), selection.context()->getTime(), r[i] );
		setValueOrAddKey( edit->translate->getChild( i ), selection.context()->getTime(), t[i] );
	}

	// Create an action to save/restore the current center of interest, so that
	// when the user undos a framing action, they get back to the old center of
	// interest as well as the old transform.
	Action::enact(
		edit->translate,
		// Do
		boost::bind(
			&CameraTool::setCameraCenterOfInterest,
			CameraToolPtr( this ), selection.path(),
			view()->viewportGadget()->getCenterOfInterest()
		),
		// Undo
		boost::bind(
			&CameraTool::setCameraCenterOfInterest,
			CameraToolPtr( this ), selection.path(),
			getCameraCenterOfInterest( selection.path() )
		)
	);
}

void CameraTool::setCameraCenterOfInterest( const GafferScene::ScenePlug::ScenePath &camera, float centerOfInterest )
{
	string key;
	ScenePlug::pathToString( camera, key );
	m_cameraCentersOfInterest[key] = centerOfInterest;
}

float CameraTool::getCameraCenterOfInterest( const GafferScene::ScenePlug::ScenePath &camera ) const
{
	string key;
	ScenePlug::pathToString( camera, key );
	CameraCentersOfInterest::const_iterator it = m_cameraCentersOfInterest.find( key );
	if( it != m_cameraCentersOfInterest.end() )
	{
		return it->second;
	}
	else
	{
		return 1.0f;
	}
}
