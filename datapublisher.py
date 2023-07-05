"""
    datapublisher.py
    ~~~~~~~~~~~~~~~~
    publish data from the server to github, website, etc.
"""

import os
import sys

import geopandas as gpd
import pandas as pd

import settings
from utilities import get_latestitems, watersheds_gdb_reader


def generate_geojson(momoutput, adate, outputdir):
    """generate geojson file from mom output, return list of geojson files
    -- momoutput: csv file in csv dir with pfaf_id
    -- adate: datestr
    -- outputdir: output directory
    """

    idfield = "pfaf_id"
    # list alert types
    alist = ["Warning", "Watch"]

    # load csv file
    df = pd.read_csv(momoutput, encoding="ISO-8859-1")
    # force id as int
    df[idfield] = df[idfield].astype(int)
    # drop duplicates
    df = df.drop_duplicates(subset=[idfield])

    # load watersheds
    watersheds = watersheds_gdb_reader()
    geojson_list = []
    for acond in alist:
        n_df = df[df["Alert"] == acond]
        out_df = watersheds.loc[n_df[idfield]]
        out_df = out_df.merge(n_df, left_on=idfield, right_on=idfield)
        # write warning result to geojson
        outputfile = f"{adate}_{acond}.geojson"
        geojson_list.append(outputfile)
        out_df.to_file(
            os.path.join(outputdir, outputfile), index=False, driver="GeoJSON"
        )

    return geojson_list


def git_push_onefile():
    """push one file to github"""
    pass


def momoutput_publisher():
    """publish data to github
    -- number of files: days_to_push * 4
    """

    # get the number of files to push
    days_to_push = settings.DAYS_TO_PUSH
    files_to_push = days_to_push * 4

    # get the file names for the latest items
    file_list = get_latestitems(settings.FINAL_MOM_DIR, numofitems=files_to_push)

    # any file to remove?
    csv_in_github = os.listdir(os.path.join(settings.GITHUB_DIR, settings.CSV_DIR))
    csv_to_remove = [x for x in csv_in_github if x not in file_list]

    # switch working directory
    os.chdir(settings.GITHUB_DIR)

    # create dir if not exist
    csv_dir = os.path.join(settings.GITHUB_DIR, settings.CSV_DIR)
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    gis_dir = os.path.join(settings.GITHUB_DIR, settings.GIS_DIR)
    if not os.path.exists(gis_dir):
        os.makedirs(gis_dir)

    # copy files to github repo
    file_counter = 0
    for csvfile in file_list:
        # check if file exists first
        if os.path.exists(os.path.join(csv_dir, csvfile)):
            continue
        else:
            os.system(
                "cp {} {}".format(
                    os.path.join(settings.FINAL_MOM_DIR, csvfile), csv_dir
                )
            )
            os.system("git add {}".format(os.path.join(settings.CSV_DIR, csvfile)))
            file_counter += 1

    # geojson output
    # Final_Attributes_2023051006HWRF+MOM+DFO+VIIRSUpdated_PDC.csv
    # 2023051006_Warning.geojson
    # 2023051006_Watch.geojson
    # check geojson files
    for csvfile in file_list:
        adate = csvfile.split("_")[2][:10]
        warning_file = "{}_Warning.geojson".format(adate)
        warning_file = os.path.join(gis_dir, warning_file)
        watch_file = "{}_Watch.geojson".format(adate)
        watch_file = os.path.join(gis_dir, watch_file)

        if os.path.exists(warning_file) and os.path.exists(watch_file):
            continue
        else:
            newfile_list = generate_geojson(
                os.path.join(csv_dir, csvfile), adate, gis_dir
            )
            for newfile in newfile_list:
                os.system("git add {}".format(os.path.join(settings.GIS_DIR, newfile)))
                file_counter += 1

    # remove old files
    if len(csv_to_remove) > 0:
        # remove files
        for csvfile in csv_to_remove:
            # git rm csv file
            os.system("git rm {}".format(os.path.join(settings.CSV_DIR, csvfile)))
            file_counter += 1
            # remove geojson files
            adate = csvfile.split("_")[2][:10]
            for acond in ["Warning", "Watch"]:
                geojsonfile = "{}_{}.geojson".format(adate, acond)
                if os.path.exists(os.path.join(gis_dir, geojsonfile)):
                    print("remove:", os.path.join(settings.GIS_DIR, geojsonfile))
                    os.system(
                        "git rm {}".format(os.path.join(settings.GIS_DIR, geojsonfile))
                    )
                    file_counter += 1
    else:
        print("no file to remove")

    # push to github
    the_latest_file = file_list[-1]
    the_latest_date = the_latest_file.split("_")[2][:10]
    print("the latest date:", the_latest_date)

    if file_counter > 0:
        os.system('git commit -m "update: {}"'.format(the_latest_date))
        os.system("git push origin main")
        print("data published")
    else:
        print("no new data to publish")


def viirspop_publisher():
    """publish data to github
    -- number of files: days_to_push * 4
    """

    # get the number of files to push
    days_to_push = settings.DAYS_TO_PUSH
    files_to_push = days_to_push * 4

    # get the file names for the latest items
    file_list = get_latestitems(settings.POPOUTPUT_DIR, numofitems=files_to_push)

    # any file to remove?
    csv_in_github = os.listdir(os.path.join(settings.GITHUB_DIR, settings.POP_DIR))
    csv_to_remove = [x for x in csv_in_github if x not in file_list]

    # switch working directory
    os.chdir(settings.GITHUB_DIR)

    # create dir if not exist
    csv_dir = os.path.join(settings.GITHUB_DIR, settings.POP_DIR)
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    # copy files to github repo
    file_counter = 0
    for csvfile in file_list:
        # check if file exists first
        if os.path.exists(os.path.join(csv_dir, csvfile)):
            continue
        else:
            os.system(
                "cp {} {}".format(
                    os.path.join(settings.POPOUTPUT_DIR, csvfile), csv_dir
                )
            )
            os.system("git add {}".format(os.path.join(settings.POP_DIR, csvfile)))
            file_counter += 1

    # remove old files
    if len(csv_to_remove) > 0:
        # remove files
        for csvfile in csv_to_remove:
            # git rm csv file
            os.system("git rm {}".format(os.path.join(settings.POP_DIR, csvfile)))
            file_counter += 1
    else:
        print("no file to remove")

    # push to github
    the_latest_file = file_list[-1]
    the_latest_date = the_latest_file.split("_")[2][:10]
    print("the latest date:", the_latest_date)

    if file_counter > 0:
        os.system('git commit -m "update: {}"'.format(the_latest_date))
        os.system("git push origin main")
        print("data published")
    else:
        print("no new data to publish")


def github_publisher():
    """publish data"""

    momoutput_publisher()
    viirspop_publisher()


def main():
    """main function"""
    github_publisher()


if __name__ == "__main__":
    main()
