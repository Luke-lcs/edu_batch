import requests
import threading
import time
from config import BASE_URL_AUTH, TOKEN_ENDPOINT, REQUEST_TIMEOUT_SECONDS

class Authenticator:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None
        self._token_expires_at_timestamp: float = 0.0
        self._expires_in_duration: int = 0
        self._created_at_timestamp: float = 0.0
        self._lock = threading.Lock()

    def _authenticate(self) -> bool:
        # Note: This method should be called within a lock context
        url = f'{BASE_URL_AUTH}{TOKEN_ENDPOINT}'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        try:
            print("Solicitando novo token de acesso à API...")
            response = requests.post(url, headers=headers, data=data, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()

            token_data = response.json()
            new_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in")
            created_at = token_data.get("created_at")

            if new_token and isinstance(expires_in, int) and isinstance(created_at, int):
                self._token = new_token
                self._expires_in_duration = expires_in
                self._created_at_timestamp = float(created_at)
                self._token_expires_at_timestamp = self._created_at_timestamp + self._expires_in_duration

                expiration_readable = time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime(self._token_expires_at_timestamp))
                print(f"Autenticado com sucesso! Novo token obtido. Expira em: {expiration_readable}")
                return True
            else:
                print(f"Erro na Autenticação: Resposta da API não continha os dados esperados do token. Resposta: {token_data}")
                self._token = None
                self._token_expires_at_timestamp = 0.0
                return False
        except requests.exceptions.HTTPError as http_err:
            print(f'Erro HTTP na Autenticação: {http_err.response.status_code} - {http_err.response.text}')
            self._token = None
            self._token_expires_at_timestamp = 0.0
            return False
        except requests.exceptions.RequestException as req_err:
            print(f'Falha na requisição de autenticação: {req_err}')
            self._token = None
            self._token_expires_at_timestamp = 0.0
            return False
        except Exception as e:
            print(f'Erro inesperado durante a autenticação: {e}')
            self._token = None
            self._token_expires_at_timestamp = 0.0
            return False

    def get_token(self) -> str | None:
        with self._lock:
            current_timestamp = time.time()
            
            # Check if token exists and is valid (with a 30s buffer)
            if self._token and self._token_expires_at_timestamp > (current_timestamp + 30):
                return self._token

            print("Token expirado ou próximo da expiração. Renovando...")
            if self._authenticate():
                return self._token
            
            return None

    def try_auth(self) -> bool:
        return self.get_token() is not None
    