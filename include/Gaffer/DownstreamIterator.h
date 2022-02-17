//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_DOWNSTREAMITERATOR_H
#define GAFFER_DOWNSTREAMITERATOR_H

#include "Gaffer/DependencyNode.h"

#include "IECore/MessageHandler.h"

#include "boost/iterator/iterator_facade.hpp"

namespace Gaffer
{

/// Performs a depth-first iteration of a plug's outputs and affected plugs.
/// Note that this performs a totally naive traversal, and may visit the same
/// plug multiple times in the event that multiple upstream plugs affect it -
/// a diamond graph being the simplest example. Typically you will want to
/// track visited plugs and prune traversal when revisiting.
/// See DependencyNodeTest.testEfficiency and Plug.cpp.
class DownstreamIterator : public boost::iterator_facade<DownstreamIterator, const Plug, boost::forward_traversal_tag>
{

	public :

		DownstreamIterator( const Plug *plug )
			:	m_root( plug ), m_pruned( false )
		{
			m_stack.push_back(
				Level(
					plug
				)
			);
		}

		size_t depth() const
		{
			return m_stack.size() - 1;
		}

		const Plug *upstream() const
		{
			if( m_stack.size() > 1 )
			{
				return *(m_stack[m_stack.size()-2].it);
			}
			return m_root;
		}

		/// Calling prune() causes the next increment to skip any recursion
		/// that it would normally perform.
		void prune()
		{
			m_pruned = true;
		}

		/// Returns true when iteration is complete.
		bool done() const
		{
			return m_stack.size() == 1 && m_stack[0].it == m_stack[0].end;
		}

	private :

		friend class boost::iterator_core_access;

		class Level
		{

			public :

				Level( const Plug *plug )
					:	plugs( plug->outputs().begin(), plug->outputs().end() )
				{
					addDependentPlugs( plug );
					addAncestorOutputs( plug );
					it = plugs.begin();
					end = plugs.end();
				}

				Level( const Level &other )
					:	plugs( other.plugs ), it( plugs.begin() + (other.it - other.plugs.begin()) ), end( plugs.end() )
				{
				}

				bool operator == ( const Level &other ) const
				{
					return plugs == other.plugs && ( it - plugs.begin() == other.it - other.plugs.begin() );
				}

				DependencyNode::AffectedPlugsContainer plugs;
				DependencyNode::AffectedPlugsContainer::const_iterator it;
				DependencyNode::AffectedPlugsContainer::const_iterator end;

			private :

				void addDependentPlugs( const Plug *plug )
				{
					if( !plug->children().empty() )
					{
						// We only call affects() for leaf level plugs. This
						// is because ComputeNode hash/compute also only occurs
						// for leaf plugs, and it would be too big a burden on
						// node implementers to implement affects() to reflect
						// child behaviour in parents.
						return;
					}

					const DependencyNode *node = IECore::runTimeCast<const DependencyNode>( plug->node() );
					if( !node || !node->refCount() )
					{
						// No node, or node constructing or destructing.
						// We can't call `DependencyNode::affects()`.
						return;
					}

					const size_t firstDependentIndex = plugs.size();

					// We don't want client code iterating the graph to
					// be responsible for dealing with buggy Node::affects()
					// implementations, so we catch and report any exceptions
					// which occur.
					try
					{
						node->affects( plug, plugs );
					}
					catch( const std::exception &e )
					{
						IECore::msg(
							IECore::Msg::Error,
							node->fullName() + "::affects()",
							e.what()
						);
					}
					catch( ... )
					{
						IECore::msg(
							IECore::Msg::Error,
							node->fullName() + "::affects()",
							"Unknown exception"
						);
					}

					// Likewise we don't want client code to be exposed to
					// dependencies which are disallowed.
					plugs.erase(
						std::remove_if(
							plugs.begin() + firstDependentIndex,
							plugs.end(),
							isNonLeaf
						),
						plugs.end()
					);
				}

				static bool isNonLeaf( const Plug *plug )
				{
					if( plug->children().empty() )
					{
						return false;
					}
					const Node *node = plug->node();
					IECore::msg(
						IECore::Msg::Error,
						node->fullName() + "::affects()",
						"Non-leaf plug " + plug->relativeName( node ) + " returned by affects()"
					);
					return true;
				}

				void addAncestorOutputs( const Plug *plug )
				{
					// It is valid to connect a compound plug into
					// a non-compound Plug, but when this is done, the
					// "leaf level" where the plugs have no children
					// is deeper on the source side than it is on the
					// destination side. Since we only propagate dependencies
					// along the leaf levels, we must account for the
					// mismatch by finding ancestors which output to leaf
					// level plugs, and including those destination
					// plugs in our traversal.
					plug = plug->parent<Plug>();
					while( plug )
					{
						for( Plug::OutputContainer::const_iterator it = plug->outputs().begin(), eIt = plug->outputs().end(); it!=eIt; ++it )
						{
							if( (*it)->children().empty() )
							{
								plugs.push_back( *it );
							}
						}
						plug = plug->parent<Plug>();
					}
				}

		};

		using Levels = std::vector<Level>;
		Levels m_stack;
		const Plug *m_root;
		bool m_pruned;

		void increment()
		{
			const Plug *currentPlug = *(stackTop().it);
			if( !m_pruned && !cyclic() )
			{
				// go downstream if we can
				Level level( currentPlug );
				if( !level.plugs.empty() )
				{
					m_stack.push_back( level );
					return;
				}
				// otherwise fall through
			}

			++(stackTop().it);
			while( m_stack.size() > 1 && stackTop().it == stackTop().end )
			{
				m_stack.pop_back();
				++(stackTop().it);
			}
			m_pruned = false;
		}

		bool equal( const DownstreamIterator &other ) const
		{
			return m_stack == other.m_stack;
		}

		const Plug &dereference() const
		{
			return **(stackTop().it);
		}

		Level &stackTop()
		{
			return *(m_stack.rbegin());
		}

		const Level &stackTop() const
		{
			return *(m_stack.rbegin());
		}

		bool cyclic() const
		{
			const Plug *currentPlug = *(stackTop().it);
			if( !currentPlug->getFlags( Plug::AcceptsDependencyCycles ) )
			{
				// We don't want to iterate our stack looking for cycles
				// on every increment - that would be slow. Instead we only
				// check for a cycle when we visit the rare plugs which
				// declare that they expect to take part in a cycle.
				return false;
			}
			if( currentPlug == m_root )
			{
				return true;
			}
			for( int i = 0, e = m_stack.size() - 1; i < e; ++i )
			{
				if( *(m_stack[i].it) == currentPlug )
				{
					return true;
				}
			}
			return false;
		}

};

} // namespace Gaffer

#endif // GAFFER_DOWNSTREAMITERATOR_H
