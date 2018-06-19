//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferSceneUI/SceneGadget.h"

#include "GafferUI/ViewportGadget.h"

#include "Gaffer/BackgroundTask.h"
#include "Gaffer/Node.h"
#include "Gaffer/StringPlug.h"

#include "IECoreGL/CachedConverter.h"
#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/PointsPrimitive.h"
#include "IECoreGL/Primitive.h"
#include "IECoreGL/Renderable.h"
#include "IECoreGL/Selector.h"

#include "IECoreScene/CurvesPrimitive.h"

#include "IECore/MessageHandler.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind.hpp"

#include "tbb/concurrent_unordered_set.h"
#include "tbb/task.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// SceneGadget implementation
//////////////////////////////////////////////////////////////////////////

SceneGadget::SceneGadget()
	:	Gadget( defaultName<SceneGadget>() ),
		m_renderer( IECoreScenePreview::Renderer::create( "OpenGL", IECoreScenePreview::Renderer::Interactive ) ),
		m_controller( nullptr, nullptr, m_renderer ),
		m_renderRequestPending( false ),
		m_baseState( new IECoreGL::State( true ) )
{

	m_baseState->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0.2f, 0.2f, 0.2f, 1.0f ) ) );
	m_baseState->add( new IECoreGL::PointColorStateComponent( Color4f( 0.9f, 0.9f, 0.9f, 1.0f ) ) );
	m_baseState->add( new IECoreGL::Primitive::PointWidth( 2.0f ) );

	m_controller.updateRequiredSignal().connect(
		boost::bind( &SceneGadget::requestRender, this )
	);

	setContext( new Context );
}

SceneGadget::~SceneGadget()
{
	// Make sure background task completes before anything
	// it relies on is destroyed.
	m_updateTask.reset();
}

void SceneGadget::setScene( GafferScene::ConstScenePlugPtr scene )
{
	m_controller.setScene( scene );
}

const GafferScene::ScenePlug *SceneGadget::getScene() const
{
	return m_controller.getScene();
}

void SceneGadget::setContext( Gaffer::ConstContextPtr context )
{
	m_controller.setContext( context );
}

const Gaffer::Context *SceneGadget::getContext() const
{
	return m_controller.getContext();
}

void SceneGadget::setExpandedPaths( const IECore::PathMatcher &expandedPaths )
{
	m_controller.setExpandedPaths( expandedPaths );
}

const IECore::PathMatcher &SceneGadget::getExpandedPaths() const
{
	return m_controller.getExpandedPaths();
}

void SceneGadget::setMinimumExpansionDepth( size_t depth )
{
	m_controller.setMinimumExpansionDepth( depth );
}

size_t SceneGadget::getMinimumExpansionDepth() const
{
	return m_controller.getMinimumExpansionDepth();
}

IECoreGL::State *SceneGadget::baseState()
{
	return m_baseState.get();
}

bool SceneGadget::objectAt( const IECore::LineSegment3f &lineInGadgetSpace, GafferScene::ScenePlug::ScenePath &path ) const
{
	std::vector<IECoreGL::HitRecord> selection;
	{
		ViewportGadget::SelectionScope selectionScope( lineInGadgetSpace, this, selection, IECoreGL::Selector::IDRender );
		m_renderer->render();
	}

	if( !selection.size() )
	{
		return false;
	}

	PathMatcher paths = convertSelection( new UIntVectorData( { selection[0].name } ) );
	path = *PathMatcher::Iterator( paths.begin() );
	return true;
}

size_t SceneGadget::objectsAt(
	const Imath::V3f &corner0InGadgetSpace,
	const Imath::V3f &corner1InGadgetSpace,
	IECore::PathMatcher &paths
) const
{

	vector<IECoreGL::HitRecord> selection;
	{
		ViewportGadget::SelectionScope selectionScope( corner0InGadgetSpace, corner1InGadgetSpace, this, selection, IECoreGL::Selector::OcclusionQuery );
		m_renderer->render();
	}

	UIntVectorDataPtr ids = new UIntVectorData;
	std::transform(
		selection.begin(), selection.end(), std::back_inserter( ids->writable() ),
		[]( const IECoreGL::HitRecord &h ) { return h.name; }
	);

	PathMatcher selectedPaths = convertSelection( ids );
	paths.addPaths( selectedPaths );

	return selectedPaths.size();
}

IECore::PathMatcher SceneGadget::convertSelection( IECore::UIntVectorDataPtr ids ) const
{
	auto pathsData = static_pointer_cast<PathMatcherData>(
		m_renderer->command(
			"gl:querySelection",
			{
				{ "selection", ids }
			}
		)
	);

	PathMatcher result = pathsData->readable();

	// Unexpanded locations are represented with
	// objects named __unexpandedChildren__ to allow
	// locations to have an object _and_ children.
	// We want to replace any such locations with their
	// parent location.
	const InternedString unexpandedChildren = "__unexpandedChildren__";
	vector<InternedString> parent;

	PathMatcher toAdd;
	PathMatcher toRemove;
	for( PathMatcher::Iterator it = result.begin(), eIt = result.end(); it != eIt; ++it )
	{
		if( it->size() && it->back() == unexpandedChildren )
		{
			toRemove.addPath( *it );
			parent.assign( it->begin(), it->end() - 1 );
			toAdd.addPath( parent );
		}
	}

	result.addPaths( toAdd );
	result.removePaths( toRemove );

	return result;
}

const IECore::PathMatcher &SceneGadget::getSelection() const
{
	return m_selection;
}

void SceneGadget::setSelection( const IECore::PathMatcher &selection )
{
	m_selection = selection;
	ConstDataPtr d = new IECore::PathMatcherData( selection );
	m_renderer->option( "gl:selection", d.get() );
	requestRender();
}

Imath::Box3f SceneGadget::selectionBound() const
{
	DataPtr d = m_renderer->command( "gl:queryBound", { { "selection", new BoolData( true ) } } );
	return static_cast<Box3fData *>( d.get() )->readable();
}

std::string SceneGadget::getToolTip( const IECore::LineSegment3f &line ) const
{
	std::string result = Gadget::getToolTip( line );
	if( result.size() )
	{
		return result;
	}

	ScenePlug::ScenePath path;
	if( objectAt( line, path ) )
	{
		ScenePlug::pathToString( path, result );
	}

	return result;
}

Imath::Box3f SceneGadget::bound() const
{
	DataPtr d = m_renderer->command( "gl:queryBound" );
	return static_cast<Box3fData *>( d.get() )->readable();
}

void SceneGadget::doRenderLayer( Layer layer, const GafferUI::Style *style ) const
{
	if( layer != Layer::Main )
	{
		return;
	}

	if( IECoreGL::Selector::currentSelector() )
	{
		return;
	}

	const_cast<SceneGadget *>( this )->updateRenderer();
	m_renderer->render();
}

void SceneGadget::updateRenderer()
{
	if( m_updateTask )
	{
		if( m_updateTask->status() == BackgroundTask::Running )
		{
			return;
		}
		m_updateTask.reset();
	}

	if( !m_controller.updateRequired() )
	{
		return;
	}

	auto renderRequestCallback = [this] {
		if( refCount() && !m_renderRequestPending.exchange( true ) )
		{
			// Must hold a reference to stop us dying before our UI thread call is scheduled.
			SceneGadgetPtr thisRef = this;
			ParallelAlgo::callOnUIThread(
				[thisRef] {
					thisRef->m_renderRequestPending = false;
					thisRef->requestRender();
				}
			);
		}
	};

	m_updateTask = m_controller.updateInBackground( renderRequestCallback );
}
