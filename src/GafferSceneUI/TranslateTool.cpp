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

#include "boost/bind.hpp"

#include "OpenEXR/ImathMatrixAlgo.h"

#include "Gaffer/UndoContext.h"
#include "Gaffer/ScriptNode.h"

#include "GafferUI/Handle.h"

#include "GafferScene/SceneAlgo.h"

#include "GafferSceneUI/TranslateTool.h"
#include "GafferSceneUI/SceneView.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

IE_CORE_DEFINERUNTIMETYPED( TranslateTool );

TranslateTool::ToolDescription<TranslateTool, SceneView> TranslateTool::g_toolDescription;

size_t TranslateTool::g_firstPlugIndex = 0;

TranslateTool::TranslateTool( SceneView *view, const std::string &name )
	:	TransformTool( view, name )
{

	static Handle::Type handleTypes[] = { Handle::TranslateX, Handle::TranslateY, Handle::TranslateZ };
	static const char *handleNames[] = { "x", "y", "z" };

	for( int i = 0; i < 3; ++i )
	{
		HandlePtr handle = new Handle( handleTypes[i] );
		handle->setRasterScale( 75 );
		handles()->setChild( handleNames[i], handle );
		// connect with group 0, so we get called before the Handle's slot does.
		handle->dragBeginSignal().connect( 0, boost::bind( &TranslateTool::dragBegin, this, i ) );
		handle->dragMoveSignal().connect( boost::bind( &TranslateTool::dragMove, this, ::_1, ::_2 ) );
		handle->dragEndSignal().connect( boost::bind( &TranslateTool::dragEnd, this ) );
	}

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "orientation", Plug::In, Local, Local, World ) );
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

bool TranslateTool::affectsHandlesTransform( const Gaffer::Plug *input ) const
{
	if( TransformTool::affectsHandlesTransform( input ) )
	{
		return true;
	}

	return
		input == orientationPlug() ||
		input == scenePlug()->transformPlug();
}

Imath::M44f TranslateTool::handlesTransform() const
{
	Context::Scope scopedContext( view()->getContext() );

	const Selection &selection = this->selection();
	const M44f localMatrix = scenePlug()->transform( selection.path );
	M44f parentMatrix;
	if( selection.path.size() )
	{
		const ScenePlug::ScenePath parentPath( selection.path.begin(), selection.path.end() - 1 );
		parentMatrix = scenePlug()->fullTransform( parentPath );
	}

	M44f result;
	switch( (Orientation)orientationPlug()->getValue() )
	{
		case Local :
			result = localMatrix * parentMatrix;
			break;
		case Parent :
			result = M44f().setTranslation( localMatrix.translation() ) * parentMatrix;
			break;
		case World :
			result.setTranslation( ( localMatrix * parentMatrix ).translation() );
			break;
	}

	return result;
}

void TranslateTool::translate( const Imath::V3f &offset )
{
	if( !selection().transformPlug )
	{
		return;
	}

	Translation t = createTranslation( offset );
	applyTranslation( t, 1.0f );
}

TranslateTool::Translation TranslateTool::createTranslation( const Imath::V3f &directionInHandleSpace )
{
	Context::Scope scopedContext( view()->getContext() );
	Translation result;

	const Selection &selection = this->selection();
	result.origin = selection.transformPlug->translatePlug()->getValue();

	V3f worldSpaceDirection;
	handlesTransform().multDirMatrix( directionInHandleSpace, worldSpaceDirection );
	worldSpaceDirection.normalize();

	const M44f downstreamMatrix = scenePlug()->fullTransform( selection.path );
	M44f upstreamMatrix;
	{
		Context::Scope scopedContext( selection.context.get() );
		upstreamMatrix = selection.upstreamScene->fullTransform( selection.upstreamPath );
	}

	V3f downstreamDirection;
	downstreamMatrix.inverse().multDirMatrix( worldSpaceDirection, downstreamDirection );

	V3f upstreamWorldDirection;
	upstreamMatrix.multDirMatrix( downstreamDirection, upstreamWorldDirection );

	selection.transformSpace.inverse().multDirMatrix( upstreamWorldDirection, result.direction );

	return result;
}

void TranslateTool::applyTranslation( const Translation &translation, float offset )
{
	const Selection &selection = this->selection();
	selection.transformPlug->translatePlug()->setValue( translation.origin + translation.direction * offset );
}

IECore::RunTimeTypedPtr TranslateTool::dragBegin( int axis )
{
	V3f handleVector( 0 );
	handleVector[axis] = 1;
	m_drag = createTranslation( handleVector );

	TransformTool::dragBegin();
	return NULL; // let the handle start the drag with the event system
}

bool TranslateTool::dragMove( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	UndoContext undoContext( selection().transformPlug->ancestor<ScriptNode>(), UndoContext::Enabled, undoMergeGroup() );
	const float offset = static_cast<const Handle *>( gadget )->dragOffset( event );
	applyTranslation( m_drag, offset );
	return true;
}

bool TranslateTool::dragEnd()
{
	TransformTool::dragEnd();
	return false;
}
