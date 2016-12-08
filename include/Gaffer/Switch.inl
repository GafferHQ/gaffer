//////////////////////////////////////////////////////////////////////////
//
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
#include "boost/regex.hpp"

#include "Gaffer/Switch.h"
#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"

namespace Gaffer
{

namespace Detail
{

struct IdentityContext
{
	IdentityContext( const Context *context )
	{
	}
};

};

template<typename BaseType>
const IECore::RunTimeTyped::TypeDescription<Switch<BaseType> > Switch<BaseType>::g_typeDescription;

template<typename BaseType>
size_t Switch<BaseType>::g_firstPlugIndex = 0;

template<typename BaseType>
Switch<BaseType>::Switch( const std::string &name)
	:	BaseType( name, 1 ) // ArrayPlug version of *Processor constructor
{
	init( /* expectBaseClassPlugs = */ true );
}

template<typename BaseType>
void Switch<BaseType>::init( bool expectBaseClassPlugs )
{
	BaseType::storeIndexOfNextChild( g_firstPlugIndex );
	BaseType::addChild( new IntPlug( "index", Gaffer::Plug::In, 0, 0 ) );
	if( !BaseType::enabledPlug() )
	{
		// if the base class doesn't provide an enabledPlug(),
		// then we'll provide our own.
		BaseType::addChild( new BoolPlug( "enabled", Gaffer::Plug::In, true ) );
	}

	if( expectBaseClassPlugs )
	{
		// We need to react to addition/removal of inputs, so connect to
		// the childAdded signal on our input array.
		ArrayPlug *inPlugs = BaseType::template getChild<ArrayPlug>( "in");
		inPlugs->childAddedSignal().connect( boost::bind( &Switch::childAdded, this, ::_2 ) );
	}
	else
	{
		// The input array doesn't exist yet, so connect to our own childAdded
		// signal so that when it's added later, we can make the connection we
		// would otherwise have made above.
		BaseType::childAddedSignal().connect( boost::bind( &Switch::childAdded, this, ::_2 ) );
	}

	BaseType::plugSetSignal().connect( boost::bind( &Switch::plugSet, this, ::_1 ) );
	BaseType::plugInputChangedSignal().connect( boost::bind( &Switch::plugInputChanged, this, ::_1 ) );
}

template<typename BaseType>
Switch<BaseType>::~Switch()
{
}

template<typename BaseType>
void Switch<BaseType>::setup( const Plug *plug )
{
	if( BaseType::template getChild<Plug>( "in") )
	{
		throw IECore::Exception( "Switch already has an \"in\" plug." );
	}
	if( BaseType::template getChild<Plug>( "out" ) )
	{
		throw IECore::Exception( "Switch already has an \"out\" plug." );
	}

	PlugPtr inElement = plug->createCounterpart( "in0", Plug::In );
	inElement->setFlags( Plug::Dynamic | Plug::Serialisable, true );
	ArrayPlugPtr in = new ArrayPlug(
		"in",
		Plug::In,
		inElement,
		0,
		Imath::limits<size_t>::max(),
		Plug::Default | Plug::Dynamic
	);
	BaseType::addChild( in );

	PlugPtr out = plug->createCounterpart( "out", Plug::Out );
	out->setFlags( Plug::Dynamic | Plug::Serialisable, true );
	BaseType::addChild( out );
}

template<typename BaseType>
Plug *Switch<BaseType>::activeInPlug()
{
	ArrayPlug *inputs = BaseType::template getChild<ArrayPlug>( "in" );
	if( !inputs )
	{
		return NULL;
	}
	return inputs->getChild<Plug>( inputIndex( Context::current() ) );
}

template<typename BaseType>
const Plug *Switch<BaseType>::activeInPlug() const
{
	return const_cast<Switch *>( this )->activeInPlug();
}

template<typename BaseType>
IntPlug *Switch<BaseType>::indexPlug()
{
	return BaseType::template getChild<IntPlug>( g_firstPlugIndex );
}

template<typename BaseType>
const IntPlug *Switch<BaseType>::indexPlug() const
{
	return BaseType::template getChild<IntPlug>( g_firstPlugIndex );
}

template<typename BaseType>
BoolPlug *Switch<BaseType>::enabledPlug()
{
	if( BoolPlug *p = BaseType::enabledPlug() )
	{
		return p;
	}
	return BaseType::template getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

template<typename BaseType>
const BoolPlug *Switch<BaseType>::enabledPlug() const
{
	if( const BoolPlug *p = BaseType::enabledPlug() )
	{
		return p;
	}
	return BaseType::template getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

template<typename BaseType>
void Switch<BaseType>::affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	BaseType::affects( input, outputs );

	if(
		input == enabledPlug() ||
		input == indexPlug()
	)
	{
		if( const Plug *out = BaseType::template getChild<Plug>( "out" ) )
		{
			if( out->children().size() )
			{
				for( RecursiveOutputPlugIterator it( out ); !it.done(); ++it )
				{
					if( !(*it)->children().size() )
					{
						outputs.push_back( it->get() );
					}
				}
			}
			else
			{
				outputs.push_back( out );
			}
		}
	}
	else if( input->direction() == Plug::In )
	{
		if( const Plug *output = oppositePlug( input ) )
		{
			outputs.push_back( output );
		}
	}
}

template<typename BaseType>
void Switch<BaseType>::childAdded( GraphComponent *child )
{
	ArrayPlug *inPlugs = BaseType::template getChild<ArrayPlug>( "in" );
	if( child->parent<Plug>() == inPlugs )
	{
		// Because inputIndex() wraps on the number of children,
		// the addition of a new one means we must update.
		updateInternalConnection();
	}
	else if( child == inPlugs )
	{
		// Our "in" plug has just been added. Update our internal connection,
		// and connect up so we can respond when extra inputs are added.
		updateInternalConnection();
		inPlugs->childAddedSignal().connect( boost::bind( &Switch::childAdded, this, ::_2 ) );
	}
	else if( child == BaseType::template getChild<Plug>( "out" ) )
	{
		// Our "out" plug has just been added. Make sure it has
		// an appropriate internal connection.
		updateInternalConnection();
	}
}

template<typename BaseType>
Plug *Switch<BaseType>::correspondingInput( const Plug *output )
{
	return const_cast<Plug *>( oppositePlug( output, 0 ) );
}

template<typename BaseType>
const Plug *Switch<BaseType>::correspondingInput( const Plug *output ) const
{
	return oppositePlug( output, 0 );
}

template<typename BaseType>
bool Switch<BaseType>::acceptsInput( const Plug *plug, const Plug *inputPlug ) const
{
	if( !BaseType::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( !inputPlug )
	{
		return true;
	}

	if( !isInstanceOf( ComputeNode::staticTypeId() ) && ( plug == enabledPlug() || plug == indexPlug() ) )
	{
		// we're not a compute node, so we have to implement the switching by making an internal connection
		// from an input to the output. this means the index must be a constant value, which means that it
		// cannot be the output of a ComputeNode, which could vary according to the Context.
		if( variesWithContext( inputPlug ) )
		{
			return false;
		}
	}

	if( plug->direction() == Plug::In )
	{
		if( const Plug *opposite = oppositePlug( plug ) )
		{
			if( !opposite->acceptsInput( inputPlug ) )
			{
				return false;
			}
		}
	}

	return true;
}

template<typename BaseType>
void Switch<BaseType>::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	hashInternal<BaseType>( output, context, h );
}

template<typename BaseType>
template<typename T>
void Switch<BaseType>::hashInternal( const ValuePlug *output, const Context *context, IECore::MurmurHash &h, typename boost::enable_if<boost::is_base_of<ComputeNode, T> >::type *enabler ) const
{
	if( const ValuePlug *input = IECore::runTimeCast<const ValuePlug>( oppositePlug( output, inputIndex( context ) ) ) )
	{
		h = input->hash();
		return;
	}

	BaseType::hash( output, context, h );
}

template<typename BaseType>
template<typename T>
void Switch<BaseType>::hashInternal( const ValuePlug *output, const Context *context, IECore::MurmurHash &h, typename boost::disable_if<boost::is_base_of<ComputeNode, T> >::type *enabler ) const
{
	// not a ComputeNode - no need for hashing
}

template<typename BaseType>
void Switch<BaseType>::compute( ValuePlug *output, const Context *context ) const
{
	// defer to computeInternal(), which is implemented appropriately for
	// ComputeNode and DependencyNode types.
	computeInternal<BaseType>( output, context );
}

template<typename BaseType>
template<typename T>
void Switch<BaseType>::computeInternal( ValuePlug *output, const Context *context, typename boost::enable_if<boost::is_base_of<ComputeNode, T> >::type *enabler ) const
{
	if( const ValuePlug *input = IECore::runTimeCast<const ValuePlug>( oppositePlug( output, inputIndex( context ) ) ) )
	{
		output->setFrom( input );
		return;
	}

	BaseType::compute( output, context );
}

template<typename BaseType>
template<typename T>
void Switch<BaseType>::computeInternal( ValuePlug *output, const Context *context, typename boost::disable_if<boost::is_base_of<ComputeNode, T> >::type *enabler ) const
{
	// not a ComputeNode - no need for computation
}

template<typename BaseType>
void Switch<BaseType>::plugSet( Plug *plug )
{
	if( plug == indexPlug() || plug == enabledPlug() )
	{
		updateInternalConnection();
	}
}

template<typename BaseType>
void Switch<BaseType>::plugInputChanged( Plug *plug )
{
	if( plug == indexPlug() || plug == enabledPlug() )
	{
		updateInternalConnection();
	}
}

template<typename BaseType>
size_t Switch<BaseType>::inputIndex( const Context *context ) const
{
	const ArrayPlug *inPlugs = BaseType::template getChild<ArrayPlug>( "in" );
	if( enabledPlug()->getValue() && inPlugs && inPlugs->children().size() > 1 )
	{
		size_t index = 0;
		const IntPlug *indexPlug = this->indexPlug();
		if( variesWithContext( indexPlug ) )
		{
			typename SwitchTraits<BaseType>::IndexContext indexContext( context );
			index = indexPlug->getValue();
		}
		else
		{
			index = indexPlug->getValue();
		}
		return index % (inPlugs->children().size() - 1);
	}
	else
	{
		return 0;
	}
}

template<typename BaseType>
const Plug *Switch<BaseType>::oppositePlug( const Plug *plug, size_t inputIndex ) const
{
	const ArrayPlug *inPlugs = BaseType::template getChild<ArrayPlug>( "in" );
	const Plug *outPlug = BaseType::template getChild<Plug>( "out" );
	if( !inPlugs || !outPlug )
	{
		return NULL;
	}

	// Find the ancestorPlug - this is either a child of inPlugs or it
	// is outPlug. At the same time, fill names with the names of the hierarchy
	// between plug and ancestorPlug.
	const Plug *ancestorPlug = NULL;
	std::vector<IECore::InternedString> names;
	while( plug )
	{
		const GraphComponent *plugParent = plug->parent<GraphComponent>();
		if( plugParent == inPlugs || plug == outPlug )
		{
			ancestorPlug = plug;
			break;
		}
		else
		{
			names.push_back( plug->getName() );
			plug = static_cast<const Plug *>( plugParent );
		}
	}

	if( !ancestorPlug )
	{
		return NULL;
	}

	// Now we can find the opposite for this ancestor plug.
	const Plug *oppositeAncestorPlug = NULL;
	if( plug->direction() == Plug::Out )
	{
		oppositeAncestorPlug = inPlugs->getChild<Plug>( inputIndex );
	}
	else
	{
		oppositeAncestorPlug = outPlug;
	}

	// And then find the opposite of plug by traversing down from the ancestor plug.
	const Plug *result = oppositeAncestorPlug;
	for( std::vector<IECore::InternedString>::const_iterator it = names.begin(), eIt = names.end(); it != eIt; ++it )
	{
		result = result->getChild<Plug>( *it );
	}

	return result;
}

template<typename BaseType>
bool Switch<BaseType>::variesWithContext( const Plug *plug ) const
{
	plug = plug->source<Gaffer::Plug>();
	return plug->direction() == Plug::Out && IECore::runTimeCast<const ComputeNode>( plug->node() );
}

template<typename BaseType>
void Switch<BaseType>::updateInternalConnection()
{
	Plug *out = BaseType::template getChild<Plug>( "out" );
	if( !out )
	{
		return;
	}

	if( variesWithContext( enabledPlug() ) || variesWithContext( indexPlug() ) )
	{
		// We can't use an internal connection to implement the switch,
		// because the index might vary from context to context. We must
		// therefore implement switching via hash()/compute().
		assert( this->isInstanceOf( ComputeNode::staticTypeId() ) );
		out->setInput( NULL );
		return;
	}

	Plug *in = const_cast<Plug *>( oppositePlug( out, inputIndex() ) );
	out->setInput( in );
}

} // namespace Gaffer
