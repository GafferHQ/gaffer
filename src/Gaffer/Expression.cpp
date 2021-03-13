//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Expression.h"

#include "Gaffer/Action.h"
#include "Gaffer/Context.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"

#include "IECore/Exception.h"
#include "IECore/MessageHandler.h"

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Expression implementation
//////////////////////////////////////////////////////////////////////////

size_t Expression::g_firstPlugIndex;

GAFFER_NODE_DEFINE_TYPE( Expression );

Expression::Expression( const std::string &name )
	:	ComputeNode( name ), m_engine( nullptr )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild(
		new StringPlug(
			"__engine",
			Plug::In,
			"",
			Plug::Default & ~( Plug::AcceptsInputs | Plug::Serialisable ),
			IECore::StringAlgo::NoSubstitutions
		)
	);
	addChild(
		new StringPlug(
			"__expression",
			Plug::In,
			"",
			Plug::Default & ~( Plug::AcceptsInputs | Plug::Serialisable ),
			IECore::StringAlgo::NoSubstitutions
		)
	);

	addChild( new ValuePlug( "__in", Plug::In, Plug::Default & ~Plug::AcceptsInputs ) );
	addChild( new ValuePlug( "__out", Plug::Out ) );
	addChild( new ObjectVectorPlug( "__execute", Plug::Out, new ObjectVector ) );

	plugSetSignal().connect( boost::bind( &Expression::plugSet, this, ::_1 ) );
}

Expression::~Expression()
{
}

void Expression::languages( std::vector<std::string> &languages )
{
	Engine::registeredEngines( languages );
}

std::string Expression::defaultExpression( const ValuePlug *output, const std::string &language )
{
	EnginePtr e = Engine::create( language );
	return e->defaultExpression( output );
}

void Expression::setExpression( const std::string &expression, const std::string &language )
{
	std::string currentLanguage;
	const std::string currentExpression = getExpression( currentLanguage );
	if( expression == currentExpression && language == currentLanguage )
	{
		return;
	}

	// Create a new engine and parse the expression.
	// We don't modify any internal state at this
	// initial stage since parsing might throw if the
	// expression is invalid.

	EnginePtr engine = Engine::create( language );
	if( !engine )
	{
		throw Exception( boost::str(
			boost::format(
				"Failed to create engine for language \"%s\""
			) % language
		) );
	}

	std::vector<ValuePlug *> inPlugs, outPlugs;
	std::vector<IECore::InternedString> contextNames;

	engine->parse( this, expression, inPlugs, outPlugs, contextNames );

	// Validate that the expression doesn't read from and write
	// to the same plug, since circular dependencies aren't allowed.
	if( inPlugs.size() )
	{
		std::vector<ValuePlug *> sortedInPlugs( inPlugs );
		std::sort( sortedInPlugs.begin(), sortedInPlugs.end() );
		for( std::vector<ValuePlug *>::const_iterator it = outPlugs.begin(), eIt = outPlugs.end(); it != eIt; ++it )
		{
			if( std::binary_search( sortedInPlugs.begin(), sortedInPlugs.end(), *it ) )
			{
				throw Exception( boost::str(
					boost::format(
						"Cannot both read from and write to plug \"%s\""
					) % (*it)->relativeName( parent() )
				) );
			}
		}
	}

	// The setExpression() method is undoable by virtue of being
	// implemented entirely using other undoable functions - all
	// except for emitting expressionChangedSignal(). When doing,
	// we need to emit after the work is done, but we don't want
	// to emit just before it is undone - we want to emit after it
	// has been undone. We therefore have two emit actions, one at
	// the start with no doer and one at the end with no undoer.
	Action::enact(
		this,
		Action::Function(), // does nothing
		boost::bind( boost::ref( expressionChangedSignal() ), this )
	);

	m_engine = engine;
	m_contextNames = contextNames;
	updatePlugs( inPlugs, outPlugs );
	enginePlug()->setValue( language );

	// We store the expression in a processed form, referencing
	// the intermediate plugs on this node rather than the plugs
	// out in the wild. This allows us to account for changes to
	// node/plug names in getExpression(), where we convert back
	// to the external form.

	const std::string internalExpression = transcribe( expression, /* toInternalForm = */ true );
	if( internalExpression == expressionPlug()->getValue() )
	{
		// It is possible for two different expressions to map to the same
		// internal form. If neither expression has any input plugs, then
		// there would be no graph change to trigger dirty propagation for
		// `executePlug()`, so we must force one.
		expressionPlug()->setValue( "" );
	}
	expressionPlug()->setValue( internalExpression );

	Action::enact(
		this,
		boost::bind( boost::ref( expressionChangedSignal() ), this ),
		Action::Function() // does nothing
	);
}

std::string Expression::getExpression( std::string &engine ) const
{
	engine = enginePlug()->getValue();
	return transcribe( expressionPlug()->getValue(), /* toInternalForm = */ false );
}

Expression::ExpressionChangedSignal &Expression::expressionChangedSignal()
{
	return m_expressionChangedSignal;
}

std::string Expression::identifier( const ValuePlug *plug ) const
{
	if( !m_engine )
	{
		return "";
	}
	return m_engine->identifier( this, plug );
}

StringPlug *Expression::enginePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const StringPlug *Expression::enginePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

StringPlug *Expression::expressionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *Expression::expressionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

ValuePlug *Expression::inPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 );
}

const ValuePlug *Expression::inPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 );
}

ValuePlug *Expression::outPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 3 );
}

const ValuePlug *Expression::outPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 3 );
}

ObjectVectorPlug *Expression::executePlug()
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 4 );
}

const ObjectVectorPlug *Expression::executePlug() const
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 4 );
}

void Expression::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		inPlug()->isAncestorOf( input ) ||
		input == expressionPlug() ||
		input == enginePlug()
	)
	{
		outputs.push_back( executePlug() );
	}
	else if( input == executePlug() )
	{
		for( RecursiveValuePlugIterator it( outPlug() ); !it.done(); ++it )
		{
			if( !(*it)->children().size() )
			{
				outputs.push_back( it->get() );
			}
		}
	}
}

void Expression::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == executePlug() )
	{
		enginePlug()->hash( h );
		expressionPlug()->hash( h );
		for( ValuePlugIterator it( inPlug() ); !it.done(); ++it )
		{
			(*it)->hash( h );
			// We must hash the types of the input plugs, because
			// an identical expression but with different input plug
			// types may yield a different result from Engine::execute().
			h.append( (*it)->typeId() );
		}
		for( ValuePlugIterator it( outPlug() ); !it.done(); ++it )
		{
			// We also need to hash the types of the output plugs,
			// because an identical expression with different output
			// types may yield a different result from Engine::execute().
			h.append( (*it)->typeId() );
		}

		for( std::vector<IECore::InternedString>::const_iterator it = m_contextNames.begin(); it != m_contextNames.end(); it++ )
		{
			// TODO - expose entry hash to avoid rehashing?
			IECore::ConstDataPtr d = context->get( *it, false );
			if( d )
			{
				d->hash( h );
			}
			else
			{
				h.append( 0 );
			}
		}
	}
	else if( outPlug()->isAncestorOf( output ) )
	{
		executePlug()->hash( h );
		// We must hash the type of the output plug, to account for
		// Engine::apply() performing conversion based on plug type.
		h.append( output->typeId() );
	}
}

Gaffer::ValuePlug::CachePolicy Expression::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == executePlug() )
	{
		if( m_engine )
		{
			return m_engine->executeCachePolicy();
		}
		else
		{
			return ValuePlug::CachePolicy::Legacy;
		}
	}
	return ComputeNode::computeCachePolicy( output );
}


void Expression::compute( ValuePlug *output, const Context *context ) const
{
	if( output == executePlug() )
	{
		if( m_engine )
		{
			std::vector<const ValuePlug *> inputs;
			for( ValuePlugIterator it( inPlug() ); !it.done(); ++it )
			{
				inputs.push_back( it->get() );
			}
			static_cast<ObjectVectorPlug *>( output )->setValue( m_engine->execute( context, inputs ) );
		}
		else
		{
			output->setToDefault();
		}
		return;
	}

	// See if we're computing a descendant of outPlug(),
	// and if we are, get the immediate child of outPlug()
	// that is its parent.
	const ValuePlug *outPlugChild = output;
	while( outPlugChild )
	{
		const ValuePlug *p = outPlugChild->parent<ValuePlug>();
		if( p == outPlug() )
		{
			break;
		}
		outPlugChild = p;
	}

	// If we've found such a plug, we can defer to the engine
	// to do the work of setting it.
	if( outPlugChild )
	{
		ConstObjectVectorPtr values = executePlug()->getValue();
		size_t index = 0;
		for( ValuePlugIterator it( outPlug() ); !it.done() && *it != outPlugChild; ++it )
		{
			index++;
		}

		if( index < values->members().size() )
		{
			m_engine->apply( output, outPlugChild, values->members()[index].get() );
		}
		else
		{
			output->setToDefault();
		}
		return;
	}

	ComputeNode::compute( output, context );
}

void Expression::updatePlugs( const std::vector<ValuePlug *> &inPlugs, const std::vector<ValuePlug *> &outPlugs )
{
	for( size_t i = 0, e = inPlugs.size(); i < e; ++i )
	{
		updatePlug( inPlug(), i, inPlugs[i] );
	}
	removeChildren( inPlug(), inPlugs.size() );

	for( size_t i = 0, e = outPlugs.size(); i < e; ++i )
	{
		updatePlug( outPlug(), i, outPlugs[i] );
	}
	removeChildren( outPlug(), outPlugs.size() );
}

void Expression::updatePlug( ValuePlug *parentPlug, size_t childIndex, ValuePlug *plug )
{
	if( parentPlug->children().size() > childIndex )
	{
		// See if we can reuse the existing plug
		Plug *existingChildPlug = parentPlug->getChild<Plug>( childIndex );
		if(
			( existingChildPlug->direction() == Plug::In && existingChildPlug->getInput() == plug ) ||
			( existingChildPlug->direction() == Plug::Out && plug->getInput() == existingChildPlug )
		)
		{
			return;
		}
	}

	// Existing plug not OK, so we need to create one. First we must remove all
	// plugs from childIndex onwards, so that when we add the new plug it gets
	// the right index.
	removeChildren( parentPlug, childIndex );

	// Finally we can add the plug we need.

	PlugPtr childPlug = plug->createCounterpart( "p0", parentPlug->direction() );
	childPlug->setFlags( Plug::Dynamic | Plug::Serialisable, true );
	parentPlug->addChild( childPlug );
	if( childPlug->direction() == Plug::In )
	{
		childPlug->setInput( plug );
	}
	else
	{
		plug->setInput( childPlug );
	}
}

void Expression::removeChildren( ValuePlug *parentPlug, size_t startChildIndex )
{
	// Remove backwards, because children() is a vector and
	// it's therefore cheaper to remove from the end.
	for( int i = (int)(parentPlug->children().size() ) - 1; i >= (int)startChildIndex; --i )
	{
		Plug *toRemove = parentPlug->getChild<Plug>( i );
		toRemove->removeOutputs();
		parentPlug->removeChild( toRemove );
	}
}

std::string Expression::transcribe( const std::string &expression, bool toInternalForm ) const
{
	if( !m_engine )
	{
		return expression;
	}

	std::vector<const ValuePlug *> internalPlugs, externalPlugs;
	for( ValuePlugIterator it( inPlug() ); !it.done(); ++it )
	{
		internalPlugs.push_back( it->get() );
		externalPlugs.push_back( (*it)->getInput<ValuePlug>() );
	}

	for( ValuePlugIterator it( outPlug() ); !it.done(); ++it )
	{
		internalPlugs.push_back( it->get() );
		if( !(*it)->outputs().empty() )
		{
			externalPlugs.push_back( static_cast<const ValuePlug *>( (*it)->outputs().front() ) );
		}
		else
		{
			externalPlugs.push_back( nullptr );
		}
	}

	if( toInternalForm )
	{
		return m_engine->replace( this, expression, externalPlugs, internalPlugs );
	}
	else
	{
		return m_engine->replace( this, expression, internalPlugs, externalPlugs );
	}
}

void Expression::plugSet( const Plug *plug )
{
	if( m_engine || plug != expressionPlug() )
	{
		return;
	}

	const std::string engineType = enginePlug()->getValue();
	std::string expression = expressionPlug()->getValue();
	if( engineType.empty() || expression.empty() )
	{
		return;
	}

	const ScriptNode *script = scriptNode();
	if( !script || !script->isExecuting() )
	{
		IECore::msg( IECore::Msg::Warning, "Expression::plugSet", "Unexpected change to __engine plug. Should you be calling setExpression() instead?" );
		return;
	}

	// We've just been loaded from serialised form. All our plugs
	// will already have been connected appropriately by the serialisation,
	// but we need to initialise m_engine so we're ready for hash/compute.

	m_contextNames.clear();
	m_engine = Engine::create( engineType );
	expression = transcribe( expression, /* toInternalForm = */ false );
	std::vector<ValuePlug *> inPlugs, outPlugs;
	m_engine->parse( this, expression, inPlugs, outPlugs, m_contextNames );

	// Alas, it's not quite that simple. Nodes might have been renamed
	// during deserialisation (to avoid name clashes between duplicates).
	// And PythonExpressionEngine returns plugs in an order that depends
	// on name, so our internal plugs may not correspond to what it is
	// expecting. Call `updatePlugs()` to fix any mismatches. Transcribe
	// to internal form to match the state that `setExpression()` leaves
	// us in.
	updatePlugs( inPlugs, outPlugs );
	expressionPlug()->setValue( transcribe( expression, /* toInternalForm = */ true ) );

}

//////////////////////////////////////////////////////////////////////////
// Expression::Engine implementation
//////////////////////////////////////////////////////////////////////////

Expression::EnginePtr Expression::Engine::create( const std::string engineType )
{
	const CreatorMap &m = creators();
	CreatorMap::const_iterator it = m.find( engineType );
	if( it == m.end() )
	{
		return nullptr;
	}
	return it->second();
}

void Expression::Engine::registerEngine( const std::string engineType, Creator creator )
{
	creators()[engineType] = creator;
}

void Expression::Engine::registeredEngines( std::vector<std::string> &engineTypes )
{
	const CreatorMap &m = creators();
	for( CreatorMap::const_iterator it = m.begin(); it!=m.end(); it++ )
	{
		engineTypes.push_back( it->first );
	}
}

Expression::Engine::CreatorMap &Expression::Engine::creators()
{
	static CreatorMap m;
	return m;
}
