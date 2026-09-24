#!/usr/bin/env python
# -*- coding: utf8 -*-
## \package cloudy_tools.simulation Running Cloudy and locating its output files.

import subprocess
from . import utils as ut
from .params import readCommand

# -----------------------------------------------------------------

## An instance of CloudySimulation represents a single Cloudy run: an input (.in) file plus the various
# "save" files it produces, all sharing the same stem and residing in the same directory. Mirrors the role
# of PTS's Simulation class, but for a single 1D Cloudy model rather than a SKIRT run.
class CloudySimulation:

	## Construct a CloudySimulation for the input file at the given path (interpreted as described for
	# cloudy_tools.utils.absPath()). The file need not exist yet if this instance will be used to run Cloudy.
	def __init__(self, inFilePath):
		self._path = ut.absPath(inFilePath)
		if self._path.suffix.lower() != ".in":
			raise ValueError("Cloudy input file must have a '.in' extension")

	## Returns the absolute path of the input (.in) file.
	def inFilePath(self):
		return self._path

	## Returns the absolute path of the directory containing the input file and its "save" output files.
	def outDirPath(self):
		return self._path.parent

	## Returns the stem of the input filename (without directory or ".in" extension).
	def prefix(self):
		return self._path.stem

	## Runs Cloudy on this simulation's input file, feeding it to the executable on stdin as usual for Cloudy
	# (invoking "cloudy" on the PATH, unless a different executable path is given). Combined stdout/stderr is
	# captured to a "<prefix>.out" file next to the input file. Raises an error if Cloudy exits with a
	# nonzero status. Returns the path to the captured output log.
	def run(self, executable="cloudy"):
		outFilePath = self._path.with_suffix(".out")
		with open(self._path) as infile, open(outFilePath, "wt") as outfile:
			result = subprocess.run([executable], stdin=infile, stdout=outfile, stderr=subprocess.STDOUT,
									 cwd=self.outDirPath())
		if result.returncode != 0:
			raise RuntimeError("Cloudy exited with status {} -- see {}".format(result.returncode, outFilePath))
		return outFilePath

	## Returns the absolute path to a "save" output file with the given filename (exactly as specified in the
	# corresponding "save ..." command of the input file). Raises an error if the file does not exist.
	def outFilePath(self, filename):
		path = self.outDirPath() / filename
		if not path.exists():
			raise ValueError("Cloudy output file not found: {}".format(path))
		return path

	def readCommand(self, keyword):
		return readCommand(self.inFilePath(), keyword)

# -----------------------------------------------------------------
