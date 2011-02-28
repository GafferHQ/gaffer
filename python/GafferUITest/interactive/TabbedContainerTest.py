import IECore
import Gaffer
import GafferUI
import gtk

window = GafferUI.Window( "Tabbed container test" )
window.gtkWidget().connect( "delete_event", gtk.main_quit )

t = GafferUI.TabbedContainer()
n = Gaffer.AddNode()

t.append( GafferUI.PlugWidget( n.op1 ) )
t.append( GafferUI.PlugWidget( n.op1 ) )

t.setLabel( t[0], "one" )
t.setLabel( t[1], "two" )

## \todo Need to find why we have to call setChild() last
window.setChild( t )

GafferUI.EventLoop.start()
