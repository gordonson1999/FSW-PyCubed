# Flight Software for the PyCubed Board (Argus-1)

The repository contains the current flight software stack for the **PyCubed Board** within Argus-1.  Argus-1 is a technology demonstration mission with the goal of (not exhaustive):
- Demonstrating Visual Attitude and Orbit Determination (A&OD) on a low-cost satellite (Independance from any GPS or ground involvement in the A&OD process)
- Collecting a dataset of images of the Earth to further efforts in CubeSat visual applications.
- Demonstrating efficient on-orbit ML/GPU Payload processing 

## Moving files to the board

Moving the flight software code to the Argus board can be automated using the pseudocompile.py script 

```bash
python pseudocompile.py -s <source_folder_path> -d <destination_folder_path>
```

## [All PyCubed Resources](https://www.notion.so/maholli/All-PyCubed-Resources-8738cab0dd0743239a3cde30c6066452)
Baseline default files used were the mainboard-v05 directory.

## License
<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />
- Hardware in this repository is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.
- Software/firmware in this repository is licensed under MIT unless otherwise indicated.
