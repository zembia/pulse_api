from threading import Thread, Lock
from PyInquirer import prompt
from dateutil.parser import parse
import requests
from time import sleep

REQUESTS_LIMIT = 20
thread_lock = Lock()
running_threads = []
request_threads = []
data_threads = []


class PulseAPI:
    def __init__(self, backend_url):
        self.backend_url = backend_url

    def get_credentials(self, credentials):
        user = credentials

        # Check user params
        new_params = False

        if user["email"] is None or user["password"] is None:
            # Request credentials
            questions = [
                {
                    "type": "input",
                    "name": "email",
                    "message": "Ingresa tu correo de la cuenta Pulse:",
                },
                {
                    "type": "password",
                    "message": "Ingrese contraseña de plataforma Pulse:",
                    "name": "password",
                },
            ]

            ans = prompt(questions)
            user_email = ans["email"]
            user_password = ans["password"]
            new_params = True

        if not new_params:
            user_email = user["email"]
            user_password = user["password"]

        return user_email, user_password

    def login(self, user_email, user_password, verify=True):
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

        return authorization

    def get_measure_names(self, authorization, device_id, verify=True):
        url = f"{self.backend_url}/devices/{device_id}/measure_names.json"
        headers = {"Authorization": authorization}
        res = requests.get(url=url, headers=headers, verify=verify)
        res_json = res.json()
        return res_json

    def get_devices(self, authorization, verify=True):
        url = f"{self.backend_url}/devices.json"
        headers = {"Authorization": authorization}
        res = requests.get(url=url, headers=headers, verify=verify)
        res_json = res.json()

        return res_json

    def get_measures(
        self,
        authorization,
        device_id_list,
        start_date,
        end_date,
        measure_name_id_list,
        verify=True,
    ):
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
                args = [thread_index, params, headers, url, verify]
                running_threads.append(Thread(target=self.thread_request, args=args))
                running_threads[-1].start()            
        else:
            url = f"{self.backend_url}/devices/{device_id}/measures/faster_simple_graph.json"

            res = requests.get(url=url, params=params, headers=headers, verify=verify)
            res_json = res.json()

            return res_json
        
        while 1:
            thread_lock.acquire()
            _data_threads_length = len(data_threads)
            thread_lock.release()
            if len(device_id_list) == _data_threads_length:
                break
            sleep(0.2)
        
        return data_threads


    def thread_request(self, thread_index, params, headers, url, verify):
        global thread_lock, request_threads, data_threads

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

        # Release request slot
        thread_lock.acquire()
        i = request_threads.index(thread_index)
        del request_threads[i]
        thread_lock.release()

        # Append data
        thread_lock.acquire()
        data_threads.append(res_json)
        thread_lock.release()

        return
