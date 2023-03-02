//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
#include "GafferScene/TypeIds.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/ComputeNode.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/TypedObjectPlug.h"

#include "IECoreScene/Shader.h"

#include "IECore/CompoundObject.h"
#include "IECore/ObjectVector.h"

#include "boost/unordered_set.hpp"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferScene
{

class GAFFERSCENE_API Shader : public Gaffer::ComputeNode
{

	public :

		Shader( const std::string &name=defaultName<Shader>() );
		~Shader() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::Shader, ShaderTypeId, Gaffer::ComputeNode );

		/// A plug defining the name of the shader.
		Gaffer::StringPlug *namePlug();
		const Gaffer::StringPlug *namePlug() const;

		/// A plug defining the type of the shader.
		Gaffer::StringPlug *typePlug();
		const Gaffer::StringPlug *typePlug() const;

		/// A plug defining the suffix used for shader assignment attributes
		Gaffer::StringPlug *attributeSuffixPlug();
		const Gaffer::StringPlug *attributeSuffixPlug() const;

		/// Plug under which the shader parameters are defined.
		Gaffer::Plug *parametersPlug();
		const Gaffer::Plug *parametersPlug() const;

		/// Shaders can be enabled and disabled. A disabled shader
		/// returns an empty object from the state() method, causing
		/// any downstream ShaderAssignments to act as if they've been
		/// disabled. If a shader in the middle of a network is disabled
		/// then by default its output connections are ignored on any
		/// downstream nodes. Derived classes may implement correspondingInput( outPlug() )
		/// to allow disabled shaders to act as a pass-through instead.
		Gaffer::BoolPlug *enabledPlug() override;
		const Gaffer::BoolPlug *enabledPlug() const override;

		/// Plug which defines the shader's output - this should
		/// be connected to a ShaderAssignment::shaderPlug() or
		/// in the case of shaders which support networking it may
		/// be connected to a parameter plug of another shader.
		Gaffer::Plug *outPlug();
		const Gaffer::Plug *outPlug() const;

		/// Implemented so that the children of parametersPlug() affect
		/// outPlug().
		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

		/// \undoable
		/// Subclasses of Shader should define how to load a given shader name, and populate the parameters
		/// plug
		virtual void loadShader( const std::string &shaderName, bool keepExistingValues=false );

		/// Subclasses of Shader should do any extra cache clearing required, and then call the
		/// base class implementation
		virtual void reloadShader();

		/// \deprecated Use ShaderPlug::attributesHash() instead.
		/// \todo Protect these methods, and enforce access via the
		/// ShaderPlug methods - this would be consistent with our
		/// other APIs where nodes provide the engine, but plugs
		/// provide the interface.
		IECore::MurmurHash attributesHash() const;
		void attributesHash( IECore::MurmurHash &h ) const;
		/// \deprecated See above.
		IECore::ConstCompoundObjectPtr attributes() const;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		/// Attributes computation
		/// ----------------------
		///
		/// These methods are used to perform the compute that turns the shader network
		/// into one or more attributes that are made available by `ShaderPlug::attributes()`.
		/// May be overridden by derived classes to customise the output. Customisation may
		/// also be achieved at the level of individual shader parameters by implementing
		/// the parameter conversion methods below.

		virtual bool affectsAttributes( const Gaffer::Plug *input ) const;
		virtual void attributesHash( const Gaffer::Plug *output, IECore::MurmurHash &h ) const;
		virtual IECore::ConstCompoundObjectPtr attributes( const Gaffer::Plug *output ) const;

		/// Parameter conversion
		/// --------------------

		/// Called when computing `attributesHash()`. May be reimplemented in derived classes
		/// to deal with special cases, in which case `parameterValue()` should be reimplemented too.
		virtual void parameterHash( const Gaffer::Plug *parameterPlug, IECore::MurmurHash &h ) const;
		/// Called for each parameter plug when constructing an IECore::Shader from this node
		/// in the `attributes()` method. May be reimplemented in derived classes to deal with special
		/// cases.
		virtual IECore::DataPtr parameterValue( const Gaffer::Plug *parameterPlug ) const;

	private :

		class NetworkBuilder;

		void nameChanged();
		void nodeMetadataChanged( IECore::InternedString key );

		// We want to use the node name when computing the shader, so that we
		// can generate more useful shader handles. It's illegal to use anything
		// other than plugs to affect computation though, so we use nameChanged()
		// to transfer the value onto this private plug, thus ensuring that
		// dirtiness is signalled appropriately and we have access to the name
		// when computing.
		Gaffer::StringPlug *nodeNamePlug();
		const Gaffer::StringPlug *nodeNamePlug() const;
		// As above, we want to put the node colour in the shader for diagnostic
		// use in the scene UI, so we must transfer it on to this plug to use
		// during compute.
		Gaffer::Color3fPlug *nodeColorPlug();
		const Gaffer::Color3fPlug *nodeColorPlug() const;
		/// Output plug where the shader network will be generated.
		Gaffer::CompoundObjectPlug *outAttributesPlug();
		const Gaffer::CompoundObjectPlug *outAttributesPlug() const;

		static const IECore::InternedString g_outputParameterContextName;

		static size_t g_firstPlugIndex;

		friend class ShaderPlug;
		friend class ShaderTweaks;

};

IE_CORE_DECLAREPTR( Shader )

} // namespace GafferScene
