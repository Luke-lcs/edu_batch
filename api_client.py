import requests
import time
import logging
from typing import Any, Dict, Optional
from api_auth import Authenticator
from config import BASE_URL_API, REQUEST_TIMEOUT_SECONDS

class ApiClient:
    def __init__(self, authenticator: Authenticator, x_school_token: str):
        self.authenticator = authenticator
        self.x_school_token = x_school_token
        self.base_url = BASE_URL_API
        self._session = requests.Session()
        self.logger = logging.getLogger('EduBatch')

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
                 files: Optional[Dict] = None, max_retries: int = 3) -> Any:
        url = f'{self.base_url}{endpoint}'
        headers = self._get_auth_headers()

        if files:
            headers.pop('Content-Type', None)
            headers.pop('Accept', None)
            headers['Accept'] = 'application/json'
        elif json_data:
            headers['Content-Type'] = 'application/json'

        # Retry logic with exponential backoff
        for attempt in range(max_retries):
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
                status_code = http_err.response.status_code
                
                # Retry on 5xx errors (server errors) and 429 (rate limit)
                if status_code >= 500 or status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        self.logger.warning(f"Erro HTTP {status_code} para {endpoint}. Tentativa {attempt + 1}/{max_retries}. Aguardando {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                
                error_message = f'Erro HTTP: {status_code} - {http_err.response.text}'
                self.logger.error(error_message)
                raise ConnectionError(f"Erro na chamada API para {endpoint}: {error_message}") from http_err
                
            except requests.exceptions.RequestException as req_err:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Falha na requisição para {endpoint}: {req_err}. Tentativa {attempt + 1}/{max_retries}. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                self.logger.error(f'Falha na requisição para {endpoint}: {req_err}')
                raise ConnectionError(f"Falha na conexão com a API para {endpoint}") from req_err
                
            except Exception as e:
                self.logger.error(f'Erro inesperado na requisição para {endpoint}: {e}')
                raise

        # Should not reach here, but for safety
        raise ConnectionError(f"Falha após {max_retries} tentativas para {endpoint}")

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        return self._request('GET', endpoint, params=params)

    def post(self, endpoint: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None, files: Optional[Dict] = None) -> Any:
        return self._request('POST', endpoint, data=data, json_data=json_data, files=files)

    def patch(self, endpoint: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Any:
        return self._request('PATCH', endpoint, data=data, json_data=json_data)