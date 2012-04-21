//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "IECore/PointDistributionOp.h"

#include "GafferScene/Seeds.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Seeds );

Seeds::Seeds( const std::string &name )
	:	SceneProcessor( name )
{
	addChild( new StringPlug( "source" ) );
	addChild( new StringPlug( "name", Plug::In, "seeds" ) );
	addChild( new FloatPlug( "density", Plug::In, 1.0f, 0.0f ) );
	addChild( new StringPlug( "pointType", Plug::In, "gl:point" ) );
}

Seeds::~Seeds()
{
}

Gaffer::StringPlug *Seeds::sourcePlug()
{
	return getChild<StringPlug>( "source" );
}

const Gaffer::StringPlug *Seeds::sourcePlug() const
{
	return getChild<StringPlug>( "source" );
}

Gaffer::StringPlug *Seeds::namePlug()
{
	return getChild<StringPlug>( "name" );
}

const Gaffer::StringPlug *Seeds::namePlug() const
{
	return getChild<StringPlug>( "name" );
}

Gaffer::FloatPlug *Seeds::densityPlug()
{
	return getChild<FloatPlug>( "density" );
}

const Gaffer::FloatPlug *Seeds::densityPlug() const
{
	return getChild<FloatPlug>( "density" );
}

Gaffer::StringPlug *Seeds::pointTypePlug()
{
	return getChild<StringPlug>( "pointType" );
}

const Gaffer::StringPlug *Seeds::pointTypePlug() const
{
	return getChild<StringPlug>( "pointType" );
}

void Seeds::affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );
	
	const ScenePlug *in = inPlug();
	if( input->parent<ScenePlug>() == in )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if( input == sourcePlug() || input == namePlug() )
	{
		outputs.push_back( outPlug() );
	}
	else if( input == densityPlug() || input == pointTypePlug() )
	{
		outputs.push_back( outPlug()->geometryPlug() );
	}
}

Imath::Box3f Seeds::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	string source = sourcePlug()->getValue();
	if( path == source + "/" + namePlug()->getValue() )
	{
		return inPlug()->bound( sourcePlug()->getValue() );
	}	
	else
	{
		return inPlug()->boundPlug()->getValue();
	}
}

Imath::M44f Seeds::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	string source = sourcePlug()->getValue();
	if( path == source + "/" + namePlug()->getValue() )
	{
		return M44f();
	}	
	else
	{
		return inPlug()->transformPlug()->getValue();
	}
}

IECore::PrimitivePtr Seeds::computeGeometry( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	string source = sourcePlug()->getValue();
	if( path == source + "/" + namePlug()->getValue() )
	{
		// do what we came for
		ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( inPlug()->geometry( source ) );
		if( !mesh )
		{
			return 0;
		}
		
		PointDistributionOpPtr op = new PointDistributionOp();
		op->meshParameter()->setValue( mesh->copy() );
		op->densityParameter()->setNumericValue( densityPlug()->getValue() );
		
		PrimitivePtr result = runTimeCast<Primitive>( op->operate() );
		result->variables["type"] = PrimitiveVariable( PrimitiveVariable::Constant, new StringData( pointTypePlug()->getValue() ) );
		
		return result;
	}
	else
	{
		ConstPrimitivePtr primitive = inPlug()->geometryPlug()->getValue();
		return primitive ? primitive->copy() : 0;
	}
}

IECore::StringVectorDataPtr Seeds::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::ConstStringVectorDataPtr inputNames = inPlug()->childNamesPlug()->getValue();
	StringVectorDataPtr outputNames = inputNames ? inputNames->copy() : 0;
	if( path == sourcePlug()->getValue() )
	{
		std::string name = namePlug()->getValue();
		if( name.size() )
		{
			if( !outputNames )
			{
				outputNames = new StringVectorData();
			}
			outputNames->writable().push_back( name );
		}
	}
	
	return outputNames;
}
