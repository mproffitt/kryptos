# Kryptos method to a solution
This repository contains a potential method for solving Kryptos K4 cipher.

To run this notebook you will need a Python 3 environment with the Pandas Dataframe library, ipyevents and ipywidgets.

Alternatively, you may use the online service 'Binder' to execute the notebook.

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mproffitt/kryptos.git/master?filepath=kryptos-k4.ipynb)

If you are using Binder, please note that it may take a moment or two to start the notebook.

The main notebook here is [`index.pynb`](index.ipynb) and for now, this is the only one that will execute.

[The other notebook](kryptos-discovery.ipynb) contains a lot of my thought process over the last few weeks.

You will also find a folder of images [here](pykryptos/characters)

This contains all my original screenshots of both the cipher and lacuna executions from where I was looking for patterns
that might help me understand this cipher better. These screenshots are from the point I discovered the table and the
associated alphabets.

Some recent workings I don't have due to a poorly timed thunderstorm but I think there is enough here to understand how
I reached this point.

The kryptos-discovery notebook will not execute at the moment as it relies on code brought in from my
[pykryptos](https://github.com/mproffitt/PyKryptos/tree/feature/ISSUE-5-add-keyword-functionality) project.
Longer term I am considering merging these two projects back into PyKryptos to give a finished clock which will run in
multiple environments.
