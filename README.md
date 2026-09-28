# RJE Avaliações - Sistema de Gestão para Personal Trainers

**Versão:** v1.1.0  (veja [MELHORIAS_v1.1.0.md](MELHORIAS_v1.1.0.md))
  
**Desenvolvido por:** RJE Tecnologia

O **RJE Avaliações** é um software completo e intuitivo desenvolvido em Python (CustomTkinter) para auxiliar Personal Trainers na gestão de seus alunos, avaliações físicas, prescrição de treinos e agenda.

---

## 🚀 Funcionalidades Principais

### 1. **Gestão de Alunos**
*   Cadastro completo de alunos (Dados pessoais, contato, anamnese básica).
*   Histórico de avaliações e treinos vinculados a cada aluno.
*   Busca rápida e listagem organizada com design compacto.
*   Máscaras de formatação automáticas (CPF, CEP, Telefone, Data).

### 2. **Avaliações Físicas**
*   Registro de medidas antropométricas (perímetros, dobras cutâneas).
*   **Controle de Pressão Arterial:** Registro de PA sistólica e diastólica com alertas clínicos visuais baseados nas diretrizes médicas.
*   Cálculo automático de percentual de gordura (Protocolo Pollock 3 e 7 Dobras).
*   Classificação de risco e estado de saúde (IMC, RCQ, Perfil Lipídico).
*   Geração de relatórios comparativos em PDF para acompanhar a evolução, incluindo alertas detalhados.

### 3. **Prescrição de Treinos**
*   Montagem de treinos personalizados.
*   **Divisões de Treino:** Organização por A, B, C, D.
*   **Catálogo de Exercícios:** Base de dados offline com centenas de exercícios, categorizados por grupo muscular.
*   Geração de ficha de treino em PDF, incluindo:
    *   Tabela de exercícios agrupada por divisão.
    *   Cargas, séries, repetições e descanso.
    *   Instruções básicas de movimento.
    *   Espaço para Cardio e Ativações.

### 4. **Agenda e Dashboard**
*   **Dashboard Interativo:** Visão geral com próximos agendamentos, aniversariantes do mês e estatísticas rápidas.
*   **Agenda:** Marcação de aulas e avaliações, com visualização clara dos compromissos e status de execução.

*   **Integração Cross-Report:** Sincronização automática de dados de saúde (como Pressão Arterial) entre Avaliações, Fichas de Treino e Agenda Diária.
*   Personalização do sistema com a marca do Personal Trainer (Logo, Nome, Contato, Reg. CREF).
*   Esses dados e selos profissionais aparecem automaticamente nos cabeçalhos dos relatórios PDF gerados.

### 6. **Administração e Segurança**
*   **Login Seguro:** Autenticação com senha criptografada.
*   **Níveis de Acesso:**
    *   **Administrador:** Acesso total, incluindo gestão de outros usuários.
    *   **Personal:** Acesso às funcionalidades de gestão de alunos e treinos.
*   **Usuário Trial:** Possibilidade de criar usuários com acesso temporário de 30 dias para demonstração.
*   **Backup:** backup completo em .zip (banco, fotos e configurações), restauração validada e backup automático diário.
*   **Senhas:** armazenadas com PBKDF2-SHA256 + salt.

### 7. **Interface Moderna e Responsiva**
*   Desenvolvido com **CustomTkinter** para uma aparência moderna (Dark/Light mode).
*   Menu lateral retrátil (Collapsible Sidebar) com ícones e tooltips.
*   Responsividade para diferentes tamanhos de janela.

### 8. **Atualização Automática**
*   Sistema integrado de verificação de atualizações via GitHub.
*   Notificação visual quando uma nova versão está disponível.
*   Atualização "One-Click" que baixa e aplica as novidades automaticamente.

### 9. **Atalhos de Teclado** (F1 mostra a lista)
*   `Ctrl+1..7` navega entre os módulos · `Ctrl+N` novo · `Ctrl+S` salvar · `Ctrl+P` PDF · `Ctrl+F` buscar · `F5` atualizar · `Ctrl+B` recolher menu.
*   Campos de data: duplo clique ou `F4` abre o calendário.

---

## 💾 Onde ficam os dados

| Execução | Pasta |
|---|---|
| Executável instalado | `C:\ProgramData\RJE Avaliacoes` (`data\`, `media\`, `backups\`, `logs\`) |
| Código-fonte (`python main.py`) | pasta do projeto (`data\`, `media\`) |

A variável de ambiente `RJE_DATA_DIR` permite usar outra pasta. Dados de versões antigas (`_internal\data`) são migrados automaticamente na primeira execução.

---

## 🛠️ Tecnologias Utilizadas

*   **Linguagem:** Python 3.10+
*   **Interface Gráfica:** CustomTkinter (Baseado em Tkinter)
*   **Banco de Dados:** SQLite 3
*   **Relatórios:** FPDF2
*   **Manipulação de Imagens:** Pillow (PIL)

---

## 📦 Instalação

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/RenatoNogueira/rje_avaliacoes_personal_trainer.git
    cd rje_avaliacoes_personal_trainer
    ```

2.  **Crie um ambiente virtual (recomendado):**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute o sistema:**
    ```bash
    python main.py
    ```

5.  **Gerar executável + instalador (Windows):**
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\build_release.ps1
    ```
    Resultado em `output\` (`RJE_Avaliacoes_Setup.exe` e o `.zip` para o atualizador).

---

## 📂 Estrutura de Arquivos

*   `main.py`: Ponto de entrada da aplicação.
*   `app_paths.py`: Resolução de caminhos (recursos x dados do usuário) e migração de dados antigos.
*   `database.py`: Gerenciamento do banco de dados e migrações.
*   `gui/`: Telas e componentes da interface gráfica.
*   `reports/`: Lógica de geração de PDFs.
*   `utils/`: Utilitários (atualizador, log/erros/backup automático, imagens).
*   `rje_avaliacoes.spec` / `installer.iss`: build do executável e do instalador.
*   `data/`: Armazenamento local (banco de dados, configurações, backups).

---

## 📝 Licença

Este projeto é proprietário e desenvolvido por RJE Tecnologia.
Todos os direitos reservados © 2026.
