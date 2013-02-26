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
	if( child->isInstanceOf( PlugClass::staticTypeId() ) )
	{
		// Remove all inputs apart from the minimum number of plugs.
		m_inputs.resize( m_minimumInputs );

		// Create an iterator to loop over the inputs. Skip the first element
		// as we know that it is the input prototype.	
		InputIterator it( m_parent );
		if ( it != it.end() ) it++;

		// Now iterate over all of the other inputs on the parent and add them to our array.
		while( it != it.end() )
		{
			///\TODO: Check here whether the plug that (*it) has the same name as our prototype.
			// This will allow each InputGenerator to only manage the plugs which are copies of the
			// origonal prototype.
			m_inputs.push_back( (*it++).get() );
		}
	}
}

template< typename PlugClass >
void InputGenerator<PlugClass>::inputChanged( Gaffer::Plug *plug )
{
	if( plug->isInstanceOf( PlugClass::staticTypeId() ) )
	{
		updateInputs();
	}
}

template< typename PlugClass >
void InputGenerator<PlugClass>::updateInputs()
{
	int lastConnected = -1;
	std::vector<PlugClass *> inputs;
	for( InputIterator it( m_parent ); it != it.end(); ++it )
	{
		if( (*it)->template getInput<Plug>() )
		{
			lastConnected = inputs.size();
		}
		inputs.push_back( it->get() );
	}

	int numInputs = (int)inputs.size();

	if( lastConnected == numInputs - 1)
	{
		if ( numInputs < (int)m_maximumInputs )
		{
			m_parent->addChild( m_inputs[0]->createCounterpart( m_inputs[0]->getName(), Plug::In ) );
		}
	}
	else
	{
		for( int i = std::max( lastConnected + 2, (int)m_minimumInputs ); i < numInputs; i++ )
		{
			m_parent->removeChild( inputs[i] );
			m_inputs.erase( m_inputs.begin()+i );
		}
	}
}

template< typename PlugClass >
InputGenerator<PlugClass>::InputGenerator( Gaffer::Node *parent, PlugClassPtr plugPrototype, size_t min, size_t max ):
	m_parent( parent ),
	m_minimumInputs( min ),
	m_maximumInputs( max )
{
	// The first of our inputs is always the prototype plug.
	m_inputs.clear();
	m_inputs.push_back( plugPrototype );
	m_parent->addChild( plugPrototype );

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

