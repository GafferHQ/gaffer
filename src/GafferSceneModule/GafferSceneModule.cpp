//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#include "boost/python.hpp"

#include "AttributesBinding.h"
#include "CoreBinding.h"
#include "EditScopeAlgoBinding.h"
#include "FilterBinding.h"
#include "GlobalsBinding.h"
#include "HierarchyBinding.h"
#include "IECoreGLPreviewBinding.h"
#include "IOBinding.h"
#include "TweaksBinding.h"
#include "ObjectProcessorBinding.h"
#include "OptionsBinding.h"
#include "PrimitiveSamplerBinding.h"
#include "PrimitiveVariablesBinding.h"
#include "PrimitivesBinding.h"
#include "RenderBinding.h"
#include "RenderControllerBinding.h"
#include "SceneAlgoBinding.h"
#include "ScenePathBinding.h"
#include "SetAlgoBinding.h"
#include "ShaderBinding.h"
#include "TransformBinding.h"
#include "QueryBinding.h"

using namespace boost::python;
using namespace GafferSceneModule;

BOOST_PYTHON_MODULE( _GafferScene )
{

	bindCore();
	bindFilter();
	bindTransform();
	bindGlobals();
	bindOptions();
	bindAttributes();
	bindSceneAlgo();
	bindSetAlgo();
	bindPrimitives();
	bindScenePath();
	bindShader();
	bindRender();
	bindRenderController();
	bindHierarchy();
	bindObjectProcessor();
	bindPrimitiveVariables();
	bindTweaks();
	bindIO();
	bindPrimitiveSampler();
	bindIECoreGLPreview();
	bindEditScopeAlgo();
	bindQueries();

}
