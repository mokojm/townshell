# TownShell

<p align="center">
<a href="./Pictures/TownShell.ico">
<img src="./Pictures/TownShell.ico" alt="TownShell ico">
</a>
</p>

![TownShellgif](/Pictures/TownShell.gif)

Wanna save some clicks on [Townscaper](https://store.steampowered.com/app/1291340/Townscaper/), this small command line shell will help you !
Get additional keyboard shortcuts to relax your fingers while building your town.
Get access to useful tools to accelerate your building process. Change the height of many blocks at a time. Change the color of your whole structure with a few words.

# Quickstart
Download "TownShell.zip" [here](https://fromsmash.com/townshell-zip)
Uncompress it
Click '**townshell.bat**'

Open "Townscaper"
Click "New"
Press "x" few seconds 
Enjoy the fast click !

Click "Save to Clipboard"
Tap "²" to open "TownShell"
Write "**level -h:10**"
Back to "Townscaper" click "Load from Clipboard"
Enjoy the time you've saved !

Explore this file for more features

# Table of contents
1) [Installation](#installation)
2) [Usage](#usage)
	- [Keyboard Shortcuts](#keyboard-shortcuts)
	- [Level command](#level-command)
	- [Paint command](#paint-command)
	- [Undo/Redo](#undo-redo)
3) [Details](#details)
	- [Startup screen](#startup-screen)
	- [Advanced installation](#advanced-installation)
	- [Shortcuts configuration](#shortcuts-configuration)
	- [More](#theory)
4) [Future Releases](#future-releases)

# Installation

The easiest way to get started is by following the link [here](https://fromsmash.com/townshell-zip),
Choose the file adapted to your system (32/64 bits)
Download "TownShell.zip"
Uncompress it
Click 'townshell.bat'
Enjoy !

If you trust me and want to have a beautiful ".exe" Go [here](https://fromsmash.com/townshell-exe),
Choose the file adapted to your system (64 bits only for now)
Download it,
Bypass the security of Windows
Launch the installer
Click "TownShell.exe"
Enjoy !

For advanced users see [Advanced installation](#advanced-installation)

# Usage
## Keyboard shortcuts
Keyboard shortcuts are active by default once TownShell is started. It works only when Townscaper is the foreground window.
Default shortcuts are as follows :

'Open TownShell' ==> '²'

'left_click' ==> 'x'

'right_click' ==> 'c'

'undo' ==> 'v'

'redo' ==> 'b'

'custom_left_click' ==> 'maj+x'

'custom_right_click' ==> 'maj+c'

'custom_undo' ==> 'maj+v'

'custom_redo' ==> 'maj+b'

For example, by default, keeping 'x' pressed will result in block creation every 0,05 seconds.

Custom shortcuts allow you to have one event done a precise number of times:
1) Press one or several digits
2) Use one of the custom shortcuts described above
Note that if you press several digits, the time between the press needs to be less than one second.
For example, if you press "1" then "2" quickly then you use 'custom_left_click' keyboard shortcut, it will result in 12 blocks getting created.

If you're not satisfied with these shortcuts see [Shortcuts configuration](#shortcuts-configuration)

## Level command

![TownShell_level_example](/Pictures/level_h_7.png)

'level' command give you the ability to elevate your structure at any height (<255) with a bunch of options. To use it, click "Save to Clipboard" on the structure you want the height to change, 
press "²" to open TownShell and enter a command following the rules below. 
Then on Townscaper click "Load from Clipboard".

Note that your original file is not modified.

level -height:\<n\> -max_height:\<n\> - min_height:\<n\> -plain:<0/1> -color:\<n\> -color_filter:\<n\> \<clip\> ==> Modify the height of your structure according to \<n\>
- height (-h): [mandatory] The height that will be added to the selected structure. Can be negative, the height of the structure will be decreased
- max_height (-maxh): [optional] The maximum height for all building in the structure.
- min_height (-minh): [optional] The minimum height for all building in the structure.
- plain (-p): [optional] If 0 or not filled, the space below the elevated building stays empty. If 1, the created spaces are filled
- color (-c): [optional] color (between 1 and 14) that will be applied to the newly created blocks. If not filled, the potential new blocks will take the color of the first colored one above them (or the default color if no blocks above them).
- color_filter (-cf): [optional] Only the blocks having this color (between 1 and 14) will be affected by this command
- \<clip\> : [optional] Clip from Townscaper to be modified

Tips:
- Do not waste time, use abbreviation. For example:
"level -height:4 -plain:1" can be written "level -h:4 -p:1"
- If for some reason you want your map to become flat, 1 voxel above the ocean use the following command :
"level -height:0 -maximum_height:1" or "level -h:0 -maxh:1"

## Paint command

![Paint_example](/Pictures/paint_c_14.png)

'paint' command give you the ability to change the color of many blocks at a time with a bunch of options.
To use it, click "Save to Clipboard" on the structure you want the height to change, 
press "²" to open TownShell and enter a command following the rules below. 
Then on Townscaper click "Load from Clipboard".

Note that your original file is not modified.

paint -color:\<multi\> -color_filter:\<n\> -height:\<multi\> \<clip\> ==> Modify the color of your structure according to \<n\>
- \<file\> : [optional] Name of the file to be modified. Can be a path. Can be a chain of characters, the first file corresponding is used
- color (-c): [mandatory] The color (between 1 and 14) that will be applied to the selected blocks. Can be 'r' for random color. Can be (n,m,p) for random choice between n,m and p
- color_filter (-cf): [optional] Only the blocks with that color will be modified
- height (-h): [optional] Can be a positive integer. Only the blocks at that height will be affected. Can be (n,m,p) only the blocks at these height will be affected. Can be ((n,m),(p,q)). Only the blocks between height n and m, and between p and q will be affected
- \<clip\> : [optional] Clip from Townscaper to be modified

## Undo Redo

![Undo_redo_example](/Pictures/undo_redo.png)

'undo' command allows you to make mistakes and get back to the previous state of your masterpiece before your last command was entered.
To use it, open TownShell, tap "undo", get back to Townscaper and click "Load from Clipboard"

'redo' command allows you to change your mind and get back to the mistake you had undone.
To use it, open TownShell, tap "redo", get back to Townscaper and click "Load from Clipboard"

Note that no changes are made on Townscaper saved files only the clipboard content is modified.

# Details

## Startup screen

When starting TownShell the following are displayed :
- Keyboard shortcuts
- The directory where Townscaper saved files are gathered.
- Main commands are displayed.
You can write your first command after 'T>'

## Advanced installation
TownShell is written in Python. If you do not have Python installed on your computer, you can download it and install it from [here](https://www.python.org) 

Once Python is installed on your computer, the following library are necessary : keyboard, mouse, pyreadline and pyperclip. You can install them using 'pip' from windows command line (cmd.exe) :

```pip install keyboard mouse pyreadline pyperclip```

Then download the master branch then run "townshell.bat" to start using TownShell.

## Shortcuts configuration
At any time, you can see the active shortcuts using 'shortcuts' command in TownShell. If you're not satisfied with the shortcuts provided by default, you can modify them by opening 'townshell.cfg' file. 
1) Use your native notepad application to open it
2) Modify the lines related to the keyboard shortcuts to personify your TownShell. Note that 'pause' is the interval between to automatic clicks in seconds.
3) Save the file, then either restart TownShell or use command 'stop_shortcuts' then 'start_shortcuts'.

**Warning** ! Beware that Townscaper use already a few keyboard shortcuts, so it's recommended not to use these ones. See: https://www.yekbot.com/townscaper-controls-useful-shortcuts-for-fast-building/

## Concepts
In Townscaper saved files, each position on the grid of Townscaper is called a 'corner'. On each 'corner' you can have one or more blocks. A block is called a 'voxel'. Therefore, every Townscaper building is an assembly of corners of voxels.
If you wish to read more about how Townscaper saved files are made, you can go to the following website : https://medium.com/@chrisluv/getting-hacky-with-townscaper-5a31cf7f4c6a


## From clipboard to customizable dictionaries

Townscaper provides us strings through "Save to clipboard" that will be called "clip" in TownShell program. These clips contain all the information describing a given structure, allowing Townscaper's users to share their creations. 

[alvaro-cuesta](https://github.com/alvaro-cuesta/townsclipper) made a very good script that converts clips to dictionary of corners and voxels using Javascript.
Since TownShell is written in Python, the core part of townsclipper code has been translated and adjusted.


## Listfiles
'listfiles' gives you the opportunity to see what are the available files in Townscaper directory. Information displayed are "File Name", "Last modification date", the amount of corners in the corresponding file, the amount of voxels.
By default, the five most recent files are displayed. Use "listfiles -a" to have all your files displayed.

Tips:
- Instead of trying your best to identify the project you want to modify with TownShell using the available information described below. Go to Townscaper, find the project you're interested in, modify one block, undo and save it using "New" or "Open" button. Then go back to TownShell, the most recent file is now the project you've spotted, so you don't need to enter its name to execute a command like 'level' or 'paint'.
- If you're as lazy as me, use the alias 'ls' or 'dir' to achieve the same function with 'listfiles'

## Colors
'colors' print the available colors in Townscaper and their associated number.
For now, TownShell use these colors digits to identify the one you want to use.

By advance, sorry for color names, I'm opened to any suggestion.

## Loadpath
TownShell might not be able to find Townscaper saved file directory by itself. If it happens, you'll need to add it to him yourself in order to use most of TownShell commands.
Use 'loadpath \<directory\>' to achieve that. \<directory\> needs to be the directory where Townscaper saved files are. It's usually something like "...\AppData\LocalLow\Oskar Stalberg\Townscaper\Saves"
Just drag and drop the directory or copy/paste the directory path in TownShell after writing "loadpath " and press "Enter".

## Exit
Use 'exit' or 'Ctrl+D' to leave properly TownShell. Note that you can just close the window and nothing dramatic will happen.

## Record and Stop
If you want to save a combination of commands you can use 'record \<file\>' before executing your combination, then 'stop' to end recording. The combination will be saved in \<file\>.
To have it played at the startup of TownShell you'll need to modify 'townshell.cfg' and enter the path to the file you've created on 'job' line inside the quotes.

## Configuration file
'townshell.cfg' is the configuration file of TownShell. 

Keyboard shortcuts are stored inside.


## Logging
In 'townshell.cfg', 'loglevel' setting determine the level of log that will be saved in 'town.log'. By default it's "INFO". It can be useful to set it to "DEBUG" when a bug is encountered and needs to be shared.

'town.log' contains only the log information related to the running TownShell. If you're looking for older log information, it's in 'town_old.log'

# Future releases

These improvements should be implemented since it betters the experience with TownShell
- Press '²' to get back to Townscaper from TownShell
- Use "ctrl+alt+z" and "ctrl+alt+x" to perform command "undo" and "redo"
- Add an 'Escape' hot-keys to be able leave custom clicks in emergency
- Colored shell, to identify more easily information displayed
- Completion improvement, using 'tab', it would become much easier to build a command without knowing the syntax by heart
- Loadpath : I could use tkinter to let the user search for the directory easily


Here are some add-ons that my mind would love to see but I'm not sure if anybody aside from me would enjoy it, let me know !
- Keyboard shortcuts : While clicking automatically, it could alternate colors or have random color choices
- 'mix' : A new command to merge several files in one
- 'copy' : would combine 'mix' and 'level' to copy a building on itself but with a different height

- Groups : why not have some functions to have corners classified in different groups according to your needs. Even so the grid is a mess to wrap, it might be feasible to identify specific groups. I've already started a function to identify the borders of the structure for example.
- 'randtown' : a very powerful command line allowing you create random town with a lot of options
- macOS : I don't have a clue what it would imply to have TownShell working on macOS.
- Provide a collection of grid with interesting features
- Make 'playback' works or add a 'load' command to play combinations

# Contributing
I'm not very experienced at programming or using github, so any help on making this project easier to understand will be appreciated.
Do not hesitate to report bugs.

Copyright © 2020, [Álvaro Cuesta](https://github.com/alvaro-cuesta/townsclipper).
//=> Copyright (c) 2020 Álvaro Cuesta
