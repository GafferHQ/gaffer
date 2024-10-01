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

#include "Gaffer/Animation.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/PathFilter.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Spreadsheet.h"
#include "Gaffer/TweakPlug.h"

#include "boost/bind/bind.hpp"

#include "fmt/format.h"

using namespace boost::placeholders;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI::Private;

using ConstPredecessors = std::vector<const SceneAlgo::History *>;

static InternedString g_valuePropertyName( "history:value" );
static InternedString g_operationPropertyName( "history:operation" );
static InternedString g_sourcePropertyName( "history:source" );
static InternedString g_editWarningPropertyName( "history:editWarning" );
static InternedString g_nodePropertyName( "history:node" );

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
				return sourceInput( spreadsheet->activeInPlug( sourceValuePlug ) );
			}
		}
	}

	return sourceInput( plug );
}

std::string nonEditableReason( const ValuePlug *plug )
{
	const ValuePlug *sourcePlug = ( plug && Animation::isAnimated( plug ) ) ? plug->source<ValuePlug>() : plug;

	const GraphComponent *readOnlyReason = MetadataAlgo::readOnlyReason( sourcePlug );
	if( readOnlyReason )
	{
		return fmt::format(
			"{} is locked.",
			readOnlyReason->relativeName( readOnlyReason->ancestor<ScriptNode>() )
		);
	}

	if( sourcePlug->getInput() )
	{
		return fmt::format(
			"{} has a non-settable input.",
			sourcePlug->relativeName( sourcePlug->ancestor<ScriptNode>() )
		);
	}

	if( auto spreadsheet = runTimeCast<const Spreadsheet>( plug->node() ) )
	{
		if( plug->ancestor<Spreadsheet::RowPlug>() == spreadsheet->rowsPlug()->defaultRow() )
		{
			// Don't want to edit the default row, as that could affect
			// all sorts of other things.
			return fmt::format(
				"{} is a spreadsheet default row.",
				plug->relativeName( plug->ancestor<ScriptNode>() )
			);
		}
	}

	for( const auto &c : ValuePlug::Range( *plug ) )
	{
		const std::string result = nonEditableReason( c.get() );
		if( !result.empty() )
		{
			return result;
		}
	}

	return "";
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
	bool fallbackValue = false;
	if( !value )
	{
		value = this->fallbackValue();
		fallbackValue = (bool)value;
	}

	ResultPtr result = new Result( value, targetEditScope() );
	inspectHistoryWalk( history.get(), result.get() );

	if( !result->m_value && !result->editable() )
	{
		// The property doesn't exist, and there's no
		// way of making it.
		return nullptr;
	}

	if( result->editScope() && !result->m_editScopeInHistory )
	{
		result->m_editFunction = fmt::format(
			"The target EditScope ({}) is not in the scene history.",
			result->editScope()->relativeName( result->editScope()->scriptNode() )
		);
		result->m_sourceType = Result::SourceType::Other;
	}

	else if( !result->m_source && !result->editable() )
	{
		// There's no source plug and no way of making
		// the property.
		result->m_editFunction = "No editable source found in history.";
	}

	if( fallbackValue )
	{
		result->m_sourceType = Result::SourceType::Fallback;
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
						const std::string nonEditableReason = ::nonEditableReason( result->m_source.get() );

						if( nonEditableReason.empty() )
						{
							result->m_editFunction = [source = result->m_source] () { return source; };
							result->m_editWarning = editWarning;
						}
						else
						{
							result->m_editFunction = nonEditableReason;
						}
					}
				}
			}
		}
	}

	// Check to see if we're at the `targetEditScope()`.

	if( auto editScope = runTimeCast<EditScope>( node ) )
	{
		if( !result->m_editScopeInHistory && history->scene == editScope->inPlug() && editScope == result->m_editScope )
		{
			// We are leaving the target EditScope for the first time. We
			// consider EditScopes on the way out to allow other nodes within
			// the scope to take precedence. An existing edit in the scope will
			// have been picked up via `source()` already.
			//
			// \todo Should call `editFunction()` with the context from the
			// `outPlug()` of the EditScope - see TransformTool. We should also
			// explicitly prefer branches where `scene:path` matches the value
			// in the `outPlug()` context, to avoid making edits to locations
			// other than the one emerging from the EditScope.
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
					result->m_editWarning = fmt::format(
						"{} has edits downstream in {}.",
						std::string( 1, std::toupper( type()[0] ) ) + type().substr( 1 ),
						downstreamNode->relativeName( downstreamNode->scriptNode() )
					);
				}
			}
			else
			{
				result->m_editFunction = fmt::format(
					"The target EditScope ({}) is disabled.",
					editScope->relativeName( editScope->scriptNode() )
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

IECore::ConstObjectPtr Inspector::fallbackValue() const
{
	return nullptr;
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

PathPtr Inspector::historyPath()
{
	return new Inspector::HistoryPath( this, new Context( *Context::current() ) );
}

//////////////////////////////////////////////////////////////////////////
// HistoryPath
//////////////////////////////////////////////////////////////////////////

Inspector::HistoryPath::HistoryPath(
	const InspectorPtr inspector,
	ConstContextPtr context,
	const std::string &path,
	PathFilterPtr filter
) :
	Path( path, filter ),
	m_inspector( inspector ),
	m_context( context ),
	m_plugMap()
{
	assert( m_inspector );
	assert( m_context );

	pathChangedSignal().connectFront( boost::bind( &Inspector::HistoryPath::pathChanged, this, ::_1 ) );
}

Inspector::HistoryPath::HistoryPath(
	const InspectorPtr inspector,
	ConstContextPtr context,
	PlugMap plugMap,
	const std::string &path,
	PathFilterPtr filter
) : Path( path, filter ),
	m_inspector( inspector ),
	m_context( context ),
	m_plugMap( plugMap )
{
	assert( m_inspector );
	assert( m_context );
}

Inspector::HistoryPath::~HistoryPath()
{

}

void Inspector::HistoryPath::propertyNames( std::vector<InternedString> &names, const Canceller *canceller) const
{
	Path::propertyNames( names );

	if( isLeaf() )
	{
		names.push_back( g_valuePropertyName );
		names.push_back( g_operationPropertyName);
		names.push_back( g_sourcePropertyName );
		names.push_back( g_editWarningPropertyName );
		names.push_back( g_nodePropertyName );
	}
}

ConstRunTimeTypedPtr Inspector::HistoryPath::property( const InternedString &name, const Canceller *canceller) const
{
	if( m_plugMap.size() == 0 )
	{
		updatePlugMap();
	}

	if( isLeaf() && name == g_nodePropertyName )
	{
		// Remove the plug name from the end.
		PlugMap::iterator it = m_plugMap.find( names()[0].string() );

		return it->history->scene->node();
	}

	if(
		isLeaf() && (
			name == g_valuePropertyName ||
			name == g_operationPropertyName ||
			name == g_sourcePropertyName ||
			name == g_editWarningPropertyName
		)
	)
	{
		PlugMap::iterator it = m_plugMap.find( names()[0].string() );

		std::string editWarning;

		Context::Scope currentScope( it->history->context.get() );

		if( ValuePlugPtr immediateSource = m_inspector->source( it->history.get(), editWarning ) )
		{
			ValuePlug *source = static_cast<ValuePlug *>( spreadsheetAwareSource( immediateSource.get() ) );

			if( name == g_valuePropertyName )
			{
				return runTimeCast<const IECore::Data>( m_inspector->value( it->history.get() ) );
			}
			else if( name == g_operationPropertyName )
			{
				if( auto tweakPlug = runTimeCast<const TweakPlug>( source ) )
				{
					return new IntData( tweakPlug->modePlug()->getValue() );
				}
				return new IntData( TweakPlug::Mode::Create );
			}
			else if( name == g_sourcePropertyName )
			{
				return source;
			}
			else if( name == g_editWarningPropertyName )
			{
				return new StringData( editWarning );
			}
		}
	}

	return Path::property( name );
}

bool Inspector::HistoryPath::isValid( const Canceller *canceller ) const
{
	if( names().size() == 0 )
	{
		return true;
	}
	return m_plugMap.find( names()[0].string() ) != m_plugMap.end();
}

bool Inspector::HistoryPath::isLeaf( const Canceller *canceller ) const
{
	return isValid() && names().size() > 0;
}

PathPtr Inspector::HistoryPath::copy() const
{
	return new Inspector::HistoryPath( m_inspector, m_context, m_plugMap, string(), const_cast<PathFilter *>( getFilter() ) );
}

void Inspector::HistoryPath::pathChanged( Path *path )
{
	updatePlugMap();
}

void Inspector::HistoryPath::doChildren( std::vector<PathPtr> &children, const Canceller *canceller) const
{
	if( m_plugMap.size() == 0 )
	{
		updatePlugMap();
	}

	if( isLeaf() || m_plugMap.size() == 0 )
	{
		return;
	}

	std::string editWarning;
	const auto &rand_index = m_plugMap.get<1>();
	for( size_t i = 0; i < rand_index.size(); ++i )
	{
		children.push_back(
			new Inspector::HistoryPath(
				m_inspector,
				m_context,
				m_plugMap,
				std::string( "/" ) + rand_index[i].hashString
			)
		);
	}
}

void Inspector::HistoryPath::updatePlugMap() const
{
	m_plugMap.clear();

	Context::Scope currentScope( m_context.get() );
	SceneAlgo::History::ConstPtr history = m_inspector->history();

	if( !history )
	{
		return;
	}
	assert( history->scene );

	std::string editWarning;

	while( true )
	{
		Context::Scope currentScope( history->context.get() );

		if( ValuePlugPtr immediateSource = m_inspector->source( history.get(), editWarning ) )
		{
			ValuePlugPtr source = runTimeCast<ValuePlug>( spreadsheetAwareSource( immediateSource.get() ) );
			MurmurHash h;
			h.append( (uintptr_t)source.get() );
			h.append( history->context->hash() );
			m_plugMap.insert( { h.toString(), history } );
		}

		if( history->predecessors.size() == 0 )
		{
			break;
		}

		else if( history->predecessors.size() > 1 )
		{
			IECore::msg(
				IECore::Msg::Warning,
				"Inspector::HistoryPath",
				"Branching histories are not supported, using first predecessor history only."
			);
		}

		history = history->predecessors[0];
	}

	m_plugMap.get<1>().reverse();
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
