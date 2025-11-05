
## QsoGrid

**Draw your Amateur Radio QSOs into a Maidenhead grid square map.**

QsoGrid is a simple, command-line utility written in Python that processes an Amateur Data Interchange Format (**ADIF**) log file and generates a visual map highlighting all the unique **Maidenhead grid squares** worked.

### Install from PyPI (Recommended)

```bash
pip install qsogrid
```

### Install from Source

If you want to install the latest version directly from this repository:

```bash
git clone https://github.com/0x9900/qsogrid.git
cd qsogrid
pip install .
```

### Usage

Run `qsogrid` from your terminal, providing the required log file, output path, and your call sign.

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

### Example

This example processes the log file `fred.adi`, names the resulting image `W6BSD-Grid.png`, and sets the call sign to W6BSD:

```
qsogrid -a ~/tmp/fred.adi -o ./misc/W6BSD-Grid.png -c W6BSD -t "Worked Grids"
```

### Result

The generated output is a visual representation of the Maidenhead grid squares worked, based on the `GRIDSQUARE` field in your ADIF log.

![Example](https://bsdworld.org/misc/W6BSD-Grid.svgz)

### License

This project is licensed under the **BSD 3-Clause "New" or "Revised" License**.

### Contributing

Contributions are welcome! If you find a bug or have a suggestion for a new feature, please feel free to open an **issue** or submit a **pull request**.
