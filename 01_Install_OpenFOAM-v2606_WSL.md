# Install OpenFOAM-v2606 in Windows WSL (with Ubuntu)

These steps install OpenFOAM-v2606 (openfoam.com) as a ready-made package in Ubuntu 24.04, running in WSL (Windows Subsystem for Linux) on Windows. You need Windows 10 (version 22H2) or Windows 11, administrator rights, at least 8 GB of RAM, hardware virtualization enabled in the BIOS/UEFI (it usually is), and about 5 GB of free disk space.

The official installation instructions are found at [www.openfoam.com](https://www.openfoam.com). The instructions below are collected here for convenience.

Feel free to try this out: the end of this document explains how to remove OpenFOAM, Ubuntu and WSL completely, leaving Windows as it was.

Commands marked **PowerShell** are typed in Windows PowerShell, opened as administrator (right-click the Start button → *Terminal (Admin)* or *Windows PowerShell (Admin)*). Commands marked **Ubuntu** are typed in the Ubuntu terminal.

## Background information

OpenFOAM runs natively in Linux. On a Windows computer the best option is to install WSL (Windows Subsystem for Linux) with Ubuntu as the Linux operating system. You will be handling and running OpenFOAM through a Linux terminal window. The results can be viewed and analyzed through Windows.

There are other options for installing OpenFOAM, found at [www.openfoam.com](https://www.openfoam.com).

The optimal way to work with OpenFOAM is on a Linux computer. But the installation presented here is great for getting started and also for reaching quite far in your OpenFOAM experience.

## Step 1: Install WSL and Ubuntu

1. In **PowerShell** (as administrator), run:

   ```
   wsl --install -d Ubuntu-24.04
   ```

   If it can't find that version of Ubuntu, pick a version that is available from the following command:

   ```
   wsl --list --online
   ```

2. Restart the computer when/if asked.
3. Ubuntu opens by itself in a terminal window after the restart (otherwise start *Ubuntu 24.04* from the Start menu). Choose a username and password when asked. They don't need to be the same as for Windows. Remember the password: it is needed for `sudo` commands below.
4. In **Ubuntu**, update the system:

   ```
   sudo apt update
   sudo apt upgrade -y
   ```

## Step 2: Install OpenFOAM-v2606

In **Ubuntu**, run:

```
curl https://dl.openfoam.com/add-debian-repo.sh | sudo bash
```

You might have to type your Ubuntu password. Then type:


```
sudo apt update
sudo apt install -y openfoam2606-default
```

Then make sure that OpenFOAM activates automatically when a new terminal window is opened, by typing:

```
echo 'source /usr/lib/openfoam/openfoam2606/etc/bashrc' >> ~/.bashrc
```

The file that is modified in the above command is used to set up the Linux environment when a new terminal window is opened. Terminal windows that were open when the file was changed are not affected. To continue in the same terminal window and make sure that the OpenFOAM environment is available you must also type:

```
source ~/.bashrc
```

When you open new terminal windows OpenFOAM will automatically be activated, so you should not type the above command(s) again.

**Note:** If you want to install several OpenFOAM versions, do not activate them automatically. Instead create one alias per version, for example `alias of2606='source /usr/lib/openfoam/openfoam2606/etc/bashrc'` in `~/.bashrc`, and type the alias in a terminal window to activate that version. This way only one OpenFOAM version is active in each terminal window. Do not switch between versions in a terminal window; open a new terminal window for each version instead.

## Step 3: Test the installation

In **Ubuntu**, check the version:

```
foamVersion
```

This should print `OpenFOAM-v2606`.

Then run the cavity tutorial:

```
mkdir -p $FOAM_RUN
cp -r $FOAM_TUTORIALS/incompressible/icoFoam/cavity/cavity $FOAM_RUN
cd $FOAM_RUN/cavity
blockMesh
icoFoam
```

The installation works if the output in the terminal ends with the line `End`.

You will learn how to visualize the results later.

## Editing files

Edit files in the **Ubuntu** terminal window with `nano`, for example:

```
nano system/controlDict
```

Save with Ctrl+O and Enter, and exit with Ctrl+X. You can see other commands at the bottom of the `nano` window, where `^` refers to Ctrl.

## Find your Linux files in Windows

In Windows File Explorer, click *Linux* (the penguin) at the bottom of the left panel. Then open *Ubuntu-24.04 > home > \<username\>*. This is your Ubuntu home directory, and your cases are in `OpenFOAM` there.

If you edit or create Linux files from Windows, use Notepad or VS Code with the *WSL* extension. In VS Code, click the remote button in the bottom-left corner (you might have to close down any current remote connection first), select *Connect to WSL*, and open your folder with *File > Open Folder*. Other Windows programs, such as Word, can save the files in a format that OpenFOAM and Linux do not read correctly.

Keep your cases in Ubuntu (in `~`), not on the Windows drives (under `/mnt/c`). OpenFOAM runs much slower there.

## Updates

In **Ubuntu**, run now and then:

```
sudo apt update
sudo apt upgrade -y
```

This also installs updates of OpenFOAM-v2606.

## Common problems

| Problem | Fix |
|---|---|
| *Ubuntu 24.04* is not in the Start menu after the restart | In **PowerShell**, run `wsl --update` and then `wsl --install -d Ubuntu-24.04`. |
| `foamVersion: command not found` | Open a new Ubuntu terminal. |
| OpenFOAM runs very slowly | The case is under `/mnt/c`. Move it to `~`. |

## Remove OpenFOAM

In **Ubuntu**, run:

```
sudo apt remove --purge -y openfoam2606-default
sudo apt autoremove --purge -y
sudo rm /etc/apt/sources.list.d/openfoam.list
sed -i '/openfoam2606/d' ~/.bashrc
```

Your case files in `$HOME/OpenFOAM` are kept. Delete them with `rm -rf ~/OpenFOAM` if you no longer need them.

## Remove Ubuntu

This deletes Ubuntu and **all files inside it**. Copy files you want to keep to Windows first, with File Explorer (see [Find your Linux files in Windows](#find-your-linux-files-in-windows)).

In **PowerShell**, run:

```
wsl --unregister Ubuntu-24.04
```

Then open *Settings > Apps > Installed apps*, find *Ubuntu 24.04*, and select *Uninstall* (if it is listed).

## Remove WSL

First remove Ubuntu (previous section). Then, in **PowerShell** (as administrator), run:

```
wsl --uninstall
```

Finally, open *Turn Windows features on or off*, untick *Windows Subsystem for Linux* and *Virtual Machine Platform*, select *OK*, and restart the computer.

## Next

Now you can continue with [02_Install_ParaView_Windows.md](02_Install_ParaView_Windows.md).

---

© 2026 Håkan Nilsson. Licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
