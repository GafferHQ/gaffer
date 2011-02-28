import IECore
import Gaffer
import GafferUI
import IECore
import gtk

## \todo Rejig this to remove all gtk specific code, and use only GafferUI classes instead

window = GafferUI.Window( "Plug widget test")
column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
column.show()
window.setChild( column )

node = Gaffer.Node()
node.floatPlug = Gaffer.FloatPlug()
node.intPlug = Gaffer.IntPlug()
node.stringPlug = Gaffer.StringPlug()

column.append( GafferUI.PlugWidget( node.floatPlug, "Float", "I am a description" ) )
column.append( GafferUI.PlugWidget( node.intPlug, "Int", "I am a description too" ) )
column.append( GafferUI.PlugWidget( node.stringPlug ) )
column.append( GafferUI.PlugWidget( GafferUI.FileNamePlugValueWidget( node.stringPlug ) ) )

window.show()

GafferUI.EventLoop.start()
