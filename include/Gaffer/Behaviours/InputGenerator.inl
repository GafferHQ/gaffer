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
#include "boost/regex.hpp"

#include "Gaffer/ScriptNode.h"

namespace Gaffer
{
namespace Behaviours
{

template< typename PlugClass >
InputGenerator<PlugClass>::InputGenerator( Gaffer::GraphComponent *parent, PlugClassPtr plugPrototype, size_t minInputs, size_t maxInputs )
	:
	m_parent( parent ),
	m_minimumInputs( std::max( minInputs, size_t( 1 ) ) ),
	m_maximumInputs( std::max( maxInputs, m_minimumInputs ) ),
	m_prototype( plugPrototype )
{
	Node *node = IECore::runTimeCast<Node>( parent );
	if( !node )
	{
		node = parent->ancestor<Node>();
		if( !node )
		{
			throw IECore::Exception( "Parent must be a Node or have an ancestor Node" );
		}
	}

	node->plugInputChangedSignal().connect( boost::bind( &InputGenerator<PlugClass>::inputChanged, this, ::_1 ) );
	m_parent->childAddedSignal().connect( boost::bind( &InputGenerator<PlugClass>::childAdded, this, ::_1, ::_2 ) );
	m_parent->childRemovedSignal().connect( boost::bind( &InputGenerator<PlugClass>::childRemoved, this, ::_1, ::_2 ) );

	if( plugPrototype->template parent<GraphComponent>() != m_parent )
	{
		m_parent->addChild( plugPrototype );
	}
	else
	{
		// because the addChild() happened before we were constructed, our childAdded() slot
		// won't have had a chance to update m_inputs.
		m_inputs.push_back( plugPrototype );
	}

	for( size_t i = 1; i < m_minimumInputs; ++i )
	{
		PlugClassPtr p = IECore::runTimeCast<PlugClass>( plugPrototype->createCounterpart( plugPrototype->getName(), Plug::In ) );
		m_parent->addChild( p );
	}
}

template< typename PlugClass >
typename std::vector<typename PlugClass::Ptr>::const_iterator InputGenerator<PlugClass>::endIterator() const
{
	return m_inputs.end();
}

template<typename PlugClass>
size_t InputGenerator<PlugClass>::nConnectedInputs() const
{
	size_t result = 0;
	for( typename std::vector<PlugClassPtr>::const_iterator it = m_inputs.begin(), eIt=m_inputs.end(); it != eIt; ++it )
	{
		if( (*it)->template getInput<Gaffer::Plug>() )
		{
			result++;
		}
	}
	return result;
}

template<typename PlugClass>
bool InputGenerator<PlugClass>::plugValid( const Plug *plug )
{
	if( plug == m_prototype )
	{
		return true;
	}

	if( !plug )
	{
		return false;
	}
	if( plug->typeId() != m_prototype->typeId() )
	{
		return false;
	}

	std::string prefix = m_prototype->getName();
	static boost::regex g_prefixSuffixRegex( "^(.*[^0-9]+)([0-9]+)$" );
	boost::cmatch match;
	if( boost::regex_match( m_prototype->getName().string().c_str(), match, g_prefixSuffixRegex ) )
	{
		prefix = match[1];
	}
	if( !boost::regex_match( plug->getName().string().c_str(), match, g_prefixSuffixRegex ) )
	{
		return false;
	}
	return match[1] == prefix;
}

template< typename PlugClass >
void InputGenerator<PlugClass>::childAdded( Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child )
{
	if( plugValid( IECore::runTimeCast<Gaffer::Plug>( child ) ) )
	{
		if( m_inputs.size() && m_inputs[m_inputs.size()-1] == child )
		{
			// we can arrive here in the circumstance that we were constructed from
			// a childAdded() handler somewhere else. in that case, we've just added
			// the first plug to m_inputs in the constructor, and added our own
			// childAdded handler, which actually seems to get called even though it
			// was added in the middle of the signal emission. so we must avoid adding
			// a second reference to child.
			return;
		}
		m_inputs.push_back( static_cast<PlugClass *>( child ) );
	}
}

template<typename PlugClass>
void InputGenerator<PlugClass>::childRemoved( Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child )
{
	m_inputs.erase( std::remove( m_inputs.begin(), m_inputs.end(), child ), m_inputs.end() );
}

template< typename PlugClass >
void InputGenerator<PlugClass>::inputChanged( Gaffer::Plug *plug )
{
	if( !plugValid( plug ) )
	{
		return;
	}

	if( const ScriptNode *script = plug->ancestor<ScriptNode>() )
	{
		if( script->currentActionStage() == Action::Undo ||
		    script->currentActionStage() == Action::Redo
		)
		{
			// if we're currently in an undo or redo, we don't
			// need to do anything, because our previous actions
			// will be in the undo queue and will be being replayed
			// for us automatically.
			return;
		}
	}

	if( plug->getInput<Plug>() )
	{
		// connection made. if it's the last plug
		// then we need to add one more.
		if( plug == *(m_inputs.rbegin()) && m_inputs.size() < m_maximumInputs )
		{
			PlugClassPtr p = IECore::runTimeCast<PlugClass>( m_prototype->createCounterpart( m_prototype->getName(), Plug::In ) );
			p->setFlags( Gaffer::Plug::Dynamic, true );
			m_parent->addChild( p );
		}
	}
	else
	{
		// connection broken. we need to remove any
		// unneeded unconnected plugs so that we have
		// only one unconnected plug at the end.
		std::vector<Plug *> toRemove;
		for( size_t i = m_inputs.size() - 1; i > m_minimumInputs - 1; --i )
		{
			if( m_inputs[i]->template getInput<Plug>() == 0 && m_inputs[i-1]->template getInput<Plug>() == 0 )
			{
				toRemove.push_back( m_inputs[i].get() );
			}
			else
			{
				break;
			}
		}

		if( toRemove.size() )
		{
			for( std::vector<Plug *>::const_iterator it = toRemove.begin(), eIt = toRemove.end(); it != eIt; ++it )
			{
				(*it)->parent<Gaffer::GraphComponent>()->removeChild( *it );
			}
		}
	}
}

} // namespace Behaviours
} // namespace Gaffer

