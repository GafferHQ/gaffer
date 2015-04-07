//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_PATHMATCHER_H
#define GAFFER_PATHMATCHER_H

#include "boost/shared_ptr.hpp"

#include "IECore/TypedData.h"

#include "GafferScene/Filter.h"

namespace GafferScene
{

/// The PathMatcher class provides an acceleration structure for matching
/// paths against a sequence of reference paths. It provides the internal
/// implementation for the PathFilter.
class PathMatcher
{

	public :

		PathMatcher();
		/// Constructs a deep copy of other.
		PathMatcher( const PathMatcher &other );

		template<typename PathIterator>
		PathMatcher( PathIterator pathsBegin, PathIterator pathsEnd );

		/// \todo Should this keep the existing tree in place,
		/// but just remove the terminator flags on any items
		/// not present in the new paths? This might give
		/// better performance for selections and expansions
		/// which will tend to be adding and removing the same
		/// paths repeatedly.
		template<typename PathIterator>
		void init( PathIterator pathsBegin, PathIterator pathsEnd );

		/// Returns true if the path was added, false if
		/// it was already there.
		bool addPath( const std::string &path );
		bool addPath( const std::vector<IECore::InternedString> &path );
		/// Returns true if the path was removed, false if
		/// it was not there.
		bool removePath( const std::string &path );
		bool removePath( const std::vector<IECore::InternedString> &path );

		/// Adds all paths from the other PathMatcher, returning true if
		/// any were added, and false if they were all already present.
		bool addPaths( const PathMatcher &paths );
		/// Removes all specified paths, returning true if any paths
		/// were removed, and false if none existed anyway.
		bool removePaths( const PathMatcher &paths );

		/// Removes the specified path and all descendant paths.
		/// Returns true if something was removed, false otherwise.
		bool prune( const std::string &path );
		bool prune( const std::vector<IECore::InternedString> &path );

		void clear();

		bool isEmpty() const;

		/// Fills the paths container with all the paths held
		/// within this matcher.
		void paths( std::vector<std::string> &paths ) const;

		/// Result is a bitwise or of the relevant values
		/// from Filter::Result.
		unsigned match( const std::string &path ) const;
		unsigned match( const std::vector<IECore::InternedString> &path ) const;

		bool operator == ( const PathMatcher &other ) const;
		bool operator != ( const PathMatcher &other ) const;

	private :

		// Struct used to store the name for each node in the tree of paths.
		// This is just an InternedString with an extra flag to specify whether
		// or not the name contains wildcards (and will therefore need to
		// be used with `match()` or the special ellipsis matching code).
		struct Name
		{

			Name( IECore::InternedString name );
			/// Allows explicit instantiation of the hasWildcards member -
			/// use with care!
			Name( IECore::InternedString name, bool hasWildcards );

			// Less than implemented to do a lexicographical comparison,
			// first on hasWildcards and then on the name. The comparison
			// of the name uses the InternedString operator which compares
			// via pointer rather than string content, which gives improved
			// performance.
			bool operator < ( const Name &other ) const;

			const IECore::InternedString name;
			const bool hasWildcards;

		};

		struct Node
		{

			// Container used to store all the children of the node.
			// We need two things out of this structure - quick access
			// to the child with a specific name, and also partitioning
			// between names with wildcards and those without. This is
			// achieved by using an ordered container, and having the
			// less than operation for Names sort first on hasWildcards
			// and second on the name.
			typedef std::map<Name, Node *> ChildMap;
			typedef ChildMap::iterator ChildMapIterator;
			typedef ChildMap::value_type ChildMapValue;
			typedef ChildMap::const_iterator ConstChildMapIterator;

			Node();
			Node( const Node &other );
			~Node();

			// Returns an iterator to the first child whose name contains wildcards.
			// All children between here and children.end() will also contain wildcards.
			ConstChildMapIterator wildcardsBegin() const;

			Node *child( const Name &name );
			const Node *child( const Name &name ) const;

			bool operator == ( const Node &other ) const;

			bool operator != ( const Node &other );

			bool clearChildren();
			bool isEmpty();

			bool terminator;
			ChildMap children;

		};

		template<typename NameIterator>
		bool addPath( const NameIterator &start, const NameIterator &end );
		template<typename NameIterator>
		void removeWalk( Node *node, const NameIterator &start, const NameIterator &end, const bool prune, bool &removed );
		bool addPathsWalk( Node *node, const Node *srcNode );
		bool removePathsWalk( Node *node, const Node *srcNode );
		void pathsWalk( Node *node, const std::string &path, std::vector<std::string> &paths ) const;

		template<typename NameIterator>
		void matchWalk( const Node *node, const NameIterator &start, const NameIterator &end, unsigned &result ) const;

		boost::shared_ptr<Node> m_root;

};

} // namespace GafferScene

#include "GafferScene/PathMatcher.inl"

#endif // GAFFER_PATHMATCHER_H
