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

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

using ConstPredecessors = std::vector<const SceneAlgo::History *>;

const InternedString g_contextVariablesPropertyName( "history:contextVariables" );
const InternedString g_varyingContextVariablesPropertyName( "history:varyingContextVariables" );
const InternedString g_valuePropertyName( "history:value" );
const InternedString g_fallbackValuePropertyName( "history:fallbackValue" );
const InternedString g_operationPropertyName( "history:operation" );
const InternedString g_editPropertyName( "history:edit" );
const InternedString g_nodePropertyName( "history:node" );
const InternedString g_contextPropertyName( "history:context" );

const std::thread::id g_mainThreadId = std::this_thread::get_id();

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

std::string nonAcquireableReason( const ValuePlug *plug )
{
	if( auto spreadsheet = runTimeCast<const Spreadsheet>( plug->node() ) )
	{
		if( plug->ancestor<Spreadsheet::RowPlug>() == spreadsheet->rowsPlug()->defaultRow() )
		{
			// Don't want to show the default row, as that could silently affect
			// all sorts of other things.
			return fmt::format(
				"{} is a spreadsheet default row.",
				plug->relativeName( plug->ancestor<ScriptNode>() )
			);
		}
	}

	return "";
}

std::string nonEditableReason( const ValuePlug *plug )
{
	const std::string nonAcquireableReason = ::nonAcquireableReason( plug );
	if( !nonAcquireableReason.empty() )
	{
		return nonAcquireableReason;
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

void setPlugValue( ValuePlug *plug, const IECore::Object *value, bool dryRun )
{
	ValuePlug *valuePlug;
	BoolPlug *enabledPlug = nullptr;
	IntPlug *modePlug = nullptr;
	if( auto nameValuePlug = runTimeCast<NameValuePlug>( plug ) )
	{
		valuePlug = runTimeCast<ValuePlug>( nameValuePlug->valuePlug() );
		enabledPlug = nameValuePlug->enabledPlug();
	}
	else if( auto tweakPlug = runTimeCast<TweakPlug>( plug ) )
	{
		valuePlug = tweakPlug->valuePlug();
		enabledPlug = tweakPlug->enabledPlug();
		modePlug = tweakPlug->modePlug();
	}
	else if( auto optionalValuePlug = runTimeCast<OptionalValuePlug>( plug ) )
	{
		valuePlug = optionalValuePlug->valuePlug();
		enabledPlug = optionalValuePlug->enabledPlug();
	}
	else
	{
		valuePlug = plug;
	}

	if( !valuePlug )
	{
		throw Inspector::EditDisallowed( "No plug found to edit." );
	}

	for( auto plugToCheck : { valuePlug, static_cast<ValuePlug *>( enabledPlug ), static_cast<ValuePlug *>( modePlug ) } )
	{
		if( plugToCheck )
		{
			std::string nonEditableReason = ::nonEditableReason( plugToCheck );
			if( !nonEditableReason.empty() )
			{
				throw Inspector::EditDisallowed( nonEditableReason );
			}
		}
	}

	const IECore::Data *data = runTimeCast<const IECore::Data>( value );
	if( !data || !PlugAlgo::canSetValueFromData( valuePlug, data ) )
	{
		throw Inspector::EditDisallowed( fmt::format( "Data of type \"{}\" is not compatible.", value->typeName() ) );
	}

	if( dryRun )
	{
		return;
	}

	if( enabledPlug )
	{
		enabledPlug->setValue( true );
	}
	if( modePlug )
	{
		modePlug->setValue( TweakPlug::Mode::Create );
	}
	PlugAlgo::setValueFromData( valuePlug, data );
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
	if( std::this_thread::get_id() != g_mainThreadId && !Context::current()->canceller() )
	{
		IECore::msg( IECore::Msg::Warning, "Inspector::inspect", fmt::format( "No canceller for background inspection of {}", m_targets[0]->fullName() ) );
	}

	SceneAlgo::History::ConstPtr history = this->history();
	if( !history )
	{
		// \todo : Now that we no longer return nullptr for any other reason, it might make sense to
		// change this as well, and always return a valid result.
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
	inspectHistoryWalk( history.get(), result.get(), Context::current()->canceller() );

	if( !result->m_value && result->m_sourceType == Result::SourceType::Other )
	{
		// Special source type if there's no value, and we didn't find an edit scope that
		// could be used to create it.
		result->m_sourceType = Result::SourceType::None;
	}

	// If we failed to initialise our editors, then initialise with failures
	// explaining why.
	if( !result->m_editors )
	{
		std::string formatString;
		if( result->m_editScope && !result->m_editScopeInHistory )
		{
			formatString = fmt::format(
				"The target edit scope {} is not in the scene history.",
				result->editScope()->relativeName( result->editScope()->scriptNode() )
			);
		}
		else if( !result->m_source )
		{
			formatString = "No editable source found in history.";
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
		result->m_editors = Result::Editors( formatString );
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

void Inspector::inspectHistoryWalk( const GafferScene::SceneAlgo::History *history, Result *result, const IECore::Canceller *canceller ) const
{
	IECore::Canceller::check( canceller );
	Node *node = history->scene->node();

	Context::EditableScope scope( history->context.get() );
	scope.setCanceller( canceller );

	// If we might have a use for it, see if there's a source for the inspected
	// value at this point in the history.

	ValuePlugPtr source;
	if(
		history->scene->direction() == Plug::Out &&
		( !result->m_source || !result->m_editors )
	)
	{
		if( hasEdit( history ) )
		{
			source = history->scene;
		}
	}

	// If this is the first source we've seen, then initialise
	// `Result::source()` and `Result::sourceType()` from it.

	const bool hadSourceAlready = (bool)result->m_source;
	if( source && !hadSourceAlready )
	{
		result->m_source = source;

		if( !source->ancestor<ScriptNode>() )
		{
			result->m_sourceType = Result::SourceType::External;
		}
		else if( result->m_editScope && result->m_editScopeInHistory )
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
		if( source && source->ancestor<EditScope>() == result->m_editScope && !source->ancestor<ScriptNode>() )
		{
			// Source is a node internal to the UI, which the user has no business editing.
			const GraphComponent *settingsNode = source->ancestor( RunTimeTyped::typeIdFromTypeName( "GafferUI::Editor::Settings" ) );
			const std::string reason = fmt::format(
				"{} is external to the script.",
				MetadataAlgo::firstViewableNode( source.get() )->relativeName( settingsNode )
			);
			result->m_editors = Result::Editors( reason );
		}
		else if( source && source->ancestor<EditScope>() == result->m_editScope )
		{
			auto acquireEditFunction = [inspector = ConstInspectorPtr( this ), history = GafferScene::SceneAlgo::History::ConstPtr( history )] ( bool createIfNecessary, bool dryRun ) -> ValuePlugPtr {
				Context::Scope scope( history->context.get() );
				if( ValuePlugPtr p = inspector->acquireEdit( history.get(), createIfNecessary, dryRun ) )
				{
					p = static_cast<ValuePlug *>( spreadsheetAwareSource( p.get() ) );
					// It's not ideal that we do this check _after_ we've potentially created
					// a new plug, but we don't want derived classes to be on the hook for calling
					// `spreadsheetAwareSource()`. It seems reasonable to assume that newly created
					// plugs would always pass the check anyway.
					const std::string r = nonAcquireableReason( p.get() );
					if( !r.empty() )
					{
						throw EditDisallowed( r );
					}
					return p;
				}

				return nullptr;
			};

			auto editFunction = [inspector = ConstInspectorPtr( this ), history = GafferScene::SceneAlgo::History::ConstPtr( history )] ( const IECore::Object *value, bool dryRun ) {
				Context::Scope scope( history->context.get() );
				inspector->edit( value, history.get(), dryRun );
			};

			auto disableEditFunction = [inspector = ConstInspectorPtr( this ), history = GafferScene::SceneAlgo::History::ConstPtr( history )] ( bool dryRun ) {
				Context::Scope scope( history->context.get() );
				inspector->disableEdit( history.get(), dryRun );
			};

			result->m_editors = Result::Editors( acquireEditFunction, editFunction, disableEditFunction );
		}
		// Otherwise try to initialise from EditScope if we've hit it.
		else if( auto editScope = runTimeCast<EditScope>( node ) )
		{
			if( !result->m_editScopeInHistory && history->scene == editScope->inPlug() && editScope == result->m_editScope )
			{
				// We are leaving the target EditScope for the first time. We
				// consider EditScopes on the way out to allow other nodes within
				// the scope to take precedence. An existing edit in the scope will
				// have been picked up in the block above already.
				//
				// \todo Should call `acquireEdit()` with the context from the
				// `outPlug()` of the EditScope - see TransformTool. We should also
				// explicitly prefer branches where `scene:path` matches the value
				// in the `outPlug()` context, to avoid making edits to locations
				// other than the one emerging from the EditScope.
				result->m_editScopeInHistory = true;
				if( editScope->enabledPlug()->getValue() )
				{
					result->m_editors = Result::Editors(
						/* acquireEditFunction = */ [ inspector = ConstInspectorPtr( this ), editScope = EditScopePtr( editScope ), history = SceneAlgo::History::ConstPtr( history ) ] ( bool createIfNecessary, bool dryRun ) {
							Context::Scope scope( history->context.get() );
							return inspector->acquireEdit( editScope.get(), history.get(), createIfNecessary, dryRun );
						},
						/* editFunction = */ [inspector = ConstInspectorPtr( this ), editScope = EditScopePtr( editScope ), history = SceneAlgo::History::ConstPtr( history ) ] ( const IECore::Object *value, bool dryRun ) {
							Context::Scope scope( history->context.get() );
							inspector->edit( value, editScope.get(), history.get(), dryRun );
						},
						/* disableEditFunction = */ [ inspector = ConstInspectorPtr( this ), editScope = EditScopePtr( editScope ), history = SceneAlgo::History::ConstPtr( history ) ] ( bool dryRun ) {
							Context::Scope scope( history->context.get() );
							inspector->disableEdit( editScope.get(), history.get(), dryRun );
						}
					);
				}
				else
				{
					const std::string reason = fmt::format(
						"The target edit scope {} is disabled.",
						editScope->relativeName( editScope->scriptNode() )
					);
					result->m_editors = Result::Editors( reason );
				}
			}
		}

		if( result->m_editors && hadSourceAlready && result->m_sourceType != Result::SourceType::External )
		{
			result->m_sourceType = Result::SourceType::Downstream;
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
		inspectHistoryWalk( predecessor.get(), result, canceller );
	}
}

bool Inspector::hasEdit( const GafferScene::SceneAlgo::History *history ) const
{
	if( acquireEdit( history, /* createIfNecessary = */ false, /* dryRun = */ true ) )
	{
		return true;
	}

	if( history->scene->direction() == Plug::Out )
	{
		ConstObjectPtr v = value( history );
		ConstObjectPtr previousValue;
		if( history->predecessors.size() )
		{
			previousValue = value( history->predecessors.front().get() );
		}
		if( (bool)v != bool(previousValue) || (v && !v->isEqualTo( previousValue.get() )) )
		{
			return true;
		}
	}

	return false;
}

Gaffer::ValuePlugPtr Inspector::acquireEdit( const GafferScene::SceneAlgo::History *history, bool createIfNecessary, bool dryRun ) const
{
	if( !createIfNecessary )
	{
		return nullptr;
	}
	throw EditDisallowed( "Editing not supported" );
}

Gaffer::ValuePlugPtr Inspector::acquireEdit( Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history, bool createIfNecessary, bool dryRun ) const
{
	if( !createIfNecessary )
	{
		return nullptr;
	}
	throw EditDisallowed( "Editing not supported" );
}

void Inspector::edit( const IECore::Object *value, const GafferScene::SceneAlgo::History *history, bool dryRun ) const
{
	// Defer to the overload that takes an EditScope, to avoid duplicating all the logic.
	/// \todo Do we really need two virtual overloads for each function? Would
	/// it simplify things to have just one overload that detects the EditScope
	/// from the `history` argument?
	edit( value, nullptr, history, dryRun );
}

void Inspector::edit( const IECore::Object *value, Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history, bool dryRun ) const
{
	if( dryRun )
	{
		ValuePlugPtr plug = editScope ?
			acquireEdit( editScope, history, /* createIfNecessary = */ true, /* dryRun = */ true ) :
			acquireEdit( history, /* createIfNecessary = */ true, /* dryRun = */ true )
		;

		if( plug )
		{
			plug = static_cast<ValuePlug *>( spreadsheetAwareSource( plug.get() ) );
			setPlugValue( plug.get(), value, /* dryRun = */ true );
		}
		else
		{
			// We want to check that the plug that `acquireEdit()` will create
			// will accept `value`, but since this is a dry run we don't want to actually
			// create a plug in the graph. Assume that the plug will be typed to match the current
			// value, and make a temporary plug to use for the check.
			ConstObjectPtr currentValue = this->value( history );
			if( !currentValue )
			{
				std::string description;
				currentValue = this->fallbackValue( history, description );
			}

			if( auto currentData = runTimeCast<const IECore::Data>( currentValue ) )
			{
				plug = PlugAlgo::createPlugFromData( "value", Plug::In, Plug::Default, currentData.get() );
			}
			auto newData = runTimeCast<const IECore::Data>( value );
			if( !plug || !newData || !PlugAlgo::canSetValueFromData( plug.get(), newData ) )
			{
				throw EditDisallowed( fmt::format( "Data of type \"{}\" is not compatible.", value->typeName() ) );
			}
		}

		return;
	}

	ValuePlugPtr plug = editScope ?
		acquireEdit( editScope, history, /* createIfNecessary = */ true, /* dryRun = */ false ) :
		acquireEdit( history, /* createIfNecessary = */ true, /* dryRun = */ false )
	;
	plug = static_cast<ValuePlug *>( spreadsheetAwareSource( plug.get() ) );
	setPlugValue( plug.get(), value, /* dryRun = */ false );
}

void Inspector::disableEdit( const GafferScene::SceneAlgo::History *history, bool dryRun ) const
{
	PlugPtr plug  = acquireEdit( history, /* createIfNecessary = */ false, dryRun );
	if( !plug || plug->direction() == Plug::Out )
	{
		throw EditDisallowed( "No edit found to disable." );
	}

	plug = spreadsheetAwareSource( plug.get() );
	const std::string nonAcquireableReason = ::nonAcquireableReason( static_cast<ValuePlug *>( plug.get() ) );
	if( !nonAcquireableReason.empty() )
	{
		throw EditDisallowed( nonAcquireableReason );
	}

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
			throw EditDisallowed( fmt::format( "{} is locked.", readOnlyReason->relativeName( readOnlyReason->ancestor<ScriptNode>() ) ) );
		}
		else if( !enabledPlug->settable() )
		{
			throw EditDisallowed( fmt::format( "{} is not settable.", enabledPlug->relativeName( enabledPlug->ancestor<ScriptNode>() ) ) );
		}
		else if( !enabledPlug->getValue() )
		{
			throw EditDisallowed( fmt::format( "{} is not enabled.", enabledPlug->relativeName( enabledPlug->ancestor<ScriptNode>() ) ) );
		}
	}
	else
	{
		throw EditDisallowed( "Disabling edits not supported for this plug." );
	}

	if( dryRun )
	{
		return;
	}

	enabledPlug->setValue( false );
}

void Inspector::disableEdit( Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history, bool dryRun ) const
{
	throw EditDisallowed( fmt::format( "There is no edit in {}.", editScope->relativeName( editScope->scriptNode() ) ) );
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

				const bool currentViewableAncestorInHistory = m_historyVector.size() && MetadataAlgo::firstViewableNode( m_historyVector.back()->scene.get() ) == MetadataAlgo::firstViewableNode( current->scene.get() );
				if( !currentViewableAncestorInHistory )
				{
					if( successor && !endsWith( m_historyVector, successor ) )
					{
						// The result of `inspector->source()` was null on the
						// previous (`successor`) iteration. But there may still
						// have been a context change at that point, in which case the
						// `successor` belongs in our history.
						if( *successor->context != *current->context )
						{
							addVaryingContextVariables( successor->context.get(), current->context.get(), varyingContextVariables );
							if( !endsWith( m_historyVector, successor ) )
							{
								m_historyVector.push_back( successor );
							}
						}
					}

					if( inspector->hasEdit( current ) )
					{
						m_historyVector.push_back( current );
					}
					else if( current->predecessors.empty() )
					{
						// Make sure we include the tip of the history whether or not
						// there is an edit there. Among other things this allows us to
						// show where a value is loaded from a SceneReader.
						m_historyVector.push_back( current );
					}
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
		names.push_back( g_editPropertyName );
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
		name == g_editPropertyName
	)
	{
		SceneAlgo::History::ConstPtr h = history( canceller );
		if( !h )
		{
			return nullptr;
		}

		if( name == g_nodePropertyName )
		{
			/// \todo Revert to returning `h->scene->node()` and deal with
			/// firstViewableNode() entirely on the UI side in _HistoryWindow.
			return MetadataAlgo::firstViewableNode( h->scene->node() );
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

		ValuePlugPtr immediateEdit = m_historyProvider->inspector->acquireEdit( h.get(), /* createIfNecessary = */ false, /* dryRun = */ false );
		if( !immediateEdit )
		{
			return nullptr;
		}

		ValuePlug *edit = static_cast<ValuePlug *>( spreadsheetAwareSource( immediateEdit.get() ) );
		if( name == g_editPropertyName )
		{
			return edit;
		}
		else if( name == g_operationPropertyName )
		{
			if( auto tweakPlug = runTimeCast<const TweakPlug>( edit ) )
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
	size_t index = std::numeric_limits<size_t>::max();
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

bool Inspector::Result::editScopeInHistory() const
{
	return m_editScopeInHistory;
}

bool Inspector::Result::canAcquireEdit( bool createIfNecessary ) const
{
	try
	{
		m_editors->acquireEditFunction( createIfNecessary, /* dryRun = */ true );
	}
	catch( EditDisallowed &e )
	{
		return false;
	}

	return true;
}

std::string Inspector::Result::cantAcquireEditReason( bool createIfNecessary ) const
{
	try
	{
		m_editors->acquireEditFunction( createIfNecessary, /* dryRun = */ true );
	}
	catch( EditDisallowed &e )
	{
		return e.what();
	}
	return "";
}

Gaffer::ValuePlugPtr Inspector::Result::acquireEdit( bool createIfNecessary ) const
{
	return m_editors->acquireEditFunction( createIfNecessary, /* dryRun = */ false );
}

bool Inspector::Result::canEdit( const IECore::Object *value ) const
{
	try
	{
		m_editors->editFunction( value, /* dryRun = */ true );
	}
	catch( EditDisallowed &e )
	{
		return false;
	}

	return true;
}

std::string Inspector::Result::cantEditReason( const IECore::Object *value ) const
{
	try
	{
		m_editors->editFunction( value, /* dryRun = */ true );
	}
	catch( EditDisallowed &e )
	{
		return e.what();
	}
	return "";
}

void Inspector::Result::edit( const IECore::Object *value ) const
{
	m_editors->editFunction( value, /* dryRun = */ false );
}

bool Inspector::Result::canDisableEdit() const
{
	try
	{
		m_editors->disableEditFunction( /* dryRun = */ true );
	}
	catch( EditDisallowed &e )
	{
		return false;
	}

	return true;
}

std::string Inspector::Result::cantDisableEditReason() const
{
	try
	{
		m_editors->disableEditFunction( /* dryRun = */ true );
	}
	catch( EditDisallowed &e )
	{
		return e.what();
	}
	return "";
}

void Inspector::Result::disableEdit() const
{
	m_editors->disableEditFunction( /* dryRun = */ false );
}

Inspector::Result::Editors::Editors( AcquireEditFunction acquireEditFunction, EditFunction editFunction, DisableEditFunction disableEditFunction )
	:	acquireEditFunction( acquireEditFunction ), editFunction( editFunction ), disableEditFunction( disableEditFunction )
{
}

Inspector::Result::Editors::Editors( const std::string &editingDisallowedReason )
{
	acquireEditFunction = [editingDisallowedReason] ( bool createIfNecessary, bool dryRun ) -> ValuePlugPtr {
		throw EditDisallowed( fmt::format( fmt::runtime( editingDisallowedReason ), "edit" ) );
	};
	editFunction = [editingDisallowedReason] ( const IECore::Object *value, bool dryRun ) {
		throw EditDisallowed(  fmt::format( fmt::runtime( editingDisallowedReason ), "edit" )  );
	};
	disableEditFunction = [editingDisallowedReason] ( bool dryRun ) {
		throw EditDisallowed(  fmt::format( fmt::runtime( editingDisallowedReason ), "disable" )  );
	};
}
