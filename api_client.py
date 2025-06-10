import requests
from typing import Any, Dict, Optional
from api_auth import Authenticator
from config import BASE_URL_API, REQUEST_TIMEOUT_SECONDS

class ApiClient:
    def __init__(self, authenticator: Authenticator, x_school_token: str):
        self.authenticator = authenticator
        self.x_school_token = x_school_token
        self.base_url = BASE_URL_API
        self._session = requests.Session()

    def _get_auth_headers(self) -> Dict[str, str]:
        token = self.authenticator.get_token()
        if not token:
            raise ConnectionError("Falha ao obter token de autenticação.")
        return {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'x-school-token': self.x_school_token
        }

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                 data: Optional[Dict] = None, json_data: Optional[Dict] = None,
                 files: Optional[Dict] = None) -> Any:
        url = f'{self.base_url}{endpoint}'
        headers = self._get_auth_headers()

        if files:
            headers.pop('Content-Type', None)
            headers.pop('Accept', None)
            headers['Accept'] = 'application/json'
        elif json_data:
            headers['Content-Type'] = 'application/json'


        try:
            response = self._session.request(
                method, url, headers=headers, params=params,
                data=data, json=json_data, files=files, timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()

            if response.content:
                try:
                    return response.json()
                except requests.exceptions.JSONDecodeError:
                    return response.text
            return None

        except requests.exceptions.HTTPError as http_err:
            error_message = f'Erro HTTP: {http_err.response.status_code} - {http_err.response.text}'
            print(error_message)
            raise ConnectionError(f"Erro na chamada API para {endpoint}: {error_message}") from http_err
        except requests.exceptions.RequestException as req_err:
            print(f'Falha na requisição para {endpoint}: {req_err}')
            raise ConnectionError(f"Falha na conexão com a API para {endpoint}") from req_err
        except Exception as e:
            print(f'Erro inesperado na requisição para {endpoint}: {e}')
            raise

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        return self._request('GET', endpoint, params=params)

    def post(self, endpoint: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None, files: Optional[Dict] = None) -> Any:
        return self._request('POST', endpoint, data=data, json_data=json_data, files=files)

    def patch(self, endpoint: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Any:
        return self._request('PATCH', endpoint, data=data, json_data=json_data)
    