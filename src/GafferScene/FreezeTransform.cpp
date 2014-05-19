//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2014, John Haddon. All rights reserved.
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

#include "IECore/TransformOp.h"
#include "IECore/DespatchTypedData.h"

#include "Gaffer/Context.h"

#include "GafferScene/FreezeTransform.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( FreezeTransform );

size_t FreezeTransform::g_firstPlugIndex = 0;

FreezeTransform::FreezeTransform( const std::string &name )
	:	FilteredSceneProcessor( name, Filter::EveryMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new M44fPlug( "__transform", Plug::Out ) );
}

FreezeTransform::~FreezeTransform()
{
}

Gaffer::M44fPlug *FreezeTransform::transformPlug()
{
	return getChild<M44fPlug>( g_firstPlugIndex );
}

const Gaffer::M44fPlug *FreezeTransform::transformPlug() const
{
	return getChild<M44fPlug>( g_firstPlugIndex );
}

void FreezeTransform::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );
	
	if( input == inPlug()->transformPlug() )
	{
		outputs.push_back( transformPlug() );
	}
	else if(
		input == transformPlug() ||
		input == filterPlug()
	)
	{
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->boundPlug() );
		outputs.push_back( outPlug()->objectPlug() );
	}
}

void FreezeTransform::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hash( output, context, h );
	
	if( output == transformPlug() )
	{
		const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
		h.append( inPlug()->fullTransformHash( scenePath ) );
		h.append( outPlug()->fullTransformHash( scenePath ) );		
	}
}

void FreezeTransform::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == transformPlug() )
	{
		/// \todo Would it speed things up if we computed this from the parent full transforms and
		/// the local transforms? So we don't traverse the full path at each location?
		const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
		const M44f inTransform = inPlug()->fullTransform( scenePath );
		const M44f outTransform = outPlug()->fullTransform( scenePath );
		const M44f transform = inTransform * outTransform.inverse();
		static_cast<M44fPlug *>( output )->setValue( transform );
		return;
	}
	
	FilteredSceneProcessor::compute( output, context );
}

void FreezeTransform::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	const unsigned m = filterPlug()->getValue();	
	if( m & ( Filter::AncestorMatch | Filter::ExactMatch ) )
	{
		// if there's an ancestor match or an exact match here then we know
		// that we'll be baking in a transform into the objects below us, and
		// thus changing the bounds - so we must compute them properly from
		// children.
		SceneProcessor::hashBound( path, context, parent, h );
		h.append( hashOfTransformedChildBounds( path, outPlug() ) );
		// we may also be changing the bounds at this specific location.
		inPlug()->boundPlug()->hash( h );
		transformPlug()->hash( h );
	}
	else
	{
		// if there's no match, we can just pass through the bound
		// unchanged. additionally, if there's a descendant match we
		// can do the same - because the descendant will just be transferring
		// the descendant transform into the descendant bound, the overall
		// bound as we see it will actually be remaining the same.
		h = inPlug()->boundPlug()->hash();
	}
}

Imath::Box3f FreezeTransform::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	const unsigned m = filterPlug()->getValue();	
	if( m & ( Filter::AncestorMatch | Filter::ExactMatch ) )
	{
		Box3f result = unionOfTransformedChildBounds( path, outPlug() );
		Box3f b = inPlug()->boundPlug()->getValue();
		b = transform( b, transformPlug()->getValue() );
		result.extendBy( b );
		return result;
	}
	else
	{
		return inPlug()->boundPlug()->getValue();
	}
}

void FreezeTransform::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	const unsigned m = filterPlug()->getValue();
	if( m & Filter::ExactMatch )
	{
		SceneProcessor::hashTransform( path, context, parent, h );
	}
	else
	{
		h = inPlug()->transformPlug()->hash();
	}
}

Imath::M44f FreezeTransform::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	const unsigned m = filterPlug()->getValue();
	if( m & Filter::ExactMatch )
	{
		return M44f();
	}
	else
	{
		return inPlug()->transformPlug()->getValue();
	}
}

void FreezeTransform::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = inPlug()->attributesPlug()->hash();
}

IECore::ConstCompoundObjectPtr FreezeTransform::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return inPlug()->attributesPlug()->getValue();
}

void FreezeTransform::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	const unsigned m = filterPlug()->getValue();
	if( m & ( Filter::AncestorMatch | Filter::ExactMatch ) )
	{
		FilteredSceneProcessor::hashObject( path, context, parent, h );
		inPlug()->objectPlug()->hash( h );
		transformPlug()->hash( h );
	}
	else
	{
		h = inPlug()->objectPlug()->hash();
	}
}

IECore::ConstObjectPtr FreezeTransform::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	const unsigned m = filterPlug()->getValue();
	if( m & ( Filter::AncestorMatch | Filter::ExactMatch ) )
	{
		ConstObjectPtr inputObject = inPlug()->objectPlug()->getValue();
		const Primitive *inputPrimitive = runTimeCast<const Primitive>( inputObject.get() );
		if( !inputPrimitive )
		{
			/// \todo It's not entirely clear what to do here. We'd end up here for
			/// any non-primitive objects, which to date include cameras and lights, and
			/// will most likely include coordinate systems in the future. In Cortex, cameras
			/// and coordinate systems actually have a setTransform() method, so in theory we
			/// could use that to bake the transform into the object - maybe we could do the
			/// same for lights?
			return inputObject;
		}
		
		PrimitivePtr outputPrimitive = inputPrimitive->copy();
		
		/// \todo This is a pain - we need functionality in Cortex to just automatically apply
		/// the transform to all appropriate primitive variables, without having to manually
		/// list them. At the same time, we could add a PrimitiveAlgo.h file to Cortex, allowing
		/// us to apply a transform without having to create an Op to do it.
		vector<string> primVarNames;
		for( PrimitiveVariableMap::const_iterator it = inputPrimitive->variables.begin(), eIt = inputPrimitive->variables.end(); it != eIt; ++it )
		{
			if( despatchTraitsTest<TypeTraits::IsFloatVec3VectorTypedData>( it->second.data ) )
			{
				primVarNames.push_back( it->first );
			} 
		}
		
		const M44f transform = transformPlug()->getValue();
		
		TransformOpPtr transformOp = new TransformOp;
		transformOp->inputParameter()->setValue( outputPrimitive );
		transformOp->copyParameter()->setTypedValue( false );
		transformOp->matrixParameter()->setValue( new M44fData( transform ) );
		transformOp->primVarsParameter()->setTypedValue( primVarNames );
		transformOp->operate();
		
		return outputPrimitive;
	}
	else
	{
		return inPlug()->objectPlug()->getValue();	
	}
}

void FreezeTransform::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = inPlug()->childNamesPlug()->hash();
}

IECore::ConstInternedStringVectorDataPtr FreezeTransform::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return inPlug()->childNamesPlug()->getValue();
}

void FreezeTransform::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = inPlug()->globalsPlug()->hash();
}

IECore::ConstCompoundObjectPtr FreezeTransform::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return inPlug()->globalsPlug()->getValue();
}
