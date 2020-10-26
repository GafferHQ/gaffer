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

#ifndef GAFFERARNOLD_ARNOLDVDB_H
#define GAFFERARNOLD_ARNOLDVDB_H

#include "GafferArnold/Export.h"
#include "GafferArnold/TypeIds.h"

#include "GafferScene/ObjectSource.h"

namespace GafferArnold
{

class GAFFERARNOLD_API ArnoldVDB : public GafferScene::ObjectSource
{

	public :

		GAFFER_NODE_DECLARE_TYPE( GafferArnold::ArnoldVDB, ArnoldVDBTypeId, GafferScene::ObjectSource );

		ArnoldVDB( const std::string &name=defaultName<ArnoldVDB>() );
		~ArnoldVDB() override;

		Gaffer::StringPlug *fileNamePlug();
		const Gaffer::StringPlug *fileNamePlug() const;

		Gaffer::StringPlug *gridsPlug();
		const Gaffer::StringPlug *gridsPlug() const;

		Gaffer::StringPlug *velocityGridsPlug();
		const Gaffer::StringPlug *velocityGridsPlug() const;

		Gaffer::FloatPlug *velocityScalePlug();
		const Gaffer::FloatPlug *velocityScalePlug() const;

		Gaffer::FloatPlug *stepSizePlug();
		const Gaffer::FloatPlug *stepSizePlug() const;

		Gaffer::FloatPlug *stepScalePlug();
		const Gaffer::FloatPlug *stepScalePlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeSource( const Gaffer::Context *context ) const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ArnoldVDB )

} // namespace GafferArnold

#endif // GAFFERARNOLD_ARNOLDVDB_H
