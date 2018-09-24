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

#include "GafferSceneUI/TransformTool.h"

#include "GafferSceneUI/SceneView.h"
#include "GafferSceneUI/ContextAlgo.h"

#include "GafferScene/Group.h"
#include "GafferScene/ObjectSource.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/SceneReader.h"
#include "GafferScene/Transform.h"

#include "Gaffer/Animation.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/Monitor.h"
#include "Gaffer/Process.h"
#include "Gaffer/ScriptNode.h"

#include "OpenEXR/ImathMatrixAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind.hpp"
#include "boost/unordered_map.hpp"

#include "tbb/spin_mutex.h"

#include <memory>
#include <unordered_set>

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

	typedef std::unique_ptr<CapturedProcess> Ptr;
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

		~CapturingMonitor() override
		{
		}

		const CapturedProcess::PtrVector &rootProcesses()
		{
			return m_rootProcesses;
		}

	protected :

		void processStarted( const Process *process ) override
		{
			CapturedProcess::Ptr capturedProcess( new CapturedProcess );
			capturedProcess->type = process->type();
			capturedProcess->plug = process->plug();
			capturedProcess->context = new Context( *process->context() );

			Mutex::scoped_lock lock( m_mutex );

			m_processMap[process] = capturedProcess.get();

			if( process->parent() )
			{
				ProcessMap::const_iterator it = m_processMap.find( process->parent() );
				it->second->children.push_back( std::move( capturedProcess ) );
			}
			else
			{
				m_rootProcesses.push_back( std::move( capturedProcess ) );
			}
		}

		void processFinished( const Process *process ) override
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
		if( transform->filterPlug()->getValue() & PathMatcher::ExactMatch )
		{
			selection.transformPlug = const_cast<TransformPlug *>( transform->transformPlug() );
			ScenePlug::ScenePath spacePath = process->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
			switch( (GafferScene::Transform::Space)transform->spacePlug()->getValue() )
			{
				case GafferScene::Transform::Local :
					break;
				case GafferScene::Transform::Parent :
				case GafferScene::Transform::ResetLocal :
					spacePath.pop_back();
					break;
				case GafferScene::Transform::World :
				case GafferScene::Transform::ResetWorld :
					spacePath.clear();
					break;
			}
			selection.transformSpace = transform->inPlug()->fullTransform( spacePath );
		}
	}
	else if( const GafferScene::SceneReader *sceneReader = runTimeCast<const GafferScene::SceneReader>( node ) )
	{
		const ScenePlug::ScenePath &path = process->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
		if( path.size() == 1 )
		{
			selection.transformPlug = const_cast<TransformPlug *>( sceneReader->transformPlug() );
			selection.transformSpace = M44f();
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

class HandlesGadget : public Gadget
{

	public :

		HandlesGadget( const std::string &name="HandlesGadget" )
			:	Gadget( name )
		{
		}

	protected :

		void doRenderLayer( Layer layer, const Style *style ) const override
		{
			if( layer != Layer::MidFront )
			{
				return;
			}

			// Clear the depth buffer so that the handles render
			// over the top of the SceneGadget. Otherwise they are
			// unusable when the object is larger than the handles.
			/// \todo Can we really justify this approach? Does it
			/// play well with new Gadgets we'll add over time? If
			/// so, then we should probably move the depth clearing
			/// to `Gadget::render()`, in between each layer. If
			/// not we'll need to come up with something else, perhaps
			/// going back to punching a hole in the depth buffer using
			/// `glDepthFunc( GL_GREATER )`. Or maybe an option to
			/// render gadgets in an offscreen buffer before compositing
			/// them over the current framebuffer?
			glClearDepth( 1.0f );
			glClear( GL_DEPTH_BUFFER_BIT );
			glEnable( GL_DEPTH_TEST );

		}

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// TransformTool::Selection
//////////////////////////////////////////////////////////////////////////

TransformTool::Selection::Selection()
{
}

TransformTool::Selection::Selection(
	const GafferScene::ConstScenePlugPtr scene,
	const GafferScene::ScenePlug::ScenePath &path,
	const Gaffer::ConstContextPtr &context
)
	:	scene( scene ), path( path ), context( context )
{
	Context::Scope scopedContext( context.get() );
	if( path.empty() || !SceneAlgo::exists( scene.get(), path ) )
	{
		return;
	}

	// Do an evaluation of the transform hash for our selection,
	// using a monitor to capture the upstream processes it triggers.
	CapturingMonitor monitor;
	{
		Monitor::Scope scopedMonitor( &monitor );
		ScenePlug::PathScope pathScope( context.get(), path );
		// Trick to bypass the hash cache and get a full upstream evaluation.
		pathScope.set( g_contextUniquefierName, g_contextUniquefierValue++ );
		scene->transformPlug()->hash();
	}

	// Iterate over the captured processes to update the selection with
	// the upstream transform plug we want to edit.

	updateSelectionWalk( monitor.rootProcesses(), *this );
}

Imath::M44f TransformTool::Selection::sceneToTransformSpace() const
{
	M44f downstreamMatrix;
	{
		Context::Scope scopedContext( context.get() );
		downstreamMatrix = scene->fullTransform( path );
	}

	M44f upstreamMatrix;
	{
		Context::Scope scopedContext( upstreamContext.get() );
		upstreamMatrix = upstreamScene->fullTransform( upstreamPath );
	}

	return downstreamMatrix.inverse() * upstreamMatrix * transformSpace.inverse();
}

Imath::M44f TransformTool::Selection::orientedTransform( Orientation orientation ) const
{
	Context::Scope scopedContext( context.get() );

	// Get a matrix with the orientation we want

	M44f result;
	{
		switch( orientation )
		{
			case Local :
				result = scene->fullTransform( path );
				break;
			case Parent :
				if( path.size() )
				{
					const ScenePlug::ScenePath parentPath( path.begin(), path.end() - 1 );
					result = scene->fullTransform( parentPath );
				}
				break;
			case World :
				result = M44f();
				break;
		}
	}

	result = sansScaling( result );

	// And reset the translation to put it where the pivot is

	Context::Scope upstreamScope( upstreamContext.get() );

	const V3f pivot = transformPlug->pivotPlug()->getValue();
	const V3f translate = transformPlug->translatePlug()->getValue();
	const V3f downstreamWorldPivot = (pivot + translate) * sceneToTransformSpace().inverse();

	result[3][0] = downstreamWorldPivot[0];
	result[3][1] = downstreamWorldPivot[1];
	result[3][2] = downstreamWorldPivot[2];

	return result;
}

//////////////////////////////////////////////////////////////////////////
// TransformTool
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( TransformTool );

size_t TransformTool::g_firstPlugIndex = 0;

TransformTool::TransformTool( SceneView *view, const std::string &name )
	:	SelectionTool( view, name ),
		m_handles( new HandlesGadget() ),
		m_selectionDirty( true ),
		m_handlesDirty( true ),
		m_dragging( false ),
		m_mergeGroupId( 0 )
{
	view->viewportGadget()->addChild( m_handles );

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ScenePlug( "__scene", Plug::In ) );
	addChild( new FloatPlug( "size", Plug::In, 1.0f, 0.0f ) );

	scenePlug()->setInput( view->inPlug<ScenePlug>() );

	view->viewportGadget()->preRenderSignal().connect( boost::bind( &TransformTool::preRender, this ) );
	view->viewportGadget()->keyPressSignal().connect( boost::bind( &TransformTool::keyPress, this, ::_2 ) );
	plugDirtiedSignal().connect( boost::bind( &TransformTool::plugDirtied, this, ::_1 ) );

	connectToViewContext();
	view->contextChangedSignal().connect( boost::bind( &TransformTool::connectToViewContext, this ) );

	Metadata::plugValueChangedSignal().connect( boost::bind( &TransformTool::metadataChanged, this, ::_3 ) );
	Metadata::nodeValueChangedSignal().connect( boost::bind( &TransformTool::metadataChanged, this, ::_2 ) );
}

TransformTool::~TransformTool()
{
}

const std::vector<TransformTool::Selection> &TransformTool::selection() const
{
	updateSelection();
	return m_selection;
}

Imath::M44f TransformTool::handlesTransform()
{
	updateSelection();
	if( m_selection.empty() )
	{
		throw IECore::Exception( "Selection not valid" );
	}

	if( m_handlesDirty )
	{
		updateHandles( sizePlug()->getValue() * 75 );
		m_handlesDirty = false;
	}

	return handles()->getTransform();
}

GafferScene::ScenePlug *TransformTool::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *TransformTool::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *TransformTool::sizePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *TransformTool::sizePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

GafferUI::Gadget *TransformTool::handles()
{
	return m_handles.get();
}

const GafferUI::Gadget *TransformTool::handles() const
{
	return m_handles.get();
}

bool TransformTool::affectsHandles( const Gaffer::Plug *input ) const
{
	return input == sizePlug();
}

void TransformTool::connectToViewContext()
{
	m_contextChangedConnection = view()->getContext()->changedSignal().connect( boost::bind( &TransformTool::contextChanged, this, ::_2 ) );
}

void TransformTool::contextChanged( const IECore::InternedString &name )
{
	if(
		ContextAlgo::affectsSelectedPaths( name ) ||
		ContextAlgo::affectsLastSelectedPath( name ) ||
		!boost::starts_with( name.string(), "ui:" )
	)
	{
		m_selectionDirty = true;
		m_handlesDirty = true;
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
		m_handlesDirty = true;
	}
	else if( plug == sizePlug() )
	{
		m_handlesDirty = true;
		view()->viewportGadget()->renderRequestSignal()(
			view()->viewportGadget()
		);
	}

	if( affectsHandles( plug ) )
	{
		m_handlesDirty = true;
	}
}

void TransformTool::metadataChanged( IECore::InternedString key )
{
	if( !MetadataAlgo::readOnlyAffectedByChange( key ) || m_handlesDirty )
	{
		return;
	}

	// We could spend a little time here to figure out if the metadata
	// change definitely applies to `selection().transformPlug`, but that
	// would involve computing our selection, which might trigger a compute.
	// Our general rule is to delay all computes until `preRender()`
	// so that a hidden Viewer has no overhead, so we just assume the worst
	// for now and do a more accurate analysis in `updateHandles()`.

	m_handlesDirty = true;
	view()->viewportGadget()->renderRequestSignal()(
		view()->viewportGadget()
	);
}

void TransformTool::updateSelection() const
{
	if( !m_selectionDirty )
	{
		return;
	}

	// Clear the selection.
	m_selection.clear();
	m_selectionDirty = false;

	// If we're not active, then there's
	// no need to do anything.
	if( !activePlug()->getValue() )
	{
		return;
	}

	// Otherwise we need to populate our selection from
	// the scene selection.

	const PathMatcher selectedPaths = ContextAlgo::getSelectedPaths( view()->getContext() );
	if( selectedPaths.isEmpty() )
	{
		return;
	}

	const ScenePlug::ScenePath lastSelectedPath = ContextAlgo::getLastSelectedPath( view()->getContext() );
	assert( selectedPaths.match( lastSelectedPath ) & IECore::PathMatcher::ExactMatch );

	Selection lastSelection;
	std::unordered_set<Gaffer::TransformPlug *> transformPlugs;
	for( PathMatcher::Iterator it = selectedPaths.begin(), eIt = selectedPaths.end(); it != eIt; ++it )
	{
		Selection selection( scenePlug(), *it, view()->getContext() );
		if( selection.transformPlug )
		{
			// Selection is editable, but it's possible that we've already added it
			// (multiple paths may originate from the same node). We use the `transformPlugs`
			// set to ensure we only include any plug in the selection once.
			if( transformPlugs.insert( selection.transformPlug.get() ).second )
			{
				if( *it != lastSelectedPath )
				{
					m_selection.push_back( selection );
				}
				else
				{
					// We'll push this back last, outside the loop
					lastSelection = selection;
				}
			}
		}
		else
		{
			// Selection is not editable - give up.
			m_selection.clear();
			return;
		}
	}

	assert( lastSelection.transformPlug );
	m_selection.push_back( lastSelection );
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

	if( m_selection.empty() )
	{
		m_handles->setVisible( false );
		return;
	}

	m_handles->setVisible( true );

	if( m_handlesDirty )
	{
		updateHandles( sizePlug()->getValue() * 75 );
		m_handlesDirty = false;
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

bool TransformTool::keyPress( const GafferUI::KeyEvent &event )
{
	if( !activePlug()->getValue() )
	{
		return false;
	}

	if( event.key == "S" && !event.modifiers )
	{
		if( selection().empty() )
		{
			return false;
		}

		UndoScope undoScope( selection().back().transformPlug->ancestor<ScriptNode>() );
		for( const auto &s : selection() )
		{
			Context::Scope contextScope( s.context.get() );
			for( RecursiveFloatPlugIterator it( s.transformPlug.get() ); !it.done(); ++it )
			{
				FloatPlug *plug = it->get();
				if( Animation::canAnimate( plug ) )
				{
					const float value = plug->getValue();
					Animation::CurvePlug *curve = Animation::acquire( plug );
					curve->addKey( new Animation::Key( s.context->getTime(), value ) );
				}
			}
		}
		return true;
	}
	else if( event.key == "Plus" || event.key == "Equal" )
	{
		sizePlug()->setValue( sizePlug()->getValue() + 0.2 );
	}
	else if( event.key == "Minus" || event.key == "Underscore" )
	{
		sizePlug()->setValue( max( sizePlug()->getValue() - 0.2, 0.2 ) );
	}

	return false;
}

bool TransformTool::canSetValueOrAddKey( const Gaffer::FloatPlug *plug )
{
	if( Animation::isAnimated( plug ) )
	{
		return !MetadataAlgo::readOnly( plug->source() );
	}

	return plug->settable() && !MetadataAlgo::readOnly( plug );
}

void TransformTool::setValueOrAddKey( Gaffer::FloatPlug *plug, float time, float value )
{
	if( Animation::isAnimated( plug ) )
	{
		Animation::CurvePlug *curve = Animation::acquire( plug );
		curve->addKey( new Animation::Key( time, value ) );
	}
	else
	{
		plug->setValue( value );
	}
}
