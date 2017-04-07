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

#include "tbb/task.h"
#include "tbb/task_scheduler_init.h"
#include "tbb/tbb_thread.h"

#include "IECore/WorldBlock.h"
#include "IECore/EditBlock.h"
#include "IECore/MessageHandler.h"
#include "IECore/SceneInterface.h"
#include "IECore/VisibleRenderable.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"

#include "GafferScene/InteractiveRender.h"
#include "GafferScene/RendererAlgo.h"
#include "GafferScene/PathMatcherData.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( InteractiveRender );

//////////////////////////////////////////////////////////////////////////
// SceneGraph implementation
//
// This is a node in a scene hierarchy, which gets built when the
// interactive render starts up. Each node stores the attribute hash of
// the input scene at its corresponding location in the hierarchy, so
// when the incoming scene updates, we are able to determine the locations
// at which the attributes have changed since the last update, reevaluate
// those attributes and send updates to the renderer.
//
// \todo: This is very similar to the SceneGraph mechanism in
// GafferSceneUI::SceneGadget. At some point it would be good to refactor
// this and use the same class for both of them. See the comments in
// src/GafferSceneUI/SceneGadget.cpp for details.
//
//////////////////////////////////////////////////////////////////////////

class InteractiveRender::SceneGraph
{

	public :

		SceneGraph() : m_parent( NULL ), m_locationPresent( true )
		{
		}

		~SceneGraph()
		{
			for( std::vector<SceneGraph *>::const_iterator it = m_children.begin(), eIt = m_children.end(); it != eIt; ++it )
			{
				delete *it;
			}
		}

		void path( ScenePlug::ScenePath &p )
		{
			if( !m_parent )
			{
				return;
			}
			m_parent->path( p );
			p.push_back( m_name );
		}

	private :

		friend class SceneGraphBuildTask;
		friend class ChildNamesUpdateTask;

		friend class SceneGraphIteratorFilter;
		friend class SceneGraphEvaluatorFilter;
		friend class SceneGraphOutputFilter;

		// scene structure data:
		IECore::InternedString m_name;
		SceneGraph *m_parent;
		std::vector<InteractiveRender::SceneGraph *> m_children;

		// hashes as of the most recent evaluation:
		IECore::MurmurHash m_attributesHash;
		IECore::MurmurHash m_childNamesHash;

		// actual scene data:
		IECore::ConstCompoundObjectPtr m_attributes;
		IECore::ConstObjectPtr m_object;
		Imath::M44f m_transform;

		// flag indicating if this location is currently present - (used
		// when the child names change)
		bool m_locationPresent;
};

size_t InteractiveRender::g_firstPlugIndex = 0;

InteractiveRender::InteractiveRender( const std::string &name )
	:	Node( name ), m_lightsDirty( true ), m_attributesDirty( true ), m_camerasDirty( true ), m_coordinateSystemsDirty( true )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in" ) );
	addChild( new ScenePlug( "out", Plug::Out, Plug::Default & ~Plug::Serialisable ) );
	outPlug()->setInput( inPlug() );
	addChild( new IntPlug( "state", Plug::In, Stopped, Stopped, Paused, Plug::Default & ~Plug::Serialisable ) );
	addChild( new BoolPlug( "updateLights", Plug::In, true ) );
	addChild( new BoolPlug( "updateAttributes", Plug::In, true ) );
	addChild( new BoolPlug( "updateCameras", Plug::In, true ) );
	addChild( new BoolPlug( "updateCoordinateSystems", Plug::In, true ) );

	plugDirtiedSignal().connect( boost::bind( &InteractiveRender::plugDirtied, this, ::_1 ) );
	parentChangedSignal().connect( boost::bind( &InteractiveRender::parentChanged, this, ::_1, ::_2 ) );

	setContext( new Context() );
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

ScenePlug *InteractiveRender::outPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 1 );
}

const ScenePlug *InteractiveRender::outPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *InteractiveRender::statePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *InteractiveRender::statePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *InteractiveRender::updateLightsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *InteractiveRender::updateLightsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

Gaffer::BoolPlug *InteractiveRender::updateAttributesPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::BoolPlug *InteractiveRender::updateAttributesPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

Gaffer::BoolPlug *InteractiveRender::updateCamerasPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::BoolPlug *InteractiveRender::updateCamerasPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 5 );
}

Gaffer::BoolPlug *InteractiveRender::updateCoordinateSystemsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::BoolPlug *InteractiveRender::updateCoordinateSystemsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

//////////////////////////////////////////////////////////////////////////
// ChildNamesUpdateTask implementation
//
// We use this tbb::task to traverse the input scene and check if the child
// names are still valid at each location. If not, we flag the location as
// not present so it doesn't get traversed during an update
//
//////////////////////////////////////////////////////////////////////////

class InteractiveRender::ChildNamesUpdateTask : public tbb::task
{

	public :

		ChildNamesUpdateTask( const ScenePlug *scene, const Context *context, SceneGraph *sceneGraph, const ScenePlug::ScenePath &scenePath )
			:	m_scene( scene ),
				m_context( context ),
				m_sceneGraph( sceneGraph ),
				m_scenePath( scenePath )
		{
		}

		~ChildNamesUpdateTask()
		{
		}

		virtual task *execute()
		{
			ScenePlug::PathScope pathScope( m_context, m_scenePath );

			IECore::MurmurHash childNamesHash = m_scene->childNamesPlug()->hash();

			if( childNamesHash != m_sceneGraph->m_childNamesHash )
			{
				// child names have changed - we need to update m_locationPresent on the children:
				m_sceneGraph->m_childNamesHash = childNamesHash;

				// read updated child names:
				IECore::ConstInternedStringVectorDataPtr childNamesData = m_scene->childNamesPlug()->getValue( &m_sceneGraph->m_childNamesHash );
				std::vector<IECore::InternedString> childNames = childNamesData->readable();

				// m_sceneGraph->m_children should be sorted by name. Sort this list too so we can
				// compare the two easily:
				std::sort( childNames.begin(), childNames.end() );

				std::vector<InternedString>::iterator childNamesBegin = childNames.begin();
				for( std::vector<SceneGraph *>::const_iterator it = m_sceneGraph->m_children.begin(), eIt = m_sceneGraph->m_children.end(); it != eIt; ++it )
				{
					// try and find the current child name in the list of child names:
					std::vector<InternedString>::iterator nameIt = std::find( childNamesBegin, childNames.end(), (*it)->m_name );
					if( nameIt != childNames.end() )
					{
						// ok, it's there - mark this child as still present
						(*it)->m_locationPresent = true;

						// As both the name lists are sorted, no further child names will be found beyond nameIt
						// in the list, nor will they be found at nameIt as there shouldn't be any duplicates.
						// This means we can move the start of the child names list one position past nameIt
						// to save a bit of time:
						/// \todo Note that if all the children have changed names, we never end up in here, and
						/// we will end up with quadratic behaviour calling find (a linear search N times).
						childNamesBegin = nameIt;
						++childNamesBegin;
					}
					else
					{
						(*it)->m_locationPresent = false;
					}
				}
			}

			// count children currently present in the scene:
			size_t numPresentChildren = 0;
			for( std::vector<SceneGraph *>::const_iterator it = m_sceneGraph->m_children.begin(), eIt = m_sceneGraph->m_children.end(); it != eIt; ++it )
			{
				numPresentChildren += (*it)->m_locationPresent;
			}

			// spawn child tasks:
			set_ref_count( 1 + numPresentChildren );
			ScenePlug::ScenePath childPath = m_scenePath;
			childPath.push_back( IECore::InternedString() ); // space for the child name
			for( std::vector<SceneGraph *>::const_iterator it = m_sceneGraph->m_children.begin(), eIt = m_sceneGraph->m_children.end(); it != eIt; ++it )
			{
				if( (*it)->m_locationPresent )
				{
					childPath.back() = (*it)->m_name;
					ChildNamesUpdateTask *t = new( allocate_child() ) ChildNamesUpdateTask(
						m_scene,
						m_context,
						(*it),
						childPath
					);

					spawn( *t );
				}
			}
			wait_for_all();

			return NULL;
		}

	private :

		const ScenePlug *m_scene;
		const Context *m_context;
		SceneGraph *m_sceneGraph;
		ScenePlug::ScenePath m_scenePath;
};


void InteractiveRender::plugDirtied( const Gaffer::Plug *plug )
{

	if(
		plug == inPlug()->transformPlug() ||
		plug == inPlug()->globalsPlug()
	)
	{
		// just store the fact that something needs
		// updating. we'll do the actual update when
		// the dirty signal is emitted for the parent plug.
		m_lightsDirty = true;
		m_camerasDirty = true;
		m_coordinateSystemsDirty = true;
	}
	else if( plug == inPlug()->objectPlug() )
	{
		// as above.
		m_lightsDirty = true;
		m_camerasDirty = true;
		m_coordinateSystemsDirty = true;
	}
	else if( plug == inPlug()->attributesPlug() )
	{
		// as above.
		m_attributesDirty = true;
		m_lightsDirty = true;
	}
	else if( plug == inPlug()->childNamesPlug() )
	{
		if( m_sceneGraph.get() )
		{
			// child names may have changed: we need to run through the scene graph data structure
			// checking for locations that are no longer present, and flag them as absent if this
			// is the case:
			/// \todo doing this directly here is out of keeping with the basic structure
			/// of this node. Everything else just figures out what is dirty here, and then
			/// waits until update() to do the work. Since we'll most likely delay calls to update()
			/// further in the future, we should fix this.
			ChildNamesUpdateTask *task = new( tbb::task::allocate_root() ) ChildNamesUpdateTask( inPlug(), m_context.get(), m_sceneGraph.get(), ScenePlug::ScenePath() );
			try
			{
				tbb::task::spawn_root_and_wait( *task );
			}
			catch( const std::exception& e )
			{
				IECore::msg( IECore::Msg::Error, "InteractiveRender::update", e.what() );
			}
		}
	}
	else if(
		plug == inPlug() ||
		plug == updateLightsPlug() ||
		plug == updateAttributesPlug() ||
		plug == updateCamerasPlug() ||
		plug == updateCoordinateSystemsPlug() ||
		plug == statePlug()
	)
	{
		try
		{
			update();
		}
		catch( const std::exception &e )
		{
			// Since we're inside an emission of plugDirtiedSignal(),
			// it's of no use to anyone to go throwing an exception.
			// instead we'll just report it as a message.
			/// \todo When we have Node::errorSignal(), we should
			/// emit that, and the UI will be able to show the error
			/// more appropriately.
			IECore::msg( IECore::Msg::Error, "InteractiveRender::update", e.what() );
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



//////////////////////////////////////////////////////////////////////////
// BuildTask implementation
//
// We use this tbb::task to traverse the input scene and build the
// hierarchy for the first time. Recursion is terminated for locations
// at which scene:visible is set to false, so this task also computes
// and stores the attributes.
//
//////////////////////////////////////////////////////////////////////////

class InteractiveRender::SceneGraphBuildTask : public tbb::task
{

	public :

		SceneGraphBuildTask( const ScenePlug *scene, const Context *context, SceneGraph *sceneGraph, const ScenePlug::ScenePath &scenePath )
			:	m_scene( scene ),
				m_context( context ),
				m_sceneGraph( sceneGraph ),
				m_scenePath( scenePath )
		{
		}

		~SceneGraphBuildTask()
		{
		}

		virtual task *execute()
		{
			ScenePlug::PathScope pathScope( m_context, m_scenePath );

			// we need the attributes so we can terminate recursion at invisible locations, so
			// we might as well store them in the scene graph, along with the hash:

			m_sceneGraph->m_attributesHash = m_scene->attributesPlug()->hash();

			// use the precomputed hash in getValue() to save a bit of time:

			m_sceneGraph->m_attributes = m_scene->attributesPlug()->getValue( &m_sceneGraph->m_attributesHash );
			const BoolData *visibilityData = m_sceneGraph->m_attributes->member<BoolData>( SceneInterface::visibilityName );
			if( visibilityData && !visibilityData->readable() )
			{
				// terminate recursion for invisible locations
				return NULL;
			}

			// store the hash of the child names so we know when they change:
			m_sceneGraph->m_childNamesHash = m_scene->childNamesPlug()->hash();

			// compute child names:
			IECore::ConstInternedStringVectorDataPtr childNamesData = m_scene->childNamesPlug()->getValue( &m_sceneGraph->m_childNamesHash );

			std::vector<IECore::InternedString> childNames = childNamesData->readable();
			if( childNames.empty() )
			{
				// nothing more to do
				return NULL;
			}

			// sort the child names so we can compare child name lists easily in ChildNamesUpdateTask:
			std::sort( childNames.begin(), childNames.end() );

			// add children for this location:
			std::vector<InteractiveRender::SceneGraph *> children;
			for( std::vector<IECore::InternedString>::const_iterator it = childNames.begin(), eIt = childNames.end(); it != eIt; ++it )
			{
				SceneGraph *child = new SceneGraph();
				child->m_name = *it;
				child->m_parent = m_sceneGraph;
				children.push_back( child );
			}

			// spawn child tasks:
			set_ref_count( 1 + children.size() );
			ScenePlug::ScenePath childPath = m_scenePath;
			childPath.push_back( IECore::InternedString() ); // space for the child name
			for( std::vector<SceneGraph *>::const_iterator it = children.begin(), eIt = children.end(); it != eIt; ++it )
			{
				childPath.back() = (*it)->m_name;
				SceneGraphBuildTask *t = new( allocate_child() ) SceneGraphBuildTask(
					m_scene,
					m_context,
					(*it),
					childPath
				);

				spawn( *t );
			}

			wait_for_all();

			// add visible children to m_sceneGraph->m_children:
			for( std::vector<SceneGraph *>::const_iterator it = children.begin(), eIt = children.end(); it != eIt; ++it )
			{
				const BoolData *visibilityData = (*it)->m_attributes->member<BoolData>( SceneInterface::visibilityName );
				if( visibilityData && !visibilityData->readable() )
				{
					continue;
				}
				m_sceneGraph->m_children.push_back( *it );
			}

			return NULL;
		}

	private :

		const ScenePlug *m_scene;
		const Context *m_context;
		SceneGraph *m_sceneGraph;
		ScenePlug::ScenePath m_scenePath;
};


//////////////////////////////////////////////////////////////////////////
// SceneGraphIteratorFilter implementation
//
// Does a serial, depth first traversal of a SceneGraph hierarchy based at
// "start", and spits out SceneGraph* tokens:
//
//////////////////////////////////////////////////////////////////////////

class InteractiveRender::SceneGraphIteratorFilter : public tbb::filter
{
	public:
		SceneGraphIteratorFilter( InteractiveRender::SceneGraph *start ) :
			tbb::filter( tbb::filter::serial_in_order ), m_current( start )
		{
			m_childIndices.push_back( 0 );
		}

		virtual void *operator()( void *item )
		{
			if( m_childIndices.empty() )
			{
				// we've finished the iteration
				return NULL;
			}
			InteractiveRender::SceneGraph *s = m_current;
			next();
			return s;
		}

	private:

		void next()
		{
			// go down one level in the hierarchy if we can:
			for( size_t i=0; i < m_current->m_children.size(); ++i )
			{
				// skip out locations that aren't present
				if( m_current->m_children[i]->m_locationPresent )
				{
					m_current = m_current->m_children[i];
					m_childIndices.push_back(i);
					return;
				}
			}

			while( m_childIndices.size() )
			{

				// increment child index:
				++m_childIndices.back();

				// find parent's child count - for the root we define this as 1:
				size_t parentNumChildren = m_current->m_parent ? m_current->m_parent->m_children.size() : 1;

				if( m_childIndices.back() == parentNumChildren )
				{
					// we've got to the end of the child list, jump up one level:
					m_childIndices.pop_back();
					m_current = m_current->m_parent;
					continue;
				}
				else if( m_current->m_parent->m_children[ m_childIndices.back() ]->m_locationPresent )
				{
					// move to next child of the parent, if it is still present in the scene:
					m_current = m_current->m_parent->m_children[ m_childIndices.back() ];
					return;
				}
			}
		}

		SceneGraph *m_current;
		std::vector<size_t> m_childIndices;
};


//////////////////////////////////////////////////////////////////////////
// SceneGraphEvaluatorFilter implementation
//
// This parallel filter computes the data living at the scene graph
// location it receives. If the "onlyChanged" flag is set to true, it
// only recomputes data when the hashes change, otherwise it computes
// all non null scene data.
//
//////////////////////////////////////////////////////////////////////////

class InteractiveRender::SceneGraphEvaluatorFilter : public tbb::filter
{
	public:
		SceneGraphEvaluatorFilter( const ScenePlug *scene, const Context *context, bool update ) :
			tbb::filter( tbb::filter::parallel ), m_scene( scene ), m_context( context ), m_update( update )
		{
		}

		virtual void *operator()( void *item )
		{
			SceneGraph *s = (SceneGraph*)item;
			ScenePlug::ScenePath path;
			s->path( path );

			try
			{
				ScenePlug::PathScope pathScope( m_context, path );

				if( m_update )
				{
					// we're re-traversing this location, so lets only recompute attributes where
					// their hashes change:

					IECore::MurmurHash attributesHash = m_scene->attributesPlug()->hash();
					if( attributesHash != s->m_attributesHash )
					{
						s->m_attributes = m_scene->attributesPlug()->getValue( &attributesHash );
						s->m_attributesHash = attributesHash;
					}
				}
				else
				{
					// First traversal: attributes and attribute hash should have been computed
					// by the SceneGraphBuildTasks, so we only need to compute the object/transform:

					s->m_object = m_scene->objectPlug()->getValue();
					s->m_transform = m_scene->transformPlug()->getValue();

				}
			}
			catch( const std::exception &e )
			{
				std::string name;
				ScenePlug::pathToString( path, name );

				IECore::msg( IECore::Msg::Error, "InteractiveRender::update", name + ": " + e.what() );
			}

			return s;
		}

	private:

		const ScenePlug *m_scene;
		const Context *m_context;
		const bool m_update;
};

//////////////////////////////////////////////////////////////////////////
// SceneGraphOutputFilter implementation
//
// This serial thread bound filter outputs scene data to a renderer on
// the main thread, then discards that data to save memory. If the
// editMode flag is set to true, the filter outputs edits, otherwise
// it renders the data directly.
//
//////////////////////////////////////////////////////////////////////////

class InteractiveRender::SceneGraphOutputFilter : public tbb::thread_bound_filter
{
	public:

		SceneGraphOutputFilter( Renderer *renderer, bool editMode ) :
			tbb::thread_bound_filter( tbb::filter::serial_in_order ),
			m_renderer( renderer ),
			m_attrBlockCounter( 0 ),
			m_editMode( editMode )
		{
		}

		virtual ~SceneGraphOutputFilter()
		{
			// close pending attribute blocks:
			while( m_attrBlockCounter )
			{
				--m_attrBlockCounter;
				m_renderer->attributeEnd();
			}
		}

		virtual void *operator()( void *item )
		{
			SceneGraph *s = (SceneGraph*)item;
			ScenePlug::ScenePath path;
			s->path( path );

			std::string name;
			ScenePlug::pathToString( path, name );

			try
			{
				if( !m_editMode )
				{
					// outputting scene for the first time - do some attribute block tracking:
					if( path.size() )
					{
						for( int i = m_previousPath.size(); i >= (int)path.size(); --i )
						{
							--m_attrBlockCounter;
							m_renderer->attributeEnd();
						}
					}

					m_previousPath = path;

					++m_attrBlockCounter;
					m_renderer->attributeBegin();

					// set the name for this location:
					m_renderer->setAttribute( "name", new StringData( name ) );

				}

				// transform:
				if( !m_editMode )
				{
					m_renderer->concatTransform( s->m_transform );
				}

				// attributes:
				if( s->m_attributes )
				{
					if( m_editMode )
					{
						CompoundDataMap parameters;
						parameters["exactscopename"] = new StringData( name );
						m_renderer->editBegin( "attribute", parameters );
					}

					RendererAlgo::outputAttributes( s->m_attributes.get(), m_renderer );
					s->m_attributes = NULL;

					if( m_editMode )
					{
						m_renderer->editEnd();
					}

				}

				// object:
				if( s->m_object && !m_editMode )
				{
					if( const VisibleRenderable *renderable = runTimeCast< const VisibleRenderable >( s->m_object.get() ) )
					{
						renderable->render( m_renderer );
					}
					s->m_object = 0;
				}
			}
			catch( const std::exception &e )
			{
				IECore::msg( IECore::Msg::Error, "InteractiveRender::update", name + ": " + e.what() );
			}

			return NULL;
		}

	private:

		Renderer *m_renderer;
		ScenePlug::ScenePath m_previousPath;
		int m_attrBlockCounter;
		bool m_editMode;
};

void InteractiveRender::runPipeline(tbb::pipeline *p)
{
	// \todo: tune this number to find a balance between memory and speed once
	// we have a load of production data:

	p->run( 2 * tbb::task_scheduler_init::default_num_threads() );
}

void InteractiveRender::outputScene( bool update )
{

	SceneGraphIteratorFilter iterator( m_sceneGraph.get() );

	SceneGraphEvaluatorFilter evaluator(
		inPlug(),
		m_context.get(),
		update // only recompute locations whose hashes have changed if true:
	);

	SceneGraphOutputFilter output(
		m_renderer.get(),
		update // edit mode if true
	);

	tbb::pipeline p;
	p.add_filter( iterator );
	p.add_filter( evaluator );
	p.add_filter( output );

	 // Another thread initiates execution of the pipeline
	tbb::tbb_thread pipelineThread( runPipeline, &p );

	// Process the SceneGraphOutputFilter with the current thread:
	while( output.process_item() != tbb::thread_bound_filter::end_of_stream )
	{
		continue;
	}
	pipelineThread.join();

}

void InteractiveRender::update()
{
	Context::Scope scopedContext( m_context.get() );

	const State requiredState = (State)statePlug()->getValue();
	ConstScenePlugPtr requiredScene = inPlug()->getInput<ScenePlug>();

	// Stop the current render if it's not what we want,
	// and early-out if we don't want another one.

	if( !requiredScene || requiredScene != m_scene || requiredState == Stopped )
	{
		stop();
		if( !requiredScene || requiredState == Stopped )
		{
			return;
		}
	}

	// no point doing an update if the scene's empty
	if( inPlug()->childNames( ScenePlug::ScenePath() )->readable().empty() )
	{
		stop();
		return;
	}

	// If we've got this far, we know we want to be running or paused.
	// Start a render if we don't have one.

	if( !m_renderer )
	{
		m_renderer = createRenderer();
		m_renderer->setOption( "editable", new BoolData( true ) );

		ConstCompoundObjectPtr globals = inPlug()->globalsPlug()->getValue();
		RendererAlgo::outputOptions( globals.get(), m_renderer.get() );
		RendererAlgo::outputOutputs( globals.get(), m_renderer.get() );
		RendererAlgo::outputCameras( inPlug(), globals.get(), m_renderer.get() );
		RendererAlgo::outputClippingPlanes( inPlug(), globals.get(), m_renderer.get() );
		{
			WorldBlock world( m_renderer );

			RendererAlgo::outputGlobalAttributes( globals.get(), m_renderer.get() );
			RendererAlgo::outputCoordinateSystems( inPlug(), globals.get(), m_renderer.get() );
			outputLightsInternal( globals.get(), /* editing = */ false );

			// build the scene graph structure in parallel:
			m_sceneGraph.reset( new SceneGraph );
			SceneGraphBuildTask *task = new( tbb::task::allocate_root() ) SceneGraphBuildTask( inPlug(), m_context.get(), m_sceneGraph.get(), ScenePlug::ScenePath() );
			tbb::task::spawn_root_and_wait( *task );

			// output the scene for the first time:
			outputScene( false );
		}

		m_scene = requiredScene;
		m_state = Running;
		m_lightsDirty = m_attributesDirty = m_camerasDirty = false;
	}

	// Make sure the paused/running state is as we want.

	if( requiredState != m_state )
	{
		if( requiredState == Paused )
		{
			m_renderer->editBegin( "suspendrendering", CompoundDataMap() );
		}
		else
		{
			m_renderer->editEnd();
		}
		m_state = requiredState;
	}

	// If we're not paused, then send any edits we need.

	if( m_state == Running )
	{
		EditBlock edit( m_renderer.get(), "suspendrendering", CompoundDataMap() );
		updateLights();
		updateAttributes();
		updateCameras();
		updateCoordinateSystems();
	}
}

void InteractiveRender::updateLights()
{
	if( !m_lightsDirty || !updateLightsPlug()->getValue() )
	{
		return;
	}
	IECore::ConstCompoundObjectPtr globals = inPlug()->globalsPlug()->getValue();
	outputLightsInternal( globals.get(), /* editing = */ true );
	m_lightsDirty = false;
}

void InteractiveRender::outputLightsInternal( const IECore::CompoundObject *globals, bool editing )
{
	// Get the paths to all the lights
	ConstPathMatcherDataPtr lightSet = inPlug()->set( "__lights" );

	std::vector<std::string> lightPaths;
	lightSet->readable().paths( lightPaths );

	// Create or update lights in the renderer as necessary

	for( vector<string>::const_iterator it = lightPaths.begin(), eIt = lightPaths.end(); it != eIt; ++it )
	{
		ScenePlug::ScenePath path;
		ScenePlug::stringToPath( *it, path );

		if( !editing )
		{
			// defining the scene for the first time
			if( RendererAlgo::outputLight( inPlug(), path, m_renderer.get() ) )
			{
				m_lightHandles.insert( *it );
			}
		}
		else
		{
			if( m_lightHandles.find( *it ) != m_lightHandles.end() )
			{
				// we've already output this light - update it
				bool visible = false;
				{
					EditBlock edit( m_renderer.get(), "light", CompoundDataMap() );
					visible = RendererAlgo::outputLight( inPlug(), path, m_renderer.get() );
				}
				// we may have turned it off before, and need to turn
				// it back on, or it may have been hidden and we need
				// to turn it off.
				{
					EditBlock edit( m_renderer.get(), "attribute", CompoundDataMap() );
					m_renderer->illuminate( *it, visible );
				}
			}
			else
			{
				// we've not seen this light before - create a new one
				EditBlock edit( m_renderer.get(), "attribute", CompoundDataMap() );
				if( RendererAlgo::outputLight( inPlug(), path, m_renderer.get() ) )
				{
					m_lightHandles.insert( *it );
				}
			}
		}
	}

	// Turn off any lights we don't want any more

	for( LightHandles::const_iterator it = m_lightHandles.begin(), eIt = m_lightHandles.end(); it != eIt; ++it )
	{
		if( !lightSet || !(lightSet->readable().match( *it ) & Filter::ExactMatch) )
		{
			EditBlock edit( m_renderer.get(), "attribute", CompoundDataMap() );
			m_renderer->illuminate( *it, false );
		}
	}
}

void InteractiveRender::updateAttributes()
{
	if( !m_attributesDirty || !updateAttributesPlug()->getValue() )
	{
		return;
	}

	// output the scene, updating locations whose hashes have changed since last time:
	outputScene( true );

	m_attributesDirty = false;
}

void InteractiveRender::updateCameras()
{
	if( !m_camerasDirty || !updateCamerasPlug()->getValue() )
	{
		return;
	}

	IECore::ConstCompoundObjectPtr globals = inPlug()->globalsPlug()->getValue();
	{
		EditBlock edit( m_renderer.get(), "option", CompoundDataMap() );
		RendererAlgo::outputCameras( inPlug(), globals.get(), m_renderer.get() );
	}
	m_camerasDirty = false;
}

void InteractiveRender::updateCoordinateSystems()
{
	if( !m_coordinateSystemsDirty || !updateCoordinateSystemsPlug()->getValue() )
	{
		return;
	}

	IECore::ConstCompoundObjectPtr globals = inPlug()->globalsPlug()->getValue();
	{
		EditBlock edit( m_renderer.get(), "attribute", CompoundDataMap() );
		RendererAlgo::outputCoordinateSystems( inPlug(), globals.get(), m_renderer.get() );
	}
	m_coordinateSystemsDirty = false;
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
	m_context = context;
}

void InteractiveRender::stop()
{
	if( m_renderer && m_state == Paused )
	{
		// Unpause if necessary. Prior to 3delight 11.0.142,
		// deleting the renderer (calling RiEnd()) while
		// paused led to deadlock.
		m_renderer->editEnd();
	}

	m_renderer = NULL;
	m_scene = NULL;
	m_state = Stopped;
	m_lightHandles.clear();
	m_attributesDirty = m_lightsDirty = m_camerasDirty = true;
	m_sceneGraph.reset( (SceneGraph*)NULL );
}
