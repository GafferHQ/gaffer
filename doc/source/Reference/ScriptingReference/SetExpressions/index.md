Set Expressions
===============

Set expressions are a convenient way to build sets from other sets or locations. For the following examples we will assume that the scene has the following hierarchy :

- A
- B
- C
- D
  - E

Set memberships in this imaginary scene are as follows.

```eval_rst
===== ===== ===== ====
set1  set2  set3  set4
===== ===== ===== ====
A B C B C D C D E E
===== ===== ===== ====
```

The following operators are currently supported

```eval_rst
=================== ======================================
Operator            Behaviour
=================== ======================================
\|                  Union, unites two sets
&                   Intersection, intersects two sets
\-                  Difference, removes elements from sets
in                  Descendant query, selects locations from
                    one set which are parented under locations
                    in another
containing          Ancestor query, selections locations from
                    one set which are parents of locations
                    in another
=================== ======================================
```

Simple Examples
---------------

```eval_rst
===================== ==============================
SetExpression         Objects in resulting set
===================== ==============================
set1                  A B C
set1 \| set2          A B C D
set1 & set2           B C
set1 \- set2          A
set1 \- C             A B
set4 in set2          E
set2 containing set4  D
===================== ==============================
```

The last example illustrates the use of objects in set expressions. Gaffer will interpret them as a set with the specified object as its sole member. Gaffer will also conveniently interpret space separated lists of sets and objects as a set that contains all the elements in the list (think of it as Gaffer inserting the \| for you).

```eval_rst
=================== ==============================
SetExpression       Objects in resulting set
=================== ==============================
set1 set2           A B C D
set1 D              A B C D
=================== ==============================
```

Note that you can build sets on-the-fly to be used in the expression by using these space separated list of sets and objects.

```eval_rst
==================== ==============================
SetExpression        Objects in resulting set
==================== ==============================
set1 \| (D E)        A B C D E
set1 & (A B D)       A B
set1 \- (B C)        A
==================== ==============================
```

Operator Precedence
-------------------

Operations in the expression are executed in the following order : `-`, `&`, `containing` and then `in`. The following examples demonstrate this in action.

```eval_rst
==================== ==============================
SetExpression        Objects in resulting set
==================== ==============================
set1 \| set3 & set4  A B C E
set1 \- set2 \| set4 A E
set1 \- set3 & set2  B
==================== ==============================
```

Parenthesis can be used to explicitly change the order of evaluation. The following examples use the same sets and operations as before, and demonstrate the effect of changing the evaluation order.

```eval_rst
====================== ==============================
SetExpression          Objects in resulting set
====================== ==============================
(set1 \| set3) & set4  E
set1 \- (set2 \| set4) A
set1 \- (set3 & set2)  A B
====================== ==============================
```
