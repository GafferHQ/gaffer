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

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include "IECore/MessageHandler.h"
#include "IECore/Exception.h"

#include "Gaffer/Expression.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/BlockedConnection.h"

using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Expression implementation
//////////////////////////////////////////////////////////////////////////

size_t Expression::g_firstPlugIndex;

IE_CORE_DEFINERUNTIMETYPED( Expression );

Expression::Expression( const std::string &name )
	:	ComputeNode( name ), m_engine( NULL )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild(
		new StringPlug(
			"__engine",
			Plug::In,
			"python",
			Plug::Default & ~( Plug::AcceptsInputs ),
			Context::NoSubstitutions
		)
	);
	addChild(
		new StringPlug(
			"__expression",
			Plug::In,
			"",
			Plug::Default & ~( Plug::AcceptsInputs ),
			Context::NoSubstitutions
		)
	);

	addChild( new ValuePlug( "__in" ) );
	addChild( new ValuePlug( "__out", Plug::Out ) );
	addChild( new ObjectVectorPlug( "__execute", Plug::Out, new ObjectVector ) );

	m_plugSetConnection = plugSetSignal().connect( boost::bind( &Expression::plugSet, this, ::_1 ) );
}

Expression::~Expression()
{
}

void Expression::setExpression( const std::string &expression, const std::string &engine )
{
	if(
		expression == expressionPlug()->getValue() &&
		engine == enginePlug()->getValue()
	)
	{
		return;
	}

	m_engine = NULL;
	m_contextNames.clear();

	m_engine = Engine::create( engine );

	std::vector<ValuePlug *> inPlugs, outPlugs;
	m_engine->parse( this, expression, inPlugs, outPlugs, m_contextNames );
	updatePlugs( inPlugs, outPlugs );

	BlockedConnection blockedConnection( m_plugSetConnection );
	enginePlug()->setValue( engine );
	expressionPlug()->setValue( expression );
}

std::string Expression::getExpression( std::string &engine ) const
{
	engine = enginePlug()->getValue();
	return expressionPlug()->getValue();
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
		for( RecursiveValuePlugIterator it( outPlug() ); it != it.end(); ++it )
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
		for( ValuePlugIterator it( inPlug() ); it!=it.end(); it++ )
		{
			(*it)->hash( h );
			// We must hash the types of the input plugs, because
			// an identical expression but with different input plug
			// types may yield a different result from Engine::execute().
			h.append( (*it)->typeId() );
		}

		for( std::vector<IECore::InternedString>::const_iterator it = m_contextNames.begin(); it != m_contextNames.end(); it++ )
		{
			const IECore::Data *d = context->get<IECore::Data>( *it, 0 );
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

void Expression::compute( ValuePlug *output, const Context *context ) const
{
	if( output == executePlug() )
	{
		if( m_engine )
		{
			std::vector<const ValuePlug *> inputs;
			for( ValuePlugIterator it( inPlug() ); it != it.end(); ++it )
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
	const Plug *outPlugChild = output;
	while( outPlugChild )
	{
		const Plug *p = outPlugChild->parent<Plug>();
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
		for( ValuePlugIterator it( outPlug() ); it != it.end() && *it != outPlugChild; ++it )
		{
			index++;
		}

		if( index < values->members().size() )
		{
			m_engine->apply( output, values->members()[index].get() );
		}
		else
		{
			output->setToDefault();
		}
		return;
	}

	ComputeNode::compute( output, context );
}

void Expression::plugSet( Plug *plug )
{
	if( plug == expressionPlug() )
	{
		// We use this to restore the engine appropriately when
		// an Expression node is loaded from serialised form. We
		// don't do all the updatePlugs() work that we do in
		// setExpression() because we know that the serialisation
		// will have rebuild the structure for us - we just need
		// to recreate the engine.
		/// \todo Perhaps it would be better if we serialised
		/// a setExpression() call and then used that in our
		/// serialisation.
		const std::string engineType = enginePlug()->getValue();
		const std::string expression = expressionPlug()->getValue();
		m_engine = NULL;
		m_contextNames.clear();
		if( !engineType.empty() && !expression.empty() )
		{
			m_engine = Engine::create( engineType );
			std::vector<ValuePlug *> inPlugs, outPlugs;
			m_engine->parse( this, expression, inPlugs, outPlugs, m_contextNames );
		}
	}
}

void Expression::updatePlugs( const std::vector<ValuePlug *> &inPlugs, const std::vector<ValuePlug *> &outPlugs )
{
	for( size_t i = 0, e = inPlugs.size(); i < e; ++i )
	{
		updatePlug( inPlug(), i, inPlugs[i] );
	}

	for( size_t i = 0, e = outPlugs.size(); i < e; ++i )
	{
		updatePlug( outPlug(), i, outPlugs[i] );
	}
}

void Expression::updatePlug( ValuePlug *parentPlug, size_t childIndex, ValuePlug *plug )
{
	if( parentPlug->children().size() > childIndex )
	{
		// See if we can reuse the existing plug
		Plug *existingChildPlug = parentPlug->getChild<Plug>( childIndex );
		if(
			( existingChildPlug->direction() == Plug::In && existingChildPlug->getInput<Plug>() == plug ) ||
			( existingChildPlug->direction() == Plug::Out && plug->getInput<Plug>() == existingChildPlug )
		)
		{
			return;
		}
	}

	// Existing plug not OK, so we need to create one. First we must remove all
	// plugs from childIndex onwards, so that when we add the new plug it gets
	// the right index. We do this backwards, because children() is a vector and
	// it's therefore cheaper to remove from the end.
	for( int i = (int)(parentPlug->children().size() ) - 1; i >= (int)childIndex; --i )
	{
		Plug *toRemove = parentPlug->getChild<Plug>( i );
		toRemove->removeOutputs();
		parentPlug->removeChild( toRemove );
	}

	// Finally we can add the plug we need.

	PlugPtr childPlug = plug->createCounterpart( "p0", parentPlug->direction() );
	childPlug->setFlags( Plug::Dynamic, true );
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

//////////////////////////////////////////////////////////////////////////
// Expression::Engine implementation
//////////////////////////////////////////////////////////////////////////

Expression::EnginePtr Expression::Engine::create( const std::string engineType )
{
	const CreatorMap &m = creators();
	CreatorMap::const_iterator it = m.find( engineType );
	if( it == m.end() )
	{
		return NULL;
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
