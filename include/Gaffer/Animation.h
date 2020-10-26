//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_ANIMATION_H
#define GAFFER_ANIMATION_H

#include "Gaffer/ComputeNode.h"
#include "Gaffer/NumericPlug.h"

#include "boost/multi_index/mem_fun.hpp"
#include "boost/multi_index/ordered_index.hpp"
#include "boost/multi_index_container.hpp"

namespace Gaffer
{

/// Node for applying keyframed animation to plugs.
class GAFFER_API Animation : public ComputeNode
{

	public :

		Animation( const std::string &name=defaultName<Animation>() );
		~Animation() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::Animation, AnimationTypeId, ComputeNode );

		/// Defines the method used to interpolate
		/// between a key and the previous one.
		enum Type
		{
			Step,
			Linear,
			/// \todo Add Smooth, implemented as
			/// bezier curves using V2f in and out
			/// tangents on each key.
		};

		class CurvePlug;

		/// Defines a single keyframe.
		class Key : public IECore::RefCounted
		{

			public :

				Key( float time = 0.0f, float value = 0.0f, Type type = Linear );

				IE_CORE_DECLAREMEMBERPTR( Key )

				float getTime() const { return m_time; };
				/// \undoable
				void setTime( float time );

				float getValue() const  { return m_value; };
				/// \undoable
				void setValue( float value );

				Type getType() const { return m_type; };
				/// \undoable
				void setType( Type type );

				bool operator == ( const Key &rhs ) const;
				bool operator != ( const Key &rhs ) const;

				CurvePlug *parent();
				const CurvePlug *parent() const;

			private :

				friend class CurvePlug;

				CurvePlug *m_parent;
				float m_time;
				float m_value;
				Type m_type;

		};

		IE_CORE_DECLAREPTR( Key )

		template<typename ValueType>
		class KeyIteratorT;

		typedef KeyIteratorT<Key> KeyIterator;
		typedef KeyIteratorT<const Key> ConstKeyIterator;

		/// Defines a curve as a collection of keyframes and methods
		/// for editing them. Provides methods for evaluating the
		/// interpolated curve at arbitrary positions.
		class CurvePlug : public ValuePlug
		{

			public :

				GAFFER_PLUG_DECLARE_TYPE( Gaffer::Animation::CurvePlug, AnimationCurvePlugTypeId, Gaffer::ValuePlug );

				CurvePlug( const std::string &name = defaultName<CurvePlug>(), Direction direction = Plug::In, unsigned flags = Plug::Default );

				/// \undoable
				void addKey( const KeyPtr &key );
				bool hasKey( float time ) const;
				Key *getKey( float time );
				const Key *getKey( float time ) const;
				// /// \undoable
				void removeKey( const KeyPtr &key );

				Key *closestKey( float time );
				const Key *closestKey( float time ) const;

				Key *closestKey( float time, float maxDistance );
				const Key *closestKey( float time, float maxDistance ) const;

				Key *previousKey( float time );
				const Key *previousKey( float time ) const;

				Key *nextKey( float time );
				const Key *nextKey( float time ) const;

				KeyIterator begin();
				KeyIterator end();

				ConstKeyIterator begin() const;
				ConstKeyIterator end() const;

				float evaluate( float time ) const;

				/// Output plug for evaluating the curve
				/// over time - use this as the input to
				/// the plug to be animated.
				FloatPlug *outPlug();
				const FloatPlug *outPlug() const;

			private :

				friend class Key;
				friend KeyIterator;
				friend ConstKeyIterator;

				typedef boost::multi_index::multi_index_container<
					KeyPtr,
					boost::multi_index::indexed_by<
						boost::multi_index::ordered_unique<
							boost::multi_index::const_mem_fun<Key, float, &Key::getTime>
						>
					>
				> Keys;

				Keys m_keys;

		};

		IE_CORE_DECLAREPTR( CurvePlug );

		/// Parent for all the curves belonging to this
		/// node. Animation nodes may have arbitrary numbers
		/// of curves.
		Plug *curvesPlug();
		const Plug *curvesPlug() const;

		static bool canAnimate( const ValuePlug *plug );
		static bool isAnimated( const ValuePlug *plug );

		/// Acquires a curve for use in applying animation
		/// to the specified plug. The methods of the curve
		/// may then be used to define a new animation or edit
		/// a preexisting one.
		///
		/// It is recommended that acquire() be used in
		/// preference to the manual construction of nodes and
		/// curves, as it automatically groups all animation
		/// for each target node onto a single animation node,
		/// to aid in the production of a tidy graph.
		static CurvePlug *acquire( ValuePlug *plug );

		void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override;
		void compute( ValuePlug *output, const Context *context ) const override;
		ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

	private :

		static CurvePlug *inputCurve( ValuePlug *plug );
		static const CurvePlug *inputCurve( const ValuePlug *plug );

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Animation )

template<typename ValueType>
class Animation::KeyIteratorT : public boost::iterator_facade<Animation::KeyIteratorT<ValueType>, ValueType, boost::bidirectional_traversal_tag>
{

	private :

		KeyIteratorT( Animation::CurvePlug::Keys::const_iterator it )
			:	m_it( it )
		{
		}

		friend class boost::iterator_core_access;
		friend class Animation::CurvePlug;

		void increment()
		{
			++m_it;
		}

		void decrement()
		{
			--m_it;
		}

		bool equal( const KeyIteratorT &other ) const
		{
			return m_it == other.m_it;
		}

		ValueType& dereference() const
		{
			return *(m_it->get());
		}

		Animation::CurvePlug::Keys::const_iterator m_it;

};

} // namespace Gaffer

#endif // GAFFER_ANIMATION_H
