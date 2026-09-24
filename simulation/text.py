#!/usr/bin/env python
# -*- coding: utf8 -*-
## \package cloudy_tools.text Reading Cloudy's tab-separated "save" output files.
#
# Cloudy's save files most often consist of a single header line starting with "#" that lists a tab-separated
# column name per column (unlike SKIRT, Cloudy does not put units in this header). loadColumns() below handles
# that common case. Several "save" types deviate from it (e.g. "save lines emissivity", whose header packs a
# label and wavelength per column, or "save species densities", whose column count depends on the model) --
# those need dedicated readers. Send example output files and we'll add functions here for each format.

import numpy as np
from . import utils as ut
from pts.simulation.units import unit as smunit

# -----------------------------------------------------------------

## This function reads a Cloudy "save"-style output file that has a single "#"-prefixed, tab-separated header
# line followed by tab-separated data rows (the format used by e.g. "save overview" and "save radius"). It
# returns a tuple (columnNames, data): columnNames is the list of column labels found on the header line (with
# the leading "#" stripped and each name trimmed of surrounding whitespace), and data is a list of 1D numpy
# arrays, one per column, in file order. Raises an error if the file's first line does not start with "#".
#
# \note Cloudy sometimes leaves a field empty for a given row/column (two consecutive tabs). Because
# np.loadtxt() (and whitespace-splitting in general) collapses consecutive delimiters, that silently shifts
# every later value in the row into the wrong column. This function instead splits each line on single tab
# characters, so an empty field is preserved as its own (empty) entry and turned into NaN, keeping every row
# aligned with the header regardless of missing values.
def loadColumns(path):
	path = ut.absPath(path)

	with open(path) as infile:
		lines = infile.readlines()
	if not lines or not lines[0].startswith("#"):
		raise ValueError("Expected a '#'-prefixed header line in Cloudy output file: {}".format(path))
	columnNames = [name.strip() for name in lines[0][1:].rstrip("\n").split("\t") if name.strip() != ""]
	numCols = len(columnNames)

	rows = []
	for line in lines[1:]:
		line = line.rstrip("\n")
		if line.strip() == "":
			continue
		fields = line.split("\t")
		# pad (some writers drop trailing empty fields) or trim to the expected column count
		if len(fields) < numCols:
			fields += [""] * (numCols - len(fields))
		elif len(fields) > numCols:
			fields = fields[:numCols]
		rows.append([float(field) if field.strip() != "" else np.nan for field in fields])

	data = np.array(rows, dtype=float).T if rows else [np.array([]) for _ in range(numCols)]
	return columnNames, list(data)

## Convenience wrapper around loadColumns() that returns a dict mapping each column name to its numpy data
# array instead of two separate lists.
def loadColumnsDict(path):
	names, data = loadColumns(path)
	return dict(zip(names, data))

# -----------------------------------------------------------------

## This function writes a SKIRT/PTS-format column text file -- the same "# column N: description (unit)"
# header format that pts.simulation.text.loadColumns() reads, and with the same call signature as
# pts.simulation.text.saveColumns(). Use this version instead of that one when the columns being written do
# not all share the same physical dimension (e.g. a wavelength column in Ryd next to a flux column in W/m3):
# pts' own saveColumns() converts each column individually but then combines them with np.stack() on the raw
# Quantity objects, which requires a single common unit across the whole stacked array and therefore raises
# a UnitConversionError as soon as two columns have different dimensions. This version instead extracts each
# column's numeric value (in its target unit, via to_value()) before stacking, so mixed dimensions are fine.
def saveColumns(path, quantities, units, descriptions, *, title=None, fmt="%1.9e"):
	path = ut.absPath(path)
	descriptions = [s.strip() for s in descriptions.split(",")]
	units = [s.strip() for s in units.split(",")]
	if len(quantities) != len(units) or len(quantities) != len(descriptions):
		raise ValueError("Number of units or descriptions does not match number of quantities")

	columns = [quantity.to_value(smunit(unit)) for quantity, unit in zip(quantities, units)]

	with open(path, "wt") as outfile:
		if title:
			outfile.write("# {}\n".format(title))
		for col, (description, unit) in enumerate(zip(descriptions, units)):
			outfile.write("# column {}: {} ({})\n".format(col + 1, description, unit))
		np.savetxt(outfile, np.array(columns).T, fmt=fmt)

# -----------------------------------------------------------------