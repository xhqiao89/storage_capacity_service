from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import os
import sys
import csv
from datetime import datetime


@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    #http://127.0.0.1:8000/apps/sc-service/?x=1696907&y=7339134.4&damh=200.0&interval=15.0
    output_csv = "sc.csv"

    time_start = datetime.now()
    status = "error"
    message = "message"
    sc = []

    try:
        if request.GET:
            x = request.GET["x"]
            y = request.GET["y"]
            damh = request.GET["damh"]
            interval = request.GET["interval"]
            interval = abs(float(interval))
            if interval == 0:
                interval = 10
                message = "interval should be greater than 0! reset to {}".format(interval)
            sc_list = SC(x, y, damh, interval)

            if sc_list is not None:
                status = "success"
                sc = sc_list
                with open(output_csv, 'wb') as fcsv:
                    writer = csv.writer(fcsv)
                    writer.writerows(sc_list)
            else:
                status = "success"
                sc = []
    except Exception as ex:
        status = "error"
        message = ex.message
    finally:
        result_dict = {}
        result_dict['t_start'] = time_start
        result_dict['t_end'] = datetime.now()
        result_dict["status"] = status
        result_dict["message"] = message
        result_dict['sc'] = sc
        return JsonResponse(result_dict)


def SC(x, y, damh, interval):
    try:
        dem = 'BearCk'
        outlet = (float(x), float(y))
        dam_h = float(damh)
        elev_interval = float(interval)

        f = open('script_log.log', 'w', 0)

        gisbase = "/usr/lib/grass70"
        gisdb = "/home/drew/grass_folder"
        location = "newLocation"
        mapset = "drew"

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

        f.write("\n ---------- raster ------------- \n")
        for rast in gscript.list_strings(type='rast'):
            f.write(str(rast))
        f.write("\n ---------- vector ------------- \n")
        for vect in gscript.list_strings(type='vect'):
            f.write(str(vect))

        f.write("\n ---------- REAL JOB STARTS HERE ------------- \n")
        #User input
        #Units all in meter


        # Define region
        f.write("\n ---------- Define region ------------- \n")
        stats = gscript.read_command('g.region', raster=dem, flags='p')

        # Flow accumulation analysis

        f.write("\n ---------- Flow accumulation analysis ------------- \n")
        f.write(str(datetime.now()))
        # stats = gscript.read_command('r.watershed', elevation=dem, threshold='10000', accumulation='accum_10K', drainage='draindir_10K', basin='basin_10K', flags='s', overwrite=True)
        stats = gscript.read_command('r.watershed', elevation=dem, threshold='10000', drainage='draindir_10K', flags='s', overwrite=True)


        # Delineate watershed
        f.write("\n ---------- Delineate watershed ------------- \n")
        stats = gscript.read_command('r.water.outlet', input='draindir_10K', output='basin_1', coordinates=outlet, overwrite=True)

        # Set computation boundary
        f.write("\n ---------- Set computation boundary ------------- \n")
        stats = gscript.read_command('r.mask', raster='basin_1', overwrite=True)

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
            lake_rast = 'lake_' + str(elev)
            f.write("\n111 --- No.{}\n".format(count))
            f.write(str(datetime.now()))
            gscript.read_command('r.lake', elevation=dem, coordinates=outlet, waterlevel=elev, lake=lake_rast, overwrite=True)
            f.write("\n222 --- No.{}\n".format(count))
            f.write(str(datetime.now()))
            stats = gscript.read_command('r.volume', input=lake_rast)
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
        return storage_list
    except Exception as e:
        print e.message
        if f is not None:
            f.write("\n!!!!!!  ERROR  !!!!!!\n")
            f.write(e.message)
            f.close()
        return None