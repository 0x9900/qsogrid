# Draw your QSOs into a Maidenhead grid square map.

## Usage:

```
qsogrid -a ~/tmp/fred.adi -o ./misc/W6BSD-Grid.png -c W6BSD
```

![Example](misc/W6BSD-Grid.png)

```
usage: qsogrid [-h] -a ADIF_FILE -o OUTPUT -c CALL [-t TITLE] [-d DPI]

Maidenhead gridsquare map

options:
  -h, --help            show this help message and exit
  -a ADIF_FILE, --adif-file ADIF_FILE
                        ADIF log filename
  -o OUTPUT, --output OUTPUT
                        png output filename
  -c CALL, --call CALL  Operator's call sign
  -t TITLE, --title TITLE
                        Title of the map
  -d DPI, --dpi DPI     Image resolution

```
