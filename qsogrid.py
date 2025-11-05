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

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Set, Tuple

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from adif_parser import ParseADIF
from shapely.geometry import box
from shapely.ops import unary_union

Rectangle = Tuple[float, float, float, float]  # (lon_min, lat_min, lon_max, lat_max)


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Constants
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
    grid = grid.upper()

    # Longitude calculation
    lon_field = (ord(grid[0]) - ord('A')) * FIELD_LON_STEP
    lon_min = -180 + lon_field + int(grid[2]) * SQUARE_LON_STEP
    lon_max = lon_min + SQUARE_LON_STEP

    # Latitude calculation
    lat_field = (ord(grid[1]) - ord('A')) * FIELD_LAT_STEP
    lat_min = -90 + lat_field + int(grid[3]) * SQUARE_LAT_STEP
    lat_max = lat_min + SQUARE_LAT_STEP

    return lon_min, lon_max, lat_min, lat_max


class GridMapGenerator:
  def __init__(self, figsize: Tuple[int, int] = (20, 10)):
    self.figsize = figsize
    self.fig: plt.Figure | None = None
    self.ax = None

  def create_base_map(self) -> Tuple[plt.Figure, plt.Axes]:
    self.fig = plt.figure(figsize=self.figsize)
    # self.ax = self.fig.add_subplot(111, projection=ccrs.PlateCarree())
    self.ax = self.fig.add_subplot(111, projection=ccrs.Robinson())
    assert self.ax is not None

    self.ax.set_global()
    self.ax.add_feature(cfeature.LAND, facecolor='lightgreen', alpha=0.2)
    self.ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.7)
    self.ax.add_feature(cfeature.COASTLINE, linewidth=1.25, edgecolor='maroon')
    self.ax.add_feature(cfeature.BORDERS, linewidth=0.75, edgecolor='gray')

    # Add grid lines
    self._draw_grid_lines()

    self.ax.set_xlabel('Longitude', fontsize=12)
    self.ax.set_ylabel('Latitude', fontsize=12)

    return self.fig, self.ax

  def _draw_grid_lines(self) -> None:
    assert self.ax is not None
    for lon in range(-180, 181, FIELD_LON_STEP):
      self.ax.plot([lon, lon], [-90, 90], color='blue', linewidth=0.75,
                   alpha=0.5, transform=ccrs.PlateCarree())
      # Skip the last one to avoid overlap
      if lon != 180:
        self.ax.text(lon, 92, f'{lon}°', ha='center', va='bottom',
                     fontsize=8, color='black', alpha=0.8,
                     transform=ccrs.PlateCarree())

    for lat in range(-90, 91, FIELD_LAT_STEP):
      self.ax.plot([-180, 180], [lat, lat], color='blue', linewidth=0.75,
                   alpha=0.5, transform=ccrs.PlateCarree())
      # Skip the top one to avoid overlap
      if lat != 90:
        self.ax.text(-182, lat + 2, f'{lat}°', ha='right', va='center',
                     fontsize=8, color='black', alpha=0.8,
                     transform=ccrs.PlateCarree())

    # thin lines
    for lon in range(-180, 181, SQUARE_LON_STEP):
      self.ax.plot([lon, lon], [-90, 90], color='grey', linewidth=0.3,
                   alpha=0.5, transform=ccrs.PlateCarree())

    for lat in range(-90, 91, SQUARE_LAT_STEP):
      self.ax.plot([-180, 180], [lat, lat], color='grey', linewidth=0.3,
                   alpha=0.5, transform=ccrs.PlateCarree())

  def highlight_grids(self, grids: Set[str], color: str = '#880000') -> None:
    assert self.ax is not None
    converter = MaidenheadConverter()

    geoms = []
    for grid in grids:
        if not converter.validate(grid):
            logger.warning("Invalid grid square '%s' skipped", grid)
            continue
        lon_min, lon_max, lat_min, lat_max = converter.to_coordinates(grid)
        geoms.append(box(lon_min, lat_min, lon_max, lat_max))

    if geoms:
        merged = unary_union(geoms)
        self.ax.add_geometries(merged, crs=ccrs.PlateCarree(), facecolor=color,
                               edgecolor=None, alpha=0.6, zorder=20)

  def save(self, call: str, title: str, filename: str, dpi: int = 300) -> None:
    assert self.ax is not None
    year = datetime.now().year
    # Set title
    self.ax.set_title(f'{call} - {title}', fontsize=16, weight='bold', pad=20)

    if self.fig is None:
      raise ValueError("No map created. Call create_base_map() first.")

    self.fig.text(.13, .09, SIGNATURE.format(year, call), fontsize=10, color='gray')
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
    if grid := qso.get('GRIDSQUARE'):
      # Extract first 4 characters
      grid = grid[:GRID_LENGTH].upper()
      grids.add(grid)

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
  opts = parser.parse_args()
  call = opts.call.upper()

  # Extract grids from ADIF
  grids = extract_grids_from_adif(opts.adif_file)

  # Generate map
  generator = GridMapGenerator(figsize=(20, 10))
  generator.create_base_map()

  # Highlight worked grids
  generator.highlight_grids(grids)

  # Save map
  generator.save(call, opts.title, opts.output, opts.dpi)


if __name__ == "__main__":
  main()
