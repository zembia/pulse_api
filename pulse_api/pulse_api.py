from threading import Thread, Lock
from dateutil.parser import parse
import requests
from time import sleep

REQUESTS_LIMIT = 20
thread_lock = Lock()
running_threads = []
request_threads = []
data_threads = []
data_cnt = 0


class PulseAPI:
    def __init__(self, backend_url="", verify=None):
        self.requests_limit = REQUESTS_LIMIT
        self.backend_url = backend_url
        self.verify = verify
        self.authorization = ""

    def set_backend_url(self, backend_url):
        self.backend_url = backend_url

    def set_verify(self, verify):
        self.verify = verify

    def set_requests_limit(self, limit):
        self.requests_limit = limit

    def get_credentials(self, credentials):
        user = credentials

        # Check user params
        new_params = False

        if user["email"] is None or user["password"] is None:
            user_email = ""
            user_password = ""
            new_params = True

        if not new_params:
            user_email = user["email"]
            user_password = user["password"]

        return user_email, user_password

    def set_authorization(self, authorization):
        self.authorization = authorization

    def login(self, user_email, user_password, verify=None):
        if verify == None:
            verify = self.verify
        # Do request
        data = {
            "user": {
                "email": user_email,
                "password": user_password,
            }
        }
        headers = {"content-type": "application/json"}
        res = requests.post(
            url=f"{self.backend_url}/login.json",
            json=data,
            headers=headers,
            verify=verify,
        )

        if res.status_code == 401:
            exit()
        elif res.status_code != 201 and res.status_code != 200:
            exit()

        authorization = res.headers["Authorization"]
        self.authorization = authorization

        return authorization

    def get_measure_names(self, device_id, authorization="", verify=None):
        if verify == None:
            verify = self.verify

        if authorization == "":
            authorization = self.authorization

        url = f"{self.backend_url}/devices/{device_id}/measure_names.json"
        headers = {"Authorization": authorization}
        res = requests.get(url=url, headers=headers, verify=verify)
        res_json = res.json()
        return res_json

    def get_devices(self, authorization="", properties=False, verify=None):
        params = []
        params_string = ""
        if verify == None:
            verify = self.verify

        if authorization == "":
            authorization = self.authorization

        if properties == True:
            params.append("new=true")
            params.append("properties=true")

        base_url = f"{self.backend_url}/devices.json"
        if len(params) > 0:
            params_string = "?" + "&".join(params)
        url = base_url + params_string

        headers = {"Authorization": authorization}
        res = requests.get(url=url, headers=headers, verify=verify)
        res_json = res.json()

        return res_json

    def get_measures(
        self,
        device_id_list,
        start_date,
        end_date,
        measure_name_id_list,
        process=None,
        process_args={},
        authorization="",
        verify=None,
    ):
        if verify == None:
            verify = self.verify

        if authorization == "":
            authorization = self.authorization

        # Parse dates
        start_date = parse(start_date, fuzzy=True)
        end_date = parse(end_date, fuzzy=True)

        # Request params
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "order": "origin_created_at",
            "measure_name_id[]": measure_name_id_list,
        }
        headers = {"Authorization": authorization}

        if type(device_id_list) is list:
            for thread_index, device_id in enumerate(device_id_list):
                url = f"{self.backend_url}/devices/{device_id}/measures/faster_simple_graph.json"
                args = [
                    thread_index,
                    params,
                    headers,
                    url,
                    verify,
                    device_id,
                    process,
                    process_args,
                ]
                running_threads.append(Thread(target=self.thread_request, args=args))
                running_threads[-1].start()
        else:
            url = f"{self.backend_url}/devices/{device_id}/measures/faster_simple_graph.json"

            res = requests.get(url=url, params=params, headers=headers, verify=verify)
            res_json = res.json()

            measures_raw = res_json["measures"]
            measures = {"device_id": device_id, "origin_dt_tz": [], "values": {}}

            for measure in measures_raw:
                measure_name_id = f'{measure["measure_name_id"]}'
                if measure_name_id not in measures["values"]:
                    measures["values"][measure_name_id] = []

                current_ts = measure["origin_dt_tz"]
                current_value = measure["value"]
                if len(measures["origin_dt_tz"]) == 0:
                    measures["origin_dt_tz"].append(current_ts)
                elif measures["origin_dt_tz"][-1] != current_ts:
                    measures["origin_dt_tz"].append(current_ts)
                measures["values"][measure_name_id].append(current_value)

            return measures

        while 1:
            thread_lock.acquire()
            _data_cnt = data_cnt  # len(data_threads)
            thread_lock.release()
            if len(device_id_list) == _data_cnt:
                break
            sleep(0.2)

        return data_threads

    def thread_request(
        self,
        thread_index,
        params,
        headers,
        url,
        verify,
        device_id,
        process,
        process_args,
    ):
        global thread_lock, request_threads, data_threads, data_cnt

        if verify == None:
            verify = self.verify

        # Acquire request slot
        while 1:
            thread_lock.acquire()
            if len(request_threads) >= REQUESTS_LIMIT:
                thread_lock.release()
                sleep(0.2)
                continue

            request_threads.append(thread_index)
            thread_lock.release()
            break

        # Make request
        res = requests.get(url=url, params=params, headers=headers, verify=verify)
        res_json = res.json()

        # Reformat response
        measures_raw = res_json["measures"]
        measures = {"device_id": device_id, "origin_dt_tz": [], "values": {}}

        for measure in measures_raw:
            measure_name_id = f'{measure["measure_name_id"]}'
            if measure_name_id not in measures["values"]:
                measures["values"][measure_name_id] = []

            current_ts = measure["origin_dt_tz"]
            current_value = measure["value"]
            if len(measures["origin_dt_tz"]) == 0:
                measures["origin_dt_tz"].append(current_ts)
            elif measures["origin_dt_tz"][-1] != current_ts:
                measures["origin_dt_tz"].append(current_ts)
            measures["values"][measure_name_id].append(current_value)

        # Release request slot
        thread_lock.acquire()
        i = request_threads.index(thread_index)
        del request_threads[i]
        thread_lock.release()

        # Append data
        thread_lock.acquire()
        if process != None:
            data_threads = process(measures, **process_args)
        else:
            data_threads.append(measures)
        data_cnt = data_cnt + 1
        thread_lock.release()

        return
