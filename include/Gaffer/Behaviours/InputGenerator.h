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

#ifndef GAFFER_BEHAVIOURS_INPUTGENERATOR_H
#define GAFFER_BEHAVIOURS_INPUTGENERATOR_H

#include <vector>

#include "boost/regex.hpp"

#include "Gaffer/Plug.h"
#include "Gaffer/PlugIterator.h"
#include "Gaffer/Node.h"
#include "Gaffer/Behaviours/Behaviour.h"

namespace Gaffer
{

namespace Behaviours
{

/// InputGenerator creates and maintains a minimum and optional set of inputs.
/// The InputGenerator creates and manages a set of input plugs based on a desired minimum and maximum number.
/// It keeps a list of all of the inputs that are currently visible on the nodes UI's and will create optional inputs
/// when the number of connections to the node is greater than the minumum but less than the maximum. The InputGenerator
/// has a hard minimum limit of 1 input plug that it will create.
/// To use the InputGenerator, create a static instance of it within your node and call createInputs within the
/// node's constructor.
template< class PlugClass >
class InputGenerator : public Behaviour
{
	public :

		typedef Gaffer::FilteredChildIterator< Gaffer::PlugPredicate<Gaffer::Plug::In, PlugClass> > InputIterator;
		typedef IECore::IntrusivePtr< PlugClass > PlugClassPtr;
		typedef IECore::IntrusivePtr< const PlugClass > ConstPlugClassPtr;	

		/// The constructor initializes the InputGenerator and creates the minimum number of inputs requested.
		/// It connects up the parent's signals to internal slots that manage the list of inputs that it holds.
		/// @param parent The parent node that the InputGenerator is a static member of.
		/// @param plugPrototype The first of the input plugs to create. This is used as a template from which the other plugs are created.
		/// @param min The minimum number of input plugs that the InputGenerator will create. There is a hard limit of 1.
		/// @param max The maximum number of input plugs that the InputGenerator will create. This cannot fall below min however, if it is
		///            greater than min a set of (max-min) optional inputs will be created and managed.
		InputGenerator( Gaffer::Node *parent, PlugClassPtr plugPrototype, size_t min, size_t max  );

		/// Returns the minimum number of inputs of type PlugClass that will appear on the node.
		inline size_t minimumInputs() const { return m_minimumInputs; };

		/// Returns the maximum number of inputs of type PlugClass that will appear on the node.
		inline size_t maximumInputs() const { return m_maximumInputs; };

		/// Returns the number of inputs that are connected.
		inline unsigned int nConnectedInputs() const { return m_nConnectedInputs; };
		
		/// Returns a vector of the input plugs which are visible on the node.
		inline const std::vector<PlugClassPtr> &inputs() const { return m_inputs; };
		inline std::vector<PlugClassPtr> &inputs() { return m_inputs; };

		// Returns a past-the-end iterator to mark the end of the last input plug that could be in use in the node graph.
		// This is implemented because in the the case of optional inputs being present on the parent node, the last input is
		// never connected as it's only purpose is to exist in waiting for a connection.
		typename std::vector<PlugClassPtr>::const_iterator endIterator() const;
		
	private :
		
		inline bool validateName( const std::string &name ) { return regex_match( name.c_str(), m_nameValidator ); }
		void inputAdded( Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child );
		void inputChanged( Gaffer::Plug *plug );
		void updateInputs();

		/// Pointer to the parent node that inputs will be instantiated upon.
		Gaffer::Node *m_parent;

		/// Variables to hold the minimum and maximum number of inputs from which
		/// the number of optional inputs are derived.
		size_t m_minimumInputs;
		size_t m_maximumInputs;

		/// The index of the last input that is connected to node. This is particularly
		/// useful when wanting to iterate over the inputs on the node that have connections.
		unsigned short m_lastConnected;
	
		/// The number of inputs that are connected.
		unsigned short m_nConnectedInputs;
		
		/// The vector which holds the inputs that are visible on the node.
		/// This vector will always hold the minimum number of inputs defined
		/// within the constructor. It can never exceed the maximum number of inputs.
		std::vector<PlugClassPtr> m_inputs;

		/// A regular expression which is used to test whether inputs of the parent node are instances
		/// of the plugPrototype which is passed into the constructor.
		boost::regex m_nameValidator;

		/// A pointer to the plug that we will use as our prototype for creating more.
		PlugClassPtr m_prototype;

};

} // namespace Behaviours
} // namespace Gaffer


#include "Gaffer/Behaviours/InputGenerator.inl"

#endif // GAFFER_BEHAVIOURS_INPUTGENERATOR_H

