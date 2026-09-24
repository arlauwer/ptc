#!/usr/bin/env python
# -*- coding: utf8 -*-
## \package cloudy_tools.utils Small helper functions shared across the package.

from pathlib import Path
import astropy.units as u

# -----------------------------------------------------------------

# Cloudy and SKIRT both label the Rydberg energy unit "Ryd" in their file headers, but astropy only
# recognizes the spelling "Ry". Register "Ryd" as an alias so any u.Unit("Ryd") / quantity.to(smunit("Ryd"))
# call -- e.g. inside pts' own saveColumns()/loadColumns() -- parses correctly. This runs once, on import.
try:
	u.Unit("Ryd")
except ValueError:
	u.add_enabled_units([u.def_unit("Ryd", u.Ry)])

# -----------------------------------------------------------------

## This function interprets a path relative to the current working directory, expanding "~", and returns
# the corresponding absolute Path object. Mirrors pts.utils.absPath().
def absPath(path):
	return Path(path).expanduser().resolve()

# -----------------------------------------------------------------