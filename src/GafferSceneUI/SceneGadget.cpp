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

#include "tbb/task.h"
#include "tbb/concurrent_unordered_set.h"

#include "boost/bind.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "IECore/CurvesPrimitive.h"
#include "IECore/MessageHandler.h"

#include "IECoreGL/Renderable.h"
#include "IECoreGL/CachedConverter.h"
#include "IECoreGL/Primitive.h"
#include "IECoreGL/Selector.h"
#include "IECoreGL/CurvesPrimitive.h"

#include "GafferUI/ViewportGadget.h"

#include "GafferSceneUI/SceneGadget.h"
#include "GafferSceneUI/Visualiser.h"

using namespace std;
using namespace Imath;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// IECore::Object -> IECoreGL::Renderable conversion
//////////////////////////////////////////////////////////////////////////

namespace
{

IECoreGL::ConstRenderablePtr objectToRenderable( const IECore::Object *object )
{
	if( const Visualiser *visualiser = Visualiser::acquire( object->typeId() ) )
	{
		return visualiser->visualise( object );
	}

	try
	{
		IECore::ConstRunTimeTypedPtr glObject = IECoreGL::CachedConverter::defaultCachedConverter()->convert( object );
		return IECore::runTimeCast<const IECoreGL::Renderable>( glObject.get() );
	}
	catch( ... )
	{
		return NULL;
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Mechanism for deferred destruction of OpenGL resources.
// We use threads to update our scene graph in parallel, and as part of
// that we need to throw away IECoreGL objects that are no longer needed.
// We can only actually destroy them on the main thread when the GL context
// is active though, so we use this mechanism to defer the destruction till
// an appropriate time.
// \todo Similar ad-hoc mechanisms exist in IECoreGL (see removeObjectWalk
// in IECoreGL/Renderer.cpp, IECoreGL::CachedConverter::clearUnused() and
// IECoreGL::ShaderLoader::clearUnused()). Perhaps we could do this properly
// once and for all in IECoreGL, at the same time as introducing proper
// OpenGL context management?
//////////////////////////////////////////////////////////////////////////

namespace
{

tbb::concurrent_unordered_set<IECore::ConstRefCountedPtr> g_pendingReferenceRemovals;

template<typename T>
void deferReferenceRemoval( boost::intrusive_ptr<T> &o )
{
	// insert() can be called concurrently with other inserts.
	g_pendingReferenceRemovals.insert( o );
	o = NULL;
}

void doPendingReferenceRemovals()
{
	// clear() cannot be called concurrently with inserts, but
	// we only call this method from doRender(), which we know
	// is single threaded.
	g_pendingReferenceRemovals.clear();
	IECoreGL::CachedConverter::defaultCachedConverter()->clearUnused();
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// SceneGraph implementation
//
// This is effectively a replacement for IECoreGL::Scene, tailored
// specifically to work well with Gaffer. Our only good means of generating
// IECoreGL::Scenes is to use IECoreGL::Renderer, which would mean regenerating
// the entire scene for any change in Gaffer. By maintaining our own scene graph,
// we are able to make in-place edits to minimally reflect changes in Gaffer,
// yielding much improved performance.
//
// In the longer term, the following might be a good course of action :
//
// - Refactor SceneGraph into an IECoreGL::GLScene class which maps well
//   to Gaffer, but doesn't have direct Gaffer dependencies. It seems
//   promising to have this class implement IECore::SceneInterface, or
//   a future version tailored a little for broader use cases such as this
//   (the existing interface is a little file-specific).
// - Refactor UpdateTask into a class which couples Gaffer to
//   IECore::SceneInterfaces, performing minimal edits as necessary to
//   reflect changes in Gaffer.
// - Implement our renderer backends for RenderMan, Arnold etc as
//   SceneInterfaces. This is the most challenging part of this approach,
//   but the hope is that the SceneInterface is a better API for performing
//   render edits for IPR, rather than the nasty RI style API we currently
//   have.
// - Reuse the new UpdateTask in the InteractiveRender node.
//
//////////////////////////////////////////////////////////////////////////

class SceneGadget::SceneGraph
{

	public :

		SceneGraph()
			:	m_selected( false ), m_visible( true ), m_expanded( false )
		{
		}

		~SceneGraph()
		{
			clear();
		}

		void render( IECoreGL::State *currentState, IECoreGL::Selector *selector = NULL ) const
		{
			if( !m_visible || !valid() )
			{
				return;
			}

			const bool haveTransform = m_transform != M44f();
			if( haveTransform )
			{
				glPushMatrix();
				glMultMatrixf( m_transform.getValue() );
			}

				{
					IECoreGL::State::ScopedBinding scope( *m_state, *currentState );
					IECoreGL::State::ScopedBinding selectionScope( selectionState(), *currentState, m_selected );

					if( selector )
					{
						m_selectionId = selector->loadName();
					}

					if( m_renderable )
					{
						m_renderable->render( currentState );
					}

					if( m_boundRenderable )
					{
						IECoreGL::State::ScopedBinding wireframeScope( wireframeState(), *currentState );
						m_boundRenderable->render( currentState );
					}

					for( std::vector<SceneGraph *>::const_iterator it = m_children.begin(), eIt = m_children.end(); it != eIt; ++it )
					{
						(*it)->render( currentState, selector );
					}
				}

			if( haveTransform )
			{
				glPopMatrix();
			}
		}

		void applySelection( const PathMatcher &selection )
		{
			ScenePlug::ScenePath rootPath;
			applySelectionWalk( selection, rootPath, true );
		}

		bool pathFromSelectionId( GLuint selectionId, ScenePlug::ScenePath &path ) const
		{
			path.clear();
			const bool result = pathFromSelectionIdWalk( selectionId, path );
			std::reverse( path.begin(), path.end() );
			return result;
		}

		const Box3f &bound() const
		{
			return m_bound;
		}

		Box3f selectionBound() const
		{
			if( m_selected )
			{
				return m_bound;
			}
			else
			{
				Box3f childSelectionBound;
				for( std::vector<SceneGraph *>::const_iterator it = m_children.begin(), eIt = m_children.end(); it != eIt; ++it )
				{
					const Box3f childBound = transform( (*it)->selectionBound(), (*it)->m_transform );
					childSelectionBound.extendBy( childBound );
				}
				return childSelectionBound;
			}
		}

		bool valid() const
		{
			// Our m_state can be null if an exception occurred during update,
			// in which case we're not valid.
			return (bool)m_state;
		}

		void clear()
		{
			deferReferenceRemoval( m_state );
			deferReferenceRemoval( m_renderable );
			deferReferenceRemoval( m_boundRenderable );
			clearChildren();
			m_objectHash = m_attributesHash = IECore::MurmurHash();
		}

	private :

		friend class UpdateTask;

		void clearChildren()
		{
			for( std::vector<SceneGraph *>::const_iterator it = m_children.begin(), eIt = m_children.end(); it != eIt; ++it )
			{
				delete *it;
			}
			m_children.clear();
		}

		void applySelectionWalk( const PathMatcher &selection, const ScenePlug::ScenePath &path, bool check )
		{
			const unsigned m = check ? selection.match( path ) : 0;

			m_selected = m & Filter::ExactMatch;

			ScenePlug::ScenePath childPath = path;
			childPath.push_back( IECore::InternedString() ); // space for the child name
			for( std::vector<SceneGraph *>::const_iterator it = m_children.begin(), eIt = m_children.end(); it != eIt; ++it )
			{
				childPath.back() = (*it)->m_name;
				(*it)->applySelectionWalk( selection, childPath, m & Filter::DescendantMatch );
			}
		}

		bool pathFromSelectionIdWalk( GLuint selectionId, ScenePlug::ScenePath &path ) const
		{
			if( m_selectionId == selectionId )
			{
				path.push_back( m_name );
				return true;
			}
			else
			{
				for( std::vector<SceneGraph *>::const_iterator it = m_children.begin(), eIt = m_children.end(); it != eIt; ++it )
				{
					/// \todo Should be able to prune recursion based on knowledge that child
					/// selection ids are always greater than parent selection ids.
					if( (*it)->pathFromSelectionIdWalk( selectionId, path ) )
					{
						if( m_name != IECore::InternedString() )
						{
							path.push_back( m_name );
						}
						return true;
					}
				}
			}

			return false;
		}

		static const IECoreGL::State &selectionState()
		{
			static IECoreGL::StatePtr s;
			if( !s )
			{
				s = new IECoreGL::State( false );
				s->add( new IECoreGL::Primitive::DrawWireframe( true ), /* override = */ true );
				s->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0.466f, 0.612f, 0.741f, 1.0f ) ), /* override = */ true );
			}
			return *s;
		}

		static const IECoreGL::State &wireframeState()
		{
			static IECoreGL::StatePtr s;
			if( !s )
			{
				s = new IECoreGL::State( false );
				s->add( new IECoreGL::Primitive::DrawWireframe( true ), /* override = */ true );
				s->add( new IECoreGL::Primitive::DrawSolid( false ), /* override = */ true );
				s->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ), /* override = */ true );
			}
			return *s;
		}

		Imath::Box3f m_bound;
		Imath::M44f m_transform;
		IECore::InternedString m_name;
		IECoreGL::ConstStatePtr m_state;
		IECoreGL::ConstRenderablePtr m_renderable;
		IECoreGL::ConstRenderablePtr m_boundRenderable;
		std::vector<SceneGraph *> m_children;
		mutable GLuint m_selectionId;
		bool m_selected;
		bool m_visible;
		bool m_expanded;

		IECore::MurmurHash m_objectHash;
		IECore::MurmurHash m_attributesHash;

};

class SceneGadget::UpdateTask : public tbb::task
{

	public :

		enum DirtyFlags
		{
			NothingDirty = 0,
			BoundDirty = 1,
			TransformDirty = 2,
			AttributesDirty = 4,
			ObjectDirty = 8,
			ChildNamesDirty = 16,
			ExpansionDirty = 32,
			AllDirty = BoundDirty | TransformDirty | AttributesDirty | ObjectDirty | ChildNamesDirty | ExpansionDirty
		};

		UpdateTask( const SceneGadget *sceneGadget, SceneGraph *sceneGraph, unsigned dirtyFlags, const ScenePlug::ScenePath &scenePath )
			:	m_sceneGadget( sceneGadget ),
				m_sceneGraph( sceneGraph ),
				m_dirtyFlags( dirtyFlags ),
				m_scenePath( scenePath )
		{
		}

		virtual task *execute()
		{
			ContextPtr context = new Context( *m_sceneGadget->m_context, Context::Borrowed );
			context->set( ScenePlug::scenePathContextName, m_scenePath );
			Context::Scope scopedContext( context.get() );

			// Update attributes, and compute visibility.

			const bool previouslyVisible = m_sceneGraph->m_visible;
			if( m_dirtyFlags & AttributesDirty )
			{
				const IECore::MurmurHash attributesHash = m_sceneGadget->m_scene->attributesPlug()->hash();
				if( attributesHash != m_sceneGraph->m_attributesHash )
				{
					IECore::ConstCompoundObjectPtr attributes = m_sceneGadget->m_scene->attributesPlug()->getValue( &attributesHash );
					const IECore::BoolData *visibilityData = attributes->member<IECore::BoolData>( "scene:visible" );
					m_sceneGraph->m_visible = visibilityData ? visibilityData->readable() : true;

					IECore::ConstRunTimeTypedPtr glState = IECoreGL::CachedConverter::defaultCachedConverter()->convert( attributes.get() );
					deferReferenceRemoval( m_sceneGraph->m_state );
					m_sceneGraph->m_state = IECore::runTimeCast<const IECoreGL::State>( glState );

					m_sceneGraph->m_attributesHash = attributesHash;
				}
			}

			if( !m_sceneGraph->m_visible )
			{
				// No need to update further since we're not visible.
				return NULL;
			}
			else if( !previouslyVisible )
			{
				// We didn't perform any updates when we were invisible,
				// so we need to update everything now.
				m_dirtyFlags = AllDirty;
			}

			// Update the object - converting it into an IECoreGL::Renderable

			if( m_dirtyFlags & ObjectDirty )
			{
				const IECore::MurmurHash objectHash = m_sceneGadget->m_scene->objectPlug()->hash();
				if( objectHash != m_sceneGraph->m_objectHash )
				{
					IECore::ConstObjectPtr object = m_sceneGadget->m_scene->objectPlug()->getValue( &objectHash );
					deferReferenceRemoval( m_sceneGraph->m_renderable );
					if( !object->isInstanceOf( IECore::NullObjectTypeId ) )
					{
						m_sceneGraph->m_renderable = objectToRenderable( object.get() );
					}
					m_sceneGraph->m_objectHash = objectHash;
				}
			}

			// Update the transform and bound

			if( m_dirtyFlags & TransformDirty )
			{
				m_sceneGraph->m_transform = m_sceneGadget->m_scene->transformPlug()->getValue();
			}

			m_sceneGraph->m_bound = m_sceneGraph->m_renderable ? m_sceneGraph->m_renderable->bound() : Box3f();

			// Update the expansion state

			const bool previouslyExpanded = m_sceneGraph->m_expanded;
			if( m_dirtyFlags & ExpansionDirty )
			{
				m_sceneGraph->m_expanded = m_sceneGadget->m_minimumExpansionDepth >= m_scenePath.size();
				if( !m_sceneGraph->m_expanded )
				{
					m_sceneGraph->m_expanded = m_sceneGadget->m_expandedPaths->readable().match( m_scenePath ) & Filter::ExactMatch;
				}
			}

			// If we're not expanded, then we can early out after creating a bounding box.

			deferReferenceRemoval( m_sceneGraph->m_boundRenderable );
			if( !m_sceneGraph->m_expanded )
			{
				// We're not expanded, so we early out before updating the children.
				// We do however need to see if we have any children, and arrange to
				// draw their bounding box if we do.
				bool haveChildren = m_sceneGraph->m_children.size();
				if( m_dirtyFlags & ChildNamesDirty || !previouslyExpanded )
				{
					IECore::ConstInternedStringVectorDataPtr childNamesData = m_sceneGadget->m_scene->childNamesPlug()->getValue();
					haveChildren = childNamesData->readable().size();
				}

				m_sceneGraph->clearChildren();

				m_sceneGraph->m_bound.extendBy( m_sceneGadget->m_scene->boundPlug()->getValue() );

				if( haveChildren )
				{
					IECore::CurvesPrimitivePtr curvesBound = IECore::CurvesPrimitive::createBox( m_sceneGraph->m_bound );
					m_sceneGraph->m_boundRenderable = boost::static_pointer_cast<const IECoreGL::Renderable>(
						IECoreGL::CachedConverter::defaultCachedConverter()->convert( curvesBound.get() )
					);
				}
				return NULL;
			}

			// We are expanded, so we need to visit all the children
			// and update those too.

			if( !previouslyExpanded )
			{
				m_dirtyFlags = AllDirty;
			}

			// Make sure we have a child for each child name

			if( m_dirtyFlags & ChildNamesDirty )
			{
				IECore::ConstInternedStringVectorDataPtr childNamesData = m_sceneGadget->m_scene->childNamesPlug()->getValue();
				const std::vector<IECore::InternedString> &childNames = childNamesData->readable();
				if( !existingChildNamesValid( childNames ) )
				{
					m_sceneGraph->clearChildren();

					for( std::vector<IECore::InternedString>::const_iterator it = childNames.begin(), eIt = childNames.end(); it != eIt; ++it )
					{
						SceneGraph *child = new SceneGraph();
						child->m_name = *it;
						m_sceneGraph->m_children.push_back( child );
					}

					m_dirtyFlags = AllDirty; // We've made brand new children, so they need a full update.
				}
			}

			// And then update each child

			if( m_sceneGraph->m_children.size() )
			{
				set_ref_count( 1 + m_sceneGraph->m_children.size() );

				ScenePlug::ScenePath childPath = m_scenePath;
				childPath.push_back( IECore::InternedString() ); // space for the child name
				for( std::vector<SceneGraph *>::const_iterator it = m_sceneGraph->m_children.begin(), eIt = m_sceneGraph->m_children.end(); it != eIt; ++it )
				{
					childPath.back() = (*it)->m_name;
					UpdateTask *t = new( allocate_child() ) UpdateTask( m_sceneGadget, *it, m_dirtyFlags, childPath );
					spawn( *t );
				}

				wait_for_all();
			}

			// Finally compute our bound from the child bounds.

			for( std::vector<SceneGraph *>::const_iterator it = m_sceneGraph->m_children.begin(), eIt = m_sceneGraph->m_children.end(); it != eIt; ++it )
			{
				const Box3f childBound = transform( (*it)->m_bound, (*it)->m_transform );
				m_sceneGraph->m_bound.extendBy( childBound );
			}

			return NULL;
		}

	private :

		bool existingChildNamesValid( const vector<IECore::InternedString> &childNames )
		{
			if( m_sceneGraph->m_children.size() != childNames.size() )
			{
				return false;
			}
			for( size_t i = 0, e = childNames.size(); i < e; ++i )
			{
				if( m_sceneGraph->m_children[i]->m_name != childNames[i] )
				{
					return false;
				}
			}
			return true;
		}

		const SceneGadget *m_sceneGadget;
		SceneGraph *m_sceneGraph;
		unsigned m_dirtyFlags;
		ScenePlug::ScenePath m_scenePath;

};

//////////////////////////////////////////////////////////////////////////
// SceneGadget implementation
//////////////////////////////////////////////////////////////////////////

SceneGadget::SceneGadget()
	:	Gadget( defaultName<SceneGadget>() ),
		m_scene( NULL ),
		m_context( NULL ),
		m_dirtyFlags( UpdateTask::AllDirty ),
		m_expandedPaths( new PathMatcherData ),
		m_minimumExpansionDepth( 0 ),
		m_baseState( new IECoreGL::State( true ) ),
		m_sceneGraph( new SceneGraph ),
		m_selection( new PathMatcherData )
{
	setContext( new Context );
}

SceneGadget::~SceneGadget()
{
}

void SceneGadget::setScene( GafferScene::ConstScenePlugPtr scene )
{
	if( scene == m_scene )
	{
		return;
	}

	m_scene = scene;
	if( Gaffer::Node *node = const_cast<Gaffer::Node *>( scene->node() ) )
	{
		m_plugDirtiedConnection = node->plugDirtiedSignal().connect( boost::bind( &SceneGadget::plugDirtied, this, ::_1 ) );
	}
	else
	{
		m_plugDirtiedConnection.disconnect();
	}

	m_dirtyFlags = UpdateTask::AllDirty;
	requestRender();
}

const GafferScene::ScenePlug *SceneGadget::getScene() const
{
	return m_scene.get();
}

void SceneGadget::setContext( Gaffer::ContextPtr context )
{
	if( context == m_context )
	{
		return;
	}

	m_context = context;
	m_contextChangedConnection = m_context->changedSignal().connect( boost::bind( &SceneGadget::contextChanged, this, ::_2 ) );
	requestRender();
}

Gaffer::Context *SceneGadget::getContext()
{
	return m_context.get();
}

const Gaffer::Context *SceneGadget::getContext() const
{
	return m_context.get();
}

void SceneGadget::setExpandedPaths( GafferScene::ConstPathMatcherDataPtr expandedPaths )
{
	m_expandedPaths = expandedPaths;
	m_dirtyFlags |= UpdateTask::ExpansionDirty;
	requestRender();
}

const GafferScene::PathMatcherData *SceneGadget::getExpandedPaths() const
{
	return m_expandedPaths.get();
}

void SceneGadget::setMinimumExpansionDepth( size_t depth )
{
	if( depth == m_minimumExpansionDepth )
	{
		return;
	}
	m_minimumExpansionDepth = depth;
	m_dirtyFlags |= UpdateTask::ExpansionDirty;
	requestRender();
}

size_t SceneGadget::getMinimumExpansionDepth() const
{
	return m_minimumExpansionDepth;
}

IECoreGL::State *SceneGadget::baseState()
{
	return m_baseState.get();
}

bool SceneGadget::objectAt( const IECore::LineSegment3f &lineInGadgetSpace, GafferScene::ScenePlug::ScenePath &path ) const
{
	updateSceneGraph();

	std::vector<IECoreGL::HitRecord> selection;
	{
		ViewportGadget::SelectionScope selectionScope( lineInGadgetSpace, this, selection, IECoreGL::Selector::IDRender );
		renderSceneGraph( selectionScope.baseState() );
	}

	if( !selection.size() )
	{
		return false;
	}

	return m_sceneGraph->pathFromSelectionId( selection[0].name, path );
}

size_t SceneGadget::objectsAt(
	const Imath::V3f &corner0InGadgetSpace,
	const Imath::V3f &corner1InGadgetSpace,
	GafferScene::PathMatcher &paths
) const
{
	updateSceneGraph();

	std::vector<IECoreGL::HitRecord> selection;
	{
		ViewportGadget::SelectionScope selectionScope( corner0InGadgetSpace, corner1InGadgetSpace, this, selection, IECoreGL::Selector::OcclusionQuery );
		renderSceneGraph( selectionScope.baseState() );
	}

	size_t result = 0;
	ScenePlug::ScenePath path;
	for( std::vector<IECoreGL::HitRecord>::const_iterator it = selection.begin(), eIt = selection.end(); it != eIt; ++it )
	{
		if( m_sceneGraph->pathFromSelectionId( it->name, path ) )
		{
			result += paths.addPath( path );
		}
	}

	return result;
}

const GafferScene::PathMatcherData *SceneGadget::getSelection() const
{
	return m_selection.get();
}

void SceneGadget::setSelection( ConstPathMatcherDataPtr selection )
{
	m_selection = selection;
	m_sceneGraph->applySelection( m_selection->readable() );
	requestRender();
}

Imath::Box3f SceneGadget::selectionBound() const
{
	updateSceneGraph();
	return m_sceneGraph->selectionBound();
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
	updateSceneGraph();
	return m_sceneGraph->bound();
}

void SceneGadget::doRender( const GafferUI::Style *style ) const
{
	if( !m_scene || IECoreGL::Selector::currentSelector() )
	{
		return;
	}

	updateSceneGraph();
	renderSceneGraph( m_baseState.get() );

	doPendingReferenceRemovals();
}

void SceneGadget::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == m_scene->boundPlug() )
	{
		m_dirtyFlags |= UpdateTask::BoundDirty;
	}
	else if( plug == m_scene->transformPlug() )
	{
		m_dirtyFlags |= UpdateTask::TransformDirty;
	}
	else if( plug == m_scene->attributesPlug() )
	{
		m_dirtyFlags |= UpdateTask::AttributesDirty;
	}
	else if( plug == m_scene->objectPlug() )
	{
		m_dirtyFlags |= UpdateTask::ObjectDirty;
	}
	else if( plug == m_scene->childNamesPlug() )
	{
		m_dirtyFlags |= UpdateTask::ChildNamesDirty;
	}
	else
	{
		return;
	}

	requestRender();
}

void SceneGadget::contextChanged( const IECore::InternedString &name )
{
	if( !boost::starts_with( name.string(), "ui:" ) )
	{
		m_dirtyFlags = UpdateTask::AllDirty;
		requestRender();
	}
}

void SceneGadget::updateSceneGraph() const
{
	if( !m_dirtyFlags )
	{
		return;
	}

	if( !m_sceneGraph->valid() )
	{
		// The previous attempt at an update failed - so
		// we need to update everything this time.
		m_dirtyFlags = UpdateTask::AllDirty;
	}

	try
	{
		UpdateTask *task = new( tbb::task::allocate_root() ) UpdateTask( this, m_sceneGraph.get(), m_dirtyFlags, ScenePlug::ScenePath() );
		tbb::task::spawn_root_and_wait( *task );

		if( m_dirtyFlags && UpdateTask::ChildNamesDirty )
		{
			m_sceneGraph->applySelection( m_selection->readable() );
		}
	}
	catch( const std::exception& e )
	{
		m_sceneGraph->clear();
		IECore::msg( IECore::Msg::Error, "SceneGadget::updateSceneGraph", e.what() );
	}

	// Even if an error occurred when updating the scene, we clear
	// the dirty flags. This prevents us from repeating the same
	// error over and over when nothing has been done to prevent it.
	// When something is next dirtied we'll turn on all the dirty
	// flags (see above) to ensure that the next update is a complete
	// one.
	m_dirtyFlags = UpdateTask::NothingDirty;
}

void SceneGadget::renderSceneGraph( const IECoreGL::State *stateToBind ) const
{
	GLint prevProgram;
	glGetIntegerv( GL_CURRENT_PROGRAM, &prevProgram );
	glPushAttrib( GL_ALL_ATTRIB_BITS );

	try
	{
		IECoreGL::State::bindBaseState();
		stateToBind->bind();
		m_sceneGraph->render( const_cast<IECoreGL::State *>( stateToBind ), IECoreGL::Selector::currentSelector() );
	}
	catch( const std::exception& e )
	{
		IECore::msg( IECore::Msg::Error, "SceneGadget::renderSceneGraph", e.what() );
	}

	glPopAttrib();
	glUseProgram( prevProgram );
}
