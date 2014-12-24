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

#include "IECore/WorldBlock.h"
#include "IECore/EditBlock.h"
#include "IECore/MessageHandler.h"
#include "IECore/SceneInterface.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"

#include "GafferScene/InteractiveRender.h"
#include "GafferScene/RendererAlgo.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/SceneProcedural.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( InteractiveRender );

size_t InteractiveRender::g_firstPlugIndex = 0;


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

		SceneGraph()
		{
		}

		~SceneGraph()
		{
			for( std::vector<SceneGraph *>::const_iterator it = m_children.begin(), eIt = m_children.end(); it != eIt; ++it )
			{
				delete *it;
			}
		}

	private :

		friend class BuildTask;
		friend class UpdateTask;
		
		IECore::InternedString m_name;
		std::vector<SceneGraph *> m_children;
		IECore::MurmurHash m_attributesHash;
};



//////////////////////////////////////////////////////////////////////////
// BuildTask implementation
//
// We use this tbb::task to traverse the input scene and build the
// hierarchy for the first time:
//
//////////////////////////////////////////////////////////////////////////

class InteractiveRender::BuildTask : public tbb::task
{

	public :

		BuildTask( const ScenePlug *scene, const Context* context, SceneGraph *sceneGraph, const ScenePlug::ScenePath &scenePath )
			:	m_scene( scene ),
				m_context( context ),
				m_sceneGraph( sceneGraph ),
				m_scenePath( scenePath )
		{
		}
		
		~BuildTask()
		{
		}

		virtual task *execute()
		{
			ContextPtr context = new Context( *m_context, Context::Borrowed );
			context->set( ScenePlug::scenePathContextName, m_scenePath );
			Context::Scope scopedContext( context.get() );
			
			// find attribute hash for current location:
			m_sceneGraph->m_attributesHash = m_scene->attributesPlug()->hash();

			// compute child names:
			IECore::ConstInternedStringVectorDataPtr childNamesData = m_scene->childNamesPlug()->getValue();
			
			const std::vector<IECore::InternedString> &childNames = childNamesData->readable();
			if( childNames.empty() )
			{
				// nothing more to do
				return NULL;
			}
			
			// add children for this location:
			for( std::vector<IECore::InternedString>::const_iterator it = childNames.begin(), eIt = childNames.end(); it != eIt; ++it )
			{
				SceneGraph *child = new SceneGraph();
				child->m_name = *it;
				m_sceneGraph->m_children.push_back( child );
			}
			
			// spawn child tasks:
			set_ref_count( 1 + m_sceneGraph->m_children.size() );
			ScenePlug::ScenePath childPath = m_scenePath;
			childPath.push_back( IECore::InternedString() ); // space for the child name
			for( std::vector<SceneGraph *>::const_iterator it = m_sceneGraph->m_children.begin(), eIt = m_sceneGraph->m_children.end(); it != eIt; ++it )
			{
				childPath.back() = (*it)->m_name;
				BuildTask *t = new( allocate_child() ) BuildTask(
					m_scene,
					m_context,
					(*it),
					childPath
				);
				
				spawn( *t );
			}
			

			wait_for_all();

			return NULL;
		}

	private :

		const ScenePlug *m_scene;
		const Context* m_context;
		SceneGraph *m_sceneGraph;
		ScenePlug::ScenePath m_scenePath;
};


//////////////////////////////////////////////////////////////////////////
// UpdateTask implementation
//
// We use this tbb::task to traverse the input scene and identify the
// locations whose attributes have changed since the last update, by
// comparing attribute hashes. Attributes are evaluated on locations which
// have changed, and are added to the attributeEditsResult map.
//
//////////////////////////////////////////////////////////////////////////

class InteractiveRender::UpdateTask : public tbb::task
{

	public :

		typedef std::map<ScenePlug::ScenePath,IECore::ConstCompoundObjectPtr> AttributeEditMap;
		
		UpdateTask( const ScenePlug *scene, const Context* context, SceneGraph *sceneGraph, const ScenePlug::ScenePath &scenePath, AttributeEditMap& attributeEditsResult )
			:	m_scene( scene ),
				m_context( context ),
				m_sceneGraph( sceneGraph ),
				m_scenePath( scenePath ),
				m_attributeEditsResult( attributeEditsResult )
		{
		}
		
		~UpdateTask()
		{
		}

		virtual task *execute()
		{
			ContextPtr context = new Context( *m_context, Context::Borrowed );
			context->set( ScenePlug::scenePathContextName, m_scenePath );
			Context::Scope scopedContext( context.get() );
			
			// find attribute hash for current location:
			IECore::MurmurHash attributesHash = m_scene->attributesPlug()->hash();
			if( attributesHash != m_sceneGraph->m_attributesHash )
			{
				// this location's attributes have changed since the last evaluation - 
				// lets reevaluate them and add them to the result:
				m_sceneGraph->m_attributesHash = attributesHash;
				m_attributeEditsResult[ m_scenePath ] = m_scene->attributesPlug()->getValue();
			}
			
			// recurse into children:
			if( m_sceneGraph->m_children.size() )
			{
				set_ref_count( 1 + m_sceneGraph->m_children.size() );

				// vector of AttributeEditMaps to collect edits from the children:
				std::vector<AttributeEditMap> childEdits( m_sceneGraph->m_children.size() );

				// launch tasks for the children:
				ScenePlug::ScenePath childPath = m_scenePath;
				childPath.push_back( IECore::InternedString() ); // space for the child name
				for( std::vector<SceneGraph *>::const_iterator it = m_sceneGraph->m_children.begin(), eIt = m_sceneGraph->m_children.end(); it != eIt; ++it )
				{
					childEdits.resize( childEdits.size() + 1 );
					childPath.back() = (*it)->m_name;
					UpdateTask *t = new( allocate_child() ) UpdateTask(
						m_scene,
						m_context,
						*it,
						childPath,
						childEdits[ it - m_sceneGraph->m_children.begin() ]
					);

					spawn( *t );
				}
				wait_for_all();

				// add the edits we collected from the child tasks to the
				// ones we collected for this task:
				for( size_t i=0; i < childEdits.size(); ++i )
				{
					for( AttributeEditMap::const_iterator it = childEdits[i].begin(); it != childEdits[i].end(); ++it )
					{
						m_attributeEditsResult[it->first] = it->second;
					}
				}
			}
			
			return NULL;
		}

	private :

		const ScenePlug *m_scene;
		const Context* m_context;
		SceneGraph *m_sceneGraph;
		ScenePlug::ScenePath m_scenePath;
		AttributeEditMap& m_attributeEditsResult;
};



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
	}
	else if( plug == inPlug()->attributesPlug() )
	{
		// as above.
		m_attributesDirty = true;
		m_lightsDirty = true;
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

void InteractiveRender::update()
{
	Context::Scope scopedContext( m_context.get() );

	const State requiredState = (State)statePlug()->getValue();
	ConstScenePlugPtr requiredScene = inPlug()->getInput<ScenePlug>();

	// Stop the current render if it's not what we want,
	// and early-out if we don't want another one.

	if( !requiredScene || requiredScene != m_scene || requiredState == Stopped )
	{
		// stop the current render
		m_renderer = NULL;
		m_scene = NULL;
		m_state = Stopped;
		m_lightHandles.clear();
		m_attributesDirty = m_lightsDirty = m_camerasDirty = true;
		if( !requiredScene || requiredState == Stopped )
		{
			return;
		}
	}

	// If we've got this far, we know we want to be running or paused.
	// Start a render if we don't have one.

	if( !m_renderer )
	{
		m_renderer = createRenderer();
		m_renderer->setOption( "editable", new BoolData( true ) );

		ConstCompoundObjectPtr globals = inPlug()->globalsPlug()->getValue();
		outputOptions( globals.get(), m_renderer.get() );
		outputOutputs( globals.get(), m_renderer.get() );
		outputCameras( inPlug(), globals.get(), m_renderer.get() );
		{
			WorldBlock world( m_renderer );

			outputGlobalAttributes( globals.get(), m_renderer.get() );
			outputCoordinateSystems( inPlug(), globals.get(), m_renderer.get() );
			outputLightsInternal( globals.get(), /* editing = */ false );

			SceneProceduralPtr proc = new SceneProcedural( inPlug(), Context::current() );
			m_renderer->procedural( proc );
		}

		m_scene = requiredScene;
		m_state = Running;
		m_lightsDirty = m_attributesDirty = m_camerasDirty = false;
		
		// now we need to clear the scene graph and build a new one. This will just replicate the structure of the
		// input scene, storing attribute hashes at each location:
		
		m_sceneGraph.reset( new SceneGraph );
		BuildTask *task = new( tbb::task::allocate_root() ) BuildTask( inPlug(), m_context.get(), m_sceneGraph.get(), ScenePlug::ScenePath() );
		tbb::task::spawn_root_and_wait( *task );
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
	const PathMatcherData *lightSet = NULL;
	if( const CompoundData *sets = globals->member<CompoundData>( "gaffer:sets" ) )
	{
		lightSet = sets->member<PathMatcherData>( "__lights" );
	}

	std::vector<std::string> lightPaths;
	if( lightSet )
	{
		lightSet->readable().paths( lightPaths );
	}

	// Create or update lights in the renderer as necessary

	for( vector<string>::const_iterator it = lightPaths.begin(), eIt = lightPaths.end(); it != eIt; ++it )
	{
		ScenePlug::ScenePath path;
		ScenePlug::stringToPath( *it, path );

		if( !editing )
		{
			// defining the scene for the first time
			if( outputLight( inPlug(), path, m_renderer.get() ) )
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
					visible = outputLight( inPlug(), path, m_renderer.get() );
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
				if( outputLight( inPlug(), path, m_renderer.get() ) )
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

	// do a multithreaded traversal and collect attribute edits since the last time we traversed the scene:
	UpdateTask::AttributeEditMap attributeEdits;
	UpdateTask *task = new( tbb::task::allocate_root() ) UpdateTask( inPlug(), m_context.get(), m_sceneGraph.get(), ScenePlug::ScenePath(), attributeEdits );
	tbb::task::spawn_root_and_wait( *task );
	
	// Now run through and make edits where we need to:
	UpdateTask::AttributeEditMap::const_iterator it = attributeEdits.begin();
	UpdateTask::AttributeEditMap::const_iterator end = attributeEdits.end();
	
	for( ;it != end; ++it )
	{
		const ScenePlug::ScenePath& path = it->first;
		ConstCompoundObjectPtr attributes = it->second;
		
		std::string name;
		ScenePlug::pathToString( path, name );
		CompoundDataMap parameters;
		parameters["exactscopename"] = new StringData( name );
		{
			EditBlock edit( m_renderer.get(), "attribute", parameters );
			for( CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; it++ )
			{
				if( const StateRenderable *s = runTimeCast<const StateRenderable>( it->second.get() ) )
				{
					s->render( m_renderer.get() );
				}
				else if( const ObjectVector *o = runTimeCast<const ObjectVector>( it->second.get() ) )
				{
					for( ObjectVector::MemberContainer::const_iterator it = o->members().begin(), eIt = o->members().end(); it != eIt; it++ )
					{
						const StateRenderable *s = runTimeCast<const StateRenderable>( it->get() );
						if( s )
						{
							s->render( m_renderer.get() );
						}
					}
				}
				else if( const Data *d = runTimeCast<const Data>( it->second.get() ) )
				{
					m_renderer->setAttribute( it->first, d );
				}
			}
		}
	}

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
		outputCameras( inPlug(), globals.get(), m_renderer.get() );
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
		outputCoordinateSystems( inPlug(), globals.get(), m_renderer.get() );
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
