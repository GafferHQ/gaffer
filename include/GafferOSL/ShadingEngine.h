//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, John Haddon. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#ifndef GAFFEROSL_SHADINGENGINE_H
#define GAFFEROSL_SHADINGENGINE_H

#include "GafferOSL/Export.h"
#include "GafferOSL/TypeIds.h"

#include "IECoreScene/ShaderNetwork.h"

#include "IECore/CompoundData.h"

#include "boost/container/flat_set.hpp"

namespace GafferOSL
{

class GAFFEROSL_API ShadingEngine : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( ShadingEngine )

		ShadingEngine( const IECoreScene::ShaderNetwork *shaderNetwork );
		~ShadingEngine() override;

		struct Transform
		{

			Transform()
			{
			}

			Transform( Imath::M44f fromObjectSpace )
				: fromObjectSpace( fromObjectSpace ), toObjectSpace( fromObjectSpace.inverse() )
			{
			}

			Transform( Imath::M44f fromObjectSpace, Imath::M44f toObjectSpace )
				: fromObjectSpace( fromObjectSpace ), toObjectSpace( toObjectSpace )
			{
			}

			Imath::M44f fromObjectSpace;
			Imath::M44f toObjectSpace;

		};

		using Transforms = std::map<IECore::InternedString, Transform>;

		/// Append a unique hash representing this shading engine to `h`.
		void hash( IECore::MurmurHash &h ) const;

		/// \todo : replace with one function with default argument value on main branch
		IECore::CompoundDataPtr shade( const IECore::CompoundData *points, const Transforms &transforms = Transforms() ) const;
		IECore::CompoundDataPtr shade( const IECore::CompoundData *points, const Transforms &transforms, const IECore::CompoundObject *attributeSubstitutions ) const;

		bool needsAttribute( const std::string &name ) const;
		bool hasDeformation() const;

	private :

		void queryShaderGroup();

		const IECore::MurmurHash m_hash;

		bool m_timeNeeded;
		std::vector<IECore::InternedString> m_contextVariablesNeeded;

		using AttributesNeededContainer = boost::container::flat_set<std::string>;
		AttributesNeededContainer m_attributesNeeded;

		// Set to true if the shader reads attributes who's name is not know at compile time
		bool m_unknownAttributesNeeded;

		bool m_hasDeformation;

		void *m_shaderGroupRef;

};

IE_CORE_DECLAREPTR( ShadingEngine )

} // namespace GafferOSL

#endif // GAFFEROSL_SHADINGENGINE_H
