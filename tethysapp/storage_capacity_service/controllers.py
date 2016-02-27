# author: Xiaohui (Sherry) Qiao, xhqiao89@gmail.com

import os
import binascii
import tempfile

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse, JsonResponse
from .sc_celery_app import add2, SC
from .model import SessionMaker, JobRecord
from celery.task.control import revoke

from tethys_sdk.gizmos import Button, TextInput, SelectInput
from django.shortcuts import render

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

    btnSearch = Button(display_text="Generate Storage Capacity Curve",
                        name="btnSearch",
                        attributes="onclick=run_sc_service()",
                        submit=False)

    damHeight = TextInput(display_text='Dam Height (m):',
                    name="damHeight",
                    initial="",
                    disabled=False,
                    attributes="")
    interval = TextInput(display_text='Interval (m):',
                name="interval",
                initial="",
                disabled=False,
                attributes="")

    context = {'btnSearch': btnSearch,
               'damHeight': damHeight,
               'interval': interval
               }

    return render(request,'storage_capacity_service/home.html', context)


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
    status = "success"
    message = ""
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

            session = SessionMaker()
            job_record = JobRecord(request.user.id, jobid, xlon, ylat, prj, damh, interval)
            session.add(job_record)
            session.commit()

            # Run SC()ys
            task_obj = SC.apply_async((jobid, xlon, ylat, prj, damh, interval), task_id=jobid)
        else:
            raise Exception("Please call this service in a GET request.")
    except Exception as ex:
        status = "error"
        message = ex.message

    # Return inputs and results
    finally:
        result_dict = {}
        result_dict['JOBID'] = task_obj.id
        result_dict['S_TIME'] = job_record.start_time
        result_dict['S_TIME_UTC'] = job_record.start_time_utc
        result_dict['MESSAGE'] = message
        result_dict['STATUS'] = status

        return JsonResponse(result_dict)

# http://127.0.0.1:8000/apps/storage-capacity-service/get/?jobid=04771964-90cf-4aa4-8eee-d4a1b4e2cac1
@login_required()
def get_sc(request):

    status = "success"
    message = ""
    sc = []
    lake_list = []

    try:
        if request.GET:
            jobid = request.GET.get("jobid", None)

            if check_user_has_job(request.user.id, jobid):
                task_obj = SC.AsyncResult(jobid)
                if task_obj.ready():
                    result_dict = task_obj.get()
                    #Check results
                    if result_dict is not None:
                        status = result_dict["status"]
                        sc = result_dict['storage_list']
                        lake_list = result_dict['lake_output_list']
                        message += result_dict['msg']
                    else:
                        status = result_dict["status"]
                        sc = []
                        lake_list = []
                        message += result_dict['msg']
                else:
                    status = "running"
                    message = "The worker is still running."
            else:
                raise Exception("Cannot find this job or this job is invisible to you.")
        else:
            raise Exception("Please call this service in a GET request.")
    except Exception as ex:
        status = "error"
        message = ex.message

    # Return inputs and results
    finally:
        result_dict = {}
        result_dict["STATUS"] = status
        result_dict["MESSAGE"] = message
        result_dict['SC_RESULT'] = sc
        result_dict["LAKE"] = lake_list
        result_dict["JOBID"] = jobid
        return JsonResponse(result_dict)

# http://127.0.0.1:8000/apps/storage-capacity-service/stop/?jobid=04771964-90cf-4aa4-8eee-d4a1b4e2cac1
@login_required()
def stop_sc(request):

    status = "success"
    message = "Job has been stopped."

    try:
        if request.GET:
            jobid = request.GET.get("jobid", None)

            if check_user_has_job(request.user.id, jobid):
                revoke(jobid, terminate=True)
            else:
                raise Exception("Cannot find this job or this job is invisible to you.")
        else:
            raise Exception("Please call this service in a GET request.")
    except Exception as ex:
        status = "error"
        message = ex.message

    # Return inputs and results
    finally:
        result_dict = {}
        result_dict["STATUS"] = status
        result_dict["MESSAGE"] = message
        result_dict["JOBID"] = jobid
        return JsonResponse(result_dict)


# http://127.0.0.1:8000/apps/storage-capacity-service/download/?jobid=ddd&filename=dr_srtm_30_a45b7df0_lake_523_0.GEOJSON
@login_required()
def download_output_files(request):
    try:
        output_filename = request.GET.get("filename", None)
        print output_filename
        jobid = request.GET.get("jobid", None)

        if check_user_has_job(request.user.id, jobid) and jobid in output_filename:
            output_file_path = os.path.join(OUTPUT_DATA_PATH, output_filename)
            print output_file_path
            response = FileResponse(open(output_file_path, 'r'), content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename="' + output_filename
            response['Content-Length'] = os.path.getsize(output_file_path)
            return response
        else:
            raise Exception("Cannot find this job or result file.")

    except Exception as e:
        response = HttpResponse(status=503)
        response.content = "<h3>Cannot find this job or result file.</h3>"
        return response

def check_user_has_job(userid, jobid):
    user_has_job = False

    session = SessionMaker()
    job_rec_array = session.query(JobRecord).all()
    for job_rec in job_rec_array:
        if job_rec.userid == userid:
            if job_rec.jobid == jobid:
                user_has_job = True
                break
    session.commit()
    return user_has_job

# http://127.0.0.1:8000/apps/storage-capacity-service/joblist/
@login_required()
def job_list(request):
    joblist = []
    jobstatus_dict = {}
    session = SessionMaker()
    job_rec_array = session.query(JobRecord).all()
    for job_rec in job_rec_array:
        if job_rec.userid == request.user.id:
            joblist.append(job_rec)
            jobstatus_dict[job_rec.jobid] = job_status(job_rec.jobid)
            # jobstatus_dict[job_rec.jobid] = 'Unknown'
    session.commit()

    context = {'joblist': joblist,
               'jobstatus_dict': jobstatus_dict
               }



    return render(request,'storage_capacity_service/joblist.html', context)

def job_status(jobid):
    status = "Unknown"
    task_obj = SC.AsyncResult(jobid)
    return task_obj.status


