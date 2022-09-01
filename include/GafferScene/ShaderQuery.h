//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#ifndef GAFFERSCENE_SHADERQUERY_H
#define GAFFERSCENE_SHADERQUERY_H

#include "GafferScene/AttributeQuery.h"
#include "GafferScene/Export.h"
#include "GafferScene/TypeIds.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/NameValuePlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"

namespace GafferScene
{

class GAFFERSCENE_API ShaderQuery : public Gaffer::ComputeNode
{
	public:
		ShaderQuery( const std::string &name = defaultName<ShaderQuery>() );
		~ShaderQuery() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::ShaderQuery, ShaderQueryTypeId, Gaffer::ComputeNode );

		ScenePlug *scenePlug();
		const ScenePlug *scenePlug() const;

		Gaffer::StringPlug *locationPlug();
		const Gaffer::StringPlug *locationPlug() const;

		Gaffer::StringPlug *shaderPlug();
		const Gaffer::StringPlug *shaderPlug() const;

		Gaffer::BoolPlug *inheritPlug();
		const Gaffer::BoolPlug *inheritPlug() const;

		Gaffer::ArrayPlug *queriesPlug();
		const Gaffer::ArrayPlug *queriesPlug() const;

		Gaffer::ArrayPlug *outPlug();
		const Gaffer::ArrayPlug *outPlug() const;

		/// Adds a query for parameter, with a type and default value specified by plug.
		/// The returned NameValuePlug is parented to queriesPlug() and may be edited
		/// subsequently to modify the parameter name and default. Corresponding children
		/// are added to existsPlug() and valuePlug() to provide the output from the query.
		Gaffer::NameValuePlug *addQuery(
			const Gaffer::ValuePlug *plug,
			const std::string &parameter = ""
		);
		/// Removes a query. Throws an Exception if the query or corresponding children
		/// of `valuesPlug()` and `existsPlug()` can not be deleted.
		void removeQuery( Gaffer::NameValuePlug *plug );

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

		/// Returns the `exists`, `value` or child of `out` corresponding to the specified
		/// query plug. Throws an exception if the query does not exist or the corresponding output
		/// plug does not exist or is the wrong type.
		const Gaffer::BoolPlug *existsPlugFromQuery( const Gaffer::NameValuePlug *queryPlug ) const;
		const Gaffer::ValuePlug *valuePlugFromQuery( const Gaffer::NameValuePlug *queryPlug ) const;
		const Gaffer::ValuePlug *outPlugFromQuery( const Gaffer::NameValuePlug *queryPlug ) const;

		/// Returns the child of `queryPlug` or `outPlug` corresponding to the `outputPlug`.
		/// `outputPlug` can be any descendant of the desired ancestor.
		/// Throws an exception if there is no corresponding query or the result is the wrong type.
		const Gaffer::NameValuePlug *queryPlug( const Gaffer::ValuePlug *outputPlug ) const;
		const Gaffer::ValuePlug *outPlug( const Gaffer::ValuePlug *outputPlug ) const;

	protected:
		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context) const override;

	private:

		AttributeQuery *attributeQuery();
		const AttributeQuery *attributeQuery() const;

		Gaffer::ObjectPlug *intermediateObjectPlug();
		const Gaffer::ObjectPlug *intermediateObjectPlug() const;

		const IECore::Data *parameterData( const IECore::Object *object, const std::string &parameterName ) const;

		static size_t g_firstPlugIndex;
};

}  // namespace GafferScene

#endif // GAFFERSCENE_SHADERQUERY_H
