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

using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Expression implementation
//////////////////////////////////////////////////////////////////////////

size_t Expression::g_firstPlugIndex;

IE_CORE_DEFINERUNTIMETYPED( Expression );

Expression::Expression( const std::string &name )
	:	ComputeNode( name ), m_engine( 0 )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild(
		new StringPlug(
			"engine",
			Plug::In,
			"python",
			Plug::Default & ~( Plug::AcceptsInputs ),
			Context::NoSubstitutions
		)
	);
	addChild(
		new StringPlug(
			"expression",
			Plug::In,
			"",
			Plug::Default & ~( Plug::AcceptsInputs ),
			Context::NoSubstitutions
		)
	);

	addChild( new ValuePlug( "__in" ) );
	addChild( new ValuePlug( "__out", Plug::Out ) );
	addChild( new ObjectVectorPlug( "__execute", Plug::Out, new ObjectVector ) );

	plugSetSignal().connect( boost::bind( &Expression::plugSet, this, ::_1 ) );
}

Expression::~Expression()
{
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
		inPlug()->hash( h );

		if( m_engine )
		{
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
	}
	else if( outPlug()->isAncestorOf( output ) )
	{
		executePlug()->hash( h );
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
			m_engine->setPlugValue( output, values->members()[index].get() );
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
		m_engine = NULL;
		m_contextNames.clear();

		try
		{
			std::string newExpression = expressionPlug()->getValue();
			if( newExpression.size() )
			{
				m_engine = Engine::create( enginePlug()->getValue(), newExpression );
				std::vector<std::string> inPlugPaths;
				std::vector<std::string> outPlugPaths;

				if( m_engine )
				{
					m_engine->inPlugs( inPlugPaths );
					m_engine->outPlugs( outPlugPaths );
					m_engine->contextNames( m_contextNames );
				}

				updatePlugs( inPlugPaths, outPlugPaths );
			}
		}
		catch( const std::exception &e )
		{
			/// \todo Report error to user somehow - error signal on Node?
			IECore::msg( IECore::Msg::Error, "Expression::plugSet", e.what() );
			m_engine = NULL;
		}

	}
}

void Expression::updatePlugs( const std::vector<std::string> &inPlugPaths, const std::vector<std::string> &outPlugPaths )
{
	/// \todo Reuse existing plugs where possible.
	inPlug()->clearChildren();
	outPlug()->removeOutputs();
	outPlug()->clearChildren();

	for( std::vector<std::string>::const_iterator it = inPlugPaths.begin(); it!=inPlugPaths.end(); ++it )
	{
		addPlug( inPlug(), *it );
	}

	for( std::vector<std::string>::const_iterator it = outPlugPaths.begin(); it!=outPlugPaths.end(); ++it )
	{
		addPlug( outPlug(), *it );
	}
}

void Expression::addPlug( ValuePlug *parentPlug, const std::string &plugPath )
{
	Node *p = parent<Node>();
	if( !p )
	{
		throw IECore::Exception( "No parent" );
	}

	ValuePlug *plug = p->descendant<ValuePlug>( plugPath );
	if( !plug )
	{
		throw IECore::Exception( boost::str( boost::format( "Plug \"%s\" does not exist" ) % plugPath ) );
	}

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

Expression::EnginePtr Expression::Engine::create( const std::string engineType, const std::string &expression )
{
	const CreatorMap &m = creators();
	CreatorMap::const_iterator it = m.find( engineType );
	if( it == m.end() )
	{
		return 0;
	}
	return it->second( expression );
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
