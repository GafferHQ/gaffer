//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#pragma once

#include "GafferScene/Export.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/TypeIds.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/ComputeNode.h"
#include "Gaffer/StringPlug.h"

namespace GafferScene
{

struct GAFFERSCENE_API CameraQuery : Gaffer::ComputeNode
{

	public :

		enum class CameraMode
		{
			RenderCamera = 0,
			Location = 1,
		};

		enum class Source
		{
			None = 0,
			Camera = 1,
			Globals = 2,
			Fallback = 3,
		};

		explicit CameraQuery( const std::string &name = defaultName<CameraQuery>() );
		~CameraQuery() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::CameraQuery, CameraQueryTypeId, Gaffer::ComputeNode );

		ScenePlug *scenePlug();
		ScenePlug const *scenePlug() const;

		Gaffer::IntPlug *cameraModePlug();
		Gaffer::IntPlug const *cameraModePlug() const;

		Gaffer::StringPlug *locationPlug();
		Gaffer::StringPlug const *locationPlug() const;

		Gaffer::ArrayPlug *queriesPlug();
		const Gaffer::ArrayPlug *queriesPlug() const;

		Gaffer::ArrayPlug *outPlug();
		const Gaffer::ArrayPlug *outPlug() const;

		/// Adds a query for parameter, with a type specified by plug.
		/// The returned StringPlug is parented to queriesPlug() and may be edited
		/// subsequently to modify the parameter name. Corresponding children are added
		/// to outPlug() to provide the output from the query.
		Gaffer::StringPlug *addQuery(
			const Gaffer::ValuePlug *plug,
			const std::string &parameter = ""
		);
		/// Removes a query. Throws an Exception if the query or corresponding children
		/// of `outPlug()` can not be deleted.
		void removeQuery( Gaffer::StringPlug *plug );

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

		/// Returns the `source`, `value` or child of `out` corresponding to the specified
		/// query plug. Throws an exception if the query does not exist or the corresponding output
		/// plug does not exist or is the wrong type.
		const Gaffer::IntPlug *sourcePlugFromQuery( const Gaffer::StringPlug *queryPlug ) const;
		const Gaffer::ValuePlug *valuePlugFromQuery( const Gaffer::StringPlug *queryPlug ) const;
		const Gaffer::ValuePlug *outPlugFromQuery( const Gaffer::StringPlug *queryPlug ) const;

		/// Returns the child of `queriesPlug` or `outPlug` corresponding to the `outputPlug`.
		/// `outputPlug` can be any descendant of the desired ancestor.
		/// Throws an exception if there is no corresponding query or the result is the wrong type.
		const Gaffer::StringPlug *queryPlug( const Gaffer::ValuePlug *outputPlug ) const;
		const Gaffer::ValuePlug *outPlug( const Gaffer::ValuePlug *outputPlug ) const;

	protected :

		void hash( Gaffer::ValuePlug const *output, Gaffer::Context const *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, Gaffer::Context const *context ) const override;

	private :

		Gaffer::AtomicCompoundDataPlug *internalParametersPlug();
		const Gaffer::AtomicCompoundDataPlug *internalParametersPlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( CameraQuery )

} // namespace GafferScene
