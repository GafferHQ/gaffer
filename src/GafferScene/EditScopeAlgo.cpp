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
#include "GafferScene/Prune.h"
#include "GafferScene/PathFilter.h"
#include "GafferScene/SceneProcessor.h"
#include "GafferScene/ShaderTweaks.h"
#include "GafferScene/Transform.h"

#include "Gaffer/EditScope.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/Spreadsheet.h"
#include "Gaffer/StringPlug.h"

#include "IECore/AngleConversion.h"
#include "IECore/CamelCase.h"

#include "OpenEXR/ImathMatrixAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/replace.hpp"
#include "boost/container/flat_map.hpp"
#include "boost/tokenizer.hpp"

#include <unordered_map>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

// Pruning
// =======

namespace
{

/// \todo Make this into an API for clients to register attributes and corresponding
/// default values they want to make available. This is needed to get the value of an
/// attribute that _could_ exist if the user activates it, allowing it to be discovered
/// in clients of history related APIs such as `AttributeInspector`.
typedef std::unordered_map<std::string, const IECore::DataPtr> AttributeRegistry;
AttributeRegistry g_attributeRegistry {
	{ "gl:visualiser:scale", new IECore::FloatData( 1.0f ) },
	{ "gl:visualiser:maxTextureResolution", new IECore::IntData( 512 ) },
	{ "gl:visualiser:frustum", new IECore::StringData( "whenSelected" ) },
	{ "gl:light:frustumScale", new IECore::FloatData( 1.0f ) },
	{ "gl:light:drawingMode", new IECore::StringData( "texture" ) }
};

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
	const V3f pivot = this->pivot->getValue();
	M44f result;
	result.translate( pivot + translate->getValue() );
	result.rotate( IECore::degreesToRadians( rotate->getValue() ) );
	result.scale( scale->getValue() );
	result.translate( -pivot );
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
	{ "as", "Appleseed" },
	{ "gl", "OpenGL" },
	{ "osl", "OSL" },
	{ "cycles", "Cycles" }
};

string parameterProcessorName( const std::string &attribute )
{
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
		throw IECore::Exception( boost::str( boost::format( "Location \"%1%\" does not exist" ) % pathString ) );
	}

	auto attributes = scene->fullAttributes( path );

	ConstObjectPtr result = attributes->members()[attribute];

	if( !result )
	{
		AttributeRegistry::const_iterator registeredAttribute = g_attributeRegistry.find( attribute );
		if( registeredAttribute != g_attributeRegistry.end() )
		{
			return registeredAttribute->second;
		}

		throw IECore::Exception( boost::str( boost::format( "Attribute \"%s\" does not exist" ) % attribute ) );
	}

	return result;
}

ConstDataPtr parameterValue( const ScenePlug *scene, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter )
{
	auto attributeShader = attributeValue( scene, path, attribute );

	auto shaderNetwork = runTimeCast<const IECoreScene::ShaderNetwork>( attributeShader.get() );
	if( !shaderNetwork )
	{
		throw IECore::Exception( boost::str( boost::format( "Attribute \"%1%\" is not a shader" ) % attribute ) );
	}

	const IECoreScene::Shader *shader;
	if( parameter.shader.string().size() )
	{
		shader = shaderNetwork->getShader( parameter.shader );
		if( !shader )
		{
			throw IECore::Exception( boost::str( boost::format( "Shader \"%1%\" does not exist" ) % parameter.shader ) );
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
		throw IECore::Exception( boost::str( boost::format( "Parameter \"%1%\" does not exist" ) % parameter.name ) );
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

	string columnName = boost::replace_all_copy( tweakName, ".", "_" );
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
	string columnName = boost::replace_all_copy( tweakName, ".", "_" );
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
	attributeTweaks->enabledPlug()->setValue( result->enabledPlug() );
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
				throw IECore::Exception( boost::str( boost::format( "Attribute \"%s\" cannot be tweaked" ) % attribute ) );
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
	MetadataAlgo::copyIf(
		tweakPlug.get(), rows->defaultRow()->cellsPlug()->getChild<Spreadsheet::CellPlug>( columnIndex )->valuePlug(),
		[] ( const GraphComponent *from, const GraphComponent *to, const std::string &name ) {
			return boost::starts_with( name, "tweakPlugValueWidget:" );
		}
	);

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
