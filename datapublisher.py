"""
    datapublisher.py
    ~~~~~~~~~~~~~~~~
    publish data from the server to github, website, etc.
"""

import os
import sys

import settings
from utilities import get_latestitems


def git_push_onefile():
    """push one file to github"""
    pass

def github_publisher():
    """publish data to github
        -- number of files: days_to_push * 4
    """

    # get the number of files to push
    days_to_push = settings.DAYS_TO_PUSH
    files_to_push = days_to_push * 4

    # get the file names
    file_list = get_latestitems(settings.FINAL_MOM_DIR, numofitems=files_to_push)
    print(file_list)

    # switch working directory
    os.chdir(settings.GITHUB_DIR)

    # create dir if not exist
    csv_dir = os.path.join(settings.GITHUB_DIR ,settings.CSV_DIR)
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    gis_dir = os.path.join(settings.GITHUB_DIR ,settings.GIS_DIR)   
    if not os.path.exists(gis_dir):
        os.makedirs(gis_dir)
    
    # copy files to github repo
    file_counter = 0
    for csvfile in file_list:    
        # check if file exists first
        if os.path.exists(os.path.join(csv_dir,csvfile)):
            continue
        else:
            os.system("cp {} {}".format(os.path.join(settings.FINAL_MOM_DIR,csvfile), csv_dir))
            os.system("git add {}".format(os.path.join(settings.CSV_DIR,csvfile)))
            file_counter += 1
    
    if file_counter > 0:
        os.system("git commit -m \"update data\"")
        os.system("git push origin master")
        print("data published")
    else:
        print("no new data to publish")    


def publish():
    """publish data"""

    github_publisher()
    # print("publishing data")
    # os.system("git add .")
    # os.system("git commit -m \"update data\"")
    # os.system("git push origin master")
    # print("data published")

def main():
    """main function"""
    publish()

if __name__ == "__main__":
    main()