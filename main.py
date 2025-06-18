import user_interaction
from api_auth import Authenticator
from api_client import ApiClient
from file_manager import FileManager
from handout_service import HandoutService
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from config import MAX_CONCURRENT_THREADS, BATCH_SIZE

def main():
    print("=== Sistema de Envio de Comunicados Agenda Edu===\n")

    # 0. Inicializar gerenciador de arquivos (cria pastas e logs se necessário)
    file_mgr = FileManager()
    file_mgr.initialize_log_files()

    # 1. Obter Credenciais
    credentials = user_interaction.get_credentials()
    if not credentials:
        return

    # 2. Autenticar
    authenticator = Authenticator(credentials["client_id"], credentials["client_secret"])
    if not authenticator.try_auth(): # Tenta autenticar
        print("Falha na autenticação inicial. Verifique suas credenciais e tente novamente.")
        return

    # 3. Inicializar Cliente API
    api_cli = ApiClient(authenticator, credentials["x_school_token"])

    # 4. Inicializar Serviços
    handout_svc = HandoutService(api_cli, file_mgr)

    # 5. Obter Detalhes do Comunicado (Título, Descrição)
    handout_details = user_interaction.get_handout_details()
    if not handout_details:
        return

    # 6. Listar e Selecionar Categoria do Comunicado
    available_categories = handout_svc.list_categories()
    selected_category_id = user_interaction.select_handout_category(available_categories)
    if not selected_category_id:
        print("Nenhuma categoria de comunicado selecionada. Encerrando.")
        return

    # 7. Selecionar Destinatários (send_to)
    send_to_target = user_interaction.select_send_to_target()
    if not send_to_target:
        print("Nenhum destinatário selecionado. Encerrando.")
        return

    # 8. Obter Lista de Alunos (IDs dos arquivos de anexo)
    student_ids = file_mgr.get_student_ids_from_attachments()
    if not student_ids:
        print("Nenhum arquivo de aluno válido encontrado para processamento. Verifique o diretório de anexos.")
        return

    # 9. Obter Imagem de Capa (agora opcional)
    cover_image_file_path = file_mgr.get_cover_image_path()
    if cover_image_file_path:
        print(f"Usando imagem de capa: {cover_image_file_path}")
    else:
        print("Continuando sem imagem de capa para os comunicados.")

    # 10. Confirmar Operação
    if not user_interaction.confirm_send_operation(
        len(student_ids),
        handout_details["title"],
        selected_category_id,
        send_to_target
    ):
        print("Operação cancelada pelo usuário.")
        return

    # 11. Processar Comunicados em Paralelo
    print(f"\nIniciando o envio de {len(student_ids)} comunicados em paralelo...")

    # Configurar número de workers baseado nas configurações
    max_workers = min(MAX_CONCURRENT_THREADS, len(student_ids))
    print(f"Usando {max_workers} threads para processamento paralelo")

    envios_sucesso = 0
    envios_falha = 0

    # Lock para operações thread-safe
    lock = threading.Lock()

    def process_student(student_id):
        try:
            handout_svc.process_student_handout(
                student_id,
                handout_details["title"],
                handout_details["description"],
                send_to_target,
                selected_category_id,
                cover_image_file_path
            )
            with lock:
                nonlocal envios_sucesso
                envios_sucesso += 1
        except Exception as e:
            print(f"Erro crítico não tratado ao processar o aluno {student_id}: {e}")
            file_mgr.log_error(student_id, f"Erro crítico no processamento paralelo: {e}")
            with lock:
                nonlocal envios_falha
                envios_falha += 1

    # Executar processamento paralelo
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submeter todas as tarefas
        future_to_student = {
            executor.submit(process_student, student_id): student_id
            for student_id in student_ids
        }

        # Processar resultados conforme completam
        for future in as_completed(future_to_student):
            student_id = future_to_student[future]
            try:
                future.result()  # Isso vai capturar qualquer exceção
            except Exception as e:
                print(f"Erro inesperado no processamento do aluno {student_id}: {e}")

    print("\n--- Processamento Concluído ---")
    print(f"Sucessos: {envios_sucesso}, Falhas: {envios_falha}")
    print(f"Verifique os arquivos '{file_mgr.success_log_file}' e '{file_mgr.error_log_file}' para o status detalhado de cada envio.")

if __name__ == "__main__":
    main()
