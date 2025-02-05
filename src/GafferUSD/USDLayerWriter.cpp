//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferUSD/USDLayerWriter.h"

#include "GafferScene/DeleteAttributes.h"
#include "GafferScene/DeleteObject.h"
#include "GafferScene/PathFilter.h"
#include "GafferScene/Prune.h"
#include "GafferScene/SceneAlgo.h"

#include "Gaffer/ContextQuery.h"
#include "Gaffer/NameSwitch.h"
#include "Gaffer/NameValuePlug.h"

#include "IECoreScene/SceneInterface.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "pxr/usd/sdf/attributeSpec.h"
#include "pxr/usd/sdf/layer.h"
#include "pxr/usd/sdf/primSpec.h"
IECORE_POP_DEFAULT_VISIBILITY

#include "boost/filesystem.hpp"

#include "tbb/parallel_reduce.h"

#include <filesystem>

using namespace std;
using namespace pxr;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferUSD;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

const PathMatcher g_emptyPathMatcher;

struct Filters
{
	bool fullyPruned = true; // True only if all descendants present in `prune`.
	PathMatcher prune;
	PathMatcher deleteObject;
	PathMatcher deleteAttributes;

	// Merges in filters from sibling locations.
	void add( const Filters &other )
	{
		fullyPruned = fullyPruned && other.fullyPruned;
		prune.addPaths( other.prune );
		deleteAttributes.addPaths( other.deleteAttributes );
		deleteObject.addPaths( other.deleteObject );
	}

	// Merges in filters from child locations.
	void addWithPrefix( const Filters &other, const ScenePlug::ScenePath &prefix )
	{
		fullyPruned = fullyPruned && other.fullyPruned;
		prune.addPaths( other.prune, prefix );
		deleteAttributes.addPaths( other.deleteAttributes, prefix );
		deleteObject.addPaths( other.deleteObject, prefix );
	}

};

// Recursively builds the PathMatchers held in a Filters struct, such that :
//
// - Objects with identical hashes will be included in `Filter::deleteObject`.
// - Attributes with identical hashes will be included in `Filter::deleteAttributes`.
// - Subtrees which are identical in all properties will be included in `Filter::prune`.
//
/// \todo The core logic of this could be lifted into a `SceneAlgo::parallelReduceLocations()`
/// and reused elsewhere. The recursive way we're building PathMatchers by prefixing with the
/// parent as unwind might outperform other approaches we're using elsewhere.
Filters filtersWalk( const GafferScene::ScenePlug *baseScene, const GafferScene::ScenePlug *layerScene, const std::vector<float> &frames, const ScenePlug::ScenePath &path, const Gaffer::ThreadState &threadState, tbb::task_group_context &taskGroupContext )
{
	ScenePlug::PathScope pathScope( threadState, &path );

	bool attributesMatch = true;
	bool objectsMatch = true;
	bool canPrune = true;

	for( auto frame : frames )
	{
		pathScope.setFrame( frame );

		if( !layerScene->existsPlug()->getValue() )
		{
			return { false, g_emptyPathMatcher, g_emptyPathMatcher, g_emptyPathMatcher };
		}

		if( attributesMatch )
		{
			attributesMatch = baseScene->attributesPlug()->hash() == layerScene->attributesPlug()->hash();
			canPrune = canPrune && attributesMatch;
		}

		if( objectsMatch )
		{
			objectsMatch = baseScene->objectPlug()->hash() == layerScene->objectPlug()->hash();
			canPrune = canPrune && objectsMatch;
		}

		if( canPrune )
		{
			canPrune = baseScene->transformPlug()->hash() == layerScene->transformPlug()->hash();
		}

		if( canPrune )
		{
			canPrune = baseScene->boundPlug()->hash() == layerScene->boundPlug()->hash();
		}
	}

	ScenePlug::ScenePath localPath;
	if( path.size() )
	{
		// We only need the last part, because we prefix with
		// the parent path as we unwind the recursion.
		localPath.push_back( path.back() );
	}

	Filters result;
	result.fullyPruned = canPrune;
	if( attributesMatch )
	{
		result.deleteAttributes.addPath( localPath );
	}
	if( objectsMatch )
	{
		result.deleteObject.addPath( localPath );
	}

	IECore::ConstInternedStringVectorDataPtr baseChildNamesData = baseScene->childNamesPlug()->getValue();
	const vector<InternedString> &baseChildNames = baseChildNamesData->readable();
	if( !baseChildNames.empty() )
	{
		using ChildNameRange = tbb::blocked_range<std::vector<IECore::InternedString>::const_iterator>;
		const ChildNameRange loopRange( baseChildNames.begin(), baseChildNames.end() );

		Filters childFilters = tbb::parallel_reduce(

			loopRange,

			Filters(),

			[&] ( const ChildNameRange &range, Filters x ) {

				ScenePlug::ScenePath childPath = path;
				childPath.push_back( InternedString() );
				for( const auto &childName : range )
				{
					childPath.back() = childName;
					const Filters childFilters = filtersWalk( baseScene, layerScene, frames, childPath, threadState, taskGroupContext );
					x.add( childFilters );
				}
				return x;
			},

			[] ( Filters x, const Filters &y ) {

				x.add( y );
				return x;

			},

			taskGroupContext


		);

		result.addWithPrefix( childFilters, localPath );
	}

	if( result.fullyPruned )
	{
		result.prune.addPath( localPath );
	}

	return result;
}

class ScopedDirectory : boost::noncopyable
{

	public :

		ScopedDirectory( const std::filesystem::path &p )
			:	m_path( p )
		{
			std::filesystem::create_directories( m_path );
		}

		~ScopedDirectory()
		{
			std::filesystem::remove_all( m_path );
		}

	private :

		std::filesystem::path m_path;

};

void createDirectories( const std::string &fileName )
{
	std::filesystem::path filePath( fileName );
	std::filesystem::path directory = filePath.parent_path();
	if( !directory.empty() )
	{
		std::filesystem::create_directories( directory );
	}
}

// Returns `true` if this prim should be retained, or `false` if it should be
// removed from its parent.
bool createDiff( const SdfPrimSpecHandle &prim, SdfLayer &layer, const SdfPrimSpecHandle &basePrim, SdfLayer &baseLayer )
{

	// Author an inactive prim for any children in `basePrim` that are not in
	// `prim`. This prunes the child from the composed scene.

	bool keepThisPrim = false;

	const vector<SdfPrimSpecHandle> childPrims = prim->GetNameChildren().values();
	for( auto &baseChildPrim : basePrim->GetNameChildren().values() )
	{
		if( !prim->GetPrimAtPath( SdfPath::ReflexiveRelativePath().AppendChild( baseChildPrim->GetNameToken() ) ) )
		{
			SdfPrimSpec::New( prim, baseChildPrim->GetName(), SdfSpecifierOver )->SetActive( false );
			keepThisPrim = true;
		}
	}

	// Recurse to process our children (not including newly-made inactive prims),
	// and remove any children we no longer need.

	for( const auto &childPrim : childPrims )
	{
		if( auto baseChildPrim = basePrim->GetPrimAtPath( SdfPath::ReflexiveRelativePath().AppendChild( childPrim->GetNameToken() ) ) )
		{
			if( createDiff( childPrim, layer, baseChildPrim, baseLayer ) )
			{
				keepThisPrim = true;
			}
			else
			{
				prim->RemoveNameChild( childPrim );
			}
		}
		else
		{
			keepThisPrim = true;
		}
	}

	// Author a blocking value for any attributes which exist in the base prim
	// but not on this prim.

	for( const auto &baseAttribute : basePrim->GetAttributes() )
	{
		if( !prim->GetAttributeAtPath( SdfPath::ReflexiveRelativePath().AppendProperty( baseAttribute->GetNameToken() ) ) )
		{
			SdfAttributeSpecHandle attribute = SdfAttributeSpec::New(
				prim, baseAttribute->GetName(), baseAttribute->GetTypeName(),
				baseAttribute->GetVariability(), baseAttribute->IsCustom()
			);
			attribute->SetDefaultValue( VtValue( SdfValueBlock() ) );
			keepThisPrim = true;
		}
	}

	// Remove any properties that are identical to those in the base prim.

	for( const auto &property : prim->GetProperties().values() )
	{
		bool keepThisProperty = false;
		SdfPropertySpecHandle baseProperty = basePrim->GetPropertyAtPath( SdfPath::ReflexiveRelativePath().AppendProperty( property->GetNameToken() ) );
		if( baseProperty )
		{
			for( auto &field : property->ListFields() )
			{
				if( property->GetField( field ) != baseProperty->GetField( field ) )
				{
					keepThisProperty = true;
					break;
				}
			}
		}
		else
		{
			keepThisProperty = true;
		}

		if( keepThisProperty )
		{
			keepThisPrim = true;
		}
		else
		{
			prim->RemoveProperty( property );
		}
	}

	// Remove any metadata that is identical to the metadata on the base prim.
	// Since a prim's type and specifier is stored as metadata, this has the
	// side effect of converting our prim to an "over" if we have the same type
	// as the base prim.
	//
	// I haven't been able to find a way to "deactivate" or "block" metadata like
	// we can for prims and attributes, so we can't block any metadata that exists
	// on the base prim but not this one. The closest I've been able to get is
	// to use `prim->GetSchema().GetFieldDefinition( key )->GetFallbackValue()` to
	// revert to the default value for the field, but that ends up producing things like
	// `kind == ""`, which isn't ideal. So for now we punt on that.

	for( const auto &key : prim->ListInfoKeys() )
	{
		if( prim->GetField( key ) == basePrim->GetField( key ) )
		{
			prim->ClearField( key );
		}
		else
		{
			keepThisPrim = true;
		}
	}

	return keepThisPrim;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// USDLayerWriter implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( USDLayerWriter );

size_t USDLayerWriter::g_firstPlugIndex = 0;

USDLayerWriter::USDLayerWriter( const std::string &name )
	: TaskNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "base", Plug::In ) );
	addChild( new ScenePlug( "layer", Plug::In ) );
	addChild( new StringPlug( "fileName" ) );
	addChild( new ScenePlug( "out", Plug::Out, Plug::Default & ~Plug::Serialisable ) );

	SceneWriterPtr sceneWriter = new SceneWriter( "__sceneWriter" );
	addChild( sceneWriter );

	NameSwitchPtr sceneSwitch = new NameSwitch( "__sceneSwitch" );
	sceneSwitch->selectorPlug()->setValue( "${usdLayerWriter:fileName}" );
	sceneSwitch->deleteContextVariablesPlug()->setValue( "usdLayerWriter:*" );
	sceneSwitch->setup( basePlug() );
	sceneSwitch->inPlugs()->getChild<NameValuePlug>( 0 )->valuePlug()->setInput( basePlug() );
	sceneSwitch->inPlugs()->getChild<NameValuePlug>( 1 )->valuePlug()->setInput( layerPlug() );
	sceneSwitch->inPlugs()->getChild<NameValuePlug>( 1 )->namePlug()->setValue( "*layer.usdc" );

	addChild( sceneSwitch );

	// The biggest bottleneck in USDLayerWriter is writing scenes via the
	// SceneWriter, where we're hampered by the fact that we can only write from
	// a single thread. To improve performance, we pre-process the scenes before
	// writing, to delete identical objects and attributes and prune entire
	// identical subtrees. This is done with the following internal node network.

	ConstValuePlugPtr queryPrototype = new StringVectorDataPlug( "queryPrototype" );
	ContextQueryPtr contextQuery = new ContextQuery( "__contextQuery" );
	const NameValuePlug *pruneQuery = contextQuery->addQuery( queryPrototype.get(), "usdLayerWriter:pruneFilter" );
	const NameValuePlug *deleteObjectQuery = contextQuery->addQuery( queryPrototype.get(), "usdLayerWriter:deleteObjectFilter" );
	const NameValuePlug *deleteAttributesQuery = contextQuery->addQuery( queryPrototype.get(), "usdLayerWriter:deleteAttributesFilter" );
	addChild( contextQuery );

	PathFilterPtr pruneFilter = new PathFilter( "__pruneFilter" );
	pruneFilter->pathsPlug()->setInput( contextQuery->valuePlugFromQueryPlug( pruneQuery ) );
	addChild( pruneFilter );

	PrunePtr prune = new Prune( "__prune" );
	prune->inPlug()->setInput( static_cast<NameValuePlug *>( sceneSwitch->outPlug() )->valuePlug() );
	// Sneaky pass-through so that sets don't get pruned, since we still need to
	// write them in full.
	prune->outPlug()->setPlug()->setInput( prune->inPlug()->setPlug() );
	prune->filterPlug()->setInput( pruneFilter->outPlug() );
	addChild( prune );

	PathFilterPtr deleteObjectFilter = new PathFilter( "__deleteObjectFilter" );
	deleteObjectFilter->pathsPlug()->setInput( contextQuery->valuePlugFromQueryPlug( deleteObjectQuery ) );
	addChild( deleteObjectFilter );

	DeleteObjectPtr deleteObject = new GafferScene::DeleteObject( "__deleteObject" );
	deleteObject->inPlug()->setInput( prune->outPlug() );
	deleteObject->filterPlug()->setInput( deleteObjectFilter->outPlug() );
	addChild( deleteObject );

	PathFilterPtr deleteAttributesFilter = new PathFilter( "__deleteAttributesFilter" );
	deleteAttributesFilter->pathsPlug()->setInput( contextQuery->valuePlugFromQueryPlug( deleteAttributesQuery ) );
	addChild( deleteAttributesFilter );

	DeleteAttributesPtr deleteAttributes = new DeleteAttributes( "__deleteAttributes" );
	deleteAttributes->inPlug()->setInput( deleteObject->outPlug() );
	deleteAttributes->filterPlug()->setInput( deleteAttributesFilter->outPlug() );
	deleteAttributes->namesPlug()->setValue( "*" );
	addChild( deleteAttributes );

	sceneWriter->inPlug()->setInput( deleteAttributes->outPlug() );
	sceneWriter->fileNamePlug()->setValue( "${usdLayerWriter:fileName}" );

	outPlug()->setInput( layerPlug() );
}

USDLayerWriter::~USDLayerWriter()
{
}

GafferScene::ScenePlug *USDLayerWriter::basePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *USDLayerWriter::basePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

GafferScene::ScenePlug *USDLayerWriter::layerPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 1 );
}

const GafferScene::ScenePlug *USDLayerWriter::layerPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 1 );
}

StringPlug *USDLayerWriter::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const StringPlug *USDLayerWriter::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

GafferScene::ScenePlug *USDLayerWriter::outPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 3 );
}

const GafferScene::ScenePlug *USDLayerWriter::outPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 3 );
}

const GafferScene::SceneWriter *USDLayerWriter::sceneWriter() const
{
	return getChild<SceneWriter>( g_firstPlugIndex + 4 );
}

IECore::MurmurHash USDLayerWriter::hash( const Gaffer::Context *context ) const
{
	const std::string fileName = fileNamePlug()->getValue();
	if( !basePlug()->getInput() || !layerPlug()->getInput() || fileName.empty() )
	{
		return IECore::MurmurHash();
	}

	IECore::MurmurHash h = TaskNode::hash( context );
	h.append( fileName );
	h.append( context->hash() );

	return h;
}

bool USDLayerWriter::requiresSequenceExecution() const
{
	return true;
}

void USDLayerWriter::execute() const
{
	std::vector<float> frame( 1, Context::current()->getFrame() );
	executeSequence( frame );
}

void USDLayerWriter::executeSequence( const std::vector<float> &frames ) const
{
	if( !basePlug()->getInput() )
	{
		throw IECore::Exception( "No `base` input" );
	}

	if( !layerPlug()->getInput() )
	{
		throw IECore::Exception( "No `layer` input" );
	}

	const std::string outputFileName = fileNamePlug()->getValue();
	if( outputFileName.empty() )
	{
		return;
	}

	// Figure out the filters for our Prune, DeleteObject and DeleteAttribute
	// nodes.
	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated ); // Prevents outer tasks silently cancelling our tasks
	const Filters filters = filtersWalk( basePlug(), layerPlug(), frames, ScenePlug::ScenePath(), ThreadState::current(), taskGroupContext );

	// Pass the filter settings via context variables since we can't call
	// `Plug::setValue()` from `executeSequence()` because it would violate
	// thread-safety.

	Context::EditableScope context( Context::current() );

	vector<string> pruneFilter; filters.prune.paths( pruneFilter );
	context.set( "usdLayerWriter:pruneFilter", &pruneFilter );
	vector<string> deleteObjectFilter; filters.deleteObject.paths( deleteObjectFilter );
	context.set( "usdLayerWriter:deleteObjectFilter", &deleteObjectFilter );
	vector<string> deleteAttributesFilter; filters.deleteAttributes.paths( deleteAttributesFilter );
	context.set( "usdLayerWriter:deleteAttributesFilter", &deleteAttributesFilter );

	// Write the complete base and layer inputs into temporary USD files. We use
	// a ScopedDirectory so that the files are cleaned up no matter how we exit
	// this function.

	const std::filesystem::path tempDirectory = std::filesystem::temp_directory_path() / boost::filesystem::unique_path().string();
	ScopedDirectory scopedTempDirectory( tempDirectory );

	const string baseFileName = ( tempDirectory / "base.usdc" ).generic_string();
	const string layerFileName = ( tempDirectory / "layer.usdc" ).generic_string();
	for( const auto &fileName : { baseFileName, layerFileName } )
	{
		context.set( "usdLayerWriter:fileName", &fileName );
		sceneWriter()->taskPlug()->executeSequence( frames );
	}

	// Load the temporary USD files, and process `layer` in place so that it
	// contains only the differences from `baseLayer`. Then write the result
	// out.

	SdfLayerRefPtr baseLayer = SdfLayer::OpenAsAnonymous( baseFileName );
	SdfLayerRefPtr layer = SdfLayer::OpenAsAnonymous( layerFileName );

	SdfChangeBlock changeBlock;
	createDiff( layer->GetPseudoRoot(), *layer, baseLayer->GetPseudoRoot(), *baseLayer );

	createDirectories( outputFileName );
	if( !layer->Export( outputFileName ) )
	{
		throw IECore::Exception( fmt::format( "Failed to export layer to \"{}\"", outputFileName ) );
	}
}
