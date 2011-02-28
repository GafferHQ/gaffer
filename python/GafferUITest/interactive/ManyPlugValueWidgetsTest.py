import IECore
import Gaffer
import GafferUI
import IECore
import gtk

numX = 15
numY = 30
## \todo Rejig this to remove all gtk specific code, and use only GafferUI classes instead

window = gtk.Window( gtk.WINDOW_TOPLEVEL )
window.set_size_request( 200, 300 )
window.set_title( "Many plug widgets test" )
window.connect( "delete_event", gtk.main_quit )
table = gtk.Table( numY, numX, True )
window.add( table )

node = Gaffer.Node()
node.floatPlug = Gaffer.FloatPlug()

cells = []
for x in range( 0, numX ) :
	for y in range( 0, numY ) :
		w = GafferUI.PlugValueWidget.create( node.floatPlug )
		table.attach( w.gtkWidget(), x, x+1, y, y+1 )
		cells.append( w )
		
window.show_all()
GafferUI.EventLoop.start()
