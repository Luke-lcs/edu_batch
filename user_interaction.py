from typing import Dict, Any, Optional, List, Tuple

def get_credentials() -> Optional[Dict[str, str]]:
    print("\n--- Credenciais da API ---")
    client_id = input("Digite o Client ID: ").strip()
    client_secret = input("Digite o Client Secret: ").strip()
    x_school_token = input('Digite o Token da Escola: ').strip()

    if not all([client_id, client_secret, x_school_token]):
        print("Todas as credenciais são obrigatórias. Encerrando.")
        return None
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "x_school_token": x_school_token
    }

def get_handout_details() -> Optional[Dict[str, str]]:
    print("\n--- Configuração do Comunicado ---")
    title = input("Digite o Título do Comunicado: ").strip()
    if not title:
        print("O Título do comunicado é obrigatório. Encerrando.")
        return None

    print("\nDigite a Descrição do Comunicado.")
    print("Você pode usar tags HTML para formatação (ex: <p>, <strong>, <ol>, <li>).")
    print("Para finalizar a entrada da descrição, pressione Enter duas vezes (deixe uma linha em branco e pressione Enter)")
    print("ou digite 'EOF' (sem aspas) em uma nova linha e pressione Enter.")

    description_lines = []
    print("Descrição:")
    
    while True:
        line = input()
        if line.strip().upper() == "EOF":
            break
        if not line and description_lines:
            if not description_lines[-1]:
                 description_lines.pop()
                 break

        description_lines.append(line)
    description = "\n".join(description_lines).strip()

    if not description:
        print("A Descrição do comunicado é obrigatória e não pode ser vazia. Encerrando.")
        return None

    print(f"\n--- Título e Descrição Configurados ---")
    print(f"Título: {title}")
    preview_len = 100
    description_preview = description[:preview_len]
    if len(description) > preview_len:
        description_preview += "..."
    print(f"Descrição (prévia): {description_preview}")

    return {"title": title, "description": description}

def select_handout_category(categories_data: Optional[Dict]) -> Optional[str]:
    if not categories_data or not categories_data.get('data'):
        print("Não há categorias de comunicado disponíveis ou ocorreu um erro ao buscá-las.")
        return None

    options: Dict[int, Tuple[str, str]] = {}
    print('\nCategorias de Comunicado Disponíveis:')
    for i, item in enumerate(categories_data['data']):
        category_id = item.get("id")
        category_name = item.get("attributes", {}).get("name")
        if category_id and category_name:
            options[i + 1] = (str(category_id), category_name)
            print(f'{i + 1}: {category_name} (ID: {category_id})')
        else:
            print(f"Item de categoria inválido encontrado: {item}")

    if not options:
        print("Nenhuma categoria válida encontrada.")
        return None

    attempts = 0
    max_attempts = 3
    while attempts < max_attempts:
        try:
            choice_str = input(f'Escolha o número da categoria do comunicado (1-{len(options)}): ').strip()
            choice = int(choice_str)
            if choice in options:
                selected_id, selected_name = options[choice]
                print(f"Categoria selecionada: '{selected_name}' (ID: {selected_id})")
                return selected_id
            else:
                print(f'Opção inválida. Por favor, escolha um número entre 1 e {len(options)}.')
        except ValueError:
            print('Entrada inválida. Por favor, digite um número.')
        attempts += 1
        if attempts < max_attempts:
            print(f"Tentativas restantes: {max_attempts - attempts}")

    print('Muitas tentativas inválidas. Encerrando seleção de categoria.')
    return None

def select_send_to_target() -> Optional[str]:
    options = {
        1: ("responsibles", "Responsáveis"),
        2: ("students", "Alunos"),
        3: ("both", "Ambos (Responsáveis e Alunos)")
    }
    print('\nOpções de Envio do Comunicado:')
    for key, (_, display_name) in options.items():
        print(f'{key}: {display_name}')

    attempts = 0
    max_attempts = 3
    while attempts < max_attempts:
        try:
            choice_str = input(f'Escolha o número da opção de envio (1-{len(options)}): ').strip()
            choice = int(choice_str)
            if choice in options:
                selected_target_value, selected_target_name = options[choice]
                print(f"Enviar para: '{selected_target_name}'")
                return selected_target_value
            else:
                print(f'Opção inválida. Por favor, escolha um número entre 1 e {len(options)}.')
        except ValueError:
            print('Entrada inválida. Por favor, digite um número.')
        attempts += 1
        if attempts < max_attempts:
            print(f"Tentativas restantes: {max_attempts - attempts}")

    print('Muitas tentativas inválidas. Encerrando seleção de envio.')
    return None

def confirm_send_operation(student_count: int, title: str, category_id: str, send_to: str) -> bool:
    print(f"\n--- Resumo da Operação ---")
    print(f"Serão processados {student_count} comunicados com os seguintes detalhes:")
    print(f"- Título: {title}")
    print(f"- Categoria ID: {category_id}")
    print(f"- Destinatários: {send_to}")

    confirm = input("\nConfirma o início do envio dos comunicados? (s/n): ").strip().lower()
    return confirm == 's'
