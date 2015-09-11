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

namespace Gaffer
{

/// Node for applying keyframed animation to plugs.
class Animation : public ComputeNode
{

	public :

		Animation( const std::string &name=defaultName<Animation>() );
		virtual ~Animation();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Animation, AnimationTypeId, ComputeNode );

		/// Defines the type of a keyframe.
		enum Type
		{
			Invalid,
			Step,
			Linear,
			/// \todo Add Smooth, implemented as
			/// bezier curves using V2f in and out
			/// tangents on each key.
		};

		/// Defines a single keyframe.
		class Key
		{

			public :

				/// Constructs a key with type == Invalid.
				Key();
				Key( float time, float value = 0.0f, Type type = Linear );

				float time;
				float value;
				/// The method used to interpolate between the
				/// previous key and this one. An Invalid value
				/// for type is used as a sentinel value to denote
				/// an invalid key.
				Type type;

				bool operator == ( const Key &rhs ) const;
				bool operator != ( const Key &rhs ) const;
				/// Compares solely on the time value.
				bool operator < ( const Key &rhs ) const;
				/// Returns false if type == Invalid, true
				/// otherwise.
				operator bool() const;

		};

		/// Defines a curve as a collection of keyframes and methods
		/// for editing them. Provides methods for evaluating the
		/// interpolated curve at arbitrary positions.
		class CurvePlug : public ValuePlug
		{

			public :

				IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Animation::CurvePlug, AnimationCurvePlugTypeId, Gaffer::ValuePlug );

				CurvePlug( const std::string &name = defaultName<CurvePlug>(), Direction direction = Plug::In, unsigned flags = Plug::Default );

				/// \undoable
				void addKey( const Key &key );
				bool hasKey( float time ) const;
				Key getKey( float time ) const;
				/// \undoable
				void removeKey( float time );

				Key closestKey( float time ) const;
				Key previousKey( float time ) const;
				Key nextKey( float time ) const;

				typedef std::set<Key> Keys;
				const Keys &keys() const;

				float evaluate( float time ) const;

				/// Output plug for evaluating the curve
				/// over time - use this as the input to
				/// the plug to be animated.
				FloatPlug *outPlug();
				const FloatPlug *outPlug() const;

			private :

				void addOrRemoveKeyInternal( const Key &key );

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

		virtual void affects( const Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		virtual void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( ValuePlug *output, const Context *context ) const;

	private :

		static CurvePlug *inputCurve( ValuePlug *plug );
		static const CurvePlug *inputCurve( const ValuePlug *plug );

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Animation )

} // namespace Gaffer

#endif // GAFFER_ANIMATION_H
