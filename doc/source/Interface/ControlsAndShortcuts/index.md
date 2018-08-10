# Controls and Shortcuts #

The following is a list of input device controls and shortcuts for manipulating the _Node Graph_, _Viewer_, and _Script Editor_.


## _Graph Editor_ ##

> Note :
> For the following controls and shortcuts, the cursor must hover over the _Graph Editor_.


### Navigation ###

```eval_rst
===================================== =============================================
Action			                      Control or Shortcut
===================================== =============================================
Pan                                   :kbd:`Alt` + click and drag
Zoom                                  :kbd:`Alt` + right-click and drag
                                      
                                      or
                                      
                                      Mouse wheel up/down
Frame selected nodes                  :kbd:`F`
Enter `Box` node (subgraph)	          :kbd:`↓`
Leave `Box` node (subgraph)           :kbd:`↑`
Search for nodes                      :kbd:`Ctrl` + :kbd:`F`
===================================== =============================================
```


### Node Creation ###

<!-- TODO: Add note explaining that Box nodes and custom-authored shaders don't support enabling/disabling without some additional setup. -->

```eval_rst
===================================== =============================================
Action			                      Control or Shortcut
===================================== =============================================
Show node menu                        Right-click
                                      
                                      or
                                      
                                      :kbd:`Tab`
Insert `Dot` at connection            :kbd:`Ctrl` + click connection
                                      
                                      or
                                      
                                      Right-click connection > *Insert Dot*
===================================== =============================================
```


### Node Selection ###

```eval_rst
===================================== =============================================
Action			                      Control or Shortcut
===================================== =============================================
Select all                            :kbd:`Ctrl` + :kbd:`A`
Clear selection                       :kbd:`Ctrl` + :kbd:`Shift` + :kbd:`A`
Select node                           Click
Add/remove node from selection        :kbd:`Shift` + click
Select nodes                          Click and drag marquee, then release
Add nodes                             :kbd:`Shift` + click and drag marquee, then 
                                      release
Select upstream nodes                 :kbd:`Shift` + :kbd:`Alt` + click node
Select downstream nodes               :kbd:`Shift` + :kbd:`Ctrl` + click node
===================================== =============================================
```


### Node Copying and Deletion ###

<!-- TODO: Once http://shotgun/detail/Ticket/12251 is resolved, add note explaining that Box nodes and custom-authored shaders don't support enabling/disabling without some additional setup. -->

```eval_rst
===================================== =============================================
Action			                      Control or Shortcut
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


### Node Connections and Layout ###

```eval_rst
===================================== =============================================
Action			                      Control or Shortcut
===================================== =============================================
Connect plug                          Click and drag plug to another plug
Disconnect plug                       Click and drag connection to background
Insert node at connection             Drag node onto connection
Auto-arrange selected nodes           :kbd:`Ctrl` + :kbd:`L`
===================================== =============================================
```


### Node Bookmarks ###

```eval_rst
===================================== =============================================
Action			                      Control or Shortcut
===================================== =============================================
Bookmark node                         Right-click node > *Bookmark*
Connect to bookmarked node            Right-click plug > *Connect Bookmark* > select
                                      node
===================================== =============================================
```


## _Viewer_ ##

> Note :
> For the following controls and shortcuts, the cursor must hover over the _Viewer_.


### General Controls ###

```eval_rst
===================================== =============================================
Action			                      Control or Shortcut
===================================== =============================================
Pan                                   :kbd:`Alt` + click and drag
Zoom/dolly                            :kbd:`Alt` + right-click and drag
                                      
                                      or
                                      
                                      Mouse wheel up/down
Frame view to contents                :kbd:`F`
===================================== =============================================
```


### 3D Scenes ###

```eval_rst
====================================================== =====================================
Action			                                       Control or Shortcut
====================================================== =====================================
Tumble                                                 :kbd:`Alt` + click and drag
Expand selection                                       :kbd:`↓`
Fully expand selection                                 :kbd:`Shift` + :kbd:`↓`
Collapse selection                                     :kbd:`↑`
Fit clipping planes to scene                           Right-click > *Clipping Planes* > *Fit 
                                                       To Scene*
Fit clipping planes to selection                       Right-click > *Clipping Planes* > *Fit 
                                                       To Selection*

                                                       or

                                                       :kbd:`Ctrl` + :kbd:`K`
Frame view, and fit clipping planes to scene/selection :kbd:`Ctrl` + :kbd:`F`
Reset clipping planes                                  Right-click > *Clipping Planes* > 
                                                       *Default*
====================================================== =====================================
```


### 2D Images ###

```eval_rst
===================================== =============================================
Action			                      Control or Shortcut
===================================== =============================================
Toggle red channel                    :kbd:`R`
Toggle green channel                  :kbd:`G`
Toggle blue channel                   :kbd:`B`
Toggle alpha channel                  :kbd:`A`
Center image at 1:1 scale             :kbd:`Home`
===================================== =============================================
```


## _Script Editor_ ##


### Text Entry ###

> Note :
> When using the following drag and drop controls and shortcuts, drop the UI element onto the _Script Editor's_ text input field.

```eval_rst
================================================== ================================================
Action                                             Control or Shortcut
================================================== ================================================
Drop node into *Script Editor*                     Middle-click and drag node from *Node Graph*
Drop plug into *Script Editor*                     Middle-click and drag plug from *Node Graph* 
                                      
                                                   or
                                      
                                                   Click and drag plug label from *Node Editor*
Drop plug value into *Script Editor*               :kbd:`Shift` + click and drag plug label from
                                                   *Node Editor*
Drop color value into *Script Editor*              Click and drag a pixel from *Viewer*
Drop scene location path(s) into *Script Editor*   Click and drag selection from *Viewer* or 
                                                   *Scene Hierarchy*
================================================== ================================================
```


### Execution ###

> Note :
> For the following controls and shortcuts, the _Script Editor's_ text input field must be in focus.

```eval_rst
===================================== =============================================
Action                                Control or Shortcut
===================================== =============================================
Execute and clear                     :kbd:`Ctrl` + :kbd:`Enter`
Execute selection                     Select code, then :kbd:`Ctrl` + :kbd:`Enter`
===================================== =============================================
```


## _Animation Editor_ ##

> Note :
> For the following controls and shortcuts, the cursor must hover over the _Animation Editor_.

```eval_rst
=============================================== =============================================
Action                                          Control or Shortcut
=============================================== =============================================
Pan                                             :kbd:`Alt` + click and drag
Zoom                                            :kbd:`Alt` + right-click and drag

                                                or
                                                
                                                Mouse wheel up or down
Adjust frame range                              :kbd:`Alt` + :kbd:`Shift` + right-click and
                                                drag left or right
Adjust key value range                          :kbd:`Alt` + :kbd:`Shift` + right-click and
                                                drag up or down
Frame all curves (no selection)                 :kbd:`F`
Frame selected key(s)                           :kbd:`F`
Add key to a curve                              :kbd:`Ctrl` + click
Add key to all selected curves at current frame :kbd:`I`
Delete selected key(s)                          :kbd:`Delete`

                                                or
                                                
                                                :kbd:`Backspace`
Adjust selected key(s)                          Click and drag
Adjust frame(s) of selected key(s)              :kbd:`Shift` + click and drag left or right
Adjust value(s) of selected key(s)              :kbd:`Shift` + click and drag up or down
=============================================== =============================================
```
