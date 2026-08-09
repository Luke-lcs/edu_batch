# URLs for Agenda Edu API
BASE_URL_AUTH = 'https://api.agendaedu.com'
BASE_URL_API = 'https://api.agendaedu.com/v2'
TOKEN_ENDPOINT = '/oauth/v2/token'
HANDOUT_CATEGORIES_ENDPOINT = '/handout_categories'
STUDENT_PROFILES_ENDPOINT = '/student_profiles'
HANDOUTS_ENDPOINT = '/handouts'

# Files Configurations
ATTACHMENT_FILES_DIR = './attachment_files'
ADDITIONAL_FILES_DIR = './additional_files'
COVER_IMAGE_DIR = './cover_image'
LOG_ERROR_FILE = 'Erros.csv'
LOG_SUCCESS_FILE = 'Comunicados_Enviados.csv'
LOG_VERIFY_FILE = 'Verificacao.csv'

# Limits and defaults
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
VALID_ATTACHMENT_EXTENSIONS = ('.pdf', '.png', '.jpeg', '.jpg')
VALID_COVER_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')
REQUEST_TIMEOUT_SECONDS = 30
API_RETRY_DELAY_SECONDS = 2
API_MAX_RETRIES = 3  # Tentativas por requisição (só retenta quando é seguro; ver ApiClient)

# Autenticação
# Margem para renovar o token antes de expirar. Precisa ser maior que
# REQUEST_TIMEOUT_SECONDS, senão um upload longo pode começar com token válido
# e terminar com token expirado (401).
TOKEN_EXPIRY_BUFFER_SECONDS = 120

# Performance configurations
# A Agenda Edu recomenda no máximo 10 requisições por segundo. O limite é de
# vazão, não de concorrência: quem garante o teto é o RateLimiter, e as threads
# só definem quantos envios ficam em voo enquanto se espera a resposta.
# Mantido abaixo de 10 para deixar folga.
API_MAX_REQUESTS_PER_SECOND = 8.0
MAX_CONCURRENT_THREADS = 10  # Número máximo de threads simultâneas

# --- Janela entre criar e aprovar o comunicado ---------------------------
# A criação do comunicado é finalizada por um job em background. Aprovar antes
# de o job terminar deixa o comunicado aprovado no banco mas NUNCA publicado
# nem notificado pelo aplicativo — e sem erro nenhum. Por isso a aprovação
# só acontece depois desta janela.
HANDOUT_CREATION_MIN_WAIT_SECONDS = 3.0    # Piso: sempre aguardado antes de aprovar
HANDOUT_CREATION_MAX_WAIT_SECONDS = 120.0  # Teto da espera pela confirmação
HANDOUT_CREATION_POLL_INTERVAL_SECONDS = 2.0

# Como confirmar que o job de criação terminou, consultando GET /handouts/{id}.
# Com HANDOUT_READY_FIELD = None a ferramenta não consulta e apenas aguarda o
# piso acima antes de aprovar (comportamento original, baseado só em tempo).
# Preenchendo o campo e os valores de "pronto", a espera passa a ser precisa:
# aprova assim que o job terminar e nunca aprova antes disso.
# Ex.: HANDOUT_READY_FIELD = 'status'
#      HANDOUT_READY_VALUES = ('created', 'pending_approval')
HANDOUT_READY_FIELD = None
HANDOUT_READY_VALUES = ()

# CSV headers
CSV_ERROR_HEADER = ["ID", "Status"]
CSV_SUCCESS_HEADER = ["ID do Aluno", "Nome do Aluno", "ID do Comunicado"]
CSV_VERIFY_HEADER = ["ID do Aluno", "Nome do Aluno", "ID do Comunicado", "Situação"]
