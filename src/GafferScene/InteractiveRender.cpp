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
#include "GafferScene/InteractiveRender.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/SceneNode.h"
#include "GafferScene/SceneProcessor.h"
#include "GafferScene/RendererAlgo.h"

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
InternedString g_setsAttributeName( "sets" );
InternedString g_rendererContextName( "scene:renderer" );

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
// attribute and transform state for passing to the renderer. Calls
// to update() are made from a threaded scene traversal performed by
// SceneGraphUpdateTask.
class InteractiveRender::SceneGraph
{

	public :

		// We store separate scene graphs for
		// objects which are classified differently
		// by the renderer. This lets us output
		// lights and cameras prior to the
		// rest of the scene, which may be a
		// requirement of some renderer backends.
		enum Type
		{
			CameraType = 0,
			LightType = 1,
			ObjectType = 2,
			FirstType = CameraType,
			LastType = ObjectType,
			NoType = LastType + 1
		};

		enum Component
		{
			NoComponent = 0,
			BoundComponent = 1,
			TransformComponent = 2,
			AttributesComponent = 4,
			ObjectComponent = 8,
			ChildNamesComponent = 16,
			GlobalsComponent = 32,
			SetsComponent = 64,
			RenderSetsComponent = 128, // Sets prefixed with "render:"
			AllComponents = BoundComponent | TransformComponent | AttributesComponent | ObjectComponent | ChildNamesComponent | GlobalsComponent | SetsComponent | RenderSetsComponent
		};

		// Constructs the root of the scene graph.
		// Children are constructed using updateChildren().
		SceneGraph()
			:	m_parent( nullptr ), m_fullAttributes( new CompoundObject )
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

		// Called by SceneGraphUpdateTask to update this location. Returns a bitmask
		// of the components which were changed.
		unsigned update( const ScenePlug *scene, const ScenePlug::ScenePath &path, unsigned dirtyComponents, unsigned changedParentComponents, Type type, IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const Preview::RendererAlgo::RenderSets &renderSets )
		{
			unsigned changedComponents = 0;

			// Attributes

			if( !m_parent )
			{
				// Root - get attributes from globals.
				if( dirtyComponents & GlobalsComponent )
				{
					if( updateAttributes( globals ) )
					{
						changedComponents |= AttributesComponent;
					}
				}
			}
			else
			{
				// Non-root - get attributes the standard way.
				const bool parentAttributesChanged = changedParentComponents & AttributesComponent;
				if( parentAttributesChanged || ( dirtyComponents & AttributesComponent ) )
				{
					if( updateAttributes( scene->attributesPlug(), parentAttributesChanged ) )
					{
						changedComponents |= AttributesComponent;
					}
				}
			}

			if( !::visible( m_fullAttributes.get() ) )
			{
				clear();
				return changedComponents;
			}

			// Render Sets. We must obviously update these if
			// the sets have changed, but we also need to do an
			// update if the attributes have changed, because in
			// that case we may have overwritten the sets attribute.

			if( ( dirtyComponents & RenderSetsComponent ) || ( changedComponents & AttributesComponent ) )
			{
				if( updateRenderSets( path, renderSets ) )
				{
					changedComponents |= AttributesComponent;
				}
			}

			// Transform

			if( ( dirtyComponents & TransformComponent ) && updateTransform( scene->transformPlug(), changedParentComponents & TransformComponent ) )
			{
				changedComponents |= TransformComponent;
			}

			// Object

			if( ( dirtyComponents & ObjectComponent ) && updateObject( scene->objectPlug(), type, renderer, globals ) )
			{
				changedComponents |= ObjectComponent;
			}

			// Object updates for transform and attributes

			if( m_objectInterface )
			{
				if( !(changedComponents & ObjectComponent) )
				{
					// Apply attribute update to old object if necessary.
					if( changedComponents & AttributesComponent )
					{
						if( !m_objectInterface->attributes( attributesInterface( renderer ) ) )
						{
							// Failed to apply attributes - must replace entire object.
							m_objectHash = MurmurHash();
							if( updateObject( scene->objectPlug(), type, renderer, globals ) )
							{
								changedComponents |= ObjectComponent;
							}
						}
					}
				}

				// If the transform has changed, or we have an entirely new object,
				// the apply the transform.
				if( changedComponents & ( ObjectComponent | TransformComponent ) )
				{
					m_objectInterface->transform( m_fullTransform );
				}
			}

			// Children

			if( ( dirtyComponents & ChildNamesComponent ) && updateChildren( scene->childNamesPlug() ) )
			{
				changedComponents |= ChildNamesComponent;
			}

			m_cleared = false;

			return changedComponents;
		}

		const std::vector<SceneGraph *> &children()
		{
			return m_children;
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

		// Returns true if the attributes changed.
		bool updateAttributes( const CompoundObjectPlug *attributesPlug, bool parentAttributesChanged )
		{
			assert( m_parent );

			const IECore::MurmurHash attributesHash = attributesPlug->hash();
			if( attributesHash == m_attributesHash && !parentAttributesChanged )
			{
				return false;
			}

			ConstCompoundObjectPtr attributes = attributesPlug->getValue( &attributesHash );
			CompoundObject::ObjectMap &fullAttributes = m_fullAttributes->members();
			fullAttributes = m_parent->m_fullAttributes->members();
			for( CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; ++it )
			{
				fullAttributes[it->first] = it->second;
			}

			m_attributesInterface = nullptr; // Will be updated lazily in attributesInterface()
			m_attributesHash = attributesHash;

			return true;
		}

		// As above, but for use at the root.
		bool updateAttributes( const CompoundObject *globals )
		{
			assert( !m_parent );

			ConstCompoundObjectPtr globalAttributes = GafferScene::SceneAlgo::globalAttributes( globals );
			if( m_fullAttributes && *m_fullAttributes == *globalAttributes )
			{
				return false;
			}

			m_fullAttributes->members() = globalAttributes->members();
			m_attributesInterface = nullptr;

			return true;
		}

		bool updateRenderSets( const ScenePlug::ScenePath &path, const Preview::RendererAlgo::RenderSets &renderSets )
		{
			m_fullAttributes->members()[g_setsAttributeName] = boost::const_pointer_cast<InternedStringVectorData>(
				renderSets.setsAttribute( path )
			);
			m_attributesInterface = nullptr;
			return true;
		}

		IECoreScenePreview::Renderer::AttributesInterface *attributesInterface( IECoreScenePreview::Renderer *renderer )
		{
			if( !m_attributesInterface )
			{
				m_attributesInterface = renderer->attributes( m_fullAttributes.get() );
			}
			return m_attributesInterface.get();
		}

		// Returns true if the transform changed.
		bool updateTransform( const M44fPlug *transformPlug, bool parentTransformChanged )
		{
			const IECore::MurmurHash transformHash = transformPlug->hash();
			if( transformHash == m_transformHash && !parentTransformChanged )
			{
				return false;
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
			return true;
		}

		// Returns true if the object changed.
		bool updateObject( const ObjectPlug *objectPlug, Type type, IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals )
		{
			const bool hadObjectInterface = static_cast<bool>( m_objectInterface );
			if( type == NoType )
			{
				m_objectInterface = nullptr;
				return hadObjectInterface;
			}

			const IECore::MurmurHash objectHash = objectPlug->hash();
			if( objectHash == m_objectHash )
			{
				return false;
			}

			m_objectInterface = nullptr;

			IECore::ConstObjectPtr object = objectPlug->getValue( &objectHash );
			m_objectHash = objectHash;

			const IECore::NullObject *nullObject = runTimeCast<const IECore::NullObject>( object.get() );
			if( (type != LightType) && nullObject )
			{
				return hadObjectInterface;
			}

			std::string name;
			ScenePlug::pathToString( Context::current()->get<vector<InternedString> >( ScenePlug::scenePathContextName ), name );
			if( type == CameraType )
			{
				if( const IECore::Camera *camera = runTimeCast<const IECore::Camera>( object.get() ) )
				{
					IECore::CameraPtr cameraCopy = camera->copy();

					// Explicit namespace can be removed once deprecated applyCameraGlobals
					// is removed from GafferScene::SceneAlgo
					GafferScene::Preview::RendererAlgo::applyCameraGlobals( cameraCopy.get(), globals );
					m_objectInterface = renderer->camera( name, cameraCopy.get(), attributesInterface( renderer ) );
				}
			}
			else if( type == LightType )
			{
				m_objectInterface = renderer->light( name, nullObject ? nullptr : object.get(), attributesInterface( renderer ) );
			}
			else
			{
				m_objectInterface = renderer->object( name, object.get(), attributesInterface( renderer ) );
			}

			return true;
		}

		void clearObject()
		{
			m_objectInterface = nullptr;
			m_objectHash = MurmurHash();
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

		bool m_cleared;

};

// TBB task used to perform multithreaded updates on our SceneGraph.
class InteractiveRender::SceneGraphUpdateTask : public tbb::task
{

	public :

		SceneGraphUpdateTask(
			const InteractiveRender *interactiveRender,
			SceneGraph *sceneGraph,
			SceneGraph::Type sceneGraphType,
			unsigned dirtyComponents,
			unsigned changedParentComponents,
			const Context *context,
			const ScenePlug::ScenePath &scenePath
		)
			:	m_interactiveRender( interactiveRender ),
				m_sceneGraph( sceneGraph ),
				m_sceneGraphType( sceneGraphType ),
				m_dirtyComponents( dirtyComponents ),
				m_changedParentComponents( changedParentComponents ),
				m_context( context ),
				m_scenePath( scenePath )
		{
		}

		task *execute() override
		{

			// Figure out if this location belongs in the type
			// of scene graph we're constructing. If it doesn't
			// belong, and neither do any of its descendants,
			// we can just early out.

			const unsigned sceneGraphMatch = this->sceneGraphMatch();
			if( !( sceneGraphMatch & ( Filter::ExactMatch | Filter::DescendantMatch ) ) )
			{
				m_sceneGraph->clear();
				return nullptr;
			}

			if( m_sceneGraph->cleared() )
			{
				// We cleared this location in the past, but now
				// want it. So we need to start from scratch, and
				// update everything.
				m_dirtyComponents = SceneGraph::AllComponents;
			}

			// Set up a context to compute the scene at the right
			// location.

			ScenePlug::PathScope pathScope( m_context, m_scenePath );

			// Update the scene graph at this location.

			unsigned changedComponents = m_sceneGraph->update(
				scene(),
				m_scenePath,
				m_dirtyComponents,
				m_changedParentComponents,
				sceneGraphMatch & Filter::ExactMatch ? m_sceneGraphType : SceneGraph::NoType,
				m_interactiveRender->m_renderer.get(),
				m_interactiveRender->m_globals.get(),
				m_interactiveRender->m_renderSets
			);

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
					SceneGraphUpdateTask *t = new( allocate_child() ) SceneGraphUpdateTask( m_interactiveRender, *it, m_sceneGraphType, m_dirtyComponents, changedComponents, m_context, childPath );
					spawn( *t );
				}

				wait_for_all();
			}

			return nullptr;
		}

	private :

		const ScenePlug *scene()
		{
			return m_interactiveRender->adaptedInPlug();
		}

		/// \todo Fast path for when sets were not dirtied.
		const unsigned sceneGraphMatch() const
		{
			switch( m_sceneGraphType )
			{
				case SceneGraph::CameraType :
					return m_interactiveRender->m_renderSets.camerasSet().match( m_scenePath );
				case SceneGraph::LightType :
					return m_interactiveRender->m_renderSets.lightsSet().match( m_scenePath );
				case SceneGraph::ObjectType :
				{
					unsigned m = m_interactiveRender->m_renderSets.lightsSet().match( m_scenePath ) |
					             m_interactiveRender->m_renderSets.camerasSet().match( m_scenePath );
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
		unsigned m_dirtyComponents;
		unsigned m_changedParentComponents;
		const Context *m_context;
		ScenePlug::ScenePath m_scenePath;

};

//////////////////////////////////////////////////////////////////////////
// InteractiveRender
//////////////////////////////////////////////////////////////////////////

size_t InteractiveRender::g_firstPlugIndex = 0;

IE_CORE_DEFINERUNTIMETYPED( InteractiveRender );

InteractiveRender::InteractiveRender( const std::string &name )
	:	InteractiveRender( /* rendererType = */ InternedString(), name )
{
}

InteractiveRender::InteractiveRender( const IECore::InternedString &rendererType, const std::string &name )
	:	Node( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in" ) );
	addChild( new StringPlug( rendererType.string().empty() ? "renderer" : "__renderer", Plug::In, rendererType.string() ) );
	addChild( new IntPlug( "state", Plug::In, Stopped, Stopped, Paused, Plug::Default & ~Plug::Serialisable ) );
	addChild( new ScenePlug( "out", Plug::Out, Plug::Default & ~Plug::Serialisable ) );
	addChild( new ScenePlug( "__adaptedIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	SceneProcessorPtr adaptors = RendererAlgo::createAdaptors();
	setChild( "__adaptors", adaptors );
	adaptors->inPlug()->setInput( inPlug() );
	adaptedInPlug()->setInput( adaptors->outPlug() );

	outPlug()->setInput( inPlug() );

	plugDirtiedSignal().connect( boost::bind( &InteractiveRender::plugDirtied, this, ::_1 ) );

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

ScenePlug *InteractiveRender::adaptedInPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 4 );
}

const ScenePlug *InteractiveRender::adaptedInPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 4 );
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
	if( m_context == context )
	{
		return;
	}

	m_context = context;
	m_dirtyComponents = SceneGraph::AllComponents;
	update();
}

void InteractiveRender::plugDirtied( const Gaffer::Plug *plug )
{

	if( plug == adaptedInPlug()->boundPlug() )
	{
		m_dirtyComponents |= SceneGraph::BoundComponent;
	}
	else if( plug == adaptedInPlug()->transformPlug() )
	{
		m_dirtyComponents |= SceneGraph::TransformComponent;
	}
	else if( plug == adaptedInPlug()->attributesPlug() )
	{
		m_dirtyComponents |= SceneGraph::AttributesComponent;
	}
	else if( plug == adaptedInPlug()->objectPlug() )
	{
		m_dirtyComponents |= SceneGraph::ObjectComponent;
	}
	else if( plug == adaptedInPlug()->childNamesPlug() )
	{
		m_dirtyComponents |= SceneGraph::ChildNamesComponent;
	}
	else if( plug == adaptedInPlug()->globalsPlug() )
	{
		m_dirtyComponents |= SceneGraph::GlobalsComponent;
	}
	else if( plug == adaptedInPlug()->setPlug() )
	{
		m_dirtyComponents |= SceneGraph::SetsComponent;
	}
	else if( plug == rendererPlug() )
	{
		stop();
		m_dirtyComponents = SceneGraph::AllComponents;
	}

	if( plug == adaptedInPlug() ||
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

void InteractiveRender::contextChanged( const IECore::InternedString &name )
{
	if( boost::starts_with( name.string(), "ui:" ) )
	{
		return;
	}
	m_dirtyComponents = SceneGraph::AllComponents;
	update();
}

void InteractiveRender::update()
{
	const std::string rendererName = rendererPlug()->getValue();

	updateEffectiveContext();
	ContextPtr context = new Context( *m_effectiveContext );
	context->set( g_rendererContextName, rendererName );
	Context::Scope scopedContext( context.get() );

	const State requiredState = (State)statePlug()->getValue();

	// Stop the current render if we've been asked to, or if
	// there is no real input scene.

	if( requiredState == Stopped || !runTimeCast<SceneNode>( inPlug()->source()->node() ) )
	{
		stop();
		return;
	}

	// If we've got this far, we know we want to be running or paused.
	// Start a render if we don't have one.

	if( !m_renderer )
	{
		m_renderer = IECoreScenePreview::Renderer::create(
			rendererName,
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

	if( m_dirtyComponents & SceneGraph::GlobalsComponent )
	{
		ConstCompoundObjectPtr globals = adaptedInPlug()->globalsPlug()->getValue();
		Preview::RendererAlgo::outputOptions( globals.get(), m_globals.get(), m_renderer.get() );
		Preview::RendererAlgo::outputOutputs( globals.get(), m_globals.get(), m_renderer.get() );
		m_globals = globals;
	}

	if( m_dirtyComponents & SceneGraph::SetsComponent )
	{
		if( m_renderSets.update( adaptedInPlug() ) & Preview::RendererAlgo::RenderSets::RenderSetsChanged )
		{
			m_dirtyComponents |= SceneGraph::RenderSetsComponent;
		}
	}

	for( int i = SceneGraph::FirstType; i <= SceneGraph::LastType; ++i )
	{
		SceneGraph *sceneGraph = m_sceneGraphs[i].get();
		if( i == SceneGraph::CameraType && ( m_dirtyComponents & SceneGraph::GlobalsComponent ) )
		{
			// Because the globals are applied to camera objects, we must update the object whenever
			// the globals have changed, so we clear the scene graph and start again. We don't expect
			// this to be a big overhead because typically there aren't many cameras in a scene. If it
			// does cause a problem, we could examine the exact changes to the globals and avoid clearing
			// if we know they won't affect the camera.
			sceneGraph->clear();
		}
		SceneGraphUpdateTask *task = new( tbb::task::allocate_root() ) SceneGraphUpdateTask( this, sceneGraph, (SceneGraph::Type)i, m_dirtyComponents, SceneGraph::NoComponent, context.get(), ScenePlug::ScenePath() );
		tbb::task::spawn_root_and_wait( *task );
	}

	if( m_dirtyComponents & SceneGraph::GlobalsComponent )
	{
		updateDefaultCamera();
	}

	m_dirtyComponents = SceneGraph::NoComponent;
	m_state = requiredState;

	m_renderer->render();
}

void InteractiveRender::updateEffectiveContext()
{
	if( m_context )
	{
		if( m_effectiveContext == m_context )
		{
			return;
		}
		m_effectiveContext = m_context;
	}
	else if( ScriptNode *n = ancestor<ScriptNode>() )
	{
		if( m_effectiveContext == n->context() )
		{
			return;
		}
		m_effectiveContext = n->context();
	}
	else
	{
		m_effectiveContext = new Context();
	}

	m_contextChangedConnection = m_effectiveContext->changedSignal().connect(
		boost::bind( &InteractiveRender::contextChanged, this, ::_2 )
	);
}

void InteractiveRender::updateDefaultCamera()
{
	const StringData *cameraOption = m_globals->member<StringData>( g_cameraGlobalName );
	m_defaultCamera = nullptr;
	if( cameraOption && !cameraOption->readable().empty() )
	{
		return;
	}

	CameraPtr defaultCamera = SceneAlgo::camera( adaptedInPlug(), m_globals.get() );
	StringDataPtr name = new StringData( "gaffer:defaultCamera" );
	IECoreScenePreview::Renderer::AttributesInterfacePtr defaultAttributes = m_renderer->attributes( adaptedInPlug()->attributesPlug()->defaultValue() );
	m_defaultCamera = m_renderer->camera( name->readable(), defaultCamera.get(), defaultAttributes.get() );
	m_renderer->option( "camera", name.get() );
}

void InteractiveRender::stop()
{
	if( m_renderer )
	{
		m_renderer->pause();
	}

	m_sceneGraphs.clear();
	for( int i = SceneGraph::FirstType; i <= SceneGraph::LastType; ++i )
	{
		m_sceneGraphs.push_back( unique_ptr<SceneGraph>( new SceneGraph ) );
	}
	m_defaultCamera = nullptr;
	m_renderer = nullptr;

	m_globals = adaptedInPlug()->globalsPlug()->defaultValue();
	m_renderSets.clear();

	m_dirtyComponents = SceneGraph::AllComponents;
	m_state = Stopped;
}
