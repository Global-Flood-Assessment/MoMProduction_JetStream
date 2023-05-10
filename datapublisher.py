"""
    datapublisher.py
    ~~~~~~~~~~~~~~~~
    publish data from the server to github, website, etc.
"""

import os
import sys

import settings


def git_push_onefile():
    """push one file to github"""
    pass

def github_publisher():
    """publish data to github"""


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