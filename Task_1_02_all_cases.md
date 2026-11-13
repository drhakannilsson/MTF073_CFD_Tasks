# Run all Task 1 cases in OpenFOAM

The folder `Task_1_OpenFOAM` contains scripts that set up, run and post-process the 40 cases of Task 1 in OpenFOAM. All cases are created from a single base case, set up in the same way as the case in [Task_1_01_OpenFOAM_tutorial.md](Task_1_01_OpenFOAM_tutorial.md). The results are shown as figures and numbers in the same order as in the Task 1 report template, so that you can compare them with the results of your own Python code.

The scripts are described in detail in [Task_1_OpenFOAM/README.md](Task_1_OpenFOAM/README.md). Below are the steps to get started.

## Step 1: Get the files

In the **Ubuntu** terminal, download all files of the course project to your home directory:

```
cd
git clone https://github.com/drhakannilsson/MTF073_CFD_Tasks.git
```

This creates the directory `~/MTF073_CFD_Tasks`. The scripts for Task 1 are in `~/MTF073_CFD_Tasks/Task_1_OpenFOAM`.

When the files have been updated, get the latest version with:

```
cd ~/MTF073_CFD_Tasks
git pull
```

## Step 2: Install the Python packages

In the **Ubuntu** terminal, install NumPy and Matplotlib, which are used for the post-processing:

```
sudo apt install -y python3-numpy python3-matplotlib
```

## Step 3: Run a case

In the **Ubuntu** terminal, first make sure that OpenFOAM is sourced (activated):

```
foamVersion
```

This should print `OpenFOAM-v2606`. It is automatic with the installation in [01_Install_OpenFOAM-v2606_WSL.md](01_Install_OpenFOAM-v2606_WSL.md).

Then set up, run and post-process case 5:

```
cd ~/MTF073_CFD_Tasks/Task_1_OpenFOAM
./t1foam.py 5
```

The case is run on four meshes. The first run takes a little longer, since some code is compiled.

Run your own case by changing the number. Show all options with:

```
./t1foam.py -h
```

## Step 4: Look at the results

In Windows File Explorer, go to `MTF073_CFD_Tasks\Task_1_OpenFOAM\results` in your Ubuntu home directory (see [01_Install_OpenFOAM-v2606_WSL.md](01_Install_OpenFOAM-v2606_WSL.md#find-your-linux-files-in-windows)), and double-click `index.html`. It opens in your web browser, with a table of all post-processed cases. Click on a case, e.g. *Case 5*, to see its results. The case page has links at the top: *All cases* goes back to the table, and the others go to each section of the results (*1 Case*, *3 Validation*, *4–5 Results & convergence*, *5.1 Equi vs nonequi* and *6 Mesh study*). The section numbers are those of the Task 1 report template. When you run more cases, they are added to the table. If the page is already open in your web browser, reload it (F5) to see the new results.

The OpenFOAM cases are in `Task_1_OpenFOAM/runs`, with one directory per case and mesh. Each of them has a `.foam` file, e.g. `runs/Case_05/nonequi_20x20/nonequi_20x20.foam`. Open it in ParaView as described in [02_Install_ParaView_Windows.md](02_Install_ParaView_Windows.md).

## Clean up

In the **Ubuntu** terminal, remove everything that was generated:

```
cd ~/MTF073_CFD_Tasks/Task_1_OpenFOAM
./Allclean
```

---

© 2026 Håkan Nilsson. Licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
