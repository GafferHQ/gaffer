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

#include "Gaffer/TypedPlug.h"
#include "Gaffer/NumericPlug.h"

#include "GafferScene/Shader.h"

using namespace Imath;
using namespace GafferScene;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( Shader );

Shader::Shader( const std::string &name )
	:	Node( name )
{
}

Shader::~Shader()
{
}

IECore::ObjectVectorPtr Shader::state() const
{
	IECore::ObjectVectorPtr s = new IECore::ObjectVector;
	s->members().push_back( shader() );
	return s;
}

/// \todo We should perhaps move the compute() method onto a new DependencyNode class,
/// so that nodes like Shader can derive straight from Node and not have any requirement
/// to implement compute().
void Shader::compute( ValuePlug *output, const Context *context ) const
{
	/// \todo If ValuePlug had a setToDefault() method then we could
	/// simply call that here.
	switch( output->typeId() )
	{
		case FloatPlugTypeId :
			static_cast<FloatPlug *>( output )->setValue( 0.0f );
			break;
		case IntPlugTypeId :
			static_cast<IntPlug *>( output )->setValue( 0 );
			break;
		case StringPlugTypeId :
			static_cast<StringPlug *>( output )->setValue( "" );
			break;
		default :
			// we don't expect to get here. if we do then there'll be an
			// error reported by ValuePlug when we don't call setValue()
			// so we don't need to do our own error handling.
			break;
	}
}
