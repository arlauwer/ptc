#!/usr/bin/env python
# -*- coding: utf8 -*-
## \package cloudy_tools.input Programmatically building Cloudy input (.in) files.

from . import utils as ut
import astropy.units as u

# -----------------------------------------------------------------

## An instance of CloudyInput represents the content of a Cloudy input (.in) file, organized into the three
# sections used throughout this toolkit's typical models: SIMULATION, INPUT and OUTPUT (matching the layout
# of the example .in files this class is meant to reproduce). Commands are accumulated with generic or
# specific helper methods, in the order they are added, and written to disk with write().
#
# Example, reproducing a typical model:
#
#     ci = CloudyInput()
#     ci.iterateUntilConvergence().sphere()
#     ci.tableSED("sed.in").radius(1e10).intensity(1e3, 1e0, 1e4).hden(1e4).abundances("GASS10").metals(1).noMolecules()
#     ci.saveOverview("sim.ovr").saveSpeciesDensities("sim.species").saveTotalOpacity("sim.opac")
#     ci.saveDiffuseContinuum("sim.emis")
#     ci.addLine("Fe25", 1.86819).addLine("Fe25", 1.859).saveLinesEmissivity("sim.lines")
#     ci.saveContinuum("sim.con").saveRadius("sim.rad").saveOpticalDepths("sim.tau")
#     ci.write("sim.in")
#
class CloudyInput:

	def __init__(self):
		self._simulation = []   # command strings for the "SIMULATION" section
		self._input = []        # command strings for the "INPUT" section
		self._output = []       # command strings for the "OUTPUT" section
		self._lines = []        # (label, wavelength) tuples for the "save lines emissivity" line list

	# ---------- generic ----------

	## Add a raw command string to the specified section ("simulation", "input" or "output"; default "input").
	# Use this for any Cloudy command not covered by one of the specific methods below.
	def add(self, command, section="input"):
		getattr(self, "_" + section).append(command)
		return self

	# ---------- SIMULATION section ----------

	def iterateUntilConvergence(self):
		return self.add("iterate until convergence", "simulation")

	def sphere(self):
		return self.add("sphere", "simulation")

	# ---------- INPUT section ----------

	def tableSED(self, filename):
		return self.add('table SED "{}"'.format(filename), "input")

	def radius(self, value, linear=True):
		return self.add("radius {} {}".format(value, "linear" if linear else "").rstrip(), "input")

	def intensity(self, value, rangeLow, rangeHigh, unit, linear=True):
		return self.add("intensity {} range {} to {} {} {}".format(
			value, rangeLow, rangeHigh, unit, "linear" if linear else "").rstrip(), "input")

	def hden(self, value, linear=True):
		return self.add("hden {} {}".format(value, "linear" if linear else "").rstrip(), "input")

	def abundances(self, name):
		return self.add("abundances {}".format(name), "input")

	def metals(self, value, linear=True):
		return self.add("metals {} {}".format(value, "linear" if linear else "").rstrip(), "input")

	def noMolecules(self):
		return self.add("no molecules", "input")

	# ---------- OUTPUT section ----------

	def saveOverview(self, filename, last=True):
		return self._save("overview", filename, last)

	def saveSpecies(self, filename, species="* temp all", last=True):
		return self._save("species densities {}".format(species), filename, last)

	def saveOpacity(self, filename, last=True):
		return self._save("total opacity", filename, last)

	def saveDiffuseContinuum(self, filename, rangeLow, rangeHigh, unit, last=True):
		return self._save("diffuse continuum", filename, last, rangeLow, rangeHigh, unit)

	def saveContinuum(self, filename, last=True):
		return self._save("continuum", filename, last)

	def saveRadius(self, filename, last=True):
		return self._save("radius", filename, last)

	def saveOpticalDepths(self, filename, last=True):
		return self._save("optical depths", filename, last)

	## Register one emission line to include in the "save lines emissivity" line list (label plus rest
	# wavelength in microns, as Cloudy expects). Call repeatedly, once per line, before saveLinesEmissivity().
	def addLine(self, label, wavelength):
		self._lines.append((label, wavelength))
		return self

	def saveLinesEmissivity(self, filename, last=True):
		return self._save("lines emissivity", filename, last)

	def _save(self, kind, filename, last, rangeLow=None, rangeHigh=None, unit=None):
		command = 'save {} "{}"'.format(kind, filename)
		if rangeLow is not None and rangeHigh is not None:
			command += " range {} to {}".format(rangeLow, rangeHigh)
			if unit is not None:
				command += " {}".format(unit)
		if last:
			command += " last"
		self._output.append(command)
		return self

	# ---------- writing ----------

	def _section(self, title, commands):
		if not commands:
			return []
		banner = "#" * 9 + " " + title + " " + "#" * 9
		return [banner, "#"] + commands + ["#"]

	## Assemble and write the complete Cloudy input file to the specified path (interpreted as described for
	# cloudy_tools.utils.absPath()), using the sectioned SIMULATION / INPUT / OUTPUT layout. The line list
	# registered via addLine(), if any, is appended right after the OUTPUT section, terminated by
	# "end of lines", as required by "save lines emissivity". Returns the absolute path written.
	def write(self, path):
		path = ut.absPath(path)
		lines = []
		lines += self._section("SIMULATION", self._simulation)
		lines += self._section("INPUT", self._input)
		lines += self._section("OUTPUT", self._output)
		if self._lines:
			for label, wavelength in self._lines:
				lines.append('"{}" {}'.format(label, wavelength))
			lines.append("end of lines")
		with open(path, "wt") as outfile:
			outfile.write("\n".join(lines) + "\n")
		return path

# -----------------------------------------------------------------

## This function writes a Cloudy "table SED" input file: two columns (x, y), with a type label following
# y on the first row only, exactly as Cloudy's "table SED" command expects (e.g. "1.0000e+00 1.0000e+00
# Flambda"). \em x and \em y must be equal-length sequences of plain numbers (Cloudy SED tables carry no
# per-column unit metadata beyond the label). \em label identifies the quantity type Cloudy should interpret
# y as (e.g. "Flambda", "nuFnu"). The path is interpreted as described for cloudy_tools.utils.absPath().
def saveSED(path, x, y, label="Flambda", fmt="{:.4e}"):
	path = ut.absPath(path)

	with open(path, "wt") as outfile:
		for i, (xi, yi) in enumerate(zip(x, y)):
			outfile.write((fmt + " " + fmt).format(xi, yi))
			outfile.write(" {}\n".format(label) if i == 0 else "\n")

# -----------------------------------------------------------------