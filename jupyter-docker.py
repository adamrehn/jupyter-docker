#!/usr/bin/env python3
import json, math, os, subprocess, sys, shutil, tempfile, time

# Utility functionality
class Util:
	
	# Determines if a command can successfully be run
	@staticmethod
	def commandExists(command):
		try:
			proc = subprocess.Popen(command)
			proc.communicate(None)
			return True
		except:
			return False
	
	# Retrieves the current user's home directory
	@staticmethod
	def homeDir():
		if sys.platform == 'win32':
			return os.environ['HOMEDRIVE'] + '/' + os.environ['HOMEPATH']
		return os.environ['HOME']

	# Writes a string to a file
	@staticmethod
	def writeFile(filename, data):
		with open(filename, 'w') as f:
			f.write(data)
	
	# Writes a string to a file, applying the specified replacements
	@staticmethod
	def writePatches(filename, data, replacements):
		patched = data
		for key in replacements:
			patched = patched.replace(key, replacements[key])
		Util.writeFile(filename, patched)
	
	# Retrieves the host port bound to the specified container port,
	# and opens it in the user's default web browser
	@staticmethod
	def discoverPortAndOpen(containerName, port):
		
		# Use `docker port` to determine which host port was bound to the container port
		result = subprocess.run(
			[DOCKER_COMMAND, 'port', containerName, str(port)],
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			universal_newlines=True
		)
		hostAddress = result.stdout.strip()
		
		# Launch the user's web browser to display the service running on the port
		openCommand = 'xdg-open' if IS_LINUX else 'open'
		subprocess.Popen([openCommand, 'http://' + hostAddress])

# The template code for our Dockerfile
DOCKERFILE_TEMPLATE = '''FROM __UPSTREAM_IMAGE__

# Install native compilers
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	gfortran && \
rm -rf /var/lib/apt/lists/*

# Install the `add-apt-repository command`
RUN apt-get update && apt-get install -y --no-install-recommends \
	software-properties-common && \
rm -rf /var/lib/apt/lists/*

# Install GDAL
RUN add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable
RUN apt-get update && apt-get install -y --no-install-recommends \
	gdal-bin \
	python3-gdal && \
rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install \
	opencv-contrib-python \
	ipywidgets \
	pandas \
	numexpr \
	matplotlib \
	scipy \
	seaborn \
	scikit-learn \
	scikit-image \
	sympy \
	cython \
	patsy \
	statsmodels \
	cloudpickle \
	dill \
	numba \
	bokeh \
	sqlalchemy \
	h5py \
	vincent \
	beautifulsoup4 \
	xlrd

# Install OpenCV dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
	libsm6 \
	libxrender1 \
	libfontconfig1 \
	libxext-dev && \
rm -rf /var/lib/apt/lists/*

# Apply our Jupyter config file
COPY jupyter_notebook_config.py /root/.jupyter/

# Create a log directory for TensorBoard
RUN mkdir /tensorboard-log

WORKDIR /workingdir
EXPOSE 8888
'''

# The code for our Jupyter notebook configuration file
CONFIG_FILE = '''c.NotebookApp.ip = '*'
c.NotebookApp.port = 8888
c.NotebookApp.token = ''
c.NotebookApp.open_browser = False
'''

# The template code for our shell script
SCRIPT_TEMPLATE = '''#!/usr/bin/env docker-script
#!__LOCAL_IMAGE__ bash
jupyter notebook --allow-root
'''

# If we are running under Linux and NVIDIA Docker is installed, use GPU acceleration
IS_LINUX       = sys.platform.startswith('linux')
USE_GPU        = IS_LINUX and Util.commandExists(['nvidia-docker', '--version'])
IMAGE_MODIFIER = '-gpu' if USE_GPU else ''
UPSTREAM_IMAGE = 'tensorflow/tensorflow:latest' + IMAGE_MODIFIER + '-py3'
LOCAL_IMAGE    = 'jupyter-tensorflow' + IMAGE_MODIFIER
DSCRIPT_ARGS   = ['---nvidia-docker'] if USE_GPU else []
DOCKER_COMMAND = 'nvidia-docker' if USE_GPU else 'docker'

# If no explicit command is specified, default to 'run'
DEFAULT_COMMAND = 'run'
command = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_COMMAND

# If the user specified the TensorBoard argument, accept it with or without 'run'
startTensorboard = False
tbArgs = ['t', 'tb', 'tboard', 'tensorboard']
if command.strip('-') in tbArgs:
	command = DEFAULT_COMMAND
	startTensorboard = True
elif len(sys.argv) > 2 and sys.argv[2].strip('-') in tbArgs:
	startTensorboard = True

# Carry out the specified command

# Builds the docker image
if command == 'install':
	tempDir = tempfile.mkdtemp()
	
	Util.writePatches(tempDir + '/Dockerfile', DOCKERFILE_TEMPLATE, {'__UPSTREAM_IMAGE__': UPSTREAM_IMAGE})
	Util.writeFile(tempDir + '/jupyter_notebook_config.py', CONFIG_FILE)
	subprocess.call([DOCKER_COMMAND, 'build', '-t', LOCAL_IMAGE, '.'], cwd=tempDir)
	shutil.rmtree(tempDir)
	print('Docker image built successfully.')
	
# Runs the docker image
elif command == 'run':
	
	# Create the shell script in the user's home directory
	scriptDir = Util.homeDir() + '/.jupyter-docker'
	scriptPath = scriptDir + '/jupyter.sh'
	if os.path.exists(scriptDir) == False:
		os.mkdir(scriptDir)
	Util.writePatches(scriptPath, SCRIPT_TEMPLATE, {'__LOCAL_IMAGE__': LOCAL_IMAGE})
	
	# Launch docker-script as a child process
	containerName = 'jupyter_docker_' + str(math.floor(time.time()))
	jupyter = subprocess.Popen([
		'docker-script',
		scriptPath,
		'---name=' + containerName,
		'---arg=-P',
	] + DSCRIPT_ARGS)
	
	# Wait briefly for the server to start
	time.sleep(2)
	
	# Launch the user's web browser to display the Jupyter Notebook index page
	Util.discoverPortAndOpen(containerName, 8888)
	
	# If we are running TensorBoard in addition to Jupyter, start it as well
	if startTensorboard == True:
		
		# Start TensorBoard and wait briefly for it to start
		tensorboard = subprocess.Popen([DOCKER_COMMAND, 'exec', containerName, 'tensorboard', '--logdir', '/tensorboard-log'])
		time.sleep(2)
		
		# Open TensorBoard in the user's web browser as well
		Util.discoverPortAndOpen(containerName, 6006)
	
	# Wait for the container to finish running
	jupyter.communicate(None)
	print('')
	
# Displays usage syntax
elif command in ['h', 'help', '-h', '-help', '--help']:
	print('Usage syntax:')
	print(sys.argv[0] + ' install - Install the Docker image for Jupyter')
	print(sys.argv[0] + ' [run]   - Run the Docker image for Jupyter')
	print('')
	
else:
	print('Error: unsupported command "' + command + '"')
	sys.exit(1)
