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

#include "GafferSceneUI/ScaleTool.h"

#include "GafferSceneUI/SceneView.h"

#include "GafferUI/ScaleHandle.h"

#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/UndoScope.h"

#include "Imath/ImathMatrixAlgo.h"

#include "boost/bind/bind.hpp"

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// ScaleTool
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( ScaleTool );

ScaleTool::ToolDescription<ScaleTool, SceneView> ScaleTool::g_toolDescription;

ScaleTool::ScaleTool( SceneView *view, const std::string &name )
	:	TransformTool( view, name )
{
	static Style::Axes axes[] = { Style::X, Style::Y, Style::Z, Style::XY, Style::XZ, Style::YZ, Style::XYZ };
	static const char *handleNames[] = { "x", "y", "z", "xy", "xz", "yz", "xyz" };

	for( int i = 0; i < 7; ++i )
	{
		ScaleHandlePtr handle = new ScaleHandle( axes[i] );
		handle->setRasterScale( 75 );
		handles()->setChild( handleNames[i], handle );
		// Connect at front, so we get called before the Handle's slot does.
		handle->dragBeginSignal().connectFront( boost::bind( &ScaleTool::dragBegin, this, axes[i] ) );
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

void ScaleTool::updateHandles( float rasterScale )
{
	handles()->setTransform(
		this->selection().back().orientedTransform( Local )
	);

	for( ScaleHandle::Iterator it( handles() ); !it.done(); ++it )
	{
		bool enabled = true;
		for( const auto &s : selection() )
		{
			if( !Scale( s ).canApply( (*it)->axisMask() ) )
			{
				enabled = false;
				break;
			}
		}
		(*it)->setEnabled( enabled );
		(*it)->setRasterScale( rasterScale );
	}
}

void ScaleTool::scale( const Imath::V3f &scale )
{
	for( const auto &s : selection() )
	{
		Scale( s ).apply( V3i( 1 ), scale );
	}
}

IECore::RunTimeTypedPtr ScaleTool::dragBegin( GafferUI::Style::Axes axes )
{
	m_drag.clear();
	for( const auto &s : selection() )
	{
		m_drag.push_back( Scale( s ) );
	}
	TransformTool::dragBegin();
	return nullptr; // Let the handle start the drag.
}

bool ScaleTool::dragMove( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	UndoScope undoScope( selection().back().editTarget()->ancestor<ScriptNode>(), UndoScope::Enabled, undoMergeGroup() );
	ScaleHandle *scaleHandle = static_cast<ScaleHandle *>( gadget );
	const V3f &scaling = scaleHandle->scaling( event );
	for( auto &s : m_drag )
	{
		s.apply( scaleHandle->axisMask(), scaling );
	}
	return true;
}

bool ScaleTool::dragEnd()
{
	TransformTool::dragEnd();
	return false;
}

//////////////////////////////////////////////////////////////////////////
// ScaleTool::Scale
//////////////////////////////////////////////////////////////////////////

ScaleTool::Scale::Scale( const Selection &selection )
	:	m_selection( selection )
{
}

bool ScaleTool::Scale::canApply( const Imath::V3i &axisMask ) const
{
	auto edit = m_selection.acquireTransformEdit( /* createIfNecessary = */ false );
	if( !edit )
	{
		// Edit will be created on demand in `apply()`.
		return !MetadataAlgo::readOnly( m_selection.editTarget() );
	}

	for( int i = 0; i < 3; ++i )
	{
		if( axisMask[i] && !canSetValueOrAddKey( edit->scale->getChild( i ) ) )
		{
			return false;
		}
	}

	return true;
}

void ScaleTool::Scale::apply( const Imath::V3i &axisMask, const Imath::V3f &scale )
{
	V3fPlug *scalePlug = m_selection.acquireTransformEdit()->scale.get();
	if( !m_originalScale )
	{
		// First call to `apply()`.
		Context::Scope scopedContext( m_selection.context() );
		m_originalScale = scalePlug->getValue();
	}

	for( int i = 0; i < 3; ++i )
	{
		FloatPlug *plug = scalePlug->getChild( i );
		if( axisMask[i] && canSetValueOrAddKey( plug ) )
		{
			setValueOrAddKey( plug, m_selection.context()->getTime(), (*m_originalScale)[i] * scale[i] );
		}
	}
}
