//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2014, John Haddon. All rights reserved.
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_CONTAINERGADGET_H
#define GAFFERUI_CONTAINERGADGET_H

#include "GafferUI/Gadget.h"

namespace GafferUI
{

/// Provides a useful base class for gadgets which are intended
/// primarily to provide layouts of child Gadgets. Note that any
/// Gadget can have children though.
/// \todo Consider a virtual method which is called to compute
/// the transforms for children when they have been dirtied. This would
/// simplify derived classes and provide greater justification for the
/// existence of this base class.
class GAFFERUI_API ContainerGadget : public Gadget
{

	public :

		ContainerGadget( const std::string &name=defaultName<ContainerGadget>() );
		~ContainerGadget() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::ContainerGadget, ContainerGadgetTypeId, Gadget );

		/// The padding is a region added around the contents of the children.
		/// It is specified as the final bounding box when the child bounding
		/// box is ( ( 0, 0, 0 ), ( 0, 0, 0 ) ). That is, padding.min is added to bound.min
		/// and padding.max is added to bound.max.
		void setPadding( const Imath::Box3f &padding );
		const Imath::Box3f &getPadding() const;

		/// Applies the padding to the default union-of-children
		/// bounding box.
		Imath::Box3f bound() const override;

	private :

		Imath::Box3f m_padding;

};

IE_CORE_DECLAREPTR( ContainerGadget );

[[deprecated("Use `ContainerGadget::Iterator` instead")]]
typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<ContainerGadget> > ContainerGadgetIterator;
[[deprecated("Use `ContainerGadget::RecursiveIterator` instead")]]
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<ContainerGadget> > RecursiveContainerGadgetIterator;

} // namespace GafferUI

#endif // GAFFERUI_CONTAINERGADGET_H
