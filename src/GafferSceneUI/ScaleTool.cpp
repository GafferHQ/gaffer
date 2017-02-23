//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, John Haddon. All rights reserved.
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

#include "boost/bind.hpp"

#include "Gaffer/UndoContext.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/MetadataAlgo.h"

#include "GafferUI/ScaleHandle.h"

#include "GafferSceneUI/ScaleTool.h"
#include "GafferSceneUI/SceneView.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

IE_CORE_DEFINERUNTIMETYPED( ScaleTool );

ScaleTool::ToolDescription<ScaleTool, SceneView> ScaleTool::g_toolDescription;

ScaleTool::ScaleTool( SceneView *view, const std::string &name )
	:	TransformTool( view, name )
{
	static Style::Axes axes[] = { Style::X, Style::Y, Style::Z };
	static const char *handleNames[] = { "x", "y", "z" };

	for( int i = 0; i < 3; ++i )
	{
		ScaleHandlePtr handle = new ScaleHandle( axes[i] );
		handle->setRasterScale( 75 );
		handles()->setChild( handleNames[i], handle );
		// connect with group 0, so we get called before the Handle's slot does.
		handle->dragBeginSignal().connect( 0, boost::bind( &ScaleTool::dragBegin, this, i ) );
		handle->dragMoveSignal().connect( boost::bind( &ScaleTool::dragMove, this, ::_1, ::_2 ) );
		handle->dragEndSignal().connect( boost::bind( &ScaleTool::dragEnd, this ) );
	}
}

ScaleTool::~ScaleTool()
{
}

bool ScaleTool::affectsHandles( const Gaffer::Plug *input ) const
{
	if( TransformTool::affectsHandles( input ) )
	{
		return true;
	}

	return input == scenePlug()->transformPlug();
}

void ScaleTool::updateHandles()
{
	Context::Scope scopedContext( view()->getContext() );
	handles()->setTransform( scenePlug()->fullTransform( selection().path ) );

	for( int i = 0; i < 3; ++i )
	{
		ValuePlug *plug = selection().transformPlug->scalePlug()->getChild( i );
		handles()->getChild<Gadget>( i )->setEnabled(
			plug->settable() && !MetadataAlgo::readOnly( plug )
		);
	}
}

void ScaleTool::scale( const Imath::V3f &scale )
{
	Scale s = createScale( V3i( 1 ) );
	applyScale( s, scale );
}

ScaleTool::Scale ScaleTool::createScale( const Imath::V3i axisMask )
{
	Context::Scope scopedContext( view()->getContext() );
	Scale result;
	result.originalScale = selection().transformPlug->scalePlug()->getValue();
	result.axisMask = axisMask;
	return result;
}

void ScaleTool::applyScale( const Scale &scale, const Imath::V3f &offset )
{
	UndoContext undoContext( selection().transformPlug->ancestor<ScriptNode>(), UndoContext::Enabled, undoMergeGroup() );
	for( int i = 0; i < 3; ++i )
	{
		if( !scale.axisMask[i] )
		{
			continue;
		}
		selection().transformPlug->scalePlug()->getChild( i )->setValue( scale.originalScale[i] * offset[i] );
	}
}

IECore::RunTimeTypedPtr ScaleTool::dragBegin( int axis )
{
	V3i axisMask( 0 );
	axisMask[axis] = 1;
	m_drag = createScale( axisMask );
	TransformTool::dragBegin();
	return NULL; // Let the handle start the drag.
}

bool ScaleTool::dragMove( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	const float scale = static_cast<const ScaleHandle *>( gadget )->dragOffset( event );
	applyScale( m_drag, V3f( scale ) );
	return true;
}

bool ScaleTool::dragEnd()
{
	TransformTool::dragEnd();
	return false;
}
