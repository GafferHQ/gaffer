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

#include "boost/python.hpp"

#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/GraphComponent.h"
#include "Gaffer/Plug.h"
#include "Gaffer/Node.h"

using namespace boost::python;
using namespace Gaffer;
using namespace Gaffer::MetadataAlgo;

namespace GafferBindings
{

void bindMetadataAlgo()
{
	object module( borrowed( PyImport_AddModule( "Gaffer.MetadataAlgo" ) ) );
	scope().attr( "MetadataAlgo" ) = module;
	scope moduleScope( module );

	def( "setReadOnly", &setReadOnly, ( arg( "graphComponent" ), arg( "readOnly"), arg( "persistent" ) = true ) );
	def( "getReadOnly", &getReadOnly );
	def( "readOnly", &readOnly );
	def(
		"affectedByChange",
		(bool (*)( const Plug *, IECore::TypeId, const MatchPattern &, const Plug * ))&affectedByChange,
		( arg( "plug" ), arg( "changedNodeTypeId"), arg( "changedPlugPath" ), arg( "changedPlug" ) )
	);
	def(
		"affectedByChange",
		(bool (*)( const Node *node, IECore::TypeId changedNodeTypeId, const Node *changedNode ))&affectedByChange,
		( arg( "node" ), arg( "changedNodeTypeId"), arg( "changedNode" ) )
	);
	def( "childAffectedByChange", &childAffectedByChange, ( arg( "parent" ), arg( "changedNodeTypeId"), arg( "changedPlugPath" ), arg( "changedPlug" ) ) );
	def( "ancestorAffectedByChange", &ancestorAffectedByChange, ( arg( "plug" ), arg( "changedNodeTypeId"), arg( "changedPlugPath" ), arg( "changedPlug" ) ) );

}

} // namespace GafferBindings
