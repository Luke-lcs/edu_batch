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
MAX_CONCURRENT_THREADS = 4  # Número máximo de threads simultâneas
HANDOUT_STATUS_CHECK_ATTEMPTS = 8  # Tentativas para verificar status do comunicado
HANDOUT_STATUS_CHECK_DELAY = 1.0  # Delay entre verificações de status (segundos)

# CSV headers
CSV_ERROR_HEADER = ["ID", "Status"]
CSV_SUCCESS_HEADER = ["ID do Aluno", "Nome do Aluno", "ID do Comunicado"]
