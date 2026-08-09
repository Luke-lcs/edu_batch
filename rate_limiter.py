import threading
import time

from config import API_MAX_REQUESTS_PER_SECOND


class RateLimiter:
    """
    Limitador de vazão compartilhado entre as threads.

    Reserva um instante para cada requisição, espaçando-as igualmente. Diferente
    de um token bucket, não permite rajadas: o limite da Agenda Edu é uma
    recomendação de requisições por segundo, e uma rajada de 10 no mesmo
    instante já a violaria.

    O número de threads controla quantos envios ficam em voo ao mesmo tempo;
    quem controla a vazão contra a API é este limitador.
    """

    def __init__(self, max_per_second: float):
        self.max_per_second = max_per_second
        self._min_interval = 1.0 / max_per_second if max_per_second > 0 else 0.0
        self._lock = threading.Lock()
        self._next_slot = 0.0

    def acquire(self) -> float:
        """Bloqueia até que seja seguro fazer a próxima requisição. Retorna quanto esperou."""
        if self._min_interval <= 0:
            return 0.0

        with self._lock:
            now = time.monotonic()
            slot = max(now, self._next_slot)
            self._next_slot = slot + self._min_interval

        waited = slot - time.monotonic()
        if waited > 0:
            time.sleep(waited)
            return waited
        return 0.0


# Instância única compartilhada por ApiClient e Authenticator: o limite da API
# vale para o processo inteiro, não por cliente.
api_rate_limiter = RateLimiter(API_MAX_REQUESTS_PER_SECOND)
