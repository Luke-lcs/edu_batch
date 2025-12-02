import os
import csv
import threading
import logging
from typing import List, Tuple, Optional
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
        self._ensure_directories_exist()
        self.logger = self._setup_logging()

    def _setup_logging(self):
        logger = logging.getLogger('EduBatch')
        logger.setLevel(logging.INFO)
        
        # Avoid adding handlers multiple times
        if not logger.handlers:
            # File Handler
            file_handler = logging.FileHandler('app.log')
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            # Console Handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('%(message)s') # Simpler format for console
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger

    def _ensure_directories_exist(self):
        for dir_path in [self.attachment_dir, self.cover_image_dir, self.additional_files_dir]:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path)
                    print(f"Diretório '{dir_path}' foi criado.")
                    if dir_path == self.attachment_dir:
                        print("Adicione os arquivos de anexo antes de continuar.")
                        print("Cada arquivo deve ser nomeado com o ID do aluno (ex: 12345.pdf).")
                    elif dir_path == self.cover_image_dir:
                         print("Adicione pelo menos uma imagem de capa (.jpg, .jpeg, .png) antes de continuar.")
                    elif dir_path == self.additional_files_dir:
                         print("Adicione quaisquer arquivos adicionais comuns aqui, se necessário.")
                except OSError as e:
                    print(f"Erro ao criar diretório '{dir_path}': {e}")

    def get_student_ids_from_attachments(self) -> List[str]:
        student_ids = []
        if not os.path.exists(self.attachment_dir):
            print(f"Diretório de anexos '{self.attachment_dir}' não encontrado.")
            return student_ids

        for filename in os.listdir(self.attachment_dir):
            file_path = os.path.join(self.attachment_dir, filename)
            if not os.path.isfile(file_path):
                continue

            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in VALID_ATTACHMENT_EXTENSIONS:
                file_size = os.path.getsize(file_path)
                if file_size <= MAX_FILE_SIZE_BYTES:
                    student_id = os.path.splitext(filename)[0]
                    student_ids.append(student_id)
                else:
                    print(f"Arquivo '{filename}' ({file_size / (1024*1024):.2f}MB) excede o limite de {MAX_FILE_SIZE_BYTES / (1024*1024):.0f}MB e será ignorado.")
            else:
                print(f"Arquivo '{filename}' com extensão inválida ('{file_ext}'), será ignorado. Válidas: {VALID_ATTACHMENT_EXTENSIONS}")

        print(f"Encontrados {len(student_ids)} arquivos de anexo válidos.")
        return student_ids

    def get_cover_image_path(self) -> Optional[str]:

        if not os.path.exists(self.cover_image_dir):
            print(f"Diretório de imagem de capa '{self.cover_image_dir}' não encontrado. Nenhuma imagem de capa será usada.")
            return None

        for filename in os.listdir(self.cover_image_dir):
            file_path = os.path.join(self.cover_image_dir, filename)
            if os.path.isfile(file_path) and filename.lower().endswith(VALID_COVER_IMAGE_EXTENSIONS):
                print(f"Imagem de capa encontrada: {file_path}")
                return file_path

        print(f"Nenhuma imagem de capa válida {VALID_COVER_IMAGE_EXTENSIONS} encontrada em '{self.cover_image_dir}'. O comunicado será enviado sem imagem de capa.")
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
                    print(f"Não foi possível determinar o tipo MIME para o anexo: {filename}")
                    return None
        print(f"Arquivo de anexo para o aluno {student_id} não encontrado nos formatos {VALID_ATTACHMENT_EXTENSIONS}.")
        return None

    def get_additional_files_info(self) -> List[Tuple[str, str, str]]:
        additional_files_list = []
        if not os.path.exists(self.additional_files_dir):
            print(
                f"Diretório de arquivos adicionais '{self.additional_files_dir}' não encontrado. Nenhum arquivo adicional será enviado.")
            return additional_files_list

        print(f"Buscando arquivos adicionais em '{self.additional_files_dir}'...")
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
                        print(
                            f"Arquivo adicional '{filename}': não foi possível determinar o tipo MIME. Será ignorado.")
                else:
                    print(
                        f"Arquivo adicional '{filename}' ({file_size / (1024 * 1024):.2f}MB) excede o limite de {MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f}MB e será ignorado.")
            else:
                print(
                    f"Arquivo adicional '{filename}' com extensão inválida ('{file_ext}'), será ignorado. Válidas: {VALID_ATTACHMENT_EXTENSIONS}")

        if additional_files_list:
            print(f"Encontrados {len(additional_files_list)} arquivos adicionais válidos.")
        else:
            print("Nenhum arquivo adicional válido encontrado ou o diretório está vazio.")
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
                print(f"Erro ao criar arquivo CSV '{filepath}': {e}")


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
