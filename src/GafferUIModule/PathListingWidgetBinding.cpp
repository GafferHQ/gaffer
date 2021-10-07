//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "PathListingWidgetBinding.h"

#include "Gaffer/FileSystemPath.h"
#include "Gaffer/Path.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECorePython/RefCountedBinding.h"
#include "IECorePython/ScopedGILLock.h"
#include "IECorePython/ScopedGILRelease.h"

#include "IECore/DateTimeData.h"
#include "IECore/MessageHandler.h"
#include "IECore/PathMatcher.h"
#include "IECore/SearchPath.h"
#include "IECore/SimpleTypedData.h"

#include "boost/date_time/posix_time/conversion.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"

#include "QtTest/QAbstractItemModelTester"

#include "QtCore/QAbstractItemModel"
#include "QtCore/QDateTime"
#include "QtCore/QModelIndex"
#include "QtCore/QVariant"

#include "QtWidgets/QTreeView"
#include "QtWidgets/QFileIconProvider"

#include <unordered_map>

using namespace boost::python;
using namespace boost::posix_time;
using namespace Gaffer;

namespace
{

// QVariant does have `operator <`, but it's deprecated as it doesn't define a
// total ordering, making it unsuitable for our purposes.
// See https://doc.qt.io/qt-5/qvariant-obsolete.html#operator-lt.
bool variantLess( const QVariant &left, const QVariant &right )
{
	// Lexicographical comparison, first on type and then on value.

	if( left.userType() < right.userType() )
	{
		return true;
	}
	else if( right.userType() < left.userType() )
	{
		return false;
	}

	assert( left.userType() == right.userType() );

	switch( left.userType() )
	{
		case QVariant::Invalid :
			// Both values are invalid, making them equal.
			return false;
		case QVariant::Int :
			return left.toInt() < right.toInt();
		case QVariant::UInt :
			return left.toUInt() < right.toUInt();
		case QVariant::LongLong:
			return left.toLongLong() < right.toLongLong();
		case QVariant::ULongLong:
			return left.toULongLong() < right.toULongLong();
		case QMetaType::Float:
			return left.toFloat() < right.toFloat();
		case QVariant::Double:
			return left.toDouble() < right.toDouble();
		case QVariant::Char:
			return left.toChar() < right.toChar();
		case QVariant::Date:
			return left.toDate() < right.toDate();
		case QVariant::Time:
			return left.toTime() < right.toTime();
		case QVariant::DateTime:
			return left.toDateTime() < right.toDateTime();
		default :
			return left.toString() < right.toString();
	}
}

IECore::InternedString g_namePropertyName( "name" );

// Abstract class for extracting QVariants from Path objects
// in order to populate columns in the PathMode. Column
// objects only do the extraction, they are not responsible
// for storage at all.
class Column : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( Column )

		virtual QVariant data( const Path *path, int role = Qt::DisplayRole ) const = 0;
		virtual QVariant headerData( int role = Qt::DisplayRole ) const = 0;

};

IE_CORE_DECLAREPTR( Column )

class StandardColumn : public Column
{

	public :

		IE_CORE_DECLAREMEMBERPTR( StandardColumn )

		StandardColumn( const std::string &label, IECore::InternedString propertyName )
			:	m_label( label.c_str() ), m_propertyName( propertyName )
		{
		}

		QVariant data( const Path *path, int role = Qt::DisplayRole ) const override
		{
			switch( role )
			{
				case Qt::DisplayRole :
					return variantFromProperty( path );
				default :
					return QVariant();
			}
		}

		QVariant headerData( int role = Qt::DisplayRole ) const override
		{
			if( role == Qt::DisplayRole )
			{
				return m_label;
			}
			return QVariant();
		}

	private :

		QVariant variantFromProperty( const Path *path ) const
		{
			// shortcut for getting the name property directly
			if( m_propertyName == g_namePropertyName )
			{
				if( path->names().size() )
				{
					return QVariant( path->names().back().c_str() );
				}
				else
				{
					return QVariant();
				}
			}

			IECore::ConstRunTimeTypedPtr property = path->property( m_propertyName );

			if( !property )
			{
				return QVariant();
			}

			switch( property->typeId() )
			{
				case IECore::StringDataTypeId :
					return static_cast<const IECore::StringData *>( property.get() )->readable().c_str();
				case IECore::IntDataTypeId :
					return static_cast<const IECore::IntData *>( property.get() )->readable();
				case IECore::UIntDataTypeId :
					return static_cast<const IECore::UIntData *>( property.get() )->readable();
				case IECore::UInt64DataTypeId :
					return (quint64)static_cast<const IECore::UInt64Data *>( property.get() )->readable();
				case IECore::FloatDataTypeId :
					return static_cast<const IECore::FloatData *>( property.get() )->readable();
				case IECore::DoubleDataTypeId :
					return static_cast<const IECore::DoubleData *>( property.get() )->readable();
				case IECore::DateTimeDataTypeId :
				{
					const IECore::DateTimeData *d = static_cast<const IECore::DateTimeData *>( property.get() );
					time_t t = ( d->readable() - from_time_t( 0 ) ).total_seconds();
					return QVariant( QDateTime::fromTime_t( t ) );
				}
				default :
				{
					// Fall back to using `str()` in python, to emulate old behaviour. If we find commonly
					// used types within large hierarchies falling through to here, we will need to give
					// them their own special case above, for improved performance.
					IECorePython::ScopedGILLock gilLock;
					object pythonProperty( boost::const_pointer_cast<IECore::RunTimeTyped>( property ) );
					boost::python::str pythonString( pythonProperty );
					return QVariant( boost::python::extract<const char *>( pythonString ) );
				}
			}
		}

		QVariant m_label;
		IECore::InternedString m_propertyName;

};

IE_CORE_DECLAREPTR( StandardColumn )

class IconColumn : public Column
{

	public :

		IE_CORE_DECLAREMEMBERPTR( IconColumn )

		IconColumn( const std::string &label, const std::string &prefix, IECore::InternedString propertyName )
			:	m_label( label.c_str() ), m_prefix( prefix ), m_propertyName( propertyName )
		{
		}

		QVariant data( const Path *path, int role = Qt::DisplayRole ) const override
		{
			if( role == Qt::DecorationRole )
			{
				IECore::ConstRunTimeTypedPtr property = path->property( m_propertyName );
				if( !property )
				{
					return QVariant();
				}

				std::string fileName = m_prefix;
				switch( property->typeId() )
				{
					case IECore::StringDataTypeId :
						fileName += static_cast<const IECore::StringData *>( property.get() )->readable();
						break;
					case IECore::IntDataTypeId :
						fileName += boost::lexical_cast<std::string>( static_cast<const IECore::IntData *>( property.get() )->readable() );
						break;
					case IECore::UInt64DataTypeId :
						fileName += boost::lexical_cast<std::string>( static_cast<const IECore::UInt64Data *>( property.get() )->readable() );
						break;
					case IECore::BoolDataTypeId :
						fileName += boost::lexical_cast<std::string>( static_cast<const IECore::BoolData *>( property.get() )->readable() );
						break;
					default :
						IECore::msg( IECore::Msg::Warning, "PathListingWidget", boost::str( boost::format( "Unsupported property type \"%s\"" ) % property->typeName() ) );
						return QVariant();
				}

				fileName += ".png";
				return g_iconCache.get( fileName );
			}
			return QVariant();
		}

		QVariant headerData( int role = Qt::DisplayRole ) const override
		{
			if( role == Qt::DisplayRole )
			{
				return m_label;
			}
			return QVariant();
		}

	private :

		QVariant m_label;
		std::string m_prefix;
		IECore::InternedString m_propertyName;

		static QVariant iconGetter( const std::string &fileName, size_t &cost, const IECore::Canceller *canceller )
		{
			const char *s = getenv( "GAFFERUI_IMAGE_PATHS" );
			IECore::SearchPath sp( s ? s : "" );

			boost::filesystem::path path = sp.find( fileName );
			if( path.empty() )
			{
				IECore::msg( IECore::Msg::Warning, "PathListingWidget", boost::str( boost::format( "Could not find file \"%s\"" ) % fileName ) );
				return QVariant();
			}

			cost = 1;
			return QPixmap( QString( path.string().c_str() ) );
		}

		typedef IECorePreview::LRUCache<std::string, QVariant> IconCache;
		static IconCache g_iconCache;

};

IconColumn::IconCache IconColumn::g_iconCache( IconColumn::iconGetter, 10000 );

IE_CORE_DECLAREPTR( IconColumn )

class FileIconColumn : public Column
{

	public :

		IE_CORE_DECLAREMEMBERPTR( FileIconColumn )

		FileIconColumn()
			:	m_label( "Type" )
		{
		}

		QVariant data( const Path *path, int role = Qt::DisplayRole ) const override
		{
			if( role == Qt::DecorationRole )
			{
				std::string s = path->string();

				if( const FileSystemPath *fileSystemPath = IECore::runTimeCast<const FileSystemPath>( path ) )
				{
					if( fileSystemPath->getIncludeSequences() )
					{
						IECore::FileSequencePtr seq = fileSystemPath->fileSequence();
						if( seq )
						{
							std::vector<IECore::FrameList::Frame> frames;
							seq->getFrameList()->asList( frames );
							s = seq->fileNameForFrame( *frames.begin() );
						}
					}
				}

				QString qs( s.c_str() );
				return m_iconProvider.icon( QFileInfo( qs ) );
			}
			return QVariant();
		}

		QVariant headerData( int role = Qt::DisplayRole ) const override
		{
			if( role == Qt::DisplayRole )
			{
				return m_label;
			}
			return QVariant();
		}

	private :

		QVariant m_label;
		QFileIconProvider m_iconProvider;

};

IE_CORE_DECLAREPTR( FileIconColumn )

// A QAbstractItemModel for the navigation of Gaffer::Paths.
// This allows us to view Paths in QTreeViews. This forms part
// of the internal implementation of PathListingWidget, the rest
// of which is implemented in Python.
class PathModel : public QAbstractItemModel
{

		// Typically the Q_OBJECT macro would be added here,
		// but since we're not adding signals, slots or properties
		// to our class, it seems we don't need it. Omitting
		// it simplifies the build process, because otherwise we
		// would need to run things through the Qt meta object
		// compiler (moc).

	public :

		PathModel( QObject *parent = nullptr )
			:	QAbstractItemModel( parent ),
				m_rootItem( new Item( nullptr, nullptr ) ),
				m_flat( true ),
				m_sortColumn( -1 ),
				m_sortOrder( Qt::AscendingOrder )
		{
		}

		///////////////////////////////////////////////////////////////////
		// Our methods - these don't mean anything to Qt
		///////////////////////////////////////////////////////////////////

		void setColumns( const std::vector<ColumnPtr> columns )
		{
			/// \todo Maintain persistent indices etc
			/// using `m_rootItem->update()`.
			beginResetModel();
			m_columns = columns;
			m_rootItem = new Item( getRoot(), nullptr );
			endResetModel();
		}

		const std::vector<ColumnPtr> &getColumns() const
		{
			return m_columns;
		}

		Path *getRoot()
		{
			return m_rootItem->path();
		}

		void setRoot( PathPtr root )
		{
			m_rootItem->update( root, this );
		}

		void setFlat( bool flat )
		{
			if( flat == m_flat )
			{
				return;
			}

			beginResetModel();
			m_flat = flat;
			endResetModel();
		}

		bool getFlat() const
		{
			return m_flat;
		}

		void attachTester()
		{
			if( !m_tester )
			{
				m_tester = std::make_unique<QAbstractItemModelTester>(
					this,
					// Outputs messages that are turned into test failures by
					// the handler installed by `GafferUI.TestCase.setUp()`.
					QAbstractItemModelTester::FailureReportingMode::Warning
				);
			}
		}

		Path *pathForIndex( const QModelIndex &index )
		{
			if( !index.isValid() )
			{
				return nullptr;
			}
			return static_cast<Item *>( index.internalPointer() )->path();
		}

		QModelIndex indexForPath( const std::vector<IECore::InternedString> &path )
		{
			const Path *rootPath = m_rootItem->path();

			if( !rootPath )
			{
				return QModelIndex();
			}

			if( path.size() <= rootPath->names().size() )
			{
				return QModelIndex();
			}

			if( !equal( rootPath->names().begin(), rootPath->names().end(), path.begin() ) )
			{
				return QModelIndex();
			}

			QModelIndex result;
			Item *item = m_rootItem.get();
			for( size_t i = rootPath->names().size(); i < path.size(); ++i )
			{
				bool foundNextItem = false;
				const Item::ChildContainer &childItems = item->childItems( this );
				for( auto it = childItems.begin(), eIt = childItems.end(); it != eIt; ++it )
				{
					if( (*it)->path()->names()[i] == path[i] )
					{
						result = index( it - childItems.begin(), 0, result );
						item = it->get();
						foundNextItem = true;
						break;
					}
				}
				if( !foundNextItem )
				{
					return QModelIndex();
				}
			}

			return result;
		}

		QModelIndex indexForPath( const Path *path )
		{
			return indexForPath( path->names() );
		}

		std::vector<QModelIndex> indicesForPaths( const IECore::PathMatcher &paths )
		{
			std::vector<QModelIndex> result;
			const Path *rootPath = m_rootItem->path();
			if( !rootPath )
			{
				return result;
			}

			indicesForPathsWalk( m_rootItem.get(), QModelIndex(), paths, result );
			return result;
		}

		///////////////////////////////////////////////////////////////////
		// QAbstractItemModel implementation - this is what Qt cares about
		///////////////////////////////////////////////////////////////////

		QVariant data( const QModelIndex &index, int role ) const override
		{
			if( !index.isValid() )
			{
				return QVariant();
			}

			Item *item = static_cast<Item *>( index.internalPointer() );
			return item->data( index.column(), role, this );
		}

		QVariant headerData( int section, Qt::Orientation orientation, int role = Qt::DisplayRole ) const override
		{
			if( orientation != Qt::Horizontal )
			{
				return QVariant();
			}
			return m_columns[section]->headerData( role );
		}

		QModelIndex index( int row, int column, const QModelIndex &parentIndex = QModelIndex() ) const override
		{
			Item *parentItem = parentIndex.isValid() ? static_cast<Item *>( parentIndex.internalPointer() ) : m_rootItem.get();

			if( row >=0 and row < (int)parentItem->childItems( this ).size() and column >=0 and column < (int)m_columns.size() )
			{
				return createIndex( row, column, parentItem->childItems( this )[row].get() );
			}
			else
			{
				return QModelIndex();
			}
		}

		QModelIndex parent( const QModelIndex &index ) const override
		{
			if( !index.isValid() )
			{
				return QModelIndex();
			}

			Item *item = static_cast<Item *>( index.internalPointer() );
			if( !item || item->parent() == m_rootItem )
			{
				return QModelIndex();
			}

			return createIndex( item->parent()->row(), 0, item->parent() );
		}

		int rowCount( const QModelIndex &parentIndex = QModelIndex() ) const override
		{
			Item *parentItem;
			if( parentIndex.isValid() )
			{
				// Parent is not the root item.
				if( m_flat || parentIndex.column() != 0 )
				{
					return 0;
				}
				parentItem = static_cast<Item *>( parentIndex.internalPointer() );
			}
			else
			{
				parentItem = m_rootItem.get();
			}
			return parentItem->childItems( this ).size();
		}

		int columnCount( const QModelIndex &parent = QModelIndex() ) const override
		{
			return m_columns.size();
		}

		// Although this method sounds like it means "take what you've got and
		// sort it right now", it seems really to also mean "and remember that
		// this is how you should sort all other stuff you might generate later".
		// So that's what we do. We also use a column of < 0 to say "turn off
		// sorting".
		void sort( int column, Qt::SortOrder order = Qt::AscendingOrder ) override
		{
			if( m_sortColumn == column && m_sortOrder == order )
			{
				return;
			}

			m_sortColumn = column;
			m_sortOrder = order;

			m_rootItem->update( m_rootItem->path(), this );
		}

	private :

		// A single item in the PathModel - stores a path and caches
		// data extracted from it to provide the model content.
		struct Item : public IECore::RefCounted
		{

			Item( Gaffer::PathPtr path, Item *parent )
				:	m_path( path ),
					m_parent( parent ),
					m_row( -1 ), // Assigned true value in `updateChildItems()`
					m_dataState( State::Unrequested ),
					m_childItemsState( State::Unrequested )
			{
			}

			IE_CORE_DECLAREMEMBERPTR( Item )

			void update( const Gaffer::PathPtr &path, PathModel *model )
			{
				// This is just intended to be called on the root item by the
				// PathModel when the path changes.
				assert( !m_parent );
				m_path = path;
				updateWalk( model );
			}

			Gaffer::Path *path()
			{
				return m_path.get();
			}

			Item *parent()
			{
				return m_parent;
			}

			int row()
			{
				return m_row;
			}

			// Returns the data for the specified column and role, using the provided
			// Columns to generate it as necessary. The Item is responsible for caching
			// the results of these queries internally.
			QVariant data( int column, int role, const PathModel *model )
			{
				// We generate data for all columns and roles at once, on the
				// assumption that access to one is likely to indicate upcoming
				// accesses to the others.
				//
				// Note : `data()` is called from public query methods of the
				// PathModel. We don't call `updateData()` here if
				// `m_childItemsState == Dirty` because we can't modify the
				// model from within a query function.

				if( m_dataState == State::Unrequested )
				{
					m_dataState = State::Requested;
					updateData( const_cast<PathModel *>( model ) );
				}

				switch( role )
				{
					case Qt::DisplayRole :
						return m_displayData[column];
					case Qt::DecorationRole :
						return m_decorationData[column];
					default :
						return QVariant();
				}
			}

			using ChildContainer = std::vector<Ptr>;

			ChildContainer &childItems( const PathModel *model )
			{
				// Note : `childItems()` is called from public query methods of
				// the PathModel. We don't call `updateChildItems()` here
				// if `m_childItemsState == Dirty` because we can't modify the
				// model from within a query function.
				if( m_childItemsState == State::Unrequested )
				{
					m_childItemsState = State::Requested;
					updateChildItems( const_cast<PathModel *>( model ) );
				}
				return m_childItems;
			}

			private :

				void updateWalk( PathModel *model )
				{
					if( m_dataState == State::Clean )
					{
						m_dataState = State::Dirty;
					}
					if( m_childItemsState == State::Clean )
					{
						m_childItemsState = State::Dirty;
					}
					updateData( model );
					updateChildItems( model );
					for( const auto &child : m_childItems )
					{
						child->updateWalk( model );
					}
				}

				void updateData( PathModel *model )
				{
					if( m_dataState == State::Clean || m_dataState == State::Unrequested )
					{
						return;
					}

					std::vector<QVariant> newDisplayData;
					std::vector<QVariant> newDecorationData;

					newDisplayData.reserve( model->m_columns.size() );
					newDecorationData.reserve( model->m_columns.size() );

					for( int i = 0, e = model->m_columns.size(); i < e; ++i )
					{
						QVariant displayData;
						QVariant decorationData;
						try
						{
							displayData = model->m_columns[i]->data( m_path.get(), Qt::DisplayRole );
							decorationData = model->m_columns[i]->data( m_path.get(), Qt::DecorationRole );
						}
						catch( const std::exception &e )
						{
							// Qt doesn't use exceptions for error handling,
							// so we must suppress them.
							IECore::msg( IECore::Msg::Warning, "PathListingWidget", e.what() );
						}
						catch( ... )
						{
							IECore::msg( IECore::Msg::Warning, "PathListingWidget", "Unknown error" );
						}

						newDisplayData.push_back( displayData );
						newDecorationData.push_back( decorationData );
					}

					if( newDisplayData != m_displayData || newDecorationData != m_decorationData )
					{
						m_displayData.swap( newDisplayData );
						m_decorationData.swap( newDecorationData );
						if( m_dataState != State::Requested )
						{
							model->dataChanged( model->createIndex( m_row, 0, this ), model->createIndex( m_row, model->m_columns.size() - 1, this ) );
						}
					}

					m_dataState = State::Clean;
				}

				void updateChildItems( PathModel *model )
				{
					if( m_childItemsState == State::Unrequested || m_childItemsState == State::Clean )
					{
						return;
					}

					// Construct a new ChildContainer to replace our previous children.
					// Where possible we reuse existing children instead of creating new
					// ones.

					ChildContainer newChildItems;
					if( m_path )
					{
						std::vector<Gaffer::PathPtr> children;
						try
						{
							m_path->children( children );
						}
						catch( const std::exception &e )
						{
							IECore::msg( IECore::Msg::Error, "PathListingWidget", e.what() );
						}

						std::unordered_map<IECore::InternedString, Item *> oldChildMap;
						for( const auto &oldChild : m_childItems )
						{
							oldChildMap[oldChild->path()->names().back()] = oldChild.get();
						}

						for( auto it = children.begin(), eIt = children.end(); it != eIt; ++it )
						{
							auto oldIt = oldChildMap.find( (*it)->names().back() );
							if( oldIt != oldChildMap.end() )
							{
								// Reuse previous item.
								Ptr itemToReuse = oldIt->second;
								itemToReuse->m_path = *it;
								newChildItems.push_back( itemToReuse );
							}
							else
							{
								// Make new item.
								newChildItems.push_back( new Item( *it, this ) );
							}
						}
					}

					// Sort the new container if necessary.

					if( model->m_sortColumn >= 0 && model->m_sortColumn < (int)model->m_columns.size() )
					{
						for( const auto &childItem : newChildItems )
						{
							if( childItem->m_dataState == State::Unrequested )
							{
								childItem->m_dataState = State::Requested;
							}
							childItem->updateData( model );
						}
						std::sort(
							newChildItems.begin(), newChildItems.end(),
							[model] ( const Item::Ptr &left, const Item::Ptr &right ) {
								const QVariant &l = left->m_displayData[model->m_sortColumn];
								const QVariant &r = right->m_displayData[model->m_sortColumn];
								return model->m_sortOrder == Qt::AscendingOrder ? variantLess( l, r ) : variantLess( r, l );
							}
						);
					}

					// Early out if nothing has changed.

					if( newChildItems == m_childItems )
					{
						m_childItemsState = State::Clean;
						return;
					}

					// If we had children before, figure out the mapping from old to new,
					// so we can tell Qt about it. This is necessary so that persistent
					// indices used to represent selection and expansion remain valid.

					QModelIndexList changedPersistentIndexesFrom, changedPersistentIndexesTo;

					std::unordered_map<IECore::InternedString, size_t> newChildMap;
					for( size_t i = 0; i < newChildItems.size(); ++i )
					{
						newChildMap[newChildItems[i]->path()->names().back()] = i;
					}

					for( const auto &oldChild : m_childItems )
					{
						auto nIt = newChildMap.find( oldChild->m_path->names().back() );
						if( nIt != newChildMap.end() )
						{
							const int toRow = nIt->second;
							for( int c = 0, ce = model->getColumns().size(); c < ce; ++c )
							{
								changedPersistentIndexesFrom.append( model->createIndex( oldChild->row(), c, oldChild.get() ) );
								changedPersistentIndexesTo.append( model->createIndex( toRow, c, newChildItems[toRow].get() ) );
							}
						}
						else
						{
							oldChild->invalidateIndexes( model, changedPersistentIndexesFrom, changedPersistentIndexesTo );
						}
					}

					// Apply the update. We have to mark ourselves clean _before_
					// changing layout, to avoid recursion when Qt responds to
					// `layoutAboutToBeChanged()`.

					const bool emitLayoutChanged = m_childItemsState != State::Requested;
					m_childItemsState = State::Clean;

					if( emitLayoutChanged )
					{
						model->layoutAboutToBeChanged( { model->createIndex( row(), 0, this ) } );
					}

					m_childItems.swap( newChildItems );
					for( size_t i = 0; i < m_childItems.size(); ++i )
					{
						m_childItems[i]->m_row = i;
					}

					if( emitLayoutChanged )
					{
						model->changePersistentIndexList( changedPersistentIndexesFrom, changedPersistentIndexesTo );
						model->layoutChanged();
					}
				}

				void invalidateIndexes( PathModel *model, QModelIndexList &from, QModelIndexList &to )
				{
					for( int c = 0, ce = model->getColumns().size(); c < ce; ++c )
					{
						from.append( model->createIndex( m_row, c, this ) );
						to.append( QModelIndex() );
					}
					for( const auto &child : m_childItems )
					{
						child->invalidateIndexes( model, from, to );
					}
				}

				Gaffer::PathPtr m_path;
				Item *m_parent;
				int m_row;

				// State transitions :
				//
				// - Unrequested->Requested : When first queried.
				// - Requested->Clean : When first updated.
				// - Clean->Dirty : When path changes.
				// - Dirty->Clean : On all subsequent updates.
				enum class State
				{
					// Initial state. Not yet requested by clients
					// of the model, therefore not yet computed, and not
					// in need of consideration during recursive updates.
					Unrequested,
					// Has just been requested for the first time. Needs
					// to be updated, but there is no need to emit change
					// signals for the first update.
					Requested,
					// Computed and up to date.
					Clean,
					// Stale data that needs recomputing.
					Dirty
				};

				State m_dataState;
				std::vector<QVariant> m_displayData;
				std::vector<QVariant> m_decorationData;

				State m_childItemsState;
				std::vector<Ptr> m_childItems;

		};

		void indicesForPathsWalk( Item *item, const QModelIndex &itemIndex, const IECore::PathMatcher &paths, std::vector<QModelIndex> &indices )
		{
			/// \todo Using `match()` here isn't right, because we want to
			/// treat wildcards in the selection verbatim rather than perform
			/// matching with them. We should use `find()`, but that doesn't
			/// provide a convenient way of checking for descendant matches.
			const unsigned match = paths.match( item->path()->names() );
			if( match & IECore::PathMatcher::ExactMatch )
			{
				indices.push_back( itemIndex );
			}

			if( !(match & IECore::PathMatcher::DescendantMatch) )
			{
				return;
			}

			size_t row = 0;
			for( const auto &childItem : item->childItems( this ) )
			{
				const QModelIndex childIndex = index( row++, 0, itemIndex );
				indicesForPathsWalk( childItem.get(), childIndex, paths, indices );
			}
		}

		Item::Ptr m_rootItem;
		bool m_flat;
		std::vector<ColumnPtr> m_columns;
		int m_sortColumn;
		Qt::SortOrder m_sortOrder;
		std::unique_ptr<QAbstractItemModelTester> m_tester;

};

void setColumns( uint64_t treeViewAddress, object pythonColumns )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	std::vector<ColumnPtr> columns;
	boost::python::container_utils::extend_container( columns, pythonColumns );
	model->setColumns( columns );
}

list getColumns( uint64_t treeViewAddress )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	const std::vector<ColumnPtr> &columns = model->getColumns();
	list result;
	for( std::vector<ColumnPtr>::const_iterator it = columns.begin(), eIt = columns.end(); it != eIt; ++it )
	{
		result.append( *it );
	}
	return result;
}

void updateModel( uint64_t treeViewAddress, Gaffer::PathPtr path )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	if( !model )
	{
		model = new PathModel( treeView );
		treeView->setModel( model );
	}
	model->setRoot( path );
}

void setFlat( uint64_t treeViewAddress, bool flat )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	model->setFlat( flat );
}

bool getFlat( uint64_t treeViewAddress )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	return model->getFlat();
}

void setExpansion( uint64_t treeViewAddress, const IECore::PathMatcher &paths )
{
	IECorePython::ScopedGILRelease gilRelease;

	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	for( const auto &modelIndex : model->indicesForPaths( paths ) )
	{
		treeView->setExpanded( modelIndex, true );
	}
}

void getExpansionWalk( QTreeView *treeView, PathModel *model, QModelIndex index, IECore::PathMatcher &expanded )
{
	for( int i = 0, e = model->rowCount( index ); i < e; ++i )
	{
		QModelIndex childIndex = model->index( i, 0, index );
		if( treeView->isExpanded( childIndex ) )
		{
			expanded.addPath( model->pathForIndex( childIndex )->names() );
			getExpansionWalk( treeView, model, childIndex, expanded );
		}
	}
}

IECore::PathMatcher getExpansion( uint64_t treeViewAddress )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );

	IECore::PathMatcher result;
	if( !model )
	{
		return result;
	}

	IECorePython::ScopedGILRelease gilRelease;
	getExpansionWalk( treeView, model, QModelIndex(), result );
	return result;
}

void propagateExpandedWalk( QTreeView *treeView, PathModel *model, QModelIndex index, bool expanded, int numLevels )
{
	for( int i = 0, e = model->rowCount( index ); i < e; ++i )
	{
		QModelIndex childIndex = model->index( i, 0, index );
		treeView->setExpanded( childIndex, expanded );
		if( numLevels - 1 > 0 )
		{
			propagateExpandedWalk( treeView, model, childIndex, expanded, numLevels - 1 );
		}
	}
}

void propagateExpanded( uint64_t treeViewAddress, uint64_t modelIndexAddress, bool expanded, int numLevels )
{
	IECorePython::ScopedGILRelease gilRelease;

	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	if( !model )
	{
		return;
	}

	QModelIndex *modelIndex = reinterpret_cast<QModelIndex *>( modelIndexAddress );
	propagateExpandedWalk( treeView, model, *modelIndex, expanded, numLevels );
}

void setSelection( uint64_t treeViewAddress, const IECore::PathMatcher &paths, bool scrollToFirst, bool expandNonLeaf )
{
	IECorePython::ScopedGILRelease gilRelease;

	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	if( !model )
	{
		return;
	}

	const std::vector<QModelIndex> indices = model->indicesForPaths( paths );
	if( treeView->selectionMode() != QAbstractItemView::ExtendedSelection && indices.size() > 1 )
	{
		throw IECore::InvalidArgumentException( "More than one path selected" );
	}

	QItemSelection itemSelection;
	for( const auto &modelIndex : indices )
	{
		if( !modelIndex.isValid() )
		{
			continue;
		}
		itemSelection.select( modelIndex, modelIndex.sibling( modelIndex.row(), model->columnCount() - 1 ) );
		if( expandNonLeaf && !model->pathForIndex( modelIndex )->isLeaf() )
		{
			treeView->setExpanded( modelIndex, true );
		}
	}

	QItemSelectionModel *selectionModel = treeView->selectionModel();
	selectionModel->select( itemSelection, QItemSelectionModel::Select );

	if( scrollToFirst && !indices.empty() )
	{
		treeView->scrollTo( indices[0], QTreeView::EnsureVisible );
		selectionModel->setCurrentIndex( indices[0], QItemSelectionModel::Current );
	}
}

IECore::PathMatcher getSelection( uint64_t treeViewAddress )
{
	IECorePython::ScopedGILRelease gilRelease;

	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );

	QModelIndexList selectedIndices = treeView->selectionModel()->selectedIndexes();
	IECore::PathMatcher result;
	for( const auto &index : selectedIndices )
	{
		result.addPath( model->pathForIndex( index )->names() );
	}
	return result;
}

PathPtr pathForIndex( uint64_t treeViewAddress, uint64_t modelIndexAddress )
{
	// put a GIL release here in case scene child name computations etc triggered by
	// this function end up calling into python:
	IECorePython::ScopedGILRelease r;
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	if( !model )
	{
		return nullptr;
	}

	QModelIndex *modelIndex = reinterpret_cast<QModelIndex *>( modelIndexAddress );
	return model->pathForIndex( *modelIndex );
}

void indexForPath( uint64_t treeViewAddress, const Path *path, uint64_t modelIndexAddress )
{
	// put a GIL release here in case scene child name computations etc triggered by
	// this function end up calling into python:
	IECorePython::ScopedGILRelease r;
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	QModelIndex *modelIndex = reinterpret_cast<QModelIndex *>( modelIndexAddress );
	*modelIndex = model->indexForPath( path );
}

list pathsForPathMatcher( uint64_t treeViewAddress, const IECore::PathMatcher &pathMatcher )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	if( !model )
	{
		return list();
	}

	std::vector<QModelIndex> indices;
	{
		IECorePython::ScopedGILRelease gilRelease;
		indices = model->indicesForPaths( pathMatcher );
	}

	list result;
	for( const auto &index : indices )
	{
		result.append( PathPtr( model->pathForIndex( index ) ) );
	}

	return result;
}

void attachTester( uint64_t treeViewAddress )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	model->attachTester();
}

} // namespace

void GafferUIModule::bindPathListingWidget()
{
	// Ideally we'd bind PathModel so it could be used in
	// the normal fashion from Python. But that would mean
	// using SIP or Shiboken to make bindings compatible
	// with PyQt or PySide. It would also mean each Gaffer
	// build would only be compatible with one or the other
	// of the Qt bindings, whereas we want a single build
	// to be compatible with either. We therefore simply
	// bind the minimum set of methods we need as free
	// functions and then use them from within PathListingWidget.py.

	def( "_pathListingWidgetSetColumns", &setColumns );
	def( "_pathListingWidgetGetColumns", &getColumns );
	def( "_pathListingWidgetUpdateModel", &updateModel );
	def( "_pathListingWidgetSetFlat", &setFlat );
	def( "_pathListingWidgetGetFlat", &getFlat );
	def( "_pathListingWidgetSetExpansion", &setExpansion );
	def( "_pathListingWidgetGetExpansion", &getExpansion );
	def( "_pathListingWidgetPropagateExpanded", &propagateExpanded );
	def( "_pathListingWidgetSetSelection", &setSelection );
	def( "_pathListingWidgetGetSelection", &getSelection );
	def( "_pathListingWidgetPathForIndex", &pathForIndex );
	def( "_pathListingWidgetIndexForPath", &indexForPath );
	def( "_pathListingWidgetPathsForPathMatcher", &pathsForPathMatcher );
	def( "_pathListingWidgetAttachTester", &attachTester );

	IECorePython::RefCountedClass<Column, IECore::RefCounted>( "_PathListingWidgetColumn" );

	IECorePython::RefCountedClass<StandardColumn, Column>( "_PathListingWidgetStandardColumn" )
		.def( init<const std::string &, IECore::InternedString>() )
	;

	IECorePython::RefCountedClass<IconColumn, Column>( "_PathListingWidgetIconColumn" )
		.def( init<const std::string &, const std::string &, IECore::InternedString>() )
	;

	IECorePython::RefCountedClass<FileIconColumn, Column>( "_PathListingWidgetFileIconColumn" )
		.def( init<>() )
	;
}
