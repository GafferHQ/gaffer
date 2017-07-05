//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2011-2015, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_PATH_H
#define GAFFER_PATH_H

#include "boost/signals.hpp"

#include "IECore/RunTimeTyped.h"
#include "IECore/InternedString.h"
#include "IECore/CompoundData.h"

#include "Gaffer/Export.h"
#include "Gaffer/TypeIds.h"

namespace GafferBindings
{

// Forward declaration for friendship declared below.
// We don't include PathBinding.h because we don't want
// python involved in any way when building the pure C++
// modules.
GAFFER_IMPORT void bindPath();

}

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Path )
IE_CORE_FORWARDDECLARE( PathFilter )

/// The Path base class provides an abstraction for traversing a hierarchy
/// of items by name, and retrieving properties from them. Examples of intended
/// uses include querying a filesystem, exploring a cache file, or navigating
/// a scene graph.
///
/// A path is represented by a root location followed by a series of names
/// which refer to items nested below the root.
class GAFFER_API Path : public IECore::RunTimeTyped
{

	public :

		typedef std::vector<IECore::InternedString> Names;

		Path( PathFilterPtr filter = NULL );
		Path( const std::string &path, PathFilterPtr filter = NULL );
		Path( const Names &names, const IECore::InternedString &root = "/", PathFilterPtr filter = NULL );

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Path, PathTypeId, IECore::RunTimeTyped );

		virtual ~Path();

		/// Returns the root of the path - this will be "/" for absolute
		/// paths and "" for relative paths.
		const IECore::InternedString &root() const;

		/// Returns true if this path is empty.
		const bool isEmpty() const;

		/// Returns true if this path is valid - ie references something
		/// which actually exists.
		virtual bool isValid() const;

		/// Returns true if this path can never have child Paths.
		virtual bool isLeaf() const;

		/// Fills the vector with the names of all the properties queryable via property().
		/// Derived class implementations must call the base class implementation first.
		virtual void propertyNames( std::vector<IECore::InternedString> &names ) const;
		/// Queries a property, whose name must have first been retrieved via propertyNames().
		/// Derived class implementations should fall back to the base class implementation for
		/// any unrecognised names. Returns NULL for unknown properties. May return NULL for invalid paths.
		virtual IECore::ConstRunTimeTypedPtr property( const IECore::InternedString &name ) const;

		/// Returns the parent of this path, or None if the path
		/// has no parent (is the root).
		PathPtr parent() const;

		/// Fills the vector with Path instances representing all
		/// the children of this path. Note that an empty list may
		/// be returned even if isLeaf() is false.
		size_t children( std::vector<PathPtr> &children ) const;

		void setFilter( PathFilterPtr filter );
		/// Filter may be NULL.
		PathFilter *getFilter();
		const PathFilter *getFilter() const;

		typedef boost::signal<void ( Path *path )> PathChangedSignal;
		PathChangedSignal &pathChangedSignal();

		/// Sets the path root and names from the other
		/// path, leaving the current filter intact.
		void setFromPath( const Path *path );

		/// Sets the path root and names from a "/"
		/// separated string.
		void setFromString( const std::string &string );

		/// Returns a copy of this path. Must be reimplemented
		/// by derived classes so that the copy has the appropriate
		/// type.
		virtual PathPtr copy() const;

		/// Keeps removing names from the back of
		/// names() until isValid() returns true.
		void truncateUntilValid();

		/// @name Name accessors
		/// These methods provide access to the vector or names that
		/// make up the path.
		////////////////////////////////////////////////////////////////////
		//@{
		/// Direct (const) access to the internal names. Use the
		/// methods below to modify them.
		const Names &names() const;
		/// Sets the name at the specified index, throwing if the
		/// index does not exist.
		void set( size_t index, const IECore::InternedString &name );
		/// Replaces the names in the specified range with the
		/// specified names. Throws if the range does not exist.
		/// The new range may be shorter or longer than the one
		/// it replaces.
		void set( size_t begin, size_t end, const Names &names );
		/// Removes the name at the specified index, throwing if
		/// the index is out of range,
		void remove( size_t index );
		/// Removes the names in the specified range, throwing
		/// if the index is out of range.
		void remove( size_t begin, size_t end );
		/// Appends a name to the end of the path.
		void append( const IECore::InternedString &name );
		//@}

		/// Returns the path concatenated into a string, using '/'
		/// as a separator between names.
		std::string string() const;

		bool operator == ( const Path &other ) const;
		bool operator != ( const Path &other ) const;

	protected :

		/// The subclass specific part of children(). This must be implemented
		/// by subclasses to return a list of children - filtering will be applied
		/// in the children() method so can be ignored by the derived classes.
		/// \todo Allocating new children and then filtering some of them away
		/// seems incredibly wasteful. Perhaps it would be better to have a
		/// virtual childNames() method, and then implement filtering by manipulating
		/// a single path and returning copies for the ones that passed?
		virtual void doChildren( std::vector<PathPtr> &children ) const;

		/// May be called by subclasses to signify that the path has changed
		/// and to emit pathChangedSignal() if necessary. Note that it can be
		/// much more efficient to call this than to call pathChangedSignal()( this ),
		/// because the signal itself is created lazily on demand in pathChangedSignal().
		void emitPathChanged();
		/// Called when the PathChangedSignal is constructed - for performance
		/// reasons this is delayed until it is accessed for the first time
		/// via pathChangedSignal(). This method may be reimplemented to perform
		/// any setup needed to emit the signal appropriately. Implementations
		/// must call the base class implementation first.
		virtual void pathChangedSignalCreated();
		/// Returns true if the PathChangedSignal has been constructed, false
		/// otherwise.
		bool havePathChangedSignal() const;

	private :

		void filterChanged();
		void checkName( const IECore::InternedString &name ) const;

		IECore::InternedString m_root;
		Names m_names;

		PathFilterPtr m_filter;
		PathChangedSignal *m_pathChangedSignal;

		// So we can bind the emitPathChanged() method.
		friend void GafferBindings::bindPath();

};

} // namespace Gaffer

#endif // GAFFER_PATH_H
