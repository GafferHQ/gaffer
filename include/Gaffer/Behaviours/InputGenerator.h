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

#include "Gaffer/Plug.h"
#include "Gaffer/PlugIterator.h"
#include "Gaffer/Node.h"
#include "Gaffer/Behaviours/Behaviour.h"

namespace Gaffer
{

namespace Behaviours
{

/// The InputGenerator is a behaviour for the on-demand creation of a variable number of
/// input plugs. The minimum and maximum number of inputs may be specified, and the generator
/// will ensure that there is always an unconnected plug available within these constraints.
/// \todo Add method to return the next available plug.
template< class PlugClass >
class InputGenerator : public Behaviour
{
	public :

		typedef IECore::IntrusivePtr< PlugClass > PlugClassPtr;
		typedef IECore::IntrusivePtr< const PlugClass > ConstPlugClassPtr;	

		/// The constructor initializes the InputGenerator and creates the minimum number of inputs requested.
		/// It connects up the ancestor Node's signals to internal slots that manage the list of inputs that it holds.
		/// @param parent The parent that plugs will be added to. This may be either a Node or a CompoundPlug.
		/// @param plugPrototype The first of the input plugs to create. This is used as a template from which the other plugs are created.
		/// @param minInputs The minimum number of input plugs that the InputGenerator will create. There is a hard limit of 1.
		/// @param maxInputs The maximum number of input plugs that the InputGenerator will create. This cannot fall below min however, if it is
		///            greater than min a set of (max-min) optional inputs will be created and managed.
		InputGenerator( Gaffer::GraphComponent *parent, PlugClassPtr plugPrototype, size_t minInputs=1, size_t maxInputs=Imath::limits<size_t>::max()  );

		/// Returns the minimum number of inputs that will be maintained.
		inline size_t minimumInputs() const { return m_minimumInputs; };

		/// Returns the maximum number of inputs that will be maintained.
		inline size_t maximumInputs() const { return m_maximumInputs; };
		
		/// Returns a vector of the input plugs which are being maintained.
		/// \todo The only reason this class is templated is so that this vector contains pointers
		/// of the desired type and can therefore be used without casts. Consider
		/// reimplementing without templates, returning vector<GraphComponentPtr> from inputs(),
		/// and using the various FilteredChildIterators with it to avoid casts in client code.
		inline const std::vector<PlugClassPtr> &inputs() const { return m_inputs; };
		inline std::vector<PlugClassPtr> &inputs() { return m_inputs; };

		/// \deprecated.
		typename std::vector<PlugClassPtr>::const_iterator endIterator() const;
		/// Returns the number of inputs that are connected.
		/// \deprecated. This encourages Node::compute() implementations to treat unconnected
		/// Plugs differently to connected plugs, which isn't desirable.
		size_t nConnectedInputs() const;

	private :
		
		// Returns true if the specified plug is one that should be managed by us.
		bool plugValid( const Plug *plug );
		void childAdded( Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child );
		void childRemoved( Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child );
		void inputChanged( Gaffer::Plug *plug );

		/// Pointer to the parent node or plug that inputs will be instantiated upon.
		Gaffer::GraphComponent *m_parent;

		/// Variables to hold the minimum and maximum number of inputs from which
		/// the number of optional inputs are derived.
		const size_t m_minimumInputs;
		const size_t m_maximumInputs;
		
		/// The vector which holds the inputs that are visible on the node.
		/// This vector will always hold the minimum number of inputs defined
		/// within the constructor. It can never exceed the maximum number of inputs.
		std::vector<PlugClassPtr> m_inputs;

		/// A pointer to the plug that we will use as our prototype for creating more.
		PlugClassPtr m_prototype;

};

} // namespace Behaviours
} // namespace Gaffer


#include "Gaffer/Behaviours/InputGenerator.inl"

#endif // GAFFER_BEHAVIOURS_INPUTGENERATOR_H

