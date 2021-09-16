## Requirements
- SOEP: An important prerequisite in order to use this version of the model an important is to have permission to use the Socio-economic Panel 2017 and to have a copy of this dataset on your local machine. You can get the data [here](https://www.diw.de/sixcms/detail.php?id=diw_01.c.738729.en).
- STATA: Unfortunately, the current version of the model also requires a working installation of STATA (version >= 13). *(We are currently working on an update which will remove the requirement for STATA and will replace the STATA-code by python-code.)*
- Conda: To install and activate the specific virtual python environment, a current installation of Conda is required.

## Setup
1. Clone this repository onto your local machine.
2. Take the folder "soep.v34" provided in the SOEP-data and copy it into the repository's folder "data".
3. Open the STATA-file "stata_01_merge_soep_datasets.do", change the working directory to the repository's root folder on your local machine.
4. Execute the STATA-skript "stata_01_merge_soep_datasets.do".
5. Open the STATA-file "stata_02_clean_soep_data.do", change the working directory to the repository's root folder on your local machine.
6. Execute the STATA-skript "stata_02_clean_soep_data.do".
7. Install the virtual environment from the file "env.yaml" using conda.
8. If everything has been done correctly, the model is now ready for use.

## Single simulation
...

## Simulation experiments
...
