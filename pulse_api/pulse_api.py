from PyInquirer import prompt
from dateutil.parser import parse
import requests


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

    def get_measure_names(self, authorization, device_id):
        url = f"{self.backend_url}/devices/{device_id}/measure_names.json"
        headers = {"Authorization": authorization}
        res = requests.get(url=url, headers=headers)
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
        device_id,
        start_date,
        end_date,
        measure_name_id_list,
        verify=True,
    ):
        start_date = parse(start_date, fuzzy=True)
        end_date = parse(end_date, fuzzy=True)

        params = {
            "start_date": start_date,
            "end_date": end_date,
            "order": "origin_created_at",
            "measure_name_id[]": measure_name_id_list,
        }

        url = (
            f"{self.backend_url}/devices/{device_id}/measures/faster_simple_graph.json"
        )
        headers = {"Authorization": authorization}

        res = requests.get(url=url, params=params, headers=headers, verify=verify)
        res_json = res.json()

        return res_json
