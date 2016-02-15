# author: Xiaohui (Sherry) Qiao, xhqiao89@gmail.com

import os
import sys
import csv
from datetime import datetime
import binascii
import subprocess
import tempfile

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


# Apache should have ownership and full permission over this path
DEM_FULL_PATH = "/home/drew/Downloads/BearCk.tif"
DEM_NAME = 'BearCk' # DEM layer name, no extension (no .tif)
GISBASE = "/usr/lib/grass70" # the full path to GRASS installation
GRASS7BIN = "grass70" # the command to start GRASS from shell

@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    # http://127.0.0.1:8000/apps/storage-capacity-service/?xlon=1696907&ylat=7339134.4&prj=native&damh=200.0&interval=15.0
    # http://127.0.0.1:8000/apps/storage-capacity-service/?xlon=1696107&ylat=7339934.4&prj=native&damh=200.0&interval=5.0

    # output_csv = "sc.csv"

    string_length = 4
    jobid = binascii.hexlify(os.urandom(string_length))
    time_start = datetime.now()
    status = "error"
    message = ""
    sc = []
    input_para = {}

    try:
        if request.GET:
            xlon = request.GET.get("xlon", None)
            ylat = request.GET.get("ylat", None)
            prj = request.GET.get("prj", None)
            damh = request.GET.get("damh", None)
            interval = request.GET.get("interval", None)
            if xlon is None or ylat is None or prj is None or damh is None or interval is None:
                raise Exception("Valid query is like: http://.../?xlon=1696907&ylat=7339134.4&prj=native&damh=200.0&interval=15.0")

            input_para = {}
            input_para["xlon"] = xlon
            input_para["ylat"] = ylat
            input_para["prj"] = prj
            input_para["damh"] = damh
            input_para["interval"] = interval

            interval = abs(float(interval))
            if interval == 0:
                interval = 10
                message = "interval should be greater than 0! reset to {}".format(interval)
            sc_list, msg = SC(jobid, xlon, ylat, prj, damh, interval)

            if sc_list is not None:
                status = "success"
                sc = sc_list
                message += msg
                # with open(output_csv, 'wb') as fcsv:
                #     writer = csv.writer(fcsv)
                #     writer.writerows(sc_list)
            else:
                status = "error"
                sc = []
                message += msg
        else:
            raise Exception("Pleas call this service in a GET request.")
    except Exception as ex:
        status = "error"
        message = ex.message
    finally:
        result_dict = {}
        result_dict['job_id'] = jobid
        result_dict['t_start'] = time_start
        result_dict['t_end'] = datetime.now()
        result_dict["status"] = status
        result_dict["message"] = message
        result_dict['sc'] = sc
        result_dict["input"] = input_para
        result_dict["Note"] = "If you encountered strange errors. Please contact Admin with the JobID."
        return JsonResponse(result_dict)


def SC(jobid, xlon, ylat, prj, damh, interval):

    dem_full_path = DEM_FULL_PATH
    dem = DEM_NAME
    gisbase = GISBASE
    grass7bin = GRASS7BIN

    gisdb = os.path.join(tempfile.gettempdir(), 'grassdata')
    location = "sc-location"
    mapset = "PERMANENT"
    keep_intermediate = False
    msg = ""

    log_name = 'log_{0}.log'.format(jobid)
    log_path = os.path.join(gisdb, log_name)

    f = open(log_path, 'w', 0)

    temp_files_list = []
    try:
        # override for now with TEMP dir
        if not os.path.exists(gisdb):
            f.write('\n---------create GISDB--------------------\n')
            f.write('{0}\n'.format(gisdb))
            os.mkdir(gisdb)

        location_path = os.path.join(gisdb, location)
        if not os.path.exists(location_path):
            f.write('\n---------create Location from DEM--------------------\n')
            f.write('{0}\n'.format(location_path))
            startcmd = grass7bin + ' -c ' + dem_full_path + ' -e ' + location_path

            print startcmd
            p = subprocess.Popen(startcmd, shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if p.returncode != 0:
                print >>sys.stderr, 'ERROR: %s' % err
                print >>sys.stderr, 'ERROR: Cannot generate location (%s)' % startcmd
                f.write('\n---------create Location failed--------------------\n')
                sys.exit(-1)
            else:
                f.write('\n---------create Location done--------------------\n')
                print 'Created location %s' % location_path
        #---------------------

        xlon = float(xlon)
        ylat = float(ylat)
        outlet = (xlon, ylat)
        dam_h = float(damh)
        elev_interval = float(interval)

        # Set GISBASE environment variable
        os.environ['GISBASE'] = gisbase
        # the following not needed with trunk
        os.environ['PATH'] += os.pathsep + os.path.join(gisbase, 'extrabin')
        # Set GISDBASE environment variable
        os.environ['GISDBASE'] = gisdb

        # define GRASS-Python environment
        gpydir = os.path.join(gisbase, "etc", "python")
        sys.path.append(gpydir)

        f.write('\n---------sys.path--------------------\n')
        f.write('\n'.join(sys.path))
        f.write('\n----------sys.version-------------------\n')
        f.write(sys.version)
        f.write('\n----------os.environ-----------------\n')
        f.write(str(os.environ))

        # import GRASS Python bindings (see also pygrass)
        import grass.script as gscript
        import grass.script.setup as gsetup
        gscript.core.set_raise_on_error(True)

        ###########
        # launch session
        gsetup.init(gisbase, gisdb, location, mapset)
        f.write(str(gscript.gisenv()))

        dem_in_mapset_path = location_path = os.path.join(gisdb, location, mapset, "cell", dem)
        if not os.path.exists(dem_in_mapset_path):
            f.write("\n ---------- import DEM file ------------- \n")
            stats = gscript.read_command('r.in.gdal', input=dem_full_path, output=dem)

        f.write("\n ---------- raster ------------- \n")
        for rast in gscript.list_strings(type='rast'):
            f.write(str(rast))
        f.write("\n ---------- vector ------------- \n")
        for vect in gscript.list_strings(type='vect'):
            f.write(str(vect))

        f.write("\n ---------- !!!!!!!!!!!  REAL JOB STARTS HERE !!!!!!!!------------- \n")

        # project xlon, ylat wgs84 into current
        if prj.lower() != "native" or prj.lower() == "wgs84":
            f.write("\n ---------- Reproject xlon and ylat into native dem projection ------------- \n")
            stats = gscript.read_command('m.proj', coordinates=(xlon, ylat), flags='i')
            coor_list = stats.split("|")
            xlon = float(coor_list[0])
            ylat = float(coor_list[1])
            outlet = (xlon, ylat)

        # Define region
        f.write("\n ---------- Define region ------------- \n")
        stats = gscript.parse_command('g.region', raster=dem, flags='p')
        f.write(str(stats))
        for key in stats:
            if "north:" in key:
                north = float(key.split(":")[1])
            elif "south:" in key:
                south = float(key.split(":")[1])
            elif "west:" in key:
                west = float(key.split(":")[1])
            elif "east:" in key:
                east = float(key.split(":")[1])

        # check if xlon, ylat is within the extent of dem
        if xlon < west or xlon > east:
            f.write("\n ERROR: xlon is out of dem region. \n")
            raise Exception("(xlon, ylat) is out of dem region.")
        elif ylat < south or ylat > north:
            f.write("\n ERROR: ylat is out of dem region. \n")
            raise Exception("(xlon, ylat) is out of dem region.")

        # Flow accumulation analysis

        f.write("\n ---------- Flow accumulation analysis ------------- \n")
        f.write(str(datetime.now()))
        # stats = gscript.read_command('r.watershed', elevation=dem, threshold='10000', accumulation='accum_10K', drainage='draindir_10K', basin='basin_10K', flags='s', overwrite=True)
        drainage = "drain_10k_{0}".format(jobid)
        temp_files_list.append(drainage)
        stats = gscript.read_command('r.watershed', elevation=dem, threshold='10000', drainage=drainage, flags='s', overwrite=True)


        # Delineate watershed
        f.write("\n ---------- Delineate watershed ------------- \n")
        basin = "basin_{0}".format(jobid)
        temp_files_list.append(basin)
        stats = gscript.read_command('r.water.outlet', input=drainage, output=basin, coordinates=outlet, overwrite=True)

        # Set computation boundary
        # f.write("\n ---------- Set computation boundary ------------- \n")
        # stats = gscript.read_command('r.mask', raster=basin, overwrite=True)

        f.write("\n ---------- Cut dem ------------- \n")
        dem_cropped = "{0}_cropped_{1}".format(dem, jobid)
        mapcalc_cmd = '{0} = if({1}, {2})'.format(dem_cropped, basin, dem)
        temp_files_list.append(dem_cropped)
        gscript.mapcalc(mapcalc_cmd, overwrite=True, quiet=True)

        # Read outlet elevation
        f.write("\n ---------- Read outlet elevation ------------- \n")
        outlet_info = gscript.read_command('r.what', map=dem, coordinates=outlet)
        outlet_elev = outlet_info.split('||')[1]
        outlet_elev = float(outlet_elev)
        dam_elev = outlet_elev + dam_h

        elev_list = []
        # elev_list.append(outlet_elev)
        elev = outlet_elev + elev_interval
        while elev < dam_elev:
             elev_list.append(elev)
             elev += elev_interval
        elev_list.append(dam_elev)
        f.write(str(elev_list))

        f.write("\n ---------- Reservoir volume calculation ------------- \n")
        storage_list = []
        count = 0
        for elev in elev_list:
            count += 1
            f.write(str(elev))
            f.write(", ")
            #Resevior volume calculation
            lake_rast = 'lake_{0}_{1}'.format(jobid, str(elev))
            temp_files_list.append(lake_rast)
            f.write("\n111 --- No.{}\n".format(count))
            f.write(str(datetime.now()))
            gscript.read_command('r.lake', elevation=dem_cropped, coordinates=outlet, waterlevel=elev, lake=lake_rast, overwrite=True)
            f.write("\n222 --- No.{}\n".format(count))
            f.write(str(datetime.now()))
            stats = gscript.read_command('r.volume', input=lake_rast, clump=lake_rast)
            f.write("\n333 --- No.{}\n".format(count))
            f.write(str(datetime.now()))
            f.write(stats)
            volume = float(stats.split('Total Volume =')[1])
            storage = (volume, elev)
            print("No. {0}--------------------> sc is {1} \n".format(count, str(storage)))
            storage_list.append(storage)

        for sc in storage_list:
            f.write(str(sc))
            f.write("\n")
        f.write("\n !!!!!!!! END !!!!!!!! \n")
        f.write(str(datetime.now()))
        f.close()
        print ("---------------------------end--------------------------------")
        keep_intermediate = False
        return storage_list, msg
    except Exception as e:
        keep_intermediate = True
        print e.message
        msg = e.message
        if f is not None:
            f.write("\n!!!!!!  ERROR  !!!!!!\n")
            f.write(e.message)
            f.close()
        return None, msg
    finally:
        if not keep_intermediate:
            for f in temp_files_list:
                f_fullpath = "{0}/{1}/{2}/cell/{3}".format(gisdb, location, mapset, f)
                if os.path.exists(f_fullpath):
                    os.remove(f_fullpath)
