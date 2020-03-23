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

#include "GafferScene/Prune.h"
#include "GafferScene/PathFilter.h"
#include "GafferScene/SceneProcessor.h"
#include "GafferScene/Transform.h"

#include "Gaffer/EditScope.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/Spreadsheet.h"
#include "Gaffer/StringPlug.h"

#include "IECore/AngleConversion.h"

#include "OpenEXR/ImathMatrixAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

// Pruning
// =======

namespace
{

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
	pathFilter->pathsPlug()->setInput( spreadsheet->activeRowNamesPlug() );

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

	PlugAlgo::promoteWithName( spreadsheet->rowsPlug(), "edits" );
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

boost::optional<GafferScene::EditScopeAlgo::TransformEdit> GafferScene::EditScopeAlgo::acquireTransformEdit( Gaffer::EditScope *scope, const ScenePlug::ScenePath &path, bool createIfNecessary )
{
	string pathString;
	ScenePlug::pathToString( path, pathString );

	auto *processor = scope->acquireProcessor<SceneProcessor>( "TransformEdits", createIfNecessary );
	if( !processor )
	{
		return boost::none;
	}

	auto *rows = processor->getChild<Spreadsheet::RowsPlug>( "edits" );
	Spreadsheet::RowPlug *row = rows->row( pathString );
	if( !row )
	{
		if( !createIfNecessary )
		{
			return boost::none;
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
