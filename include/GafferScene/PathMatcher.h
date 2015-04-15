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
		/// within this matcher. Iterators should be preferred
		/// over this method.
		void paths( std::vector<std::string> &paths ) const;

		/// Result is a bitwise or of the relevant values
		/// from Filter::Result.
		unsigned match( const std::string &path ) const;
		unsigned match( const std::vector<IECore::InternedString> &path ) const;

		bool operator == ( const PathMatcher &other ) const;
		bool operator != ( const PathMatcher &other ) const;

		class RawIterator;
		class Iterator;

		/// Returns an iterator to the start of the
		/// tree of paths.
		RawIterator begin() const;
		/// Returns an iterator to the end of the
		/// tree of paths.
		RawIterator end() const;

	private :

		// Struct used to store the name for each node in the tree of paths.
		// This is just an InternedString with an extra field used to separate
		// names containing wildcards from plain names - since they need to
		// be used with `match()` or the special ellipsis matching code.
		struct Name
		{

			enum Type
			{
				Plain = 0, // No wildcards
				Boundary = 1, // Marker between plain and wildcarded
				Wildcarded = 2 // Has wildcards or ...
			};

			Name( IECore::InternedString name );
			// Allows explicit instantiation of the type member -
			// use with care!
			Name( IECore::InternedString name, Type type );

			// Less than implemented to do a lexicographical comparison,
			// first on type and then on the name. This has the effect of
			// segregating plain strings from wildcarded strings with the
			// Boundary type providing a marker between them. The comparison
			// of the name uses the InternedString operator which compares
			// via pointer rather than string content, which gives improved
			// performance.
			bool operator < ( const Name &other ) const;

			const IECore::InternedString name;
			const unsigned char type;

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

		template<typename NameIterator>
		void matchWalk( const Node *node, const NameIterator &start, const NameIterator &end, unsigned &result ) const;

		boost::shared_ptr<Node> m_root;

};

/// Iterates over the tree of paths in a PathMatcher, visiting not only the locations
/// explicitly added with addPath(), but also their ancestor locations. Iteration is
/// guaranteed to be depth-first recursive, but the order of iteration over siblings
/// at the same depth is not guaranteed. For an iterator which ignores ancestor
/// locations, see the PathMatcher::Iterator class.
class PathMatcher::RawIterator : public boost::iterator_facade<RawIterator, const std::vector<IECore::InternedString>, boost::forward_traversal_tag>
{

	public :

		/// Calling prune() causes the next increment to skip any recursion
		/// that it would normally perform.
		void prune();

		/// Returns true if this path is in the matcher because it
		/// has been explicitly added with addPath(), and will therefore
		/// yield an exact match. If this returns false, then this
		/// path exists in the matcher only as the ancestor of descendant
		/// paths for which exactMatch() will be true.
		const bool exactMatch() const;

	private :

		friend class boost::iterator_core_access;
		friend class PathMatcher;
		friend class Iterator;

		// Private constructor, called by PathMatcher::begin() and PathMatcher::end().
		RawIterator( const PathMatcher &matcher, bool atEnd );

		//////////////////////////////////////////////////
		// Methods required by boost::iterator_facade
		//////////////////////////////////////////////////

		void increment();
		bool equal( const RawIterator &other ) const;
		const std::vector<IECore::InternedString> &dereference() const;

		//////////////////////////////////////////////////
		// Our own internal methods.
		//////////////////////////////////////////////////

		const Node *node() const;

		// Keeps track of our iteration at a given depth in
		// the hierarchy. We keep a stack of these to allow
		// us to perform recursion.
		struct Level
		{

			Level( const Node::ChildMap &children, Node::ConstChildMapIterator it );

			bool operator == ( const Level &other ) const;

			Node::ConstChildMapIterator end;
			Node::ConstChildMapIterator it;

		};

		typedef std::vector<Level> Levels;
		Levels m_stack;
		std::vector<IECore::InternedString> m_path;
		// Because there is no ChildMapIterator for the root
		// node, we have to store it explicitly. The value
		// will be non-null only when we're pointing at the root.
		Node *m_nodeIfRoot;
		bool m_pruned;

};

/// Iterates over the tree of paths in a PathMatcher, visiting only the locations
/// explicitly added with addPath(). Iteration is guaranteed to be depth-first recursive,
/// but the order of iteration over siblings at the same depth is not guaranteed.
class PathMatcher::Iterator : public boost::iterator_adaptor<Iterator, PathMatcher::RawIterator>
{

	public :

		Iterator( const RawIterator &it );

		bool operator==( const RawIterator &rhs ) const;
		bool operator!=( const RawIterator &rhs ) const;

		void prune();

	private :

		friend class boost::iterator_core_access;

		void increment();
		void satisfyTerminatorRequirement();

};

} // namespace GafferScene

#include "GafferScene/PathMatcher.inl"

#endif // GAFFER_PATHMATCHER_H
