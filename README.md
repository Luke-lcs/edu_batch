# Edu Batch - Automação de Comunicados Agenda Edu

Ferramenta de linha de comando (CLI) para envio em lote de comunicados na plataforma Agenda Edu, com suporte a processamento paralelo, renomeação de arquivos e limpeza automática.

## 📋 Funcionalidades

- **Envio em Lote**: Envia comunicados personalizados para múltiplos alunos simultaneamente.
- **Alta Performance**: Utiliza processamento paralelo (threads) para maximizar a velocidade de envio.
- **Resiliência**: Sistema de reconexão automática e renovação de tokens de autenticação.
- **Utilitários de Arquivo**: Ferramentas integradas para renomear arquivos e limpar anexos já enviados.
- **Logs Detalhados**: Registro completo de sucessos e erros em CSV e logs de aplicação (`app.log`).

## 🚀 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- Pip (gerenciador de pacotes do Python)

### Passo a Passo

1. **Clone o repositório** (se ainda não o fez):
   ```bash
   git clone <url-do-repositorio>
   cd edu_batch_sc6716
   ```

2. **Crie um ambiente virtual (recomendado)**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuração

### Estrutura de Pastas
A ferramenta cria automaticamente as pastas necessárias na primeira execução, mas você deve organizá-las assim:

- **`attachment_files/`**: Coloque aqui os arquivos PDF/Imagens que serão enviados.
  - **Importante**: O nome do arquivo deve ser o ID do aluno. Ex: `12345.pdf`.
- **`cover_image/`**: (Opcional) Coloque uma imagem (.jpg, .png) para ser a capa do comunicado.
- **`files_to_send/`**: Diretório auxiliar para usar as ferramentas de renomeação.

### Credenciais
Ao iniciar o envio, você precisará informar:
1. **Client ID** (API Agenda Edu)
2. **Client Secret** (API Agenda Edu)
3. **Token da Escola** (`x-school-token`)

## 📖 Como Usar

A ferramenta possui um comando principal (`main.py`) com vários subcomandos.

### 1. Enviar Comunicados (`send`)
Este é o comando principal. Ele vai ler os arquivos da pasta `attachment_files/`, pedir as credenciais e iniciar o envio.

```bash
python main.py send
# ou apenas
python main.py
```

**Fluxo:**
1. Digite as credenciais.
2. Defina o Título e a Descrição do comunicado.
3. Escolha a Categoria e o Público Alvo (Alunos/Responsáveis).
4. Confirme o envio.

### 2. Limpar Arquivos Enviados (`cleanup`)
Remove da pasta de anexos os arquivos que foram enviados com sucesso (baseado no log `Comunicados_Enviados.csv`). Útil para liberar espaço ou preparar o próximo lote.

```bash
# Modo seguro (apenas simula)
python main.py cleanup --dry-run

# Modo real (apaga os arquivos)
python main.py cleanup
```

### 3. Renomear Arquivos (`rename`)
Remove sufixos de nomes de arquivos. Útil se você baixou arquivos com nomes como `12345 - Nome do Aluno.pdf` e precisa deixá-los apenas como `12345.pdf`.

```bash
python main.py rename --dir files_to_send
```

### 4. Renomear via Mapeamento (`map-rename`)
Renomeia arquivos baseando-se em um CSV "De/Para". Útil quando o arquivo tem um ID externo e você precisa converter para o ID do aluno na Agenda Edu.

**Formato do CSV (`files_to_send.csv`):**
```csv
EXTERNAL_ID,ID
cod_sistema_antigo,12345
```

**Comando:**
```bash
python main.py map-rename --csv files_to_send.csv
```

## 📊 Logs e Monitoramento

- **`app.log`**: Log técnico detalhado. Verifique aqui se algo der errado (erros de conexão, falhas de API).
- **`Comunicados_Enviados.csv`**: Lista de envios bem sucedidos. Colunas: `ID do Aluno`, `Nome`, `ID do Comunicado`.
- **`Erros.csv`**: Lista de falhas. Colunas: `ID`, `Status/Erro`.

## 🛠️ Resolução de Problemas comum

- **Erro de Autenticação**: Verifique se o token expirou ou se as credenciais estão corretas. O sistema tenta renovar automaticamente, mas credenciais inválidas falharão imediatamente.
- **Arquivo não encontrado**: Certifique-se de que o arquivo na pasta `attachment_files` tem **exatamente** o ID do aluno como nome (ex: `10.pdf` para o aluno de ID 10).
- **Rate Limit**: Se houver muitos erros de conexão, tente reduzir o número de threads no arquivo `config.py` (`MAX_CONCURRENT_THREADS`).

## ⚙️ Configurações avançadas (`config.py`)

- `MAX_CONCURRENT_THREADS`: Número de envios simultâneos. Comece baixo e aumente conforme a API suportar.
- `API_MAX_RETRIES`: Tentativas por requisição. Retentativas só ocorrem quando são seguras (ver abaixo).
- `MAX_FILE_SIZE_BYTES`: Tamanho máximo de cada anexo (padrão 100MB).
- `REQUEST_TIMEOUT_SECONDS`: Timeout das requisições. Aumente se ocorrerem erros de `Read timed out` em rede lenta ou com arquivos muito grandes.
- `TOKEN_EXPIRY_BUFFER_SECONDS`: Margem de segurança para renovar o token antes de expirar. Deve ser maior que `REQUEST_TIMEOUT_SECONDS`.
- `HANDOUT_STATUS_CHECK_ATTEMPTS` / `HANDOUT_STATUS_CHECK_DELAY`: Tentativas e intervalo da verificação de que o comunicado ficou pronto após a aprovação.
- `VALID_ATTACHMENT_EXTENSIONS` / `VALID_COVER_IMAGE_EXTENSIONS`: Extensões permitidas.

### Política de retentativas

Para nunca gerar comunicado duplicado, a retentativa automática segue estas regras:

| Situação | GET / PATCH | POST (criação do comunicado) |
| --- | --- | --- |
| HTTP 429 (rate limit) | Retenta (respeita `Retry-After`) | Retenta (a requisição foi recusada, não processada) |
| HTTP 5xx | Retenta | **Não** retenta — o servidor pode ter criado o comunicado |
| Timeout de conexão | Retenta | Retenta (a conexão nem foi estabelecida) |
| Demais falhas de rede | Retenta | **Não** retenta |

Antes de cada retentativa os anexos são rebobinados (`seek(0)`) e o token de autenticação é revalidado.

## Contribuindo

Contribuições são bem-vindas! Se tiver sugestões de melhoria ou encontrar um bug, abra uma issue ou envie um pull request.

---
Desenvolvido para otimizar a operação da Agenda Edu.

**Copyright (C) 2025 Lucas Monteiro**
