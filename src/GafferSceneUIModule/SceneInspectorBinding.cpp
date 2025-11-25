//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "boost/python.hpp"

#include "SceneInspectorBinding.h"

#include "GafferSceneUI/Private/AttributeInspector.h"
#include "GafferSceneUI/Private/BasicInspector.h"
#include "GafferSceneUI/Private/InspectorColumn.h"
#include "GafferSceneUI/Private/OptionInspector.h"
#include "GafferSceneUI/Private/ParameterInspector.h"
#include "GafferSceneUI/Private/TransformInspector.h"
#include "GafferSceneUI/TypeIds.h"

#include "GafferBindings/PathBinding.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/Path.h"
#include "Gaffer/PathFilter.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/ExternalProcedural.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/Output.h"
#include "IECoreScene/Primitive.h"
#include "IECoreScene/ShaderNetwork.h"
#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/DataAlgo.h"
#include "IECore/TypeTraits.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/multi_index/key.hpp"
#include "boost/multi_index/ordered_index.hpp"
#include "boost/multi_index/sequenced_index.hpp"
#include "boost/multi_index_container.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"

#include <mutex>

using namespace std;
using namespace Imath;
using namespace boost;
using namespace boost::placeholders;
using namespace boost::python;
using namespace IECore;
using namespace IECoreScene;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;
using namespace GafferSceneUI;
using namespace GafferSceneUI::Private;

namespace
{

// InspectorPath
// =============
//
// The SceneInspector uses a PathListingWidget for display, because that deals
// with all the nasty details of implementing an asynchronous tree view for us.
// It also means we can reuse InspectorColumn and HistoryWindow, so that the
// SceneInspector presents all the same functionality as other SceneEditors. For
// this, we implement a Path subclass that navigates a tree of inspectors covering
// all aspects of the scene (both an individual location and also the globals).

const IECore::InternedString g_contextPropertyName( "inspector:context" );
const IECore::InternedString g_contextAPropertyName( "inspector:contextA" );
const IECore::InternedString g_contextBPropertyName( "inspector:contextB" );
const IECore::InternedString g_inspectorPropertyName( "inspector:inspector" );
const IECore::InternedString g_locationPathName( "Location" );
const IECore::InternedString g_globalsPathName( "Globals" );

// The Path class has turned out to be an awkward abstraction for anything which
// isn't backed by a statically accessible data source (like FileSystemPath is).
// Individual Path instances can't easily store the data relevant to their own
// path, because the path can be changed at any time via `setFromString()` or by
// direct modification of `names()`. And there isn't anywhere natural to store
// global data that could be used by all paths.
//
// For InspectorPath we are trying out a new factoring, whereby all state and
// logic is handled by a central Tree instance, and Path subclasses are merely
// used to index into that tree. If taken to its logical conclusion, this would
// mean that Path is no longer subclassable, and instead a single Path type can
// be used with any Tree type, by passing the tree to the Path constructor. Baby
// steps though - for now we are just trying the idea out via InspectorPath.
class InspectorTree : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( InspectorTree )

		/// Context for each side of an A/B diff.
		using Contexts = std::array<Gaffer::ConstContextPtr, 2>;

		InspectorTree( const ScenePlugPtr &scene, const Contexts &contexts, const Gaffer::PlugPtr &editScope )
			:	m_scene( scene ), m_editScope( editScope ), m_filter( "/..." ), m_isolateDifferences( false )
		{
			setContexts( contexts );
			scene->node()->plugDirtiedSignal().connect( boost::bind( &InspectorTree::plugDirtied, this, ::_1 ) );
		}

		void setContexts( const Contexts &contexts )
		{
			// We don't bother connecting to `Context::changedSignal()`, because we
			// are always used with immutable contexts sourced from a ContextTracker.
			bool dirty = false;
			{
				std::scoped_lock lock( m_mutex );

				for( size_t i = 0; i < m_contexts.size(); ++i )
				{
					if( !contexts[i] )
					{
						throw IECore::Exception( "Context must not be null" );
					}
					dirty |= !m_contexts[i] || *m_contexts[i] != *contexts[i];
				}

				m_contexts = contexts;
				if( dirty )
				{
					m_rootItem.reset();
				}
			}
			if( dirty )
			{
				// Emit signal after releasing lock, to avoid risk of deadlock
				// if connected slots call back into InspectorTree.
				m_dirtiedSignal();
			}
		}

		const Contexts &getContexts() const
		{
			return m_contexts;
		}

		// It's easier for InspectorTree to do its own filter than it
		// is to use a PathFilter, so that's what we do.
		void setFilter( const IECore::StringAlgo::MatchPattern &filter )
		{
			bool dirty = false;
			{
				std::scoped_lock lock( m_mutex );
				if( filter != m_filter )
				{
					m_filter = filter;
					dirty = true;
					m_rootItem.reset();
				}
			}
			if( dirty )
			{
				m_dirtiedSignal();
			}
		}

		const IECore::StringAlgo::MatchPattern &getFilter() const
		{
			return m_filter;
		}

		void setIsolateDifferences( bool isolateDifferences )
		{
			bool dirty = false;
			{
				std::scoped_lock lock( m_mutex );
				if( isolateDifferences != m_isolateDifferences )
				{
					m_isolateDifferences = isolateDifferences;
					dirty = true;
					m_rootItem.reset();
				}
			}
			if( dirty )
			{
				m_dirtiedSignal();
			}
		}

		using DirtiedSignal = Gaffer::Signals::Signal<void ()>;

		DirtiedSignal &dirtiedSignal()
		{
			return m_dirtiedSignal;
		}

		// Inspector Registry
		// ==================
		//
		// The tree of inspectors needs to vary according to the current scene
		// content, and be customisable to show data from custom extensions. We
		// use a registry of inspection providers to define the tree.

		// An inspector, and its position within the tree.
		struct Inspection
		{
			Inspection() = default;
			Inspection( const vector<InternedString> &path, const GafferSceneUI::Private::ConstInspectorPtr inspector )
				:	path( path ), inspector( inspector )
			{
			}
			vector<InternedString> path;
			GafferSceneUI::Private::ConstInspectorPtr inspector;
		};
		using Inspections = vector<Inspection>;

		// Function that generates inspections for a scene.
		using InspectionProvider = std::function<Inspections ( ScenePlug *scene, const Gaffer::PlugPtr &editScope  )>;

		// Registers an InspectionProvider, whose results will appear below
		// `path` in the tree.
		static void registerInspectors( const vector<InternedString> &path, const InspectionProvider &inspectionProvider )
		{
			inspectionProviders().push_back( { path, inspectionProvider } );
		}

		static void deregisterInspectors( const vector<InternedString> &path )
		{
			auto &providers = inspectionProviders();
			providers.erase(
				std::remove_if(
					providers.begin(),
					providers.end(),
					[&] ( const auto &item ) {
						return item.first == path;
					}
				),
				providers.end()
			);
		}

		// Convenience for making registrations using a static variable.
		struct Registration : boost::noncopyable
		{
			Registration( const vector<InternedString> &path, const InspectionProvider &inspectionProvider )
			{
				registerInspectors( path, inspectionProvider );
			}
		};

	protected :

		friend class InspectorPath;

		bool isValid( const Path::Names &path, const IECore::Canceller *canceller ) const
		{
			if( path.empty() )
			{
				return true;
			}

			if( path.size() == 1 )
			{
				return path[0] == g_locationPathName || path[0] == g_globalsPathName;
			}

			std::shared_ptr<const TreeItem> root = rootItem( canceller );
			return root->findDescendant( path );
		}

		bool isLeaf( const Path::Names &path, const IECore::Canceller *canceller ) const
		{
			// Any part of the path could get children, in theory.
			return false;
		}

		void propertyNames( const Path::Names &path, std::vector<IECore::InternedString> &propertyNames, const IECore::Canceller *canceller ) const
		{
			propertyNames.push_back( g_inspectorPropertyName );
			propertyNames.push_back( g_contextPropertyName );
			propertyNames.push_back( g_contextAPropertyName );
			propertyNames.push_back( g_contextBPropertyName );
		}

		IECore::ConstRunTimeTypedPtr property( const Path::Names &path, const IECore::InternedString &propertyName, const IECore::Canceller *canceller ) const
		{
			if( propertyName == g_inspectorPropertyName )
			{
				std::shared_ptr<const TreeItem> root = rootItem( canceller );
				const TreeItem *item = root->findDescendant( path );
				return item ? item->inspector : nullptr;
			}
			return nullptr;
		}

		Gaffer::ConstContextPtr contextProperty( const Path::Names &path, const IECore::InternedString &propertyName, const IECore::Canceller *canceller ) const
		{
			if( propertyName == g_contextPropertyName || propertyName == g_contextAPropertyName || propertyName == g_contextBPropertyName )
			{
				std::scoped_lock lock( m_mutex );
				const Context *context = m_contexts[propertyName==g_contextBPropertyName?1:0].get();
				if(
					path.size() && path[0] == g_locationPathName &&
					!context->getIfExists<ScenePlug::ScenePath>( ScenePlug::scenePathContextName )
				)
				{
					// Prevent inspection in an invalid context.
					return nullptr;
				}
				return context;
			}
			return nullptr;
		}

		vector<InternedString> childNames( const Path::Names &path, const IECore::Canceller *canceller ) const
		{
			std::shared_ptr<const TreeItem> root = rootItem( canceller );

			vector<InternedString> result;
			if( auto item = root->findDescendant( path ) )
			{
				auto &index = item->children.get<1>();
				for( const auto &child : index )
				{
					result.push_back( child.first );
				}
			}
			return result;
		}

		const Gaffer::Plug *cancellationSubject() const
		{
			return m_scene.get();
		}

	private :

		// A single entry in the tree, corresponding to a particular path.
		// May hold an Inspector and child items indexed by name.
		struct TreeItem
		{

			// Children are indexed two ways :
			//
			// - An ordered index, for fast lookup by name.
			// - A sequenced index, containing the order in which we want
			//   to report children from `childNames()`.
			using NamedChild = pair<InternedString, std::unique_ptr<TreeItem>>;
			using ChildMap = multi_index::multi_index_container<
				NamedChild,
				multi_index::indexed_by<
					multi_index::ordered_unique<
						multi_index::key<&NamedChild::first>
					>,
					multi_index::sequenced<>
				>
			>;

			GafferSceneUI::Private::ConstInspectorPtr inspector;
			ChildMap children;

			TreeItem *insertDescendant( const Path::Names &relativePath )
			{
				TreeItem *item = this;
				for( const auto name : relativePath )
				{
					auto [childIt, inserted] = item->children.insert( { name, nullptr } );
					if( inserted )
					{
						// Cast is necessary because `multi_index_container` only allows const access.
						// But it is safe because the thing we're modifying is not used by any of the
						// container indices.
						const_cast<unique_ptr<TreeItem>&>( childIt->second ) = std::make_unique<TreeItem>();
					}
					item = childIt->second.get();
				}
				return item;
			}

			const TreeItem *findDescendant( const Path::Names &relativePath ) const
			{
				const TreeItem *result = this;
				for( const auto name : relativePath )
				{
					auto childIt = result->children.find( name );
					if( childIt != result->children.end() )
					{
						result = childIt->second.get();
					}
					else
					{
						return nullptr;
					}
				}
				return result;
			}

		};

		void plugDirtied( const Plug *plug )
		{
			if( plug == m_scene.get() )
			{
				{
					std::scoped_lock lock( m_mutex );
					m_rootItem.reset();
				}
				m_dirtiedSignal();
			}
		}

		bool contextValidForPath( const Path::Names &path ) const
		{
			if( path.size() && path[0] == g_locationPathName )
			{
				if(
					!Context::current()->getIfExists<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ) ||
					!m_scene->existsPlug()->getValue()
				)
				{
					return false;
				}
			}
			else if( path.size() && path[0] == g_globalsPathName )
			{
				if( Context::current()->getIfExists<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ) )
				{
					return false;
				}
			}
			return true;
		}

		std::shared_ptr<const TreeItem> rootItem( const IECore::Canceller *canceller ) const
		{
			std::scoped_lock lock( m_mutex );
			if( m_rootItem )
			{
				// We're not dirty. We return a `shared_ptr` so that callees get
				// to maintain ownership over the root for as long as they use
				// it, without needing to hold the lock the whole time. This
				// makes queries thread-safe with respect to the root being reset
				// when the tree is dirtied on another thread, with a minimum of
				// contention between querying threads.
				return m_rootItem;
			}

			// We're dirty. Rebuild the tree from scratch. We build the entire
			// tree at once rather than build it lazily as queries come in,
			// because in practice the PathListingWidget will generate paths for
			// `/*/*` immediately (to determine whether it should draw the
			// triangle expansion indicator for the children of the root). And
			// that means we'll end up querying all properties of the location
			// being viewed anyway.
			//
			// Note : This is not as bad as it sounds, because the more
			// expensive calls to `TreeItem::inspector` _are_ deferred.

			auto newRootItem = std::make_shared<TreeItem>();
			const IECore::StringAlgo::MatchPatternPath filterPath = IECore::StringAlgo::matchPatternPath( m_filter );

			for( const auto &context : m_contexts )
			{
				if( &context == &m_contexts[1] && *context == *m_contexts[0] )
				{
					// Second context is identical to the first, so skip it.
					continue;
				}

				Context::EditableScope scope( context.get() );
				if( canceller )
				{
					scope.setCanceller( canceller );
				}

				for( const auto &[root, provider] : inspectionProviders() )
				{
					if( !contextValidForPath( root ) )
					{
						continue;
					}

					auto inspections = provider( m_scene.get(), m_editScope );
					if( !inspections.size() )
					{
						continue;
					}

					for( const auto &[subPath, inspector] : inspections )
					{
						vector<InternedString> fullPath = root;
						fullPath.insert( fullPath.end(), subPath.begin(), subPath.end() );

						if( !StringAlgo::match( fullPath, filterPath ) )
						{
							continue;
						}

						TreeItem *inspectorItem = newRootItem->insertDescendant( fullPath );
						inspectorItem->inspector = inspector;
					}
				}
			}

			if( m_isolateDifferences )
			{
				isolateDifferencesWalk( newRootItem.get(), Path::Names(), canceller );
			}

			m_rootItem = newRootItem;
			return m_rootItem;
		}

		// Removes children from `tree` as necessary, and returns
		// true if this item should be kept by its parent, false
		// otherwise.
		bool isolateDifferencesWalk( TreeItem *item, const Path::Names &path, const IECore::Canceller *canceller ) const
		{
			Path::Names childPath = path;
			childPath.resize( childPath.size() + 1 );
			for( auto it = item->children.begin(); it != item->children.end(); /* empty */ )
			{
				childPath.back() = it->first;
				if( !isolateDifferencesWalk( it->second.get(), childPath, canceller ) )
				{
					it = item->children.erase( it );
				}
				else
				{
					++it;
				}
			}

			if( !item->children.empty() )
			{
				return true;
			}

			if( !item->inspector )
			{
				return false;
			}

			std::array<ConstObjectPtr, 2> values;
			for( size_t i = 0; i < m_contexts.size(); ++i )
			{
				Context::EditableScope scope( m_contexts[i].get() );
				if( contextValidForPath( path ) )
				{
					scope.setCanceller( canceller );
					auto inspection = item->inspector->inspect();
					values[i] = inspection ? inspection->value() : nullptr;
				}
			}

			if( (bool)values[0] != (bool)values[1] )
			{
				return true;
			}
			else if( !values[0] )
			{
				return false;
			}

			return values[0]->isNotEqualTo( values[1].get() );
		}

		using InspectionProviders = vector<std::pair<vector<InternedString>, InspectionProvider>>;
		static InspectionProviders &inspectionProviders()
		{
			// Deliberately leaking, since this will contain Python callbacks
			// which cannot be destroyed during shutdown.
			static InspectionProviders *g_inspectionProviders = new InspectionProviders;
			return *g_inspectionProviders;
		}

		// Members which don't change after initialisation.
		const ScenePlugPtr m_scene;
		const Gaffer::PlugPtr m_editScope;
		DirtiedSignal m_dirtiedSignal;

		// Mutable members. Access to these must be protected by a lock on
		// `m_mutex.
		mutable std::mutex m_mutex;
		mutable std::shared_ptr<TreeItem> m_rootItem;
		Contexts m_contexts;
		IECore::StringAlgo::MatchPattern m_filter;
		bool m_isolateDifferences;

};

IE_CORE_DECLAREPTR( InspectorTree )

// Simply delegates all queries to an InspectorTree.
/// \todo Consider refactoring the Path base class so that it delegates
/// to an abstract tree, and then removing all Path subclasses.
class InspectorPath : public Gaffer::Path
{

	public :

		InspectorPath( const InspectorTreePtr &tree, const Names &names, const IECore::InternedString &root = "/", const Gaffer::PathFilterPtr &filter = nullptr )
			:	Path( names, root, filter ), m_tree( tree )
		{
		}

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( InspectorPath, GafferSceneUI::InspectorPathTypeId, Gaffer::Path );

		~InspectorPath() override
		{
		}

		InspectorTree *tree()
		{
			return m_tree.get();
		}

		bool isValid( const IECore::Canceller *canceller = nullptr ) const override
		{
			return m_tree->isValid( names(), canceller );
		}

		bool isLeaf( const IECore::Canceller *canceller ) const override
		{
			return m_tree->isLeaf( names(), canceller );
		}

		PathPtr copy() const override
		{
			return new InspectorPath( m_tree, names(), root(), const_cast<PathFilter *>( getFilter() ) );
		}

		void propertyNames( std::vector<IECore::InternedString> &names, const IECore::Canceller *canceller = nullptr ) const override
		{
			Path::propertyNames( names, canceller );
			m_tree->propertyNames( this->names(), names, canceller );
		}

		IECore::ConstRunTimeTypedPtr property( const IECore::InternedString &name, const IECore::Canceller *canceller = nullptr ) const override
		{
			auto p = m_tree->property( names(), name, canceller );
			return p ? p : Path::property( name, canceller );
		}

		Gaffer::ConstContextPtr contextProperty( const IECore::InternedString &name, const IECore::Canceller *canceller = nullptr ) const override
		{
			auto p = m_tree->contextProperty( names(), name, canceller );
			return p ? p : Path::contextProperty( name, canceller );
		}

		const Gaffer::Plug *cancellationSubject() const override
		{
			return m_tree->cancellationSubject();
		}

	protected :

		void doChildren( std::vector<PathPtr> &children, const IECore::Canceller *canceller ) const override
		{
			auto newNames = names();
			newNames.push_back( InternedString() );
			for( const auto &childName : m_tree->childNames( names(), canceller ) )
			{
				newNames.back() = childName;
				children.push_back(
					new InspectorPath( m_tree, newNames, root(), const_cast<PathFilter *>( getFilter() ) )
				);
			}
		}

		void pathChangedSignalCreated() override
		{
			Path::pathChangedSignalCreated();
			m_treeDirtiedConnection = m_tree->dirtiedSignal().connect( boost::bind( &InspectorPath::treeDirtied, this ) );
		}

	private :

		void treeDirtied()
		{
			emitPathChanged();
		}

		InspectorTreePtr m_tree;
		Gaffer::Signals::ScopedConnection m_treeDirtiedConnection;

};

IE_CORE_DEFINERUNTIMETYPED( InspectorPath );

// Transform inspectors
// ====================

InspectorTree::Inspections transformInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	InspectorTree::Inspections result;
	for( auto space : { TransformInspector::Space::Local, TransformInspector::Space::World } )
	{
		vector<InternedString> path = { TransformInspector::toString( space ), "" };
		using C = TransformInspector::Component;
		for( auto component : { C::Matrix, C::Translate, C::Rotate, C::Scale, C::Shear } )
		{
			path[1] = TransformInspector::toString( component );
			result.push_back( {
				path,
				new GafferSceneUI::Private::TransformInspector(
					scene, editScope, space, component
				)
			} );
		}
	}
	return result;
}

const InspectorTree::Registration g_transformInspectionRegistration( { "Location", "Transform" }, transformInspectionProvider );

// Bound inspectors
// ================

InspectorTree::Inspections boundInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	InspectorTree::Inspections result;
	result.push_back( {
		{ "Local" },
		new GafferSceneUI::Private::BasicInspector(
			scene->boundPlug(), editScope,
			[] ( const AtomicBox3fPlug *boundPlug ) {
				return new Box3fData( boundPlug->getValue() );
			}
		)
	} );
	result.push_back( {
		{ "World" },
		new GafferSceneUI::Private::BasicInspector(
			scene->boundPlug(), editScope,
			[] ( const AtomicBox3fPlug *boundPlug ) {
				const Imath::Box3f bound = Imath::transform(
					boundPlug->getValue(),
					// Calling `fullTransform()` is a bit naughty, because we're only
					// meant to be inspecting the `bound` plug. But we get away with
					// it because InspectorPath emits `changedSignal()` when any child
					// of the ScenePlug is dirtied.
					boundPlug->parent<ScenePlug>()->fullTransform( Context::current()->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ) )
				);
				return new Box3fData( bound );
			}
		)
	} );
	return result;
}

const InspectorTree::Registration g_boundInspectionRegistration( { "Location", "Bound" }, boundInspectionProvider );

// Attribute Inspectors
// ====================

template<typename T>
vector<InternedString> alphabeticallySortedKeys( const T &container )
{
	vector<InternedString> result;
	result.reserve( container.size() );
	for( const auto &[name, value] : container )
	{
		result.push_back( name );
	}
	std::sort(
		result.begin(), result.end(),
		[] ( InternedString a, InternedString b ) { return a.string() < b.string(); }
	);
	return result;
}

const InternedString g_other( "Other" );
const InternedString g_category( "category" );

void addShaderInspections( InspectorTree::Inspections &inspections, const vector<InternedString> &path, ScenePlug *scene, const Gaffer::PlugPtr &editScope, InternedString attributeName, const IECoreScene::ShaderNetwork *shaderNetwork )
{
	// Sort the shaders in the order you'd encounter them if you started
	// at the final output and worked backwards up the connections.
	vector<InternedString> orderedShaderHandles;
	IECoreScene::ShaderNetworkAlgo::depthFirstTraverse(
		shaderNetwork,
		[&] ( const ShaderNetwork *network, InternedString shaderHandle ) {
			orderedShaderHandles.push_back( shaderHandle );
		}
	);
	std::reverse( orderedShaderHandles.begin(), orderedShaderHandles.end() );

	// Add inspections for each shader and all of its parameters.

	for( const auto shaderHandle : orderedShaderHandles )
	{
		vector<InternedString> shaderPath = path;
		StringAlgo::tokenize( shaderHandle, '/', shaderPath );

		const Shader *shader = shaderNetwork->getShader( shaderHandle );

		inspections.push_back( {

			shaderPath,
			new GafferSceneUI::Private::BasicInspector(
				scene->attributesPlug(), editScope,
				[attributeName, shaderHandle] ( const CompoundObjectPlug *attributesPlug ) -> ConstShaderPtr {
					ConstCompoundObjectPtr attributes = attributesPlug->parent<ScenePlug>()->fullAttributes(
						Context::current()->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName )
					);
					auto shaderNetwork = attributes->member<ShaderNetwork>( attributeName );
					if( !shaderNetwork )
					{
						return nullptr;
					}
					return shaderNetwork->getShader( shaderHandle );
				}
			)

		} );

		vector<InternedString> parameterPath = shaderPath;
		parameterPath.push_back( InternedString() );
		for( const auto parameterName : alphabeticallySortedKeys( shader->parameters() ) )
		{
			parameterPath.back() = parameterName;
			inspections.push_back( {
				parameterPath,
				new GafferSceneUI::Private::ParameterInspector(
					scene, editScope, attributeName, { shaderHandle, parameterName }, /* inheritAttributes = */ true
				)
			} );
		}
	}
}

InspectorTree::Inspections attributeInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	ConstCompoundObjectPtr attributes = scene->fullAttributes( Context::current()->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ) );
	const vector<InternedString> sortedAttributeNames = alphabeticallySortedKeys( attributes->members() );

	InspectorTree::Inspections result;
	for( auto name : sortedAttributeNames )
	{
		InternedString category = g_other;
		if( auto categoryMetadata = Metadata::value<StringData>( fmt::format( "attribute:{}", name.c_str() ), g_category ) )
		{
			category = categoryMetadata->readable();
		}
		result.push_back( { { category, name }, new GafferSceneUI::Private::AttributeInspector( scene, editScope, name ) } );
		if( auto shaderNetwork = attributes->member<const ShaderNetwork>( name ) )
		{
			addShaderInspections( result, { category, name }, scene, editScope, name, shaderNetwork );
		}
	}
	return result;
}

const InspectorTree::Registration g_attributeInspectionRegistration( { "Location", "Attributes" }, attributeInspectionProvider );

// Object Inspectors
// =================

InspectorTree::Inspections objectTypeInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	InspectorTree::Inspections result;
	ConstObjectPtr object = scene->objectPlug()->getValue();
	if( object->typeId() != NullObjectTypeId )
	{
		result.push_back( {
			{ "Type" },
			new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[] ( const ObjectPlug *objectPlug ) -> ConstStringDataPtr {
					ConstObjectPtr object = objectPlug->getValue();
					if( object->typeId() == NullObjectTypeId )
					{
						return nullptr;
					}
					return new StringData( object->typeName() );
				}
			)
		} );
	}

	return result;
}

const InspectorTree::Registration g_objectTypeInspectionRegistration( { "Location", "Object" }, objectTypeInspectionProvider );

const vector<pair<PrimitiveVariable::Interpolation, const char *>> g_primitiveVariableInterpolations = {
	{ PrimitiveVariable::Constant, "Constant" },
	{ PrimitiveVariable::Uniform, "Uniform" },
	{ PrimitiveVariable::Vertex, "Vertex" },
	{ PrimitiveVariable::Varying, "Varying" },
	{ PrimitiveVariable::FaceVarying, "FaceVarying" }
};

InspectorTree::Inspections primitiveTopologyInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	InspectorTree::Inspections result;

	ConstObjectPtr object = scene->objectPlug()->getValue();
	if( runTimeCast<const Primitive>( object.get() ) )
	{
		for( const auto &[interpolation, interpolationName] : g_primitiveVariableInterpolations )
		{
			result.push_back( {
				{ interpolationName },
				new GafferSceneUI::Private::BasicInspector(
					scene->objectPlug(), editScope,
					[ interpolation = interpolation ] ( const ObjectPlug *objectPlug ) -> ConstDataPtr {
						ConstObjectPtr object = objectPlug->getValue();
						if( auto primitive = runTimeCast<const Primitive>( object.get() ) )
						{
							return new IntData( primitive->variableSize( interpolation ) );
						}
						return nullptr;
					}
				)
			} );
		}
	}
	return result;
}

const InspectorTree::Registration g_primitiveTopologyInspectionRegistration( { "Location", "Object", "Topology" }, primitiveTopologyInspectionProvider );

InspectorTree::Inspections meshTopologyInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	InspectorTree::Inspections result;

	ConstObjectPtr object = scene->objectPlug()->getValue();
	if( runTimeCast<const MeshPrimitive>( object.get() ) )
	{
		result.push_back( {
			{ "Vertices" },
			new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[] ( const ObjectPlug *objectPlug ) -> ConstDataPtr {
					if( auto mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() ) )
					{
						return new IntData( mesh->variableSize( PrimitiveVariable::Vertex ) );
					}
					return nullptr;
				}
			)
		} );
		result.push_back( {
			{ "Faces" },
			new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[] ( const ObjectPlug *objectPlug ) -> ConstDataPtr {
					if( auto mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() ) )
					{
						return new IntData( mesh->numFaces() );
					}
					return nullptr;
				}
			)
		} );
		result.push_back( {
			{ "Vertices Per Face" },
			new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[] ( const ObjectPlug *objectPlug ) -> ConstDataPtr {
					if( auto mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() ) )
					{
						return mesh->verticesPerFace();
					}
					return nullptr;
				}
			)
		} );
		result.push_back( {
			{ "Vertex Ids" },
			new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[] ( const ObjectPlug *objectPlug ) -> ConstDataPtr {
					if( auto mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() ) )
					{
						return mesh->vertexIds();
					}
					return nullptr;
				}
			)
		} );
	}
	return result;
}

const InspectorTree::Registration g_meshTopologyInspectionRegistration( { "Location", "Object", "Mesh Topology" }, meshTopologyInspectionProvider );

InspectorTree::Inspections curvesTopologyInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	InspectorTree::Inspections result;

	ConstObjectPtr object = scene->objectPlug()->getValue();
	if( runTimeCast<const CurvesPrimitive>( object.get() ) )
	{
		result.push_back( {
			{ "Vertices" },
			new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[] ( const ObjectPlug *objectPlug ) -> ConstDataPtr {
					if( auto curves = runTimeCast<const CurvesPrimitive>( objectPlug->getValue() ) )
					{
						return new IntData( curves->variableSize( PrimitiveVariable::Vertex ) );
					}
					return nullptr;
				}
			)
		} );
		result.push_back( {
			{ "Curves" },
			new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[] ( const ObjectPlug *objectPlug ) -> ConstDataPtr {
					if( auto curves = runTimeCast<const CurvesPrimitive>( objectPlug->getValue() ) )
					{
						return new IntData( curves->numCurves() );
					}
					return nullptr;
				}
			)
		} );
		result.push_back( {
			{ "Vertices Per Curve" },
			new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[] ( const ObjectPlug *objectPlug ) -> ConstDataPtr {
					if( auto curves = runTimeCast<const CurvesPrimitive>( objectPlug->getValue() ) )
					{
						return curves->verticesPerCurve();
					}
					return nullptr;
				}
			)
		} );
		result.push_back( {
			{ "Periodic" },
			new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[] ( const ObjectPlug *objectPlug ) -> ConstDataPtr {
					if( auto curves = runTimeCast<const CurvesPrimitive>( objectPlug->getValue() ) )
					{
						return new BoolData( curves->periodic() );
					}
					return nullptr;
				}
			)
		} );
		result.push_back( {
			{ "Basis" },
				new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[] ( const ObjectPlug *objectPlug ) -> ConstDataPtr {
					if( auto curves = runTimeCast<const CurvesPrimitive>( objectPlug->getValue() ) )
					{
						switch( curves->basis().standardBasis() )
						{
							case StandardCubicBasis::Linear : return new StringData( "Linear" );
							case StandardCubicBasis::Bezier : return new StringData( "Bezier" );
							case StandardCubicBasis::BSpline : return new StringData( "BSpline" );
							case StandardCubicBasis::CatmullRom : return new StringData( "CatmullRom" );
							case StandardCubicBasis::Constant : return new StringData( "Constant" );
							default : return nullptr;
						}
					}
					return nullptr;
				}
			)
		} );
	}

	return result;
}

const InspectorTree::Registration g_curvesTopologyInspectionRegistration( { "Location", "Object", "Curves Topology" }, curvesTopologyInspectionProvider );

const CompoundData *objectParameters( const Object *object )
{
	if( auto camera = runTimeCast<const Camera>( object ) )
	{
		return camera->parametersData();
	}
	else if( auto externalProcedural = runTimeCast<const ExternalProcedural>( object ) )
	{
		return externalProcedural->parameters();
	}
	return nullptr;
}

InspectorTree::Inspections objectParametersInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	InspectorTree::Inspections result;

	ConstObjectPtr object = scene->objectPlug()->getValue();
	if( auto parameters = objectParameters( object.get() ) )
	{
		for( const auto name : alphabeticallySortedKeys( parameters->readable() ) )
		{
			result.push_back( {
				{ name },
				new GafferSceneUI::Private::BasicInspector(
					scene->objectPlug(), editScope,
					[ name = name ] ( const ObjectPlug *objectPlug ) -> ConstDataPtr {
						ConstObjectPtr object = objectPlug->getValue();
						if( auto parameters = objectParameters( object.get() ) )
						{
							return parameters->member( name );
						}
						return nullptr;
					}
				)
			} );
		}
	}
	return result;
}

const InspectorTree::Registration g_objectParametersInspectionRegistration( { "Location", "Object", "Parameters" }, objectParametersInspectionProvider );

ConstStringDataPtr g_invalidStringData = new StringData( "Invalid" );
ConstStringDataPtr g_constantStringData = new StringData( "Constant" );
ConstStringDataPtr g_uniformStringData = new StringData( "Uniform" );
ConstStringDataPtr g_vertexStringData = new StringData( "Vertex" );
ConstStringDataPtr g_varyingStringData = new StringData( "Varying" );
ConstStringDataPtr g_faceVaryingStringData = new StringData( "FaceVarying" );

const PrimitiveVariable *primitiveVariable( const Object *object, const std::string &name )
{
	auto primitive = runTimeCast<const Primitive>( object );
	if( !primitive )
	{
		return nullptr;
	}

	auto it = primitive->variables.find( name );
	return it != primitive->variables.end() ? &it->second : nullptr;
}

ConstStringDataPtr primitiveVariableInterpolation( const std::string &name, const ObjectPlug *objectPlug )
{
	ConstObjectPtr object = objectPlug->getValue();
	auto variable = primitiveVariable( object.get(), name );
	if( !variable )
	{
		return nullptr;
	}

	switch( variable->interpolation )
	{
		case PrimitiveVariable::Invalid : return g_invalidStringData;
		case PrimitiveVariable::Constant : return g_constantStringData;
		case PrimitiveVariable::Uniform : return g_uniformStringData;
		case PrimitiveVariable::Vertex : return g_vertexStringData;
		case PrimitiveVariable::Varying : return g_varyingStringData;
		case PrimitiveVariable::FaceVarying : return g_faceVaryingStringData;
		default : return nullptr;
	}
}

ConstStringDataPtr primitiveVariableType( const std::string &name, const ObjectPlug *objectPlug )
{
	ConstObjectPtr object = objectPlug->getValue();
	auto variable = primitiveVariable( object.get(), name );
	if( !variable || !variable->data )
	{
		return nullptr;
	}

	return new StringData( variable->data->typeName() );
}

const boost::container::flat_map<IECore::GeometricData::Interpretation, IECore::ConstStringDataPtr> g_geometricInterpretations = {
	{ GeometricData::None, new IECore::StringData( "None" ) },
	{ GeometricData::Point, new IECore::StringData( "Point" ) },
	{ GeometricData::Normal, new IECore::StringData( "Normal" ) },
	{ GeometricData::Vector, new IECore::StringData( "Vector" ) },
	{ GeometricData::Color, new IECore::StringData( "Color" ) },
	{ GeometricData::UV, new IECore::StringData( "UV" ) },
	{ GeometricData::Rational, new IECore::StringData( "Rational" ) }
};

ConstStringDataPtr primitiveVariableInterpretation( const std::string &name, const ObjectPlug *objectPlug )
{
	ConstObjectPtr object = objectPlug->getValue();
	auto variable = primitiveVariable( object.get(), name );
	if( !variable || !variable->data )
	{
		return nullptr;
	}

	auto it = g_geometricInterpretations.find( IECore::getGeometricInterpretation( variable->data.get() ) );
	return it != g_geometricInterpretations.end() ? it->second : nullptr;
}

ConstDataPtr primitiveVariableData( const std::string &name, const ObjectPlug *objectPlug )
{
	ConstObjectPtr object = objectPlug->getValue();
	auto variable = primitiveVariable( object.get(), name );
	if( !variable )
	{
		return nullptr;
	}

	return variable->data;
}

ConstDataPtr primitiveVariableIndices( const std::string &name, const ObjectPlug *objectPlug )
{
	ConstObjectPtr object = objectPlug->getValue();
	auto variable = primitiveVariable( object.get(), name );
	if( !variable )
	{
		return nullptr;
	}

	return variable->indices;
}

InspectorTree::Inspections primitiveVariablesInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	InspectorTree::Inspections result;

	ConstObjectPtr object = scene->objectPlug()->getValue();
	auto primitive = runTimeCast<const Primitive>( object.get() );
	if( !primitive )
	{
		return result;
	}

	for( const auto name : alphabeticallySortedKeys( primitive->variables ) )
	{
		result.push_back( {
			{ name, "Interpolation" },
			new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[ name = name ] ( const ObjectPlug *objectPlug ) {
					return primitiveVariableInterpolation( name, objectPlug );
				}
			)
		} );
		result.push_back( {
			{ name, "Type" },
			new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[ name = name ] ( const ObjectPlug *objectPlug ) {
					return primitiveVariableType( name, objectPlug );
				}
			)
		} );

		const Data *data = primitive->variables.find( name )->second.data.get();
		if( data && IECore::trait<IECore::TypeTraits::IsGeometricTypedData>( data ) )
		{
			result.push_back( {
				{ name, "Interpretation" },
				new GafferSceneUI::Private::BasicInspector(
					scene->objectPlug(), editScope,
					[ name = name ] ( const ObjectPlug *objectPlug ) {
						return primitiveVariableInterpretation( name, objectPlug );
					}
				)
			} );
		}

		result.push_back( {
			{ name, "Data" },
			new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[ name = name ] ( const ObjectPlug *objectPlug ) {
					return primitiveVariableData( name, objectPlug );
				}
			)
		} );
		result.push_back( {
			{ name, "Indices" },
			new GafferSceneUI::Private::BasicInspector(
				scene->objectPlug(), editScope,
				[ name = name ] ( const ObjectPlug *objectPlug ) {
					return primitiveVariableIndices( name, objectPlug );
				}
			)
		} );
	}

	return result;
}

const InspectorTree::Registration g_primitiveVariablesInspectionRegistration( { "Location", "Object", "Primitive Variables" }, primitiveVariablesInspectionProvider );

InspectorTree::Inspections subdivisionInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	InspectorTree::Inspections result;

	ConstObjectPtr object = scene->objectPlug()->getValue();
	auto mesh = runTimeCast<const MeshPrimitive>( object.get() );
	if( !mesh )
	{
		return result;
	}

	result.push_back( {
		{ "Interpolation" },
		new GafferSceneUI::Private::BasicInspector(
			scene->objectPlug(), editScope,
			[] ( const ObjectPlug *objectPlug ) {
				ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() );
				return mesh ? new StringData( mesh->interpolation() ) : nullptr;
			}
		)
	} );

	result.push_back( {
		{ "Corners" },
		new GafferSceneUI::Private::BasicInspector(
			scene->objectPlug(), editScope,
			[] ( const ObjectPlug *objectPlug ) {
				ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() );
				return mesh ? new UInt64Data( mesh->cornerIds()->readable().size() ) : nullptr;
			}
		)
	} );

	result.push_back( {
		{ "Corners", "Indices" },
		new GafferSceneUI::Private::BasicInspector(
			scene->objectPlug(), editScope,
			[] ( const ObjectPlug *objectPlug ) {
				ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() );
				return mesh ? mesh->cornerIds() : nullptr;
			}
		)
	} );

	result.push_back( {
		{ "Corners", "Sharpnesses" },
		new GafferSceneUI::Private::BasicInspector(
			scene->objectPlug(), editScope,
			[] ( const ObjectPlug *objectPlug ) {
				ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() );
				return mesh ? mesh->cornerSharpnesses() : nullptr;
			}
		)
	} );

	result.push_back( {
		{ "Creases" },
		new GafferSceneUI::Private::BasicInspector(
			scene->objectPlug(), editScope,
			[] ( const ObjectPlug *objectPlug ) {
				ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() );
				return mesh ? new UInt64Data( mesh->creaseLengths()->readable().size() ) : nullptr;
			}
		)
	} );

	result.push_back( {
		{ "Creases", "Lengths" },
		new GafferSceneUI::Private::BasicInspector(
			scene->objectPlug(), editScope,
			[] ( const ObjectPlug *objectPlug ) {
				ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() );
				return mesh ? mesh->creaseLengths() : nullptr;
			}
		)
	} );

	result.push_back( {
		{ "Creases", "Ids" },
		new GafferSceneUI::Private::BasicInspector(
			scene->objectPlug(), editScope,
			[] ( const ObjectPlug *objectPlug ) {
				ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() );
				return mesh ? mesh->creaseIds() : nullptr;
			}
		)
	} );

	result.push_back( {
		{ "Creases", "Sharpnesses" },
		new GafferSceneUI::Private::BasicInspector(
			scene->objectPlug(), editScope,
			[] ( const ObjectPlug *objectPlug ) {
				ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() );
				return mesh ? mesh->creaseSharpnesses() : nullptr;
			}
		)
	} );

	result.push_back( {
		{ "Interpolate Boundary" },
		new GafferSceneUI::Private::BasicInspector(
			scene->objectPlug(), editScope,
			[] ( const ObjectPlug *objectPlug ) {
				ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() );
				return mesh ? new StringData( mesh->getInterpolateBoundary() ) : nullptr;
			}
		)
	} );

	result.push_back( {
		{ "FaceVarying Linear Interpolation" },
		new GafferSceneUI::Private::BasicInspector(
			scene->objectPlug(), editScope,
			[] ( const ObjectPlug *objectPlug ) {
				ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() );
				return mesh ? new StringData( mesh->getFaceVaryingLinearInterpolation() ) : nullptr;
			}
		)
	} );

	result.push_back( {
		{ "Triangle Subdivision Rule" },
		new GafferSceneUI::Private::BasicInspector(
			scene->objectPlug(), editScope,
			[] ( const ObjectPlug *objectPlug ) {
				ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( objectPlug->getValue() );
				return mesh ? new StringData( mesh->getTriangleSubdivisionRule() ) : nullptr;
			}
		)
	} );
	return result;
}

const InspectorTree::Registration g_subdivisionInspectionRegistration( { "Location", "Object", "Subdivision" }, subdivisionInspectionProvider );

// Option Inspectors
// =================

const std::string g_optionPrefix( "option:" );
const std::string g_attributePrefix( "attribute:" );

InspectorTree::Inspections optionsInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	InspectorTree::Inspections result;
	ConstCompoundObjectPtr globals = scene->globalsPlug()->getValue();
	for( const auto name : alphabeticallySortedKeys( globals->members() ) )
	{
		if( !boost::starts_with( name.string(), g_optionPrefix ) )
		{
			continue;
		}

		string optionName = name.string().substr( g_optionPrefix.size() );
		InternedString category = g_other;
		if( auto categoryMetadata = Metadata::value<StringData>( name, g_category ) )
		{
			category = categoryMetadata->readable();
		}

		result.push_back( {
			{ category, optionName },
			new GafferSceneUI::Private::OptionInspector( scene, editScope, optionName )
		} );
	}
	return result;
}

const InspectorTree::Registration g_optionsInspectionRegistration( { "Globals", "Options" }, optionsInspectionProvider );

// Global Attribute Inspectors
// ============================

InspectorTree::Inspections globalAttributesInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	InspectorTree::Inspections result;
	ConstCompoundObjectPtr globals = scene->globalsPlug()->getValue();
	for( const auto &[name, value] : globals->members() )
	{
		if( !boost::starts_with( name.string(), g_attributePrefix ) )
		{
			continue;
		}

		string attributeName = name.string().substr( g_attributePrefix.size() );
		InternedString category = g_other;
		if( auto categoryMetadata = Metadata::value<StringData>( name, g_category ) )
		{
			category = categoryMetadata->readable();
		}

		result.push_back( {
			{ category, attributeName },
			new GafferSceneUI::Private::BasicInspector(
				scene->globalsPlug(), editScope,
				[ name = name ] ( const CompoundObjectPlug *globalsPlug ) {
					ConstCompoundObjectPtr globals = globalsPlug->getValue();
					return globals->member( name );
				}
			)
		} );
	}
	return result;
}

const InspectorTree::Registration g_globalAttributesInspectionRegistration( { "Globals", "Attributes" }, globalAttributesInspectionProvider );

// Output Inspectors
// =================

const std::string g_outputPrefix( "output:" );

InspectorTree::Inspections outputsInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	InspectorTree::Inspections result;
	ConstCompoundObjectPtr globals = scene->globalsPlug()->getValue();
	for( const auto name : alphabeticallySortedKeys( globals->members() ) )
	{
		if( !boost::starts_with( name.string(), g_outputPrefix ) )
		{
			continue;
		}

		auto output = globals->member<Output>( name );
		if( !output )
		{
			continue;
		}

		vector<InternedString> path = ScenePlug::stringToPath( name.string().substr( g_outputPrefix.size( ) ) );
		path.push_back( "File Name" );
		result.push_back( {
			path,
			new GafferSceneUI::Private::BasicInspector(
				scene->globalsPlug(), editScope,
				[ name = name ] ( const CompoundObjectPlug *globalsPlug ) {
					ConstOutputPtr output = globalsPlug->getValue()->member<Output>( name );
					return output ? new StringData( output->getName() ) : nullptr;
				}
			)
		} );

		path.back() = "Type";
		result.push_back( {
			path,
			new GafferSceneUI::Private::BasicInspector(
				scene->globalsPlug(), editScope,
				[ name = name ] ( const CompoundObjectPlug *globalsPlug ) {
					ConstOutputPtr output = globalsPlug->getValue()->member<Output>( name );
					return output ? new StringData( output->getType() ) : nullptr;
				}
			)
		} );

		path.back() = "Data";
		result.push_back( {
			path,
			new GafferSceneUI::Private::BasicInspector(
				scene->globalsPlug(), editScope,
				[ name = name ] ( const CompoundObjectPlug *globalsPlug ) {
					ConstOutputPtr output = globalsPlug->getValue()->member<Output>( name );
					return output ? new StringData( output->getData() ) : nullptr;
				}
			)
		} );

		path.back() = "Parameters"; path.resize( path.size() + 1 );
		for( const auto parameterName : alphabeticallySortedKeys( output->parameters() ) )
		{
			path.back() = parameterName;
			result.push_back( {
				path,
				new GafferSceneUI::Private::BasicInspector(
					scene->globalsPlug(), editScope,
					[ name = name, parameterName = parameterName ] ( const CompoundObjectPlug *globalsPlug ) {
						ConstOutputPtr output = globalsPlug->getValue()->member<Output>( name );
						return output ? output->parametersData()->member( parameterName ) : nullptr;
					}
				)
			} );
		}
	}
	return result;
}

const InspectorTree::Registration g_outputsInspectionRegistration( { "Globals", "Outputs" }, outputsInspectionProvider );

// InspectorDiffColumn
// ===================

const std::array<ConstStringDataPtr, 2> g_diffColumnHeaders = {
	new StringData( "A" ),
	new StringData( "B" )
};

const std::array<ConstColor4fDataPtr, 2> g_diffColumnBackgroundColors = {
	new Color4fData( Color4f( 0.7, 0.12, 0, 0.3 ) ),
	new Color4fData( Color4f( 0.13, 0.62, 0, 0.3 ) )
};

const std::array<InternedString, 2> g_diffColumnContextProperties = { "inspector:contextA", "inspector:contextB" };

class InspectorDiffColumn : public GafferSceneUI::Private::InspectorColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( InspectorDiffColumn )

		enum class DiffContext { A, B };

		InspectorDiffColumn( DiffContext diffContext )
			:	InspectorColumn(
					"inspector:inspector",
					CellData( g_diffColumnHeaders[(int)diffContext] ),
					g_diffColumnContextProperties[(int)diffContext],
					SizeMode::Stretch
				),
				m_backgroundColor( g_diffColumnBackgroundColors[(int)diffContext] )
		{
			const DiffContext otherContext = diffContext == DiffContext::A ? DiffContext::B : DiffContext::A;
			m_otherColumn = new InspectorColumn( "inspector:inspector", CellData( g_diffColumnHeaders[(int)diffContext] ), g_diffColumnContextProperties[(int)otherContext] );
		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			GafferSceneUI::Private::Inspector::ResultPtr inspectionA = inspect( path, canceller );
			GafferSceneUI::Private::Inspector::ResultPtr inspectionB = m_otherColumn->inspect( path, canceller );

			CellData result = InspectorColumn::cellDataFromInspection( inspectionA.get() );

			const Object *valueA = inspectionA ? inspectionA->value() : nullptr;
			const Object *valueB = inspectionB ? inspectionB->value() : nullptr;

			bool different = false;
			if( (bool)valueA != (bool)valueB )
			{
				different = true;
			}
			else if( valueA )
			{
				different = valueA->isNotEqualTo( valueB );
			}

			result.background = different ? m_backgroundColor : nullptr;

			return result;
		}

	private :

		GafferSceneUI::Private::ConstInspectorColumnPtr m_otherColumn;
		ConstColor4fDataPtr m_backgroundColor;

};

// Bindings
// ========

InspectorTree::Contexts contextsFromPython( object pythonContexts )
{
	InspectorTree::Contexts result;
	for( size_t i = 0; i < result.size(); ++i )
	{
		result[i] = extract<ContextPtr>( pythonContexts[i] )();
	}
	return result;
}

InspectorTree::Ptr inspectorTreeConstructor( ScenePlug &scene, object pythonContexts, const Gaffer::PlugPtr &editScope )
{
	return new InspectorTree( &scene, contextsFromPython( pythonContexts ), editScope );
}

void inspectorTreeSetContextsWrapper( InspectorTree &tree, object pythonContexts )
{
	InspectorTree::Contexts contexts = contextsFromPython( pythonContexts );
	IECorePython::ScopedGILRelease gilRelease;
	tree.setContexts( contexts );
}

boost::python::tuple inspectorTreeGetContextsWrapper( InspectorTree &tree )
{
	auto c = tree.getContexts();
	return boost::python::make_tuple( boost::const_pointer_cast<Context>( c[0] ), boost::const_pointer_cast<Context>( c[1] ) );
}

void inspectorTreeSetFilterWrapper( InspectorTree &tree, const IECore::StringAlgo::MatchPattern &filter )
{
	IECorePython::ScopedGILRelease gilRelease;
	tree.setFilter( filter );
}

void inspectorTreeSetIsolateDifferencesWrapper( InspectorTree &tree, bool isolateDifferences )
{
	IECorePython::ScopedGILRelease gilRelease;
	tree.setIsolateDifferences( isolateDifferences );
}

void inspectorTreeRegisterInspectorsWrapper( const vector<InternedString> &path, object pythonInspectionProvider )
{
	InspectorTree::InspectionProvider inspectionProvider = [pythonInspectionProvider] ( ScenePlug *scene, const Gaffer::PlugPtr &editScope ) {
		InspectorTree::Inspections result;
		IECorePython::ScopedGILLock gilLock;
		try
		{
			object pythonInspections = pythonInspectionProvider( ScenePlugPtr( scene ), editScope );
			boost::python::container_utils::extend_container( result, pythonInspections );
		}
		catch( const error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
		return result;
	};
	InspectorTree::registerInspectors( path, inspectionProvider );
}

} // namespace

void GafferSceneUIModule::bindSceneInspector()
{

	object module( borrowed( PyImport_AddModule( "GafferSceneUI._SceneInspector" ) ) );
	scope().attr( "_SceneInspector" ) = module;
	scope moduleScope( module );

	{
		scope s = IECorePython::RefCountedClass<InspectorTree, RefCounted>( "InspectorTree" )
			.def(
				"__init__",
				make_constructor(
					inspectorTreeConstructor,
					default_call_policies(),
					(
						boost::python::arg( "scene" ),
						boost::python::arg( "contexts" ),
						boost::python::arg( "editScope" )
					)
				)
			)
			.def( "setContexts", &inspectorTreeSetContextsWrapper )
			.def( "getContexts", &inspectorTreeGetContextsWrapper )
			.def( "setFilter", &inspectorTreeSetFilterWrapper )
			.def( "getFilter", &InspectorTree::getFilter, return_value_policy<copy_const_reference>() )
			.def( "setIsolateDifferences", &inspectorTreeSetIsolateDifferencesWrapper )
			.def( "dirtiedSignal", &InspectorTree::dirtiedSignal, return_internal_reference<1>() )
			.def( "registerInspectors", &inspectorTreeRegisterInspectorsWrapper ).staticmethod( "registerInspectors" )
			.def( "deregisterInspectors",  &InspectorTree::deregisterInspectors ).staticmethod( "deregisterInspectors" )
		;

		class_<InspectorTree::Inspection>( "Inspection" )
			.def( init<const vector<InternedString> &, GafferSceneUI::Private::ConstInspectorPtr>() )
			.def_readwrite( "path", &InspectorTree::Inspection::path )
			.def_readwrite( "inspector", &InspectorTree::Inspection::inspector )
		;
	}

	PathClass<InspectorPath>()

		.def(
			init<InspectorTreePtr, const Path::Names &, const std::string &, const Gaffer::PathFilterPtr &>(
				(
					boost::python::arg( "tree" ),
					boost::python::arg( "names" ) = boost::python::list(),
					boost::python::arg( "root" ) = "/",
					boost::python::arg( "filter" ) = object()
				)
			)
		)
		.def( "tree", &InspectorPath::tree, return_value_policy<CastToIntrusivePtr>() )
	;

	{
		scope s = RefCountedClass<InspectorDiffColumn, GafferSceneUI::Private::InspectorColumn>( "InspectorDiffColumn" )
			.def( init<InspectorDiffColumn::DiffContext>() )
		;

		enum_<InspectorDiffColumn::DiffContext>( "DiffContext" )
			.value( "A", InspectorDiffColumn::DiffContext::A )
			.value( "B", InspectorDiffColumn::DiffContext::B )
		;
	}

}
