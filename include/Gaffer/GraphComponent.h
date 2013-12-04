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

#ifndef GAFFER_GRAPHCOMPONENT_H
#define GAFFER_GRAPHCOMPONENT_H

#include "boost/signals.hpp"

#include "IECore/RunTimeTyped.h"
#include "IECore/InternedString.h"

#include "Gaffer/TypeIds.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( GraphComponent )

template<typename T>
class TypePredicate;

template<typename Predicate>
class FilteredChildIterator;

template<typename Predicate, typename RecursionPredicate>
class FilteredRecursiveChildIterator;

class GraphComponent : public IECore::RunTimeTyped, public boost::signals::trackable
{

	public :

		GraphComponent( const std::string &name=defaultName<GraphComponent>() );
		virtual ~GraphComponent();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::GraphComponent, GraphComponentTypeId, IECore::RunTimeTyped );

		typedef boost::signal<void (GraphComponent *)> UnarySignal;
		typedef boost::signal<void (GraphComponent *, GraphComponent *)> BinarySignal;
		
		/// @name Naming
		/// All GraphComponents have a name, which must be unique among
		/// siblings. Names may contain only A-Z, a-z, _ and 0-9, with the
		/// additional constraint that they must not start with a number.
		////////////////////////////////////////////////////////////////////
		//@{
		/// Sets the name for this component. Note that the requested name
		/// may have a numeric suffix appended to keep the name unique within
		/// parent(), and illegal characters may be replaced - for this reason
		/// the new name is returned.
		/// \undoable
		const IECore::InternedString &setName( const IECore::InternedString &name );
		/// Returns the name for this component.
		const IECore::InternedString &getName() const;
		/// Returns the full path name from the topmost parent to this component.
		std::string fullName() const;
		/// Returns the relative path name from the specified ancestor to this component.
		/// Passing 0 for ancestor yields the same result as calling fullName().
		std::string relativeName( const GraphComponent *ancestor ) const;
		/// A signal which is emitted whenever a name is changed.
		UnarySignal &nameChangedSignal();
		/// Returns T::staticTypeName() without namespace prefixes, for use as the
		/// default name in GraphComponent constructors.
		template<typename T>
		static std::string defaultName();
		//@}
		
		/// @name Parent-child relationships
		/// GraphComponents are structured through parent-child
		/// relationships. A GraphComponent may have many children but may
		/// have only one parent. Methods are provided whereby children can be added and
		/// removed from a GraphComponent, and GraphComponents can specify
		/// which children and/or parents they are willing to accept.
		////////////////////////////////////////////////////////////////////
		//@{
		/// The datatype used internally to store children.
		typedef std::vector<GraphComponentPtr> ChildContainer;
		typedef ChildContainer::const_iterator ChildIterator;
		/// Components can accept or reject potential children by implementing this
		/// call. By default all children are accepted.
		virtual bool acceptsChild( const GraphComponent *potentialChild ) const;
		/// Components can accept or reject potential parents by implementing this
		/// call. By default all parents are accepted.
		virtual bool acceptsParent( const GraphComponent *potentialParent ) const;
		/// Adds a child to this component. If the child already has a parent it
		/// will first be removed from it. Note that the child may be renamed to
		/// preserve uniqueness, and an exception is thrown if the child or
		/// parent doesn't accept the new relationship.
		/// \todo Prevent reparenting from changing the ScriptNode ancestor of the child -
		/// this would seriously mess up the undo system.
		/// \undoable
		void addChild( GraphComponentPtr child );
		/// Adds a child to this component, giving it the specified name. If a child
		/// of that name already exists then it will be replaced. If the
		/// child already has a parent then it is first removed from it. An exception is
		/// thrown if the child or parent doesn't accept the new relationship.
		/// \undoable
		void setChild( const IECore::InternedString &name, GraphComponentPtr child );
		/// Removes a child. Throws an Exception if the passed component is
		/// not a child of this component.
		/// \todo Do we need acceptsRemoval()?
		/// \undoable
		void removeChild( GraphComponentPtr child );
		/// Removes all the children.
		/// \undoable
		void clearChildren();
		/// Get an immediate child by name, performing a runTimeCast to T.
		template<typename T>
		T *getChild( const IECore::InternedString &name );
		/// Get an immediate child by name, performing a runTimeCast to T.
		template<typename T>
		const T *getChild( const IECore::InternedString &name ) const;
		/// Get a child by index, performing a runTimeCast to T.
		/// Note that this function does not perform any bounds checking.
		template<typename T>
		inline T *getChild( size_t index );
		/// Get a child by index, performing a runTimeCast to T.
		/// Note that this function does not perform any bounds checking.
		template<typename T>
		inline const T *getChild( size_t index ) const;		
		/// Read only access to the internal container of children. This
		/// is useful for iteration over children.
		const ChildContainer &children() const;
		/// Returns a descendant of this node specified by a "." separated
		/// relative path, performing a runTimeCast to T.
		template<typename T>
		inline T *descendant( const std::string &relativePath );
		/// Returns a descendant of this node specified by a "." separated
		/// relative path, performing a runTimeCast to T.
		template<typename T>
		inline const T *descendant( const std::string &relativePath ) const;
		/// Returns the parent for this component, performing a runTimeCast to T.
		template<typename T>
		T *parent();
		/// Returns the parent for this component, performing a runTimeCast to T.
		template<typename T>
		const T *parent() const;
		/// Returns the first ancestor of type T.
		template<typename T>
		T *ancestor();
		/// Returns the first ancestor of type T.
		template<typename T>
		const T *ancestor() const;
		/// As above, but taking a TypeId to specify type - this is mainly provided for the binding.
		GraphComponent *ancestor( IECore::TypeId ancestorType );
		const GraphComponent *ancestor( IECore::TypeId ancestorType ) const;
		/// Returns the first ancestor of type T which
		/// is also an ancestor of other.
		template<typename T>
		T *commonAncestor( const GraphComponent *other );
		/// Returns the first ancestor of type T which
		/// is also an ancestor of other.
		template<typename T>
		const T *commonAncestor( const GraphComponent *other ) const;
		/// As above, but taking a TypeId to specify type - this is mainly provided for the binding.
		GraphComponent *commonAncestor( const GraphComponent *other, IECore::TypeId ancestorType );
		const GraphComponent *commonAncestor( const GraphComponent *other, IECore::TypeId ancestorType ) const;
		/// Returns true if this GraphComponent is an ancestor (or direct parent) of other.
		bool isAncestorOf( const GraphComponent *other ) const;
		/// A signal emitted when a child is added to this component. Slots should
		/// be of the form void ( parent, child ).
		BinarySignal &childAddedSignal();
		/// A signal emitted when a child is removed from this component. Slot format
		/// is as above.
		BinarySignal &childRemovedSignal();
		/// A signal emitted when the parent of this component changes. Slots should
		/// be of the form void ( child, oldParent ). Note that in the special case
		/// of a child being removed from the destructor of the parent, oldParent
		/// will be 0 as it is no longer available.
		BinarySignal &parentChangedSignal();
		//@}
	
	protected :
	
		/// Called just /before/ the parent of this GraphComponent is
		/// changed to newParent. This is an opportunity to do things
		/// in preparation for the new relationship - currently it allows
		/// Plugs to remove their connections if they're about to have no parent.
		/// In the special case of a child being removed from the destructor of the
		/// parent, parent() will already be 0 in addition to newParent
		/// being 0 - this is to avoid the temptation to access the dying parent.
		///
		/// Implementations should call the base class implementation
		/// before doing their own thing.
		///
		/// The rationale for not having this as a public signal is that
		/// outside observers don't need the priviledge of knowing events
		/// beforehand - they should just react to them afterwards. The
		/// rationale for having this as a virtual function rather than
		/// a protected signal is that there is less overhead in the virtual
		/// function. 
		virtual void parentChanging( Gaffer::GraphComponent *newParent );
		
		/// It is common for derived classes to provide accessors for
		/// constant-time access to specific children, as this can be
		/// much quicker than a call to getChild<>( name ). This function
		/// helps in implementing such accessors by storing the index for
		/// the next child to be added - it should therefore be called
		/// from a constructor before children are added, and the offset can
		/// then be used for constant-time access of subsequent children
		/// using getChild<>( index + offset ). It is common for the index
		/// variable to be a static member of the class, as it shouldn't vary
		/// from instance to instance, and storeIndexOfNextChild() will error
		/// if it discovers that not to be the case.
		void storeIndexOfNextChild( size_t &index ) const;
				
	private :
	
		static std::string unprefixedTypeName( const char *typeName );

		void throwIfChildRejected( const GraphComponent *potentialChild ) const;
		void setNameInternal( const IECore::InternedString &name );
		void addChildInternal( GraphComponentPtr child );
		void removeChildInternal( GraphComponentPtr child, bool emitParentChanged );

		/// \todo The memory overhead of all these signals may become too great.
		/// At this point we need to reimplement the signal returning functions to
		/// create the signals on the fly (and possibly to delete signals when they have
		/// no connections). One method might be to store a static map from this to signal *.
		/// Or alternatively we could make all the signals static. Both these trade off
		/// reduced memory usage for slower execution.
		UnarySignal m_nameChangedSignal;
		BinarySignal m_childAddedSignal;
		BinarySignal m_childRemovedSignal;
		BinarySignal m_parentChangedSignal;
		
		IECore::InternedString m_name;
		GraphComponent *m_parent;
		ChildContainer m_children;

};

} // namespace Gaffer

#include "Gaffer/GraphComponent.inl"

#endif // GAFFER_GRAPHCOMPONENT_H
