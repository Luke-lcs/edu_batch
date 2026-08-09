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

**Sobre o processamento em background:** a Agenda Edu finaliza a criação do
comunicado num job assíncrono. Aprovar antes de esse job terminar deixa o
comunicado aprovado no banco mas **nunca publicado nem notificado pelo
aplicativo**, e sem erro nenhum. Por isso a ferramenta espera entre criar e
aprovar — veja `Janela entre criar e aprovar` nas configurações avançadas.

A publicação em si também é assíncrona, e essa o envio não espera. Use o
`verify` depois para confirmar o que já saiu.

### 2. Verificar Publicação (`verify`)
Relê o `Comunicados_Enviados.csv` e consulta na API quais comunicados já foram
publicados. Pode ser rodado quantas vezes quiser, até que não sobrem pendentes.

```bash
python main.py verify
```

Gera o `Verificacao.csv` com uma linha por comunicado e uma destas situações:

- **Publicado**: já está visível na plataforma.
- **Pendente (em processamento)**: ainda na fila de background. Rode de novo mais tarde.
- **Não foi possível verificar**: a consulta falhou ou a resposta veio fora do formato esperado. Não significa que o envio falhou.

### 3. Limpar Arquivos Enviados (`cleanup`)
Remove da pasta de anexos os arquivos que foram enviados com sucesso (baseado no log `Comunicados_Enviados.csv`). Útil para liberar espaço ou preparar o próximo lote.

```bash
# Modo seguro (apenas simula)
python main.py cleanup --dry-run

# Modo real (apaga os arquivos)
python main.py cleanup
```

### 4. Renomear Arquivos (`rename`)
Remove sufixos de nomes de arquivos. Útil se você baixou arquivos com nomes como `12345 - Nome do Aluno.pdf` e precisa deixá-los apenas como `12345.pdf`.

```bash
python main.py rename --dir files_to_send
```

### 5. Renomear via Mapeamento (`map-rename`)
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
- **`Comunicados_Enviados.csv`**: Lista de comunicados criados e aprovados. Colunas: `ID do Aluno`, `Nome`, `ID do Comunicado`.
- **`Erros.csv`**: Lista de falhas, incluindo anexos descartados na varredura (extensão inválida, tamanho acima do limite, ID não numérico). Colunas: `ID`, `Status/Erro`.
- **`Verificacao.csv`**: Gerado pelo `verify`. Colunas: `ID do Aluno`, `Nome`, `ID do Comunicado`, `Situação`.

## 🛠️ Resolução de Problemas comum

- **Erro de Autenticação**: Verifique se o token expirou ou se as credenciais estão corretas. O sistema tenta renovar automaticamente, mas credenciais inválidas falharão imediatamente.
- **Arquivo não encontrado**: Certifique-se de que o arquivo na pasta `attachment_files` tem **exatamente** o ID do aluno como nome (ex: `10.pdf` para o aluno de ID 10).
- **Rate Limit**: A vazão é limitada por `API_MAX_REQUESTS_PER_SECOND` (não pelo número de threads). Se ainda houver erros 429, reduza esse valor.
- **Comunicado não aparece na plataforma**: A publicação é assíncrona. Rode `python main.py verify` para ver se ainda está na fila de processamento.
- **Comunicado aprovado que nunca chegou aos responsáveis**: Sinal de que a aprovação aconteceu antes de o job de criação terminar. Aumente `HANDOUT_CREATION_MIN_WAIT_SECONDS` ou, melhor, configure `HANDOUT_READY_FIELD`.

## ⚙️ Configurações avançadas (`config.py`)

- `API_MAX_REQUESTS_PER_SECOND`: Teto de vazão contra a API (padrão `8.0`). A Agenda Edu recomenda no máximo 10 req/s **por token de escola**; o padrão deixa folga. Se outras integrações suas consumirem a mesma cota, reduza.
- `MAX_CONCURRENT_THREADS`: Quantos envios ficam em voo ao mesmo tempo. **Não** controla a vazão — quem garante o teto de req/s é o `RateLimiter`. Serve para aproveitar o tempo de espera das respostas.
- `API_MAX_RETRIES`: Tentativas por requisição. Retentativas só ocorrem quando são seguras (ver abaixo).
- `MAX_FILE_SIZE_BYTES`: Tamanho máximo de cada anexo (padrão 100MB).
- `REQUEST_TIMEOUT_SECONDS`: Timeout das requisições. Aumente se ocorrerem erros de `Read timed out` em rede lenta ou com arquivos muito grandes.
- `TOKEN_EXPIRY_BUFFER_SECONDS`: Margem de segurança para renovar o token antes de expirar. Deve ser maior que `REQUEST_TIMEOUT_SECONDS`.
- `VALID_ATTACHMENT_EXTENSIONS` / `VALID_COVER_IMAGE_EXTENSIONS`: Extensões permitidas.

### Janela entre criar e aprovar

Aprovar um comunicado antes de o job de criação terminar é uma falha
silenciosa: ele fica aprovado no banco e nunca é enviado. A ferramenta tem dois
modos para evitar isso.

**Por tempo (padrão).** Com `HANDOUT_READY_FIELD = None`, espera
`HANDOUT_CREATION_MIN_WAIT_SECONDS` (padrão 3s) e aprova. Não consulta a API,
então não gasta orçamento de req/s — mas é um chute sobre a duração do job.

**Por confirmação (recomendado).** Preenchendo o campo da resposta de
`GET /handouts/{id}` que indica job concluído, a espera passa a ser exata:

```python
HANDOUT_READY_FIELD = 'status'
HANDOUT_READY_VALUES = ('created', 'pending_approval')
```

A ferramenta aguarda o piso, consulta a cada `HANDOUT_CREATION_POLL_INTERVAL_SECONDS`
e aprova assim que o job terminar. Se estourar `HANDOUT_CREATION_MAX_WAIT_SECONDS`
sem confirmar, **não aprova** e registra o ID no `Erros.csv` para aprovação
manual — um comunicado não aprovado é visível e corrigível; um aprovado sem ser
enviado, não.

### Política de retentativas

Para nunca gerar comunicado duplicado, a retentativa automática segue estas regras:

| Situação | GET / PATCH | POST (criação do comunicado) |
| --- | --- | --- |
| HTTP 429 (rate limit) | Retenta (respeita `Retry-After`) | Retenta (a requisição foi recusada, não processada) |
| HTTP 5xx | Retenta | **Não** retenta — o servidor pode ter criado o comunicado |
| Timeout de conexão | Retenta | Retenta (a conexão nem foi estabelecida) |
| Demais falhas de rede | Retenta | **Não** retenta |

Antes de cada retentativa os anexos são rebobinados (`seek(0)`) e o token de autenticação é revalidado. Toda requisição — inclusive retentativas, autenticação e verificações de status — passa pelo limitador de vazão.

## Contribuindo

Contribuições são bem-vindas! Se tiver sugestões de melhoria ou encontrar um bug, abra uma issue ou envie um pull request.

---
Desenvolvido para otimizar a operação da Agenda Edu.

**Copyright (C) 2025 Lucas Monteiro**
