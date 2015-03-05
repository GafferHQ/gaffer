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

#ifndef GAFFERSCENE_FILTERMIXINBASE_H
#define GAFFERSCENE_FILTERMIXINBASE_H

#include "GafferScene/Filter.h"

namespace GafferScene
{

/// See SceneMixinBase for details.
class FilterMixinBase : public Filter
{

	public :

		FilterMixinBase( const std::string &name=defaultName<FilterMixinBase>() );
		virtual ~FilterMixinBase();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::FilterMixinBase, FilterMixinBaseTypeId, Filter );

		virtual bool sceneAffectsMatch( const ScenePlug *scene, const Gaffer::ValuePlug *child ) const;

	private :

		/// These stubs should never be called, because the mixed-in class should implement hash() and compute()
		/// totally. If they are called, they throw to highlight the fact that something is amiss.
		virtual void hashMatch( const ScenePlug *scene, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual unsigned computeMatch( const ScenePlug *scene, const Gaffer::Context *context ) const;

};

IE_CORE_DECLAREPTR( FilterMixinBase )

} // namespace GafferScene

#endif // GAFFERSCENE_FILTERMIXINBASE_H
