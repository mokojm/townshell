# TownShell
![TownShell](/Pictures/Townshell.PNG)

Wanna save some clicks on Townscaper, this small command line shell will help you !
Get additional keyboard shortcuts to relax your fingers while building your town.
Get access to useful tools to accelerate your building process. Change the height of many blocks with one command. Change the color of your whole structure with a few words.

# Features
Keyboards shortcuts are active at the start of the shell
- Keyboard shortcuts for fast left click, right click, undo, redo
- Keyboard shortcuts for fast click with customized amount of press

The following features need you to write command in the shell (ex: level -height:3 -color_filter:1)
- Modify the height of all blocks at a time, or part of the blocks, with various settings (color, maximum height, ...)
- Modify the color of all blocks, or part of the blocks, with various settings (previous color, height, ...)
- Control the versions of your files to keep trace of changes made, get back to your original files whenever you want thanks to the following commands (undo, redo, restore, backup)

# Installation
If you do not have python installed and you want to use TownShell right away I'd recommend downloading "TownShell.zip" here :
All you have to do is uncompress the zip file and click "TownShell.exe"

If you already have python installed on your computer, the following library are necessary : keyboard, mouse, pyreadline. You can install them using 'pip' :

```pip install keyboard mouse pyreadline```

Then you can download the master branch then click "townshell.bat" to start using it.

# Usage
## Keyboard shortcuts
### Getting started
Keyboard shortcuts are active by default once TownShell is started. They work only when Townscaper is the foreground window.
Default shortcuts are as follows :

'left_click' ==> 'x'

'right_click' ==> 'c'

'undo' ==> 'v'

'redo' ==> 'b'

'custom_left_click' ==> 'd'

'custom_right_click' ==> 'f'

'custom_undo' ==> 'g'

'custom_redo' ==> 'h'

For example, by default, keeping 'x' pressed will result in block creation every 0,05 seconds.

Custom shortcuts allow you to have one event done a precise number of times:
1) Press one or several digits
2) Use one of the custom shortcuts described above
Note that if you press several digits, the time between the press needs to be less than one second.
For example, if you press "1" then "2" quickly then you use 'custom_left_click' keyboard shortcut, it will result in 12 blocks getting created.

### Shortcuts configuration
At any time, you can see the active shortcuts using 'shortcuts' command in TownShell. If you're not satisfied with the shortcuts provided by default, you can modify them by opening 'townshell.cfg' file. 
1) Use your native notepad application to open it
2) Modify the lines related to the keyboard shortcuts to personify your TownShell. Note that 'pause' is the interval between to automatic clicks in seconds.
3) Save the file, then either restart TownShell or use command 'stop_shortcuts' then 'start_shortcuts'.

Warning ! Beware that Townscaper use already a few keyboard shortcuts, so it's recommended not to use these ones. See: https://www.yekbot.com/townscaper-controls-useful-shortcuts-for-fast-building/

## General information

The main purpose of TownShell is to manipulate Townscaper saved files to achieve operations that would be very time consuming using only left and right click.

### Theory

In Townscaper saved files, each position on the grid of Townscaper is called a 'corner'. On each 'corner' you can have one or more blocks. A block is called a 'voxel'. Therefore, every Townscaper building is an assembly of corners of voxels.
If you wish to read more about how Townscaper saved files are made, you can read the following website : 

### Limitations

**When using the most of the commands described below it's necessary to proceed this way :
1) Enter your command (ex: level -height:7)
2) On Townscaper, click 'New'
3) Then click 'Open' and select the most recent file**
Even so your structure has now changed, you'll notice that the picture is not updated, that's because TownShell does not know how to do it. However, just create one block and remove it to have your file saved again by Townscaper and the picture will be updated too.

For now, TownShell is able to change the color of voxels, change the height of voxels, create voxels on an existing corner.

It cannot create corners from an empty map. Indeed, I have not figure out the algorithm behind grid generation so I'm quite restrained on this side. Hope I get some time or some help to find out and create much more amazing functions.

## Getting started with command line TownShell
### Startup screen
![TownShell_get_started](/Pictures/TownShell_start_screen.png)

When starting TownShell the following are displayed :
1) Right after the title, this line means that TownShell was able to find the place where your Townscaper saved filed are gathered by the game. If not follow these steps :

2) The list of the five most recent Townscaper saved files is displayed. The information delivered can be useful to identify you want modify

3) Keyboard shortcuts are displayed

4) Main commands are displayed.

All your Townscaper saved files are backup-ed in 'backup' directory on startup. You'll never what you've been working on so hard !

You can write your first command after 'T>'

### Level

![TownShell_level_example](/Pictures/level_h_7.png)

'level' command give you the ability to elevate your structure at any height (<255) with a bunch of options.

level \<file\> -height:\<n\> -max_height:\<n\> - min_height:\<n\> -plain:<0/1> -color:\<n\> -color_filter:\<n\> -new_file:\<file\> ==> Modify the height of your structure according to \<n\>
- \<file\> : [optional] Name of the file to be modified. Can be a path. Can be a chain of characters, the first file corresponding is used
- height (h): [mandatory] The height that will be added to the selected structure. Can be negative, the height of the structure will be decreased
- max_height (maxh): [optional] The maximum height for all building in the structure.
- min_height (minh): [optional] The minimum height for all building in the structure.
- plain (p): [optional] If 0 or not filled, the space below the elevated building stays empty. If 1, the created spaces are filled
- color (c): [optional] color (between 1 and 14) that will be applied to the newly created blocks. If not filled, the potential new blocks will take the color of the first colored one above them (or the default color if no blocks above them).
- color_filter (cf): [optional] Only the blocks having this color (between 1 and 14) will be affected by this command
- new_file (nf): [optional] Instead of updating the original file, a new one is created. Can be anything

Tips:
- If it makes you more comfortable to keep both the new modified Townscaper file and the original, do not hesitate to use '-new_file'
- \<file\> is not mandatory. If not provided, the most recent file will be used. Your agreement is required if there is a doubt on whether it's the good file to modify or not.
- Townscaper saved files names are terrible, do not hesitate to input just a small portion in your command or copy/paste
- Do not waste time, use abbreviation. For example:
"level -height:4 -plain:1" can be written "level -h:4 -p:1"
- If for some reason you want your map to become flat, 1 voxel above the ocean use the following command :
"level -height:0 -maximum_height:1" or "level -h:0 -maxh:1"

Future releases :
- 'default_color' to be customizable
- 'height': to be an optional setting (height=0 by default)
- 'color filter': several colors to be filtered at a time
- 'color' could be 'random' or several colors
- 'plain' : more options to have holes 

### Paint

![Paint_example](/Pictures/paint_c_14.png)

'paint' command give you the ability to change the color of many voxels at a time with a bunch of options

paint \<file\> -color:\<multi\> -color_filter:\<n\> -height:\<multi\> -new_file:\<file\> ==> Modify the color of your structure according to \<n\>
- \<file\> : [optional] Name of the file to be modified. Can be a path. Can be a chain of characters, the first file corresponding is used
- color (c): [mandatory] The color (between 1 and 14) that will be applied to the selected blocks. Can be 'r' for random color. Can be (n,m,p) for random choice between n,m and p
- color_filter (cf): [optional] Only the blocks with that color will be modified
- height (h): [optional] Can be a positive integer. Only the blocks at that height will be affected. Can be (n,m,p) only the blocks at these height will be affected. Can be ((n,m),(p,q)). Only the blocks between height n and m, and between p and q will be affected
- new_file (nf): [optional] Instead of updating the original file, a new one is created. Can be anything

Tips:
- \<file\> is not mandatory. If not provided, the most recent file will be used.

Future releases:
- 'color filter': several colors to be filtered at a time
- 'details' : option to be added to associate height and colors directly
- 'height' : add '>', '<', '\<\>'
- 'color' : add the possibility to alternate several colors

### Undo and Redo

![Undo_redo_example](/Pictures/undo_redo.png)

'undo' command allows you to make mistakes and get back to the previous state of your masterpiece before your last command was entered.

'redo' command allows you to change your mind and get back to the mistake you had undone.

Tips:
- 'undo \<file\>' and 'redo \<file\>' allow you to specify the file you want to bring back to its previous state. Otherwise, the most recent file will be the one undone

Future releases:
- For now, if you modify the file you're working on outside TownShell, then use a command like 'level' or 'paint' then use 'undo', it will get back to the state of your file before the modification you did before outside TownShell. It could be improved.
- 'backup' and 'restore' commands do not reset 'undo' nor 'redo'. Maybe it should...
- 'undo' and 'redo' do not save meta data of the files. I'm still questioning whether it's useful

### Restore and Backup
While 'undo' and 'redo' save your data in memory, 'restore' and 'backup' allow you to manage the state of your files on your hard disk.
At startup, 'backup -all' is done automatically so your files are saved in 'backup/\<timestamp\>' before anything happen to them.

You can do a 'backup' at any time. However, it will erase the previous backup made for this run of TownShell.
'backup \<file\>' does exactly what you think it should.
'backup -all' and 'backup -a' do exactly what you think it should (hope you think the same with me)

'restore' gives the ability to bring back the file you've spotted to its last backup state. If no manual backup done before, it will use the backup done during startup.

'restore -all' and 'restore -a' do exac... (you know... let's move on !)

### Listfiles
'listfiles' gives you the opportunity to see what are the available files in Townscaper directory. Information displayed are "File Name", "Last modification date", the amount of corners in the corresponding file, the amount of voxels.
Since you cannot recognize your projects using pictures like in-game directory, these information may help you figure out which file you want to work with.
By default, the five most recent files are displayed. Use "listfiles -a" to have all your files displayed.

Tips:
- Instead of trying your best to identify the project you want to modify with TownShell using the available information described below. Go to Townscaper, find the project you're interested in, modify one block, undo and save it using "New" or "Open" button. Then go back to TownShell, the most recent file is now the project you've spotted, so you don't need to enter its name to execute a command like 'level' or 'paint'.
- If you're as lazy as me, use the alias 'ls' or 'dir' to achieve the same function with 'listfiles'

### Colors
'colors' print the available colors in Townscaper and their associated number.
For now, TownShell use these colors digits to identify the one you want to use.

By advance, sorry for color names, I'm opened to any suggestion.

### Loadpath
TownShell might not be able to find Townscaper saved file directory by itself. If it happens, you'll need to add it to him yourself in order to use most of TownShell commands.
Use 'loadpath \<directory\>' to achieve that. \<directory\> needs to be the directory where Townscaper saved files are. It's usually something like "...\AppData\LocalLow\Oskar Stalberg\Townscaper\Saves"
Just drag and drop the directory or copy/paste the directory path in TownShell after writing "loadpath " and press "Enter".

### Exit
Use 'exit' or 'Ctrl+D' to leave properly TownShell. Note that you can just close the window and nothing dramatic will happen.

## Advanced features

### Record and Stop
If you want to save a combination of commands you can use 'record \<file\>' before executing your combination, then 'stop' to end recording. The combination will be saved in \<file\>.
To have it played at the startup of TownShell you'll need to modify 'townshell.cfg' and enter the path to the file you've created on 'job' line inside the quotes.

### Configuration file
'townshell.cfg' is the configuration file of TownShell. 

Keyboard shortcuts are stored inside.

'user_approval' setting controls TownShell behavior when a command like 'level', 'paint', or 'undo' is used without any file name in the command (Example : level -h:8). TownShell will use the last modified file in Townscaper saved file directory, however if this last modified file changed between the last command and the current one, TownShell will ask approval of the user before performing anything. This can happen when you're alternatively using Townscaper and TownShell.

# Future releases

## High Priority
These improvements will for sure be implemented since it betters the experience with TownShell
- Add an 'Escape' hot-keys to be able custom clicks in emergency
- Make 'playback' works or add a 'load' command to play combinations
- Colored shell, to identify more easily information displayed
- Completion improvement, using 'tab', it would become much easier to build a command without knowing the syntax by heart
- Loadpath : I could use tkinter to let the user search for the directory a more common way

## Questionable Priority
Here are some add-ons that my mind would love to see but I'm not sure if anybody aside from me would enjoy it, let me know !
- Keyboard shortcuts : While clicking automatically, it could alternate colors or have random color choices
- 'mix' : A new command to merge several files in one
- 'copy' : would combine 'mix' and 'level' to copy a building on itself but with a different height

- Groups : why not have some functions to have corners classified in different groups according to your needs. Even so the grid is a mess to wrap, it might be feasible to identify specific groups. I've already started a function to identify the borders of the structure for example.
- 'randtown' : a very powerful command line allowing you create random town with a lot of options
- macOS : I don't have a clue what it would imply to have TownShell working on macOS.
- Provide a collection of grid with interesting features
