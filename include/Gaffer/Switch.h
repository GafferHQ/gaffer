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

#ifndef GAFFER_SWITCH_H
#define GAFFER_SWITCH_H

#include "boost/utility/enable_if.hpp"

#include "Gaffer/Behaviours/InputGenerator.h"

#include "Gaffer/ComputeNode.h"
#include "Gaffer/NumericPlug.h"

namespace Gaffer
{

/// The Switch provides a generic base class to implement nodes which choose
/// between many input branches, feeding only one of them to the output.
/// The series of input branches are represented by plugs of identical type
/// and called "in", "in1", "in2" etc, and the output is a plug of the same
/// type named "out".
///
/// Switches can be instantiated in either of two ways :
///
/// - By instantiating Switch<BaseType> where BaseType creates an "in" and
/// and "out" plug during construction. This is the method used to create
/// the SceneSwitch and ImageSwitch.
///
/// - By adding dynamic "in" and "out" plugs to a generic Switch node after
/// construction. This method can be seen in the GafferTest.SwitchTest
/// test cases.
///
/// \todo It would be better to use an ArrayPlug for the inputs, but because
/// this class must be useable with the SceneProcessor and ImageProcessor classes
/// we must wait until those classes themselves use ArrayPlugs.
template<typename BaseType>
class Switch : public BaseType
{

	public :

		IECORE_RUNTIMETYPED_DECLARETEMPLATE( Switch<BaseType>, BaseType );

		Switch( const std::string &name=GraphComponent::defaultName<Switch>() );
		virtual ~Switch();

		IntPlug *indexPlug();
		const IntPlug *indexPlug() const;

		virtual BoolPlug *enabledPlug();
		virtual const BoolPlug *enabledPlug() const;

		virtual Plug *correspondingInput( const Plug *output );
		virtual const Plug *correspondingInput( const Plug *output ) const;

		virtual void affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const;

	protected :

		// Implemented to reject ComputeNode inputs to "index" and "enabled" if we ourselves
		// are not a ComputeNode, and to reject input branches inputs if they wouldn't
		// be accepted by the output.
		virtual bool acceptsInput( const Plug *plug, const Plug *inputPlug ) const;

		// The hash() and compute() methods are implemented to pass through the results from
		// the input branch specified by indexPlug(). They operate via the hashInternal() and
		// computeInternal() methods, which are specialised for the cases where we do and do
		// not inherit from ComputeNode.
		virtual void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( ValuePlug *output, const Context *context ) const;

	private :

		// The internal implementation for hash(). Does nothing when BaseType is not a ComputeNode,
		// and passes through the hash from the appropriate input when it is.
		template<typename T>
		void hashInternal( const ValuePlug *output, const Context *context, IECore::MurmurHash &h, typename boost::enable_if<boost::is_base_of<ComputeNode, T> >::type *enabler = 0 ) const;
		template<typename T>
		void hashInternal( const ValuePlug *output, const Context *context, IECore::MurmurHash &h, typename boost::disable_if<boost::is_base_of<ComputeNode, T> >::type *enabler = 0 ) const;

		// The internal implementation for compute(). Does nothing when BaseType is not a ComputeNode,
		// and passes through the value from the appropriate input when it is.
		template<typename T>
		void computeInternal( ValuePlug *output, const Context *context, typename boost::enable_if<boost::is_base_of<ComputeNode, T> >::type *enabler = 0 ) const;
		template<typename T>
		void computeInternal( ValuePlug *output, const Context *context, typename boost::disable_if<boost::is_base_of<ComputeNode, T> >::type *enabler = 0 ) const;

		void childAdded( GraphComponent *child );
		void plugSet( Plug *plug );
		size_t inputIndex() const;
		// Returns the input corresponding to the output and vice versa. Returns NULL
		// if plug is not meaningful to the switching process.
		const Plug *oppositePlug( const Plug *plug, size_t inputIndex = 0 ) const;

		void updateInternalConnection();

		boost::shared_ptr<Gaffer::Behaviours::InputGenerator<Plug> > m_inputGenerator;

		IE_CORE_DECLARERUNTIMETYPEDDESCRIPTION( Switch<BaseType> );
		static size_t g_firstPlugIndex;

};

typedef Switch<DependencyNode> SwitchDependencyNode;
typedef Switch<ComputeNode> SwitchComputeNode;

IE_CORE_DECLAREPTR( SwitchDependencyNode );
IE_CORE_DECLAREPTR( SwitchComputeNode );

} // namespace Gaffer

#endif // GAFFER_SWITCH_H
