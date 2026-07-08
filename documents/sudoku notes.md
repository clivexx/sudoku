Title on number notes button should make the current mode obvious. Something like  **Number**/Note or Number/**Note** Currently it does not display correctly.

When a number is entered it is not displayed as bold. When a number button is clicked, and number mode is on, then that number is selected, and a function is called  to change the display to make all the instances of the selected number larger and bold. This function should be used whenever a number is entered or deleted. Notes are always displayed normally.



I think that this is the correct logic, please check.

A cell can have five different states:

1. Original number. Cannot be altered. slight grey shading.
2. Manually entered number. Can be cleared.
3. Blue triangle, no notes displayed. In number mode, a number can be entered to change to state 2. The triangle can be clicked to change to state 4.
4. Yellow triangle, calculated notes displayed. In number mode, a number can be entered to change to state 2. The triangle can be clicked to change to state 3. In note mode, notes can be entered or deleted this changes the cell to 5.
5. Green triangle, manual notes displayed. In number mode, a number can be entered to change to state 2. In note mode, notes can be entered or deleted. Clicking on a green triangle changes to state 4





Two points to be saved for later

Clearing a number changes the state from 2 to 3

Auto notes should simply change all cells in states 3 and 5 to state 4. I don't think that there should be any long term effect on the processing. It is an unnecessary complication.



To simplify the number or note entry, add another 3 by 3 block of buttons for notes below left

The validate button should de select number or note button

Rename instant errors as "show errors"

