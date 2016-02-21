# author: Xiaohui (Sherry) Qiao, xhqiao89@gmail.com

import os
import sys
import csv
from datetime import datetime, timedelta
import binascii
import subprocess
import tempfile

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse, JsonResponse

# Apache should have ownership and full permission to access this path
DEM_FULL_PATH = "/home/drew/dem/dr_srtm_30.tif"
DEM_NAME = 'dr_srtm_30' # DEM layer name, no extension (no .tif)
GISBASE = "/usr/lib/grass70" # full path to GRASS installation
GRASS7BIN = "grass70" # command to start GRASS from shell
GISDB = os.path.join(tempfile.gettempdir(), 'grassdata')
LOGS_PATH = os.path.join(tempfile.gettempdir(), 'grassdata', "logs")
OUTPUT_DATA_PATH = os.path.join(tempfile.gettempdir(), 'grassdata', "output_data")


@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    # BearCk
    # http://127.0.0.1:8000/apps/storage-capacity-service/?xlon=1696907&ylat=7339134.4&prj=native&damh=200.0&interval=15.0
    # DR
    # http://127.0.0.1:8000/apps/storage-capacity-service/?xlon=-7958864.55633&ylat=2038268.9716&prj=native&damh=50&interval=15

    string_length = 4
    jobid = binascii.hexlify(os.urandom(string_length))
    time_start = datetime.now()
    status = "error"
    message = ""
    sc = []
    lake_list = []
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

            input_para["xlon"] = xlon
            input_para["ylat"] = ylat
            input_para["prj"] = prj
            input_para["damh"] = damh
            input_para["interval"] = interval

            # Check interval greater than 0
            interval = float(interval)
            if interval <= 0:
                message = "Error: Interval should be greater than 0!"
                raise Exception(message)

            # Run SC()
            sc_list, lake_list, msg = SC(jobid, xlon, ylat, prj, damh, interval)

            #Check results
            if sc_list is not None:
                status = "success"
                sc = sc_list
                lake_list = lake_list
                message += msg
            else:
                status = "error"
                sc = []
                lake_list = []
                message += msg
        else:
            raise Exception("Please call this service in a GET request.")
    except Exception as ex:
        status = "error"
        message = ex.message

    # Return inputs and results
    finally:
        result_dict = {}
        result_dict['JOB_ID'] = jobid
        result_dict['T_START'] = time_start
        result_dict['T_END'] = datetime.now()
        elapsed = result_dict['T_END'] - result_dict['T_START']
        result_dict['RUN_TIME'] = str(elapsed)
        result_dict["STATUS"] = status
        result_dict["ERROR"] = message
        result_dict['SC_RESULT'] = sc
        result_dict["INPUT"] = input_para
        result_dict["NOTE"] = "If you encountered errors. Please contact Admin with the JobID."
        result_dict["LAKE"] = lake_list
        return JsonResponse(result_dict)


def SC(jobid, xlon, ylat, prj, damh, interval):

    dem_full_path = DEM_FULL_PATH
    dem = DEM_NAME
    gisbase = GISBASE
    grass7bin = GRASS7BIN
    gisdb = GISDB

    # Define grass data folder, location, mapset
    if not os.path.exists(gisdb):
        os.mkdir(gisdb)
    location = "location_{0}".format(dem)
    mapset = "PERMANENT"
    keep_intermediate = False
    msg = ""

    # Create log file for each job
    logs_path = LOGS_PATH
    if not os.path.exists(logs_path):
        os.mkdir(logs_path)
    log_name = 'log_{0}.log'.format(jobid)
    f = open(os.path.join(logs_path, log_name), 'w', 0)

    # Create output_data folder path
    output_data_path = OUTPUT_DATA_PATH
    if not os.path.exists(output_data_path):
        os.mkdir(output_data_path)

    temp_files_list = []

    try:
        # Create location
        location_path = os.path.join(gisdb, location)
        if not os.path.exists(location_path):
            f.write('\n---------Create Location from DEM--------------------\n')
            f.write('{0}\n'.format(location_path))
            startcmd = grass7bin + ' -c ' + dem_full_path + ' -e ' + location_path

            print startcmd
            p = subprocess.Popen(startcmd, shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if p.returncode != 0:
                print >>sys.stderr, 'ERROR: %s' % err
                print >>sys.stderr, 'ERROR: Cannot generate location (%s)' % startcmd
                f.write('\n---------Create Location failed--------------------\n')
                sys.exit(-1)
            else:
                f.write('\n---------Create Location done--------------------\n')
                print 'Created location %s' % location_path

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

        # launch session
        gsetup.init(gisbase, gisdb, location, mapset)
        f.write(str(gscript.gisenv()))

        # Check dem file, import if not exist
        dem_in_mapset_path = location_path = os.path.join(gisdb, location, mapset, "cell", dem)
        if not os.path.exists(dem_in_mapset_path):
            f.write("\n ---------- import DEM file ------------- \n")
            stats = gscript.read_command('r.in.gdal', input=dem_full_path, output=dem)
        # List all files in location to check if the DEM file imported successfully
        f.write("\n ---------- raster ------------- \n")
        for rast in gscript.list_strings(type='rast'):
            f.write(str(rast))
        f.write("\n ---------- vector ------------- \n")
        for vect in gscript.list_strings(type='vect'):
            f.write(str(vect))

        f.write("\n ---------------------------JOB START-------------------------------- \n")
        f.write(str(datetime.now()))

        # Project xlon, ylat wgs84 into current
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

        # Read extent of the dem file
        for key in stats:
            if "north:" in key:
                north = float(key.split(":")[1])
            elif "south:" in key:
                south = float(key.split(":")[1])
            elif "west:" in key:
                west = float(key.split(":")[1])
            elif "east:" in key:
                east = float(key.split(":")[1])
            elif "nsres:" in key:
                nsres = float(key.split(":")[1])
            elif "ewres:" in key:
                ewres = float(key.split(":")[1])

        # check if xlon, ylat is within the extent of dem
        if xlon < west or xlon > east:
            f.write("\n ERROR: xlon is out of dem region. \n")
            raise Exception("(xlon, ylat) is out of dem region.")
        elif ylat < south or ylat > north:
            f.write("\n ERROR: ylat is out of dem region. \n")
            raise Exception("(xlon, ylat) is out of dem region.")

        # Calculate cell area
        cell_area = nsres * ewres

        # Flow accumulation analysis
        f.write("\n ---------- Flow accumulation analysis ------------- \n")

        drainage = "{0}_drain_10k".format(dem)
        path_to_drainage = os.path.join(gisdb, location, mapset, "cell", drainage)
        if not os.path.exists(path_to_drainage):
            stats = gscript.read_command('r.watershed', elevation=dem, threshold='10000', drainage=drainage, flags='s', overwrite=True)

        # Delineate watershed
        f.write("\n ---------- Delineate watershed ------------- \n")
        basin = "{0}_{1}_basin".format(dem, jobid)
        temp_files_list.append(basin)
        stats = gscript.read_command('r.water.outlet', input=drainage, output=basin, coordinates=outlet, overwrite=True)

        # Cut dem with watershed
        f.write("\n -------------- Cut dem ----------------- \n")
        dem_cropped = "{0}_{1}_cropped".format(dem, jobid)
        mapcalc_cmd = '{0} = if({1}, {2})'.format(dem_cropped, basin, dem)
        temp_files_list.append(dem_cropped)
        gscript.mapcalc(mapcalc_cmd, overwrite=True, quiet=True)

        # Read outlet elevation
        f.write("\n ---------- Read outlet elevation ------------- \n")
        outlet_info = gscript.read_command('r.what', map=dem, coordinates=outlet)
        f.write("\n{0} \n".format(outlet_info))
        outlet_elev = outlet_info.split('||')[1]
        try:
            outlet_elev = float(outlet_elev)
        except Exception as e:
            f.write("{0} \n".format(e.message))
            raise Exception("This point has no data.")

        f.write("------------Outlet elevation--{0} ---------------- \n".format(outlet_elev))

        # Create a list including elevations of all interval points
        dam_elev = outlet_elev + dam_h
        elev_list = []
        elev = outlet_elev + elev_interval
        while elev < dam_elev:
             elev_list.append(elev)
             elev += elev_interval
        elev_list.append(dam_elev)
        f.write("\n----------Elevation list----------\n")
        f.write(str(elev_list))

        #For each interval point, calculate reservior volume
        f.write("\n ------------- Reservoir volume calculation ---------------- \n")
        storage_list = []
        lake_output_list = []
        count = 0
        for elev in elev_list:
            count += 1
            f.write(str(elev))
            f.write(", ")

            # Generate reservoir raster file
            f.write("\n-----------Generate lake file ---------- No.{}\n".format(count))
            lake_rast = '{0}_{1}_lake_{2}'.format(dem, jobid, str(elev))
            temp_files_list.append(lake_rast)
            stats = gscript.read_command('r.lake', elevation=dem_cropped, coordinates=outlet, waterlevel=elev, lake=lake_rast, overwrite=True)

            #Calculate reservoir volume
            f.write("\n-----------Calculate lake volume --------- No.{}\n".format(count))
            stats = gscript.parse_command('r.univar', map=lake_rast, flags='g')
            f.write("\n{0}\n".format(str(stats)))

            sum_height = float(stats['sum'])
            f.write("\n-------Cell area--{0}----------\n".format(str(cell_area)))
            volume = sum_height * cell_area
            storage = (volume, elev)
            print("\nNo. {0}--------> sc is {1} \n".format(count, str(storage)))
            storage_list.append(storage)

            # output lake
            # r.mapcalc expression="lake_285.7846_all_0 = if( lake_285.7846, 0)" --o
            f.write("\n -------------- Set all values of raster lake to 0 ----------------- \n")
            lake_rast_all_0 = "{0}_all_0".format(lake_rast)
            mapcalc_cmd = '{0} = if({1}, 0)'.format(lake_rast_all_0, lake_rast)
            gscript.mapcalc(mapcalc_cmd, overwrite=True, quiet=True)

            # covert raster lake_rast_all_0 into vector
            # r.to.vect input='lake_285.7846_all_0@drew' output='lake_285_all_0_vec' type=area --o
            f.write("\n -------------- convert raster lake_rast_all_0 into vector ----------------- \n")
            lake_rast_all_0_vec = "{0}_all_0_vect".format(lake_rast)
            lake_rast_all_0_vec = lake_rast_all_0_vec.replace(".", "_")
            f.write("\n -------------- {0} ----------------- \n".format(lake_rast_all_0_vec))
            stats = gscript.parse_command('r.to.vect', input=lake_rast_all_0, output=lake_rast_all_0_vec, type="area", overwrite=True)

            # output GeoJSON
            # v.out.ogr -c input='lake_285_all_0_vec' output='/tmp/lake_285_all_0_vec.geojson' format=GeoJSON type=area --overwrite
            geojson_f_name = "{0}.GEOJSON".format(lake_rast.replace(".", "_"))
            lake_rast_all_0_vec_GEOJSON = os.path.join(output_data_path, geojson_f_name)
            stats = gscript.parse_command('v.out.ogr', input=lake_rast_all_0_vec, output=lake_rast_all_0_vec_GEOJSON, \
                                          format="GeoJSON", type="area", overwrite=True, flags="c")

            # output KML
            # v.out.ogr -c input='lake_285_all_0_vec' output='/tmp/lake_285_all_0_vec.KML' format=KML type=area --overwrite
            kml_f_name = "{0}.KML".format(lake_rast.replace(".", "_"))
            lake_rast_all_0_vec_KML = os.path.join(output_data_path, kml_f_name)
            stats = gscript.parse_command('v.out.ogr', input=lake_rast_all_0_vec, output=lake_rast_all_0_vec_KML, \
                                          format="KML", type="area", overwrite=True, flags="c")

            output_tuple = (str(elev), geojson_f_name, kml_f_name)
            lake_output_list.append(output_tuple)

        for sc in storage_list:
            f.write(str(sc))
            f.write("\n")
        f.write("\n-------------------------END--------------------------\n")
        f.write(str(datetime.now()))
        f.close()
        keep_intermediate = False
        return storage_list, lake_output_list, msg

    except Exception as e:
        keep_intermediate = True
        print e.message
        msg = e.message
        if f is not None:
            f.write("\n-------------!!!!!!  ERROR  !!!!!!--------------\n")
            f.write(e.message)
            f.close()
        return None, None, msg

    finally:
        # Remove all temp files
        if not keep_intermediate:
            for f in temp_files_list:
                f_fullpath = "{0}/{1}/{2}/cell/{3}".format(gisdb, location, mapset, f)
                if os.path.exists(f_fullpath):
                    os.remove(f_fullpath)

# http://127.0.0.1:8000/apps/storage-capacity-service/download/?filename=dr_srtm_30_a45b7df0_lake_523_0.GEOJSON
def download_output_files(request):
    try:
        output_filename = request.GET.get("filename", None)
        print output_filename

        output_file_path = os.path.join(OUTPUT_DATA_PATH, output_filename)
        print output_file_path
        response = FileResponse(open(output_file_path, 'r'), content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="' + output_filename
        response['Content-Length'] = os.path.getsize(output_file_path)
        return response

    except Exception as e:
        response = HttpResponse(status=503)
        response.content = "<h3>Failed to download this files!</h3>"
        return response