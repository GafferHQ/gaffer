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

		explicit Animation( const std::string &name=defaultName<Animation>() );
		~Animation() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::Animation, AnimationTypeId, ComputeNode );

		/// Defines the method used to interpolate between a key and the next one.
		enum class Interpolation
		{
			Constant = 0,
			ConstantNext,
			Linear,
			Cubic,
			Bezier
		};

		/// Defines the method used to extrapolate before the in key and after the out key.
		enum class Extrapolation
		{
			Constant = 0,
			Linear,
			Repeat,
			RepeatOffset,
			Mirror,
			Oscillate
		};

		/// Defines direction relative to a key.
		enum class Direction
		{
			In = 0,
			Out
		};

		/// Defines whether slope and scale are tied.
		enum class TieMode
		{
			Manual = 0,
			Slope,
			Scale
		};

		/// Get the default interpolation mode.
		static Interpolation defaultInterpolation();

		/// Get the default extrapolation mode.
		static Extrapolation defaultExtrapolation();

		/// Get the default tie mode.
		static TieMode defaultTieMode();

		/// Get the opposite direction to the specified direction
		static Direction opposite( Direction direction );

		/// Get the default slope
		static double defaultSlope();

		/// Get the default scale
		static double defaultScale();

		class Key;
		class CurvePlug;
		class Interpolator;
		IE_CORE_DECLAREPTR( Interpolator )

		// Defines a tangent
		class Tangent : private boost::noncopyable
		{
			public:

				~Tangent();

				/// Get parent key.
				Key& key();
				/// Get parent key. (const access)
				const Key& key() const;

				/// Get the direction of the tangent
				Direction direction() const;

				/// Get tangent's slope.
				/// The slope is in range [-inf,+inf]
				/// If slopeIsConstrained() returns true this function will return the constrained slope.
				double getSlope() const;
				/// \undoable
				/// Set tangent's slope.
				/// The slope is in range [-inf,+inf]
				/// If the tangent's key has tie mode set to either Slope or Scale the opposite tangents slope will be set to the same value.
				/// If slopeIsConstrained() returns true this function will have no effect.
				void setSlope( double slope );
				/// \undoable
				/// Set tangent's position from specified position whilst maintaining the current scale.
				/// If relative is true the position is relative to the parent key's position.
				/// If the tangent's key has tie mode set to either Slope or Scale the opposite tangents slope will be set to the same value.
				/// If slopeIsConstrained() returns true this function will have no effect.
				/// Slope cannot be set from a position if there is no adjacent key in the direction of the tangent.
				void setSlopeFromPosition( const Imath::V2d& position, bool relative = false );

				/// Get tangent's scale.
				/// The scale is multiplied by the span width to derive the tangent's length.
				/// If scaleIsConstrained() returns true this function will return the constrained scale.
				double getScale() const;
				/// \undoable
				/// Set tangent's scale.
				/// The scale is multiplied by the span width to derive the tangent's length.
				/// If the tangent's key has tie mode set to Scale the opposite tangent's scale will be kept proportional.
				/// If scaleIsConstrained() returns true this function will have no effect.
				void setScale( double scale );
				/// \undoable
				/// Set tangent's scale from the specified position whilst maintaining the current slope.
				/// If relative is true the position is relative to the parent key's position.
				/// If the tangent's key has tie mode set to Scale the opposite tangent's scale will be kept proportional.
				/// If scaleIsConstrained() returns true this function will have no effect.
				/// Scale cannot be set from a position if there is no adjacent key in the direction of the tangent.
				void setScaleFromPosition( const Imath::V2d& position, bool relative = false );

				/// \undoable
				/// Set tangent's slope and scale, constrained slope and/or scale will be maintained.
				void setSlopeAndScale( double slope, double scale );

				/// Is slope currently constrained by interpolation mode.
				bool slopeIsConstrained() const;
				/// Is scale currently constrained by interpolation mode.
				bool scaleIsConstrained() const;

				/// Get tangent's position.
				/// If relative is true the position is relative to the parent key's position.
				/// The position will be derived from the current (possibly constrained) slope and scale.
				/// The position will be the same as the parent key when there is no adjacent key in the direction of the tangent.
				Imath::V2d getPosition( bool relative = false ) const;
				/// \undoable
				/// Set tangent's position.
				/// If relative is true the position is relative to the parent key's position.
				/// The position will be used to derive a new slope and scale for the tangent, constrained slope and/or scale will be maintained.
				/// The position cannot be set if there is no adjacent key in the direction of the tangent.
				void setPosition( const Imath::V2d& position, bool relative = false );

			private:

				friend class CurvePlug;
				friend class Key;

				Tangent( Key&, Direction, double, double );
				/// \undoable
				void setSlope( double, bool );
				/// \undoable
				void setScale( double, bool );
				/// \undoable
				void setSlopeAndScale( double, double, bool );
				void update();
				void positionToRelative( Imath::V2d&, bool ) const;

				Key* m_key;
				Direction m_direction;
				double m_dt;
				double m_dv;
				double m_slope;
				double m_scale;
		};

		/// Defines a single keyframe.
		class Key : public IECore::RunTimeTyped
		{

			public :

				explicit Key( float time = 0.0f, float value = 0.0f, Interpolation interpolation = Animation::defaultInterpolation(),
					double inSlope = Animation::defaultSlope(), double inScale = Animation::defaultScale(),
					double outSlope = Animation::defaultSlope(), double outScale = Animation::defaultScale(),
					TieMode tieMode = Animation::defaultTieMode() );
				~Key() override;

				IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Animation::Key, AnimationKeyTypeId, IECore::RunTimeTyped )

				// Get in tangent
				Tangent& tangentIn();
				// Get in tangent (const access)
				const Tangent& tangentIn() const;
				// Get out tangent
				Tangent& tangentOut();
				// Get out tangent (const access)
				const Tangent& tangentOut() const;
				// Get tangent in specified direction
				Tangent& tangent( Direction direction );
				// Get tangent in specified direction (const access)
				const Tangent& tangent( Direction direction ) const;

				/// Get current tie mode of key.
				TieMode getTieMode() const;
				/// Set tie mode of key. If tie mode is Slope or Scale the slope of the in and
				/// out tangents with be made equal. If only one tangent's slope is constrained
				/// or protrudes beyond the start or end of the parent curve, the opposite tangent's
				/// slope will be preserved, otherwise the slopes are averaged. If tie mode is Scale
				/// the ratio between the in and out tangent's scales is captured and changes to
				/// either tangent's scale preserve the proportionality of the opposite tangent's scale.
				/// \undoable
				void setTieMode( TieMode mode );

				/// Get current time of key.
				float getTime() const;
				/// Set time of key. If key is parented it will become the active key of its parent
				/// curve at the specified time. If parent curve has an existing active key at the
				/// specified time, that key will remain parented to curve, become inactive and be
				/// returned by this function. The parent curve's inactive keys are inspected and
				/// the last key to become inactive, at the old time, is made active.
				/// \undoable
				Key::Ptr setTime( float time );

				/// Get current value of key.
				float getValue() const;
				/// Set the value of the key.
				/// \undoable
				void setValue( float value );

				/// Get current interpolation of key.
				Interpolation getInterpolation() const;
				/// \undoable
				void setInterpolation( Interpolation interpolation );

				/// Is the key currently active? The key is considered inactive whilst unparented.
				bool isActive() const;

				/// Get parent curve.
				CurvePlug *parent();
				/// Get parent curve (const access).
				const CurvePlug *parent() const;

			private :

				friend class CurvePlug;
				friend class Tangent;

				Key *nextKey();
				Key *prevKey();
				const Key *nextKey() const;
				const Key *prevKey() const;

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

				static Tangent Key::* const m_tangents[ 2 ];

				Hook m_hook;
				CurvePlug *m_parent;
				Tangent m_tangentIn;
				Tangent m_tangentOut;
				float m_time;
				float m_value;
				ConstInterpolatorPtr m_interpolator;
				double m_tieScaleRatio;
				TieMode m_tieMode;
				bool m_active;

		};

		IE_CORE_DECLAREPTR( Key )

		class KeyIterator;
		class ConstKeyIterator;

		class Extrapolator;
		IE_CORE_DECLAREPTR( Extrapolator )

		/// Defines a curve as a collection of keyframes and methods
		/// for editing them. Provides methods for evaluating the
		/// interpolated curve at arbitrary positions.
		class CurvePlug : public ValuePlug
		{

			public :

				GAFFER_PLUG_DECLARE_TYPE( Gaffer::Animation::CurvePlug, AnimationCurvePlugTypeId, Gaffer::ValuePlug );

				explicit CurvePlug( const std::string &name = defaultName<CurvePlug>(), Plug::Direction direction = Plug::In, unsigned flags = Plug::Default );
				~CurvePlug() override;

				typedef boost::signal< void ( CurvePlug*, Key* ), Gaffer::CatchingSignalCombiner< void > > CurvePlugKeySignal;
				typedef boost::signal< void ( CurvePlug*, Animation::Direction ), Gaffer::CatchingSignalCombiner< void > > CurvePlugDirectionSignal;

				CurvePlugKeySignal& keyAddedSignal();
				CurvePlugKeySignal& keyRemovedSignal();
				CurvePlugKeySignal& keyTimeChangedSignal();
				CurvePlugKeySignal& keyValueChangedSignal();
				CurvePlugKeySignal& keyInterpolationChangedSignal();
				CurvePlugKeySignal& keyTieModeChangedSignal();
				CurvePlugDirectionSignal& extrapolationChangedSignal();

				/// Adds specified key to curve, if key is parented to another curve or already parented
				/// to the curve and inactive it is removed from its parent curve. If the key has already
				/// been added to the curve and is active, there is no effect. If the curve already has an
				/// active key with the same time, then if removeActiveClashing is true that key will be
				/// removed from the curve and returned otherwise that key will remain parented to the
				/// curve, become inactive and be returned. The key will be the active key at its time.
				/// \undoable
				KeyPtr addKey( const KeyPtr &key, bool removeActiveClashing = true );

				/// Inserts a key at the given time, if the specified time is outside the range of the
				/// existing keys the extrapolated value of the curve will be used, otherwise the curve
				/// is bisected at the specified time. If there is already a key at the specified time
				/// it is returned unaltered.
				/// \undoable
				KeyPtr insertKey( float time );

				/// Inserts a key at the given time, if the specified value is equivalent to the
				/// evaluated value of the curve at the specfied time the curve is bisected otherwise
				/// a new key is created and added with the same interpolation as the previous or
				/// first key of the curve. If there is already a key at the specified time its value
				/// is adjusted if its not equivalent to the specified value.
				/// \undoable
				KeyPtr insertKey( float time, float value );

				/// Does the curve have a key at the specified time?
				bool hasKey( float time ) const;

				/// Get the active key at the specified time, returns nullptr if no key with specified
				/// time.
				Key *getKey( float time );
				/// Get the active key at the specified time, returns nullptr if no key with specified
				/// time. (const access)
				const Key *getKey( float time ) const;
				/// Get the active in key, return nullptr if curve has no keys.
				Key *getKeyIn();
				/// Get the active in key, return nullptr if curve has no keys. (const access)
				const Key *getKeyIn() const;
				/// Get the active out key, return nullptr if curve has no keys.
				Key *getKeyOut();
				/// Get the active out key, return nullptr if curve has no keys. (const access)
				const Key *getKeyOut() const;
				/// Get the active key in the specified direction, return nullptr if curve has no keys.
				Key *getKey( Animation::Direction direction );
				/// Get the active key in the specified direction, return nullptr if curve has no keys. (const access)
				const Key *getKey( Animation::Direction direction ) const;

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

				/// Get in extrapolation.
				Extrapolation getExtrapolationIn() const;
				/// Get out extrapolation.
				Extrapolation getExtrapolationOut() const;
				/// Get extrapolation in specified direction.
				Extrapolation getExtrapolation( Animation::Direction direction ) const;
				/// Set in extrapolation.
				/// \undoable
				void setExtrapolationIn( Extrapolation extrapolation );
				/// Set out extrapolation.
				/// \undoable
				void setExtrapolationOut( Extrapolation extrapolation );
				/// Set extrapolation in specified direction.
				/// \undoable
				void setExtrapolation( Animation::Direction direction, Extrapolation extrapolation );

				/// Evaluate the curve at the specified time
				float evaluate( float time ) const;

				/// Output plug for evaluating the curve
				/// over time - use this as the input to
				/// the plug to be animated.
				FloatPlug *outPlug();
				const FloatPlug *outPlug() const;

			private :

				friend class Key;
				friend class Tangent;
				friend KeyIterator;
				friend ConstKeyIterator;

				KeyPtr insertKeyInternal( float, const float* );

				struct TimeKey
				{
					typedef float type;
					type operator()( const Animation::Key& ) const; // NOTE : must NEVER throw
				};

				typedef boost::intrusive::member_hook< Key, Key::Hook, &Key::m_hook > KeyHook;
				typedef boost::intrusive::key_of_value< TimeKey > KeyOfValue;

				typedef boost::intrusive::avl_set< Key, KeyHook, KeyOfValue > Keys;
				typedef boost::intrusive::avl_multiset< Key, KeyHook, KeyOfValue > InactiveKeys;

				static ConstExtrapolatorPtr CurvePlug::* const m_extrapolators[ 2 ];

				Keys m_keys;
				InactiveKeys m_inactiveKeys;
				CurvePlugKeySignal m_keyAddedSignal;
				CurvePlugKeySignal m_keyRemovedSignal;
				CurvePlugKeySignal m_keyTimeChangedSignal;
				CurvePlugKeySignal m_keyValueChangedSignal;
				CurvePlugKeySignal m_keyInterpolationChangedSignal;
				CurvePlugKeySignal m_keyTieModeChangedSignal;
				CurvePlugDirectionSignal m_extrapolationChangedSignal;
				ConstExtrapolatorPtr m_extrapolatorIn;
				ConstExtrapolatorPtr m_extrapolatorOut;
		};

		/// convert enums to strings
		static const char* toString( Interpolation interpolation );
		static const char* toString( Extrapolation extrapolation );
		static const char* toString( Direction direction );
		static const char* toString( TieMode mode );

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
