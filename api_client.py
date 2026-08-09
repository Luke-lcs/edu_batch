import requests
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Iterator, Optional
from api_auth import Authenticator
from config import BASE_URL_API, REQUEST_TIMEOUT_SECONDS, API_MAX_RETRIES
from logging_config import get_logger
from rate_limiter import api_rate_limiter

# Métodos cuja repetição não muda o resultado no servidor. Só eles podem ser
# retentados depois que a requisição chegou a ser processada.
IDEMPOTENT_METHODS = ('GET', 'HEAD', 'PUT', 'PATCH', 'DELETE')


class ApiClient:
    def __init__(self, authenticator: Authenticator, x_school_token: str):
        self.authenticator = authenticator
        self.x_school_token = x_school_token
        self.base_url = BASE_URL_API
        self._session = requests.Session()
        self.logger = get_logger()

    def _get_auth_headers(self) -> Dict[str, str]:
        token = self.authenticator.get_token()
        if not token:
            raise ConnectionError("Falha ao obter token de autenticação.")
        return {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'x-school-token': self.x_school_token
        }

    def _build_headers(self, files: Optional[Any], json_data: Optional[Dict]) -> Dict[str, str]:
        # Reconstruído a cada tentativa para que uma retentativa não use token vencido.
        headers = self._get_auth_headers()
        if files:
            # O requests define o Content-Type com o boundary do multipart.
            headers.pop('Content-Type', None)
        elif json_data:
            headers['Content-Type'] = 'application/json'
        return headers

    @staticmethod
    def _iter_file_objects(files: Optional[Any]) -> Iterator[Any]:
        if not files:
            return
        items = files.items() if isinstance(files, dict) else files
        for _, value in items:
            candidate = value[1] if isinstance(value, (tuple, list)) and len(value) > 1 else value
            if hasattr(candidate, 'read') and hasattr(candidate, 'seek'):
                yield candidate

    def _rewind_files(self, files: Optional[Any]) -> bool:
        """
        Volta os anexos para o início do arquivo.

        Sem isso, uma retentativa reenviaria o handle já lido até o fim, ou seja,
        um anexo de 0 byte — e a API aceitaria normalmente.
        """
        try:
            for file_obj in self._iter_file_objects(files):
                if not file_obj.seekable():
                    return False
                file_obj.seek(0)
            return True
        except (OSError, ValueError):
            return False

    @staticmethod
    def _should_retry(error: Exception, idempotent: bool) -> bool:
        if isinstance(error, requests.exceptions.HTTPError):
            response = getattr(error, 'response', None)
            status_code = response.status_code if response is not None else None
            if status_code == 429:
                # Recusada pelo rate limit: o servidor não processou nada.
                return True
            if status_code is not None and status_code >= 500:
                # O servidor pode ter processado antes de falhar. Repetir um POST
                # aqui criaria um comunicado duplicado para o aluno.
                return idempotent
            return False
        if isinstance(error, requests.exceptions.ConnectTimeout):
            # A conexão nem chegou a ser estabelecida: nada foi enviado.
            return True
        if isinstance(error, requests.exceptions.RequestException):
            return idempotent
        return False

    @staticmethod
    def _retry_after_seconds(error: Exception) -> Optional[float]:
        response = getattr(error, 'response', None)
        if response is None:
            return None
        header_value = response.headers.get('Retry-After')
        if not header_value:
            return None

        try:
            return max(0.0, float(header_value))
        except (TypeError, ValueError):
            pass

        try:
            retry_at = parsedate_to_datetime(header_value)
        except (TypeError, ValueError):
            return None
        if retry_at is None:
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                 data: Optional[Dict] = None, json_data: Optional[Dict] = None,
                 files: Optional[Any] = None, max_retries: int = API_MAX_RETRIES,
                 idempotent: Optional[bool] = None) -> Any:
        url = f'{self.base_url}{endpoint}'
        if idempotent is None:
            idempotent = method.upper() in IDEMPOTENT_METHODS

        for attempt in range(max_retries):
            if attempt > 0 and not self._rewind_files(files):
                message = (f"Não foi possível reposicionar os anexos para retentar {endpoint}; "
                           f"a requisição seria enviada com arquivos vazios.")
                self.logger.error(message)
                raise ConnectionError(message)

            headers = self._build_headers(files, json_data)

            # Vale para toda requisição, inclusive retentativas e verificações
            # de status — tudo conta para o limite de rps da API.
            api_rate_limiter.acquire()

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

            except requests.exceptions.RequestException as req_err:
                is_http_error = isinstance(req_err, requests.exceptions.HTTPError)
                if is_http_error:
                    status_code = req_err.response.status_code
                    detail = f'Erro HTTP: {status_code} - {req_err.response.text}'
                else:
                    detail = f'Falha na requisição: {req_err}'

                if attempt < max_retries - 1 and self._should_retry(req_err, idempotent):
                    wait_time = self._retry_after_seconds(req_err)
                    if wait_time is None:
                        wait_time = 2 ** attempt  # Backoff exponencial: 1s, 2s, 4s
                    self.logger.warning(
                        f"{detail} em {endpoint}. Tentativa {attempt + 1}/{max_retries}. "
                        f"Aguardando {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                    continue

                self.logger.error(f'{detail} em {endpoint}')
                if is_http_error:
                    raise ConnectionError(f"Erro na chamada API para {endpoint}: {detail}") from req_err
                raise ConnectionError(f"Falha na conexão com a API para {endpoint}") from req_err

            except Exception as e:
                self.logger.error(f'Erro inesperado na requisição para {endpoint}: {e}')
                raise

        # Inalcançável: o laço sempre retorna ou levanta exceção na última tentativa.
        raise ConnectionError(f"Falha após {max_retries} tentativas para {endpoint}")

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        return self._request('GET', endpoint, params=params)

    def post(self, endpoint: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None, files: Optional[Any] = None) -> Any:
        return self._request('POST', endpoint, data=data, json_data=json_data, files=files)

    def patch(self, endpoint: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Any:
        return self._request('PATCH', endpoint, data=data, json_data=json_data)
