//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_CONNECTIONGADGET_H
#define GAFFERUI_CONNECTIONGADGET_H

#include "boost/regex.hpp"

#include "Gaffer/Plug.h"

#include "GafferUI/Gadget.h"

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( Nodule )
IE_CORE_FORWARDDECLARE( ConnectionGadget )

/// ConnectionGadgets are responsible for drawing the Connections between
/// Nodules in the node graph, and for implementing the drag and drop of
/// those connections. The ConnectionsGadget base class is an abstract class -
/// see StandardConnectionGadget for a concrete implementation suitable for
/// most purposes. ConnectionGadget provides a factory mechanism whereby
/// different creation methods can be called for different plugs on different
/// nodes - this allows the customisation of connection display. The most
/// common customisation would be to apply a different style or custom
/// tooltip - see ConnectionGadgetTest for an example.
class ConnectionGadget : public Gadget
{

	public :

		virtual ~ConnectionGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::ConnectionGadget, ConnectionGadgetTypeId, Gadget );

		/// Accepts only GraphGadgets as parent.
		virtual bool acceptsParent( const Gaffer::GraphComponent *potentialParent ) const;

		/// Returns the Nodule representing the source plug in the connection.
		/// Note that this may be NULL if the source plug belongs to a node which
		/// has been hidden.
		Nodule *srcNodule();
		const Nodule *srcNodule() const;
		/// Returns the Nodule representing the destination plug in the connection.
		Nodule *dstNodule();
		const Nodule *dstNodule() const;
		/// May be called to change the connection represented by this gadget.
		/// Derived classes may reimplement this method but implementations
		/// must call the base class implementation first.
		virtual void setNodules( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule );

		/// A minimised connection is drawn only as a small stub
		/// entering the destination nodule - this can be useful in
		/// uncluttering a complex graph.
		void setMinimised( bool minimised );
		bool getMinimised() const;

		/// Setter and getter for highlighting state
		void setHighlighted( bool state );
		bool getHighlighted() const;

		/// May be called by the recipient of a drag to set a more appropriate position
		/// and tangent for the connection as the drag progresses within the destination.
		/// Throws if this connection is not currently the source of a connection.
		virtual void updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent ) = 0;

		/// Returns the closest point on this connection to the given point.
		/// Used for snapping new dots onto an existing connection
		virtual Imath::V3f closestPoint( const Imath::V3f &p ) const = 0;

		/// Creates a ConnectionGadget to represent the connection between the two
		/// specified Nodules.
		static ConnectionGadgetPtr create( NodulePtr srcNodule, NodulePtr dstNodule );

		typedef boost::function<ConnectionGadgetPtr ( NodulePtr, NodulePtr )> ConnectionGadgetCreator;
		/// Registers a function which will return a ConnectionGadget instance for a
		/// destination plug of a specific type.
		static void registerConnectionGadget( IECore::TypeId dstPlugType, ConnectionGadgetCreator creator );
		/// Registers a function which will return a Nodule instance for destination plugs with
		/// specific names on a specific type of node. Nodules registered in this way will take
		/// precedence over those registered above.
		static void registerConnectionGadget( const IECore::TypeId nodeType, const std::string &dstPlugPathRegex, ConnectionGadgetCreator creator );

	protected :

		ConnectionGadget( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule );

		/// Creating a static one of these is a convenient way of registering a ConnectionGadget type.
		template<class T>
		struct ConnectionGadgetTypeDescription
		{
			ConnectionGadgetTypeDescription( IECore::TypeId dstPlugType ) { ConnectionGadget::registerConnectionGadget( dstPlugType, &creator ); };
			static ConnectionGadgetPtr creator( NodulePtr srcNodule, NodulePtr dstNodule ) { return new T( srcNodule, dstNodule ); };
		};

	private :

		NodulePtr m_srcNodule;
		NodulePtr m_dstNodule;

		bool m_minimised;
		bool m_highlighted;

		typedef std::map<IECore::TypeId, ConnectionGadgetCreator> CreatorMap;
		static CreatorMap &creators();

		typedef std::pair<boost::regex, ConnectionGadgetCreator> RegexAndCreator;
		typedef std::vector<RegexAndCreator> RegexAndCreatorVector;
		typedef std::map<IECore::TypeId, RegexAndCreatorVector> NamedCreatorMap;
		static NamedCreatorMap &namedCreators();


};

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<ConnectionGadget> > ConnectionGadgetIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<ConnectionGadget> > RecursiveConnectionGadgetIterator;

} // namespace GafferUI

#endif // GAFFERUI_CONNECTIONGADGET_H
