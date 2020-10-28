//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_BOXIO_H
#define GAFFER_BOXIO_H

#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"
#include "Gaffer/TypedPlug.h"

namespace GafferModule
{

// Forward declaration to enable friend declaration
class BoxIOSerialiser;

} // namespace GafferModule

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )
IE_CORE_FORWARDDECLARE( Box )
IE_CORE_FORWARDDECLARE( Switch )

/// Utility node for representing plug promotion
/// graphically in the GraphEditor. Note that this has
/// no special priviledges or meaning in the Box API;
/// it is merely a convenience for the user.
///
/// In terms of structure, BoxIO is much like
/// a Dot, with an internal pass-through connection
/// between a single input plug and a single output plug.
/// It differs in that one of these plugs is
/// always private and managed such that it is
/// automatically promoted to any parent Box. Which plug
/// is promoted is determined by the BoxIO's direction,
/// which specifies whether it provides an input or
/// output for the box.
///
/// The BoxIO constructor is protected. Construct
/// the derived BoxIn and BoxOut classes rather than
/// attempt to construct BoxIO itself.
class GAFFER_API BoxIO : public Node
{

	public :

		~BoxIO() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::BoxIO, BoxIOTypeId, Node );

		StringPlug *namePlug();
		const StringPlug *namePlug() const;

		/// Sets this node up using `plug`
		/// as a prototype. Call this after
		/// construction to determine what
		/// sort of plug this node will promote.
		void setup( const Plug *plug );
		/// Sets up the promoted plug on the parent box.
		/// This is called automatically by `setup()`, so
		/// there is no need to call it unless `setup()`
		/// was called before parenting the BoxIO to a Box.
		void setupPromotedPlug();

		/// The internal plug which
		/// can be used within the box.
		/// Will be null unless `setup()`
		/// has been called.
		template<typename T=Plug>
		T *plug();
		template<typename T=Plug>
		const T *plug() const;

		/// The external plug which has
		/// been promoted to the outside
		/// of the box. Will be null unless
		/// `setup()` has been called.
		template<typename T=Plug>
		T *promotedPlug();
		template<typename T=Plug>
		const T *promotedPlug() const;

		Plug::Direction direction() const;

		/// Static utility methods
		/// ======================
		///
		/// Equivalent to `PlugAlgo::promote()`, but
		/// inserting an intermediate BoxIO node where
		/// relevant (based on querying nodule layout
		/// metadata).
		/// \undoable
		static Plug *promote( Plug *plug );
		/// Inserts intermediate BoxIO nodes for any
		/// promoted plugs that require them (based
		/// on querying nodule layout metadata). This
		/// can be used to upgrade boxes that were
		/// either authored in the pre-BoxIO era, or
		/// were created by automated scripts that
		/// are not BoxIO savvy.
		/// \undoable
		static void insert( Box *box );
		/// Returns true if `insert( box )` would
		/// do anything.
		/// \undoable
		static bool canInsert( const Box *box );

	protected :

		BoxIO( Plug::Direction direction, const std::string &name=defaultName<BoxIO>() );

		Gaffer::Plug *inPlugInternal();
		const Gaffer::Plug *inPlugInternal() const;

		Gaffer::Plug *outPlugInternal();
		const Gaffer::Plug *outPlugInternal() const;

		Gaffer::Plug *passThroughPlugInternal();
		const Gaffer::Plug *passThroughPlugInternal() const;

		BoolPlug *enabledPlugInternal();
		const BoolPlug *enabledPlugInternal() const;

		void parentChanging( Gaffer::GraphComponent *newParent ) override;
		void parentChanged( Gaffer::GraphComponent *oldParent ) override;

	private :

		friend class GafferModule::BoxIOSerialiser;

		IECore::InternedString inPlugName() const;
		IECore::InternedString outPlugName() const;

		Gaffer::Switch *switchInternal();
		const Gaffer::Switch *switchInternal() const;

		Plug::Direction m_direction;

		boost::signals::scoped_connection m_promotedPlugNameChangedConnection;
		boost::signals::scoped_connection m_promotedPlugParentChangedConnection;

		void setupPassThrough();
		void setupBoxEnabledPlug();
		void scriptExecuted( ScriptNode *script );
		void plugSet( Plug *plug );
		void plugInputChanged( Plug *plug );
		void promotedPlugNameChanged( GraphComponent *graphComponent );
		void promotedPlugParentChanged( GraphComponent *graphComponent );

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( BoxIO )

/// \deprecated Use BoxIO::Iterator etc instead.
typedef FilteredChildIterator<TypePredicate<BoxIO> > BoxIOIterator;
typedef FilteredRecursiveChildIterator<TypePredicate<BoxIO> > RecursiveBoxIOIterator;

} // namespace Gaffer

#include "Gaffer/BoxIO.inl"

#endif // GAFFER_BOXIO_H
