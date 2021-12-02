"""
GFMS_tool.py

Download and process GFMS and GloFAS data

Two main function:
    * GFMS_cron : run the daily cron job
    * GFMS_cron_fix: rerun cron-job for a given date
"""

import os, sys
import logging
import requests 
import pandas as pd
import geopandas
from datetime import date,timedelta,datetime

from settings import *
from utilities import watersheds_gdb_reader

def GloFAS_download():
    """download glofas data from ftp"""
    ftpsite = {}
    ftpsite['host'] = config.get('glofas','HOST')
    ftpsite['user'] = config.get('glofas','USER')
    ftpsite['passwd'] = config.get('glofas','PASSWD')
    ftpsite['directory'] = config.get('glofas','DIRECTORY')
    from ftplib import FTP
    ftp = FTP(host=ftpsite['host'],user=ftpsite['user'],passwd=ftpsite['passwd'])
    ftp.cwd(ftpsite['directory'])
    file_list = ftp.nlst()
    job_list = []
    for txt in file_list:
        save_txt = os.path.join(GLOFAS_PROC_DIR,txt)
        if os.path.exists(save_txt):
            continue
        with open(save_txt, 'wb') as fp:
            ftp.retrbinary('RETR '+txt, fp.write)
            if ("threspoints_"  in txt):
                job_list.append((txt.split(".")[0]).replace("threspoints_",""))
    ftp.quit()
    
    return job_list

def GloFAS_process():
    """process glofas data"""

    new_files = GloFAS_download()
    if len(new_files) == 0:
        logging.info("no new glofas file to process!")
        sys.exit()

    # load watersheds data
    watersheds = watersheds_gdb_reader()
    for data_date in new_files:
        logging.info("processing: " + data_date)
        fixed_sites = os.path.join(GLOFAS_PROC_DIR, "threspoints_"+data_date + ".txt") 
        dyn_sites = os.path.join(GLOFAS_PROC_DIR, "threspointsDyn_" + data_date + ".txt")
        # read fixed station data
        header_fixed_19 = ["Point No", "ID", "Basin", "Location", "Station", "Country", "Continent", "Country_code", "Upstream area", "unknown_1", "Lon", "Lat", "empty", "unknown_2", "Days_until_peak", "GloFAS_2yr", "GloFAS_5yr", "GloFAS_20yr", "Alert_level"]
        header_fixed_18 = ["Point No", "ID", "Basin", "Location", "Station", "Country", "Continent", "Country_code", "Upstream area", "Lon", "Lat", "empty", "unknown_2", "Days_until_peak", "GloFAS_2yr", "GloFAS_5yr", "GloFAS_20yr", "Alert_level"]
        fixed_data = pd.read_csv(fixed_sites,header = None,on_bad_lines='skip')
        fixed_data_col = len(fixed_data.axes[1])
        if fixed_data_col == 19:
            fixed_data.columns = header_fixed_19
        elif fixed_data_col == 18:
            fixed_data.columns = header_fixed_18
        # read dynamic station data
        header_dyn_19 = ["Point No", "ID", "Station", "Basin", "Location", "Country", "Continent", "Country_code", "unknown_1","Upstream area", "Lon", "Lat", "empty", "unknown_2", "Days_until_peak", "GloFAS_2yr", "GloFAS_5yr", "GloFAS_20yr", "Alert_level"]
        header_dyn_18 = ["Point No", "ID", "Station", "Basin", "Location", "Country", "Continent", "Country_code", "Upstream area", "Lon", "Lat", "empty", "unknown_2", "Days_until_peak", "GloFAS_2yr", "GloFAS_5yr", "GloFAS_20yr", "Alert_level"]
        dyn_data = pd.read_csv(dyn_sites,header=None,on_bad_lines='skip')
        dyn_data_col = len(dyn_data.axes[1])
        if dyn_data_col == 19:
            dyn_data.columns = header_dyn_19
        elif dyn_data_col == 18:
            dyn_data.columns = header_dyn_18
        # merge two datasets
        if fixed_data_col== dyn_data_col:
            total_data = fixed_data.append(dyn_data,sort=True)
        else:
            total_data = fixed_data
            print("dyn_data is ignored")

        # create a geopanda dataset
        gdf = geopandas.GeoDataFrame(total_data, geometry=geopandas.points_from_xy(total_data.Lon, total_data.Lat))
        gdf.crs = "EPSG:4326"
        # generate sindex
        gdf.sindex

        # sjoin 
        gdf_watersheds = geopandas.sjoin(gdf, watersheds, op='within')
        gdf_watersheds.rename(columns={"index_right":"pfaf_id"},inplace=True)

        forcast_time = (fixed_sites.split("_")[1]).replace('00.txt','')
        forcast_time = datetime.strptime(forcast_time, '%Y%m%d' )
        # add column "Forecast Date"
        gdf_watersheds["Forecast Date"]=forcast_time.isoformat()

        # convert "GloFAS_2yr","GloFAS_5yr","GloFAS_20y" to 0~100
        if (gdf_watersheds["GloFAS_2yr"].max() <= 1.0):
            gdf_watersheds["GloFAS_2yr"] = gdf_watersheds["GloFAS_2yr"]*100
            gdf_watersheds["GloFAS_5yr"] = gdf_watersheds["GloFAS_5yr"]*100
            gdf_watersheds["GloFAS_20yr"] = gdf_watersheds["GloFAS_20yr"]*100
        gdf_watersheds=gdf_watersheds.astype({"GloFAS_2yr":int,"GloFAS_5yr":int,"GloFAS_20yr":int})

        # fill max_EPS
        gdf_watersheds["max_EPS"]=gdf_watersheds.apply(lambda row: str(row['GloFAS_2yr'])+"/"+str(row['GloFAS_5yr'])+"/"+str(row['GloFAS_20yr']), axis=1)

        # write out csv file
        out_csv = os.path.join(GLOFAS_DIR, "threspoints_" + data_date + ".csv")
        out_columns =['Point No',"Station","Basin","Country","Lat","Lon","Upstream area","Forecast Date","max_EPS",
                    "GloFAS_2yr","GloFAS_5yr","GloFAS_20yr","Alert_level","Days_until_peak","pfaf_id"]
        gdf_watersheds.to_csv(out_csv,index=False,columns=out_columns,float_format='%.3f')
        
        logging.info("glofas: " + out_csv)

        # write to excel
        # out_excel = glofasdata + "threspoints_" + data_date + ".xlsx"
        # gdf_watersheds.to_excel(out_excel,index=False,columns=out_columns,sheet_name='Sheet_name_1')
        
        # to geojson
        out_geojson = os.path.join(GLOFAS_DIR, "threspoints_" + data_date + ".geojson")
        gdf_watersheds.to_file(out_geojson,driver='GeoJSON')
    
    # return a list date to be processed with GFMS
    return new_files

def GFMS_download(bin_file):
    """download a given bin file"""

    # find download url
    datestr = bin_file.split("_")[2]
    baseurl = config.get('gfms','HOST')
    dataurl = os.path.join(baseurl, datestr[:4], datestr[:6])
    download_data_url = os.path.join(dataurl,bin_file)

    # check if it download
    binfile_local = os.path.join(GFMS_PROC_DIR,bin_file)
    if not os.path.exists(binfile_local):
        # download the data
        try:
            r = requests.get(download_data_url, allow_redirects=True)
        except requests.exceptions.HTTPError as e:
            logging.ERROR("Downlaod failed: " + e.response.text)
            sys.exit()

        open(binfile_local, 'wb').write(r.content)

    # generate header file
    hdr_header = """NCOLS 2458
    NROWS 800
    XLLCORNER -127.25
    YLLCORNER -50
    CELLSIZE 0.125
    PIXELTYPE FLOAT
    BYTEORDER LSBFIRST
    NODATA_VALUE -9999
    """
    header_file = binfile_local.replace(".bin",".hdr")
    with open(header_file,"w") as f:
        f.write(hdr_header)
    
    # generate vrt file
    vrt_template = """<VRTDataset rasterXSize="4916" rasterYSize="1600" subClass="VRTWarpedDataset">
  <GeoTransform> -1.2725000000000000e+02,  6.2500000000000000e-02,  0.0000000000000000e+00,  5.0000000000000000e+01,  0.0000000000000000e+00, -6.2500000000000000e-02</GeoTransform>
  <VRTRasterBand dataType="Float32" band="1" subClass="VRTWarpedRasterBand">
    <NoDataValue>-9999</NoDataValue>
  </VRTRasterBand>
  <BlockXSize>512</BlockXSize>
  <BlockYSize>128</BlockYSize>
  <GDALWarpOptions>
    <WarpMemoryLimit>6.71089e+07</WarpMemoryLimit>
    <ResampleAlg>NearestNeighbour</ResampleAlg>
    <WorkingDataType>Float32</WorkingDataType>
    <Option name="INIT_DEST">NO_DATA</Option>
    <SourceDataset relativeToVRT="1">{}</SourceDataset>
    <Transformer>
      <ApproxTransformer>
        <MaxError>0.125</MaxError>
        <BaseTransformer>
          <GenImgProjTransformer>
            <SrcGeoTransform>-127.25,0.125,0,50,0,-0.125</SrcGeoTransform>
            <SrcInvGeoTransform>1018,8,0,400,0,-8</SrcInvGeoTransform>
            <DstGeoTransform>-127.25,0.0625,0,50,0,-0.0625</DstGeoTransform>
            <DstInvGeoTransform>2036,16,0,800,0,-16</DstInvGeoTransform>
          </GenImgProjTransformer>
        </BaseTransformer>
      </ApproxTransformer>
    </Transformer>
    <BandList>
      <BandMapping src="1" dst="1">
        <SrcNoDataReal>-9999</SrcNoDataReal>
        <SrcNoDataImag>0</SrcNoDataImag>
        <DstNoDataReal>-9999</DstNoDataReal>
        <DstNoDataImag>0</DstNoDataImag>
      </BandMapping>
    </BandList>
  </GDALWarpOptions>
</VRTDataset>"""

    # generate VRT file
    vrt_file = binfile_local.replace(".bin",".vrt")
    with open(vrt_file,"w") as f:
        f.write(vrt_template.format(bin_file))

    return vrt_file

def GFMS_data_extractor(bin_file):
    """extract data from a given binfile"""

    # download GFMS binfile
    vrt_file = GFMS_download(bin_file)
    print(vrt_file)

def GFMS_processing(proc_dates_list):
    '''process GFMS data with a given list of dates'''
    
    binhours = ["00","03","06","09","12","15","18","21"]
    for data_date in proc_dates_list:
        real_date = data_date[:-2]
        for binhour in binhours:
            bin_file = "Flood_byStor_" + real_date + binhour + ".bin"
            # process bin file
            GFMS_data_extractor(bin_file)

def GFMS_cron():
    """ run GFMS cron job"""

    # process GloFAS data
    #processing_dates = GloFAS_process()
    # process GFMS data
    processing_dates = ['2021120200']
    GFMS_processing(processing_dates)

def main():
    """test code"""
    GFMS_cron()

if __name__ == "__main__":
    main()
