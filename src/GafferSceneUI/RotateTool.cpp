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
	static Style::Axes axes[] = { Style::X, Style::Y, Style::Z };
	static const char *handleNames[] = { "x", "y", "z" };

	for( int i = 0; i < 3; ++i )
	{
		RotateHandlePtr handle = new RotateHandle( axes[i] );
		handle->setRasterScale( 75 );
		handles()->setChild( handleNames[i], handle );
		// connect with group 0, so we get called before the Handle's slot does.
		handle->dragBeginSignal().connect( 0, boost::bind( &RotateTool::dragBegin, this, i ) );
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

void RotateTool::rotate( int axis, float degrees )
{
	Rotation r = createRotation( axis );
	applyRotation( r, degreesToRadians( degrees ) );
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
	for( int i = 0; i < 3; ++i )
	{
		const Rotation rotation = createRotation( i );
		const V3f r = this->rotation( rotation, M_PI / 4.0 );
		bool editable = true;
		for( int j = 0; j < 3; ++j )
		{
			if( r[j] != rotation.originalRotation[j] )
			{
				ValuePlug *plug = selection().transformPlug->rotatePlug()->getChild( j );
				if( !plug->settable() || MetadataAlgo::readOnly( plug ) )
				{
					editable = false;
					break;
				}
			}
		}
		handles()->getChild<Gadget>( i )->setEnabled( editable );
	}
}

RotateTool::Rotation RotateTool::createRotation( int axis )
{
	Context::Scope scopedContext( view()->getContext() );

	const Selection &selection = this->selection();

	Rotation result;
	result.originalRotation = selection.transformPlug->rotatePlug()->getValue();

	/// \todo Share this with TranslateTool somehow
	V3f handleSpaceAxis( 0.0f );
	handleSpaceAxis[axis] = 1.0f;
	const M44f handlesTransform = orientedTransform( static_cast<Orientation>( orientationPlug()->getValue() ) );
	V3f worldSpaceAxis;
	handlesTransform.multDirMatrix( handleSpaceAxis, worldSpaceAxis );

	const M44f downstreamMatrix = scenePlug()->fullTransform( selection.path );
	M44f upstreamMatrix;
	{
		Context::Scope scopedContext( selection.context.get() );
		upstreamMatrix = selection.upstreamScene->fullTransform( selection.upstreamPath );
	}

	V3f downstreamAxis;
	downstreamMatrix.inverse().multDirMatrix( worldSpaceAxis, downstreamAxis );

	V3f upstreamWorldAxis;
	upstreamMatrix.multDirMatrix( downstreamAxis, upstreamWorldAxis );

	selection.transformSpace.inverse().multDirMatrix( upstreamWorldAxis, result.axis );
	return result;
}

Imath::V3f RotateTool::rotation( const Rotation &rotation, float radians ) const
{
	const Selection &selection = this->selection();

	// Compose our new rotation with the original
	Quatf q; q.setAxisAngle( rotation.axis, radians );
	M44f m = q.toMatrix44();
	m.rotate( degreesToRadians( rotation.originalRotation ) );

	// Convert to the euler angles closest to
	// those we currently have.
	Eulerf e; e.extract( m );
	e.makeNear( degreesToRadians( selection.transformPlug->rotatePlug()->getValue() ) );

	return V3f( e );
}

void RotateTool::applyRotation( const Rotation &rotation, float radians )
{
	const Selection &selection = this->selection();
	const V3f r = radiansToDegrees( this->rotation( rotation, radians ) );
	for( int i = 0; i < 3; ++i )
	{
		FloatPlug *p = selection.transformPlug->rotatePlug()->getChild( i );
		if( p->settable() && !MetadataAlgo::readOnly( p ) )
		{
			p->setValue( r[i] );
		}
	}
}

IECore::RunTimeTypedPtr RotateTool::dragBegin( int axis )
{
	m_drag = createRotation( axis );
	TransformTool::dragBegin();
	return nullptr; // Let the handle start the drag.
}

bool RotateTool::dragMove( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	UndoScope undoScope( selection().transformPlug->ancestor<ScriptNode>(), UndoScope::Enabled, undoMergeGroup() );
	const float r = static_cast<const RotateHandle *>( gadget )->rotation( event );
	applyRotation( m_drag, r );
	return true;
}

bool RotateTool::dragEnd()
{
	TransformTool::dragEnd();
	return false;
}
