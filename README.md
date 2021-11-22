# ModeofModels Production
The following guide is tested on Ubuntu 18.04 and 20.04 LTS.
## 1. Setup Python environment
### 1.1 Install Python
Python version: >= 3.8  
[Miniconda](https://docs.conda.io/en/latest/miniconda.html) is recommanded.  
Latest release: [Miniconda3 Linux 64-bit](https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh) 

**Note**: virtual evn is not recommanded in prodution.
### 1.2 Enable conda-forge channel
After miniconda installed, the commands enable conda-forge channel  
```
conda config --add channels conda-forge
conda config --set channel_priority strict
conda config --show channels
```
### 1.2 Install Packages

## 2. Clone MoMProduction repo:
```
git clone https://github.com/Global-Flood-Assessment/MoMProduction.git
```
## 3. Ininitlize the setup
Please check [production.cfg](https://github.com/Global-Flood-Assessment/MoMProduction/blob/main/production.cfg) first: in general section, change WORKING_DIR (base directory for downloading and processing data) and OUTPUT_DIR (base directory for the data products); in glofas section, fill in user/passwd for ftp site.
```
[general]
WORKING_DIR: ~/MoM/Processing
OUTPUT_DIR: ~/MoM/Products

[glofas]
HOST: data-portal.ecmwf.int
USER: ???
PASSWD: ???
DIRECTORY: /for_PDC
```
Ininitlize the production setup: 
```
python initialize.py
```
It performs the following taks:   
- create the folder structures defined in production.cfg
- check username/password in production.cfg
- unzip watershed.shp 

