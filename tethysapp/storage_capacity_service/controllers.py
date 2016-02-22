# author: Xiaohui (Sherry) Qiao, xhqiao89@gmail.com

import os
from datetime import datetime
import binascii
import tempfile

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse, JsonResponse
from .sc_celery_app import add, SC

# Apache should have ownership and full permission to access this path
DEM_FULL_PATH = "/home/drew/dem/dr_srtm_30.tif"
DEM_NAME = 'dr_srtm_30' # DEM layer name, no extension (no .tif)
GISBASE = "/usr/lib/grass70" # full path to GRASS installation
GRASS7BIN = "grass70" # command to start GRASS from shell
GISDB = os.path.join(tempfile.gettempdir(), 'grassdata')
LOGS_PATH = os.path.join(tempfile.gettempdir(), 'grassdata', "logs")
OUTPUT_DATA_PATH = os.path.join(tempfile.gettempdir(), 'grassdata', "output_data")

@login_required()
def run_sc(request):
    """
    Controller for the app home page.
    """
    # BearCk
    # http://127.0.0.1:8000/apps/storage-capacity-service/run/?xlon=1696907&ylat=7339134.4&prj=native&damh=200.0&interval=15.0
    # DR
    # http://127.0.0.1:8000/apps/storage-capacity-service/run/?xlon=-7958864.55633&ylat=2038268.9716&prj=native&damh=50&interval=15

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
                raise Exception("Valid query is like: http://.../run/?xlon=1696907&ylat=7339134.4&prj=native&damh=200.0&interval=15.0")

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
            task_obj = SC.delay(jobid, xlon, ylat, prj, damh, interval)
        else:
            raise Exception("Please call this service in a GET request.")
    except Exception as ex:
        status = "error"
        message = ex.message

    # Return inputs and results
    finally:
        result_dict = {}
        result_dict['JOB_ID'] = jobid
        result_dict['CELERY_ID'] = task_obj.id
        result_dict['message'] = message
        result_dict['status'] = status

        return JsonResponse(result_dict)

# http://127.0.0.1:8000/apps/storage-capacity-service/get/?celery_id=04771964-90cf-4aa4-8eee-d4a1b4e2cac1
@login_required()
def get_sc(request):
    """
    Controller for the app home page.
    """
    # BearCk
    # http://127.0.0.1:8000/apps/storage-capacity-service/?xlon=1696907&ylat=7339134.4&prj=native&damh=200.0&interval=15.0
    # DR
    # http://127.0.0.1:8000/apps/storage-capacity-service/run/?xlon=-7958864.55633&ylat=2038268.9716&prj=native&damh=50&interval=15

    status = "error"
    message = ""
    sc = []
    lake_list = []
    input_para = {}

    try:
        if request.GET:
            celery_id = request.GET.get("celery_id", None)

            task_obj = SC.AsyncResult(celery_id)
            if task_obj.ready():
                sc_list, lake_list, msg = task_obj.get()

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
                status = "working..."
                message = "The worker is still running."
        else:
            raise Exception("Please call this service in a GET request.")
    except Exception as ex:
        status = "error"
        message = ex.message

    # Return inputs and results
    finally:
        result_dict = {}
        result_dict["STATUS"] = status
        result_dict["ERROR"] = message
        result_dict['SC_RESULT'] = sc
        result_dict["LAKE"] = lake_list
        result_dict["CELERY_ID"] = celery_id
        return JsonResponse(result_dict)


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