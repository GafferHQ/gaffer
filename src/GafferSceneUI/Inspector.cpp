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
#include "Gaffer/OptionalValuePlug.h"
#include "Gaffer/PathFilter.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Spreadsheet.h"
#include "Gaffer/TweakPlug.h"

#include "boost/bind/bind.hpp"

#include "fmt/format.h"

#include <mutex>
#include <thread>

using namespace boost::placeholders;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI::Private;

using ConstPredecessors = std::vector<const SceneAlgo::History *>;

static InternedString g_contextVariablesPropertyName( "history:contextVariables" );
static InternedString g_varyingContextVariablesPropertyName( "history:varyingContextVariables" );
static InternedString g_valuePropertyName( "history:value" );
static InternedString g_fallbackValuePropertyName( "history:fallbackValue" );
static InternedString g_operationPropertyName( "history:operation" );
static InternedString g_sourcePropertyName( "history:source" );
static InternedString g_editWarningPropertyName( "history:editWarning" );
static InternedString g_nodePropertyName( "history:node" );
static InternedString g_contextPropertyName( "history:context" );

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
/// and is eerily similar to `PlugAlgo::contextSensitiveSource()`, which handles
/// Switches and ContextProcessors too. It would be good if we could use
/// `contextSensitiveSource()`, but we also need to make sure we never
/// return an output plug, such as when it is connected to an anim curve. This
/// seems to suggest that maybe there are two concepts? Something like a pure
/// `contextSensitiveSource()` and a `userEditableSource()`?
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
	if( plug->direction() == Plug::Out )
	{
		return fmt::format(
			"{} is not editable.",
			plug->relativeName( plug->ancestor<ScriptNode>() )
		);
	}

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

bool canEdit( const Gaffer::ValuePlug *plug, const IECore::Object *value, std::string &failureReason )
{
	const IECore::Data *data = runTimeCast<const IECore::Data>( value );
	if( !data )
	{
		failureReason = fmt::format( "Unsupported value of type \"{}\".", value->typeName() );
		return false;
	}

	const ValuePlug *valuePlug;
	if( auto nameValuePlug = runTimeCast<const NameValuePlug>( plug ) )
	{
		valuePlug = runTimeCast<const ValuePlug>( nameValuePlug->valuePlug() );
	}
	else if( auto tweakPlug = runTimeCast<const TweakPlug>( plug ) )
	{
		valuePlug = tweakPlug->valuePlug();
	}
	else if( auto optionalValuePlug = runTimeCast<const OptionalValuePlug>( plug ) )
	{
		valuePlug = optionalValuePlug->valuePlug();
	}
	else
	{
		valuePlug = plug;
	}

	if( !valuePlug )
	{
		failureReason = "No plug found to edit.";
		return false;
	}

	if( !PlugAlgo::canSetValueFromData( valuePlug, data ) )
	{
		failureReason = fmt::format( "Data of type \"{}\" is not compatible.", value->typeName() );
		return false;
	}

	return true;
}

void edit( Gaffer::ValuePlug *plug, const IECore::Object *value )
{
	const IECore::Data *data = runTimeCast<const IECore::Data>( value );
	if( !data )
	{
		return;
	}

	ValuePlug *valuePlug;
	if( auto nameValuePlug = runTimeCast<NameValuePlug>( plug ) )
	{
		if( auto enabledPlug = nameValuePlug->enabledPlug() )
		{
			enabledPlug->setValue( true );
		}
		valuePlug = runTimeCast<ValuePlug>( nameValuePlug->valuePlug() );
	}
	else if( auto tweakPlug = runTimeCast<TweakPlug>( plug ) )
	{
		tweakPlug->enabledPlug()->setValue( true );
		tweakPlug->modePlug()->setValue( TweakPlug::Mode::Create );
		valuePlug = tweakPlug->valuePlug();
	}
	else if( auto optionalValuePlug = runTimeCast<OptionalValuePlug>( plug ) )
	{
		optionalValuePlug->enabledPlug()->setValue( true );
		valuePlug = optionalValuePlug->valuePlug();
	}
	else
	{
		valuePlug = plug;
	}

	if( !valuePlug )
	{
		throw IECore::Exception( "No plug found to edit" );
	}

	if( !PlugAlgo::setValueFromData( valuePlug, data ) )
	{
		throw IECore::Exception( fmt::format( "Data of type \"{}\" is not compatible.", value->typeName() ) );
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Inspector
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Inspector )

Inspector::Inspector( const std::vector<Gaffer::PlugPtr> &targets, const std::string &type, const std::string &name, const Gaffer::PlugPtr &editScope )
	:	m_targets( targets ), m_type( type ), m_name( name ), m_editScope( editScope )
{
	assert( !targets.empty() );
	for( const auto &target : targets )
	{
		// Check all targets are on the same node, as assumed by `plugDirtied()` and
		// `HistoryPath::cancellationSubject()`.
		if( target->node() != targets.front()->node() )
		{
			throw IECore::Exception( fmt::format( "Targets {} and {} are not on the same node", target->fullName(), targets.front()->fullName() ) );
		}
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

	ResultPtr result = new Result( this->value( history.get() ), targetEditScope() );
	if( !result->m_value )
	{
		result->m_fallbackValue = this->fallbackValue( history.get(), result->m_fallbackDescription );
		if( result->m_fallbackValue && result->m_fallbackDescription.empty() )
		{
			IECore::msg( IECore::Msg::Level::Error, "Inspector", "Fallback value without a description" );
		}
	}
	inspectHistoryWalk( history.get(), result.get() );

	if( !result->m_value && !result->m_fallbackValue && !result->editable() )
	{
		// The property doesn't exist, and there's no
		// way of making it.
		return nullptr;
	}

	// If we failed to initialise our editors, then initialise with failures
	// explaining why.
	if( !result->m_editors )
	{
		std::string formatString;
		if( !result->m_source )
		{
			formatString = "No editable source found in history.";
		}
		else if( result->m_editScope && !result->m_editScopeInHistory )
		{
			formatString = fmt::format(
				"The target edit scope {} is not in the scene history.",
				result->editScope()->relativeName( result->editScope()->scriptNode() )
			);
		}
		else if( !result->m_editScope )
		{
			const EditScope *sourceEditScope = result->m_source->ancestor<EditScope>();
			if( sourceEditScope )
			{
				formatString = fmt::format(
					"Source is in an EditScope. Change scope to {} to {{}}.",
					sourceEditScope->relativeName( sourceEditScope->scriptNode() )
				);
			}
		}

		result->m_editors = {
			fmt::format( formatString, "edit" ), "", fmt::format( formatString, "disable" ), nullptr, nullptr
		};
	}

	return result;
}

Inspector::InspectorSignal &Inspector::dirtiedSignal()
{
	if( !m_dirtiedSignal )
	{
		m_dirtiedSignal.emplace();

		// Connect to signals that allow us to emit `m_dirtiedSignal` when
		// necessary. We delay doing this until `dirtiedSignal()` is first
		// accessed for the sake of the SceneInspector. The SceneInspector
		// constructs Inspectors from background tasks, where connecting to
		// signals is not allowed, but it fortunately doesn't use
		// `dirtiedSignal()`.

		m_targets.front()->node()->plugDirtiedSignal().connect(
			boost::bind( &Inspector::plugDirtied, this, ::_1 )
		);

		Metadata::plugValueChangedSignal().connect( boost::bind( &Inspector::plugMetadataChanged, this, ::_3, ::_4 ) );
		Metadata::nodeValueChangedSignal().connect( boost::bind( &Inspector::nodeMetadataChanged, this, ::_2, ::_3 ) );

		if( m_editScope && m_editScope->node() )
		{
			m_editScope->node()->plugInputChangedSignal().connect(
				boost::bind( &Inspector::editScopeInputChanged, this, ::_1 )
			);
		}
	}
	return *m_dirtiedSignal;
}

void Inspector::inspectHistoryWalk( const GafferScene::SceneAlgo::History *history, Result *result ) const
{
	Node *node = history->scene->node();

	// If we might have a use for it, see if there's a source for the inspected
	// value at this point in the history.

	std::string editWarning;
	ValuePlugPtr source;
	if(
		history->scene->direction() == Plug::Out &&
		( !result->m_source || !result->m_editors )
	)
	{
		if( auto dependencyNode = runTimeCast<DependencyNode>( node ) )
		{
			Context::Scope scope( history->context.get() );
			const BoolPlug *enabledPlug = dependencyNode->enabledPlug();
			if( !enabledPlug || enabledPlug->getValue() )
			{
				source = this->source( history, editWarning );
				if( source )
				{
					source = static_cast<ValuePlug *>( spreadsheetAwareSource( source.get() ) );
				}
			}
		}
	}

	// If this is the first source we've seen, then initialise
	// `Result::source()` and `Result::sourceType()` from it.

	const bool hadSourceAlready = (bool)result->m_source;
	if( source && !hadSourceAlready )
	{
		result->m_source = source;

		if( result->m_editScope && result->m_editScopeInHistory )
		{
			result->m_sourceType = Result::SourceType::Upstream;
		}
		else if( result->m_editScope && node->ancestor<EditScope>() == result->m_editScope )
		{
			result->m_sourceType = Result::SourceType::EditScope;
			result->m_editScopeInHistory = true;
		}
		else
		{
			// We'll convert this to Downstream if we later find the edit scope.
			result->m_sourceType = Result::SourceType::Other;
		}
	}

	// If we haven't initialised the editors yet, see if we can do that here.

	if( !result->m_editors )
	{
		// Initialise editors from source if we can.
		if( source && source->ancestor<EditScope>() == result->m_editScope )
		{
			const std::string nonEditableReason = ::nonEditableReason( result->m_source.get() );
			if( nonEditableReason.empty() )
			{
				result->m_editors = {
					[source = source] ( bool unused ) { return source; },
					editWarning,
					disableEditFunction( source.get(), history ),
					canEditFunction( history ),
					editFunction( history )
				};
			}
			else
			{
				result->m_editors = { nonEditableReason, "", nonEditableReason, canEditFunction( history ), editFunction( history ) };
			}
		}
		// Otherwise try to initialise from EditScope if we've hit it.
		else if( auto editScope = runTimeCast<EditScope>( node ) )
		{
			if( !result->m_editScopeInHistory && history->scene == editScope->inPlug() && editScope == result->m_editScope )
			{
				// We are leaving the target EditScope for the first time. We
				// consider EditScopes on the way out to allow other nodes within
				// the scope to take precedence. An existing edit in the scope will
				// have been picked up via `source()` already.
				//
				// \todo Should call `acquireEditFunction()` with the context from the
				// `outPlug()` of the EditScope - see TransformTool. We should also
				// explicitly prefer branches where `scene:path` matches the value
				// in the `outPlug()` context, to avoid making edits to locations
				// other than the one emerging from the EditScope.
				result->m_editScopeInHistory = true;
				Context::Scope scope( history->context.get() );
				AcquireEditFunctionOrFailure func;
				if( editScope->enabledPlug()->getValue() )
				{
					func = acquireEditFunction( editScope, history );
				}
				else
				{
					func = fmt::format(
						"The target edit scope {} is disabled.",
						editScope->relativeName( editScope->scriptNode() )
					);
				}

				result->m_editors = {
					func, "",
					fmt::format(
						"There is no edit in {}.", editScope->relativeName( editScope->scriptNode() )
					),
					canEditFunction( history ),
					editFunction( history )
				};
			}
		}

		if( result->m_editors && hadSourceAlready )
		{
			result->m_sourceType = Result::SourceType::Downstream;
		}

		// If we initialised the acquire edit function, tag on a warning if any edits won't be visible
		// due to being overridden downstream.
		if( result->m_editors && std::holds_alternative<AcquireEditFunction>( result->m_editors->acquireEditFunction ) && result->m_sourceType == Result::SourceType::Downstream )
		{
			const Node *downstreamNode = result->m_source->node();
			const auto *downstreamEditScope = downstreamNode->ancestor<EditScope>();
			downstreamNode = downstreamEditScope ? downstreamEditScope : downstreamNode;
			result->m_editors->editWarning = fmt::format(
				"{} has edits downstream in {}.",
				std::string( 1, std::toupper( type()[0] ) ) + type().substr( 1 ),
				downstreamNode->relativeName( downstreamNode->scriptNode() )
			);
		}
	}

	// If we haven't found everything we want yet, then recurse up the history
	// until we have.

	for( const auto &predecessor : history->predecessors )
	{
		if( result->m_source && ((bool)result->m_editScope == result->m_editScopeInHistory) && result->m_editors )
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

Inspector::AcquireEditFunctionOrFailure Inspector::acquireEditFunction( Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history ) const
{
	return "Editing not supported";
}

Inspector::CanEditFunction Inspector::canEditFunction( const GafferScene::SceneAlgo::History *history ) const
{
	return [] ( const Gaffer::ValuePlug *plug, const IECore::Object *value, std::string &failureReason ) { return ::canEdit( plug, value, failureReason ); };
}

Inspector::EditFunction Inspector::editFunction( const GafferScene::SceneAlgo::History *history ) const
{
	return [] ( Gaffer::ValuePlug *plug, const IECore::Object *value ) { ::edit( plug, value ); };
}

Inspector::DisableEditFunctionOrFailure Inspector::disableEditFunction( Gaffer::ValuePlug *plug, const GafferScene::SceneAlgo::History *history ) const
{
	Gaffer::BoolPlugPtr enabledPlug;
	if( auto tweakPlug = runTimeCast<TweakPlug>( plug ) )
	{
		enabledPlug = tweakPlug->enabledPlug();
	}
	else if( auto nameValuePlug = runTimeCast<NameValuePlug>( plug ) )
	{
		enabledPlug = nameValuePlug->enabledPlug();
	}
	else if( auto optionalValuePlug = runTimeCast<OptionalValuePlug>( plug ) )
	{
		enabledPlug = optionalValuePlug->enabledPlug();
	}

	if( enabledPlug )
	{
		if( const GraphComponent *readOnlyReason = MetadataAlgo::readOnlyReason( enabledPlug.get() ) )
		{
			return fmt::format( "{} is locked.", readOnlyReason->relativeName( readOnlyReason->ancestor<ScriptNode>() ) );
		}
		else if( !enabledPlug->settable() )
		{
			return fmt::format( "{} is not settable.", enabledPlug->relativeName( enabledPlug->ancestor<ScriptNode>() ) );
		}
		else if( !enabledPlug->getValue() )
		{
			return fmt::format( "{} is not enabled.", enabledPlug->relativeName( enabledPlug->ancestor<ScriptNode>() ) );
		}
		else
		{
			return [ enabledPlug ] () { enabledPlug->setValue( false ); };
		}
	}
	else
	{
		return "Disabling edits not supported for this plug.";
	}
}

IECore::ConstObjectPtr Inspector::fallbackValue( const GafferScene::SceneAlgo::History *history, std::string &description ) const
{
	return nullptr;
}

Gaffer::EditScope *Inspector::targetEditScope() const
{
	if( !m_editScope || !m_editScope->getInput() )
	{
		return nullptr;
	}

	return PlugAlgo::findSource(
		m_editScope.get(),
		[] ( Plug *plug ) {
			return runTimeCast<EditScope>( plug->node() );
		}
	);
}


void Inspector::plugDirtied( Gaffer::Plug *plug )
{
	if( std::find( m_targets.begin(), m_targets.end(), plug ) != m_targets.end() )
	{
		dirtiedSignal()( this );
	}
}

void Inspector::plugMetadataChanged( IECore::InternedString key, const Gaffer::Plug *plug )
{
	if( !plug )
	{
		// Assume readOnly metadata is only registered on instances.
		return;
	}
	nodeMetadataChanged( key, plug->node() );
}

void Inspector::nodeMetadataChanged( IECore::InternedString key, const Gaffer::Node *node )
{
	if( !node )
	{
		// Assume readOnly metadata is only registered on instances.
		return;
	}

	EditScope *scope = targetEditScope();
	if( !scope )
	{
		return;
	}

	if(
		MetadataAlgo::readOnlyAffectedByChange( scope, node, key ) ||
		( MetadataAlgo::readOnlyAffectedByChange( key ) && scope->isAncestorOf( node ) )
	)
	{
		// Might affect `EditScopeAlgo::*ReadOnlyReason()` methods which we
		// expect derived classes to be calling.
		/// \todo Can we ditch the signal processing and call `attributeEditReadOnlyReason()`
		/// just-in-time from `editable()`? In the past that wasn't possible
		/// because editability changed the appearance of the UI, but it isn't
		/// doing that currently.
		dirtiedSignal()( this );
	}
}

void Inspector::editScopeInputChanged( const Gaffer::Plug *plug )
{
	if( plug == m_editScope )
	{
		dirtiedSignal()( this );
	}
}

PathPtr Inspector::historyPath() const
{
	return new Inspector::HistoryPath( this, new Context( *Context::current() ) );
}

//////////////////////////////////////////////////////////////////////////
// HistoryPath::HistoryProvider
//////////////////////////////////////////////////////////////////////////

// Generates the history for a HistoryPath. The same provider is shared
// between all children and copies of a path initially created by
// `Inspector::historyPath()`. The history is initialised when it is first
// required, allowing us to defer computation to the background task in
// PathListingWidget.
struct Inspector::HistoryPath::HistoryProvider
{

	HistoryProvider( const ConstInspectorPtr &inspector, const ConstContextPtr &context )
		:	inspector( inspector ), m_context( context ), m_constructorThreadId( std::this_thread::get_id() )
	{
	}

	const ConstInspectorPtr inspector;

	size_t historySize( const IECore::Canceller *canceller )
	{
		std::call_once( m_initFlag, &HistoryProvider::initHistory, this, canceller );
		return m_historyVector.size();
	}

	const SceneAlgo::History *historyItem( size_t index, const IECore::Canceller *canceller )
	{
		std::call_once( m_initFlag, &HistoryProvider::initHistory, this, canceller );
		return m_historyVector[index].get();
	}

	const StringVectorData *contextVariables( const IECore::Canceller *canceller )
	{
		std::call_once( m_initFlag, &HistoryProvider::initHistory, this, canceller );
		return m_contextVariables.get();
	}

	const StringVectorData *varyingContextVariables( const IECore::Canceller *canceller )
	{
		std::call_once( m_initFlag, &HistoryProvider::initHistory, this, canceller );
		return m_varyingContextVariables.get();
	}

	private :

		const ConstContextPtr m_context;
		std::thread::id m_constructorThreadId;

		void initHistory( const IECore::Canceller *canceller )
		{
			assert( m_historyVector.empty() );

			if( std::this_thread::get_id() == m_constructorThreadId )
			{
				// Our intention is that HistoryPath is constructed on the main
				// thread and then only ever evaluated in BackgroundTasks by a
				// PathListingWidget, to avoid blocking the UI. Warn if we fail
				// in this regard.
				IECore::msg( IECore::Msg::Warning, "HistoryPath", "Path evaluated on unexpected thread" );
			}

			Context::EditableScope scope( m_context.get() );
			if( canceller )
			{
				scope.setCanceller( canceller );
			}

			SceneAlgo::History::ConstPtr history = inspector->history();
			if( !history )
			{
				return;
			}

			std::string editWarning;

			std::unordered_set<InternedString> contextVariables;
			std::unordered_set<InternedString> varyingContextVariables;

			ConstObjectPtr successorValue;
			const SceneAlgo::History *successor = nullptr;
			const SceneAlgo::History *current = history.get();
			while( current )
			{
				Context::EditableScope scope( current->context.get() );
				if( canceller )
				{
					scope.setCanceller( canceller );
				}

				std::vector<InternedString> currentContextVariables;
				current->context->names( currentContextVariables );
				contextVariables.insert( currentContextVariables.begin(), currentContextVariables.end() );

				ConstObjectPtr currentValue = inspector->value( current );
				if( successor && !endsWith( m_historyVector, successor ) )
				{
					// The result of `inspector->source()` was null on the
					// previous (`successor`) iteration. But there may still
					// have been a value change at that point, in which case the
					// `successor` belongs in our history.
					if(
						(bool)currentValue != (bool)successorValue ||
						( currentValue && currentValue->isNotEqualTo( successorValue.get() ) )
					)
					{
						m_historyVector.push_back( successor );
					}
				}

				if( successor && *successor->context != *current->context )
				{
					addVaryingContextVariables( successor->context.get(), current->context.get(), varyingContextVariables );
					if( !endsWith( m_historyVector, successor ) )
					{
						m_historyVector.push_back( successor );
					}
				}

				if( inspector->source( current, editWarning ) )
				{
					m_historyVector.push_back( current );
				}

				if( current->predecessors.size() > 1 )
				{
					IECore::msg(
						IECore::Msg::Warning,
						"Inspector::HistoryPath",
						"Branching histories are not supported, using first predecessor history only."
					);
				}

				successor = current;
				successorValue = currentValue;
				current = current->predecessors.size() ? current->predecessors[0].get() : nullptr;
				if( !current && !endsWith( m_historyVector, successor ) )
				{
					// Make sure we include the tip of the history whether or not
					// there is an edit there. Among other things this allows us to
					// show where a value is loaded from a SceneReader.
					m_historyVector.push_back( successor );
				}
			}

			std::reverse( m_historyVector.begin(), m_historyVector.end() );
			m_contextVariables = new StringVectorData(
				std::vector<std::string>( contextVariables.begin(), contextVariables.end() )
			);
			m_varyingContextVariables = new StringVectorData(
				std::vector<std::string>( varyingContextVariables.begin(), varyingContextVariables.end() )
			);
		}

		static bool endsWith( const std::vector<SceneAlgo::History::ConstPtr> historyVector, const SceneAlgo::History *history )
		{
			return historyVector.size() && historyVector.back() == history;
		}

		static void addVaryingContextVariables( const Context *context0, const Context *context1, std::unordered_set<InternedString> &variables )
		{
			std::vector<InternedString> variableNames;
			context0->names( variableNames );
			context1->names( variableNames );
			for( auto variable : variableNames )
			{
				if( context0->variableHash( variable ) != context1->variableHash( variable ) )
				{
					variables.insert( variable );
				}
			}
		}

		std::once_flag m_initFlag;
		std::vector<SceneAlgo::History::ConstPtr> m_historyVector;
		ConstStringVectorDataPtr m_contextVariables;
		ConstStringVectorDataPtr m_varyingContextVariables;

};

//////////////////////////////////////////////////////////////////////////
// HistoryPath
//////////////////////////////////////////////////////////////////////////

Inspector::HistoryPath::HistoryPath(
	const ConstInspectorPtr &inspector,
	ConstContextPtr context,
	const std::string &path,
	PathFilterPtr filter
)
	:	Path( path, filter ), m_historyProvider( std::make_shared<HistoryProvider>( inspector, context ) )
{
}

Inspector::HistoryPath::HistoryPath(
	const HistoryProviderPtr &historyProvider,
	const std::string &path,
	PathFilterPtr filter
)
	:	Path( path, filter ), m_historyProvider( historyProvider )
{
}

Inspector::HistoryPath::~HistoryPath()
{

}

void Inspector::HistoryPath::propertyNames( std::vector<InternedString> &names, const Canceller *canceller ) const
{
	Path::propertyNames( names );

	if( this->names().empty() )
	{
		// Root
		names.push_back( g_contextVariablesPropertyName );
		names.push_back( g_varyingContextVariablesPropertyName );
	}

	if( history( canceller ) )
	{
		names.push_back( g_valuePropertyName );
		names.push_back( g_fallbackValuePropertyName );
		names.push_back( g_operationPropertyName);
		names.push_back( g_sourcePropertyName );
		names.push_back( g_editWarningPropertyName );
		names.push_back( g_nodePropertyName );
		names.push_back( g_contextPropertyName );
	}
}

ConstRunTimeTypedPtr Inspector::HistoryPath::property( const InternedString &name, const Canceller *canceller ) const
{
	if( name == g_contextVariablesPropertyName )
	{
		return names().empty() ? m_historyProvider->contextVariables( canceller ) : nullptr;
	}
	else if( name == g_varyingContextVariablesPropertyName )
	{
		return names().empty() ? m_historyProvider->varyingContextVariables( canceller ) : nullptr;
	}
	else if(
		name == g_nodePropertyName ||
		name == g_valuePropertyName ||
		name == g_fallbackValuePropertyName ||
		name == g_operationPropertyName ||
		name == g_sourcePropertyName ||
		name == g_editWarningPropertyName
	)
	{
		SceneAlgo::History::ConstPtr h = history( canceller );
		if( !h )
		{
			return nullptr;
		}

		if( name == g_nodePropertyName )
		{
			return h->scene->node();
		}

		Context::EditableScope scope( h->context.get() );
		if( canceller )
		{
			scope.setCanceller( canceller );
		}

		if( name == g_valuePropertyName )
		{
			return m_historyProvider->inspector->value( h.get() );
		}
		else if( name == g_fallbackValuePropertyName )
		{
			std::string fallbackDescription;
			return m_historyProvider->inspector->fallbackValue( h.get(), fallbackDescription );
		}

		std::string editWarning;
		ValuePlugPtr immediateSource = m_historyProvider->inspector->source( h.get(), editWarning );
		if( !immediateSource )
		{
			return nullptr;
		}

		ValuePlug *source = static_cast<ValuePlug *>( spreadsheetAwareSource( immediateSource.get() ) );
		if( name == g_sourcePropertyName )
		{
			return source;
		}
		else if( name == g_editWarningPropertyName )
		{
			return new StringData( editWarning );
		}
		else if( name == g_operationPropertyName )
		{
			if( auto tweakPlug = runTimeCast<const TweakPlug>( source ) )
			{
				return new IntData( tweakPlug->modePlug()->getValue() );
			}
			return new IntData( TweakPlug::Mode::Create );
		}
	}

	return Path::property( name, canceller );
}

Gaffer::ConstContextPtr Inspector::HistoryPath::contextProperty( const InternedString &name, const Canceller *canceller ) const
{
	if( name == g_contextPropertyName )
	{
		SceneAlgo::History::ConstPtr h = history( canceller );
		return h ? h->context : nullptr;
	}

	return Path::contextProperty( name, canceller );
}

bool Inspector::HistoryPath::isValid( const Canceller *canceller ) const
{
	return names().size() == 0 || history( canceller );
}

bool Inspector::HistoryPath::isLeaf( const Canceller *canceller ) const
{
	return names().size() == 1 && history( canceller );
}

PathPtr Inspector::HistoryPath::copy() const
{
	return new Inspector::HistoryPath( m_historyProvider, string(), const_cast<PathFilter *>( getFilter() ) );
}

const Gaffer::Plug *Inspector::HistoryPath::cancellationSubject() const
{
	return m_historyProvider->inspector->m_targets[0].get();
}

void Inspector::HistoryPath::doChildren( std::vector<PathPtr> &children, const Canceller *canceller) const
{
	if( names().size() != 0 )
	{
		return;
	}

	const size_t numChildren = m_historyProvider->historySize( canceller );
	for( size_t i = 0; i < numChildren; ++i )
	{
		children.push_back(
			new Inspector::HistoryPath( m_historyProvider, fmt::format( "/{}", i ) )
		);
	}
}

const GafferScene::SceneAlgo::History *Inspector::HistoryPath::history( const IECore::Canceller *canceller ) const
{
	if( names().size() != 1 )
	{
		return nullptr;
	}

	const std::string &s = names()[0].string();
	if( !s.size() )
	{
		return nullptr;
	}
	size_t index;
	if( std::from_chars( s.data(), s.data() + s.size(), index ).ptr != s.data() + s.size() )
	{
		return nullptr;
	}

	if( index >= m_historyProvider->historySize( canceller ) )
	{
		return nullptr;
	}
	return m_historyProvider->historyItem( index, canceller );
}

//////////////////////////////////////////////////////////////////////////
// Result
//////////////////////////////////////////////////////////////////////////

Inspector::Result::Result( const IECore::ConstObjectPtr &value, const Gaffer::EditScopePtr &editScope )
	:	m_value( value ), m_sourceType( SourceType::Other ), m_editScope( editScope ), m_editScopeInHistory( false )
{
}

const IECore::Object *Inspector::Result::value( bool useFallbacks ) const
{
	if( m_value )
	{
		return m_value.get();
	}

	return useFallbacks ? m_fallbackValue.get() : nullptr;
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

const std::string &Inspector::Result::fallbackDescription() const
{
	return m_fallbackDescription;
}

bool Inspector::Result::editable() const
{
	return m_editors && std::holds_alternative<AcquireEditFunction>( m_editors->acquireEditFunction );
}

std::string Inspector::Result::nonEditableReason( const IECore::Object *value ) const
{
	if( auto s = std::get_if<std::string>( &m_editors.value().acquireEditFunction ) )
	{
		return *s;
	}

	std::string reason;
	if( value && !canEdit( value, reason ) )
	{
		return reason;
	}

	return "";
}

Gaffer::ValuePlugPtr Inspector::Result::acquireEdit( bool createIfNecessary ) const
{
	if( auto f = std::get_if<AcquireEditFunction>( &m_editors.value().acquireEditFunction ) )
	{
		return (*f)( createIfNecessary );
	}

	throw IECore::Exception( "Not editable : " + std::get<std::string>( m_editors.value().acquireEditFunction ) );
}

bool Inspector::Result::canDisableEdit() const
{
	return std::holds_alternative<DisableEditFunction>( m_editors.value().disableEditFunction );
}

std::string Inspector::Result::nonDisableableReason() const
{
	if( auto s = std::get_if<std::string>( &m_editors.value().disableEditFunction ) )
	{
		return *s;
	}

	return "";
}

void Inspector::Result::disableEdit() const
{
	if( auto f = std::get_if<DisableEditFunction>( &m_editors.value().disableEditFunction ) )
	{
		return (*f)();
	}

	throw IECore::Exception( "Cannot disable edit : " + std::get<std::string>( m_editors.value().disableEditFunction ) );
}

std::string Inspector::Result::editWarning() const
{
	return m_editors.value().editWarning;
}

bool Inspector::Result::canEdit( const IECore::Object *value, std::string &failureReason ) const
{
	if( !m_editors || !m_editors->editFunction || !m_editors->canEditFunction )
	{
		failureReason = "Direct editing is not supported.";
		return false;
	}

	ValuePlugPtr plug;
	if( auto f = std::get_if<AcquireEditFunction>( &m_editors.value().acquireEditFunction ) )
	{
		// Attempt to acquire an existing edit to test against.
		plug = (*f)( /* createIfNecessary = */ false );

		if( !plug )
		{
			if( const IECore::Data *currentData = runTimeCast<const IECore::Data>( Result::value() ) )
			{
				// If we can't acquire an existing edit, create a temporary plug based on the current
				// value to avoid creating an edit.
				plug = PlugAlgo::createPlugFromData( "value", Plug::In, Plug::Default, currentData );
			}
		}
	}
	else
	{
		failureReason = nonEditableReason();
		return false;
	}

	return m_editors->canEditFunction( plug.get(), value, failureReason );
}

void Inspector::Result::edit( const IECore::Object *value ) const
{
	std::string reason;
	if( !canEdit( value, reason ) )
	{
		throw IECore::Exception( "Not editable : " + reason );
	}

	m_editors->editFunction( acquireEdit( /* createIfNecessary = */ true ).get(), value );
}
