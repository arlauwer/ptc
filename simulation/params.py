#!/usr/bin/env python
# -*- coding: utf8 -*-
## \package cloudy_tools.params Reading command values back out of a Cloudy input (.in) file.

import re
from dataclasses import dataclass
import astropy.units as u
from . import utils as ut

# -----------------------------------------------------------------

## Holds everything readCommand() can pull out of one Cloudy command line: the command's main \em value
# (a float if it parses as one, otherwise the raw string -- e.g. "GASS10" for "abundances GASS10"),
# whether the line ends in "linear", and, if present, the "range LOW to HIGH [unit]" clause as
# (low, high) plus the optional unit string.
@dataclass
class Command:
	value: float | str
	linear: bool = False
	range: tuple[float, float] | None = None
	unit: str | None = None

	## Returns this command's main value as an astropy Quantity: since Cloudy commands are given on a log
	# scale unless followed by "linear", this returns 10**value in that case (or plain value if linear).
	# Raises TypeError if the value is a non-numeric string (e.g. "abundances GASS10").
	@property
	def quantity(self):
		if isinstance(self.value, str):
			raise TypeError("Command value '{}' is not numeric".format(self.value))
		return self.value if self.linear else 10 ** self.value

	## Returns this command's "range LOW to HIGH" clause as a 2-element astropy Quantity, applying the same
	# log/linear and unit handling as quantity(). Raises ValueError if there is no range clause.
	@property
	def rangeQuantity(self):
		if self.range is None:
			raise ValueError("Command has no range clause")
		low, high = self.range
		if not self.linear:
			low, high = 10 ** low, 10 ** high
		return [low, high] * (u.Unit(self.unit) if self.unit else u.dimensionless_unscaled)

# Matches "<keyword> <value> [range <low> to <high> [<unit>]] [linear]", e.g. any of:
#   intensity 2 range 3.04473e-09 to 7028020.0 Ryd
#   hden 3
#   abundances GASS10
#   metals 1 linear
_COMMAND_PATTERN = re.compile(
	r"^(?P<keyword>\S+)\s+(?P<value>\S+)"
	r"(?:\s+range\s+(?P<low>[\d.eE+\-]+)\s+to\s+(?P<high>[\d.eE+\-]+)(?:\s+(?P<unit>\S+))?)?"
	r"(?:\s+(?P<linear>linear))?\s*$",
	re.IGNORECASE,
)

## This function scans a Cloudy input (.in) file for a line whose first token is the specified command
# keyword (case-insensitive), parses it with a single general-purpose regex, and returns the result as a
# Command. Handles a plain "<keyword> <value>", a "range LOW to HIGH [unit]" clause, and a trailing
# "linear", in any combination -- see the examples above _COMMAND_PATTERN. Raises an error if the command
# is not found.
#
# \note Does not handle multi-word keywords (e.g. "no molecules") -- only the first token is matched.
def readCommand(path, keyword):
	path = ut.absPath(path)
	with open(path) as infile:
		for line in infile:
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			m = _COMMAND_PATTERN.match(line)
			if m and m.group("keyword").lower() == keyword.lower():
				value = m.group("value")
				try:
					value = float(value)
				except ValueError:
					pass
				rng = (float(m.group("low")), float(m.group("high"))) if m.group("low") else None
				return Command(value=value, linear=bool(m.group("linear")), range=rng, unit=m.group("unit"))
	raise ValueError("Command '{}' not found in Cloudy input file: {}".format(keyword, path))

## Convenience wrapper returning just the numeric/string value, as the old readCommandValue() did.
def readCommandValue(path, keyword):
	return readCommand(path, keyword).value

## Convenience wrapper returning just the (low, high) range, as the old readCommandRange() did.
def readCommandRange(path, keyword):
	command = readCommand(path, keyword)
	if command.range is None:
		raise ValueError("Command '{}' has no range clause in Cloudy input file: {}".format(keyword, path))
	return command.range

## Convenience wrapper around readCommandValue() that looks up several keywords at once and returns a dict
# mapping each keyword to its value. Keywords that are not found in the file are simply omitted from the result.
def readCommandValues(path, keywords):
	values = {}
	for keyword in keywords:
		try:
			values[keyword] = readCommandValue(path, keyword)
		except ValueError:
			pass
	return values

# -----------------------------------------------------------------