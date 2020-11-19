```eval_rst
.. role:: raw-html(raw)
    :format: html
```

# Controls and Shortcuts #

The following is a list of input device controls and shortcuts for manipulating the Graph Editor, Viewer, and Python Editor.

> Tip :
> macOS users: replace <kbd>Ctrl</kbd> with <kbd>Command ⌘</kbd>.


## General ##

```eval_rst
===================================== =============================================
Action                                Control or shortcut
===================================== =============================================
New node graph                        :kbd:`Ctrl` + :kbd:`N`
Open node graph                       :kbd:`Ctrl` + :kbd:`O`
Save node graph                       :kbd:`Ctrl` + :kbd:`S`
Save node graph as                    :kbd:`Ctrl` + :kbd:`Shift` + :kbd:`S`
Undo                                  :kbd:`Ctrl` + :kbd:`Z`
Redo                                  :kbd:`Ctrl` + :kbd:`Shift` + :kbd:`Z`
Step one frame forward                :kbd:`→`
Step one frame backward               :kbd:`←`
Fullscreen mode                       :raw-html:`<kbd>&#96;</kbd>`
Hide tabs of current panel            :kbd:`Ctrl` + :kbd:`T`
===================================== =============================================
```

### Pinnable Editors and Inspectors ###

When editors are following another editor (linked), keybaord shortcuts will
affect the master editor.

```eval_rst
===================================== =============================================
Action                                Control or shortcut
===================================== =============================================
Pin the node selection                Hover cursor over editor, :kbd:`p`
Pin numeric bookmark 1-9              Hover cursor over editor, :kbd:`1` - :kbd:`9`
Follow to the node selection          Hover cursor over editor, :kbd:`u`
===================================== =============================================
```

## Graph Editor ##

> Note :
> For the following controls and shortcuts, the cursor must hover over the Graph Editor.


### Navigation ###

```eval_rst
===================================== =============================================
Action                                Control or shortcut
===================================== =============================================
Pan                                   :kbd:`Alt` + |M1| and drag
Zoom                                  :kbd:`Alt` + |M2| and drag
                                      
                                      or
                                      
                                      |MW|
Pan/Zoom, fine precision              Hold :kbd:`Shift` during action
Frame selected nodes                  :kbd:`F`
Enter `Box` node (subgraph)           :kbd:`↓`
Leave `Box` node (subgraph)           :kbd:`↑`
Search for nodes                      :kbd:`Ctrl` + :kbd:`F`
Frame to numeric bookmark             :kbd:`1` … :kbd:`9`
===================================== =============================================

.. |M1| image:: images/mouseLeftClick.png
    :alt: Left click
.. |M2| image:: images/mouseRightClick.png
    :alt: Right click
.. |M3| image:: images/mouseMiddleClick.png
    :alt: Middle click
.. |MW| image:: images/mouseWheelUpDown.png
    :alt: Mouse wheel
```


### Node creation ###

```eval_rst
===================================== =============================================
Action                                Control or shortcut
===================================== =============================================
Show node menu                        |M2|
                                      
                                      or
                                      
                                      :kbd:`Tab`
Insert `Dot` at connection            :kbd:`Ctrl` + |M1| connection
                                      
                                      or
                                      
                                      |M2| connection > *Insert Dot*
===================================== =============================================
```


### Node selection ###

```eval_rst
===================================== =============================================
Action                                Control or shortcut
===================================== =============================================
Select all                            :kbd:`Ctrl` + :kbd:`A`
Clear selection                       :kbd:`Ctrl` + :kbd:`Shift` + :kbd:`A`
Select node                           |M1|
Add node to selection                 :kbd:`Shift` + |M1|
Add/remove node from selection        :kbd:`Ctrl` + |M1|
Select nodes                          |M1| and drag marquee, then release
Add nodes                             :kbd:`Shift` + |M1| and drag marquee, then 
                                      release
Deselect nodes                        :kbd:`Ctrl` + |M1| and drag marquee, then
                                      release
Select upstream nodes                 :kbd:`Shift` + :kbd:`Alt` + |M1| node
Select downstream nodes               :kbd:`Ctrl` + :kbd:`Alt` + |M1| node
===================================== =============================================
```

### Node dispatch ###

> Note :
> For these dispatch-related shortcuts, the cursor does **not** need to hover over the Graph Editor.

```eval_rst
===================================== =============================================
Action                                Control or shortcut
===================================== =============================================
Dispatch selected node(s)             :kbd:`Ctrl` + :kbd:`E`
Redo last dispatch                    :kbd:`Ctrl` + :kbd:`R`
===================================== =============================================
```


### Node copying and deletion ###

> Tip :
> For a Box node to be disableable, it must first be [set up for pass-through](../../WorkingWithTheNodeGraph/BoxNode/index.html#setting-up-a-box-for-pass-through).

```eval_rst
===================================== =============================================
Action                                Control or shortcut
===================================== =============================================
Cut node(s)                           :kbd:`Ctrl` + :kbd:`X`
Copy node(s)                          :kbd:`Ctrl` + :kbd:`C`
Paste node(s)                         :kbd:`Ctrl` + :kbd:`V`
Delete node(s)                        :kbd:`Backspace`
                                      
                                      or
                                      
                                      :kbd:`Delete`
Enable/disable node(s)                :kbd:`D`
===================================== =============================================
```


### Node connections and layout ###

```eval_rst
===================================== =============================================
Action                                Control or shortcut
===================================== =============================================
Connect plug                          |M1| and drag plug to another plug
Disconnect plug                       |M1| and drag connection to background
Insert node onto connection           |M1| and drag node onto connection
Auto-arrange selected nodes           :kbd:`Ctrl` + :kbd:`L`
Duplicate outgoing connection         :kbd:`Shift`-|M1| and drag connection just 
                                      before in plug
===================================== =============================================
```


### Node bookmarks ###

```eval_rst
===================================== =============================================
Action                                Control or shortcut
===================================== =============================================
Bookmark node                         |M2| node > *Bookmark*
Connect to bookmarked node            |M2| plug > *Connect Bookmark* > select
                                      node
Jump to bookmarked node               Hover cursor over editor, :kbd:`Ctrl` +
                                      :kbd:`B` > select bookmarked node
                                      
                                      or
                                      
                                      |M1| |focusMenu|, select *Bookmark* > ...
Assign numeric bookmark               :kbd:`Ctrl` + :kbd:`1` … :kbd:`9`
Remove numeric bookmark               :kbd:`Ctrl` + :kbd:`0`
===================================== =============================================

.. |focusMenu| image:: images/editorFocusMenuNodeSelection.png
    :alt: Editor focus menu
```


## Node Editor ##


### Numeric plugs ###

```eval_rst
============================================== ===============================================
Action                                         Control or shorcut
============================================== ===============================================
Increment/decrement value, specific precision  Position cursor next to a number position in 
                                               plug field, then hit :kbd:`↑` / :kbd:`↓`
Scrub value, coarse precision                  :kbd:`Ctrl` + |M1| and drag the field
                                               left/right
Scrub value, fine precision                    :kbd:`Ctrl` + :kbd:`Shift` + |M1| and drag
                                               the field left/right
Gang plugs together                            :kbd:`Ctrl` + :kbd:`G`
============================================== ===============================================
```

> Tip :
> Numeric fields support basic mathematical operators to adjust their values. For example, appending `+1` to a plug with an existing value of `2`, will set it to `3`. You can use `+`, `-`, `/`, `*` and `%` to modify the existing value.


### Path plugs ###

```eval_rst
==================================== ================================================
Action                               Control or shorcut
==================================== ================================================
Autocomplete path component          :kbd:`Tab`
Path-level contents menu             Select path component

                                     or
                                     
                                     Position text cursor in path component, then hit
                                     :kbd:`↓`
Path hierarchy menu                  Select all
==================================== ================================================
```


## Viewer ##

> Note :
> For the following controls and shortcuts, the cursor must hover over the Viewer.


### General controls ###

```eval_rst
===================================== =============================================
Action                                Control or shortcut
===================================== =============================================
Pan                                   :kbd:`Alt` + |M1| and drag
Zoom/dolly                            :kbd:`Alt` + |M2| and drag
                                      
                                      or
                                      
                                      |MW|
Pan/Zoom, fine precision              Hold :kbd:`Shift` during action
Frame view to contents                :kbd:`F`
Pause processing                      :kbd:`Escape`
Selection Tool                        :kbd:`Q`
Translate Tool                        :kbd:`W`
Rotate Tool                           :kbd:`E`
Scale Tool                            :kbd:`R`
Camera Tool                           :kbd:`T`
Crop Window Tool                      :kbd:`C`
Pin to numeric bookmark               :kbd:`1` … :kbd:`9`
===================================== =============================================
```

### 3D scenes ###

```eval_rst
====================================================== =====================================
Action                                                 Control or shortcut
====================================================== =====================================
Tumble                                                 :kbd:`Alt` + |M1| and drag
Tumble, fine precision                                 Hold :kbd:`Shift` during action
Select objects                                         |M1| and drag marquee, then release
Add/remove object from selection                       :kbd:`Ctrl` + |M1|
Add objects to selection                               :kbd:`Shift` + |M1| and drag marquee, then
                                                       release
Deselect objects                                       :kbd:`Ctrl` + |M1| and drag marquee, then
                                                       release
Expand selection                                       :kbd:`↓`
Fully expand selection                                 :kbd:`Shift` + :kbd:`↓`
Collapse selection                                     :kbd:`↑`
Edit source node of selection                          :kbd:`Alt` + :kbd:`E`
Edit tweaks node for selection                         :kbd:`Alt` + :kbd:`Shift` + :kbd:`E`
Fit clipping planes to scene                           |M2| > *Clipping Planes* > *Fit
                                                       To Scene*
Fit clipping planes to selection                       |M2| > *Clipping Planes* > *Fit 
                                                       To Selection*

                                                       or

                                                       :kbd:`Ctrl` + :kbd:`K`
Frame view, and fit clipping planes to scene/selection :kbd:`Ctrl` + :kbd:`F`
Reset clipping planes                                  |M2| > *Clipping Planes* > 
                                                       *Default*
Toggle Inspector                                       :kbd:`I`
====================================================== =====================================
```

### Transform tools ###

> Note :
> For the following controls and shortcuts, a Transform Tool must be active.

```eval_rst
==================================================== =============================================
Action                                               Control or shortcut
==================================================== =============================================
Increase manipulator size                            :kbd:`+`
Decrease manipulator size                            :kbd:`-`
Add animation key to transform of selected object(s) :kbd:`S`
Adjust, fine precision                               Hold :kbd:`Shift` during action
Adjust, snapping to rounded increments               Hold :kbd:`Ctrl` + during action
Target mode (Translate and Rotate only)              Hold :kbd:`v`
==================================================== =============================================
```


### 2D images ###

```eval_rst
===================================== =============================================
Action                                Control or shortcut
===================================== =============================================
Isolate red channel                   :kbd:`R`
Isolate green channel                 :kbd:`G`
Isolate blue channel                  :kbd:`B`
Isolate alpha channel                 :kbd:`A`
Center image at 1:1 scale             :kbd:`Home`
Next Catalogue image                  :kbd:`↓`
Previous Catalogue image              :kbd:`↑`
Duplicate current Catalogue image     :kbd:`Ctrl` + `:kbd:`D`
===================================== =============================================
```


### Crop window tool ###

```eval_rst
===================================== =============================================
Action                                Control or shortcut
===================================== =============================================
Draw new region anywhere              :kbd:`Shift` + click and drag
===================================== =============================================
```


## Hierarchy View ##

```eval_rst
==================================== ================================================
Action                               Control or shorcut
==================================== ================================================
Copy selected paths                  :kbd:`Ctrl` + :kbd:`C`
==================================== ================================================
```


## Python Editor ##


### Text entry ###

> Note :
> When using the following drag and drop controls and shortcuts, drop the UI element onto the input field of the Python Editor.

```eval_rst
================================================== ================================================
Action                                             Control or shortcut
================================================== ================================================
Drop node into *Python Editor*                     |M3| and drag node from Node Graph
Drop plug into *Python Editor*                     |M3| and drag plug from Node Graph
                                      
                                                   or
                                      
                                                   |M1| and drag plug label from Node Editor
Drop plug value into Python Editor                 :kbd:`Shift` + |M1| and drag plug label from
                                                   Node Editor
Drop color value into Python Editor                |M1| and drag a pixel from Viewer
Drop scene location path(s) into Python Editor     |M1| and drag selection from Viewer or
                                                   Hierarchy View
================================================== ================================================
```


### Execution ###

> Note :
> For the following controls and shortcuts, the input field of the Python Editor must be in focus.

```eval_rst
===================================== ===================================================
Action                                Control or shortcut
===================================== ===================================================
Execute and clear                     :kbd:`Ctrl` + :kbd:`Enter`
Execute selection                     Select code, then hit :kbd:`Ctrl` + :kbd:`Enter`
===================================== ===================================================
```


## Animation Editor ##

> Note :
> For the following controls and shortcuts, the cursor must hover over the Animation Editor.

```eval_rst
=============================================== =============================================
Action                                          Control or shortcut
=============================================== =============================================
Pan                                             :kbd:`Alt` + |M1| and drag
Zoom                                            :kbd:`Alt` + |M2| and drag

                                                or
                                                
                                                |MW|
Zoom x/y axes independently                     Hold :kbd:`Ctrl` during action
Pan/Zoom, fine precision                        Hold :kbd:`Shift` during action
Adjust frame range                              :kbd:`Alt` + :kbd:`Shift` + |M2| and
                                                drag left/right
Adjust key value range                          :kbd:`Alt` + :kbd:`Shift` + |M2| and
                                                drag up/down
Frame all curves (no selection)                 :kbd:`F`
Frame selected key(s)                           :kbd:`F`
Add key to a curve                              :kbd:`Ctrl` + |M1|
Add key to all selected curves at current frame :kbd:`I`
Delete selected key(s)                          :kbd:`Delete`

                                                or
                                                
                                                :kbd:`Backspace`
Adjust selected key(s)                          |M1| and drag
Adjust frame(s) of selected key(s)              :kbd:`Shift` + |M1| and drag left/right
Adjust value(s) of selected key(s)              :kbd:`Shift` + |M1| and drag up/down
=============================================== =============================================
```


## Interactive Render Log ##

```eval_rst
==================================== ================================================
Action                               Control or shorcut
==================================== ================================================
Next message of level                :kbd:`e`, :kbd:`w`, :kbd:`i`, :kbd:`d`
Previous message of level            :kbd:`Shift` + :kbd:`e`, :kbd:`w`, :kbd:`i`, :kbd:`d`
Search                               :kbd:`Ctrl` + :kbd:`F`
  Next match (search field focus)    :kbd:`Enter`
  Next match (log focus)             :kbd:`N`
  Previous match (log focus)         :kbd:`P`
Scroll to bottom                     :kbd:`B`
==================================== ================================================
```

## Spreadsheet ##

```eval_rst
================================================== ================================================================
Action                                             Control or shorcut
================================================== ================================================================
Toggle/edit selected cells                         :kbd:`Return` or |M1| |M1|
Toggle Enabled state of selected cells             :kbd:`D`
Copy/Paste selected cells or rows                  :kbd:`Ctrl` + :kbd:`C`/:kbd:`V`
Move cell selection                                :kbd:`Up`, :kbd:`Down`, :kbd:`Left`, :kbd:`Right`
Extend cell selection                              :kbd:`Shift` + :kbd:`Up`, :kbd:`Down`, :kbd:`Left`, :kbd:`Right`
Move keyboard focus                                :kbd:`Ctrl` + :kbd:`Up`, :kbd:`Down`, :kbd:`Left`, :kbd:`Right`
Toggle selection state of cell with keyboard focus :kbd:`Space`
================================================== ================================================================
```
