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
#include "Gaffer/CatchingSignalCombiner.h"

#include "boost/intrusive/avl_set.hpp"
#include "boost/intrusive/avl_set_hook.hpp"
#include "boost/intrusive/options.hpp"

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
		enum class Interpolation
		{
			Step,
			Linear,
			/// \todo Add Smooth, implemented as
			/// bezier curves using V2f in and out
			/// tangents on each key.
		};

		class CurvePlug;

		/// Defines a single keyframe.
		class Key : public IECore::RunTimeTyped
		{

			public :

				explicit Key( float time = 0.0f, float value = 0.0f, Interpolation interpolation = Interpolation::Linear );
				~Key() override;

				IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Animation::Key, AnimationKeyTypeId, IECore::RunTimeTyped )

				/// Get current time of key.
				float getTime() const { return m_time; };

				/// Set time of key. If key is parented it will become the active key of its parent
				/// curve at the specified time. If parent curve has an existing active key at the
				/// specified time, that key will remain parented to curve, become inactive and be
				/// returned by this function. The parent curve's inactive keys are inspected and
				/// the last key to become inactive, at the old time, is made active.
				/// \undoable
				Key::Ptr setTime( float time );

				/// Get current value of key.
				float getValue() const  { return m_value; };
				/// Set the value of the key.
				/// \undoable
				void setValue( float value );

				Interpolation getInterpolation() const;
				/// \undoable
				void setInterpolation( Interpolation interpolation );

				/// Is the key currently active? The key is considered inactive whilst unparented.
				bool isActive() const;

				bool operator == ( const Key &rhs ) const;
				bool operator != ( const Key &rhs ) const;

				CurvePlug *parent();
				const CurvePlug *parent() const;

			private :

				friend class CurvePlug;

				void throwIfStateNotAsExpected( const CurvePlug*, bool, float ) const;

				typedef boost::intrusive::avl_set_member_hook<
					boost::intrusive::link_mode<
#					ifndef NDEBUG
					boost::intrusive::safe_link
#					else
					boost::intrusive::normal_link
#					endif
					> > Hook;

				struct Dispose
				{
					void operator()( Key* ) const;
				};

				Hook m_hook;
				CurvePlug *m_parent;
				float m_time;
				float m_value;
				Interpolation m_interpolation;
				bool m_active;

		};

		IE_CORE_DECLAREPTR( Key )

		class KeyIterator;
		class ConstKeyIterator;

		/// Defines a curve as a collection of keyframes and methods
		/// for editing them. Provides methods for evaluating the
		/// interpolated curve at arbitrary positions.
		class CurvePlug : public ValuePlug
		{

			public :

				GAFFER_PLUG_DECLARE_TYPE( Gaffer::Animation::CurvePlug, AnimationCurvePlugTypeId, Gaffer::ValuePlug );

				CurvePlug( const std::string &name = defaultName<CurvePlug>(), Direction direction = Plug::In, unsigned flags = Plug::Default );
				~CurvePlug() override;

				typedef boost::signal< void ( CurvePlug*, Key* ), Gaffer::CatchingSignalCombiner< void > > CurvePlugKeySignal;

				CurvePlugKeySignal& keyAddedSignal();
				CurvePlugKeySignal& keyRemovedSignal();

				/// Adds specified key to curve, if key is parented to another curve it is removed
				/// from the other curve. If the key has already been added to the curve, there is
				/// no affect. If the curve already has an active key with the same time, then if
				/// removeActiveClashing is true that key will be removed from the curve and returned
				/// otherwise that key will remain parented to the curve, become inactive and be returned.
				/// The new key will be the active key at its time.
				/// \undoable
				KeyPtr addKey( const KeyPtr &key, bool removeActiveClashing = true );

				/// Does the curve have a key at the specified time?
				bool hasKey( float time ) const;

				/// Get the active key at the specified time, returns nullptr if no key with specified
				/// time.
				Key *getKey( float time );
				/// Get the active key at the specified time, returns nullptr if no key with specified
				/// time. (const access)
				const Key *getKey( float time ) const;

				/// Removes specified key from curve, if key is not parented to curve an exception
				/// is thrown. If key is active, after it has been removed from curve, the inactive
				/// keys are inspected and the last key to become inactive, with the same time as
				/// the key being removed, is made active.
				/// \undoable
				void removeKey( const KeyPtr &key );

				/// Removes all inactive keys from curve.
				/// \undoable
				void removeInactiveKeys();

				/// Get the closest active key to the specified time.
				Key *closestKey( float time );
				/// Get the closest active key to the specified time. (const access)
				const Key *closestKey( float time ) const;

				/// Get the closest active key to the specified time, search is limited to specified
				/// maxDistance.
				Key *closestKey( float time, float maxDistance );
				/// Get the closest active key to the specified time, search is limited to specified
				/// maxDistance. (const access)
				const Key *closestKey( float time, float maxDistance ) const;

				/// Get the closest active key with time less than the specified time.
				Key *previousKey( float time );
				/// Get the closest active key with time less than the specified time. (const access)
				const Key *previousKey( float time ) const;

				/// Get the closest active key with time greater than the specified time.
				Key *nextKey( float time );
				/// Get the closest active key with time greater than the specified time. (const access)
				const Key *nextKey( float time ) const;

				/// iterator to start of range of active keys
				KeyIterator begin();
				/// iterator to end of range of active keys
				KeyIterator end();

				/// iterator to start of range of active keys. (const access)
				ConstKeyIterator begin() const;
				/// iterator to end of range of active keys. (const access)
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

				struct TimeKey
				{
					typedef float type;
					type operator()( const Animation::Key& key ) const; // NOTE : must NEVER throw
				};

				typedef boost::intrusive::member_hook< Key, Key::Hook, &Key::m_hook > KeyHook;
				typedef boost::intrusive::key_of_value< TimeKey > KeyOfValue;

				typedef boost::intrusive::avl_set< Key, KeyHook, KeyOfValue > Keys;
				typedef boost::intrusive::avl_multiset< Key, KeyHook, KeyOfValue > InactiveKeys;

				Keys m_keys;
				InactiveKeys m_inactiveKeys;
				CurvePlugKeySignal m_keyAddedSignal;
				CurvePlugKeySignal m_keyRemovedSignal;
		};

		/// Are two double precision values considered equivalent
		static bool equivalentValues( double a, double b );

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

class Animation::KeyIterator
: public boost::iterator_facade< Animation::KeyIterator, Animation::Key, boost::bidirectional_traversal_tag >
{
	friend class boost::iterator_core_access;
	friend class Animation::CurvePlug;

	KeyIterator( const Animation::CurvePlug::Keys::iterator it )
	: m_it( it )
	{}

	void increment()
	{
		++m_it;
	}

	void decrement()
	{
		--m_it;
	}

	bool equal( const KeyIterator& other ) const
	{
		return m_it == other.m_it;
	}

	Animation::Key& dereference() const
	{
		return *( m_it );
	}

	Animation::CurvePlug::Keys::iterator m_it;
};

class Animation::ConstKeyIterator
: public boost::iterator_facade< Animation::ConstKeyIterator, const Animation::Key, boost::bidirectional_traversal_tag >
{
	friend class boost::iterator_core_access;
	friend class Animation::CurvePlug;

	ConstKeyIterator( const Animation::CurvePlug::Keys::const_iterator it )
	: m_it( it )
	{}

	void increment()
	{
		++m_it;
	}

	void decrement()
	{
		--m_it;
	}

	bool equal( const ConstKeyIterator& other ) const
	{
		return m_it == other.m_it;
	}

	const Animation::Key& dereference() const
	{
		return *( m_it );
	}

	Animation::CurvePlug::Keys::const_iterator m_it;
};

} // namespace Gaffer

#endif // GAFFER_ANIMATION_H
