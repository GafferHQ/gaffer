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
#include "GafferSceneUI/TypeIds.h"

#include "GafferBindings/PathBinding.h"

#include "Gaffer/Context.h"
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

#include "Imath/ImathMatrixAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/multi_index/member.hpp"
#include "boost/multi_index/ordered_index.hpp"
#include "boost/multi_index/sequenced_index.hpp"
#include "boost/multi_index_container.hpp"

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
			:	m_scene( scene ), m_editScope( editScope )
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
						multi_index::member<NamedChild, InternedString, &NamedChild::first>
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

			m_rootItem = std::make_shared<TreeItem>();

			for( const auto &context : m_contexts )
			{
				Context::EditableScope scope( context.get() );
				if( canceller )
				{
					scope.setCanceller( canceller );
				}

				for( const auto &[root, provider] : inspectionProviders() )
				{
					if( root[0] == g_locationPathName )
					{
						if(
							!context->getIfExists<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ) ||
							!m_scene->existsPlug()->getValue()
						)
						{
							continue;
						}
					}
					else if( root[0] == g_globalsPathName )
					{
						if( context->getIfExists<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ) )
						{
							continue;
						}
					}

					auto inspections = provider( m_scene.get(), m_editScope );
					if( !inspections.size() )
					{
						continue;
					}

					TreeItem *inspectorRootItem = m_rootItem->insertDescendant( root );
					for( const auto &[subPath, inspector] : inspections )
					{
						TreeItem *inspectorItem = inspectorRootItem->insertDescendant( subPath );
						inspectorItem->inspector = inspector;
					}
				}
			}

			return m_rootItem;
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

const boost::container::flat_map<string, InternedString> g_attributeCategories = {
	{ "ai:*", "Arnold" },
	{ "dl:*", "3Delight" },
	{ "cycles:*", "Cycles" },
	{ "ri:*", "RenderMan" },
	{ "gl:*", "OpenGL" },
	{ "usd:*", "USD" },
	{ "user:*", "User" },
	{
		"scene:visible doubleSided render:* gaffer:* "
		"linkedLights shadowedLights filteredLights "
		"surface displacement volume light",
		"Standard"
	}
};

const InternedString g_other( "Other" );

InspectorTree::Inspections attributeInspectionProvider( ScenePlug *scene, const Gaffer::PlugPtr &editScope )
{
	ConstCompoundObjectPtr attributes = scene->fullAttributes( Context::current()->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ) );
	const vector<InternedString> sortedAttributeNames = alphabeticallySortedKeys( attributes->members() );

	InspectorTree::Inspections result;
	for( auto name : sortedAttributeNames )
	{
		InternedString category = g_other;
		for( const auto &[pattern, matchingCategory] : g_attributeCategories )
		{
			if( StringAlgo::matchMultiple( name, pattern ) )
			{
				category = matchingCategory;
				break;
			}
		}
		result.push_back( { { category, name }, new GafferSceneUI::Private::AttributeInspector( scene, editScope, name ) } );
	}
	return result;
}

const InspectorTree::Registration g_attributeInspectionRegistration( { "Location", "Attributes" }, attributeInspectionProvider );

// Option Inspectors
// =================

const boost::container::flat_map<string, InternedString> g_optionCategories = {
	{ "ai:*", "Arnold" },
	{ "dl:*", "3Delight" },
	{ "cycles:*", "Cycles" },
	{ "ri:*", "RenderMan" },
	{ "gl:*", "OpenGL" },
	{ "usd:*", "USD" },
	{ "user:*", "User" },
	{ "render:* sampleMotion", "Standard" },
};

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
		for( const auto &[pattern, matchingCategory] : g_optionCategories )
		{
			if( StringAlgo::matchMultiple( optionName, pattern ) )
			{
				category = matchingCategory;
				break;
			}
		}
		result.push_back( {
			{ category, optionName },
			new GafferSceneUI::Private::OptionInspector( scene, editScope, optionName )
		} );
	}
	return result;
}

const InspectorTree::Registration g_optionsInspectionRegistration( { "Globals", "Options" }, optionsInspectionProvider );

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
			CellData result = InspectorColumn::cellData( path, canceller );

			/// \todo Rejig InspectorColumn so we can share the inspection it already did.
			GafferSceneUI::Private::Inspector::ResultPtr inspectionA = inspect( path, canceller );
			GafferSceneUI::Private::Inspector::ResultPtr inspectionB = m_otherColumn->inspect( path, canceller );
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

void inspectorTreeRegisterInspectorsWrapper( const vector<InternedString> &path, object pythonInspectionProvider )
{
	InspectorTree::InspectionProvider inspectionProvider = [pythonInspectionProvider] ( ScenePlug *scene, const Gaffer::PlugPtr &editScope ) {
		InspectorTree::Inspections result;
		IECorePython::ScopedGILLock gilLock;
		try
		{
			object pythonInspections = pythonInspectionProvider( ScenePlugPtr( scene ), editScope );
			dict inspectionsDict = extract<dict>( pythonInspections );
			boost::python::list items = inspectionsDict.items();
			for( size_t i = 0, e = len( items ); i < e; ++i )
			{
				vector<InternedString> path = extract<vector<InternedString>>( items[i][0] );
				Private::InspectorPtr inspector = extract<Private::InspectorPtr>( items[i][1] );
				result.push_back( { path, inspector } );
			}
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

	IECorePython::RefCountedClass<InspectorTree, RefCounted>( "InspectorTree" )
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
		.def( "dirtiedSignal", &InspectorTree::dirtiedSignal, return_internal_reference<1>() )
		.def( "registerInspectors", &inspectorTreeRegisterInspectorsWrapper ).staticmethod( "registerInspectors" )
	;

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
