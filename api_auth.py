import requests
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

    def _authenticate(self) -> bool:
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
        if not self._token or not self._token_expires_at_timestamp:
            print("Nenhum token existente ou informações de expiração. Tentando autenticar...")
            if not self._authenticate():
                return None
            return self._token

        current_timestamp = time.time()
        time_remaining_seconds = self._token_expires_at_timestamp - current_timestamp
        
        # Log do tempo restante para depuração
        # print(f"DEBUG: Tempo restante para expiração do token: {time_remaining_seconds:.2f} segundos.")

        if time_remaining_seconds <= 25: # Limite de 25 segundos
            if time_remaining_seconds > 0: # Ainda válido, mas dentro da janela crítica
                wait_time = time_remaining_seconds
                print(f"Token atual expira em {wait_time:.2f} segundos (dentro da janela crítica de 25s).")
                print(f"Aguardando {wait_time + 1:.2f} segundos para a expiração completa do token atual...")
                time.sleep(wait_time + 1) # Espera o tempo restante + 1 segundo de margem
            else:
                print("Token atual já expirou.")

            print("Solicitando renovação do token...")
            if not self._authenticate():
                print("Falha ao renovar o token.")
                return None

        return self._token

    def try_auth(self) -> bool:
        return self.get_token() is not None
    