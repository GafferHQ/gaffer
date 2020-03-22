//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
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

#include "GafferSceneUI/RotateTool.h"

#include "GafferSceneUI/SceneView.h"

#include "GafferUI/Pointer.h"
#include "GafferUI/RotateHandle.h"

#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/UndoScope.h"

#include "IECore/AngleConversion.h"
#include "IECore/Export.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathEuler.h"
#include "OpenEXR/ImathMatrixAlgo.h"
IECORE_POP_DEFAULT_VISIBILITY

#include "boost/bind.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( RotateTool );

RotateTool::ToolDescription<RotateTool, SceneView> RotateTool::g_toolDescription;

size_t RotateTool::g_firstPlugIndex = 0;

RotateTool::RotateTool( SceneView *view, const std::string &name )
	:	TransformTool( view, name )
{
	static Style::Axes axes[] = { Style::XYZ, Style::X, Style::Y, Style::Z, };
	static const char *handleNames[] = { "xyz", "x", "y", "z" };

	for( int i = 0; i < 4; ++i )
	{
		RotateHandlePtr handle = new RotateHandle( axes[i] );
		handle->setRasterScale( 75 );
		handles()->setChild( handleNames[i], handle );
		// connect with group 0, so we get called before the Handle's slot does.
		handle->dragBeginSignal().connect( 0, boost::bind( &RotateTool::handleDragBegin, this ) );
		handle->dragMoveSignal().connect( boost::bind( &RotateTool::handleDragMove, this, ::_1, ::_2 ) );
		handle->dragEndSignal().connect( boost::bind( &RotateTool::handleDragEnd, this ) );
	}

	SceneGadget *sg = runTimeCast<SceneGadget>( this->view()->viewportGadget()->getPrimaryChild() );
	sg->keyPressSignal().connect( boost::bind( &RotateTool::keyPress, this, ::_2 ) );
	sg->keyReleaseSignal().connect( boost::bind( &RotateTool::keyRelease, this, ::_2 ) );
	sg->leaveSignal().connect( boost::bind( &RotateTool::sceneGadgetLeave, this, ::_2 ) );
	// We have to insert this before the underlying SelectionTool connections or it starts an object drag.
	sg->buttonPressSignal().connect( 0, boost::bind( &RotateTool::buttonPress, this, ::_2 ) );

	// We need to track the tool state/view visibility so we don't leave a lingering target cursor
	sg->visibilityChangedSignal().connect( boost::bind( &RotateTool::visibilityChanged, this, ::_1 ) );
	// We use set not dirtied to make sure we're called synchronously. We're
	// happy to assume that this plug won't ever be connected to anything.
	plugSetSignal().connect( boost::bind( &RotateTool::plugSet, this, ::_1 ) );

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "orientation", Plug::In, Parent, Local, World ) );
}

RotateTool::~RotateTool()
{
}

Gaffer::IntPlug *RotateTool::orientationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *RotateTool::orientationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

void RotateTool::rotate( const Imath::Eulerf &degrees )
{
	const Orientation orientation = static_cast<Orientation>( orientationPlug()->getValue() );
	for( const auto &s : selection() )
	{
		Rotation( s, orientation ).apply( degreesToRadians( V3f( degrees ) ) );
	}
}

bool RotateTool::affectsHandles( const Gaffer::Plug *input ) const
{
	if( TransformTool::affectsHandles( input ) )
	{
		return true;
	}

	return
		input == orientationPlug() ||
		input == scenePlug()->transformPlug();
}

void RotateTool::updateHandles( float rasterScale )
{
	const Orientation orientation = static_cast<Orientation>( orientationPlug()->getValue() );
	handles()->setTransform(
		selection().back().orientedTransform( orientation )
	);

	for( RotateHandleIterator it( handles() ); !it.done(); ++it )
	{
		bool enabled = true;
		for( const auto &s : selection() )
		{
			if( !Rotation( s, orientation ).canApply( (*it)->axisMask() ) )
			{
				enabled = false;
				break;
			}
		}

		(*it)->setEnabled( enabled );
		(*it)->setRasterScale( rasterScale );
	}
}

bool RotateTool::keyPress( const GafferUI::KeyEvent &event )
{
	// We track this regardless of whether we're active or not in case the tool
	// is changed whilst the key is held down.
	if( activePlug()->getValue() && event.key == "V" )
	{
		setTargetedMode( true );
		return true;
	}

	return false;
}

bool RotateTool::keyRelease( const GafferUI::KeyEvent &event )
{
	if( activePlug()->getValue() && event.key == "V" )
	{
		setTargetedMode( false );
		return true;
	}

	return false;
}

void RotateTool::sceneGadgetLeave( const GafferUI::ButtonEvent & event )
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

void RotateTool::plugSet( Gaffer::Plug *plug )
{
	if( plug == activePlug() )
	{
		if( !activePlug()->getValue() && getTargetedMode() )
		{
			setTargetedMode( false );
		}
	}
}

void RotateTool::visibilityChanged( GafferUI::Gadget *gadget )
{
	if( !gadget->visible() && getTargetedMode() )
	{
		setTargetedMode( false );
	}
}

void RotateTool::setTargetedMode( bool targeted )
{
	if( targeted == m_targetedMode )
	{
		return;
	}

	m_targetedMode = targeted;

	GafferUI::Pointer::setCurrent( targeted ? "target" : "" );
}


IECore::RunTimeTypedPtr RotateTool::handleDragBegin()
{
	m_drag.clear();
	const Orientation orientation = static_cast<Orientation>( orientationPlug()->getValue() );
	for( const auto &s : selection() )
	{
		m_drag.push_back( Rotation( s, orientation ) );
	}

	TransformTool::dragBegin();
	return nullptr; // Let the handle start the drag.
}

bool RotateTool::handleDragMove( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	UndoScope undoScope( selection().back().editTarget()->ancestor<ScriptNode>(), UndoScope::Enabled, undoMergeGroup() );
	const V3f rotation = static_cast<RotateHandle *>( gadget )->rotation( event );
	for( auto &r : m_drag )
	{
		r.apply( rotation );
	}
	return true;
}

bool RotateTool::handleDragEnd()
{
	TransformTool::dragEnd();
	return false;
}

bool RotateTool::buttonPress( const GafferUI::ButtonEvent &event )
{
	if( event.buttons != ButtonEvent::Left || !activePlug()->getValue() || !getTargetedMode() )
	{
		return false;
	}

	// In targeted mode, we orient the selection so -z aims towards the clicked point.
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

	UndoScope undoScope( selection().back().editTarget()->ancestor<ScriptNode>() );

	for( const auto &s : selection() )
	{
		// There are two potential approaches as to the 'correct' space to do
		// this in.  Production suggested that the guiding principal of
		// 'minimise additional roll in the object's local z axis' is
		// preferable. Hence the more elaborate implementation here.
		//
		// The alternative (work out the current object's world z and simply
		// use rotationMatrix()) calculates in world space tends to add more
		// roll in local Z.

		Context::Scope scopedContext( s.context() );

		ScenePlug::ScenePath parentPath( s.path() );
		parentPath.pop_back();

		const M44f worldParentTransform = s.scene()->fullTransform( parentPath );
		const M44f worldParentTransformInverse = worldParentTransform.inverse();
		const M44f localTransform = s.scene()->transform( s.path() );

		V3f currentYAxis;
		localTransform.multDirMatrix( V3f( 0.0f, 1.0f, 0.0f ), currentYAxis );

		// The local space position of the target is the direction we want the Z axis to point
		V3f targetZAxis = targetPos * worldParentTransformInverse - V3f( 0.0f ) * localTransform;

		M44f orientationMatrix = rotationMatrixWithUpDir(
			V3f( 0.0f, 0.0f, -1.0f ), targetZAxis, currentYAxis
		);

		// We now have the desired local space orientation matrix, and we want
		// to set the rotation to match this.  This means we want the value of
		// "m" computed in apply() to be equal to orientationMatrix.  Because
		// there is no way to call apply without it composing with the existing
		// rotation, we now need to pre-invert the existing rotation.

		V3f originalRotation;
		extractEulerXYZ( localTransform, originalRotation );
		M44f originalRotationMatrix;
		originalRotationMatrix.rotate( originalRotation );

		M44f relativeMatrix = originalRotationMatrix.inverse() * orientationMatrix;

		V3f relativeRotation;
		extractEulerXYZ( relativeMatrix, relativeRotation );
		Rotation( s, Parent ).apply( relativeRotation );
	}

	return true;
}

//////////////////////////////////////////////////////////////////////////
// RotateTool::Rotation
//////////////////////////////////////////////////////////////////////////

RotateTool::Rotation::Rotation( const Selection &selection, Orientation orientation )
	:	m_selection( selection )
{
	const M44f handlesTransform = selection.orientedTransform( orientation );
	m_gadgetToTransform = handlesTransform * selection.sceneToTransformSpace();
}

bool RotateTool::Rotation::canApply( const Imath::V3i &axisMask ) const
{
	auto edit = m_selection.acquireTransformEdit( /* createIfNecessary = */ false );
	if( !edit )
	{
		// Edit will be created on demand in apply(), at which point we know
		// it will be editable.
		return true;
	}

	Imath::V3f current;
	const Imath::V3f updated = updatedRotateValue( edit->rotate.get(), V3f( axisMask ), &current );
	for( int i = 0; i < 3; ++i )
	{
		if( updated[i] == current[i] )
		{
			continue;
		}

		if( !canSetValueOrAddKey( edit->rotate->getChild( i ) ) )
		{
			return false;
		}
	}
	return true;
}

void RotateTool::Rotation::apply( const Imath::Eulerf &rotation )
{
	V3fPlug *rotatePlug = m_selection.acquireTransformEdit()->rotate.get();
	const Imath::V3f e = updatedRotateValue( rotatePlug, rotation );
	for( int i = 0; i < 3; ++i )
	{
		FloatPlug *p = rotatePlug->getChild( i );
		if( canSetValueOrAddKey( p ) )
		{
			setValueOrAddKey( p, m_selection.context()->getTime(), e[i] );
		}
	}
}

Imath::V3f RotateTool::Rotation::updatedRotateValue( const Gaffer::V3fPlug *rotatePlug, const Imath::Eulerf &rotation, Imath::V3f *currentValue ) const
{
	if( !m_originalRotation )
	{
		Context::Scope scopedContext( m_selection.context() );
		m_originalRotation = degreesToRadians( rotatePlug->getValue() );
	}

	// Convert the rotation into the space of the
	// upstream transform.
	Quatf q = rotation.toQuat();
	V3f transformSpaceAxis;
	m_gadgetToTransform.multDirMatrix( q.axis(), transformSpaceAxis );
	q.setAxisAngle( transformSpaceAxis, q.angle() );

	// Compose it with the original.

	M44f m = q.toMatrix44();
	m.rotate( *m_originalRotation );

	// Convert to the euler angles closest to
	// those we currently have.

	const V3f current = rotatePlug->getValue();
	if( currentValue )
	{
		*currentValue = current;
	}

	Eulerf e; e.extract( m );
	e.makeNear( degreesToRadians( current ) );

	return radiansToDegrees( V3f( e ) );
}
