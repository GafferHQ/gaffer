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

#ifndef GAFFERIMAGE_FORMATPLUG_H
#define GAFFERIMAGE_FORMATPLUG_H

#include "Gaffer/BoxPlug.h"

#include "GafferImage/Format.h"
#include "GafferImage/TypeIds.h"

namespace GafferImage
{

/// Compound plug for representing an image format in a way
/// easily edited by users, with individual child plugs for
/// each aspect of the format.
class FormatPlug : public Gaffer::ValuePlug
{

	public :

		typedef Format ValueType;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::FormatPlug, FormatPlugTypeId, Gaffer::ValuePlug );

		FormatPlug(
			const std::string &name = defaultName<FormatPlug>(),
			Direction direction=In,
			Format defaultValue = Format(),
			unsigned flags = Default
		);

		virtual ~FormatPlug();

		/// Accepts no children following construction.
		virtual bool acceptsChild( const GraphComponent *potentialChild ) const;
		virtual Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

		Gaffer::Box2iPlug *displayWindowPlug();
		const Gaffer::Box2iPlug *displayWindowPlug() const;

		Gaffer::FloatPlug *pixelAspectPlug();
		const Gaffer::FloatPlug *pixelAspectPlug() const;

		const Format &defaultValue() const;

		/// \undoable
		void setValue( const Format &value );
		Format getValue() const;

	private :

		Format m_defaultValue;

};

IE_CORE_DECLAREPTR( FormatPlug );

typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, FormatPlug> > FormatPlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, FormatPlug> > InputFormatPlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, FormatPlug> > OutputFormatPlugIterator;

typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, FormatPlug>, Gaffer::PlugPredicate<> > RecursiveFormatPlugIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, FormatPlug>, Gaffer::PlugPredicate<> > RecursiveInputFormatPlugIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, FormatPlug>, Gaffer::PlugPredicate<> > RecursiveOutputFormatPlugIterator;

} // namespace GafferImage

#endif // GAFFERIMAGE_FORMATPLUG_H
