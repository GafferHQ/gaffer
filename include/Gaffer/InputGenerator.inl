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

namespace Gaffer
{

template< typename PlugClass >
void InputGenerator<PlugClass>::inputAdded( Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child )
{
	if( child->isInstanceOf( PlugClass::staticTypeId() ) && validateName( child->getName() ) )
	{
		// Rebuild our list of input plugs.
		m_inputs.clear();

		// Iterate over all of the inputs on the parent and add them to our array
		// if their name is valid.
		for( InputIterator it( m_parent ); it != it.end(); it++ )
		{
			if ( validateName( (*it)->getName() ) )
			{
				m_inputs.push_back( (*it).get() );
			}
		}
	}
}

template< typename PlugClass >
void InputGenerator<PlugClass>::inputChanged( Gaffer::Plug *plug )
{
	if( plug->isInstanceOf( PlugClass::staticTypeId() ) && validateName( plug->getName() ) )
	{
		updateInputs();
	}
}

template< typename PlugClass >
void InputGenerator<PlugClass>::updateInputs()
{
	m_lastConnected = -1;
	m_nConnectedInputs = 0;
	std::vector<PlugClass *> inputs;
	for( InputIterator it( m_parent ); it != it.end(); ++it )
	{
		if ( validateName( (*it)->getName() ) )
		{
			if( (*it)->template getInput<Plug>() )
			{
				m_lastConnected = inputs.size();
				++m_nConnectedInputs;
			}
			inputs.push_back( it->get() );
		}
	}

	int numInputs = (int)inputs.size();

	if( m_lastConnected == numInputs - 1)
	{
		if ( numInputs < (int)m_maximumInputs )
		{
			PlugClassPtr p = IECore::runTimeCast<PlugClass>( m_prototype->createCounterpart( m_prototype->getName(), Plug::In ) );
			m_parent->addChild( p );
		}
	}
	else
	{
		for( int i = std::max( m_lastConnected + 2, (int)m_minimumInputs ); i < numInputs; i++ )
		{
			m_parent->removeChild( inputs[i] );
			m_inputs.erase( m_inputs.begin()+i );
		}
	}
}

template< typename PlugClass >
typename std::vector< IECore::IntrusivePtr< PlugClass > >::const_iterator InputGenerator<PlugClass>::endIterator() const
{
	if ( m_inputs.size() > m_minimumInputs )
	{
		return m_inputs.begin()+m_lastConnected+1;
	}
	return m_inputs.begin()+m_minimumInputs;
}

template< typename PlugClass >
InputGenerator<PlugClass>::InputGenerator( Gaffer::Node *parent, PlugClassPtr plugPrototype, size_t min, size_t max ):
	m_parent( parent ),
	m_minimumInputs( min ),
	m_maximumInputs( max ),
	m_lastConnected( 0 ),
	m_nConnectedInputs( 0 ),
	m_nameValidator( std::string("^") + plugPrototype->getName().string() + std::string("[_0-9]*") ),
	m_prototype( plugPrototype )
{
	// The first of our inputs is always the prototype plug.
	m_inputs.clear();
	m_inputs.push_back( plugPrototype );

	// Check whether the parent already has an instance of the plugPrototype and if not, add it to the parent node.
	if ( !m_parent->isAncestorOf( plugPrototype ) )
	{
		m_parent->addChild( plugPrototype );
	}

	m_minimumInputs = std::max( min, size_t(1) );
	m_maximumInputs = std::max( max, m_minimumInputs );

	for ( unsigned int i = 1; i < m_minimumInputs; ++i )
	{
		PlugClassPtr p = IECore::runTimeCast<PlugClass>( plugPrototype->createCounterpart( plugPrototype->getName(), Plug::In ) );
		m_parent->addChild( p );
		m_inputs.push_back( p );
	}
	
	// Connect up the signals of the parent to our slots.
	m_parent->plugInputChangedSignal().connect( boost::bind( &InputGenerator<PlugClass>::inputChanged, this, ::_1 ) );
	m_parent->childAddedSignal().connect( boost::bind( &InputGenerator<PlugClass>::inputAdded, this, ::_1, ::_2 ) );
}

} // namespace gaffer

