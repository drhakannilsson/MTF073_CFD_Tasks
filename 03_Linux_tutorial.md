# A Linux tutorial for beginners

You don't need this tutorial to follow the rest of the instructions, but it helps you understand what you are doing. If you continue using Ubuntu, it gives you a good start with Linux. If you want to skip, move on to [04_The_OpenFOAM_flange_tutorial.md](04_The_OpenFOAM_flange_tutorial.md).

To follow the tutorial, type the commands in the left column into a terminal window. Type each command on a single line, even if it is shown on multiple lines here. Some rows have several commands, separated by `;`. You can type them on a single line, or one at a time. Read the description in the right column. It is in some cases important that the commands are entered in the exact order they are listed. When you are familiar with Linux commands you should be able to practice them in any order.

Useful keys in the terminal window:
- Copy and paste with Ctrl-Shift-C and Ctrl-Shift-V.
- Stop the running command with Ctrl-C (this is why copy is Ctrl-Shift-C).
- Go through earlier commands with the ↑ and ↓ arrow keys.
- Search for an earlier command with Ctrl-R, and type some characters of it. Press Ctrl-R again to go to older commands containing the same characters. Press Enter to run the command, or the → arrow key to edit it first. Press Ctrl-C to cancel.

Paths are written with `/`, as in `~/OpenFOAM/<username>-v2606/run` (not with `\` as in Windows). Upper and lower case letters are different (`Allrun` is not `allrun`).

Please let me know if you find any errors or have any suggestions.

## Managing files and directories, and moving around in the file system

| Command | Description |
|---|---|
| `cd` | Move to your home directory. You should be there already if you just opened the terminal. |
| `ls` | List the files and directories in a directory (use this command at any time during the tutorial to see what files and directories you have in the current directory!) |
| `ls -l` | List the files in a directory with extended information |
| `ls -a` | List all files, including hidden files (files with names starting with a dot, for example `.bashrc`) |
| `ls --help` | Get information on how to use the `ls` command (note that `--` are two dashes). |
| `man ls` | Show the manual page for the `ls` command.<br>Move up and down a single line with the arrow keys.<br>Move up and down the number of displayed lines using CTRL-F and CTRL-B.<br>Go to the first line by typing `1G` (try other line numbers).<br>Go to the last line by typing `G`.<br>Search forward for the flag `-a` by typing `/-a` (does not go to the beginning, first type `1G`).<br>Search for the next occurrence of `-a` by pressing `n`.<br>Search for the previous occurrence of `-a` by pressing `N`.<br>Search backward using `?-a` (now `n` will continue backward and `N` the opposite).<br>(Now you were actually fooled to learn some vi commands.)<br>Exit by typing `q`. |
| `mkdir linuxTutorial` | Make a directory named `linuxTutorial`. Note that Linux is case-sensitive, i.e. `linuxTutorial` is different from `linuxtutorial`. |
| `cd linuxTutorial` | Move into the directory named `linuxTutorial`.<br>Hint:<br>You can use the TAB key to complete entries. Test by:<br>&nbsp;&nbsp;`cd`<br>&nbsp;&nbsp;`cd li<TAB>`<br>(where `<TAB>` means that you should press the tab key).<br>You should see the original line automatically expanded.<br>If there are several directories or files with names starting the same way the line will not be expanded. Instead, you can press TAB again to see the files and directories that start with `li`. Try this:<br>&nbsp;&nbsp;`cd`<br>&nbsp;&nbsp;`mkdir liTest`<br>&nbsp;&nbsp;`cd li<TAB><TAB>`<br>At this point, the command that you have started to type is still at the command line, and you can continue the command with the next letter of the directory you intend to move into:<br>&nbsp;&nbsp;`cd lin<TAB>`<br>Clean up and go to the `linuxTutorial` directory:<br>&nbsp;&nbsp;`cd`<br>&nbsp;&nbsp;`rmdir liTest`<br>&nbsp;&nbsp;`cd linuxTutorial` |
| `echo "Hello World!"` | Print "Hello World!" in the terminal window |
| `echo "A first text line in my file" > myFile.txt` | Create a file named `myFile.txt`, and add a line to it saying: "A first text line in my file". Here, the `>` re-directs the output from the `echo` command to a file instead of to the terminal window. |
| `echo "A second text line in my file" >> myFile.txt` | Append the line "A second text line in my file" to `myFile.txt`. The `>>` appends the output of the `echo` command to the same file as before. If we had used the `>` we would have overwritten the file instead. If the file is not already available it will be created.<br>Many commands in Linux produce outputs. In general, `>` and `>>` can be used to redirect any command output to a file. |
| `cp myFile.txt copyOfMyFile.txt` | Copy the file (check with `ls`!) |
| `rm myFile.txt` | Remove the original file (check with `ls`!)<br>**Be careful with `rm`. There is no undo and no recycle bin.** |
| `mv copyOfMyFile.txt myFile.txt` | Rename the new file to the name of the original file (check with `ls`!)<br>`mv` is the move file/directory command. But here, since both source and destination directories are the same (both are the current directory), the `mv` command works as rename. |
| `mkdir aSecondDirectory` | Make a directory named `aSecondDirectory` inside the `linuxTutorial` directory (check with `ls`!) |
| `cd aSecondDirectory` | Move inside `aSecondDirectory` |
| `cd ..` | Move up one directory, in this case to the directory named `linuxTutorial`.<br>Note that `.` means the current directory while `..` points to the upper directory. |
| `rmdir aSecondDirectory` | Remove the empty directory named `aSecondDirectory` |
| `mkdir -p aSecondDirectory/aThirdDirectory/aFourthDirectory` | Create this directory structure inside the `linuxTutorial` directory |
| `cp myFile.txt aSecondDirectory/aThirdDirectory/aFourthDirectory` | Copy the file to the directory named `aFourthDirectory` |
| `ls aSecondDirectory/aThirdDirectory/aFourthDirectory` | List the files in the directory named `aFourthDirectory` |
| `cd aSecondDirectory/aThirdDirectory/aFourthDirectory` | Go to the directory named `aFourthDirectory` |
| `pwd` | Show your current directory path |
| `cd ../../..` | Move up three directory levels (you should now be in the `linuxTutorial` directory, check with `pwd`) |
| `pushd aSecondDirectory/aThirdDirectory/aFourthDirectory` | Go directly to the directory named `aFourthDirectory`, but remember where you came from |
| `popd` | Go back to where you came from using the previous `pushd` command |
| `cd -` | Go back to where you last came from. This is good if you want to move back and forth between two directories. Every time you type the command, you will go to the other directory. Type `cd -` again to go back to `linuxTutorial` (check with `pwd`). |
| `sudo apt install tree` | Install the `tree` command, which is used below. You are asked for your Ubuntu password. |
| `tree -L 3` | Print out the directory structure in the terminal window |
| `tree -L 2` | Print out only two levels of the directory structure |
| `tree -d` | Print out only the directories in the directory structure |
| `more myFile.txt` | View the contents of `myFile.txt`. If the file is large you exit with `q`, and move down in the file by pressing Enter. |
| `head myFile.txt` | View the beginning of `myFile.txt` (in this case it shows all of the file since it is small). |
| `tail myFile.txt` | View the end of `myFile.txt` (in this case it shows all of the file since it is small). |
| `tail -f myFile.txt` | View the end of a file and update when lines are added to the file. Exit with CTRL-C. |
| `grep "second text line" myFile.txt` | Search for the string "second text line" in `myFile.txt`, and print out all lines that match |
| `grep -r "first text line" aSecondDirectory` | Search for the string "first text line" recursively in the directory named `aSecondDirectory` |
| `find aSecondDirectory -iname "*yfi*"` | Find all files that have the string `yfi` in their file name. The string is not case sensitive because we use the flag `-iname`. The `*` means "any string". The command is recursive. |
| `sed -i 's/second text line/modified text line/g' myFile.txt` | Substitute the string "second text line" in `myFile.txt` with "modified text line". Use your Linux skills to check that it was done! |
| `mkdir newDirectory;`<br>`cp --parents aSecondDirectory/aThirdDirectory/aFourthDirectory/myFile.txt newDirectory` | Make a new directory and copy the whole file structure of `myFile.txt` into that directory. Use your Linux knowledge to check out the directory structure. |
| `rm -r newDirectory` | Remove `newDirectory` and everything in it. |
| `rm -r aSecondDirectory` | Remove the directory `aSecondDirectory` and all files and directories in it (`rmdir` does not work if there are files or directories in a directory) |
| `ln -s myFile.txt softLinkToMyFile.txt` | Make a soft link to `myFile.txt`. The original file will NOT be copied, but the name `softLinkToMyFile.txt` will point at `myFile.txt`. If you edit `softLinkToMyFile.txt` you will actually edit `myFile.txt`. However, removing `softLinkToMyFile.txt` will only remove the link, and not `myFile.txt`. You can see links using the `ls -l` command, showing the sign `->`, meaning that it points at another file. |
| `touch touchedFile.txt` | Create a file without opening it, and without adding anything in it. |
| `cd ; rm -r linuxTutorial` | Remove the `linuxTutorial` directory. Note that we here do two commands on the same line, first a `cd`, and then an `rm`! |
| `exit` | Close the terminal window |

## Managing processes

A process is a piece of code that is running. There are always processes running in the background. Some of them you may have started yourself. Here are some Linux commands that help you manage the processes:

| Command | Description |
|---|---|
| `sleep 1d &` | Put a job in background when starting it. `sleep 1d` is the job we run in this case, and `&` puts it in background, so that you can continue working in the terminal window. Of course, any other process than `sleep` can be used. |
| `jobs` | List background jobs in the current terminal window. The jobs are numbered 1, 2, 3, ... |
| `ps -ef \| grep sleep` | List all the processes on the computer containing the string `sleep`. The `ps -ef` command lists all the processes on the computer. The `\|` sign sends that output to the `grep sleep` command, which makes sure that only lines containing the string `sleep` are shown. The first number on each line is the process id (PID). |
| `fg` | Put a process in foreground, in this case the `sleep` process. If there are several jobs in background, the number of the job can be given after the `fg` command, otherwise it will operate on the one with the highest number. |
| CTRL-C | Kill a process in foreground, in this case the `sleep` process |
| `sleep 1d` | Start a job in foreground (i.e., don't use the `&` sign), which will lock the terminal window from further work. |
| CTRL-Z | Stop the process in foreground. The process will be paused until it is put in background with the `bg` command. |
| `bg` | Put the paused process in background, where it continues to run. |
| `top` | Show the activity of all the processes on the computer. The first number on each line is the process id (PID). Exit by typing `q`. |
| `kill <PID>` | Kill a job in background. Find the process id (PID) from the `ps` command, or the `top` command. |
| `kill -9 <PID>` | If the `kill` command doesn't work, try to add the `-9` flag, which should force the kill. |
| `which sleep` | Print the full path to the `sleep` executable, so that you can check that you are running the file you think that you are running. |
| `sle<TAB>` | The TAB key also works for finding executables that start with some string. |

## Environment and aliases

Environment variables can be set to different values in each terminal window, forming an "environment" of that specific terminal window. In simple terms, it is a variable in the terminal window with a name and a value. It does not do anything by itself, but can be used by other commands and in scripts. An environment variable that is set in one terminal window is not automatically set in any other terminal window.

| Command | Description |
|---|---|
| `env` | List the currently available environment variables, such as `HOME` |
| `echo $HOME` | Print to the terminal window the value of the environment variable named `HOME`, which is set up automatically as the path to the home directory (unless you have changed it). Note that the character `$` is only used to say that you want the system to expand the environment variable before executing the command. |
| `echo $PWD` | Print to the terminal window the value of the environment variable `PWD`, which automatically has the path to the current directory. |
| `echo $PATH` | Print to the terminal window the value of the environment variable `PATH`, which keeps a colon-separated list of paths where the system should look for the executables of the commands that you type in the terminal window.<br>The command `which ls` returns `/usr/bin/ls`, which shows the full path to the file that is executed when you type the command `ls`. The path `/usr/bin` can only be found if it is in the list of paths given in the `PATH` environment variable. In most/all cases the current directory is not listed in the path, which means that an executable that is located in the current directory can not be found if you try to execute it by typing its name. As an example we can copy the `ls` command to our current directory:<br>&nbsp;&nbsp;`cp /usr/bin/ls myLs`<br>Trying to execute it by typing `myLs` will fail, although you know that the executable is in the exact directory where you are located! This can be annoying if you do not know why. The command `myLs` can not be found in any of the directories listed in the environment variable `PATH`, so the system will not find it. You can still run commands that can't automatically be found, by giving the exact path:<br>&nbsp;&nbsp;`./myLs`<br>The dot refers to the current directory. You know that the `PWD` environment variable keeps the path to the current directory, so you can also type:<br>&nbsp;&nbsp;`$PWD/myLs`<br>Note here that I do not have to know in which directory you executed the previous command. In particular, it is most common to work in your home directory. The path to that directory contains your user name, so it is different for users with different user names. The `PWD` environment variable will adapt to that, so that I do not have to bother about differences in user names. The use of environment variables thus makes things more general. |
| `export myEnvironmentVariable="valueOfMyEnvironmentVariable"` | Set the value of the environment variable named `myEnvironmentVariable` to `valueOfMyEnvironmentVariable`. |
| `echo $myEnvironmentVariable` | Print to the terminal window the value of the environment variable named `myEnvironmentVariable`, which you just assigned the value to. |
| `export PATH=$PATH:.` | Add the current directory to the environment variable `PATH`. Note here that `$PATH` will first expand the current contents of the environment variable `PATH`. Then we add `:.` to it. If you now try the above exercise with the `myLs` command, the system will find it without giving the full path. |
| `rm myLs` | Clean up by removing your copy of the `ls` command. |
| `cd $HOME` | Go to the directory that corresponds to the value of the environment variable named `HOME`, which is the path to the home directory (unless you have changed it). |

Aliases are used to define a name of a command, or group of commands. The alias can be used to execute that command or group of commands, without having to type the original command or group of commands.

| Command | Description |
|---|---|
| `alias` | List the currently available aliases, which you can use as "commands" in the terminal window. |
| `alias goHome='echo "Going to home directory"; cd $HOME'` | Define a new alias named `goHome`, and when used it will write the string "Going to home directory" to the terminal window and execute the command `cd $HOME`. Note here that it is important to use different quotation marks for the entire command after the `=` sign, and the string inside that command.<br>Test by typing:<br>&nbsp;&nbsp;`goHome` |

## The bash shell and the ~/.bashrc file

### Shells

The "shell" is the program that takes the command that you type in the terminal window, and gives it to the operating system to perform the operation. There are different shells, like bash, sh, ksh, tcsh, zsh. They differ in the syntax you give the commands. We will here focus on the bash shell, which is an enhanced version of the original UNIX shell "sh", and the default shell in Ubuntu.

| Command | Description |
|---|---|
| `echo $0` | Print the shell name to the terminal window. |
| `bash` | Start a new bash shell inside the current one. Type `exit` to go back to the original shell. |

### Scripts

The commands that you write in the terminal window can as well be added to scripts that can be used to execute more complex combinations of commands. Create a file named `testScript.sh` with `nano testScript.sh`, and paste this into it:

```
#!/bin/sh
echo "Hello world"
if [ "$#" -ne 1 ]
then
    echo "Wrong number of arguments, expected one integer"
    exit 1
fi
i=$1
while [ $i -gt 0 ];
do
    echo "Hello again!"
    i=$(expr $i - 1)
done
```

Save with Ctrl+O and Enter, and exit with Ctrl+X.

The first line specifies which shell to be used in the script, and the path to where it is located. Then the commands follow, following the syntax of the chosen shell. In this case we see an example of an if-statement and an example of a while loop. There is also the usage of an argument that is passed to the script, and assignment and usage of variables.

| Command | Description |
|---|---|
| `chmod +x testScript.sh` | Make it possible to run the script. |
| `./testScript.sh 2` | Run the script with the argument `2`. Try also other numbers, and no number. |
| `rm testScript.sh` | Clean up by removing the script. |

### The ~/.bashrc file

The file `~/.bashrc` (where `~` is short for `$HOME`) is used to do some initializations every time a new terminal window is opened. It is said that the file is "sourced" when a new terminal window is opened. The file can thus be used to set environment variables, aliases, and execute some bash code every time a new terminal window is opened. Those environment variables and aliases are therefore exactly the same in all terminal windows that are opened, as long as `~/.bashrc` is not modified between the opening of two terminal windows.

There are already important things in `~/.bashrc`, for example the line that activates OpenFOAM. Therefore, we first make a backup copy of it, and restore it at the end.

| Command | Description |
|---|---|
| `cp ~/.bashrc ~/.bashrc.backup` | Make a backup copy of `~/.bashrc`. |
| `echo "export MYENV=dummyEnv" >> ~/.bashrc` | Add to `~/.bashrc` a definition of an environment variable `MYENV`, with the value `dummyEnv`, so that it is defined in each terminal window that is opened at a later stage.<br>It is important that `>>` is used, so that the line is APPENDED to the file. A single `>` would overwrite the file!<br>Test by opening a new terminal window and typing:<br>&nbsp;&nbsp;`echo $MYENV` |
| `echo "alias lsl='ls -l'" >> ~/.bashrc` | Add to `~/.bashrc` a definition of an alias `lsl`, which does `ls -l` when executed, so that it is defined in each terminal window that is opened at a later stage.<br>Test by opening a new terminal window and typing:<br>&nbsp;&nbsp;`lsl` |
| `tail ~/.bashrc` | See the two lines that you added at the end of the file. |
| `mv ~/.bashrc.backup ~/.bashrc` | Restore the original `~/.bashrc`, which removes the two lines again.<br>Test by opening a new terminal window and typing:<br>&nbsp;&nbsp;`echo $MYENV`<br>&nbsp;&nbsp;`lsl`<br>Nothing is printed by the first command, and the second command is not found. |

Sourcing a file is similar (but different) to executing a file. Read more at [What is the difference between executing a Bash script vs sourcing it?](https://superuser.com/questions/176783/what-is-the-difference-between-executing-a-bash-script-vs-sourcing-it)

## File modes and how to modify them

We will here practice how to determine and change the modes of files (and directories, which is done the same way).

| Command | Description |
|---|---|
| `mkdir -p testDir0/testDir1; touch testDir0/testFile` | Create a directory with a directory and a file in it. |
| `ls -l testDir0` | List the properties and modes of the files and directories in the `testDir0` directory.<br>Depending on how your environment is set up, the modes of the file and directory may differ. You may get, for example:<br>&nbsp;&nbsp;`drwxr-xr-x 2 <username> <username> 4096 Nov 11 14:03 testDir1`<br>&nbsp;&nbsp;`-rw-r--r-- 1 <username> <username>    0 Nov 11 14:03 testFile`<br>A `d` as the first character says that it is a directory.<br>The following 9 characters are grouped into 3x3 characters:<br>* An `r` in the first position of each group says that the file/directory is readable.<br>* A `w` in the second position of each group says that the file/directory is writeable.<br>* An `x` in the third position of each group says that the file/directory is executable.<br>A directory must be executable to make it possible to enter it.<br>The first group of 3 characters is for the owner of the file/directory.<br>The second group of 3 characters is for a group (can have the same name as the owner).<br>The third group of 3 characters is for others.<br>In the example above, the owner is `<username>` (the first name on each line), and the group is `<username>` (the second name on each line). |
| `chmod u+x testDir0/testFile` | Change the mode of the file so that it is executable by the owner (check with `ls -l testDir0`):<br>&nbsp;&nbsp;`-rwxr--r-- 1 <username> <username> 0 Nov 11 14:03 testFile`<br>Note that the command only adds the first `x`. Everything else is the same as before the command was executed. |
| `chmod g+w testDir0/testFile` | Change the mode of the file so that it is writeable by the group:<br>&nbsp;&nbsp;`-rwxrw-r-- 1 <username> <username> 0 Nov 11 14:03 testFile` |
| `chmod o+rwx testDir0/testFile` | Change the mode of the file so that it is readable, writeable, and executable by others:<br>&nbsp;&nbsp;`-rwxrw-rwx 1 <username> <username> 0 Nov 11 14:03 testFile` |
| `chmod go-rwx testDir0/testFile` | Change the mode of the file so that it is neither readable, writeable, nor executable by the group or others:<br>&nbsp;&nbsp;`-rwx------ 1 <username> <username> 0 Nov 11 14:03 testFile` |
| `rm -r testDir0` | Clean up by removing the `testDir0` directory. |

The default modes of new files and directories are set by the `umask` command.

| Command | Description |
|---|---|
| `umask` | Report the current setting of the default modes, typically `0022`. Google the meaning of the numbers that are reported. It is too much for this tutorial. |
| `umask 077; touch privateFile; ls -l privateFile` | With an umask of `077`, new files and directories are only for you. The file gets the mode `-rw-------`. The setting only applies to the current terminal window, and old files keep their modes. |
| `umask 022; rm privateFile` | Restore the default setting, and clean up. |

## Regular expressions

It is really useful to know regular expressions. Below are some examples, but please also Google.

Regular expressions are special characters (or combinations of characters) that are used to represent parts of strings.

Strictly, the `ls` examples below use the wildcards of the shell (`?`, `*`, `[...]`) and brace expansion (`{...}`), which are similar to regular expressions. The `grep` examples use regular expressions. Note that `*` means "any string" in the shell, but "the previous character, any number of times" in a regular expression. Therefore `.*` (any character, any number of times) is used in the last `grep` example.

| Command | Description |
|---|---|
| `mkdir regexpTests; cd regexpTests` | Create a directory for some tests and go there. |
| `touch myFile my1File myFile1 myFile2 myFile3;`<br>`touch myFirstFile mySecondFile;`<br>`touch yourFile yourFile1` | Create some files to play with. |
| `ls myFile?` | The `?` matches any single character, so the command lists files starting with `myFile` followed by a single character. |
| `ls my*File` | The `*` matches any string, so the command lists files starting with `my` and ending with `File`, with any number of characters between (including zero). |
| `ls *File` | The `*` can be put anywhere. The command lists all files starting with anything (including nothing) and ending with `File`. |
| `ls my*?File` | The `?` makes sure that there must be at least one character, but the `*` allows additional characters. |
| `ls myFile[2-3]` | List files starting with `myFile` and ending with a single character that is a digit between 2 and 3. |
| `ls myFile{1,3}` | List files starting with `myFile` and ending with either `1` or `3`. |
| `ls my{1,First}*` | List files starting with `my`, followed by `1` or `First`, followed by any string (including no string). |
| `printf "firstLine\nsecondLine\n\nfourthLine\nNotfirst\nfirst" > myFile` | Add some lines (and one empty line) to `myFile`, for preparation. |
| `grep -c first myFile` | Count the number of lines with the string `first`. |
| `grep -c ^first myFile` | Count the number of lines *starting with* (`^`) `first`. |
| `grep -c ^first$ myFile` | Count the number of lines containing only `first`, i.e. starting with (`^`) and ending with (`$`) it. |
| `grep -c '[sN]' myFile` | Count the number of lines containing `s` and/or `N`. |
| `grep -c '\<first' myFile` | Count the number of lines with words starting with `first`. |
| `grep -c 'first\>' myFile` | Count the number of lines with words ending with `first`. |
| `grep -c '\<first\>' myFile` | Count the number of lines with the word `first` (not as part of a word, but as a separate word). |
| `grep -c '\<.....Line' myFile` | Count the number of lines with words starting with five characters and continuing with `Line`. |
| `grep -c '\<f.......e\>' myFile` | Count the number of lines with words starting with `f`, followed by seven characters, and ending with `e`. |
| `grep -c '\<f.*e\>' myFile` | Count the number of lines with words starting with `f`, followed by any number of characters (including zero), and ending with `e`. |
| `cd ..; rm regexpTests/my*File` | Remove all files in the `regexpTests` directory starting with `my` and ending with `File`. |
| `rm -r regexpTests` | Clean up. |

## Clean up

In case you missed to remove something during the tutorial, these commands remove everything that was created. Nothing happens if it was already removed.

| Command | Description |
|---|---|
| `cd; rm -rf linuxTutorial liTest myLs testScript.sh testDir0 privateFile regexpTests` | Go to your home directory and remove all files and directories that were created in the tutorial. The `-f` flag makes `rm` silent if something is not found. Be careful with `rm -rf`, since it removes things without asking! |
| `pkill sleep` | Kill all `sleep` processes that you may have left running in background. |
| `sed -i '/^export MYENV=dummyEnv$/d; /^alias lsl=/d' ~/.bashrc; rm -f ~/.bashrc.backup` | Remove the two test lines from `~/.bashrc`, in case you did not restore it, and remove the backup copy. |
| `sudo apt remove tree` | Uninstall the `tree` command, if you do not want to keep it. |
| `exit` | Close the terminal window. Environment variables, aliases, and the `umask` setting that you set in the terminal window are forgotten. |

## Recovering the ~/.bashrc file

Ubuntu keeps a fresh copy of the original `.bashrc` file in `/etc/skel`. If your `~/.bashrc` has been removed or destroyed, you can restore it from there. Note that it is a fresh file, without anything that was added to `~/.bashrc` later, for example the line that activates OpenFOAM.

| Command | Description |
|---|---|
| `diff /etc/skel/.bashrc ~/.bashrc` | Show the differences between the fresh file and your current `~/.bashrc`. Lines starting with `>` are only in your current file, i.e. things that have been added to it. Lines starting with `<` are only in the fresh file. Nothing is printed if the files are the same. Save any lines that you want to keep. |
| `cp -b /etc/skel/.bashrc ~/.bashrc` | Replace your `~/.bashrc` with the fresh copy. The `-b` flag makes `cp` keep a backup copy of your previous `~/.bashrc`, named `~/.bashrc~`. If necessary, you can recover the previous version with:<br>&nbsp;&nbsp;`mv ~/.bashrc~ ~/.bashrc` |
| `echo 'source /usr/lib/openfoam/openfoam2606/etc/bashrc' >> ~/.bashrc` | Add the line that activates OpenFOAM again, as in [01_Install_OpenFOAM-v2606_WSL.md](01_Install_OpenFOAM-v2606_WSL.md). Add any other lines that you saved in the same way. Open a new terminal window to use the restored file. |

## Next

Now you can continue with [04_The_OpenFOAM_flange_tutorial.md](04_The_OpenFOAM_flange_tutorial.md).

---

© 2026 Håkan Nilsson. Licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
