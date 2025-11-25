import os
import sqlite3
from math import trunc
import pandas as pd


# Função para limpar a tela
def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')


# Conectar ao banco SQLite
conn = sqlite3.connect("dbLotofacil.db")
cursor = conn.cursor()

# Criar tabela (se não existir)
cursor.execute("""
               CREATE TABLE IF NOT EXISTS conclt
               (
                   concurso
                   INTEGER
                   PRIMARY
                   KEY,
                   dtsorteio
                   TEXT,
                   d1
                   INTEGER,
                   d2
                   INTEGER,
                   d3
                   INTEGER,
                   d4
                   INTEGER,
                   d5
                   INTEGER,
                   d6
                   INTEGER,
                   d7
                   INTEGER,
                   d8
                   INTEGER,
                   d9
                   INTEGER,
                   d10
                   INTEGER,
                   d11
                   INTEGER,
                   d12
                   INTEGER,
                   d13
                   INTEGER,
                   d14
                   INTEGER,
                   d15
                   INTEGER,
                   qtganhador
                   INTEGER,
                   rateio15
                   REAL
               )
               """)
conn.commit()


# <--------->
# Função para inserir vários registros
def inserir_registros():
    limpar_tela()
    while True:
        try:
            concurso = int(input("Digite o número do concurso (ID): "))
        except ValueError:
            print("ID inválido. Digite um número inteiro.")
            continue

        data = input("Digite a data (dd/mm/aaaa): ").strip()

        valores = []
        for i in range(1, 16):
            while True:
                try:
                    valor = int(input(f"Digite o valor de D{i} (inteiro): "))
                    valores.append(valor)
                    break
                except ValueError:
                    print("Valor inválido. Digite um número inteiro.")

        # Opcional: quantidade de ganhadores e rateio
        qtganhador = None
        rateio15 = None
        entrada = input("Deseja informar qtganhador e rateio15 agora? (s/n): ").lower()
        if entrada == "s":
            try:
                qtganhador = int(input("Digite qtganhador (inteiro): "))
            except ValueError:
                qtganhador = None
            try:
                rateio15 = float(input("Digite rateio15 (ex: 1234.56): ").replace(",", "."))
            except ValueError:
                rateio15 = None

        cursor.execute("""
            INSERT OR REPLACE INTO conclt (
                concurso, dtsorteio,
                d1, d2, d3, d4, d5,
                d6, d7, d8, d9, d10,
                d11, d12, d13, d14, d15,
                qtganhador, rateio15
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (concurso, data, *valores, qtganhador, rateio15))
        conn.commit()
        print("✅ Registro inserido com sucesso!\n")

        continuar = input("Deseja cadastrar outro registro? (s/n): ").lower()
        if continuar != "s":
            break


# Função para listar todos os registros
def listar_registros():
    limpar_tela()
    cursor.execute("SELECT * FROM conclt")
    rows = cursor.fetchall()

    colunas = [
                  "concurso", "dtsorteio"
              ] + [f"d{i}" for i in range(1, 16)] + ["qtganhador", "rateio15"]

    if not rows:
        print("\n--- TODOS OS REGISTROS ---")
        print("Nenhum registro encontrado.\n")
        return

    df = pd.DataFrame(rows, columns=colunas)

    # Conversões de tipo seguras
    int_cols = ["concurso", "qtganhador"] + [f"d{i}" for i in range(1, 16)]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    if "rateio15" in df.columns:
        df["rateio15"] = pd.to_numeric(df["rateio15"], errors="coerce").astype(float)

    print("\n--- TODOS OS REGISTROS ---")
    print(df)
    print()


# Função para buscar registros e ordenar cada coluna separadamente + ranking
def buscar_registros():
    while True:
        limpar_tela()
        qtd = int(input("Digite a quantidade de sorteios que deseja ver: "))
        # Buscar os últimos sorteios de acordo com a quantidade
        cursor.execute(f"""
                SELECT concurso, dtsorteio, d1, d2, d3, d4, d5,
                       d6, d7, d8, d9, d10, d11, d12, d13, d14, d15
                FROM conclt
                ORDER BY concurso DESC
                LIMIT {qtd}
            """)
        rows = cursor.fetchall()

        if not rows:
            print("Nenhum registro encontrado.\n")
            return

        # Colunas alinhadas com a tabela criada
        colunas = ["concurso", "dtsorteio"] + [f"d{i}" for i in range(1, 16)]
        df = pd.DataFrame(rows, columns=colunas)

        # Apenas colunas d1..d15 para análise
        resultado = {}
        for col in [f"d{i}" for i in range(1, 16)]:
            resultado[col] = sorted(df[col].tolist())

        tabela = pd.DataFrame(resultado).astype(int)
        tabela.insert(0, "dtsorteio", df["dtsorteio"].values)
        tabela.insert(0, "concurso", df["concurso"].values)

        print("\n--- RESULTADO ORDENADO POR COLUNA ---")
        print(tabela)

        # Ranking dos 3 mais repetidos por coluna em formato de tabela
        ranking_final = {}
        for col in [f"d{i}" for i in range(1, 16)]:
            contagem = tabela[col].value_counts().head(3)
            contagem.index = contagem.index.astype(int)
            contagem = contagem.astype(int)
            ranking_final[col] = contagem

        ranking_df = pd.DataFrame(ranking_final).fillna("")

        print("\n--- RANKING DOS 3 MAIS REPETIDOS POR COLUNA ---")
        print(ranking_df)
        print()
        opcao = input("Deseja retornar ao menu inicial? (s/n) ").lower()
        if opcao == "s":
            limpar_tela()
            break

# Importa a planilha para o banco de dados
def import_planilha():
    limpar_tela()

    def ler_excel_com_moedas_convertidas(caminho_arquivo, sheet_name=0):
        # Lê o Excel
        df = pd.read_excel(caminho_arquivo, sheet_name=sheet_name)

        # Função auxiliar para detectar e converter valores monetários
        def converter_moeda(valor):
            if isinstance(valor, str) and 'R$' in valor:
                valor = valor.replace('R$', '').replace('.', '').replace(',', '.')
                try:
                    return float(valor)
                except ValueError:
                    return None
            return valor

        # Aplica conversão apenas em colunas com strings contendo "R$"
        for coluna in df.columns:
            if df[coluna].dtype == object and df[coluna].astype(str).str.contains('R\\$').any():
                df[coluna] = df[coluna].apply(converter_moeda)

        return df

    # Caminho do arquivo Excel
    arquivo_excel = 'Lotofácil.xlsx'

    # Nome da aba (sheet) que você quer ler
    nome_aba = 'LOTOFÁCIL'  # ou use sheet_name=0 para a primeira aba

    # Lê os dados da planilha
    df = ler_excel_com_moedas_convertidas(arquivo_excel, nome_aba)

    colunas_desejadas = ['Concurso', 'Data Sorteio', 'Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6', 'Bola7',
                         'Bola8', 'Bola9', 'Bola10', 'Bola11', 'Bola12', 'Bola13', 'Bola14', 'Bola15',
                         'Ganhadores 15 acertos', 'Rateio 15 acertos']

    df_filtrado = df[colunas_desejadas].copy()

    # Renomeia colunas para bater com a tabela
    df_filtrado.columns = [
        'concurso', 'dtsorteio',
        'd1', 'd2', 'd3', 'd4', 'd5',
        'd6', 'd7', 'd8', 'd9', 'd10',
        'd11', 'd12', 'd13', 'd14', 'd15',
        'qtganhador', 'rateio15'
    ]

    # Insere no banco (apenas novos ou atualiza existentes)
    for _, row in df_filtrado.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO conclt (
                concurso, dtsorteio,
                d1, d2, d3, d4, d5,
                d6, d7, d8, d9, d10,
                d11, d12, d13, d14, d15,
                qtganhador, rateio15
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(row))

    conn.commit()
    print("✅ Importação concluída! Dados novos foram inseridos/atualizados.\n")

# Função para buscar ranking global e sugerir apostas
def buscar_ranking_global():
    limpar_tela()
    qtd = int(input("Digite a quantidade de sorteios que deseja analisar: "))

    # Buscar os últimos sorteios
    cursor.execute(f"""
        SELECT d1, d2, d3, d4, d5,
               d6, d7, d8, d9, d10,
               d11, d12, d13, d14, d15
        FROM conclt
        ORDER BY concurso DESC
        LIMIT {qtd}
    """)
    rows = cursor.fetchall()

    if not rows:
        print("Nenhum registro encontrado.\n")
        return

    # Criar DataFrame com apenas as dezenas
    colunas = [f"d{i}" for i in range(1, 16)]
    df = pd.DataFrame(rows, columns=colunas)

    # Contagem global de todas as dezenas
    todas_dezenas = df.values.flatten()
    contagem = pd.Series(todas_dezenas).value_counts().sort_values(ascending=False)

    print("\n--- RANKING GLOBAL DAS DEZENAS ---")
    print(contagem)

    # Sugestões de apostas
    mais_frequentes = contagem.index.tolist()

    aposta15 = mais_frequentes[:15]
    aposta16 = mais_frequentes[:16]
    aposta17 = mais_frequentes[:17]

    menos_frequentes = contagem.index.tolist()[::-1]
    aposta15_inversa = menos_frequentes[:15]

    print("\n--- SUGESTÕES DE APOSTAS ---")
    print(f"15 dezenas (mais frequentes): {sorted(aposta15)}")
    print(f"16 dezenas (mais frequentes): {sorted(aposta16)}")
    print(f"17 dezenas (mais frequentes): {sorted(aposta17)}")
    print(f"15 dezenas (menos frequentes): {sorted(aposta15_inversa)}")

    # 🔎 Verificar se a aposta de 15 dezenas já ocorreu em algum concurso
    cursor.execute("""
        SELECT concurso, dtsorteio,
               d1, d2, d3, d4, d5,
               d6, d7, d8, d9, d10,
               d11, d12, d13, d14, d15
        FROM conclt
    """)
    todos_registros = cursor.fetchall()

    for registro in todos_registros:
        dezenas_registro = sorted(registro[2:17])  # pega d1..d15
        if dezenas_registro == aposta15:
            print("\n⚠️ Atenção: Essa combinação de 15 dezenas já ocorreu!")
            print(f"Concurso: {registro[0]} | Data: {registro[1]}")
            print(f"Dezenas: {dezenas_registro}")
            break
    else:
        print("\n✅ Nenhum concurso anterior teve exatamente essa combinação de 15 dezenas.")

    # git
    input("\nPressione ENTER para retornar ao menu...")
    limpar_tela()

# Menu principal
def menu():
    limpar_tela()
    while True:
        print("=== MENU PRINCIPAL ===")
        print("1 - Inserir registros")
        print("2 - Listar registros")
        print("3 - Buscar registros ordenados + ranking")
        print("4 - Importar registros do Excel")
        print("5 - Ranking global + sugestões de apostas")  # <-- NOVO

        print("0 - Sair")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            inserir_registros()
        elif opcao == "2":
            listar_registros()
        elif opcao == "3":
            buscar_registros()
        elif opcao == "4":
            import_planilha()
        elif opcao == "5":
            buscar_ranking_global()  # <-- NOVO

        elif opcao == "0":
            print("Saindo...")
            limpar_tela()
            break
        else:
            print("Opção inválida!\n")


# Executar menu
menu()
