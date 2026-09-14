#!/usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 fred <github-fred@hidzz.com>
#
# Distributed under terms of the BSD 3-Clause license.

"""
Maidenhead Grid Square Visualization Tool

Generates a map showing worked grid squares from ADIF ham radio logs.
"""

__version__ = "0.1.7"

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Set, Tuple

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
from adif_parser import ParseADIF
from geo_ham import Rectangle, grid2rectangle
from matplotlib.collections import LineCollection
from shapely import box
from shapely.ops import unary_union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

FIELD_LON_STEP = 20  # degrees
FIELD_LAT_STEP = 10  # degrees
SQUARE_LON_STEP = 2  # degrees
SQUARE_LAT_STEP = 1  # degrees
GRID_LENGTH = 4  # 4-character grids

TITLE = 'Worked Maidenhead Grid Squares'
SIGNATURE = '(c) {} Fred W6BSD - MaidenHead Grid for {}'


class MaidenheadConverter:
  @staticmethod
  def validate(grid: str) -> bool:
    if len(grid) != GRID_LENGTH:
      return False
    return (grid[0:2].isalpha() and grid[2:4].isdigit())

  @staticmethod
  def to_coordinates(grid: str) -> Rectangle:
    return grid2rectangle(grid)


class GridMapGenerator:
  def __init__(self, figsize: Tuple[int, int] = (20, 10)):
    self.figsize = figsize
    self.fig: plt.Figure | None = None
    self.ax = None

  def create_base_map(self, lon: int = 0) -> Tuple[plt.Figure, plt.Axes]:
    self.fig = plt.figure(figsize=self.figsize)
    self.ax = self.fig.add_subplot(111, projection=ccrs.Robinson(central_longitude=lon))
    assert self.ax

    self.ax.set_global()
    self.ax.add_feature(cfeature.LAND, facecolor='lightgreen', alpha=0.2)
    self.ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.7)
    self.ax.add_feature(cfeature.COASTLINE, linewidth=1.25, edgecolor='maroon')
    self.ax.add_feature(cfeature.BORDERS, linewidth=0.75, edgecolor='gray')

    self._draw_grid_lines()
    self._draw_fine_grid()

    self.ax.set_xlabel('Longitude', fontsize=12)
    self.ax.set_ylabel('Latitude', fontsize=12)

    return self.fig, self.ax

  @staticmethod
  def _meridian_segments(lons: np.ndarray, n_samples: int = 91) -> np.ndarray:
    """Build (n_lons, n_samples, 2) array of densely-sampled meridians."""
    lats = np.linspace(-90, 90, n_samples)
    segs = np.empty((len(lons), n_samples, 2))
    segs[:, :, 0] = lons[:, None]
    segs[:, :, 1] = lats[None, :]
    return segs

  @staticmethod
  def _parallel_segments(lats: np.ndarray, n_samples: int = 2) -> np.ndarray:
    """Build (n_lats, n_samples, 2) array of parallels."""
    lons = np.linspace(-180, 180, n_samples)
    segs = np.empty((len(lats), n_samples, 2))
    segs[:, :, 0] = lons[None, :]
    segs[:, :, 1] = lats[:, None]
    return segs

  def _draw_grid_lines(self) -> None:
    assert self.ax
    lons = np.arange(-180, 181, FIELD_LON_STEP)
    lats = np.arange(-90, 91, FIELD_LAT_STEP)

    meridians = self._meridian_segments(lons)
    lc = LineCollection(meridians, colors='blue', linewidths=0.75,
                        alpha=0.5, transform=ccrs.PlateCarree())
    self.ax.add_collection(lc)

    parallels = self._parallel_segments(lats)
    linewidths = np.where(lats == 0, 1.5, 0.75)
    lc = LineCollection(parallels, colors='blue', linewidths=linewidths,
                        alpha=0.5, transform=ccrs.PlateCarree())
    self.ax.add_collection(lc)

    for lon_val in lons:
      # Skip the last one to avoid overlap
      if lon_val != 180:
        self.ax.text(lon_val, 92, f'{lon_val}°', ha='center', va='bottom',
                     fontsize=8, color='black', alpha=0.8,
                     transform=ccrs.PlateCarree())

    for lat_val in lats:
      # Skip the top one to avoid overlap
      if lat_val != 90:
        self.ax.text(-182, lat_val + 2, f'{lat_val}°', ha='right', va='center',
                     fontsize=8, color='black', alpha=0.8,
                     transform=ccrs.PlateCarree())

  def _draw_fine_grid(self) -> None:
    assert self.ax
    lons = np.arange(-180, 181, SQUARE_LON_STEP)
    lats = np.arange(-90, 91, SQUARE_LAT_STEP)

    meridians = self._meridian_segments(lons)
    lc = LineCollection(meridians, colors='grey', linewidths=0.3,
                        alpha=0.5, transform=ccrs.PlateCarree())
    self.ax.add_collection(lc)

    parallels = self._parallel_segments(lats)
    lc = LineCollection(parallels, colors='grey', linewidths=0.3,
                        alpha=0.5, transform=ccrs.PlateCarree())
    self.ax.add_collection(lc)

  def highlight_grids(self, grids: Set[str], color: str = '#880000') -> None:
    assert self.ax
    valid = [g for g in grids if MaidenheadConverter.validate(g)]
    for g in grids - set(valid):
      logger.warning("Invalid grid square '%s' skipped", g)

    if not valid:
      return

    rects = [MaidenheadConverter.to_coordinates(g) for g in valid]
    bounds = np.array([(r.lon_min, r.lat_min, r.lon_max, r.lat_max) for r in rects])

    geoms = box(bounds[:, 0], bounds[:, 1], bounds[:, 2], bounds[:, 3])
    merged = unary_union(geoms)

    self.ax.add_geometries(merged, crs=ccrs.PlateCarree(), facecolor=color,
                           edgecolor=None, alpha=0.6, zorder=20)

  def save(self, call: str, title: str, filename: str, dpi: int = 300) -> None:
    assert self.ax
    year = datetime.now().year
    # Set title
    self.ax.set_title(f'{call} - {title}', fontsize=16, weight='bold', pad=20)

    if self.fig is None:
      raise ValueError("No map created. Call create_base_map() first.")

    self.fig.text(.13, .09, SIGNATURE.format(year, call), fontsize=8, color='gray')
    self.fig.text(.13, .11, 'Map source Natural Earth',  fontsize=8, color='gray')
    self.fig.savefig(filename, dpi=dpi, bbox_inches='tight', pad_inches=0.6)
    logger.info("Map saved as '%s'", filename)


def extract_grids_from_adif(filepath: Path) -> Set[str]:
  try:
    with filepath.open('r', errors='replace') as fd:
      adif = ParseADIF(fd)
  except FileNotFoundError as err:
    logger.error(err)
    raise

  grids = set()
  for qso in adif.contacts:
    if (grid := qso.get('GRIDSQUARE')) and isinstance(grid, str):
      # Extract first 4 characters
      grid = grid[:GRID_LENGTH].upper()
      if MaidenheadConverter.validate(grid):
        grids.add(grid)
      else:
        logger.warning("Invalid grid square '%s' for %s skipped", grid, qso['CALL'])

  logger.info("Extracted %d unique grid squares from %s", len(grids), filepath.name)
  return grids


def main():
  parser = argparse.ArgumentParser(description='Maidenhead gridsquare map')
  parser.add_argument('-a', '--adif-file', type=Path, required=True,
                      help='ADIF log filename')
  parser.add_argument('-o', '--output', type=Path, required=True,
                      help='png output filename')
  parser.add_argument('-c', '--call', required=True,
                      help='Operator\'s call sign')
  parser.add_argument('-t', '--title', default=TITLE,
                      help='Title of the map')
  parser.add_argument('-d', '--dpi', type=int, default=100,
                      help='Image resolution')
  parser.add_argument('-l', '--longitude', type=int, default=0,
                      help='Center the map around a specific longitude (default %(default)s)')
  parser.add_argument('-v', '--version', action='version', version=__version__)

  opts = parser.parse_args()
  call = opts.call.upper()

  # Extract grids from ADIF
  grids = extract_grids_from_adif(opts.adif_file)

  # Generate map
  generator = GridMapGenerator(figsize=(20, 10))
  generator.create_base_map(opts.longitude)

  # Highlight worked grids
  generator.highlight_grids(grids)

  # Save map
  generator.save(call, opts.title, opts.output, opts.dpi)


if __name__ == "__main__":
  main()
