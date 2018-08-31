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

#include "GafferUI/RotateHandle.h"

#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/UndoScope.h"

#include "IECore/AngleConversion.h"
#include "IECore/Export.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathEuler.h"
IECORE_POP_DEFAULT_VISIBILITY

#include "boost/bind.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

IE_CORE_DEFINERUNTIMETYPED( RotateTool );

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
		handle->dragBeginSignal().connect( 0, boost::bind( &RotateTool::dragBegin, this ) );
		handle->dragMoveSignal().connect( boost::bind( &RotateTool::dragMove, this, ::_1, ::_2 ) );
		handle->dragEndSignal().connect( boost::bind( &RotateTool::dragEnd, this ) );
	}

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
	const Rotation r( this );
	r.apply( degreesToRadians( V3f( degrees ) ) );
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

void RotateTool::updateHandles()
{
	handles()->setTransform(
		orientedTransform( static_cast<Orientation>( orientationPlug()->getValue() ) )
	);
	Rotation rotation( this );
	for( RotateHandleIterator it( handles() ); !it.done(); ++it )
	{
		(*it)->setEnabled( rotation.canApply( (*it)->axisMask() ) );
	}
}

IECore::RunTimeTypedPtr RotateTool::dragBegin()
{
	m_drag = Rotation( this );
	TransformTool::dragBegin();
	return nullptr; // Let the handle start the drag.
}

bool RotateTool::dragMove( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	UndoScope undoScope( selection().transformPlug->ancestor<ScriptNode>(), UndoScope::Enabled, undoMergeGroup() );
	m_drag.apply( static_cast<const RotateHandle *>( gadget )->rotation( event ) );
	return true;
}

bool RotateTool::dragEnd()
{
	TransformTool::dragEnd();
	return false;
}

//////////////////////////////////////////////////////////////////////////
// RotateTool::Rotation
//////////////////////////////////////////////////////////////////////////

RotateTool::Rotation::Rotation( const RotateTool *tool )
{
	Context::Scope scopedContext( tool->view()->getContext() );

	const Selection &selection = tool->selection();

	m_plug = selection.transformPlug->rotatePlug();
	m_originalRotation = degreesToRadians( m_plug->getValue() );

	const M44f handlesTransform = tool->orientedTransform( static_cast<Orientation>( tool->orientationPlug()->getValue() ) );
	m_gadgetToTransform = handlesTransform * selection.sceneToTransformSpace();
}

bool RotateTool::Rotation::canApply( const Imath::V3i &axisMask ) const
{
	Imath::V3f current;
	const Imath::V3f updated = updatedRotateValue( V3f( axisMask ), &current );
	for( int i = 0; i < 3; ++i )
	{
		if( updated[i] == current[i] )
		{
			continue;
		}

		FloatPlug *p = m_plug->getChild( i );
		if( !p->settable() || MetadataAlgo::readOnly( p ) )
		{
			return false;
		}
	}
	return true;
}

void RotateTool::Rotation::apply( const Imath::Eulerf &rotation ) const
{
	const Imath::V3f e = updatedRotateValue( rotation );
	for( int i = 0; i < 3; ++i )
	{
		FloatPlug *p = m_plug->getChild( i );
		if( p->settable() && !MetadataAlgo::readOnly( p ) )
		{
			p->setValue( e[i] );
		}
	}
}

Imath::V3f RotateTool::Rotation::updatedRotateValue( const Imath::Eulerf &rotation, Imath::V3f *currentValue ) const
{
	// Convert the rotation into the space of the
	// upstream transform.
	Quatf q = rotation.toQuat();
	V3f transformSpaceAxis;
	m_gadgetToTransform.multDirMatrix( q.axis(), transformSpaceAxis );
	q.setAxisAngle( transformSpaceAxis, q.angle() );

	// Compose it with the original.

	M44f m = q.toMatrix44();
	m.rotate( m_originalRotation );

	// Convert to the euler angles closest to
	// those we currently have.

	const V3f current = m_plug->getValue();
	if( currentValue )
	{
		*currentValue = current;
	}

	Eulerf e; e.extract( m );
	e.makeNear( degreesToRadians( current ) );

	return radiansToDegrees( V3f( e ) );
}
