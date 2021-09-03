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

#include "boost/multi_index/mem_fun.hpp"
#include "boost/multi_index/ordered_index.hpp"
#include "boost/multi_index_container.hpp"

#include <cstdint>

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
		/// \deprecated Use Interpolator instead.
		enum Type
		{
			Step,
			Linear,
			Unknown
		};

		/// Defines tick based time
		class Time
		{

			public:

				enum class Units
				{
					Seconds	= 1,
					Fps24	= 24,
					Fps25	= 25,
					Fps48	= 48,
					Fps60	= 60,
					Fps90	= 90,
					Fps120	= 120,
					Milli	= 1000,
					Ticks	= 705600000
				};

				Time();
				explicit Time( std::int64_t value );
				Time( double value, Units units );
				Time( double value, double units );
				Time( Time const& rhs );
				~Time();

				Time& operator  = ( const Time& rhs );
				Time& operator += ( const Time& rhs );
				Time& operator -= ( const Time& rhs );
				Time& operator /= ( const Time& rhs );
				Time& operator %= ( const Time& rhs );

				std::int64_t getTicks() const;
				double getReal( double units ) const;
				double getSeconds() const;

				void snap( double units );

				GAFFER_API friend Time operator +  ( const Time& lhs, const Time& rhs );
				GAFFER_API friend Time operator -  ( const Time& lhs, const Time& rhs );
				GAFFER_API friend Time operator /  ( const Time& lhs, const Time& rhs );
				GAFFER_API friend Time operator %  ( const Time& lhs, const Time& rhs );
				GAFFER_API friend bool operator == ( const Time& lhs, const Time& rhs );
				GAFFER_API friend bool operator != ( const Time& lhs, const Time& rhs );
				GAFFER_API friend bool operator <  ( const Time& lhs, const Time& rhs );
				GAFFER_API friend bool operator >  ( const Time& lhs, const Time& rhs );
				GAFFER_API friend bool operator <= ( const Time& lhs, const Time& rhs );
				GAFFER_API friend bool operator >= ( const Time& lhs, const Time& rhs );
				GAFFER_API friend Time abs( const Time& rhs );

			private:

				std::int64_t m_ticks;
		};

		class Key;
		class CurvePlug;

		// Defines a tangent
		class Tangent : private boost::noncopyable
		{

			public:

				enum class Space
				{
					Key  = 0,
					Span = 1
				};

				enum class Direction
				{
					Into = 0,
					From = 1
				};

				enum class TieMode
				{
					Manual = 0,
					Slope = 1,
					SlopeAndAccel = 2
				};

				static Direction opposite( Direction direction );

				static double defaultSlope();
				static double defaultAccel();

				~Tangent();

				Key& getKey();
				const Key& getKey() const;
				Direction getDirection() const;

				Imath::V2d getPosition( Space space, bool relative ) const;
				/// \undoable
				void setPosition( Imath::V2d position, Space space, bool relative );
				/// \undoable
				/// set position whilst maintaining specified span space slope
				void setPositionWithSlope( Imath::V2d position, double slope, Space space, bool relative );
				/// \undoable
				/// set position whilst maintaining specified span space acceleration
				void setPositionWithAccel( Imath::V2d position, double accel, Space space, bool relative );

				double getSlope( Space space ) const;
				/// \undoable
				void setSlope( double slope, Space space );
				/// \undoable
				/// set slope whilst maintaining specified span space acceleration
				void setSlopeWithAccel( double slope, double accel, Space space );

				double getAccel( Space space ) const;
				/// \undoable
				void setAccel( double accel, Space space );

				/// is slope currently used by interpolator
				bool slopeIsUsed() const;
				/// is accel currently used by interpolator
				bool accelIsUsed() const;

			private:

				/// \undoable
				void setSlopeSpace( Space );
				/// \undoable
				void setAccelSpace( Space );

				friend class CurvePlug;
				friend class Key;

				void update();
				void convertPosition( Imath::V2d&, Space, bool ) const;

				Tangent( Key& key, Direction direction, double slope, Space slopeSpace, double accel, Space accelSpace );

				Key* m_key;
				double m_slope;
				double m_accel;
				double m_dt;
				double m_vt;
				Direction m_direction;
				Space m_slopeSpace;
				Space m_accelSpace;
		};

		/// Defines span interpolator
		class Interpolator : public IECore::RefCounted
		{

			public:

				IE_CORE_DECLAREMEMBERPTR( Interpolator )

				enum class Hint
				{
					UseSlopeLo = 0,
					UseSlopeHi = 1,
					UseAccelLo = 2,
					UseAccelHi = 3
				};

				struct Hints
				{
					Hints();
					Hints( Hint hint );
					Hints( const Hints& rhs );
					Hints& operator = ( const Hints& rhs );
					bool test( Hint hint ) const;

					GAFFER_API friend Hints operator | ( const Hints& lhs, const Hints& rhs );

				private:

					std::uint32_t m_bits;
				};

				struct Factory : public IECore::RefCounted
				{
					~Factory();

					bool add( Interpolator::Ptr interpolator );
					std::uint32_t count();
					Interpolator* get( const std::string& name );
					Interpolator* get( std::uint32_t index );
					Interpolator* getDefault();

					IE_CORE_DECLAREMEMBERPTR( Factory )

				private:

					friend class Interpolator;
					Factory();

					typedef std::vector< Interpolator::Ptr > Container;
					Container m_container;
					Interpolator::Ptr m_default;
				};

			static Factory& getFactory();

			~Interpolator();

			const std::string& getName() const;
			Hints getHints() const;
			double defaultSlope() const;
			double defaultAccel() const;

		protected:

			/// construct with specified name, hints and span space default slope and accel
			Interpolator( const std::string& name, Hints hints,
				double defaultSlope = Tangent::defaultSlope(),
				double defaultAccel = Tangent::defaultAccel() );

		private:

			friend class CurvePlug;

			/// Implement to return interpolated value at specified normalised time
			virtual double evaluate( double valueLo, double valueHi, const Tangent& tangentLo, const Tangent& tangentHi, double time ) const = 0;

			/// Implement to bisect the span at the specified time, should set new key's value and slope and accel of new tangents
			virtual void bisect( double valueLo, double valueHi, const Tangent& tangentLo, const Tangent& tangentHi, double time,
				Key& newKey, Tangent& newTangentLo, Tangent& newTangentHi ) const;

			std::string m_name;
			Hints m_hints;
			double m_defaultSlope;
			double m_defaultAccel;
		};

		IE_CORE_DECLAREPTR( Interpolator )

		/// Defines a single keyframe.
		class Key : public IECore::RefCounted
		{

			public :

				/// \deprecated Use Key(const Time&, float, const std::string& ) instead.
				explicit Key( float time = 0.0f, float value = 0.0f, Type type = Linear );
				explicit Key( const Time& time = Time(), float value = 0.0f,
					const std::string& interpolatorName = Interpolator::getFactory().getDefault()->getName() );
				/// construct Key with specified key space tangent slope and accel
				Key( const Time& time, float value, const std::string& interpolatorName,
					double intoSlope, Tangent::Space intoSlopeSpace, double intoAccel, Tangent::Space intoAccelSpace,
					double fromSlope, Tangent::Space fromSlopeSpace, double fromAccel, Tangent::Space fromAccelSpace,
					Tangent::TieMode tieMode );

				IE_CORE_DECLAREMEMBERPTR( Key )

				Tangent& getTangent( Tangent::Direction direction );
				const Tangent& getTangent( Tangent::Direction direction ) const;

				Tangent::TieMode getTieMode() const;
				/// \undoable
				void setTieMode( Tangent::TieMode mode );

				/// \deprecated Use Time getTime() instead.
				float getFloatTime() const;
				Time getTime() const;

				/// \undoable
				/// \deprecated Use setTime(const Time&) instead.
				void setTime( float time );
				/// \undoable
				void setTime( const Time& time );

				float getValue() const;
				/// \undoable
				void setValue( float value );

				/// \deprecated Use getInterpolator() instead.
				Type getType() const;
				/// \undoable
				/// \deprecated Use setInterpolator( const std::string& ) instead.
				void setType( Type type );

				Interpolator* getInterpolator();
				const Interpolator* getInterpolator() const;
				/// \undoable
				void setInterpolator( const std::string& name );

				bool operator == ( const Key &rhs ) const;
				bool operator != ( const Key &rhs ) const;

				Key *nextKey();
				Key *prevKey();
				const Key *nextKey() const;
				const Key *prevKey() const;

				CurvePlug *parent();
				const CurvePlug *parent() const;

			private :

				friend class CurvePlug;
				friend class Tangent;

				void tieSlopeAverage();
				bool tieSlopeActive( Tangent::Direction ) const;
				bool tieAccelActive( Tangent::Direction ) const;

				CurvePlug *m_parent;
				Interpolator* m_interpolator;
				Tangent m_into;
				Tangent m_from;
				Time m_time;
				float m_value;
				Tangent::TieMode m_tieMode;

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

				typedef boost::signal< void ( CurvePlug* ), Gaffer::CatchingSignalCombiner< void > > CurvePlugSignal;
				typedef boost::signal< void ( CurvePlug*, Tangent::Direction ), Gaffer::CatchingSignalCombiner< void > > CurvePlugDirectionSignal;
				typedef boost::signal< void ( CurvePlug*, Key* ), Gaffer::CatchingSignalCombiner< void > > CurvePlugKeySignal;
				typedef boost::signal< void ( CurvePlug*, Key*, Tangent::Direction ), Gaffer::CatchingSignalCombiner< void > > CurvePlugKeyDirectionSignal;

				CurvePlugSignal& colorChangedSignal();
				CurvePlugDirectionSignal& extrapolatorChangedSignal();
				CurvePlugKeySignal& keyAddedSignal();
				CurvePlugKeySignal& keyRemovedSignal();
				CurvePlugKeySignal& keyTimeChangedSignal();
				CurvePlugKeySignal& keyValueChangedSignal();
				CurvePlugKeySignal& keyTieModeChangedSignal();
				CurvePlugKeySignal& keyInterpolatorChangedSignal();
				CurvePlugKeyDirectionSignal& keyTangentSlopeChangedSignal();
				CurvePlugKeyDirectionSignal& keyTangentAccelChangedSignal();
				CurvePlugKeyDirectionSignal& keyTangentAutoModeChangedSignal();

				/// \undoable
				void addKey( const KeyPtr &key, bool inherit = false );

				/// \undoable
				Key *insertKey( const Time& time );

				/// \deprecated Use hasKey( const Time& ) instead.
				bool hasKey( float time ) const;
				bool hasKey( const Time& time ) const;

				/// \deprecated Use getKey( const Time& ) instead.
				Key *getKey( float time );
				Key *getKey( const Time& time );

				/// \deprecated Use getKey( const Time& ) instead.
				const Key *getKey( float time ) const;
				const Key *getKey( const Time& time ) const;

				/// \undoable
				void removeKey( const KeyPtr &key );

				/// \deprecated Use closestKey( const Time& ) instead.
				Key *closestKey( float time );
				Key *closestKey( const Time& time );

				/// \deprecated Use closestKey( const Time& ) instead.
				const Key *closestKey( float time ) const;
				const Key *closestKey( const Time& time ) const;

				/// \deprecated Use closestKey( const Time&, float ) instead.
				Key *closestKey( float time, float maxDistance );
				Key *closestKey( const Time& time, float maxDistance );

				/// \deprecated Use closestKey( const Time&, float ) instead.
				const Key *closestKey( float time, float maxDistance ) const;
				const Key *closestKey( const Time& time, float maxDistance ) const;

				/// \deprecated Use previousKey( const Time& ) instead.
				Key *previousKey( float time );
				Key *previousKey( const Time& time );

				/// \deprecated Use previousKey( const Time& ) instead.
				const Key *previousKey( float time ) const;
				const Key *previousKey( const Time& time ) const;

				/// \deprecated Use nextKey( const Time& ) instead.
				Key *nextKey( float time );
				Key *nextKey( const Time& time );

				/// \deprecated Use nextKey( const Time& ) instead.
				const Key *nextKey( float time ) const;
				const Key *nextKey( const Time& time ) const;

				KeyIterator begin();
				KeyIterator end();

				ConstKeyIterator begin() const;
				ConstKeyIterator end() const;

				/// \deprecated Use evaluate( const Time& ) instead.
				float evaluate( float time ) const;
				float evaluate( const Time& time ) const;

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

				Key *firstKey();
				Key *finalKey();
				const Key *firstKey() const;
				const Key *finalKey() const;

				typedef boost::multi_index::multi_index_container<
					KeyPtr,
					boost::multi_index::indexed_by<
						boost::multi_index::ordered_unique<
							boost::multi_index::const_mem_fun<Key, Time, &Key::getTime>
						>
					>
				> Keys;

				Keys m_keys;
				CurvePlugSignal m_colorChangedSignal;
				CurvePlugDirectionSignal m_extrapolatorChangedSignal;
				CurvePlugKeySignal m_keyAddedSignal;
				CurvePlugKeySignal m_keyRemovedSignal;
				CurvePlugKeySignal m_keyTimeChangedSignal;
				CurvePlugKeySignal m_keyValueChangedSignal;
				CurvePlugKeySignal m_keyTieModeChangedSignal;
				CurvePlugKeySignal m_keyInterpolatorChangedSignal;
				CurvePlugKeyDirectionSignal m_keyTangentSlopeChangedSignal;
				CurvePlugKeyDirectionSignal m_keyTangentAccelChangedSignal;
				CurvePlugKeyDirectionSignal m_keyTangentAutoModeChangedSignal;
		};

		/// Are two double precision values considered equivalent
		static bool equivalentValues( double a, double b );

		/// convert enums to strings
		static const char* toString( Type type );
		static const char* toString( Time::Units time );
		static const char* toString( Tangent::Space space );
		static const char* toString( Tangent::Direction direction );
		static const char* toString( Tangent::TieMode mode );

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
