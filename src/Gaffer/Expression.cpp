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
#include "Gaffer/CompoundPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/Context.h"

using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Expression implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Expression );

Expression::Expression( const std::string &name )
	:	ComputeNode( name ), m_engine( 0 )
{
	addChild(
		new StringPlug(
			"engine",
			Plug::In,
			"python",
			Plug::Default & ~( Plug::AcceptsInputs | Plug::PerformsSubstitutions )
		)
	);
	addChild(
		new StringPlug(
			"expression",
			Plug::In,
			"",
			Plug::Default & ~( Plug::AcceptsInputs | Plug::PerformsSubstitutions )
		)
	);

	plugSetSignal().connect( boost::bind( &Expression::plugSet, this, ::_1 ) );
	parentChangedSignal().connect( boost::bind( &Expression::parentChanged, this, ::_1, ::_2 ) );
}

Expression::~Expression()
{
}

StringPlug *Expression::enginePlug()
{
	return getChild<StringPlug>( "engine" );
}

const StringPlug *Expression::enginePlug() const
{
	return getChild<StringPlug>( "engine" );
}

StringPlug *Expression::expressionPlug()
{
	return getChild<StringPlug>( "expression" );
}

const StringPlug *Expression::expressionPlug() const
{
	return getChild<StringPlug>( "expression" );
}

void Expression::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	const CompoundPlug *in = getChild<CompoundPlug>( "in" );
	const ValuePlug *out = getChild<ValuePlug>( "out" );
	if( in && out )
	{
		if( input->parent<CompoundPlug>() == in )
		{
			outputs.push_back( out );
		}
	}
	else if( out )
	{
		if( input == expressionPlug() || input == enginePlug() )
		{
			outputs.push_back( out );
		}
	}
}

void Expression::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );
	if( output == getChild<ValuePlug>( "out" ) )
	{
		enginePlug()->hash( h );
		expressionPlug()->hash( h );
		const CompoundPlug *in = getChild<CompoundPlug>( "in" );
		if( in )
		{
			in->hash( h );
		}
		if( m_engine )
		{
			std::vector<std::string> contextNames;
			m_engine->contextNames( contextNames );
			for( std::vector<std::string>::const_iterator it = contextNames.begin(); it != contextNames.end(); it++ )
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
}

void Expression::compute( ValuePlug *output, const Context *context ) const
{
	if( output == getChild<ValuePlug>( "out" ) )
	{
		if( m_engine )
		{
			const CompoundPlug *in = getChild<CompoundPlug>( "in" );
			std::vector<const ValuePlug *> inputs;
			for( ChildContainer::const_iterator it = in->children().begin(); it!=in->children().end(); it++ )
			{
				inputs.push_back( static_cast<const ValuePlug *>( (*it).get() ) );
			}

			m_engine->execute( context, inputs, output );
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
	if( !parent<Node>() )
	{
		// typically this happens when a plug is set during the loading of a script,
		// as at the point our plugs are set, we don't yet have a parent. instead
		// we'll make an engine in our parentChanged slot.
		return;
	}

	StringPlug *e = expressionPlug();
	if( plug == e )
	{
		m_engine = 0;

		try {
			std::string newExpression = e->getValue();
			if( newExpression.size() )
			{
				m_engine = Engine::create( enginePlug()->getValue(), newExpression );

				std::vector<std::string> inPlugPaths;
				std::string outPlugPath;

				if( m_engine )
				{
					m_engine->inPlugs( inPlugPaths );
					outPlugPath = m_engine->outPlug();
				}

				updatePlugs( outPlugPath, inPlugPaths );
			}
		}
		catch( const std::exception &e )
		{
			/// \todo Report error to user somehow - error signal on Node?
			IECore::msg( IECore::Msg::Error, "Expression::plugSet", e.what() );
			m_engine = 0;
		}

	}
}

void Expression::parentChanged( GraphComponent *child, GraphComponent *oldParent )
{
	assert( this == child );
	if( oldParent == 0 && parent<GraphComponent>() )
	{
		// assume we've just been created and parented during the loading of a script.
		// our plugs are already set up, so we just need to make sure we have an engine.
		std::string expression = expressionPlug()->getValue();
		if( expression.size() )
		{
			m_engine = Engine::create( enginePlug()->getValue(), expression );
		}
	}
}

void Expression::updatePlugs( const std::string &dstPlugPath, std::vector<std::string> &srcPlugPaths )
{
	Node *p = parent<Node>();

	// if the expression was invalid, remove our plugs
	if( !dstPlugPath.size() )
	{
		Plug *in = getChild<Plug>( "in" );
		if( in )
		{
			removeChild( in );
		}
		Plug *out = getChild<Plug>( "out" );
		if( out )
		{
			removeChild( out );
		}
		return;
	}

	// otherwise try to create connections to the plugs the expression wants

	ValuePlug *dstPlug = p->descendant<ValuePlug>( dstPlugPath );
	if( !dstPlug )
	{
		throw IECore::Exception( boost::str( boost::format( "Destination plug \"%s\" does not exist" ) % dstPlugPath ) );
	}

	CompoundPlugPtr inPlugs = new CompoundPlug( "in", Plug::In, Plug::Default | Plug::Dynamic );
	setChild( "in", inPlugs );
	for( std::vector<std::string>::const_iterator it = srcPlugPaths.begin(); it!=srcPlugPaths.end(); it++ )
	{
		ValuePlug *srcPlug = p->descendant<ValuePlug>( *it );
		if( !srcPlug )
		{
			throw IECore::Exception( boost::str( boost::format( "Source plug \"%s\" does not exist" ) % *it ) );
		}
		PlugPtr inPlug = srcPlug->createCounterpart( "plug", Plug::In );
		inPlugs->addChild( inPlug );
		inPlug->setInput( srcPlug );
	}

	PlugPtr outPlug = dstPlug->createCounterpart( "out", Plug::Out );
	setChild( "out", outPlug );
	dstPlug->setInput( outPlug );
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
