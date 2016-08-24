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

#ifndef GAFFERSCENE_LIGHTTWEAKS_H
#define GAFFERSCENE_LIGHTTWEAKS_H

#include "Gaffer/StringPlug.h"

#include "GafferScene/SceneElementProcessor.h"

namespace GafferScene
{

class LightTweaks : public SceneElementProcessor
{

	public :

		LightTweaks( const std::string &name=defaultName<LightTweaks>() );
		virtual ~LightTweaks();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::LightTweaks, LightTweaksTypeId, SceneElementProcessor );

		/// Compound plug type used to represent a tweak.
		/// Add instances of these to the tweaksPlug() to
		/// add tweaks.
		class TweakPlug : public Gaffer::Plug
		{

			public :

				IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::LightTweaks::TweakPlug, LightTweaksTweakPlugTypeId, Gaffer::Plug );

				TweakPlug( const std::string &tweakName, Gaffer::ValuePlugPtr tweakValuePlug, bool enabled = true );
				TweakPlug( const std::string &tweakName, const IECore::Data *tweakValue, bool enabled = true );
				/// Primarily used for serialisation.
				TweakPlug( const std::string &name=defaultName<TweakPlug>(), Direction direction=In, unsigned flags=Default );

				enum Mode
				{
					Replace,
					Add,
					Subtract,
					Multiply
				};

				Gaffer::StringPlug *namePlug();
				const Gaffer::StringPlug *namePlug() const;

				Gaffer::BoolPlug *enabledPlug();
				const Gaffer::BoolPlug *enabledPlug() const;

				Gaffer::IntPlug *modePlug();
				const Gaffer::IntPlug *modePlug() const;

				template<typename T>
				T *valuePlug();
				template<typename T>
				const T *valuePlug() const;

				virtual bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const;
				virtual Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

			private :

				void construct( const std::string &tweakName, Gaffer::ValuePlugPtr tweakValuePlug, bool enabled );

		};

		typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, TweakPlug> > TweakPlugIterator;
		IE_CORE_DECLAREPTR( TweakPlug )

		Gaffer::StringPlug *typePlug();
		const Gaffer::StringPlug *typePlug() const;

		Gaffer::Plug *tweaksPlug();
		const Gaffer::Plug *tweaksPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		virtual bool processesAttributes() const;
		virtual void hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstCompoundObjectPtr computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( LightTweaks )

} // namespace GafferScene

#endif // GAFFERSCENE_LIGHTTWEAKS_H
