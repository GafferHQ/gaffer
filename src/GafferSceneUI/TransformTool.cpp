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
#include "boost/unordered_map.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "tbb/spin_mutex.h"

#include "OpenEXR/ImathMatrixAlgo.h"

#include "Gaffer/ScriptNode.h"
#include "Gaffer/Monitor.h"
#include "Gaffer/Process.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ObjectSource.h"
#include "GafferScene/Group.h"
#include "GafferScene/Transform.h"

#include "GafferSceneUI/TransformTool.h"
#include "GafferSceneUI/SceneView.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

struct CapturedProcess
{

	typedef boost::shared_ptr<CapturedProcess> Ptr;
	typedef vector<Ptr> PtrVector;

	InternedString type;
	ConstPlugPtr plug;
	ContextPtr context;

	PtrVector children;

};

/// \todo Perhaps add this to the Gaffer module as a
/// public class, and expose it within the stats app?
/// Give a bit more thought to the CapturedProcess
/// class if doing this.
class CapturingMonitor : public Monitor
{

	public :

		CapturingMonitor()
		{
		}

		virtual ~CapturingMonitor()
		{
		}

		const CapturedProcess::PtrVector &rootProcesses()
		{
			return m_rootProcesses;
		}

	protected :

		virtual void processStarted( const Process *process )
		{
			CapturedProcess::Ptr capturedProcess = boost::make_shared<CapturedProcess>();
			capturedProcess->type = process->type();
			capturedProcess->plug = process->plug();
			capturedProcess->context = new Context( *Context::current() );

			Mutex::scoped_lock lock( m_mutex );
			if( process->parent() )
			{
				ProcessMap::const_iterator it = m_processMap.find( process->parent() );
				it->second->children.push_back( capturedProcess );
			}
			else
			{
				m_rootProcesses.push_back( capturedProcess );
			}
			m_processMap[process] = capturedProcess.get();
		}

		virtual void processFinished( const Process *process )
		{
			Mutex::scoped_lock lock( m_mutex );
			m_processMap.erase( process );
		}

	private :

		typedef tbb::spin_mutex Mutex;

		Mutex m_mutex;
		typedef boost::unordered_map<const Process *, CapturedProcess *> ProcessMap;
		ProcessMap m_processMap;
		CapturedProcess::PtrVector m_rootProcesses;

};

InternedString g_contextUniquefierName = "transformTool:uniquefier";
uint64_t g_contextUniquefierValue = 0;

bool updateSelection( const CapturedProcess *process, TransformTool::Selection &selection )
{
	const M44fPlug *matrixPlug = runTimeCast<const M44fPlug>( process->plug.get() );
	if( !matrixPlug )
	{
		return false;
	}

	const ScenePlug *scenePlug = matrixPlug->parent<ScenePlug>();
	if( !scenePlug )
	{
		return false;
	}

	const SceneNode *node = runTimeCast<const SceneNode>( scenePlug->node() );
	if( !node )
	{
		return false;
	}

	Context::Scope scopedContext( process->context.get() );
	if( !node->enabledPlug()->getValue() )
	{
		return false;
	}

	if( const ObjectSource *objectSource = runTimeCast<const ObjectSource>( node ) )
	{
		selection.transformPlug = const_cast<TransformPlug *>( objectSource->transformPlug() );
		selection.transformSpace = M44f();
	}
	else if( const Group *group = runTimeCast<const Group>( node ) )
	{
		const ScenePlug::ScenePath &path = process->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
		if( path.size() == 1 )
		{
			selection.transformPlug = const_cast<TransformPlug *>( group->transformPlug() );
			selection.transformSpace = M44f();
		}
	}
	else if( const GafferScene::Transform *transform = runTimeCast<const GafferScene::Transform>( node ) )
	{
		if( transform->filterPlug()->getValue() & Filter::ExactMatch )
		{
			selection.transformPlug = const_cast<TransformPlug *>( transform->transformPlug() );
			ScenePlug::ScenePath spacePath = process->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
			switch( transform->spacePlug()->getValue() )
			{
				case GafferScene::Transform::Local :
					break;
				case GafferScene::Transform::Parent :
				case GafferScene::Transform::ResetLocal :
					spacePath.pop_back();
					break;
				case GafferScene::Transform::ResetWorld :
					spacePath.clear();
					break;
			}
			selection.transformSpace = transform->outPlug()->fullTransform( spacePath );
		}
	}

	if( selection.transformPlug )
	{
		selection.upstreamScene = scenePlug;
		selection.upstreamPath = process->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
		selection.upstreamContext = process->context;
		return true;
	}

	return false;
}

bool updateSelectionWalk( const CapturedProcess::PtrVector &processes, TransformTool::Selection &selection )
{
	for( CapturedProcess::PtrVector::const_iterator it = processes.begin(), eIt = processes.end(); it != eIt; ++it )
	{
		if( updateSelection( it->get(), selection ) )
		{
			return true;
		}
		if( updateSelectionWalk( (*it)->children, selection ) )
		{
			return true;
		}
	}
	return false;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// TransformTool
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( TransformTool );

size_t TransformTool::g_firstPlugIndex = 0;

TransformTool::TransformTool( SceneView *view, const std::string &name )
	:	SelectionTool( view, name ),
		m_handles( new Gadget() ),
		m_selectionDirty( true ),
		m_handlesTransformDirty( true ),
		m_dragging( false ),
		m_mergeGroupId( 0 )
{
	view->viewportGadget()->addChild( m_handles );

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ScenePlug( "__scene", Plug::In ) );
	scenePlug()->setInput( view->inPlug<ScenePlug>() );

	view->viewportGadget()->preRenderSignal().connect( boost::bind( &TransformTool::preRender, this ) );
	plugDirtiedSignal().connect( boost::bind( &TransformTool::plugDirtied, this, ::_1 ) );

	connectToViewContext();
	view->contextChangedSignal().connect( boost::bind( &TransformTool::connectToViewContext, this ) );
}

TransformTool::~TransformTool()
{
}

const TransformTool::Selection &TransformTool::selection() const
{
	updateSelection();
	return m_selection;
}

GafferScene::ScenePlug *TransformTool::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *TransformTool::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

GafferUI::Gadget *TransformTool::handles()
{
	return m_handles.get();
}

const GafferUI::Gadget *TransformTool::handles() const
{
	return m_handles.get();
}

bool TransformTool::affectsHandlesTransform( const Gaffer::Plug *input ) const
{
	return false;
}

void TransformTool::connectToViewContext()
{
	m_contextChangedConnection = view()->getContext()->changedSignal().connect( boost::bind( &TransformTool::contextChanged, this, ::_2 ) );
}

void TransformTool::contextChanged( const IECore::InternedString &name )
{
	if(
		name == "ui:scene:selectedPaths" ||
		!boost::starts_with( name.string(), "ui:" )
	)
	{
		m_selectionDirty = true;
		m_handlesTransformDirty = true;
	}
}

void TransformTool::plugDirtied( const Gaffer::Plug *plug )
{
	if(
		plug == activePlug() ||
		plug == scenePlug()->childNamesPlug() ||
		plug == scenePlug()->transformPlug()
	)
	{
		m_selectionDirty = true;
		m_handlesTransformDirty = true;
	}

	if( affectsHandlesTransform( plug ) )
	{
		m_handlesTransformDirty = true;
	}
}

void TransformTool::updateSelection() const
{
	if( !m_selectionDirty )
	{
		return;
	}

	// Clear the selection.
	m_selection = Selection();
	m_selectionDirty = false;

	// If we're not active, then there's
	// no need to do anything.
	if( !activePlug()->getValue() )
	{
		return;
	}

	// Find the selected path, and early out if it's not valid.
	Selection newSelection;
	if( const IECore::StringVectorData *selection = view()->getContext()->get<IECore::StringVectorData>( "ui:scene:selectedPaths", NULL ) )
	{
		if( selection->readable().size() == 1 )
		{
			ScenePlug::stringToPath( selection->readable()[0], newSelection.path );
		}
	}
	if( newSelection.path.empty() || !exists( scenePlug(), newSelection.path ) )
	{
		return;
	}

	// Do an evaluation of the transform hash for our selection,
	// using a monitor to capture the upstream processes it triggers.
	CapturingMonitor monitor;
	{
		Monitor::Scope scopedMonitor( &monitor );
		ContextPtr tmpContext = new Context( *(view()->getContext()), Context::Borrowed );
		Context::Scope scopedContext( tmpContext.get() );
		tmpContext->set( ScenePlug::scenePathContextName, newSelection.path );
		// Trick to bypass the hash cache and get a full upstream evaluation.
		tmpContext->set( g_contextUniquefierName, g_contextUniquefierValue++ );
		scenePlug()->transformPlug()->hash();
	}

	// Iterate over the captured processes to update the selection with
	// the upstream transform plug we want to edit.

	if( updateSelectionWalk( monitor.rootProcesses(), newSelection ) )
	{
		newSelection.scene = scenePlug();
		newSelection.context = view()->getContext();
		m_selection = newSelection;
	}
}

void TransformTool::preRender()
{
	if( !m_dragging )
	{
		// In theory, an expression or some such could change the effective
		// transform plug while we're dragging (for instance, by driving the
		// enabled status of a downstream transform using the translate value
		// we're editing). But we ignore that on the grounds that it's unlikely,
		// and also that it would be very confusing for the edited plug to be
		// changed mid-drag.
		updateSelection();
	}

	if( !m_selection.transformPlug )
	{
		m_handles->setVisible( false );
		return;
	}

	m_handles->setVisible( true );

	if( m_handlesTransformDirty )
	{
		m_handles->setTransform( handlesTransform() );
		m_handlesTransformDirty = false;
	}
}

void TransformTool::dragBegin()
{
	m_dragging = true;
}

void TransformTool::dragEnd()
{
	m_dragging = false;
	m_mergeGroupId++;
}

std::string TransformTool::undoMergeGroup() const
{
	return boost::str( boost::format( "TransformTool%1%%2%" ) % this % m_mergeGroupId );
}

