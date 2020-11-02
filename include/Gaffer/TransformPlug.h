//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_TRANSFORMPLUG_H
#define GAFFER_TRANSFORMPLUG_H

#include "Gaffer/CompoundNumericPlug.h"

namespace Gaffer
{

class GAFFER_API TransformPlug : public ValuePlug
{

	public :

		TransformPlug(
			const std::string &name = defaultName<TransformPlug>(),
			Direction direction=In,
			const Imath::V3f &defaultTranslate = Imath::V3f( 0 ),
			const Imath::V3f &defaultRotate = Imath::V3f( 0 ),
			const Imath::V3f &defaultScale = Imath::V3f( 1 ),
			const Imath::V3f &defaultPivot = Imath::V3f( 0 ),
			unsigned flags = Default
		);
		~TransformPlug() override;

		GAFFER_PLUG_DECLARE_TYPE( Gaffer::TransformPlug, TransformPlugTypeId, ValuePlug );

		bool acceptsChild( const GraphComponent *potentialChild ) const override;
		PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		V3fPlug *translatePlug();
		const V3fPlug *translatePlug() const;
		V3fPlug *rotatePlug();
		const V3fPlug *rotatePlug() const;
		V3fPlug *scalePlug();
		const V3fPlug *scalePlug() const;
		V3fPlug *pivotPlug();
		const V3fPlug *pivotPlug() const;

		Imath::M44f matrix() const;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( TransformPlug );

/// \deprecated Use TransformPlug::Iterator etc instead
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, TransformPlug> > TransformPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, TransformPlug> > InputTransformPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, TransformPlug> > OutputTransformPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, TransformPlug>, PlugPredicate<> > RecursiveTransformPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, TransformPlug>, PlugPredicate<> > RecursiveInputTransformPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, TransformPlug>, PlugPredicate<> > RecursiveOutputTransformPlugIterator;

} // namespace Gaffer

#endif // GAFFER_TRANSFORMPLUG_H
