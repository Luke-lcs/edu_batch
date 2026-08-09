import os
import csv
import threading
from typing import List, Tuple, Optional
from logging_config import get_logger
from config import (
    ATTACHMENT_FILES_DIR, ADDITIONAL_FILES_DIR, COVER_IMAGE_DIR,
    LOG_ERROR_FILE, LOG_SUCCESS_FILE,
    MAX_FILE_SIZE_BYTES, VALID_ATTACHMENT_EXTENSIONS,
    VALID_COVER_IMAGE_EXTENSIONS,
    CSV_ERROR_HEADER, CSV_SUCCESS_HEADER
)

class FileManager:
    def __init__(self):
        self.attachment_dir = ATTACHMENT_FILES_DIR
        self.additional_files_dir = ADDITIONAL_FILES_DIR
        self.cover_image_dir = COVER_IMAGE_DIR
        self.error_log_file = LOG_ERROR_FILE
        self.success_log_file = LOG_SUCCESS_FILE
        self._lock = threading.Lock()  # Lock para operações thread-safe
        self.logger = get_logger()
        self._ensure_directories_exist()

    def _ensure_directories_exist(self):
        for dir_path in [self.attachment_dir, self.cover_image_dir, self.additional_files_dir]:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path)
                    self.logger.info(f"Diretório '{dir_path}' foi criado.")
                    if dir_path == self.attachment_dir:
                        self.logger.info("Adicione os arquivos de anexo antes de continuar.")
                        self.logger.info("Cada arquivo deve ser nomeado com o ID do aluno (ex: 12345.pdf).")
                    elif dir_path == self.cover_image_dir:
                         self.logger.info("Adicione pelo menos uma imagem de capa (.jpg, .jpeg, .png) antes de continuar.")
                    elif dir_path == self.additional_files_dir:
                         self.logger.info("Adicione quaisquer arquivos adicionais comuns aqui, se necessário.")
                except OSError as e:
                    self.logger.error(f"Erro ao criar diretório '{dir_path}': {e}")

    def get_student_ids_from_attachments(self) -> List[str]:
        student_ids = []
        if not os.path.exists(self.attachment_dir):
            self.logger.warning(f"Diretório de anexos '{self.attachment_dir}' não encontrado.")
            return student_ids

        for filename in os.listdir(self.attachment_dir):
            file_path = os.path.join(self.attachment_dir, filename)
            if not os.path.isfile(file_path):
                continue

            # Arquivos descartados vão para o Erros.csv: um aluno pulado em
            # silêncio não aparece em nenhum dos dois relatórios.
            student_id = os.path.splitext(filename)[0]
            file_ext = os.path.splitext(filename)[1].lower()

            if file_ext not in VALID_ATTACHMENT_EXTENSIONS:
                self.log_error(student_id, f"Arquivo '{filename}' ignorado: extensão inválida ('{file_ext}'). Válidas: {VALID_ATTACHMENT_EXTENSIONS}")
                continue

            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE_BYTES:
                self.log_error(student_id, f"Arquivo '{filename}' ignorado: {file_size / (1024*1024):.2f}MB excede o limite de {MAX_FILE_SIZE_BYTES / (1024*1024):.0f}MB.")
                continue

            # O ID do aluno na Agenda Edu é numérico.
            if not student_id.isdigit():
                self.log_error(student_id, f"Arquivo '{filename}' ignorado: ID '{student_id}' não é um número inteiro válido.")
                continue

            student_ids.append(student_id)

        self.logger.info(f"Encontrados {len(student_ids)} arquivos de anexo válidos.")
        return student_ids

    def get_cover_image_path(self) -> Optional[str]:

        if not os.path.exists(self.cover_image_dir):
            self.logger.warning(f"Diretório de imagem de capa '{self.cover_image_dir}' não encontrado. Nenhuma imagem de capa será usada.")
            return None

        for filename in os.listdir(self.cover_image_dir):
            file_path = os.path.join(self.cover_image_dir, filename)
            if os.path.isfile(file_path) and filename.lower().endswith(VALID_COVER_IMAGE_EXTENSIONS):
                self.logger.info(f"Imagem de capa encontrada: {file_path}")
                return file_path

        self.logger.warning(f"Nenhuma imagem de capa válida {VALID_COVER_IMAGE_EXTENSIONS} encontrada em '{self.cover_image_dir}'. O comunicado será enviado sem imagem de capa.")
        return None

    def get_attachment_file_for_student(self, student_id: str) -> Optional[Tuple[str, str]]:
        for ext in VALID_ATTACHMENT_EXTENSIONS:
            filename = f"{student_id}{ext}"
            file_path = os.path.join(self.attachment_dir, filename)
            if os.path.exists(file_path):
                mime_type = self._get_mime_type(file_path)
                if mime_type:
                    return file_path, mime_type
                else:
                    self.logger.error(f"Não foi possível determinar o tipo MIME para o anexo: {filename}")
                    return None
        self.logger.error(f"Arquivo de anexo para o aluno {student_id} não encontrado nos formatos {VALID_ATTACHMENT_EXTENSIONS}.")
        return None

    def get_additional_files_info(self) -> List[Tuple[str, str, str]]:
        additional_files_list = []
        if not os.path.exists(self.additional_files_dir):
            self.logger.warning(
                f"Diretório de arquivos adicionais '{self.additional_files_dir}' não encontrado. Nenhum arquivo adicional será enviado.")
            return additional_files_list

        self.logger.info(f"Buscando arquivos adicionais em '{self.additional_files_dir}'...")
        for filename in os.listdir(self.additional_files_dir):
            file_path = os.path.join(self.additional_files_dir, filename)
            if not os.path.isfile(file_path):
                continue

            original_filename = filename
            file_ext = os.path.splitext(filename)[1].lower()

            if file_ext in VALID_ATTACHMENT_EXTENSIONS:
                file_size = os.path.getsize(file_path)
                if file_size <= MAX_FILE_SIZE_BYTES:
                    mime_type = self._get_mime_type(file_path)
                    if mime_type:
                        additional_files_list.append((file_path, mime_type, original_filename))
                    else:
                        self.logger.warning(
                            f"Arquivo adicional '{filename}': não foi possível determinar o tipo MIME. Será ignorado.")
                else:
                    self.logger.warning(
                        f"Arquivo adicional '{filename}' ({file_size / (1024 * 1024):.2f}MB) excede o limite de {MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f}MB e será ignorado.")
            else:
                self.logger.warning(
                    f"Arquivo adicional '{filename}' com extensão inválida ('{file_ext}'), será ignorado. Válidas: {VALID_ATTACHMENT_EXTENSIONS}")

        if additional_files_list:
            self.logger.info(f"Encontrados {len(additional_files_list)} arquivos adicionais válidos.")
        else:
            self.logger.info("Nenhum arquivo adicional válido encontrado ou o diretório está vazio.")
        return additional_files_list

    def _get_mime_type(self, file_path: str) -> Optional[str]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return 'application/pdf'
        elif ext in ('.jpg', '.jpeg'):
            return 'image/jpeg'
        elif ext == '.png':
            return 'image/png'
        return None

    def _prepare_csv_file(self, filepath: str, header: List[str]):
        if not os.path.exists(filepath):
            try:
                with open(filepath, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(header)
            except IOError as e:
                self.logger.error(f"Erro ao criar arquivo CSV '{filepath}': {e}")


    def initialize_log_files(self):
        self._prepare_csv_file(self.error_log_file, CSV_ERROR_HEADER)
        self._prepare_csv_file(self.success_log_file, CSV_SUCCESS_HEADER)

    def log_error(self, student_id: str, status: str):
        self.logger.error(f"Erro [Aluno: {student_id}]: {status}")
        with self._lock:  # Thread-safe logging
            try:
                with open(self.error_log_file, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow([student_id, status])
            except IOError as e:
                self.logger.error(f"Erro ao escrever no log de erros '{self.error_log_file}': {e}")


    def log_success(self, student_id: str, student_name: str, handout_id: str):
        self.logger.info(f"Sucesso [Aluno: {student_id}]: Comunicado {handout_id} enviado.")
        with self._lock:  # Thread-safe logging
            try:
                with open(self.success_log_file, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow([student_id, student_name, handout_id])
            except IOError as e:
                self.logger.error(f"Erro ao escrever no log de sucessos '{self.success_log_file}': {e}")
