//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferSceneUI/Private/Inspector.h"

#include "GafferScene/TweakPlug.h"

#include "Gaffer/ScriptNode.h"
#include "Gaffer/Spreadsheet.h"

#include "boost/bind.hpp"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI::Private;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo Why would this walk past all the output plugs except the last one? I
/// suspect this wasn't the intention.
Gaffer::Plug *sourceInput( Gaffer::Plug *plug )
{
	Gaffer::Plug *result = plug;
	while( plug )
	{
		if( plug->direction() == Plug::In )
		{
			result = plug;
		}
		plug = plug->getInput();
	}

	return result;
}

/// \todo This is a modified copy of `TransformTool::spreadsheetAwareSource()`,
/// and is eerily similar to `Dispatcher::computedSource()` and others. This
/// needs factoring out into some general `contextAwareSource()` method that can
/// be shared by all these. In this case, we also need to make sure we never
/// return an output plug, such as when it is connected to an anim curve. This
/// seems to suggest that maybe there are two concepts? Something like a pure
/// `contextAwareSource()` and a `userEditableSource()`?
Gaffer::Plug *spreadsheetAwareSource( Gaffer::Plug *plug )
{
	if( auto sourceValuePlug = plug->source<ValuePlug>() )
	{
		if( auto spreadsheet = runTimeCast<Spreadsheet>( sourceValuePlug->node() ) )
		{
			if( spreadsheet->outPlug()->isAncestorOf( sourceValuePlug ) )
			{
				Gaffer::Plug *inPlug = spreadsheet->activeInPlug( sourceValuePlug );
				if( inPlug->ancestor<Spreadsheet::RowPlug>() == spreadsheet->rowsPlug()->defaultRow() )
				{
					// Don't want to edit the default row, as that could affect
					// all sorts of other things.
					return nullptr;
				}
				return sourceInput( inPlug );
			}
		}
	}

	return sourceInput( plug );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Inspector
//////////////////////////////////////////////////////////////////////////

Inspector::Inspector( const std::string &type, const std::string &name, const Gaffer::PlugPtr &editScope )
	:	m_type( type ), m_name( name ), m_editScope( editScope )
{
	if( editScope && editScope->node() )
	{
		editScope->node()->plugInputChangedSignal().connect(
			boost::bind( &Inspector::editScopeInputChanged, this, ::_1 )
		);
	}
}

const std::string &Inspector::type() const
{
	return m_type;
}

const std::string &Inspector::name() const
{
	return m_name;
}

Inspector::ResultPtr Inspector::inspect() const
{
	SceneAlgo::History::ConstPtr history = this->history();
	if( !history )
	{
		return nullptr;
	}

	ConstObjectPtr value = this->value( history.get() );

	ResultPtr result = new Result( value, targetEditScope() );
	inspectHistoryWalk( history.get(), result.get() );

	if( result->editScope() && !result->m_editScopeInHistory )
	{
		result->m_editFunction = boost::str(
			boost::format( "The target EditScope (%1%) is not in the scene history." )
				% result->editScope()->relativeName( result->editScope()->scriptNode() )
		);
		result->m_sourceType = Result::SourceType::Other;
	}

	if( !result->m_value && !result->editable() )
	{
		// The property doesn't exist, and there's no
		// way of making it.
		return nullptr;
	}

	return result;
}

Inspector::InspectorSignal &Inspector::dirtiedSignal()
{
	return m_dirtiedSignal;
}

void Inspector::inspectHistoryWalk( const GafferScene::SceneAlgo::History *history, Result *result ) const
{
	Node *node = history->scene->node();

	// If we haven't found the source yet, call `source()`
	// to see if we can find one here.

	if( !result->m_source && history->scene->direction() == Plug::Out )
	{
		if( auto dependencyNode = runTimeCast<DependencyNode>( node ) )
		{
			Context::Scope scope( history->context.get() );
			const BoolPlug *enabledPlug = dependencyNode->enabledPlug();
			if( !enabledPlug || enabledPlug->getValue() )
			{
				std::string editWarning;
				if( auto source = this->source( history, editWarning ) )
				{
					// We've found the source of the value we're inspecting.

					result->m_source = static_cast<ValuePlug *>( spreadsheetAwareSource( source.get() ) );

					if( result->m_editScope && result->m_editScopeInHistory )
					{
						result->m_sourceType = Result::SourceType::Upstream;
					}
					else if( result->m_editScope && node->ancestor<EditScope>() == result->m_editScope )
					{
						result->m_sourceType = Result::SourceType::EditScope;
						result->m_editScopeInHistory = true;
					}
					else if( result->m_editScope )
					{
						// We'll convert this to `Other` later if we don't
						// find the EditScope.
						result->m_sourceType = Result::SourceType::Downstream;
					}
					else
					{
						result->m_sourceType = Result::SourceType::Other;
					}

					// See if we can use it for editing

					if( !result->m_editScope || node->ancestor<EditScope>() == result->m_editScope )
					{
						result->m_editFunction = [source = result->m_source] () { return source; };
						result->m_editWarning = editWarning;
					}
				}
			}
		}
	}

	// Check to see if we're at the `targetEditScope()`.

	if( auto editScope = runTimeCast<EditScope>( node ) )
	{
		if( history->scene == editScope->inPlug() && editScope == result->m_editScope )
		{
			// We are leaving the target EditScope. We consider EditScopes on
			// the way out to allow other nodes within the scope to take
			// precedence. An existing edit in the scope will have been picked
			// up via `source()` already.
			//
			// \todo Should call `editFunction()` with the context from the
			// `outPlug()` of the EditScope - see TransformTool.
			result->m_editScopeInHistory = true;
			Context::Scope scope( history->context.get() );
			if( editScope->enabledPlug()->getValue() )
			{
				result->m_editFunction = editFunction( editScope, history );
				if( result->m_source && result->m_sourceType == Result::SourceType::Downstream )
				{
					const Node *downstreamNode = result->m_source->node();
					const auto *downstreamEditScope = downstreamNode->ancestor<EditScope>();
					downstreamNode = downstreamEditScope ? downstreamEditScope : downstreamNode;
					result->m_editWarning = boost::str(
						boost::format( "%1% has edits downstream in %2%." )
							% ( std::string( 1, std::toupper( type()[0] ) ) + type().substr( 1 ) )
							% downstreamNode->relativeName( downstreamNode->scriptNode() )
					);
				}
			}
			else
			{
				result->m_editFunction = boost::str(
					boost::format( "The target EditScope (%1%) is disabled." )
						% editScope->relativeName( editScope->scriptNode() )
				);
			}
		}
	}

	// If we haven't found the source and the EditScope, then recurse up the
	// history until we have.

	for( const auto &predecessor : history->predecessors )
	{
		if( result->m_source && ((bool)result->m_editScope == result->m_editScopeInHistory) )
		{
			return;
		}
		inspectHistoryWalk( predecessor.get(), result );
	}
}

Gaffer::ValuePlugPtr Inspector::source( const GafferScene::SceneAlgo::History *history, std::string &editWarning ) const
{
	return nullptr;
}

Inspector::EditFunctionOrFailure Inspector::editFunction( Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history ) const
{
	return "Editing not supported";
}

Gaffer::EditScope *Inspector::targetEditScope() const
{
	if( !m_editScope || !m_editScope->getInput() )
	{
		return nullptr;
	}

	return runTimeCast<EditScope>( m_editScope->getInput()->node() );
}

void Inspector::editScopeInputChanged( const Gaffer::Plug *plug )
{
	if( plug == m_editScope )
	{
		dirtiedSignal()( this );
	}
}

//////////////////////////////////////////////////////////////////////////
// Result
//////////////////////////////////////////////////////////////////////////

Inspector::Result::Result( const IECore::ConstObjectPtr &value, const Gaffer::EditScopePtr &editScope )
	:	m_value( value ), m_sourceType( SourceType::Other ), m_editScope( editScope ), m_editScopeInHistory( false )
{
}

const IECore::Object *Inspector::Result::value() const
{
	return m_value.get();
}

Gaffer::ValuePlug *Inspector::Result::source() const
{
	return m_source.get();
}

Gaffer::EditScope *Inspector::Result::editScope() const
{
	return m_editScope.get();
}

Inspector::Result::SourceType Inspector::Result::sourceType() const
{
	return m_sourceType;
}

bool Inspector::Result::editable() const
{
	return m_editFunction.which() == 0 && boost::get<EditFunction>( m_editFunction ) != nullptr;
}

std::string Inspector::Result::nonEditableReason() const
{
	if( m_editFunction.which() == 1 )
	{
		return boost::get<std::string>( m_editFunction );
	}

	return "";
}

Gaffer::ValuePlugPtr Inspector::Result::acquireEdit() const
{
	if( m_editFunction.which() == 0 )
	{
		return boost::get<EditFunction>( m_editFunction )();
	}

	throw IECore::Exception( "Not editable : " + boost::get<std::string>( m_editFunction ) );
}

std::string Inspector::Result::editWarning() const
{
	return m_editWarning;
}
