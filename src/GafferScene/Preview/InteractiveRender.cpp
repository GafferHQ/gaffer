//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
#include "boost/algorithm/string/predicate.hpp"

#include "tbb/task.h"

#include "IECore/MessageHandler.h"
#include "IECore/VisibleRenderable.h"
#include "IECore/NullObject.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"

#include "GafferScene/Preview/RendererAlgo.h"
#include "GafferScene/Preview/InteractiveRender.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/SceneNode.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferScene::Preview;

//////////////////////////////////////////////////////////////////////////
// Private utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

InternedString g_cameraGlobalName( "option:render:camera" );

InternedString g_visibleAttributeName( "scene:visible" );

bool visible( const CompoundObject *attributes )
{
	const IECore::BoolData *d = attributes->member<IECore::BoolData>( g_visibleAttributeName );
	return d ? d->readable() : true;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Internal implementation details
//////////////////////////////////////////////////////////////////////////

// Represents a location in the Gaffer scene as specified to the
// renderer. We use this to build up a persistent representation of
// the scene which we can traverse to perform selective updates to
// only the changed locations. A Renderer's representation of the
// scene contains only a flat list of objects, whereas the SceneGraph
// maintains the original hierarchy, providing the means of flattening
// attribute and transform state for passing to the renderer. The
// various update() methods are called in order from a threaded scene
// traversal performed by SceneGraphUpdateTask based on which plugs
// have been dirtied since the last traversal.
class InteractiveRender::SceneGraph
{

	public :

		// We store separate scene graphs for
		// objects which are classified differently
		// by the renderer. This lets us output
		// lights (and soon cameras) prior to the
		// rest of the scene, which may be a
		// requirement of some renderer backends.
		enum Type
		{
			Camera = 0,
			Light = 1,
			Object = 2,
			First = Camera,
			Last = Object
		};

		// Constructs the root of the scene graph.
		// Children are constructed using updateChildren().
		SceneGraph()
			:	m_parent( NULL ), m_fullAttributes( new CompoundObject )
		{
			clear();
		}

		~SceneGraph()
		{
			clear();
		}

		const InternedString &name() const
		{
			return m_name;
		}

		// Returns false if the attributes make the location invisible, true otherwise.
		bool updateAttributes( const CompoundObjectPlug *attributesPlug, IECoreScenePreview::Renderer *renderer )
		{
			const IECore::MurmurHash attributesHash = attributesPlug->hash();
			if( attributesHash == m_attributesHash && !parentPending( AttributesPending ) )
			{
				return true;
			}

			ConstCompoundObjectPtr attributes = attributesPlug->getValue( &attributesHash );
			CompoundObject::ObjectMap &fullAttributes = m_fullAttributes->members();
			if( m_parent )
			{
				fullAttributes = m_parent->m_fullAttributes->members();
			}
			else
			{
				fullAttributes.clear();
			}

			for( CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; ++it )
			{
				fullAttributes[it->first] = it->second;
			}

			m_attributesInterface = NULL;
			m_attributesHash = attributesHash;
			m_pending = m_pending | AttributesPending;

			return ::visible( m_fullAttributes.get() );
		}

		// Version of the above for use at the root, where attributes come from the globals.
		// Also returns false if the attributes make the location invisible, true otherwise.
		bool updateAttributes( const CompoundObject *attributes )
		{
			assert( !m_parent );
			m_fullAttributes->members() = attributes->members();
			m_attributesInterface = NULL;
			m_pending = m_pending | AttributesPending;
			return ::visible( m_fullAttributes.get() );
		}

		void updateTransform( const M44fPlug *transformPlug )
		{
			const IECore::MurmurHash transformHash = transformPlug->hash();
			if( transformHash == m_transformHash && !parentPending( TransformPending ) )
			{
				return;
			}

			const M44f transform = transformPlug->getValue( &transformHash );
			if( m_parent )
			{
				m_fullTransform = transform * m_parent->m_fullTransform;
			}
			else
			{
				m_fullTransform = transform;
			}

			m_transformHash = transformHash;
			m_pending = m_pending | TransformPending;
		}

		void updateObject( const ObjectPlug *objectPlug, Type type, IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals )
		{
			if( !objectPlug )
			{
				clearObject();
				return;
			}

			const IECore::MurmurHash objectHash = objectPlug->hash();
			if( objectHash == m_objectHash )
			{
				return;
			}

			m_objectInterface = NULL;
			IECore::ConstObjectPtr object = objectPlug->getValue( &objectHash );
			m_objectHash = objectHash;

			const IECore::NullObject *nullObject = runTimeCast<const IECore::NullObject>( object.get() );
			if( (type != Light) && nullObject )
			{
				return;
			}

			std::string name;
			ScenePlug::pathToString( Context::current()->get<vector<InternedString> >( ScenePlug::scenePathContextName ), name );
			if( type == Camera )
			{
				if( const IECore::Camera *camera = runTimeCast<const IECore::Camera>( object.get() ) )
				{
					IECore::CameraPtr cameraCopy = camera->copy();
					applyCameraGlobals( cameraCopy.get(), globals );
					m_objectInterface = renderer->camera( name, cameraCopy.get() );
				}
			}
			else if( type == Light )
			{
				m_objectInterface = renderer->light( name, nullObject ? NULL : object.get() );
			}
			else
			{
				m_objectInterface = renderer->object( name, object.get() );
			}

			m_pending = m_pending | ObjectPending;
		}

		// Ensures that children() contains a child for every name specified
		// by childNamesPlug(). This just ensures that the children exist - they
		// will be subsequently be updated in parallel by the SceneGraphUpdateTask.
		bool updateChildren( const InternedStringVectorDataPlug *childNamesPlug )
		{
			const IECore::MurmurHash childNamesHash = childNamesPlug->hash();
			if( childNamesHash == m_childNamesHash )
			{
				return false;
			}

			IECore::ConstInternedStringVectorDataPtr childNamesData = childNamesPlug->getValue( &childNamesHash );
			const std::vector<IECore::InternedString> &childNames = childNamesData->readable();
			if( !existingChildNamesValid( childNames ) )
			{
				clearChildren();
				for( std::vector<IECore::InternedString>::const_iterator it = childNames.begin(), eIt = childNames.end(); it != eIt; ++it )
				{
					SceneGraph *child = new SceneGraph( *it, this );
					m_children.push_back( child );
				}
			}
			return true;
		}

		const std::vector<SceneGraph *> &children()
		{
			return m_children;
		}

		// Called after all children have been updated.
		// We use the finalisation step to apply our transform
		// and attributes to the object interface within the renderer.
		// We could actually do this in the update*() methods if
		// we wanted, but by deferring it until now we avoid
		// the situation where we update attributes, apply them
		// to the current object, then replace the object and have
		// to apply the attributes to the new object.
		void finalise( IECoreScenePreview::Renderer *renderer )
		{
			if( m_objectInterface )
			{
				if( m_pending & ( TransformPending | ObjectPending ) )
				{
					m_objectInterface->transform( m_fullTransform );
				}

				if( m_pending & ( AttributesPending | ObjectPending ) )
				{
					if( !m_attributesInterface )
					{
						m_attributesInterface = renderer->attributes( m_fullAttributes.get() );
					}
					m_objectInterface->attributes( m_attributesInterface.get() );
				}
			}

			m_pending = NonePending;
			m_cleared = false;
		}

		// Invalidates this location, removing any resources it
		// holds in the renderer, and clearing all children. This is
		// used to "remove" a location without having to delete it
		// from the children() of its parent. We avoid the latter
		// because it would involve some unwanted locking - we
		// process children in parallel, and therefore want to avoid
		// child updates having to write to the parent.
		void clear()
		{
			clearChildren();
			clearObject();
			m_attributesHash = m_transformHash = m_childNamesHash = IECore::MurmurHash();
			m_pending = NonePending;
			m_cleared = true;
		}

		// Returns true if the location has not been finalised
		// since the last call to clear() - ie that it is not
		// in a valid state.
		bool cleared()
		{
			return m_cleared;
		}

	private :

		SceneGraph( const InternedString &name, const SceneGraph *parent )
			:	m_name( name ), m_parent( parent ), m_fullAttributes( new CompoundObject )
		{
			clear();
		}

		void clearObject()
		{
			m_objectInterface = NULL;
			m_objectHash = MurmurHash();
		}

		void clearChildren()
		{
			for( std::vector<SceneGraph *>::const_iterator it = m_children.begin(), eIt = m_children.end(); it != eIt; ++it )
			{
				delete *it;
			}
			m_children.clear();
		}

		bool existingChildNamesValid( const vector<IECore::InternedString> &childNames ) const
		{
			if( m_children.size() != childNames.size() )
			{
				return false;
			}
			for( size_t i = 0, e = childNames.size(); i < e; ++i )
			{
				if( m_children[i]->m_name != childNames[i] )
				{
					return false;
				}
			}
			return true;
		}

		bool parentPending( unsigned pending )
		{
			if( !m_parent )
			{
				return false;
			}

			return m_parent->m_pending & pending;
		}

		IECore::InternedString m_name;

		const SceneGraph *m_parent;

		IECore::MurmurHash m_objectHash;
		IECoreScenePreview::Renderer::ObjectInterfacePtr m_objectInterface;

		IECore::MurmurHash m_attributesHash;
		IECore::CompoundObjectPtr m_fullAttributes;
		IECoreScenePreview::Renderer::AttributesInterfacePtr m_attributesInterface;

		IECore::MurmurHash m_transformHash;
		Imath::M44f m_fullTransform;

		IECore::MurmurHash m_childNamesHash;
		std::vector<SceneGraph *> m_children;

		// We need to defer some changes until finalise(),
		// and use this bitmask to keep track of what
		// changes are pending.
		enum Pending
		{
			NonePending = 0,
			AttributesPending = 1,
			TransformPending = 2,
			ObjectPending = 4,
		};
		unsigned char m_pending;
		bool m_cleared;

};

// TBB task used to perform multithreaded updates on our SceneGraph.
class InteractiveRender::SceneGraphUpdateTask : public tbb::task
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
			GlobalsDirty = 32,
			SetsDirty = 64,
			AllDirty = BoundDirty | TransformDirty | AttributesDirty | ObjectDirty | ChildNamesDirty | GlobalsDirty | SetsDirty
		};

		SceneGraphUpdateTask(
			const InteractiveRender *interactiveRender,
			SceneGraph *sceneGraph,
			SceneGraph::Type sceneGraphType,
			unsigned dirtyFlags,
			const ScenePlug::ScenePath &scenePath
		)
			:	m_interactiveRender( interactiveRender ),
				m_sceneGraph( sceneGraph ),
				m_sceneGraphType( sceneGraphType ),
				m_dirtyFlags( dirtyFlags ),
				m_scenePath( scenePath )
		{
		}

		virtual task *execute()
		{

			// Figure out if this location belongs in the type
			// of scene graph we're constructing. If it doesn't
			// belong, and neither do any of its descendants,
			// we can just early out.

			const unsigned sceneGraphMatch = this->sceneGraphMatch();
			if( !( sceneGraphMatch & ( Filter::ExactMatch | Filter::DescendantMatch ) ) )
			{
				m_sceneGraph->clear();
				return NULL;
			}

			if( m_sceneGraph->cleared() )
			{
				// We cleared this location in the past, but now
				// want it. So we need to start from scratch, and
				// update everything.
				m_dirtyFlags = AllDirty;
			}

			// Set up a context to compute the scene at the right
			// location.

			ContextPtr context = new Context( *m_interactiveRender->getContext(), Context::Borrowed );
			context->set( ScenePlug::scenePathContextName, m_scenePath );
			Context::Scope scopedContext( context.get() );

			// Update attributes. We do this first because we can then
			// exit early if the object is invisible.

			bool visible = true;
			if( m_scenePath.size() > 0 && (m_dirtyFlags & AttributesDirty ) )
			{
				visible = m_sceneGraph->updateAttributes( scene()->attributesPlug(), m_interactiveRender->m_renderer.get() );
			}

			if( !visible )
			{
				// No need to update further since we're not visible.
				m_sceneGraph->clear();
				return NULL;
			}

			// Update the transform.

			if( m_dirtyFlags & TransformDirty )
			{
				m_sceneGraph->updateTransform( scene()->transformPlug() );
			}

			// Update the object.
			if( sceneGraphMatch & Filter::ExactMatch )
			{
				if( m_dirtyFlags & ObjectDirty )
				{
					m_sceneGraph->updateObject( scene()->objectPlug(), m_sceneGraphType, m_interactiveRender->m_renderer.get(), m_interactiveRender->m_globals.get() );
				}
			}
			else
			{
				m_sceneGraph->updateObject( NULL, m_sceneGraphType, NULL, NULL );
			}

			// Update the children. This just ensures that they exist - we'll
			// update them in parallel in the next step.

			if( m_dirtyFlags & ChildNamesDirty )
			{
				if( m_sceneGraph->updateChildren( scene()->childNamesPlug() ) )
				{
					// We have new children, so they'll need a full update.
					m_dirtyFlags = AllDirty;
				}
			}

			// Spawn subtasks to apply updates to each child.

			const std::vector<SceneGraph *> &children = m_sceneGraph->children();
			if( children.size() )
			{
				set_ref_count( 1 + children.size() );

				ScenePlug::ScenePath childPath = m_scenePath;
				childPath.push_back( IECore::InternedString() ); // space for the child name
				for( std::vector<SceneGraph *>::const_iterator it = children.begin(), eIt = children.end(); it != eIt; ++it )
				{
					childPath.back() = (*it)->name();
					SceneGraphUpdateTask *t = new( allocate_child() ) SceneGraphUpdateTask( m_interactiveRender, *it, m_sceneGraphType, m_dirtyFlags, childPath );
					spawn( *t );
				}

				wait_for_all();
			}

			// Finally give the SceneGraph an opportunity to finalise
			// everything so the renderer is totally up to date.

			m_sceneGraph->finalise( m_interactiveRender->m_renderer.get() );

			return NULL;
		}

	private :

		const ScenePlug *scene()
		{
			return m_interactiveRender->inPlug();
		}

		/// \todo Fast path for when sets were not dirtied.
		const unsigned sceneGraphMatch() const
		{
			switch( m_sceneGraphType )
			{
				case SceneGraph::Camera :
					return m_interactiveRender->m_cameraSet.match( m_scenePath );
				case SceneGraph::Light :
					return m_interactiveRender->m_lightSet.match( m_scenePath );
				case SceneGraph::Object :
				{
					unsigned m = m_interactiveRender->m_lightSet.match( m_scenePath ) |
					             m_interactiveRender->m_cameraSet.match( m_scenePath );
					if( m & Filter::ExactMatch )
					{
						return Filter::AncestorMatch | Filter::DescendantMatch;
					}
					else
					{
						return Filter::EveryMatch;
					}
				}
				default :
					return Filter::NoMatch;
			}
		}

		const InteractiveRender *m_interactiveRender;
		SceneGraph *m_sceneGraph;
		SceneGraph::Type m_sceneGraphType;
		unsigned m_dirtyFlags;
		ScenePlug::ScenePath m_scenePath;

};

//////////////////////////////////////////////////////////////////////////
// InteractiveRender
//////////////////////////////////////////////////////////////////////////

size_t InteractiveRender::g_firstPlugIndex = 0;

IE_CORE_DEFINERUNTIMETYPED( InteractiveRender );

InteractiveRender::InteractiveRender( const std::string &name )
	:	Node( name )
{
	construct();
}

InteractiveRender::InteractiveRender( const IECore::InternedString &rendererType, const std::string &name )
	:	Node( name )
{
	construct( rendererType );
}

void InteractiveRender::construct( const IECore::InternedString &rendererType )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in" ) );
	addChild( new StringPlug( rendererType.string().empty() ? "renderer" : "__renderer", Plug::In, rendererType.string() ) );
	addChild( new IntPlug( "state", Plug::In, Stopped, Stopped, Paused, Plug::Default & ~Plug::Serialisable ) );
	addChild( new ScenePlug( "out", Plug::Out, Plug::Default & ~Plug::Serialisable ) );
	outPlug()->setInput( inPlug() );

	plugDirtiedSignal().connect( boost::bind( &InteractiveRender::plugDirtied, this, ::_1 ) );
	parentChangedSignal().connect( boost::bind( &InteractiveRender::parentChanged, this, ::_1, ::_2 ) );

	setContext( new Context() );
	stop(); // Use stop to initialise remaining member variables
}

InteractiveRender::~InteractiveRender()
{
	stop();
}

ScenePlug *InteractiveRender::inPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *InteractiveRender::inPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *InteractiveRender::rendererPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *InteractiveRender::rendererPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *InteractiveRender::statePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *InteractiveRender::statePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

ScenePlug *InteractiveRender::outPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 3 );
}

const ScenePlug *InteractiveRender::outPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 3 );
}

Gaffer::Context *InteractiveRender::getContext()
{
	return m_context.get();
}

const Gaffer::Context *InteractiveRender::getContext() const
{
	return m_context.get();
}

void InteractiveRender::setContext( Gaffer::ContextPtr context )
{
	if(
		m_context &&
		( m_context == context || *m_context == *context )
	)
	{
		return;
	}
	m_context = context;
	m_contextChangedConnection = m_context->changedSignal().connect(
		boost::bind( &InteractiveRender::contextChanged, this, ::_2 )
	);
}

void InteractiveRender::plugDirtied( const Gaffer::Plug *plug )
{

	if( plug == inPlug()->boundPlug() )
	{
		m_dirtyFlags |= SceneGraphUpdateTask::BoundDirty;
	}
	else if( plug == inPlug()->transformPlug() )
	{
		m_dirtyFlags |= SceneGraphUpdateTask::TransformDirty;
	}
	else if( plug == inPlug()->attributesPlug() )
	{
		m_dirtyFlags |= SceneGraphUpdateTask::AttributesDirty;
	}
	else if( plug == inPlug()->objectPlug() )
	{
		m_dirtyFlags |= SceneGraphUpdateTask::ObjectDirty;
	}
	else if( plug == inPlug()->childNamesPlug() )
	{
		m_dirtyFlags |= SceneGraphUpdateTask::ChildNamesDirty;
	}
	else if( plug == inPlug()->globalsPlug() )
	{
		m_dirtyFlags |= SceneGraphUpdateTask::GlobalsDirty;
	}
	else if( plug == inPlug()->setPlug() )
	{
		m_dirtyFlags |= SceneGraphUpdateTask::SetsDirty;
	}
	else if( plug == rendererPlug() )
	{
		stop();
		m_dirtyFlags = SceneGraphUpdateTask::AllDirty;
	}

	if( plug == inPlug() ||
	    plug == statePlug()
	)
	{
		try
		{
			update();
		}
		catch( const std::exception &e )
		{
			errorSignal()( plug, plug, e.what() );
		}
	}
}

void InteractiveRender::parentChanged( GraphComponent *child, GraphComponent *oldParent )
{
	ScriptNode *n = ancestor<ScriptNode>();
	if( n )
	{
		setContext( n->context() );
	}
	else
	{
		setContext( new Context() );
	}
}

void InteractiveRender::contextChanged( const IECore::InternedString &name )
{
	if( boost::starts_with( name.string(), "ui:" ) )
	{
		return;
	}
	m_dirtyFlags = SceneGraphUpdateTask::AllDirty;
	update();
}

void InteractiveRender::update()
{
	Context::Scope scopedContext( m_context.get() );

	const State requiredState = (State)statePlug()->getValue();

	// Stop the current render if we've been asked to, or if
	// there is no real input scene.

	if( requiredState == Stopped || !runTimeCast<SceneNode>( inPlug()->source<Plug>()->node() ) )
	{
		stop();
		return;
	}

	// If we've got this far, we know we want to be running or paused.
	// Start a render if we don't have one.

	if( !m_renderer )
	{
		m_renderer = IECoreScenePreview::Renderer::create(
			rendererPlug()->getValue(),
			IECoreScenePreview::Renderer::Interactive
		);
	}

	// We need to pause to make edits, even if we want to
	// be running in the end.
	m_renderer->pause();
	if( requiredState == Paused )
	{
		m_state = requiredState;
		return;
	}

	// We want to be running, so update the globals
	// and the scene graph, and kick off a render.
	assert( requiredState == Running );

	bool globalAttributesChanged = false;
	if( m_dirtyFlags & SceneGraphUpdateTask::GlobalsDirty )
	{
		ConstCompoundObjectPtr globals = inPlug()->globalsPlug()->getValue();
		outputOptions( globals.get(), m_globals.get(), m_renderer.get() );
		outputOutputs( globals.get(), m_globals.get(), m_renderer.get() );
		m_globals = globals;
		ConstCompoundObjectPtr globalAttributes = GafferScene::globalAttributes( m_globals.get() );
		if( *globalAttributes != *m_globalAttributes )
		{
			m_globalAttributes = globalAttributes;
			globalAttributesChanged = true;
			// Force attribute changes on the root to be
			// propagated through the scene graph.
			m_dirtyFlags |= SceneGraphUpdateTask::AttributesDirty;
		}
	}

	if( m_dirtyFlags & SceneGraphUpdateTask::SetsDirty )
	{
		m_lightSet = inPlug()->set( "__lights" )->readable();
		m_cameraSet = inPlug()->set( "__cameras" )->readable();
	}

	for( int i = SceneGraph::First; i <= SceneGraph::Last; ++i )
	{
		SceneGraph *sceneGraph = m_sceneGraphs[i].get();
		if( globalAttributesChanged || sceneGraph->cleared() )
		{
			if( !sceneGraph->updateAttributes( m_globalAttributes.get() ) )
			{
				// Deal with absurd case of visibility being turned off globally.
				sceneGraph->clear();
				continue;
			}
		}
		if( i == SceneGraph::Camera && ( m_dirtyFlags & SceneGraphUpdateTask::GlobalsDirty ) )
		{
			// Because the globals are applied to camera objects, we must update the object whenever
			// the globals have changed, so we clear the scene graph and start again. We don't expect
			// this to be a big overhead because typically there aren't many cameras in a scene. If it
			// does cause a problem, we could examine the exact changes to the globals and avoid clearing
			// if we know they won't affect the camera.
			sceneGraph->clear();
		}
		SceneGraphUpdateTask *task = new( tbb::task::allocate_root() ) SceneGraphUpdateTask( this, sceneGraph, (SceneGraph::Type)i, m_dirtyFlags, ScenePlug::ScenePath() );
		tbb::task::spawn_root_and_wait( *task );
	}

	if( m_dirtyFlags & SceneGraphUpdateTask::GlobalsDirty )
	{
		updateDefaultCamera();
	}

	m_dirtyFlags = SceneGraphUpdateTask::NothingDirty;
	m_state = requiredState;

	m_renderer->render();
}

void InteractiveRender::updateDefaultCamera()
{
	const StringData *cameraOption = m_globals->member<StringData>( g_cameraGlobalName );
	m_defaultCamera = NULL;
	if( cameraOption && !cameraOption->readable().empty() )
	{
		return;
	}

	CameraPtr defaultCamera = camera( inPlug(), m_globals.get() );
	StringDataPtr name = new StringData( "gaffer:defaultCamera" );
	m_defaultCamera = m_renderer->camera( name->readable(), defaultCamera.get() );
	m_renderer->option( "camera", name.get() );
}

void InteractiveRender::stop()
{
	m_sceneGraphs.clear();
	for( int i = SceneGraph::First; i <= SceneGraph::Last; ++i )
	{
		m_sceneGraphs.push_back( boost::make_shared<SceneGraph>() );
	}
	m_defaultCamera = NULL;
	m_renderer = NULL;

	m_globals = inPlug()->globalsPlug()->defaultValue();
	m_globalAttributes = inPlug()->globalsPlug()->defaultValue();
	m_lightSet.clear();

	m_dirtyFlags = SceneGraphUpdateTask::AllDirty;
	m_state = Stopped;
}
