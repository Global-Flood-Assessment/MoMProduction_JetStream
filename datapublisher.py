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
    flie_list = get_latestitems(settings.FINAL_MOM_DIR, numofitems=files_to_push)
    print(flie_list)

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