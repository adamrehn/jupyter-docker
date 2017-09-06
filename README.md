Docker Launcher for Jupyter Notebook
====================================

This tool automates the process of building and running [Docker](https://www.docker.com/) images for [Jupyter Notebook](http://jupyter.org/). The generated images contain all of the Python libraries from the [Jupyter Notebook Data Science Stack](https://hub.docker.com/r/jupyter/datascience-notebook/), as well as Python 3.x bindings for the following libraries:

- [TensorFlow](https://www.tensorflow.org/)
- [OpenCV](http://opencv.org/)
- [GDAL](http://www.gdal.org/)

When running under Linux, the launcher will detect if [NVIDIA Docker](https://github.com/NVIDIA/nvidia-docker) is installed and use GPU acceleration when available.


Requirements
------------

For the launcher to run, [docker-script](https://github.com/adamrehn/docker-script) needs to be installed and exist in the system PATH.


Usage
-----

To build the Docker image for Jupyter, run:

```
python3 ./jupyter-docker.py install
```

To start the Jupyter Notebook server in the current working directory, run:

```
python3 ./jupyter-docker.py
```

The launcher will automatically identify the host port that Docker binds to the Jupyter HTTP port, and open the server's index page in the user's default web browser.
