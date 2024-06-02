# gis_misc

Miscellaneous scripts/tools that involves spatial data processing


## airspace_geometry

Functions to easily create airspace geometries based on airspace definitions that is used in aeronautical publications,
example:
 * circle with given center point  and radius
 * circular sector with given center point, beginning and end azimuth
 * ring, with given center point and two radii

## polygons_from_csv

Function to create polygons from CSV file with format:

* field separator: ; (semicolon)
* fields:
    * name: polygon name
    * lat: latitude
    * lon: longitude
* coordinates: format DMS (degrees, minutes, seconds) with hemisphere prefix or suffix.
 degrees, minutes, seconds - separated by space or not separated ('compacted' HDMS/DMSH format), examples: `253246.99N, 050 34 21.79 E`
* polygon name can be specified only for the first pair or coordinates

Example CSV data file:

    name;lat;lon
    polygonA;latA1;lonA1
    ;latA2;lonA2
    ;latA3;lonA3
    ;latA4;lonA4
    polygonB;latB1;lonB1
    ;latB2;lonB2
    ;latB3;lonB3
    ;latB4;lonB4
    ;latB5;lonB5
    ;latB6;lonB6



