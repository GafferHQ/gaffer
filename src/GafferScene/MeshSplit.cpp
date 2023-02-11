//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/MeshSplit.h"

#include "GafferScene/SceneAlgo.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/MeshAlgo.h"

#include "IECore/DataAlgo.h"
#include "IECore/NullObject.h"
#include "IECore/StringAlgo.h"

#include "fmt/compile.h"
#include "fmt/core.h"

#include <unordered_map>

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace {

// Various private helpers for formatAsInternedString

const std::string g_commaStr( ", " );

template< typename T >
void stringConvertHelper( const T &a, char *&current, char *end )
{
	// This interface was planned for std::to_chars, but it works fine with fmt::format_to_n
	// too. It's all private anyway.
	auto result = fmt::format_to_n( current, end - current, FMT_COMPILE("{}"), a);
	if( result.size > (size_t)( end - current ) )
	{
		throw IECore::Exception( "Internal error in formatAsInternedString - buffer not large enough" );
	}
	current = result.out;
}

void stringConvertHelper( const half &a, char *&current, char *end )
{
	float f = a;
	stringConvertHelper( f, current, end );
}

template< typename T >
void stringConvertHelper( const Imath::Vec2<T> &a, char *&current, char *end )
{
	stringConvertHelper( a.x, current, end );
	stringConvertHelper( g_commaStr, current, end );
	stringConvertHelper( a.y, current, end );
}

template< typename T >
void stringConvertHelper( const Imath::Vec3<T> &a, char *&current, char *end )
{
	stringConvertHelper( a.x, current, end );
	stringConvertHelper( g_commaStr, current, end );
	stringConvertHelper( a.y, current, end );
	stringConvertHelper( g_commaStr, current, end );
	stringConvertHelper( a.z, current, end );
}

template< typename T >
void stringConvertHelper( const Imath::Color3<T> &a, char *&current, char *end )
{
	stringConvertHelper( a.x, current, end );
	stringConvertHelper( g_commaStr, current, end );
	stringConvertHelper( a.y, current, end );
	stringConvertHelper( g_commaStr, current, end );
	stringConvertHelper( a.z, current, end );
}

template< typename T >
void stringConvertHelper( const Imath::Color4<T> &a, char *&current, char *end )
{
	stringConvertHelper( a.r, current, end );
	stringConvertHelper( g_commaStr, current, end );
	stringConvertHelper( a.g, current, end );
	stringConvertHelper( g_commaStr, current, end );
	stringConvertHelper( a.b, current, end );
	stringConvertHelper( g_commaStr, current, end );
	stringConvertHelper( a.a, current, end );
}

template< typename T >
void stringConvertHelper( const Imath::Quat<T> &a, char *&current, char *end )
{
	stringConvertHelper( a.r, current, end );
	stringConvertHelper( g_commaStr, current, end );
	stringConvertHelper( a.v, current, end );
}

template< typename T >
void stringConvertHelper( const Imath::Matrix33<T> &a, char *&current, char *end )
{
	for( int i = 0; i < 3; i++ )
	{
		for( int j = 0; j < 3; j++ )
		{
			stringConvertHelper( a[i][j], current, end );
			if( !( i == 2 && j == 2 ) )
			{
				stringConvertHelper( g_commaStr, current, end );
			}
		}
	}
}

template< typename T >
void stringConvertHelper( const Imath::Matrix44<T> &a, char *&current, char *end )
{
	for( int i = 0; i < 4; i++ )
	{
		for( int j = 0; j < 4; j++ )
		{
			stringConvertHelper( a[i][j], current, end );
			if( !( i == 3 && j == 3 ) )
			{
				stringConvertHelper( g_commaStr, current, end );
			}
		}
	}
}

template< typename T >
void stringConvertHelper( const Imath::Box<T> &a, char *&current, char *end )
{
	static const std::string arrowStr = " -> ";
	stringConvertHelper( a.min, current, end );
	stringConvertHelper( arrowStr, current, end );
	stringConvertHelper( a.max, current, end );
}

// A fast function for converting any of the value types supported by vector typed data to an interned string,
// including Imath types.
template< typename T >
inline IECore::InternedString formatAsInternedString( const T &a, std::string &buffer )
{
	if constexpr(
		std::is_integral< T >::value ||
		std::is_same< T, std::string >::value ||
		std::is_same< T, IECore::InternedString >::value
	)
	{
		return IECore::InternedString( a );
	}
	else
	{
		// Allocate enough space in the temp buffer to format an M44d, which is the largest type
		// currently supported
		buffer.resize( 16 * 20 );
		char *current = buffer.data();
		char *end = buffer.data() + buffer.size();
		stringConvertHelper( a, current, end );
		buffer.resize( current - buffer.data() );
		return IECore::InternedString( buffer );
	}
}

} // namespace

class MeshSplit::MeshSplitterData : public IECore::Data
{

	public :
		MeshSplitterData( ConstMeshPrimitivePtr mesh, const PrimitiveVariable &primitiveVariable, bool nameFromSegment, const IECore::Canceller *canceller ) : m_splitter( mesh, primitiveVariable, canceller )
		{
			InternedStringVectorDataPtr namesData = new InternedStringVectorData;
			std::vector<InternedString> &names = namesData->writable();
			names.reserve( m_splitter.numMeshes() );

			if( !nameFromSegment )
			{
				for( int i = 0; i < m_splitter.numMeshes(); i++ )
				{
					if( i % 10000 == 0 )
					{
						Canceller::check( canceller );
					}
					InternedString name( i );
					names.push_back( name );
				}
			}
			else
			{
				IECore::dispatch( primitiveVariable.data.get(),
					[ this, &names, canceller]( const auto *primVarData )
					{
						using DataType = typename std::remove_pointer_t< decltype( primVarData ) >;
						if constexpr ( !TypeTraits::IsVectorTypedData<DataType>::value )
						{
							throw IECore::Exception( "Invalid PrimitiveVariable, data is not a vector." );
						}
						else
						{
							using ElementType = typename DataType::ValueType::value_type;
							std::string buffer;
							for( int i = 0; i < m_splitter.numMeshes(); i++ )
							{
								if( i % 10000 == 0 )
								{
									Canceller::check( canceller );
								}
								const ElementType& val = m_splitter.value< ElementType >( i );
								InternedString name = formatAsInternedString( val, buffer );
								m_nameMap[ name ] = i;
								names.push_back( name );
							}
						}
					}
				);
			}

			m_names = namesData;
		}

		ConstInternedStringVectorDataPtr names() const
		{
			return m_names;
		}

		MeshPrimitivePtr splitMesh( const IECore::InternedString &name ) const
		{
			return m_splitter.mesh( indexFromName( name ) );
		}

		Imath::Box3f splitBound( const IECore::InternedString &name ) const
		{
			return m_splitter.bound( indexFromName( name ) );
		}

	private:

		inline int indexFromName( const IECore::InternedString &name ) const
		{
			if( m_nameMap.size() )
			{
				return m_nameMap.at( name );
			}
			else
			{
				return stoi( name.string() );
			}
		}

		IECore::ConstInternedStringVectorDataPtr m_names;
		std::unordered_map< InternedString, int > m_nameMap;

		const MeshAlgo::MeshSplitter m_splitter;

};

GAFFER_NODE_DEFINE_TYPE( MeshSplit );

size_t MeshSplit::g_firstPlugIndex = 0;

MeshSplit::MeshSplit( const std::string &name )
	:	BranchCreator( name )
{

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "segment", Plug::In, "segment" ) );
	addChild( new BoolPlug( "nameFromSegment" ) );
	addChild( new BoolPlug( "preciseBounds" ) );

	addChild( new ObjectPlug( "__meshSplitter", Plug::Out, NullObject::defaultNullObject() ) );

	// Hide `destination` plug until we resolve issues surrounding `processesRootObject()`.
	// See `BranchCreator::computeObject()`. Or perhaps we would never want to allow a
	// different destination anyway?
	destinationPlug()->setName( "__destination" );

	// Since we don't introduce any new sets, but just duplicate parts
	// of existing ones, we can save the BranchCreator base class some
	// trouble by making the setNamesPlug into a pass-through.
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
}

MeshSplit::~MeshSplit()
{
}

Gaffer::StringPlug *MeshSplit::segmentPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *MeshSplit::segmentPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *MeshSplit::nameFromSegmentPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *MeshSplit::nameFromSegmentPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *MeshSplit::preciseBoundsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *MeshSplit::preciseBoundsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::ObjectPlug *MeshSplit::meshSplitterPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::ObjectPlug *MeshSplit::meshSplitterPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 3 );
}

void MeshSplit::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	BranchCreator::affects( input, outputs );

	if( input == segmentPlug() || input == nameFromSegmentPlug() || input == inPlug()->objectPlug() )
	{
		outputs.push_back( meshSplitterPlug() );
	}
}

void MeshSplit::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hash( output, context, h );

	if( output == meshSplitterPlug() )
	{
		segmentPlug()->hash( h );
		nameFromSegmentPlug()->hash( h );

		inPlug()->objectPlug()->hash( h );
	}
}

void MeshSplit::compute( ValuePlug *output, const Context *context ) const
{
	if( output == meshSplitterPlug() )
	{
		MeshSplitterDataPtr splitter = nullptr;

		std::string segmentPrimVarName = segmentPlug()->getValue();
		bool nameFromSegment = nameFromSegmentPlug()->getValue();

		IECore::ConstObjectPtr object = inPlug()->objectPlug()->getValue();
		const MeshPrimitive *mesh = runTimeCast<const MeshPrimitive>( object.get() );

		// Silently ignore if there is no mesh, in case you want to
		// split a bunch of meshes with a filter that include some non-mesh objects as well
		if( mesh )
		{
			auto varIt = mesh->variables.find( segmentPrimVarName );
			if( varIt == mesh->variables.end() )
			{
				throw IECore::Exception( "Cannot find primitive variable \"" + segmentPrimVarName + "\"." );
			}

			splitter = new MeshSplitterData( mesh, varIt->second, nameFromSegment, context->canceller() );
		}

		static_cast<ObjectPlug *>( output )->setValue( splitter ? (const Object*)splitter.get() : NullObject::defaultNullObject() );
		return;
	}

	BranchCreator::compute( output, context );
}

bool MeshSplit::affectsBranchBound( const Gaffer::Plug *input ) const
{
	return input == inPlug()->boundPlug() || input == preciseBoundsPlug() || input == meshSplitterPlug();
}

void MeshSplit::hashBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( !preciseBoundsPlug()->getValue() )
	{
		h = inPlug()->boundHash( sourcePath );
	}
	else
	{
		BranchCreator::hashBranchBound( sourcePath, branchPath, context, h );
		ScenePlug::PathScope s( context, &sourcePath );
		meshSplitterPlug()->hash( h );
		h.append( branchPath[0] );
	}
}

Imath::Box3f MeshSplit::computeBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	assert( branchPath.size() == 1 );

	if( !preciseBoundsPlug()->getValue() )
	{
		return inPlug()->bound( sourcePath );
	}
	else
	{
		ScenePlug::PathScope s( context, &sourcePath );
		ConstMeshSplitterDataPtr meshSplitter = static_pointer_cast<const MeshSplitterData>( meshSplitterPlug()->getValue() );
		return meshSplitter->splitBound( branchPath[0] );
	}
}

bool MeshSplit::affectsBranchTransform( const Gaffer::Plug *input ) const
{
	return false;
}

void MeshSplit::hashBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchTransform( sourcePath, branchPath, context, h );
}

Imath::M44f MeshSplit::computeBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return Imath::M44f();
}

void MeshSplit::hashBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->attributesPlug()->defaultHash();
}

IECore::ConstCompoundObjectPtr MeshSplit::computeBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return inPlug()->attributesPlug()->defaultValue();
}

bool MeshSplit::processesRootObject() const
{
	return true;
}

bool MeshSplit::affectsBranchObject( const Gaffer::Plug *input ) const
{
	return input == inPlug()->objectPlug();
}

void MeshSplit::hashBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchObject( sourcePath, branchPath, context, h );

	if( branchPath.size() == 0 )
	{
		inPlug()->objectPlug()->hash( h );
		return;
	}

	assert( branchPath.size() == 1 );

	ScenePlug::PathScope s( context, &sourcePath );
	meshSplitterPlug()->hash( h );
	h.append( branchPath[0] );
}

IECore::ConstObjectPtr MeshSplit::computeBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 0 )
	{
		IECore::ConstObjectPtr inObject = inPlug()->objectPlug()->getValue();
		if( runTimeCast<const MeshPrimitive>( inObject.get() ) )
		{
			// If we're filtered to a mesh, we're going to split into it's children, so we remove
			// the original mesh.
			return NullObject::defaultNullObject();
		}
		else
		{
			// Not a mesh, pass it unchanged
			return inObject;
		}
	}

	assert( branchPath.size() == 1 );

	ScenePlug::PathScope s( context, &sourcePath );
	ConstMeshSplitterDataPtr meshSplitter = static_pointer_cast<const MeshSplitterData>( meshSplitterPlug()->getValue() );
	return meshSplitter->splitMesh( branchPath[0] );
}

bool MeshSplit::affectsBranchChildNames( const Gaffer::Plug *input ) const
{
	return input == meshSplitterPlug();
}

void MeshSplit::hashBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 0 )
	{
		BranchCreator::hashBranchChildNames( sourcePath, branchPath, context, h );
		ScenePlug::PathScope s( context, &sourcePath );
		meshSplitterPlug()->hash( h );
	}
	else
	{
		h = inPlug()->childNamesPlug()->defaultHash();
	}
}

IECore::ConstInternedStringVectorDataPtr MeshSplit::computeBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 0 )
	{
		ScenePlug::PathScope s( context, &sourcePath );
		ConstObjectPtr meshSplitterRaw = meshSplitterPlug()->getValue();

		if( meshSplitterRaw.get() == NullObject::defaultNullObject() )
		{
			// Not a valid target for splitting
			return inPlug()->childNamesPlug()->defaultValue();
		}

		const MeshSplitterData *meshSplitter = static_cast<const MeshSplitterData*>( meshSplitterRaw.get() );
		return meshSplitter->names();
	}
	else
	{
		return inPlug()->childNamesPlug()->defaultValue();
	}
}
