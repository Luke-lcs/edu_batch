import user_interaction
from api_auth import Authenticator
from api_client import ApiClient
from file_manager import FileManager
from handout_service import HandoutService

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

    # 11. Processar Comunicados para cada Aluno
    print(f"\nIniciando o envio de {len(student_ids)} comunicados...")
    envios_sucesso = 0
    envios_falha = 0

    for student_id in student_ids:
        try:
            handout_svc.process_student_handout(
                student_id,
                handout_details["title"],
                handout_details["description"],
                send_to_target,
                selected_category_id,
                cover_image_file_path
            )
        except Exception as e:
            print(f"Erro crítico não tratado ao processar o aluno {student_id} no loop principal: {e}")
            file_mgr.log_error(student_id, f"Erro crítico no main loop: {e}")
            envios_falha +=1


    print("\n--- Processamento Concluído ---")
    print(f"Verifique os arquivos '{file_mgr.success_log_file}' e '{file_mgr.error_log_file}' para o status detalhado de cada envio.")

if __name__ == "__main__":
    main()
