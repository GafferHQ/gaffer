//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/EditScopeAlgo.h"

#include "GafferScene/AttributeTweaks.h"
#include "GafferScene/OptionTweaks.h"
#include "GafferScene/Prune.h"
#include "GafferScene/PathFilter.h"
#include "GafferScene/SceneProcessor.h"
#include "GafferScene/Set.h"
#include "GafferScene/ShaderTweaks.h"
#include "GafferScene/Transform.h"
#include "GafferScene/RenderPasses.h"

#include "Gaffer/EditScope.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/Spreadsheet.h"
#include "Gaffer/StringPlug.h"

#include "IECore/AngleConversion.h"
#include "IECore/CamelCase.h"

#include "Imath/ImathMatrixAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/replace.hpp"
#include "boost/range/algorithm/replace_copy_if.hpp"
#include "boost/container/flat_map.hpp"
#include "boost/tokenizer.hpp"

#include "fmt/format.h"

#include <unordered_map>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

// Pruning
// =======

SceneProcessorPtr pruningProcessor()
{
	SceneProcessorPtr result = new SceneProcessor( "PruningEdits" );

	PathFilterPtr pathFilter = new PathFilter;
	result->addChild( pathFilter );

	PrunePtr prune = new Prune;
	result->addChild( prune );
	prune->inPlug()->setInput( result->inPlug() );
	prune->filterPlug()->setInput( pathFilter->outPlug() );
	prune->enabledPlug()->setInput( result->enabledPlug() );
	PlugAlgo::promote( pathFilter->pathsPlug() );
	PlugAlgo::promote( prune->adjustBoundsPlug() );

	result->outPlug()->setInput( prune->outPlug() );

	return result;
}

EditScope::ProcessorRegistration g_pruneProcessorRegistration( "PruningEdits", pruningProcessor );

} // namespace

void GafferScene::EditScopeAlgo::setPruned( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, bool pruned )
{
	PathMatcher paths;
	paths.addPath( path );
	setPruned( scope, paths, pruned );
}

void GafferScene::EditScopeAlgo::setPruned( Gaffer::EditScope *scope, const IECore::PathMatcher &paths, bool pruned )
{
	Node *processor = scope->acquireProcessor( "PruningEdits" );
	auto pathsPlug = processor->getChild<StringVectorDataPlug>( "paths" );
	ConstStringVectorDataPtr existingPaths = pathsPlug->getValue();
	IECore::PathMatcher combinedPathMatcher( existingPaths->readable().begin(), existingPaths->readable().end() );

	if( pruned )
	{
		combinedPathMatcher.addPaths( paths );
	}
	else
	{
		combinedPathMatcher.removePaths( paths );
	}

	IECore::StringVectorDataPtr combinedPaths = new StringVectorData;
	combinedPathMatcher.paths( combinedPaths->writable() );
	sort( combinedPaths->writable().begin(), combinedPaths->writable().end() );
	pathsPlug->setValue( combinedPaths );
}

bool GafferScene::EditScopeAlgo::getPruned( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path )
{
	Node *processor = scope->acquireProcessor( "PruningEdits", /* createIfNecessary = */ false );
	if( !processor )
	{
		return false;
	}
	auto pathsPlug = processor->getChild<StringVectorDataPlug>( "paths" );
	ConstStringVectorDataPtr paths = pathsPlug->getValue();
	string pathString; ScenePlug::pathToString( path, pathString );
	return find( paths->readable().begin(), paths->readable().end(), pathString ) != paths->readable().end();
}

const GraphComponent *GafferScene::EditScopeAlgo::prunedReadOnlyReason( const EditScope *scope )
{
	if( const Node *processor = const_cast<EditScope *>( scope )->acquireProcessor( "PruningEdits", /* createIfNecessary = */ false ) )
	{
		return MetadataAlgo::readOnlyReason( processor->getChild<StringVectorDataPlug>( "paths" ) );
	}

	return MetadataAlgo::readOnlyReason( scope );
}

// Transforms
// ==========

namespace
{

const InternedString g_translate( "translate" );
const InternedString g_rotate( "rotate" );
const InternedString g_scale( "scale" );
const InternedString g_pivot( "pivot" );

SceneProcessorPtr transformProcessor()
{
	SceneProcessorPtr result = new SceneProcessor( "TransformEdits" );

	SpreadsheetPtr spreadsheet = new Spreadsheet;
	result->addChild( spreadsheet );
	spreadsheet->selectorPlug()->setValue( "${scene:path}" );

	PathFilterPtr pathFilter = new PathFilter;
	result->addChild( pathFilter );
	pathFilter->pathsPlug()->setInput( spreadsheet->enabledRowNamesPlug() );

	TransformPtr transform = new Transform;
	result->addChild( transform );
	transform->inPlug()->setInput( result->inPlug() );
	transform->filterPlug()->setInput( pathFilter->outPlug() );
	transform->enabledPlug()->setInput( result->enabledPlug() );
	transform->spacePlug()->setValue( Transform::Space::ResetLocal );

	for( auto name : { g_translate, g_rotate, g_scale, g_pivot } )
	{
		auto plug = transform->transformPlug()->getChild<ValuePlug>( name );
		spreadsheet->rowsPlug()->addColumn( plug );
		plug->setInput( spreadsheet->outPlug()->getChild<Plug>( name ) );
	}

	auto rowsPlug = static_cast<Spreadsheet::RowsPlug *>( PlugAlgo::promoteWithName( spreadsheet->rowsPlug(), "edits" ) );
	Metadata::registerValue( rowsPlug, "spreadsheet:defaultRowVisible", new BoolData( false ) );
	Metadata::registerValue( rowsPlug->defaultRow(), "spreadsheet:rowNameWidth", new IntData( 300 ) );
	for( auto &cell : Spreadsheet::CellPlug::Range( *rowsPlug->defaultRow()->cellsPlug() ) )
	{
		Metadata::registerValue( cell.get(), "spreadsheet:columnWidth", new IntData( 200 ) );
	}

	result->outPlug()->setInput( transform->outPlug() );

	return result;
}

EditScope::ProcessorRegistration g_transformProcessorRegistration( "TransformEdits", transformProcessor );

} // namespace

bool GafferScene::EditScopeAlgo::hasTransformEdit( const Gaffer::EditScope *scope, const ScenePlug::ScenePath &path )
{
	return (bool)acquireTransformEdit( const_cast<EditScope *>( scope ), path, /* createIfNecessary = */ false );
}

void GafferScene::EditScopeAlgo::removeTransformEdit( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path )
{
	auto p = acquireTransformEdit( scope, path, /* createIfNecessary = */ false );
	if( !p )
	{
		return;
	}
	auto row = p->translate->ancestor<Spreadsheet::RowPlug>();
	row->parent()->removeChild( row );
}

EditScopeAlgo::TransformEdit::TransformEdit(
	const Gaffer::V3fPlugPtr &translate,
	const Gaffer::V3fPlugPtr &rotate,
	const Gaffer::V3fPlugPtr &scale,
	const Gaffer::V3fPlugPtr &pivot
)
	:	translate( translate ), rotate( rotate ), scale( scale ), pivot( pivot )
{
}

Imath::M44f EditScopeAlgo::TransformEdit::matrix() const
{
	const V3f p = this->pivot->getValue();
	M44f result;
	result.translate( p + translate->getValue() );
	result.rotate( IECore::degreesToRadians( rotate->getValue() ) );
	result.scale( scale->getValue() );
	result.translate( -p );
	return result;
}

bool EditScopeAlgo::TransformEdit::operator == ( const TransformEdit &rhs ) const
{
	return
		translate == rhs.translate &&
		rotate == rhs.rotate &&
		scale == rhs.scale &&
		pivot == rhs.pivot
	;
}

bool EditScopeAlgo::TransformEdit::operator != ( const TransformEdit &rhs ) const
{
	return !(*this == rhs);
}

std::optional<GafferScene::EditScopeAlgo::TransformEdit> GafferScene::EditScopeAlgo::acquireTransformEdit( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, bool createIfNecessary )
{
	string pathString;
	ScenePlug::pathToString( path, pathString );

	auto *processor = scope->acquireProcessor<SceneProcessor>( "TransformEdits", createIfNecessary );
	if( !processor )
	{
		return std::nullopt;
	}

	auto *rows = processor->getChild<Spreadsheet::RowsPlug>( "edits" );
	Spreadsheet::RowPlug *row = rows->row( pathString );
	if( !row )
	{
		if( !createIfNecessary )
		{
			return std::nullopt;
		}
		row = rows->addRow();
		row->namePlug()->setValue( pathString );
	}

	return TransformEdit {
		row->cellsPlug()->getChild<Spreadsheet::CellPlug>( g_translate )->valuePlug<V3fPlug>(),
		row->cellsPlug()->getChild<Spreadsheet::CellPlug>( g_rotate )->valuePlug<V3fPlug>(),
		row->cellsPlug()->getChild<Spreadsheet::CellPlug>( g_scale )->valuePlug<V3fPlug>(),
		row->cellsPlug()->getChild<Spreadsheet::CellPlug>( g_pivot )->valuePlug<V3fPlug>()
	};
}

const GraphComponent *GafferScene::EditScopeAlgo::transformEditReadOnlyReason( const Gaffer::EditScope *scope, const ScenePlug::ScenePath &path )
{
	auto *processor = const_cast<EditScope *>( scope )->acquireProcessor<SceneProcessor>( "TransformEdits", /* createIfNecessary = */ false );
	if( !processor )
	{
		return MetadataAlgo::readOnlyReason( scope );
	}

	string pathString;
	ScenePlug::pathToString( path, pathString );

	auto *rows = processor->getChild<Spreadsheet::RowsPlug>( "edits" );
	const Spreadsheet::RowPlug *row = rows->row( pathString );
	if( !row )
	{
		return MetadataAlgo::readOnlyReason( rows );
	}

	if( const auto reason = MetadataAlgo::readOnlyReason( row->cellsPlug() ) )
	{
		return reason;
	}

	for( const auto &plug : Plug::RecursiveRange( *row->cellsPlug() ) )
	{
		if( MetadataAlgo::getReadOnly( plug.get() ) )
		{
			return plug.get();
		}
	}

	return nullptr;
}

// Shaders
// =======

namespace
{

const std::string g_attributePrefix = "attribute:";

SceneProcessorPtr shaderParameterProcessor( const std::string &attribute, const std::string &name )
{
	SceneProcessorPtr result = new SceneProcessor( name );

	SpreadsheetPtr spreadsheet = new Spreadsheet;
	result->addChild( spreadsheet );
	spreadsheet->selectorPlug()->setValue( "${scene:path}" );

	PathFilterPtr pathFilter = new PathFilter;
	result->addChild( pathFilter );
	pathFilter->pathsPlug()->setInput( spreadsheet->enabledRowNamesPlug() );

	ShaderTweaksPtr shaderTweaks = new ShaderTweaks;
	result->addChild( shaderTweaks );
	shaderTweaks->inPlug()->setInput( result->inPlug() );
	shaderTweaks->filterPlug()->setInput( pathFilter->outPlug() );
	shaderTweaks->enabledPlug()->setInput( result->enabledPlug() );
	shaderTweaks->shaderPlug()->setValue( attribute );
	shaderTweaks->localisePlug()->setValue( true );
	shaderTweaks->ignoreMissingPlug()->setValue( true );

	auto rowsPlug = static_cast<Spreadsheet::RowsPlug *>( PlugAlgo::promoteWithName( spreadsheet->rowsPlug(), "edits" ) );
	Metadata::registerValue( rowsPlug, "spreadsheet:defaultRowVisible", new BoolData( false ) );
	Metadata::registerValue( rowsPlug->defaultRow(), "spreadsheet:rowNameWidth", new IntData( 300 ) );

	result->outPlug()->setInput( shaderTweaks->outPlug() );

	return result;
}

/// \todo Create a central renderer/attribute registry that we can
/// query for this information.
const boost::container::flat_map<string, string> g_rendererAttributePrefixes = {
	{ "ai", "Arnold" },
	{ "dl", "Delight" },
	{ "gl", "OpenGL" },
	{ "osl", "OSL" },
	{ "cycles", "Cycles" }
};

/// \todo Create a registration method for populating overrides.
using ProcessorOverrideMap = std::unordered_map<std::string, std::string>;
const ProcessorOverrideMap g_processorNameOverrides = {
	{ "ai:lightFilter:filter", "ArnoldLightBlockerFilterEdits" },
	{ "ai:lightFilter:barndoor", "ArnoldBarndoorFilterEdits" },
	{ "ai:lightFilter:light_decay", "ArnoldLightDecayFilterEdits" },
	{ "ai:lightFilter:gobo", "ArnoldGoboFilterEdits" }
};

string parameterProcessorName( const std::string &attribute )
{
	ProcessorOverrideMap::const_iterator override = g_processorNameOverrides.find( attribute );
	if( override != g_processorNameOverrides.end() )
	{
		return override->second;
	}

	string rendererPrefix;
	vector<string> parts;

	using Tokenizer = boost::tokenizer<boost::char_separator<char>>;
	Tokenizer tokens( attribute, boost::char_separator<char>( ":" ) );
	for( const auto &token : tokens )
	{
		if( parts.empty() )
		{
			auto it = g_rendererAttributePrefixes.find( token );
			if( it != g_rendererAttributePrefixes.end() )
			{
				rendererPrefix = it->second;
				continue;
			}
		}
		CamelCase::split( token, back_inserter( parts ) );
	}

	return rendererPrefix + CamelCase::join( parts.begin(), parts.end() ) + "Edits";
}

SceneProcessor *acquireParameterProcessor( EditScope *editScope, const std::string &attribute, bool createIfNecessary )
{
	static unordered_map<string, string> attributeProcessors;
	auto inserted = attributeProcessors.insert( { attribute, "" } );
	if( inserted.second )
	{
		const string name = parameterProcessorName( attribute );
		EditScope::registerProcessor(
			name,
			[ attribute, name ] () {
				return ::shaderParameterProcessor( attribute, name );
			}
		);
		inserted.first->second = name;
	}

	return editScope->acquireProcessor<SceneProcessor>( inserted.first->second, createIfNecessary );
}

ConstObjectPtr attributeValue( const ScenePlug *scene, const ScenePlug::ScenePath &path, const std::string &attribute )
{
	if( !scene->exists( path ) )
	{
		string pathString; ScenePlug::pathToString( path, pathString );
		throw IECore::Exception( fmt::format( "Location \"{}\" does not exist", pathString ) );
	}

	auto attributes = scene->fullAttributes( path );

	ConstObjectPtr result = attributes->members()[attribute];

	if( !result )
	{
		if( const auto defaultValue = Gaffer::Metadata::value( g_attributePrefix + attribute, "defaultValue" ) )
		{
			return defaultValue;
		}

		throw IECore::Exception( fmt::format( "Attribute \"{}\" does not exist", attribute ) );
	}

	return result;
}

ConstDataPtr parameterValue( const ScenePlug *scene, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter )
{
	auto attributeShader = attributeValue( scene, path, attribute );

	auto shaderNetwork = runTimeCast<const IECoreScene::ShaderNetwork>( attributeShader.get() );
	if( !shaderNetwork )
	{
		throw IECore::Exception( fmt::format( "Attribute \"{}\" is not a shader", attribute ) );
	}

	const IECoreScene::Shader *shader;
	if( parameter.shader.string().size() )
	{
		shader = shaderNetwork->getShader( parameter.shader );
		if( !shader )
		{
			throw IECore::Exception( fmt::format( "Shader \"{}\" does not exist", parameter.shader.string() ) );
		}
	}
	else
	{
		shader = shaderNetwork->outputShader();
		if( !shader )
		{
			throw IECore::Exception( "Output shader does not exist" );
		}
	}

	const Data *result = shader->parametersData()->member( parameter.name );
	if( result )
	{
		return result;
	}
	else
	{
		throw IECore::Exception( fmt::format( "Parameter \"{}\" does not exist", parameter.name.string() ) );
	}
}

} // namespace

bool GafferScene::EditScopeAlgo::hasParameterEdit( const Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter )
{
	return acquireParameterEdit( const_cast<EditScope *>( scope ), path, attribute, parameter, /* createIfNecessary = */ false );
}

TweakPlug *GafferScene::EditScopeAlgo::acquireParameterEdit( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter, bool createIfNecessary )
{
	string pathString;
	ScenePlug::pathToString( path, pathString );

	// If we need to create an edit, we'll need to do a compute to figure our the parameter
	// type and value. But we don't want to do that if we already have an edit. And since the
	// compute could error, we need to get the parameter value before making _any_ changes, so we
	// don't leave things in a partial state. We use `ensureParameterValue()` to get the value
	// lazily at the first point we know it will be needed.
	ConstDataPtr parameterValue;
	auto ensureParameterValue = [&] {
		if( !parameterValue )
		{
			parameterValue = ::parameterValue( scope->outPlug<ScenePlug>(), path, attribute, parameter );
		}
	};

	// Find processor, and row for `path`.

	auto *processor = acquireParameterProcessor( scope, attribute, /* createIfNecessary = */ false );
	if( !processor )
	{
		if( !createIfNecessary )
		{
			return nullptr;
		}
		else
		{
			ensureParameterValue();
			processor = acquireParameterProcessor( scope, attribute, /* createIfNecessary = */ true );
		}
	}

	auto *rows = processor->getChild<Spreadsheet::RowsPlug>( "edits" );
	Spreadsheet::RowPlug *row = rows->row( pathString );
	if( !row )
	{
		if( !createIfNecessary )
		{
			return nullptr;
		}
		ensureParameterValue();
		row = rows->addRow();
		row->namePlug()->setValue( pathString );
	}

	// Find cell for parameter

	string tweakName = parameter.name.string();
	if( parameter.shader.string().size() )
	{
		tweakName = parameter.shader.string() + "." + tweakName;
	}

	string columnName;
	boost::replace_copy_if( tweakName, std::back_inserter( columnName ), boost::is_any_of( ".:" ), '_' );
	if( auto *cell = row->cellsPlug()->getChild<Spreadsheet::CellPlug>( columnName ) )
	{
		return cell->valuePlug<TweakPlug>();
	}

	if( !createIfNecessary )
	{
		return nullptr;
	}

	// No tweak for parameter yet. Create it.

	ensureParameterValue();
	ValuePlugPtr valuePlug = PlugAlgo::createPlugFromData( "value", Plug::In, Plug::Default, parameterValue.get() );
	/// \todo The TweakPlug constructor makes a plug where `namePlug()` has a default value of "" and `enabledPlug()`
	/// has a default value of `true`. This makes for a lot of redundancy in our spreadsheet serialisations because
	/// every cell will have a `setValue()` for the name, and we expect to have fewer enabled cells than disabled ones.
	/// Change the TweakPlug constructor (or provide an overload) so we can get the defaults we want. Consider the
	/// relationship to NameValuePlug and ShufflePlug constructors at the same time.
	TweakPlugPtr tweakPlug = new TweakPlug( tweakName, valuePlug, TweakPlug::Replace, false );

	auto *shaderTweaks = processor->getChild<ShaderTweaks>( "ShaderTweaks" );
	shaderTweaks->tweaksPlug()->addChild( tweakPlug );

	size_t columnIndex = rows->addColumn( tweakPlug.get(), columnName, /* adoptEnabledPlug = */ true );
	tweakPlug->setInput( processor->getChild<Spreadsheet>( "Spreadsheet" )->outPlug()->getChild<Plug>( columnIndex ) );

	return row->cellsPlug()->getChild<Spreadsheet::CellPlug>( columnIndex )->valuePlug<TweakPlug>();
}

void GafferScene::EditScopeAlgo::removeParameterEdit( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter )
{
	TweakPlug *edit = acquireParameterEdit( scope, path, attribute, parameter, /* createIfNecessary = */ false );
	if( !edit )
	{
		return;
	}
	// We're unlikely to be able to delete the row or column,
	// because that would affect other edits, so we simply disable
	// the edit instead.
	edit->enabledPlug()->setValue( false );
}

const GraphComponent *GafferScene::EditScopeAlgo::parameterEditReadOnlyReason( const Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter )
{
	auto *processor = acquireParameterProcessor( const_cast<EditScope *>( scope ), attribute, /* createIfNecessary = */ false );
	if( !processor )
	{
		return MetadataAlgo::readOnlyReason( scope );
	}

	string pathString;
	ScenePlug::pathToString( path, pathString );

	auto *rows = processor->getChild<Spreadsheet::RowsPlug>( "edits" );
	Spreadsheet::RowPlug *row = rows->row( pathString );
	if( !row )
	{
		return MetadataAlgo::readOnlyReason( rows );
	}

	if( const auto reason = MetadataAlgo::readOnlyReason( row->cellsPlug() ) )
	{
		return reason;
	}

	string tweakName = parameter.name.string();
	if( parameter.shader.string().size() )
	{
		tweakName = parameter.shader.string() + "." + tweakName;
	}
	string columnName;
	boost::replace_copy_if( tweakName, std::back_inserter( columnName ), boost::is_any_of( ".:" ), '_' );
	if( auto *cell = row->cellsPlug()->getChild<Spreadsheet::CellPlug>( columnName ) )
	{
		if( MetadataAlgo::getReadOnly( cell ) )
		{
			return cell;
		}

		for( const auto &plug : Plug::RecursiveRange( *cell ) )
		{
			if( MetadataAlgo::getReadOnly( plug.get() ) )
			{
				return plug.get();
			}
		}
	}

	return nullptr;
}

// Attributes
// ==========

namespace
{

const std::string g_attributeProcessorName = "AttributeEdits";

SceneProcessorPtr attributeProcessor( const std::string &name )
{
	SceneProcessorPtr result = new SceneProcessor( name );

	SpreadsheetPtr spreadsheet = new Spreadsheet;
	result->addChild( spreadsheet );
	spreadsheet->selectorPlug()->setValue( "${scene:path}" );

	PathFilterPtr pathFilter = new PathFilter;
	result->addChild( pathFilter );
	pathFilter->pathsPlug()->setInput( spreadsheet->enabledRowNamesPlug() );

	AttributeTweaksPtr attributeTweaks = new AttributeTweaks;
	result->addChild( attributeTweaks );
	attributeTweaks->inPlug()->setInput( result->inPlug() );
	attributeTweaks->filterPlug()->setInput( pathFilter->outPlug() );
	attributeTweaks->enabledPlug()->setInput( result->enabledPlug() );
	attributeTweaks->localisePlug()->setValue( true );
	attributeTweaks->ignoreMissingPlug()->setValue( true );

	auto rowsPlug = static_cast<Spreadsheet::RowsPlug *>(
		PlugAlgo::promoteWithName( spreadsheet->rowsPlug(), "edits" )
	);
	Metadata::registerValue( rowsPlug, "spreadsheet:defaultRowVisible", new BoolData( false ) );
	Metadata::registerValue( rowsPlug->defaultRow(), "spreadsheet:rowNameWidth", new IntData( 300 ) );

	result->outPlug()->setInput( attributeTweaks->outPlug() );

	return result;
}

SceneProcessor *acquireAttributeProcessor( EditScope *editScope, bool createIfNecessary )
{
	static bool isRegistered = false;
	if( !isRegistered )
	{
		EditScope::registerProcessor(
			g_attributeProcessorName,
			[]() {
				return attributeProcessor( g_attributeProcessorName );
			}
		);

		isRegistered = true;
	}

	return editScope->acquireProcessor<SceneProcessor>( g_attributeProcessorName, createIfNecessary );
}

}  // namespace


bool GafferScene::EditScopeAlgo::hasAttributeEdit( const Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, const std::string &attribute )
{
	return acquireAttributeEdit( const_cast<EditScope *>( scope ), path, attribute, /* createIfNecessary = */ false );
}

TweakPlug *GafferScene::EditScopeAlgo::acquireAttributeEdit( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, const std::string &attribute, bool createIfNecessary )
{
	const std::string pathString = ScenePlug::pathToString( path );

	// If we need to create an edit, we'll need to do a compute to figure our the attribute
	// type and value. But we don't want to do that if we already have an edit. And since the
	// compute could error, we need to get the attribute value before making _any_ changes, so we
	// don't leave things in a partial state. We use `ensureAttributeValue()` to get the value
	// lazily at the first point we know it will be needed.
	ConstDataPtr attributeValue;
	auto ensureAttributeValue = [&] {
		if( !attributeValue )
		{
			attributeValue = runTimeCast<const Data>(
				::attributeValue( scope->outPlug<ScenePlug>(), path, attribute )
			);
			if( !attributeValue )
			{
				throw IECore::Exception( fmt::format( "Attribute \"{}\" cannot be tweaked", attribute ) );
			}
		}
	};

	// Find processor, and row for `path`.

	auto *processor = acquireAttributeProcessor( scope, /* createIfNecessary */ false );
	if( !processor )
	{
		if( !createIfNecessary )
		{
			return nullptr;
		}
		else
		{
			ensureAttributeValue();
			processor = acquireAttributeProcessor( scope, /* createIfNecessary */ true );
		}
	}

	auto *rows = processor->getChild<Spreadsheet::RowsPlug>( "edits" );
	Spreadsheet::RowPlug *row = rows->row( pathString );
	if( !row )
	{
		if( !createIfNecessary )
		{
			return nullptr;
		}
		ensureAttributeValue();
		row = rows->addRow();
		row->namePlug()->setValue( pathString );
	}

	// Find cell for attribute

	std::string columnName = boost::replace_all_copy( attribute, ":", "_" );
	if( auto *cell = row->cellsPlug()->getChild<Spreadsheet::CellPlug>( columnName ) )
	{
		return cell->valuePlug<TweakPlug>();
	}

	if( !createIfNecessary )
	{
		return nullptr;
	}

	// No tweak for the attribute yet. Create it.

	ensureAttributeValue();

	ValuePlugPtr valuePlug = PlugAlgo::createPlugFromData( "value", Plug::In, Plug::Default, attributeValue.get() );

	TweakPlugPtr tweakPlug = new TweakPlug( attribute, valuePlug, TweakPlug::Create, false );

	auto *attributeTweaks = processor->getChild<AttributeTweaks>( "AttributeTweaks" );
	attributeTweaks->tweaksPlug()->addChild( tweakPlug );

	size_t columnIndex = rows->addColumn( tweakPlug.get(), columnName, /* adoptEnabledPlug */ true );
	tweakPlug->setInput( processor->getChild<Spreadsheet>( "Spreadsheet" )->outPlug()->getChild<Plug>( columnIndex ) );

	return row->cellsPlug()->getChild<Spreadsheet::CellPlug>( columnIndex )->valuePlug<TweakPlug>();
}

void GafferScene::EditScopeAlgo::removeAttributeEdit( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, const std::string &attribute )
{
	TweakPlug *edit = acquireAttributeEdit( scope, path, attribute, /* createIfNecessary */ false );
	if( !edit )
	{
		return;
	}
	// We're unlikely to be able to delete the row or column,
	// because that would affect other edits, so we simply disable
	// the edit instead.
	edit->enabledPlug()->setValue( false );
}

const Gaffer::GraphComponent *GafferScene::EditScopeAlgo::attributeEditReadOnlyReason( const Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, const std::string &attribute )
{
	auto *processor = acquireAttributeProcessor( const_cast<EditScope *>( scope ), /*createIfNecessary */ false );
	if( !processor )
	{
		return MetadataAlgo::readOnlyReason( scope );
	}

	const std::string pathString = ScenePlug::pathToString( path );

	auto *rows = processor->getChild<Spreadsheet::RowsPlug>( "edits" );
	Spreadsheet::RowPlug *row = rows->row( pathString );
	if( !row )
	{
		return MetadataAlgo::readOnlyReason( rows );
	}

	if( const auto reason = MetadataAlgo::readOnlyReason( row->cellsPlug() ) )
	{
		return reason;
	}

	std::string columnName = boost::replace_all_copy( attribute, ":", "_" );
	if( auto *cell = row->cellsPlug()->getChild<Spreadsheet::CellPlug>( columnName ) )
	{
		if( MetadataAlgo::getReadOnly( cell ) )
		{
			return cell;
		}

		for( const auto &plug : Plug::RecursiveRange( *cell ) )
		{
			if( MetadataAlgo::getReadOnly( plug.get() ) )
			{
				return plug.get();
			}
		}
	}

	return nullptr;
}

// Set Membership
// ==============

namespace
{

static int g_addSetColumnIndex = 0;
static int g_removeSetColumnIndex = 1;

SceneProcessorPtr setMembershipProcessor()
{
	SceneProcessorPtr result = new SceneProcessor( "SetMembershipEdits" );

	SpreadsheetPtr spreadsheet = new Spreadsheet;
	result->addChild( spreadsheet );
	spreadsheet->selectorPlug()->setValue( "${setMembership:set}" );
	spreadsheet->rowsPlug()->addColumn( new StringVectorDataPlug( "Added", Plug::Direction::In, new StringVectorData() ) );
	spreadsheet->rowsPlug()->addColumn( new StringVectorDataPlug( "Removed", Plug::Direction::In, new StringVectorData() ) );

	PathFilterPtr addPathFilter = new PathFilter;
	result->addChild( addPathFilter );
	addPathFilter->pathsPlug()->setInput( spreadsheet->outPlug()->getChild<StringVectorDataPlug>( g_addSetColumnIndex ) );

	PathFilterPtr removePathFilter = new PathFilter;
	result->addChild( removePathFilter );
	removePathFilter->pathsPlug()->setInput( spreadsheet->outPlug()->getChild<StringVectorDataPlug>( g_removeSetColumnIndex ) );

	GafferScene::SetPtr addSet = new GafferScene::Set();
	result->addChild( addSet );
	addSet->inPlug()->setInput( result->inPlug() );
	addSet->filterPlug()->setInput( addPathFilter->outPlug() );
	addSet->namePlug()->setInput( spreadsheet->enabledRowNamesPlug() );
	addSet->modePlug()->setValue( GafferScene::Set::Mode::Add );
	addSet->enabledPlug()->setInput( result->enabledPlug() );
	addSet->setVariablePlug()->setValue( "setMembership:set" );

	GafferScene::SetPtr removeSet = new GafferScene::Set();
	result->addChild( removeSet );
	removeSet->inPlug()->setInput( addSet->outPlug() );
	removeSet->filterPlug()->setInput( removePathFilter->outPlug() );
	removeSet->namePlug()->setInput( spreadsheet->enabledRowNamesPlug() );
	removeSet->modePlug()->setValue( GafferScene::Set::Mode::Remove );
	removeSet->enabledPlug()->setInput( result->enabledPlug() );
	removeSet->setVariablePlug()->setValue( "setMembership:set" );

	auto rowsPlug = static_cast<Spreadsheet::RowsPlug *>(
		PlugAlgo::promoteWithName( spreadsheet->rowsPlug(), "edits" )
	);

	Metadata::registerValue( rowsPlug, "spreadsheet:defaultRowVisible", new BoolData( false ) );
	Metadata::registerValue( rowsPlug->defaultRow(), "spreadsheet:rowNameWidth", new IntData( 100 ) );

	for( auto &cell : Spreadsheet::CellPlug::Range( *rowsPlug->defaultRow()->cellsPlug() ) )
	{
		Metadata::registerValue( cell.get(), "spreadsheet:columnWidth", new IntData( 300 ) );
	}

	result->outPlug()->setInput( removeSet->outPlug() );

	return result;
}

EditScope::ProcessorRegistration g_setMembershipProcessorRegistration( "SetMembershipEdits", setMembershipProcessor );

}  // namespace

Gaffer::ValuePlug *EditScopeAlgo::acquireSetEdits( Gaffer::EditScope *scope, const std::string &set, bool createIfNecessary )
{
	Node *processor = scope->acquireProcessor( "SetMembershipEdits", createIfNecessary );

	if( !processor )
	{
		return nullptr;
	}

	auto rows = processor->getChild<Spreadsheet::RowsPlug>( "edits" );

	auto row = rows->row( set );

	if( !row && createIfNecessary )
	{
		row = rows->addRow();
		row->namePlug()->setValue( set );
	}

	return row ? row->cellsPlug() : nullptr;
}

void EditScopeAlgo::setSetMembership( Gaffer::EditScope *scope, const IECore::PathMatcher &paths, const std::string &set, EditScopeAlgo::SetMembership state )
{
	auto cells = EditScopeAlgo::acquireSetEdits( scope, set );

	auto addCell = cells->getChild<Spreadsheet::CellPlug>( g_addSetColumnIndex );
	auto removeCell = cells->getChild<Spreadsheet::CellPlug>( g_removeSetColumnIndex );

	auto addStringPlug = addCell->valuePlug<StringVectorDataPlug>();
	auto removeStringPlug = removeCell->valuePlug<StringVectorDataPlug>();

	auto row = cells->parent<Spreadsheet::RowPlug>();

	if( !row->enabledPlug()->getValue() )
	{
		row->enabledPlug()->setValue( true );
		addStringPlug->setValue( new StringVectorData() );
		removeStringPlug->setValue( new StringVectorData() );
	}

	ConstStringVectorDataPtr addData = addStringPlug->getValue();
	ConstStringVectorDataPtr removeData = removeStringPlug->getValue();

	PathMatcher addPaths( addData->readable().begin(), addData->readable().end() );
	PathMatcher removePaths( removeData->readable().begin(), removeData->readable().end() );

	if( state == EditScopeAlgo::SetMembership::Unchanged )
	{
		addPaths.removePaths( paths );
		removePaths.removePaths( paths );
	}
	else if( state == EditScopeAlgo::SetMembership::Added )
	{
		addPaths.addPaths( paths );
		removePaths.removePaths( paths );
	}
	else if( state == EditScopeAlgo::SetMembership::Removed )
	{
		addPaths.removePaths( paths );
		removePaths.addPaths( paths );
	}

	StringVectorDataPtr addResult = new StringVectorData;
	StringVectorDataPtr removeResult = new StringVectorData;

	addPaths.paths( addResult->writable() );
	removePaths.paths( removeResult->writable() );

	sort( addResult->writable().begin(), addResult->writable().end() );
	sort( removeResult->writable().begin(), removeResult->writable().end() );

	addStringPlug->setValue( addResult );
	removeStringPlug->setValue( removeResult );
}

EditScopeAlgo::SetMembership EditScopeAlgo::getSetMembership( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, const std::string &set )
{
	auto cells = EditScopeAlgo::acquireSetEdits( scope, set, false );
	if( !cells )
	{
		return EditScopeAlgo::SetMembership::Unchanged;
	}

	auto row = cells->parent<Spreadsheet::RowPlug>();
	if( !row->enabledPlug()->getValue() )
	{
		return EditScopeAlgo::SetMembership::Unchanged;
	}

	auto removeCell = row->cellsPlug()->getChild<Spreadsheet::CellPlug>( g_removeSetColumnIndex );
	auto removeStringPlug = removeCell->valuePlug<StringVectorDataPlug>();
	ConstStringVectorDataPtr removeData = removeStringPlug->getValue();
	PathMatcher removePaths( removeData->readable().begin(), removeData->readable().end() );

	if( removePaths.match( path ) == PathMatcher::ExactMatch )
	{
		return EditScopeAlgo::SetMembership::Removed;
	}

	auto addCell = row->cellsPlug()->getChild<Spreadsheet::CellPlug>( g_addSetColumnIndex );
	auto addStringPlug = addCell->valuePlug<StringVectorDataPlug>();
	ConstStringVectorDataPtr addData = addStringPlug->getValue();
	PathMatcher addPaths( addData->readable().begin(), addData->readable().end() );

	if( addPaths.match( path ) == PathMatcher::ExactMatch )
	{
		return EditScopeAlgo::SetMembership::Added;
	}

	return EditScopeAlgo::SetMembership::Unchanged;
}

const Gaffer::GraphComponent *EditScopeAlgo::setMembershipReadOnlyReason( const Gaffer::EditScope *scope, const std::string &set, EditScopeAlgo::SetMembership state )
{
	auto processor = const_cast<EditScope *>( scope )->acquireProcessor( "SetMembershipEdits", /* createIfNecessary */ false );
	if( !processor )
	{
		return MetadataAlgo::readOnlyReason( scope );
	}

	auto rows = processor->getChild<Spreadsheet::RowsPlug>( "edits" );

	auto row = rows->row( set );
	if( !row )
	{
		return MetadataAlgo::readOnlyReason( rows );
	}

	if( const auto reason = MetadataAlgo::readOnlyReason( row->cellsPlug() ) )
	{
		return reason;
	}

	for( auto columnIndex : { g_addSetColumnIndex, g_removeSetColumnIndex } )
	{
		auto cell = row->cellsPlug()->getChild<Spreadsheet::CellPlug>( columnIndex );
		if( MetadataAlgo::getReadOnly( cell ) )
		{
			return cell;
		}

		auto plug = cell->valuePlug<StringVectorDataPlug>();
		if( MetadataAlgo::getReadOnly( plug ) )
		{
			return plug;
		}
	}

	return nullptr;
}


// Options
// =======

namespace
{

const std::string g_optionProcessorName = "OptionEdits";
const std::string g_optionPrefix = "option:";

SceneProcessorPtr optionProcessor( const std::string &name )
{
	SceneProcessorPtr result = new SceneProcessor( name );

	OptionTweaksPtr optionTweaks = new OptionTweaks;
	result->addChild( optionTweaks );
	optionTweaks->inPlug()->setInput( result->inPlug() );
	optionTweaks->enabledPlug()->setInput( result->enabledPlug() );
	optionTweaks->ignoreMissingPlug()->setValue( true );

	PlugAlgo::promoteWithName( optionTweaks->tweaksPlug(), "edits" );

	result->outPlug()->setInput( optionTweaks->outPlug() );

	return result;
}

SceneProcessor *acquireOptionProcessor( EditScope *editScope, bool createIfNecessary )
{
	static bool isRegistered = false;
	if( !isRegistered )
	{
		EditScope::registerProcessor(
			g_optionProcessorName,
			[]() {
				return optionProcessor( g_optionProcessorName );
			}
		);

		isRegistered = true;
	}

	return editScope->acquireProcessor<SceneProcessor>( g_optionProcessorName, createIfNecessary );
}

ConstObjectPtr optionValue( const ScenePlug *scene, const std::string &option )
{
	auto options = scene->globals();

	ObjectPtr result = nullptr;

	const CompoundObject::ObjectMap &map = options->members();
	CompoundObject::ObjectMap::const_iterator it = map.find( g_optionPrefix + option );
	if( it != map.end() )
	{
		result = it->second;
	}
	else if( const auto defaultValue = Gaffer::Metadata::value( g_optionPrefix + option, "defaultValue" ) )
	{
		return defaultValue;
	}

	if( !result )
	{
		throw IECore::Exception( fmt::format( "Option \"{}\" does not exist", option ) );
	}

	return result;
}

/// \todo Finding a child tweak plug by the tweak name is needed in a few different
/// places (AttributeInspector, ParameterInspector). Consider adding this to TweaksPlug.

TweakPlug *tweakPlug( TweaksPlug *tweaks, const std::string &tweakName )
{
	for( auto &p : TweakPlug::Range( *tweaks ) )
	{
		if( p->namePlug()->getValue() == tweakName )
		{
			return p.get();
		}
	}
	return nullptr;
}

}  // namespace


bool GafferScene::EditScopeAlgo::hasOptionEdit( const Gaffer::EditScope *scope, const std::string &option )
{
	return acquireOptionEdit( const_cast<EditScope *>( scope ), option, /* createIfNecessary = */ false );
}

TweakPlug *GafferScene::EditScopeAlgo::acquireOptionEdit( Gaffer::EditScope *scope, const std::string &option, bool createIfNecessary )
{
	// If we need to create an edit, we'll need to do a compute to figure our the option
	// type and value. But we don't want to do that if we already have an edit. And since the
	// compute could error, we need to get the option value before making _any_ changes, so we
	// don't leave things in a partial state. We use `ensureOptionValue()` to get the value
	// lazily at the first point we know it will be needed.
	ConstDataPtr optionValue;
	auto ensureOptionValue = [&] {
		if( !optionValue )
		{
			optionValue = runTimeCast<const Data>(
				::optionValue( scope->outPlug<ScenePlug>(), option )
			);
			if( !optionValue )
			{
				throw IECore::Exception( fmt::format( "Option \"{}\" cannot be tweaked", option ) );
			}
		}
	};

	// Find processor

	auto *processor = acquireOptionProcessor( scope, /* createIfNecessary */ false );
	if( !processor )
	{
		if( !createIfNecessary )
		{
			return nullptr;
		}
		else
		{
			ensureOptionValue();
			processor = acquireOptionProcessor( scope, /* createIfNecessary */ true );
		}
	}

	auto *tweaks = processor->getChild<TweaksPlug>( "edits" );

	if( TweakPlug *tweak = tweakPlug( tweaks, option ) )
	{
		return tweak;
	}

	if( !createIfNecessary )
	{
		return nullptr;
	}

	// No tweak for the option yet. Create it.

	ensureOptionValue();

	ValuePlugPtr valuePlug = PlugAlgo::createPlugFromData( "value", Plug::In, Plug::Default, optionValue.get() );

	tweaks->addChild( new TweakPlug( option, valuePlug, TweakPlug::Create, false ) );

	return tweakPlug( tweaks, option );
}

void GafferScene::EditScopeAlgo::removeOptionEdit( Gaffer::EditScope *scope, const std::string &option )
{
	TweakPlug *edit = acquireOptionEdit( scope, option, /* createIfNecessary */ false );
	if( !edit )
	{
		return;
	}

	edit->parent()->removeChild( edit );
}

const Gaffer::GraphComponent *GafferScene::EditScopeAlgo::optionEditReadOnlyReason( const Gaffer::EditScope *scope, const std::string &option )
{
	auto *processor = acquireOptionProcessor( const_cast<EditScope *>( scope ), /*createIfNecessary */ false );
	if( !processor )
	{
		return MetadataAlgo::readOnlyReason( scope );
	}

	auto *tweaks = processor->getChild<TweaksPlug>( "edits" );
	if( !tweaks )
	{
		return MetadataAlgo::readOnlyReason( processor );
	}

	if( const auto reason = MetadataAlgo::readOnlyReason( tweaks ) )
	{
		return reason;
	}

	TweakPlug *tweak = tweakPlug( tweaks, option );
	if( tweak )
	{
		if( MetadataAlgo::getReadOnly( tweak ) )
		{
			return tweak;
		}
		for( const auto &plug : Plug::RecursiveRange( *tweak ) )
		{
			if( MetadataAlgo::getReadOnly( plug.get() ) )
			{
				return plug.get();
			}
		}
	}

	return nullptr;
}

// Render Pass Option Edits
// ========================

namespace
{

const std::string g_renderPassOptionProcessorName = "RenderPassOptionEdits";

SceneProcessorPtr renderPassOptionProcessor( const std::string &name )
{
	SceneProcessorPtr result = new SceneProcessor( name );

	SpreadsheetPtr spreadsheet = new Spreadsheet;
	result->addChild( spreadsheet );
	spreadsheet->selectorPlug()->setValue( "${renderPass}" );

	OptionTweaksPtr optionTweaks = new OptionTweaks;
	result->addChild( optionTweaks );
	optionTweaks->inPlug()->setInput( result->inPlug() );
	optionTweaks->enabledPlug()->setInput( result->enabledPlug() );
	optionTweaks->ignoreMissingPlug()->setValue( true );

	auto rowsPlug = static_cast<Spreadsheet::RowsPlug *>(
		PlugAlgo::promoteWithName( spreadsheet->rowsPlug(), "edits" )
	);
	Metadata::registerValue( rowsPlug, "spreadsheet:defaultRowVisible", new BoolData( false ) );
	Metadata::registerValue( rowsPlug->defaultRow(), "spreadsheet:rowNameWidth", new IntData( 150 ) );

	result->outPlug()->setInput( optionTweaks->outPlug() );

	return result;
}

SceneProcessor *acquireRenderPassOptionProcessor( EditScope *editScope, bool createIfNecessary )
{
	static bool isRegistered = false;
	if( !isRegistered )
	{
		EditScope::registerProcessor(
			g_renderPassOptionProcessorName,
			[]() {
				return renderPassOptionProcessor( g_renderPassOptionProcessorName );
			}
		);

		isRegistered = true;
	}

	return editScope->acquireProcessor<SceneProcessor>( g_renderPassOptionProcessorName, createIfNecessary );
}

}  // namespace

bool GafferScene::EditScopeAlgo::hasRenderPassOptionEdit( const Gaffer::EditScope *scope, const std::string &renderPass, const std::string &option )
{
	return acquireRenderPassOptionEdit( const_cast<EditScope *>( scope ), renderPass, option, /* createIfNecessary = */ false );
}

TweakPlug *GafferScene::EditScopeAlgo::acquireRenderPassOptionEdit( Gaffer::EditScope *scope, const std::string &renderPass, const std::string &option, bool createIfNecessary )
{
	// If we need to create an edit, we'll need to do a compute to figure our the option
	// type and value. But we don't want to do that if we already have an edit. And since the
	// compute could error, we need to get the option value before making _any_ changes, so we
	// don't leave things in a partial state. We use `ensureOptionValue()` to get the value
	// lazily at the first point we know it will be needed.
	ConstDataPtr optionValue;
	auto ensureOptionValue = [&] {
		if( !optionValue )
		{
			optionValue = runTimeCast<const Data>(
				::optionValue( scope->outPlug<ScenePlug>(), option )
			);
			if( !optionValue )
			{
				throw IECore::Exception( fmt::format( "Option \"{}\" cannot be tweaked", option ) );
			}
		}
	};

	// Find processor

	auto *processor = acquireRenderPassOptionProcessor( scope, /* createIfNecessary */ false );
	if( !processor )
	{
		if( !createIfNecessary )
		{
			return nullptr;
		}
		else
		{
			ensureOptionValue();
			processor = acquireRenderPassOptionProcessor( scope, /* createIfNecessary */ true );
		}
	}

	auto *rows = processor->getChild<Spreadsheet::RowsPlug>( "edits" );
	Spreadsheet::RowPlug *row = rows->row( renderPass );
	if( !row )
	{
		if( !createIfNecessary )
		{
			return nullptr;
		}
		ensureOptionValue();
		row = rows->addRow();
		row->namePlug()->setValue( renderPass );
	}

	// Find cell for option

	const std::string columnName = boost::replace_all_copy( option, ".", "_" );
	if( auto *cell = row->cellsPlug()->getChild<Spreadsheet::CellPlug>( columnName ) )
	{
		return cell->valuePlug<TweakPlug>();
	}

	if( !createIfNecessary )
	{
		return nullptr;
	}

	// No tweak for the option yet. Create it.

	ensureOptionValue();

	ValuePlugPtr valuePlug = PlugAlgo::createPlugFromData( "value", Plug::In, Plug::Default, optionValue.get() );

	TweakPlugPtr tweakPlug = new TweakPlug( option, valuePlug, TweakPlug::Create, false );

	auto *optionTweaks = processor->getChild<OptionTweaks>( "OptionTweaks" );
	optionTweaks->tweaksPlug()->addChild( tweakPlug );

	size_t columnIndex = rows->addColumn( tweakPlug.get(), columnName, /* adoptEnabledPlug */ true );
	tweakPlug->setInput( processor->getChild<Spreadsheet>( "Spreadsheet" )->outPlug()->getChild<Plug>( columnIndex ) );

	return row->cellsPlug()->getChild<Spreadsheet::CellPlug>( columnIndex )->valuePlug<TweakPlug>();
}

void GafferScene::EditScopeAlgo::removeRenderPassOptionEdit( Gaffer::EditScope *scope, const std::string &renderPass, const std::string &option )
{
	TweakPlug *edit = acquireRenderPassOptionEdit( scope, renderPass, option, /* createIfNecessary */ false );
	if( !edit )
	{
		return;
	}
	// We're unlikely to be able to delete the row or column,
	// because that would affect other edits, so we simply disable
	// the edit instead.
	edit->enabledPlug()->setValue( false );
}

const Gaffer::GraphComponent *GafferScene::EditScopeAlgo::renderPassOptionEditReadOnlyReason( const Gaffer::EditScope *scope, const std::string &renderPass, const std::string &option )
{
	auto *processor = acquireRenderPassOptionProcessor( const_cast<EditScope *>( scope ), /*createIfNecessary */ false );
	if( !processor )
	{
		return MetadataAlgo::readOnlyReason( scope );
	}

	auto *rows = processor->getChild<Spreadsheet::RowsPlug>( "edits" );
	Spreadsheet::RowPlug *row = rows->row( renderPass );
	if( !row )
	{
		return MetadataAlgo::readOnlyReason( rows );
	}

	if( const auto reason = MetadataAlgo::readOnlyReason( row->cellsPlug() ) )
	{
		return reason;
	}

	const std::string columnName = boost::replace_all_copy( option, ".", "_" );
	if( auto *cell = row->cellsPlug()->getChild<Spreadsheet::CellPlug>( columnName ) )
	{
		if( MetadataAlgo::getReadOnly( cell ) )
		{
			return cell;
		}

		for( const auto &plug : Plug::RecursiveRange( *cell ) )
		{
			if( MetadataAlgo::getReadOnly( plug.get() ) )
			{
				return plug.get();
			}
		}
	}

	return nullptr;
}

// Render Passes
// =============

namespace
{

const std::string g_renderPassesProcessorName = "RenderPasses";

SceneProcessorPtr renderPassesProcessor()
{
	return new RenderPasses( g_renderPassesProcessorName );
}

EditScope::ProcessorRegistration g_renderPassProcessorRegistration( g_renderPassesProcessorName, renderPassesProcessor );

} // namespace

const Gaffer::GraphComponent *GafferScene::EditScopeAlgo::renderPassesReadOnlyReason( const Gaffer::EditScope *scope )
{
	if( auto processor = const_cast<EditScope *>( scope )->acquireProcessor<RenderPasses>( g_renderPassesProcessorName, /* createIfNecessary = */ false ) )
	{
		return MetadataAlgo::readOnlyReason( processor->namesPlug() );
	}

	return MetadataAlgo::readOnlyReason( scope );
}
