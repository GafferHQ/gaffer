import IECore
import Gaffer
import GafferUI
import IECore
import gtk

## \todo Rejig this to remove all gtk specific code, and use only GafferUI classes instead

window = GafferUI.Window( "Plug value widget test")
column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )

node = Gaffer.Node()
node.floatPlug = Gaffer.FloatPlug()
node.intPlug = Gaffer.IntPlug()
node.stringPlug = Gaffer.StringPlug()

column.append( GafferUI.NumericPlugValueWidget( node.floatPlug ) )
column.append( GafferUI.PlugValueWidget.create( node.floatPlug ) )
column.append( GafferUI.NumericPlugValueWidget( node.intPlug ) )
column.append( GafferUI.PlugValueWidget.create( node.intPlug ) )
column.append( GafferUI.PlugValueWidget.create( node.stringPlug ) )
column.append( GafferUI.FileNamePlugValueWidget( node.stringPlug ) )

window.gtkWidget().show_all()
window.setChild( column )

GafferUI.EventLoop.start()
