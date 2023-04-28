Metadata
========

Gaffer's UIs for plugs and nodes are defined using a metadata convention. This
makes it easy to customise the UI for a specific node type, or even for a
specific node instance. This document provides a reference for the most common
metadata items.

General
-------

Name                | Purpose                                        | Example values
--------------------|------------------------------------------------|---------------
`label`             | Label used instead of plug name                | `"My Label"`
`description`       | Describes the purpose of a node or plug        | `"Turns on the thingammajig"`
`icon`              | Name of an image file used to represent a node | `"myAwesomeNode.png"`
`documentation:url` | Link to node documentation                     | `!http://www.gafferhq.org"`
`userDefault`       | Overrides the default value of a plug          | `10.5`
`preset:<name>`     | Specifies a named preset value                 | `"preset:Max", 1`
`renameable`        | Enables renaming by user                       | `True`, `False`
`deletable`         | Enables deletion by user                       | `True`, `False`

NodeEditor layout
-----------------

Name                              | Purpose                                       | Example values
----------------------------------|-----------------------------------------------|----------------
`layout:divider`                  | Places a divider after the plug               | `True`
`layout:index`                    | Integer index in the layout order             | `0` (first), `-1` (last)
`layout:section`                  | Specifies the section the plug belongs in     | `TabName.SectionName`
`layout:section:<name>:collapsed` | Specifies whether the section is collapsed    | `True` (collapsed), `False` (expanded)
`layout:accessory`                | Places widget on same line as previous widget | `True`
`layout:width`                    | Specifies a fixed width for the widget        | `100`
`layout:minimumWidth`             | Specifies a minimum width for the widget      | `100`

GraphEditor layout
------------------

Name                     | Purpose                         | Example values
-------------------------|---------------------------------|----------------
`nodule:color`           | The colour of the plug          | `imath.Color3f( 0, 1, 0 )`
`connectionGadget:color` | The colour of input connections | `imath.Color3f( 1, 0, 0 )`
`nodeGadget:color`       | The colour of a node            | `imath.Color3f( 0, 0, 1 )`
`noduleLayout:section`   | The edge the plug appears on    | `"left"`, `"right"`, `"top"`, `"bottom"`
`noduleLayout:visible`   | Shows/hides the plug            | `True` (visible), `False` (hidden)

Viewer layout
-------------

Name                    | Purpose                                    | Example values
------------------------|--------------------------------------------|-------------------
`layout:divider`        | Places a divider after the plug            | `True`
`layout:index`          | Integer index in the layout order          | `0` (first), `-1` (last)
`toolbarLayout:section` | The edge of the viewer the plug appears on | `"Left"`, `"Right"`, `"Top"`, `"Bottom"`

PlugValueWidgets
----------------

Custom widget types may be registered for use in the Node Editor by adding `plugValueWidget:type` metadata to a plug. Note that not all widget types are compatible with all plug types - the table below lists the relevant widget types by plug type.

Plug Type                  | Purpose                        | PlugValueWidgetType
---------------------------|--------------------------------|--------------------
Plug (and subclasses)      | Hide the plug permanently      |  `""`
Plug (and subclasses)      | Display the input connection   |  `"GafferUI.ConnectionPlugValueWidget"`
ValuePlug (and subclasses) | Show a menu of presets         |  `"GafferUI.PresetsPlugValueWidget"`
IntPlug                    | Display a checkbox             |  `"GafferUI.BoolPlugValueWidget"`
StringPlug                 | Allow multi-line text entry    |  `"GafferUI.MultiLineStringPlugValueWidget"`
StringPlug                 | Show a file chooser            |  `"GafferUI.FileSystemPathPlugValueWidget"`
StringVectorDataPlug       | Show a file chooser            |  `"GafferUI.FileSystemPathVectorDataPlugValueWidget"`

These widget types may be further customised using additional metadata as follows

### BoolPlugValueWidget

Name                               | Purpose               | Example values
-----------------------------------|-----------------------|---------------
`boolPlugValueWidget:displayMode`  | Change display style  | `"checkBox"`, `"switch"`

### FileSystemPathPlugValueWidget

These options also apply to the FileSystemPathVectorDataPlugValueWidget.

Name                              | Purpose                        | Example values
----------------------------------|--------------------------------|---------------
`path:bookmarks`                  | Specify which bookmarks to use | `"image"`
`path:leaf`                       | Don't accept directories       | `True`, `False`
`path:valid`                      | Only accept files that exist   | `True`, `False`
`fileSystemPath:extensions`       | Specify valid file types       | `"jpg jpeg png"`
`fileSystemPath:extensionsLabel`  | Describe valid file types      | `"Web images"`
`fileSystemPath:includeSequences` | Display file sequences         | `True`

### PresetsPlugValueWidget

Name                                 | Purpose                         | Example values
-------------------------------------|---------------------------------|---------------
`presetsPlugValueWidget:allowCustom` | Allow values not in preset list | `True`, `False`
