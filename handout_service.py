import os
import time
from typing import Dict, Optional, Tuple
from api_client import ApiClient
from file_manager import FileManager
from logging_config import get_logger
from config import (
    HANDOUT_CATEGORIES_ENDPOINT, STUDENT_PROFILES_ENDPOINT,
    HANDOUTS_ENDPOINT,
    HANDOUT_CREATION_MIN_WAIT_SECONDS, HANDOUT_CREATION_MAX_WAIT_SECONDS,
    HANDOUT_CREATION_POLL_INTERVAL_SECONDS,
    HANDOUT_READY_FIELD, HANDOUT_READY_VALUES
)

# Campos que a API deve devolver para que o status do comunicado seja verificável.
HANDOUT_STATUS_FIELDS = frozenset({'approved', 'visible'})


class HandoutService:
    def __init__(self, api_client: ApiClient, file_manager: FileManager):
        self.api_client = api_client
        self.file_manager = file_manager
        self.logger = get_logger()

    def list_categories(self) -> Optional[Dict]:
        self.logger.info("Buscando categorias de comunicados...")
        try:
            return self.api_client.get(HANDOUT_CATEGORIES_ENDPOINT)
        except ConnectionError as e:
            self.logger.error(f"Falha ao buscar categorias: {e}")
            return None

    def get_student_classroom_info(self, student_id: str) -> Optional[Tuple[str, Optional[int]]]:
        self.logger.info(f"Buscando informações do aluno {student_id}...")
        endpoint = f"{STUDENT_PROFILES_ENDPOINT}/{str(student_id).strip()}"
        response_data = None
        try:
            response_data = self.api_client.get(endpoint)
            if response_data and isinstance(response_data, dict) and 'data' in response_data:
                student_name = response_data['data']['attributes']['name']
                classrooms_data = response_data['data']['relationships']['classrooms']['data']
                if classrooms_data:
                    highest_classroom_id = max(int(classroom['id']) for classroom in classrooms_data)
                    return student_name, highest_classroom_id
                else:
                    self.logger.warning(f"Aluno {student_id} ('{student_name}') não está associado a nenhuma sala.")
                    return student_name, None
            else:
                self.logger.error(f"Resposta inesperada da API ao buscar aluno {student_id}: {response_data}")
                return None
        except ConnectionError as e:
            self.logger.error(f"Erro de conexão ao buscar informações do aluno {student_id}: {e}")
            return None
        except (KeyError, TypeError, ValueError) as e:
            self.logger.error(f"Erro ao processar dados do aluno {student_id} da resposta da API: {e}. Resposta: {response_data}")
            return None

    def create_handout(self, student_id: str, classroom_id: int, title: str, description: str,
                       send_to: str, category_id: str, cover_image_path: Optional[str]) -> Optional[str]:
        self.logger.info(f"Criando comunicado para o aluno {student_id}...")

        student_attachment_info = self.file_manager.get_attachment_file_for_student(student_id)
        if not student_attachment_info:
            self.file_manager.log_error(student_id, "Arquivo de anexo específico do aluno não encontrado ou inválido")
            return None
        student_attachment_file_path, student_attachment_mime_type = student_attachment_info

        additional_files_info_list = self.file_manager.get_additional_files_info()

        payload = {
            'sendTo': send_to,
            'title': title,
            'description': description,
            'createdFor': 'students',
            'categoryId': category_id,
            'studentsFromClassroomId[][classroomId]': str(classroom_id),
            'studentsFromClassroomId[][studentIds][]': str(student_id)
        }

        files_for_api_request = []
        opened_file_objects = []

        try:
            sa_file_object = open(student_attachment_file_path, 'rb')
            opened_file_objects.append(sa_file_object)
            files_for_api_request.append(
                ('attachments[]',
                 (os.path.basename(student_attachment_file_path), sa_file_object, student_attachment_mime_type))
            )

            for add_file_path, add_file_mime, add_file_original_name in additional_files_info_list:
                add_file_object = open(add_file_path, 'rb')
                opened_file_objects.append(add_file_object)
                files_for_api_request.append(
                    ('attachments[]', (add_file_original_name, add_file_object, add_file_mime))
                )

            if cover_image_path:
                cover_mime_type = self.file_manager._get_mime_type(cover_image_path)
                if cover_mime_type:
                    cover_file_object = open(cover_image_path, 'rb')
                    opened_file_objects.append(cover_file_object)
                    files_for_api_request.append(
                        ('coverImage', (os.path.basename(cover_image_path), cover_file_object, cover_mime_type))
                    )
                else:
                    self.logger.warning(
                        f"Não foi possível determinar o tipo MIME para a imagem de capa: {cover_image_path}. O comunicado será enviado sem imagem de capa.")

            if not files_for_api_request:
                self.logger.error(f"Erro crítico: Nenhum arquivo preparado para envio para o aluno {student_id}")
                self.file_manager.log_error(student_id, "Nenhum arquivo preparado para envio (erro interno)")
                return None

            response_data_api = self.api_client.post(HANDOUTS_ENDPOINT, data=payload, files=files_for_api_request)

            if response_data_api and isinstance(response_data_api, dict) and response_data_api.get('data', {}).get(
                    'id'):
                handout_id = response_data_api['data']['id']
                self.logger.info(f"Comunicado criado com sucesso para o aluno {student_id}. ID: {handout_id}")
                return str(handout_id)
            else:
                self.logger.error(f"Erro ao criar comunicado para {student_id}. Resposta da API: {response_data_api}")
                self.file_manager.log_error(student_id,
                                            f"Falha na criação do comunicado. API Respondeu: {response_data_api}")
                return None
        except FileNotFoundError as fnf_err:
            self.logger.error(f"Erro de arquivo não encontrado ao preparar comunicado para {student_id}: {fnf_err}")
            self.file_manager.log_error(student_id, f"Arquivo não encontrado durante preparação: {fnf_err.filename}")
            return None
        except ConnectionError as e:
            self.logger.error(f"Erro de conexão ao criar comunicado para {student_id}: {e}")
            self.file_manager.log_error(student_id, f"Falha na criação do comunicado devido a erro na API: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Exceção inesperada ao criar comunicado para {student_id}: {e}")
            self.file_manager.log_error(student_id, f"Exceção inesperada na criação: {e}")
            return None
        finally:
            for f_obj in opened_file_objects:
                if f_obj:
                    try:
                        f_obj.close()
                    except Exception as e_close:
                        self.logger.warning(f"Aviso: Erro ao fechar arquivo no finally: {e_close}")

    def approve_handout(self, handout_id: str) -> bool:
        self.logger.info(f"Aprovando comunicado {handout_id}...")
        endpoint = f"{HANDOUTS_ENDPOINT}/{handout_id}/approve"
        payload = {'approve': True}

        try:
            self.api_client.patch(endpoint, json_data=payload)
            self.logger.info(f"Comunicado {handout_id} aprovado com sucesso.")
            return True
        except ConnectionError as e:
            self.logger.error(f"Falha ao aprovar comunicado {handout_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Exceção inesperada ao aprovar comunicado {handout_id}: {e}")
            return False

    def check_handout_status(self, handout_id: str) -> Optional[bool]:
        """
        Verifica se o comunicado está aprovado e visível na plataforma.

        Retorna True (pronto), False (ainda não ficou pronto) ou None quando não
        foi possível verificar — resposta fora do formato esperado ou falha na
        consulta. O None é o que impede que uma mudança no contrato da API
        transforme todo envio bem-sucedido em erro no relatório.
        """
        self.logger.info(f"Verificando status do comunicado {handout_id}...")

        attributes = self._get_handout_attributes(handout_id)
        if attributes is None:
            return None

        if not HANDOUT_STATUS_FIELDS.intersection(attributes.keys()):
            self.logger.warning(
                f"A API não retornou os campos {sorted(HANDOUT_STATUS_FIELDS)} para o comunicado {handout_id}. "
                f"Não é possível confirmar o status. Campos recebidos: {sorted(attributes.keys())}"
            )
            return None

        return bool(attributes.get('approved', False)) and bool(attributes.get('visible', False))

    def process_student_handout(self, student_id: str, title: str, description: str,
                                send_to: str, category_id: str, cover_image_path: Optional[str]) -> bool:
        """Processa o comunicado de um aluno. Retorna True apenas se o envio foi concluído."""
        self.logger.info(f"--- Iniciando processamento para o aluno {student_id} ---")

        student_info = self.get_student_classroom_info(student_id)
        if not student_info or student_info[1] is None:
            error_msg = "Aluno não encontrado na API ou sem sala de aula associada."
            if student_info and student_info[1] is None:
                error_msg = f"Aluno '{student_info[0]}' encontrado, mas não está associado a nenhuma sala de aula."

            self.logger.error(error_msg)
            self.file_manager.log_error(student_id, error_msg)
            return False

        student_name: str = student_info[0]
        classroom_id: int = student_info[1]

        self.logger.info(f"Aluno: {student_name}, Sala ID: {classroom_id}")

        handout_id = self.create_handout(
            student_id, classroom_id, title, description,
            send_to, category_id, cover_image_path
        )
        if not handout_id:
            # create_handout já registrou o motivo em Erros.csv.
            return False

        # Aprovar antes de o job de criação terminar deixa o comunicado
        # aprovado no banco mas nunca publicado nem notificado — falha
        # silenciosa. Só aprova depois desta janela.
        criado = self.wait_for_handout_created(handout_id)
        if criado is False:
            self.file_manager.log_error(
                student_id,
                f"Comunicado ID: {handout_id} não terminou o processamento em "
                f"{HANDOUT_CREATION_MAX_WAIT_SECONDS:.0f}s e NÃO foi aprovado, para não ser aprovado "
                f"sem ser enviado. Aprove manualmente depois de confirmar na plataforma (Nome: {student_name})"
            )
            return False

        if criado is None:
            self.logger.warning(
                f"Sem como confirmar que o processamento do comunicado {handout_id} terminou; "
                f"aprovando após a espera fixa de {HANDOUT_CREATION_MIN_WAIT_SECONDS:.0f}s "
                f"(aluno {student_id} - {student_name})."
            )

        if not self.approve_handout(handout_id):
            self.file_manager.log_error(student_id, f"Falha ao aprovar o comunicado ID: {handout_id} (Nome: {student_name})")
            return False

        # A publicação e a notificação também são feitas em background, com
        # tempo de fila variável. Esperar por elas aqui atrasaria o lote e
        # marcaria como falha um comunicado que só está na fila — essa
        # confirmação fica a cargo do comando `verify`.
        self.file_manager.log_success(student_id, student_name, handout_id)
        return True

    def _get_handout_attributes(self, handout_id: str) -> Optional[Dict]:
        """Busca data.attributes do comunicado. None quando não foi possível obter."""
        try:
            response = self.api_client.get(f"{HANDOUTS_ENDPOINT}/{handout_id}")
        except Exception as e:
            self.logger.warning(f"Não foi possível consultar o comunicado {handout_id}: {e}")
            return None

        if not isinstance(response, dict):
            self.logger.warning(f"Resposta inesperada ao consultar o comunicado {handout_id}: {response}")
            return None

        data = response.get('data')
        attributes = data.get('attributes') if isinstance(data, dict) else None
        if not isinstance(attributes, dict):
            self.logger.warning(f"Resposta sem 'data.attributes' ao consultar o comunicado {handout_id}: {response}")
            return None

        return attributes

    def check_handout_created(self, handout_id: str) -> Optional[bool]:
        """
        Verifica se o job de criação do comunicado já terminou.

        Retorna True (terminou), False (ainda em processamento) ou None quando
        não é possível saber — porque HANDOUT_READY_FIELD não foi configurado,
        porque a API não devolveu esse campo ou porque a consulta falhou.
        """
        if not HANDOUT_READY_FIELD:
            return None

        attributes = self._get_handout_attributes(handout_id)
        if attributes is None:
            return None

        if HANDOUT_READY_FIELD not in attributes:
            self.logger.warning(
                f"A API não retornou o campo '{HANDOUT_READY_FIELD}' para o comunicado {handout_id}. "
                f"Campos recebidos: {sorted(attributes.keys())}"
            )
            return None

        return attributes[HANDOUT_READY_FIELD] in HANDOUT_READY_VALUES

    def wait_for_handout_created(self, handout_id: str) -> Optional[bool]:
        """
        Aguarda o job de criação terminar, antes de aprovar.

        Sempre respeita o piso de HANDOUT_CREATION_MIN_WAIT_SECONDS. Depois
        dele, se houver como consultar o status, faz polling até o teto.

        Retorna True (confirmado pronto), False (confirmado que ainda não está
        pronto, estourou o teto) ou None (sem como confirmar — só o piso foi
        aguardado).
        """
        time.sleep(HANDOUT_CREATION_MIN_WAIT_SECONDS)

        if not HANDOUT_READY_FIELD:
            return None

        limite = time.monotonic() + HANDOUT_CREATION_MAX_WAIT_SECONDS
        conseguiu_consultar = False

        while True:
            status = self.check_handout_created(handout_id)
            if status is True:
                return True
            if status is False:
                conseguiu_consultar = True
            if time.monotonic() >= limite:
                break
            self.logger.info(f"Comunicado {handout_id} ainda em processamento. Aguardando para aprovar...")
            time.sleep(HANDOUT_CREATION_POLL_INTERVAL_SECONDS)

        return False if conseguiu_consultar else None

    def verify_handout(self, student_id: str, student_name: str, handout_id: str) -> Tuple[str, str, str, str]:
        """
        Confere na API se um comunicado já foi publicado.

        Retorna a linha do relatório: (id do aluno, nome, id do comunicado, status).
        """
        status = self.check_handout_status(handout_id)
        if status is True:
            situacao = 'Publicado'
        elif status is False:
            situacao = 'Pendente (em processamento)'
        else:
            situacao = 'Não foi possível verificar'
        return student_id, student_name, handout_id, situacao
