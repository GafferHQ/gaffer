//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_NODEGADGET_H
#define GAFFERUI_NODEGADGET_H

#include "GafferUI/IndividualContainer.h"

#include "Gaffer/Set.h"

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( Nodule )
IE_CORE_FORWARDDECLARE( NodeGadget )

/// A base class for representing nodes within a GraphGadget.
class NodeGadget : public IndividualContainer
{

	public :

		virtual ~NodeGadget();
		
		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::NodeGadget, NodeGadgetTypeId, ContainerGadget );
		
		Gaffer::Node *node();
		const Gaffer::Node *node() const;

		/// Should be overridden by derived classes to return a nodule for
		/// the plug if it has one, and 0 otherwise.
		virtual Nodule *nodule( const Gaffer::Plug *plug );
		virtual const Nodule *nodule( const Gaffer::Plug *plug ) const;
		/// Returns the tangent for a nodule - this is a direction which
		/// can be considered to be "away" from the NodeGadget for the
		/// purposes of drawing connections.
		virtual Imath::V3f noduleTangent( const Nodule *nodule ) const;
				
		/// Creates a NodeGadget for the specified node.
		static NodeGadgetPtr create( Gaffer::NodePtr node );
		
		typedef boost::function<NodeGadgetPtr ( Gaffer::NodePtr )> NodeGadgetCreator;
		/// Registers a function which will return a NodeGadget instance for a node of a specific
		/// type. This can be used to customise the NodeGadget for specific node types.
		static void registerNodeGadget( IECore::TypeId nodeType, NodeGadgetCreator creator );

		virtual std::string getToolTip( const IECore::LineSegment3f &line ) const;
		
	protected :

		NodeGadget( Gaffer::NodePtr node );
	
		/// Creating a static one of these is a convenient way of registering a NodeGadget type.
		template<class T>
		struct NodeGadgetTypeDescription
		{
			NodeGadgetTypeDescription( IECore::TypeId nodeType ) { NodeGadget::registerNodeGadget( nodeType, &creator ); };
			static NodeGadgetPtr creator( Gaffer::NodePtr node ) { return new T( node ); };
		};
		
	private :
				
		Gaffer::Node *m_node;
		
		typedef std::map<IECore::TypeId, NodeGadgetCreator> CreatorMap;
		static CreatorMap &creators();
		
};

IE_CORE_DECLAREPTR( NodeGadget );

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<NodeGadget> > NodeGadgetIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<NodeGadget> > RecursiveNodeGadgetIterator;

} // namespace GafferUI

#endif // GAFFERUI_NODEGADGET_H
