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

#include "Gaffer/UndoScope.h"
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
	static Style::Axes axes[] = { Style::X, Style::Y, Style::Z, Style::XYZ };
	static const char *handleNames[] = { "x", "y", "z", "xyz" };

	for( int i = 0; i < 4; ++i )
	{
		ScaleHandlePtr handle = new ScaleHandle( axes[i] );
		handle->setRasterScale( 75 );
		handles()->setChild( handleNames[i], handle );
		// connect with group 0, so we get called before the Handle's slot does.
		handle->dragBeginSignal().connect( 0, boost::bind( &ScaleTool::dragBegin, this, axes[i] ) );
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
	const Selection &selection = this->selection();

	M44f pivotMatrix;
	{
		Context::Scope upstreamScope( selection.upstreamContext.get() );
		const V3f pivot = selection.transformPlug->pivotPlug()->getValue();
		pivotMatrix.translate( pivot );
	}

	handles()->setTransform(
		pivotMatrix * selection.transformPlug->matrix() * selection.sceneToTransformSpace().inverse()
	);

	bool allSettable = true;
	for( int i = 0; i < 3; ++i )
	{
		ValuePlug *plug = selection.transformPlug->scalePlug()->getChild( i );
		const bool settable = plug->settable() && !MetadataAlgo::readOnly( plug );
		handles()->getChild<Gadget>( i )->setEnabled( settable );
		allSettable &= settable;
	}

	handles()->getChild<Gadget>( 3 )->setEnabled( allSettable );
}

void ScaleTool::scale( const Imath::V3f &scale )
{
	for( int i = 0; i < 3; ++i )
	{
		Scale s = createScale( (Style::Axes)i );
		applyScale( s, scale[i] );
	}
}

ScaleTool::Scale ScaleTool::createScale( Style::Axes axes )
{
	Context::Scope scopedContext( view()->getContext() );
	Scale result;
	result.originalScale = selection().transformPlug->scalePlug()->getValue();
	result.axes = axes;
	return result;
}

void ScaleTool::applyScale( const Scale &scale, float s )
{
	if( scale.axes == Style::XYZ )
	{
		selection().transformPlug->scalePlug()->setValue(
			scale.originalScale * V3f( s )
		);
	}
	else
	{
		selection().transformPlug->scalePlug()->getChild( scale.axes )->setValue(
			scale.originalScale[scale.axes] * s
		);
	}
}

IECore::RunTimeTypedPtr ScaleTool::dragBegin( GafferUI::Style::Axes axes )
{
	m_drag = createScale( axes );
	TransformTool::dragBegin();
	return NULL; // Let the handle start the drag.
}

bool ScaleTool::dragMove( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	UndoScope undoScope( selection().transformPlug->ancestor<ScriptNode>(), UndoScope::Enabled, undoMergeGroup() );
	const float scale = static_cast<const ScaleHandle *>( gadget )->scaling( event );
	applyScale( m_drag, scale );
	return true;
}

bool ScaleTool::dragEnd()
{
	TransformTool::dragEnd();
	return false;
}
