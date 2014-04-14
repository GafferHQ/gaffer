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

#ifndef GAFFEROSL_OSLRENDERER_H
#define GAFFEROSL_OSLRENDERER_H

#include <stack>

#include "OSL/oslexec.h"

#include "IECore/Renderer.h"
#include "IECore/Shader.h"

#include "GafferOSL/TypeIds.h"

namespace GafferOSL
{

IE_CORE_FORWARDDECLARE( OSLRenderer )

/// This class allows the execution of networks of OSL shaders on sets of points provided
/// as IECore datatypes, returning the shading results as IECore data. It derives from Renderer
/// so that code for declaring shaders and state to an actual renderer can be reused for
/// specifying the shaders and state to be executed with here.
/// \threading None of the methods of this class are threadsafe, but ShadingEngine::shade()
/// method is.
class OSLRenderer : public IECore::Renderer
{

	public :
		
		OSLRenderer();
		virtual ~OSLRenderer();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferOSL::OSLRenderer, OSLRendererTypeId, IECore::Renderer );

		/// Parameters matching "osl:*" are passed to OSL::ShadingSystem::attribute().
		virtual void setOption( const std::string &name, IECore::ConstDataPtr value );
		virtual IECore::ConstDataPtr getOption( const std::string &name ) const;

		virtual void camera( const std::string &name, const IECore::CompoundDataMap &parameters );
		virtual void display( const std::string &name, const std::string &type, const std::string &data, const IECore::CompoundDataMap &parameters );

		virtual void worldBegin();
		virtual void worldEnd();

		virtual void transformBegin();
		virtual void transformEnd();
		virtual void setTransform( const Imath::M44f &m );
		virtual void setTransform( const std::string &coordinateSystem );
		virtual Imath::M44f getTransform() const;
		virtual Imath::M44f getTransform( const std::string &coordinateSystem ) const;
		virtual void concatTransform( const Imath::M44f &m );
		virtual void coordinateSystem( const std::string &name );

		virtual void attributeBegin();
		virtual void attributeEnd();

		virtual void setAttribute( const std::string &name, IECore::ConstDataPtr value );
		virtual IECore::ConstDataPtr getAttribute( const std::string &name ) const;

		virtual void shader( const std::string &type, const std::string &name, const IECore::CompoundDataMap &parameters );
		virtual void light( const std::string &name, const std::string &handle, const IECore::CompoundDataMap &parameters );
		virtual void illuminate( const std::string &lightHandle, bool on );

		virtual void motionBegin( const std::set<float> &times );
		virtual void motionEnd();

		virtual void points( size_t numPoints, const IECore::PrimitiveVariableMap &primVars );
		virtual void disk( float radius, float z, float thetaMax, const IECore::PrimitiveVariableMap &primVars );

		virtual void curves( const IECore::CubicBasisf &basis, bool periodic, IECore::ConstIntVectorDataPtr numVertices, const IECore::PrimitiveVariableMap &primVars );

		virtual void text( const std::string &font, const std::string &text, float kerning = 1.0f, const IECore::PrimitiveVariableMap &primVars=IECore::PrimitiveVariableMap() );
		virtual void sphere( float radius, float zMin, float zMax, float thetaMax, const IECore::PrimitiveVariableMap &primVars );

		virtual void image( const Imath::Box2i &dataWindow, const Imath::Box2i &displayWindow, const IECore::PrimitiveVariableMap &primVars );
		virtual void mesh( IECore::ConstIntVectorDataPtr vertsPerFace, IECore::ConstIntVectorDataPtr vertIds, const std::string &interpolation, const IECore::PrimitiveVariableMap &primVars );

		virtual void nurbs( int uOrder, IECore::ConstFloatVectorDataPtr uKnot, float uMin, float uMax, int vOrder, IECore::ConstFloatVectorDataPtr vKnot, float vMin, float vMax, const IECore::PrimitiveVariableMap &primVars );

		virtual void patchMesh( const IECore::CubicBasisf &uBasis, const IECore::CubicBasisf &vBasis, int nu, bool uPeriodic, int nv, bool vPeriodic, const IECore::PrimitiveVariableMap &primVars );

		virtual void geometry( const std::string &type, const IECore::CompoundDataMap &topology, const IECore::PrimitiveVariableMap &primVars );

		virtual void procedural( IECore::Renderer::ProceduralPtr proc );

		virtual void instanceBegin( const std::string &name, const IECore::CompoundDataMap &parameters );
		virtual void instanceEnd();
		virtual void instance( const std::string &name );

		virtual IECore::DataPtr command( const std::string &name, const IECore::CompoundDataMap &parameters );

		virtual void editBegin( const std::string &editType, const IECore::CompoundDataMap &parameters );
		virtual void editEnd();
				
		class ShadingEngine : public IECore::RefCounted
		{
			
			public :

				IE_CORE_DECLAREMEMBERPTR( ShadingEngine )
		
				IECore::CompoundDataPtr shade( const IECore::CompoundData *points ) const;
				
			private :
			
				friend class OSLRenderer;
			
				ShadingEngine( ConstOSLRendererPtr renderer, OSL::ShadingAttribStateRef shadingState );
			
				ConstOSLRendererPtr m_renderer;
				OSL::ShadingAttribStateRef m_shadingState;
		
		};
		
		IE_CORE_DECLAREPTR( ShadingEngine )
		
		/// Returns a shading engine set up using the current attribute state.
		ShadingEnginePtr shadingEngine() const;

	private :

		class RenderState;
		class RendererServices;
		class ShadingResults;
		
		enum ClosureId
		{
			EmissionClosureId,
			DebugClosureId
		};
		
		struct EmissionParameters;
		struct DebugParameters;

		boost::shared_ptr<OSL::ShadingSystem> m_shadingSystem;

		struct State
		{
			State();
			State( const State &other );
			~State();
			
			std::vector<IECore::ConstShaderPtr> shaders;
			IECore::ConstShaderPtr surfaceShader;
		};
		
		typedef std::stack<State> StateStack;
		
		StateStack m_stateStack;
		
};

IE_CORE_DECLAREPTR( OSLRenderer );

} // namespace GafferOSL

#endif // GAFFEROSL_OSLRENDERER_H
