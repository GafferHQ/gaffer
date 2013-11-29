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

namespace Gaffer
{

template<typename BaseType>
const IECore::RunTimeTyped::TypeDescription<Switch<BaseType> > Switch<BaseType>::g_typeDescription;

template<typename BaseType>
size_t Switch<BaseType>::g_firstPlugIndex = 0;

template<typename BaseType>
Switch<BaseType>::Switch( const std::string &name )
	:	BaseType( name )
{
	BaseType::storeIndexOfNextChild( g_firstPlugIndex );
	BaseType::addChild( new IntPlug( "index", Gaffer::Plug::In, 0, 0 ) );
	if( !BaseType::enabledPlug() )
	{
		// if the base class doesn't provide an enabledPlug(),
		// then we'll provide our own.
		BaseType::addChild( new BoolPlug( "enabled", Gaffer::Plug::In, true ) );		
	}

	if( Plug *in = BaseType::template getChild<Plug>( "in" ) )
	{
		// our BaseType provides an "in" plug - we use that to seed our InputGenerator.
		m_inputGenerator = boost::shared_ptr<Gaffer::Behaviours::InputGenerator<Plug> >(
			new Gaffer::Behaviours::InputGenerator<Plug>( this, in )
		);
	}
	else
	{
		// our BaseType doesn't provide an "in" plug - we'll make our InputGenerator
		// when one gets added following construction.
		BaseType::childAddedSignal().connect( boost::bind( &Switch::childAdded, this, ::_2 ) );
	}
}

template<typename BaseType>
Switch<BaseType>::~Switch()
{
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
		const Plug *out = BaseType::template getChild<Plug>( "out" );
		if( out->children().size() )
		{
			for( RecursiveOutputPlugIterator it( out ); it != it.end(); ++it )
			{
				if( !(*it)->children().size() )
				{
					outputs.push_back( *it );
				}
			}
		}
		else
		{
			outputs.push_back( out );
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
	if( child->getName() == "in" )
	{
		PlugPtr in = IECore::runTimeCast<Plug>( child );
		if( in )
		{
			m_inputGenerator = boost::shared_ptr<Gaffer::Behaviours::InputGenerator<Plug> >(
				new Gaffer::Behaviours::InputGenerator<Plug>( this, in )
			);
			BaseType::childAddedSignal().disconnect( boost::bind( &Switch::childAdded, this, ::_2 ) );
		}
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
void Switch<BaseType>::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	if( const ValuePlug *input = IECore::runTimeCast<const ValuePlug>( oppositePlug( output, inputIndex() ) ) )
	{
		h = input->hash();
		return;
	}

	BaseType::hash( output, context, h );
}

template<typename BaseType>
void Switch<BaseType>::compute( ValuePlug *output, const Context *context ) const
{
	if( const ValuePlug *input = IECore::runTimeCast<const ValuePlug>( oppositePlug( output, inputIndex() ) ) )
	{
		output->setFrom( input );
		return;
	}

	BaseType::compute( output, context );
}

template<typename BaseType>
size_t Switch<BaseType>::inputIndex() const
{
	if( enabledPlug()->getValue() )
	{
		return indexPlug()->getValue();	
	}
	else
	{
		return 0;
	}
}

template<typename BaseType>
const Plug *Switch<BaseType>::oppositePlug( const Plug *plug, size_t inputIndex ) const
{
	// ancestorPlug will be the parent of plug (or plug itself) immediately under
	// the node, and names will contain the names of the hierarchy
	// between plug and ancestorPlug.
	const Plug *ancestorPlug = NULL;
	std::vector<IECore::InternedString> names;	
	while( plug )
	{
		const GraphComponent *plugParent = plug->parent<GraphComponent>();
		if( plugParent == this )
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
	
	// now we can find the opposite for this ancestor plug.
	const Plug *oppositeAncestorPlug = NULL;
	if( plug->direction() == Plug::Out )
	{
		size_t remappedIndex = inputIndex;
		if( m_inputGenerator->inputs().size() > 1 )
		{
			remappedIndex = remappedIndex % (m_inputGenerator->inputs().size() - 1);
		}
		else
		{
			remappedIndex = 0;
		}
		oppositeAncestorPlug = m_inputGenerator->inputs()[remappedIndex];
	}
	else
	{
		static boost::regex inPlugRegex( "^in[0-9]*$" );
		if( boost::regex_match( ancestorPlug->getName().c_str(), inPlugRegex ) )
		{
			oppositeAncestorPlug = BaseType::template getChild<Plug>( "out" );
		}
	}
	
	if( !oppositeAncestorPlug )
	{
		return NULL;
	}
	
	// and then find the opposite of plug by traversing down from the ancestor plug.
	const Plug *result = oppositeAncestorPlug;
	for( std::vector<IECore::InternedString>::const_iterator it = names.begin(), eIt = names.end(); it != eIt; ++it )
	{
		result = result->getChild<Plug>( *it );
	}
	
	return result;
}

} // namespace Gaffer
