//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/RenderController.h"

#include "GafferScene/Private/IECoreScenePreview/Placeholder.h"
#include "GafferScene/SceneAlgo.h"

#include "Gaffer/ParallelAlgo.h"

#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/Transform.h"
#include "IECoreScene/VisibleRenderable.h"

#include "IECore/Interpolator.h"
#include "IECore/NullObject.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"
#include "boost/container/flat_set.hpp"
#include "boost/multi_index/member.hpp"
#include "boost/multi_index/ordered_index.hpp"
#include "boost/multi_index_container.hpp"

#include "tbb/task.h"

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferScene::Private::RendererAlgo;

//////////////////////////////////////////////////////////////////////////
// Private utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

const InternedString g_openGLRendererName( "OpenGL" );
const InternedString g_compoundRendererName( "Compound" );

// Copied from RendererAlgo.cpp

const InternedString g_cameraGlobalName( "option:render:camera" );
const InternedString g_transformBlurOptionName( "option:render:transformBlur" );
const InternedString g_deformationBlurOptionName( "option:render:deformationBlur" );

const InternedString g_visibleAttributeName( "scene:visible" );
const InternedString g_setsAttributeName( "sets" );
const InternedString g_rendererContextName( "scene:renderer" );

bool visible( const CompoundObject *attributes )
{
	const IECore::BoolData *d = attributes->member<IECore::BoolData>( g_visibleAttributeName );
	return d ? d->readable() : true;
}

bool cameraGlobalsChanged( const CompoundObject *globals, const CompoundObject *previousGlobals, const ScenePlug *scene )
{
	if( !previousGlobals )
	{
		return true;
	}
	CameraPtr camera1 = new Camera;
	CameraPtr camera2 = new Camera;
	SceneAlgo::applyCameraGlobals( camera1.get(), globals, scene );
	SceneAlgo::applyCameraGlobals( camera2.get(), previousGlobals, scene );

	return *camera1 != *camera2;
}

// This is for the very specific case of determining change for global
// attributes, where we need to avoid comparisons of certain synthetic members
// that are only present in previousFullAttributes.
bool globalAttributesChanged( const CompoundObject* globalAttributes, const CompoundObject* previousFullAttributes )
{
	static const boost::container::flat_set<IECore::InternedString> ignoredMembers = { IECore::InternedString( "sets" ) };

	if( !previousFullAttributes )
	{
		return true;
	}

	if( ( globalAttributes->members().size() + ignoredMembers.size() ) != previousFullAttributes->members().size() )
	{
		return true;
	}

	// Borrowed from IECore::CompoundObject, uses a std::map so we can assume iteration
	// order is the same for both containers.

	const CompoundObject::ObjectMap::const_iterator end = previousFullAttributes->members().end();
	CompoundObject::ObjectMap::const_iterator it1 = previousFullAttributes->members().begin();
	CompoundObject::ObjectMap::const_iterator it2 = globalAttributes->members().begin();
	while( it1 != end )
	{
		if( ignoredMembers.find( it1->first ) != ignoredMembers.end() )
		{
			it1++;
			continue;
		}

		if( it1->first != it2->first )
		{
			return true;
		}

		if ( it1->second != it2->second )
		{
			if ( !it1->second || !it2->second )
			{
				/// either one of the pointers is NULL
				return true;
			}
			if( ! it1->second->isEqualTo( it2->second.get() ) )
			{
				return true;
			}
		}
		it1++;
		it2++;
	}

	return false;
}

/// Acts like an ObjectInterfacePtr, with additional functionality
/// for calling an arbitrary function when changing pointee.
struct ObjectInterfaceHandle : public boost::noncopyable
{

	using RemovalCallback = std::function<void ()>;

	ObjectInterfaceHandle()
	{
	}

	~ObjectInterfaceHandle()
	{
		if( m_removalCallback )
		{
			m_removalCallback();
		}
	}

	void operator = ( const IECoreScenePreview::Renderer::ObjectInterfacePtr &p )
	{
		assign( p, RemovalCallback() );
	}

	void assign( const IECoreScenePreview::Renderer::ObjectInterfacePtr &p, const RemovalCallback &removalCallback )
	{
		if( m_removalCallback )
		{
			m_removalCallback();
		}
		m_objectInterface = p;
		m_removalCallback = removalCallback;
	}

	IECoreScenePreview::Renderer::ObjectInterface *operator->() const
	{
		return m_objectInterface.get();
	}

	IECoreScenePreview::Renderer::ObjectInterface *get() const
	{
		return m_objectInterface.get();
	}

	operator bool () const
	{
		return m_objectInterface.get();
	}

	private :

		IECoreScenePreview::Renderer::ObjectInterfacePtr m_objectInterface;
		RemovalCallback m_removalCallback;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Internal implementation details
//////////////////////////////////////////////////////////////////////////

// Maps between scene locations and integer IDs.
class RenderController::IDMap
{

	public :

		// Creates an ID if no ID has been created yet.
		uint32_t acquireID( const ScenePlug::ScenePath &path )
		{
			Mutex::scoped_lock lock( m_mutex, /* write = */ false );
			auto it = m_map.find( path );
			if( it != m_map.end() )
			{
				return it->second;
			}

			lock.upgrade_to_writer();
			return m_map.insert( PathAndID( path, m_map.size() + 1 ) ).first->second;
		}

		uint32_t idForPath( const ScenePlug::ScenePath &path ) const
		{
			Mutex::scoped_lock lock( m_mutex, /* write = */ false );
			auto it = m_map.find( path );
			if( it != m_map.end() )
			{
				return it->second;
			}
			return 0;
		}

		std::optional<ScenePlug::ScenePath> pathForID( uint32_t id ) const
		{
			Mutex::scoped_lock lock( m_mutex, /* write = */ false );
			auto &index = m_map.get<1>();
			auto it = index.find( id );
			if( it != index.end() )
			{
				return it->first;
			}
			return std::nullopt;
		}

	private :

		using PathAndID = std::pair<ScenePlug::ScenePath, uint32_t>;
		using Map = boost::multi_index::multi_index_container<
			PathAndID,
			boost::multi_index::indexed_by<
				boost::multi_index::ordered_unique<
					boost::multi_index::member<PathAndID, ScenePlug::ScenePath, &PathAndID::first>
				>,
				boost::multi_index::ordered_unique<
					boost::multi_index::member<PathAndID, uint32_t, &PathAndID::second>
				>
			>
		>;
		using Mutex = tbb::spin_rw_mutex;

		Map m_map;
		mutable Mutex m_mutex;

};

// Represents a location in the Gaffer scene as specified to the
// renderer. We use this to build up a persistent representation of
// the scene which we can traverse to perform selective updates to
// only the changed locations. A Renderer's representation of the
// scene contains only a flat list of objects, whereas the SceneGraph
// maintains the original hierarchy, providing the means of flattening
// attribute and transform state for passing to the renderer. Calls
// to update() are made from a threaded scene traversal performed by
// SceneGraphUpdateTask.
class RenderController::SceneGraph
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
			LightFilterType = 2,
			ObjectType = 3,
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
			ExpansionComponent = 32,
			AllComponents = BoundComponent | TransformComponent | AttributesComponent | ObjectComponent | ChildNamesComponent | ExpansionComponent,
		};

		// Constructs the root of the scene graph.
		// Children are constructed using updateChildren().
		SceneGraph()
			:	m_parent( nullptr ), m_fullAttributes( new CompoundObject ), m_dirtyComponents( AllComponents ), m_changedComponents( NoComponent )
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

		void dirty( unsigned components )
		{
			if( ( components & m_dirtyComponents ) == components )
			{
				return;
			}
			m_dirtyComponents |= components;
			for( const auto &c : m_children )
			{
				c->dirty( components );
			}
		}

		// Called by SceneGraphUpdateTask to update this location. Returns true if
		// anything changed.
		bool update( const ScenePlug::ScenePath &path, unsigned changedGlobals, Type type, RenderController *controller )
		{
			const unsigned originalChangedComponents = m_changedComponents;

			// Attributes

			if( !m_parent )
			{
				// Root - get attributes from globals.
				if( changedGlobals & GlobalsGlobalComponent )
				{
					if( updateAttributes( controller->m_globals.get() ) )
					{
						m_changedComponents |= AttributesComponent;
					}
				}
			}
			else
			{
				// Non-root - get attributes the standard way.
				const bool parentAttributesChanged = m_parent->m_changedComponents & AttributesComponent;
				if( parentAttributesChanged || ( m_dirtyComponents & AttributesComponent ) )
				{
					if( updateAttributes( controller->m_scene->attributesPlug(), parentAttributesChanged ) )
					{
						m_changedComponents |= AttributesComponent;
					}
				}

				// If attributes have changed, need to check if this has affected our motion sample times
				if( ( m_changedComponents & AttributesComponent ) || ( changedGlobals & TransformBlurGlobalComponent ) )
				{
					if( Private::RendererAlgo::transformMotionTimes( controller->m_motionBlurOptions.transformBlur, controller->m_motionBlurOptions.shutter, m_fullAttributes.get(), m_transformTimes ) )
					{
						m_dirtyComponents |= TransformComponent;
					}
				}

				if( ( m_changedComponents & AttributesComponent ) || ( changedGlobals & DeformationBlurGlobalComponent ) )
				{
					if( Private::RendererAlgo::deformationMotionTimes( controller->m_motionBlurOptions.deformationBlur, controller->m_motionBlurOptions.shutter, m_fullAttributes.get(), m_deformationTimes ) )
					{
						m_dirtyComponents |= ObjectComponent;
					}
				}
			}

			if( !::visible( m_fullAttributes.get() ) )
			{
				clear();
				return originalChangedComponents != m_changedComponents;
			}

			// Render Sets. We must obviously update these if
			// the sets have changed, but we also need to do an
			// update if the attributes have changed, because in
			// that case we may have overwritten the sets attribute.

			if( ( changedGlobals & RenderSetsGlobalComponent ) || ( m_changedComponents & AttributesComponent ) )
			{
				if( updateRenderSets( path, controller->m_renderSets ) )
				{
					m_changedComponents |= AttributesComponent;
				}
			}

			clean( AttributesComponent );

			// Transform

			const bool parentTransformChanged = m_parent && ( m_parent->m_changedComponents & TransformComponent );
			if( ( m_dirtyComponents & TransformComponent ) || parentTransformChanged )
			{
				if( updateTransform( controller->m_scene->transformPlug(), parentTransformChanged, controller->m_motionBlurOptions ) )
				{
					m_changedComponents |= TransformComponent;
				}
			}

			clean( TransformComponent );

			// Object

			if( ( m_dirtyComponents & ObjectComponent ) && updateObject( controller->m_scene->objectPlug(), type, controller->m_renderer.get(), controller->m_globals.get(), controller->m_scene.get(), controller->m_lightLinks.get(), controller->m_motionBlurOptions ) )
			{
				m_changedComponents |= ObjectComponent;
			}

			if( m_objectInterface )
			{
				if( !(m_changedComponents & ObjectComponent) )
				{
					// Apply attribute update to old object if necessary.
					if( m_changedComponents & AttributesComponent )
					{
						if( m_objectInterface->attributes( attributesInterface( controller->m_renderer.get() ) ) )
						{
							// Update succeeded. Update light filter links if necessary.
							if( type == LightFilterType && controller->m_lightLinks )
							{
								controller->m_lightLinks->updateLightFilter( m_objectInterface.get(), m_fullAttributes.get() );
							}
						}
						else
						{
							// Failed to apply attributes - must replace entire object.
							m_objectHash = MurmurHash();
							if( updateObject( controller->m_scene->objectPlug(), type, controller->m_renderer.get(), controller->m_globals.get(), controller->m_scene.get(), controller->m_lightLinks.get(), controller->m_motionBlurOptions ) )
							{
								m_changedComponents |= ObjectComponent;
								controller->m_failedAttributeEdits++;
							}
						}
					}
				}
			}

			if( m_objectInterface )
			{
				// If the transform has changed, or we have an entirely new object,
				// the apply the transform.
				if( m_changedComponents & ( ObjectComponent | TransformComponent ) )
				{
					assert( m_fullTransform.size() );
					if( !m_transformTimesOutput )
					{
						m_objectInterface->transform( m_fullTransform[0] );
					}
					else
					{
						m_objectInterface->transform( m_fullTransform, *m_transformTimesOutput );
					}
				}

				// Assign an ID
				if( m_changedComponents & ObjectComponent )
				{
					// We don't assign IDs for OpenGL renders, because the OpenGL renderer
					// assigns its own lightweight IDs.
					/// \todo Measure overhead and consider using same IDs everywhere.
					if( controller->m_renderer->name() != g_openGLRendererName )
					{
						m_objectInterface->assignID( controller->m_idMap->acquireID( path ) );
					}
				}

				if( type == ObjectType && controller->m_lightLinks )
				{
					// Apply light links if necessary.
					if( m_changedComponents & ( ObjectComponent | AttributesComponent ) || controller->m_lightLinks->lightLinksDirty() )
					{
						controller->m_lightLinks->outputLightLinks( controller->m_scene.get(), m_fullAttributes.get(), m_objectInterface.get(), &m_lightLinksHash );
					}
				}
			}

			clean( ObjectComponent );

			// Children

			if( ( m_dirtyComponents & ChildNamesComponent ) && updateChildren( controller->m_scene->childNamesPlug() ) )
			{
				m_changedComponents |= ChildNamesComponent;
			}

			clean( ChildNamesComponent );

			// Expansion

			if( ( m_dirtyComponents & ExpansionComponent ) && updateExpansion( path, controller->m_expandedPaths, controller->m_minimumExpansionDepth ) )
			{
				m_changedComponents |= ExpansionComponent;
			}

			bool newBound = false;
			if(
				( m_changedComponents & ( ExpansionComponent | ChildNamesComponent ) ) ||
				( m_dirtyComponents & BoundComponent )
			)
			{
				// Create bounding box if needed
				Box3f bound;
				if( !m_expanded && m_children.size() )
				{
					bound = controller->m_scene->boundPlug()->getValue();
				}

				if( !bound.isEmpty() )
				{
					IECoreScenePreview::PlaceholderPtr placeholder = new IECoreScenePreview::Placeholder( bound );

					std::string boundName;
					ScenePlug::pathToString( path, boundName );
					boundName += "/__unexpandedChildren__";

					if( controller->m_renderer->name() != g_openGLRendererName )
					{
						// See comments in `updateObject()`.
						m_boundInterface = nullptr;
					}

					m_boundInterface = controller->m_renderer->object( boundName, placeholder.get(), controller->m_defaultAttributes.get() );
					if( m_boundInterface )
					{
						newBound = true;
					}
				}
				else
				{
					m_boundInterface = nullptr;
				}
			}

			if( newBound || ( m_boundInterface && ( m_changedComponents & TransformComponent ) ) )
			{
				// Apply transform to bounding box
				assert( m_fullTransform.size() );
				if( !m_transformTimesOutput )
				{
					m_boundInterface->transform( m_fullTransform[0] );
				}
				else
				{
					m_boundInterface->transform( m_fullTransform, *m_transformTimesOutput );
				}
			}

			clean( ExpansionComponent | BoundComponent );

			m_cleared = false;

			assert( m_dirtyComponents == NoComponent );

			return originalChangedComponents != m_changedComponents;
		}

		bool expanded() const
		{
			return m_expanded;
		}

		const std::vector<std::unique_ptr<SceneGraph>> &children()
		{
			return m_children;
		}

		void allChildrenUpdated()
		{
			m_changedComponents = NoComponent;
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
			m_children.clear();
			clearObject();
			m_attributesHash = m_lightLinksHash = m_transformHash = m_childNamesHash = IECore::MurmurHash();
			m_cleared = true;
			m_expanded = false;
			m_boundInterface = nullptr;
			m_dirtyComponents = AllComponents;
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

			// m_fullAttributes contains things other than just the globals attributes
			// (@see updateRenderSets). We have a couple of options here:
			//
			//  1) Tracks set changes separately to attributes, and create
			//     fullAttributes on the fly.
			//  2) Minimise held state and the needs to recreate fullAttributes,
			//     at the expense of maintaining custom comparison code.
			//
			//  The second options seems preferable, given a direct comparison
			//  already involves a full iteration over attributes, and as such
			//  we're not adding much overhead.
			if( !globalAttributesChanged( globalAttributes.get(), m_fullAttributes.get() ) )
			{
				return false;
			}

			m_fullAttributes->members() = globalAttributes->members();
			m_attributesInterface = nullptr;

			return true;
		}

		bool updateRenderSets( const ScenePlug::ScenePath &path, const Private::RendererAlgo::RenderSets &renderSets )
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
		bool updateTransform( const M44fPlug *transformPlug, bool parentTransformChanged, const MotionBlurOptions &motionBlurOptions  )
		{
			if( parentTransformChanged )
			{
				// We don't store the local transform - if the parent has changed, wipe the hash
				// to ensure that we recompute the local transform so we can redo the concatenation
				m_transformHash = IECore::MurmurHash();
			}

			vector<M44f> samples;
			if( !Private::RendererAlgo::transformSamples( transformPlug, m_transformTimes, samples, &m_transformHash ) )
			{
				return false;
			}

			if( !m_parent )
			{
				m_fullTransform = samples;
				m_transformTimesOutput = samples.size() > 1 ? &m_transformTimes : nullptr;
			}
			else
			{
				m_fullTransform.clear();
				if( samples.size() == 1 )
				{
					m_fullTransform.reserve( m_parent->m_fullTransform.size() );
					for( const M44f& it : m_parent->m_fullTransform )
					{
						m_fullTransform.push_back( samples.front() * it );
					}
					m_transformTimesOutput = m_parent->m_transformTimesOutput;
				}
				else
				{
					m_transformTimesOutput = &m_transformTimes;
					m_fullTransform.reserve( samples.size() );

					for( size_t i = 0; i < samples.size(); i++ )
					{
						m_fullTransform.push_back( samples[i] * m_parent->fullTransform( m_transformTimes[i] ) );
					}
				}
			}
			return true;
		}

		// Returns true if the object changed.
		bool updateObject( const ObjectPlug *objectPlug, Type type, IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const ScenePlug *scene, LightLinks *lightLinks, const MotionBlurOptions &motionBlurOptions )
		{
			const bool hadObjectInterface = static_cast<bool>( m_objectInterface );
			if( type == NoType )
			{
				clearObject();
				return hadObjectInterface;
			}

			// Types that don't support motion blur
			if( type == LightType || type == LightFilterType )
			{
				const IECore::MurmurHash objectHash = objectPlug->hash();
				if( objectHash == m_objectHash )
				{
					return false;
				}

				IECore::ConstObjectPtr object = objectPlug->getValue( &objectHash );
				m_objectHash = objectHash;

				const IECore::NullObject *nullObject = runTimeCast<const IECore::NullObject>( object.get() );
				if( renderer->name() != g_openGLRendererName )
				{
					m_objectInterface = nullptr;
				}

				std::string name;
				ScenePlug::pathToString( Context::current()->get<vector<InternedString> >( ScenePlug::scenePathContextName ), name );
				if( type == LightType )
				{
					auto light = renderer->light( name, nullObject ? nullptr : object.get(), attributesInterface( renderer ) );
					if( light && lightLinks )
					{
						lightLinks->addLight( name, light );
						m_objectInterface.assign(
							light,
							[name, lightLinks]() {
								lightLinks->removeLight( name );
							}
						);
					}
					else
					{
						m_objectInterface = light;
					}
				}
				else
				{
					auto lightFilter = renderer->lightFilter( name, nullObject ? nullptr : object.get(), attributesInterface( renderer ) );
					if( lightFilter && lightLinks )
					{
						lightLinks->addLightFilter( lightFilter, m_fullAttributes.get() );
						m_objectInterface.assign(
							lightFilter,
							[lightFilter, lightLinks]() {
								lightLinks->removeLightFilter( lightFilter );
							}
						);
					}
					else
					{
						m_objectInterface = lightFilter;
					}
				}

				return true;

			}

			vector<ConstObjectPtr> samples;
			if( !Private::RendererAlgo::objectSamples( objectPlug, m_deformationTimes, samples, &m_objectHash ) )
			{
				return false;
			}

			bool isNull = true;
			for( ConstObjectPtr &i : samples )
			{
				if( !runTimeCast<const IECore::NullObject>( i.get() ) )
				{
					isNull = false;
				}
			}

			if( (type != LightType && type != LightFilterType) && isNull )
			{
				m_objectInterface = nullptr;
				return hadObjectInterface;
			}

			if( renderer->name() != g_openGLRendererName )
			{
				// Delete our current object interface before we potentially
				// create a new one. This is essential for renderer backends
				// which rely on object names being unique (typically because
				// they use them as handles in the renderer they connect to).
				// We avoid doing this for the OpenGL renderer though, because
				// destroying the object before its replacement is ready can
				// lead to the object flickering during progressive updates
				// in Gaffer's viewport (the OpenGL renderer is designed such
				// that it can draw concurrently with the updates we make,
				// whereas other renderers must wait for all edits to be complete
				// first).
				//
				/// \todo Consider ways of redesigning the Renderer API so this
				/// is cleaner. Should there be an atomic way of swapping an
				/// ObjectInterface? Or a way of updating geometry without creating
				/// a new object? Perhaps the latter could allow a smart backend to make
				/// more minimal edits?
				m_objectInterface = nullptr;
			}

			std::string name;
			ScenePlug::pathToString( Context::current()->get<vector<InternedString> >( ScenePlug::scenePathContextName ), name );
			if( type == CameraType )
			{
				vector<ConstCameraPtr> cameraSamples; cameraSamples.reserve( samples.size() );
				for( const auto &sample : samples )
				{
					if( auto cameraSample = runTimeCast<const Camera>( sample.get() ) )
					{
						IECoreScene::CameraPtr cameraSampleCopy = cameraSample->copy();
						SceneAlgo::applyCameraGlobals( cameraSampleCopy.get(), globals, scene );
						cameraSamples.push_back( cameraSampleCopy );
					}
				}

				// Create ObjectInterface

				if( !samples.size() || cameraSamples.size() != samples.size() )
				{
					IECore::msg(
						IECore::Msg::Warning,
						"RenderController::updateObject",
						boost::format( "Camera missing for location \"%1%\" at frame %2%" )
							% name
							% Context::current()->getFrame()
					);
				}
				else
				{
					if( cameraSamples.size() == 1 )
					{
						m_objectInterface = renderer->camera(
							name,
							cameraSamples[0].get(),
							attributesInterface( renderer )
						);
					}
					else
					{
						vector<const Camera *> rawCameraSamples; rawCameraSamples.reserve( cameraSamples.size() );
						for( auto &c : cameraSamples )
						{
							rawCameraSamples.push_back( c.get() );
						}
						m_objectInterface = renderer->camera(
							name,
							rawCameraSamples,
							m_deformationTimes,
							attributesInterface( renderer )
						);
					}
				}
			}
			else
			{
				if( !samples.size() )
				{
					return true;
				}

				if( samples.size() == 1 )
				{
					m_objectInterface = renderer->object( name, samples[0].get(), attributesInterface( renderer ) );
				}
				else
				{
					/// \todo Can we rejig things so this conversion isn't necessary?
					vector<const Object *> objectsVector; objectsVector.reserve( samples.size() );
					for( const auto &sample : samples )
					{
						objectsVector.push_back( sample.get() );
					}
					m_objectInterface = renderer->object( name, objectsVector, m_deformationTimes, attributesInterface( renderer ) );
				}
			}

			return true;
		}

		void clearObject()
		{
			m_objectInterface = nullptr;
			m_objectHash = MurmurHash();
		}

		bool updateExpansion( const ScenePlug::ScenePath &path, const IECore::PathMatcher &expandedPaths, size_t minimumExpansionDepth )
		{
			const bool expanded = ( minimumExpansionDepth >= path.size() ) || ( expandedPaths.match( path ) & PathMatcher::ExactMatch );
			if( expanded == m_expanded )
			{
				return false;
			}
			m_expanded = expanded;
			return true;
		}

		// Ensures that children() contains a child for every name specified
		// by childNamesPlug(). This just ensures that the children exist - they
		// will subsequently be updated in parallel by the SceneGraphUpdateTask.
		bool updateChildren( const InternedStringVectorDataPlug *childNamesPlug )
		{
			const IECore::MurmurHash childNamesHash = childNamesPlug->hash();
			if( childNamesHash == m_childNamesHash )
			{
				return false;
			}

			IECore::ConstInternedStringVectorDataPtr childNamesData = childNamesPlug->getValue( &childNamesHash );
			const std::vector<IECore::InternedString> &childNames = childNamesData->readable();
			m_childNamesHash = childNamesHash;

			// Our vector of children no longer matches `childNames`, but we may be
			// able to reuse most of them (often only one has been added or removed).
			// Move them to the side and sort them by name for quick lookups.

			vector<unique_ptr<SceneGraph>> oldChildren;
			oldChildren.swap( m_children );
			sort(
				oldChildren.begin(), oldChildren.end(),
				[]( const unique_ptr<SceneGraph> &a, const unique_ptr<SceneGraph> &b )
				{
					return a->m_name < b->m_name;
				}
			);

			// As we refill `m_children`, we're going to transfer ownership out of
			// `oldChildren` as we go. This will leave nullptr gaps in `oldChildren`,
			// breaking the sorting needed by `lower_bound()`. We therefore use this
			// non-owning copy to perform the search.

			vector<SceneGraph *> oldChildrenRaw;
			oldChildrenRaw.reserve( oldChildren.size() );
			for( const auto &c : oldChildren )
			{
				oldChildrenRaw.push_back( c.get() );
			}

			// Fill m_children with a combination of old and new children as necessary.

			m_children.reserve( childNames.size() );
			for( const auto &name : childNames )
			{
				auto it = lower_bound(
					oldChildrenRaw.begin(), oldChildrenRaw.end(),
					name,
					[]( const SceneGraph *a, const InternedString &b )
					{
						return a->m_name < b;
					}
				);

				if( it != oldChildrenRaw.end() && (*it)->m_name == name )
				{
					decltype( it )::difference_type index = it - oldChildrenRaw.begin();
					if( !oldChildren[ index ] )
					{
						std::string path;
						ScenePlug::pathToString( Context::current()->get<vector<InternedString> >( ScenePlug::scenePathContextName ), path );
						path += "/" + name.string();
						throw Exception( "RenderControllerSceneGraph::updateChildren() failed.  Duplicate children with name: " + path );
					}
					m_children.push_back( std::move( oldChildren[ index ] ) );
				}
				else
				{
					m_children.push_back( unique_ptr<SceneGraph>( new SceneGraph( name, this ) ) );
				}
			}

			return true;
		}

		void clean( unsigned components )
		{
			m_dirtyComponents &= ~components;
		}

		M44f fullTransform( float time ) const
		{
			if( m_fullTransform.empty() )
			{
				return M44f();
			}
			if( !m_transformTimesOutput )
			{
				return m_fullTransform[0];
			}

			vector<float>::const_iterator t1 = lower_bound( m_transformTimesOutput->begin(), m_transformTimesOutput->end(), time );
			if( t1 == m_transformTimesOutput->begin() || *t1 == time )
			{
				return m_fullTransform[t1 - m_transformTimesOutput->begin()];
			}
			else
			{
				vector<float>::const_iterator t0 = t1 - 1;
				const float l = lerpfactor( time, *t0, *t1 );
				const M44f &s0 = m_fullTransform[t0 - m_transformTimesOutput->begin()];
				const M44f &s1 = m_fullTransform[t1 - m_transformTimesOutput->begin()];
				M44f result;
				LinearInterpolator<M44f>()( s0, s1, l, result );
				return result;
			}
		}

		IECore::InternedString m_name;

		const SceneGraph *m_parent;

		IECore::MurmurHash m_objectHash;
		ObjectInterfaceHandle m_objectInterface;
		std::vector<float> m_deformationTimes;

		IECore::MurmurHash m_attributesHash;
		IECore::CompoundObjectPtr m_fullAttributes;
		IECoreScenePreview::Renderer::AttributesInterfacePtr m_attributesInterface;
		IECore::MurmurHash m_lightLinksHash;

		IECore::MurmurHash m_transformHash;
		std::vector<Imath::M44f> m_fullTransform;
		std::vector<float> m_transformTimes;

		// The m_transformTimes represents what times we sample the transform at.  The actual
		// times we output at may differ due to the transform samples turning out to not vary,
		// or inheriting parent samples
		std::vector<float> *m_transformTimesOutput;

		IECore::MurmurHash m_childNamesHash;
		std::vector<std::unique_ptr<SceneGraph>> m_children;

		IECoreScenePreview::Renderer::ObjectInterfacePtr m_boundInterface;
		bool m_expanded;

		// Tracks work which needs to be done on
		// the next call to `update()`.
		unsigned m_dirtyComponents;
		// Tracks things that were changed on the last
		// call to `update()`. This is needed in two
		// scenarios :
		//
		//  - When `update()` is cancelled part way
		//    through either through cancellation or
		//    a computation error. In the next call to
		//    `update()` we need to know what we
		//    changed previously because we won't repeat
		//    the part of the update that we completed before.
		//  - From the `update()` call for our children.
		//    The children need to know if the parent transform
		//    or attributes changed so they can concatenate
		//    them appropriately.
		//
		// We clear `m_changedComponents` once all children have
		// been updated successfully, in `allChildrenUpdated()`.
		unsigned m_changedComponents;

		bool m_cleared;

};

// TBB task used to perform multithreaded updates on our SceneGraph.
class RenderController::SceneGraphUpdateTask : public tbb::task
{

	public :

		SceneGraphUpdateTask(
			RenderController *controller,
			SceneGraph *sceneGraph,
			SceneGraph::Type sceneGraphType,
			unsigned changedGlobalComponents,
			const ThreadState &threadState,
			const ScenePlug::ScenePath &scenePath,
			const ProgressCallback &callback,
			const PathMatcher *pathsToUpdate
		)
			:	m_controller( controller ),
				m_sceneGraph( sceneGraph ),
				m_sceneGraphType( sceneGraphType ),
				m_changedGlobalComponents( changedGlobalComponents ),
				m_threadState( threadState ),
				m_scenePath( scenePath ),
				m_callback( callback ),
				m_pathsToUpdate( pathsToUpdate )
		{
		}

		task *execute() override
		{

			const unsigned pathsToUpdateMatch = m_pathsToUpdate ? m_pathsToUpdate->match( m_scenePath ) : (unsigned)PathMatcher::EveryMatch;
			if( !pathsToUpdateMatch )
			{
				return nullptr;
			}

			// Figure out if this location belongs in the type
			// of scene graph we're constructing. If it doesn't
			// belong, and neither do any of its descendants,
			// we can just early out.

			const unsigned sceneGraphMatch = this->sceneGraphMatch();
			if( !( sceneGraphMatch & ( IECore::PathMatcher::ExactMatch | IECore::PathMatcher::DescendantMatch ) ) )
			{
				m_sceneGraph->clear();
				return nullptr;
			}

			// Set up a context to compute the scene at the right
			// location.

			ScenePlug::PathScope pathScope( m_threadState, &m_scenePath );

			// Update the scene graph at this location.

			const bool changesMade = m_sceneGraph->update(
				m_scenePath,
				m_changedGlobalComponents,
				sceneGraphMatch & IECore::PathMatcher::ExactMatch ? m_sceneGraphType : SceneGraph::NoType,
				m_controller
			);

			if( changesMade && m_callback )
			{
				m_callback( BackgroundTask::Running );
			}

			// Spawn subtasks to apply updates to each child.

			const auto &children = m_sceneGraph->children();
			if( m_sceneGraph->expanded() && children.size() )
			{
				set_ref_count( 1 + children.size() );

				ScenePlug::ScenePath childPath = m_scenePath;
				childPath.push_back( IECore::InternedString() ); // space for the child name
				for( const auto &child : children )
				{
					childPath.back() = child->name();
					SceneGraphUpdateTask *t = new( allocate_child() ) SceneGraphUpdateTask( m_controller, child.get(), m_sceneGraphType, m_changedGlobalComponents, m_threadState, childPath, m_callback, m_pathsToUpdate );
					spawn( *t );
				}

				wait_for_all();
			}
			else
			{
				for( auto &child : children )
				{
					child->clear();
				}
			}

			if( pathsToUpdateMatch & ( PathMatcher::AncestorMatch | PathMatcher::ExactMatch ) )
			{
				m_sceneGraph->allChildrenUpdated();
			}

			return nullptr;
		}

	private :

		const ScenePlug *scene()
		{
			return m_controller->m_scene.get();
		}

		/// \todo Fast path for when sets were not dirtied.
		unsigned sceneGraphMatch() const
		{
			switch( m_sceneGraphType )
			{
				case SceneGraph::CameraType :
					return m_controller->m_renderSets.camerasSet().match( m_scenePath );
				case SceneGraph::LightType :
					return m_controller->m_renderSets.lightsSet().match( m_scenePath );
				case SceneGraph::LightFilterType :
					return m_controller->m_renderSets.lightFiltersSet().match( m_scenePath );
				case SceneGraph::ObjectType :
				{
					unsigned m = m_controller->m_renderSets.lightsSet().match( m_scenePath ) |
					             m_controller->m_renderSets.camerasSet().match( m_scenePath );
					if( m & IECore::PathMatcher::ExactMatch )
					{
						return IECore::PathMatcher::AncestorMatch | IECore::PathMatcher::DescendantMatch;
					}
					else
					{
						return IECore::PathMatcher::EveryMatch;
					}
				}
				default :
					return IECore::PathMatcher::NoMatch;
			}
		}

		RenderController *m_controller;
		SceneGraph *m_sceneGraph;
		SceneGraph::Type m_sceneGraphType;
		unsigned m_changedGlobalComponents;
		const ThreadState &m_threadState;
		ScenePlug::ScenePath m_scenePath;
		const ProgressCallback &m_callback;
		const PathMatcher *m_pathsToUpdate;

};

//////////////////////////////////////////////////////////////////////////
// RenderController
//////////////////////////////////////////////////////////////////////////

RenderController::RenderController( const ConstScenePlugPtr &scene, const Gaffer::ConstContextPtr &context, const IECoreScenePreview::RendererPtr &renderer )
	:	m_renderer( renderer ),
		m_idMap( std::make_unique<IDMap>() ),
		m_minimumExpansionDepth( 0 ),
		m_updateRequired( false ),
		m_updateRequested( false ),
		m_failedAttributeEdits( 0 ),
		m_dirtyGlobalComponents( NoGlobalComponent ),
		m_changedGlobalComponents( NoGlobalComponent ),
		m_globals( new CompoundObject )
{
	for( int i = SceneGraph::FirstType; i <= SceneGraph::LastType; ++i )
	{
		m_sceneGraphs.push_back( unique_ptr<SceneGraph>( new SceneGraph ) );
	}

	if( renderer->name() != g_openGLRendererName )
	{
		// We avoid light linking overhead for the GL renderer,
		// because we know it doesn't support it.
		m_lightLinks = std::make_unique<LightLinks>();
	}

	IECore::CompoundObjectPtr defaultAttributes = new CompoundObject();
	m_defaultAttributes = m_renderer->attributes( defaultAttributes.get() );

	setScene( scene );
	setContext( context );
}

RenderController::~RenderController()
{
	// Cancel background task before the things it relies
	// on are destroyed.
	cancelBackgroundTask();
	// Drop references to ObjectInterfaces before the renderer
	// is destroyed.
	m_renderer->pause();
	m_sceneGraphs.clear();
	m_defaultCamera.reset();
	m_lightLinks.reset();
}

IECoreScenePreview::Renderer *RenderController::renderer()
{
	return m_renderer.get();
}

void RenderController::setScene( const ConstScenePlugPtr &scene )
{
	if( scene == m_scene )
	{
		return;
	}

	const Node *node = scene->node();
	if( !node )
	{
		throw Exception( "Scene must belong to a Node" );
	}

	cancelBackgroundTask();

	m_scene = scene;
	m_plugDirtiedConnection = const_cast<Node *>( node )->plugDirtiedSignal().connect(
		boost::bind( &RenderController::plugDirtied, this, ::_1 )
	);

	dirtyGlobals( AllGlobalComponents );
	dirtySceneGraphs( SceneGraph::AllComponents );
	requestUpdate();
}

const ScenePlug *RenderController::getScene() const
{
	return m_scene.get();
}

void RenderController::setContext( const Gaffer::ConstContextPtr &context )
{
	if( m_context == context )
	{
		return;
	}

	cancelBackgroundTask();

	m_context = context;
	m_contextChangedConnection = const_cast<Context *>( m_context.get() )->changedSignal().connect(
		boost::bind( &RenderController::contextChanged, this, ::_2 )
	);

	dirtyGlobals( AllGlobalComponents );
	dirtySceneGraphs( SceneGraph::AllComponents );
	requestUpdate();
}

const Gaffer::Context *RenderController::getContext() const
{
	return m_context.get();
}

void RenderController::setExpandedPaths( const IECore::PathMatcher &expandedPaths )
{
	cancelBackgroundTask();

	m_expandedPaths = expandedPaths;
	dirtySceneGraphs( SceneGraph::ExpansionComponent );
	requestUpdate();
}

const IECore::PathMatcher &RenderController::getExpandedPaths() const
{
	return m_expandedPaths;
}

void RenderController::setMinimumExpansionDepth( size_t depth )
{
	if( depth == m_minimumExpansionDepth )
	{
		return;
	}

	cancelBackgroundTask();

	m_minimumExpansionDepth = depth;
	dirtySceneGraphs( SceneGraph::ExpansionComponent );
	requestUpdate();
}

size_t RenderController::getMinimumExpansionDepth() const
{
	return m_minimumExpansionDepth;
}

RenderController::UpdateRequiredSignal &RenderController::updateRequiredSignal()
{
	return m_updateRequiredSignal;
}

bool RenderController::updateRequired() const
{
	return m_updateRequired;
}

void RenderController::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == m_scene->boundPlug() )
	{
		dirtySceneGraphs( SceneGraph::BoundComponent );
	}
	else if( plug == m_scene->transformPlug() )
	{
		dirtySceneGraphs( SceneGraph::TransformComponent );
	}
	else if( plug == m_scene->attributesPlug() )
	{
		dirtySceneGraphs( SceneGraph::AttributesComponent );
	}
	else if( plug == m_scene->objectPlug() )
	{
		dirtySceneGraphs( SceneGraph::ObjectComponent );
	}
	else if( plug == m_scene->childNamesPlug() )
	{
		dirtySceneGraphs( SceneGraph::ChildNamesComponent );
	}
	else if( plug == m_scene->globalsPlug() )
	{
		dirtyGlobals( GlobalsGlobalComponent );
	}
	else if( plug == m_scene->setPlug() )
	{
		dirtyGlobals( SetsGlobalComponent );
	}
	else if( plug == m_scene )
	{
		requestUpdate();
	}
}

void RenderController::contextChanged( const IECore::InternedString &name )
{
	if( boost::starts_with( name.string(), "ui:" ) )
	{
		return;
	}

	cancelBackgroundTask();

	dirtyGlobals( AllGlobalComponents );
	dirtySceneGraphs( SceneGraph::AllComponents );
	requestUpdate();
}

void RenderController::requestUpdate()
{
	m_updateRequired = true;
	if( !m_updateRequested )
	{
		m_updateRequested = true;
		updateRequiredSignal()( *this );
	}
}

void RenderController::dirtyGlobals( unsigned components )
{
	m_dirtyGlobalComponents |= components;
}

void RenderController::dirtySceneGraphs( unsigned components )
{
	for( auto &sg : m_sceneGraphs )
	{
		sg->dirty( components );
	}

	if( components & SceneGraph::ObjectComponent )
	{
		// We don't track dirtiness of different SceneGraphs separately anyway,
		// so just recheck if a camera has changed a shutter override whenever
		// any object is dirtied
		m_changedGlobalComponents |= CameraShutterGlobalComponent;
	}
}

void RenderController::update( const ProgressCallback &callback )
{
	if( !m_scene || !m_context )
	{
		return;
	}

	m_updateRequested = false;

	Context::EditableScope scopedContext( m_context.get() );
	scopedContext.set( "scene:renderer", &m_renderer->name().string() );

	updateInternal( callback );
}

std::shared_ptr<Gaffer::BackgroundTask> RenderController::updateInBackground( const ProgressCallback &callback, const IECore::PathMatcher &priorityPaths )
{
	if( !m_scene || !m_context )
	{
		return nullptr;
	}

	m_updateRequested = false;
	cancelBackgroundTask();

	Context::EditableScope scopedContext( m_context.get() );
	scopedContext.set( "scene:renderer", &m_renderer->name().string() );

	m_backgroundTask = ParallelAlgo::callOnBackgroundThread(
		// Subject
		m_scene.get(),
		[this, callback, priorityPaths] {
			if( !priorityPaths.isEmpty() )
			{
				updateInternal( callback, &priorityPaths, /* signalCompletion = */ false );
			}
			updateInternal( callback );
		}
	);

	return m_backgroundTask;
}

void RenderController::updateMatchingPaths( const IECore::PathMatcher &pathsToUpdate, const ProgressCallback &callback )
{
	if( !m_scene || !m_context )
	{
		return;
	}

	Context::EditableScope scopedContext( m_context.get() );
	scopedContext.set( "scene:renderer", &m_renderer->name().string() );

	updateInternal( callback, &pathsToUpdate );
}

void RenderController::updateInternal( const ProgressCallback &callback, const IECore::PathMatcher *pathsToUpdate, bool signalCompletion )
{
	try
	{
		// Update globals
		if( m_dirtyGlobalComponents & GlobalsGlobalComponent )
		{
			ConstCompoundObjectPtr globals = m_scene->globalsPlug()->getValue();
			Private::RendererAlgo::outputOptions( globals.get(), m_globals.get(), m_renderer.get() );
			Private::RendererAlgo::outputOutputs( m_scene.get(), globals.get(), m_globals.get(), m_renderer.get() );
			if( !m_globals || *m_globals != *globals )
			{
				m_changedGlobalComponents |= GlobalsGlobalComponent;
			}
			if( cameraGlobalsChanged( globals.get(), m_globals.get(), m_scene.get() ) )
			{
				m_changedGlobalComponents |= CameraOptionsGlobalComponent;
			}
			m_globals = globals;
		}

		// Update motion blur options
		if( m_changedGlobalComponents & ( GlobalsGlobalComponent | CameraShutterGlobalComponent ) )
		{
			const BoolData *transformBlurData = m_globals->member<BoolData>( g_transformBlurOptionName );
			bool transformBlur = transformBlurData ? transformBlurData->readable() : false;

			const BoolData *deformationBlurData = m_globals->member<BoolData>( g_deformationBlurOptionName );
			bool deformationBlur = deformationBlurData ? deformationBlurData->readable() : false;

			V2f shutter = SceneAlgo::shutter( m_globals.get(), m_scene.get() );

			if( shutter != m_motionBlurOptions.shutter || transformBlur != m_motionBlurOptions.transformBlur )
			{
				m_changedGlobalComponents |= TransformBlurGlobalComponent;
			}
			if( shutter != m_motionBlurOptions.shutter || deformationBlur != m_motionBlurOptions.deformationBlur )
			{
				m_changedGlobalComponents |= DeformationBlurGlobalComponent;
			}
			if( shutter != m_motionBlurOptions.shutter )
			{
				m_changedGlobalComponents |= CameraOptionsGlobalComponent;
			}
			m_motionBlurOptions.transformBlur = transformBlur;
			m_motionBlurOptions.deformationBlur = deformationBlur;
			m_motionBlurOptions.shutter = shutter;
		}

		if( m_dirtyGlobalComponents & SetsGlobalComponent )
		{
			if( m_renderSets.update( m_scene.get() ) & Private::RendererAlgo::RenderSets::RenderSetsChanged )
			{
				m_changedGlobalComponents |= RenderSetsGlobalComponent;
			}
			// Light linking expressions might refer to any set, so we
			// must assume that linking needs to be recalculated.
			if( m_lightLinks )
			{
				m_lightLinks->setsDirtied();
			}
		}

		m_dirtyGlobalComponents = NoGlobalComponent;

		// Update scene graphs

		for( int i = SceneGraph::FirstType; i <= SceneGraph::LastType; ++i )
		{
			SceneGraph *sceneGraph = m_sceneGraphs[i].get();
			if( i == SceneGraph::CameraType && ( m_changedGlobalComponents & CameraOptionsGlobalComponent ) )
			{
				// Because the globals are applied to camera objects, we must update the object whenever
				// the globals have changed, so we clear the scene graph and start again.
				/// \todo Can we do better here, by using m_changedGlobalComponents in `SceneGraph::update()`?
				sceneGraph->clear();
			}

			tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );
			SceneGraphUpdateTask *task = new( tbb::task::allocate_root( taskGroupContext ) ) SceneGraphUpdateTask(
				this, sceneGraph, (SceneGraph::Type)i, m_changedGlobalComponents, ThreadState::current(), ScenePlug::ScenePath(), callback, pathsToUpdate
			);
			tbb::task::spawn_root_and_wait( *task );

			if( i == SceneGraph::LightFilterType && m_lightLinks && m_lightLinks->lightFilterLinksDirty() )
			{
				m_lightLinks->outputLightFilterLinks( m_scene.get() );
			}
		}

		if( m_changedGlobalComponents & CameraOptionsGlobalComponent )
		{
			updateDefaultCamera();
		}

		if( !pathsToUpdate )
		{
			// Only clear `m_changedGlobalComponents` when we
			// know our entire scene has been updated successfully.
			m_changedGlobalComponents = NoGlobalComponent;
			m_updateRequired = false;
			if( m_failedAttributeEdits )
			{
				IECore::msg(
					IECore::Msg::Warning, "RenderController",
					boost::format( "%1% attribute edit%2% required geometry to be regenerated" )
						% m_failedAttributeEdits
						% ( m_failedAttributeEdits > 1 ? "s" : "" )
				);
				m_failedAttributeEdits = 0;
			}
			if( m_lightLinks )
			{
				m_lightLinks->clean();
			}
		}

		if( callback && signalCompletion )
		{
			callback( BackgroundTask::Completed );
		}
	}
	catch( const IECore::Cancelled &e )
	{
		if( callback )
		{
			callback( BackgroundTask::Cancelled );
		}
		throw;
	}
	catch( ... )
	{
		// No point updating again, since it'll just repeat
		// the same error.
		m_updateRequired = false;
		if( callback )
		{
			callback( BackgroundTask::Errored );
		}
		throw;
	}
}

void RenderController::updateDefaultCamera()
{
	if( m_renderer->name() == g_openGLRendererName || m_renderer->name() == g_compoundRendererName )
	{
		// Don't need a default camera for OpenGL, because in interactive mode
		// the renderer currently expects the camera to be provided externally.
		// Don't currently need one for compound renderers either, because then
		// SceneGadget provides a camera.
		return;
	}

	const StringData *cameraOption = m_globals->member<StringData>( g_cameraGlobalName );
	m_defaultCamera = nullptr;
	if( cameraOption && !cameraOption->readable().empty() )
	{
		return;
	}

	CameraPtr defaultCamera = new IECoreScene::Camera;
	SceneAlgo::applyCameraGlobals( defaultCamera.get(), m_globals.get(), m_scene.get() );
	IECoreScenePreview::Renderer::AttributesInterfacePtr defaultAttributes = m_renderer->attributes( m_scene->attributesPlug()->defaultValue() );
	ConstStringDataPtr name = new StringData( "gaffer:defaultCamera" );
	m_defaultCamera = m_renderer->camera( name->readable(), defaultCamera.get(), defaultAttributes.get() );
	m_renderer->option( "camera", name.get() );
}

void RenderController::cancelBackgroundTask()
{
	if( m_backgroundTask )
	{
		m_backgroundTask->cancelAndWait();
		m_backgroundTask.reset();
	}
}

std::optional<ScenePlug::ScenePath> RenderController::pathForID( uint32_t id ) const
{
	return m_idMap->pathForID( id );
}

IECore::PathMatcher RenderController::pathsForIDs( const std::vector<uint32_t> &ids ) const
{
	IECore::PathMatcher result;
	for( auto id : ids )
	{
		if( auto path = m_idMap->pathForID( id ) )
		{
			result.addPath( *path );
		}
	}
	return result;
}

uint32_t RenderController::idForPath( const ScenePlug::ScenePath &path ) const
{
	return m_idMap->idForPath( path );
}

std::vector<uint32_t> RenderController::idsForPaths( const IECore::PathMatcher &paths ) const
{
	std::vector<uint32_t> result;
	for( PathMatcher::Iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
	{
		if( auto id = idForPath( *it ) )
		{
			result.push_back( id );
		}
	}
	return result;
}
