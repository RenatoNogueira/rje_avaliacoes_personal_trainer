# RJE Avaliações - Sistema de Gestão para Personal Trainers

**Versão:** 1.0.0  
**Desenvolvido por:** RJE Tecnologia

O **RJE Avaliações** é um software completo e intuitivo desenvolvido em Python (CustomTkinter) para auxiliar Personal Trainers na gestão de seus alunos, avaliações físicas, prescrição de treinos e agenda.

---

## 🚀 Funcionalidades Principais

### 1. **Gestão de Alunos**
*   Cadastro completo de alunos (Dados pessoais, contato, anamnese básica).
*   Histórico de avaliações e treinos vinculados a cada aluno.
*   Busca rápida e listagem organizada.

### 2. **Avaliações Físicas**
*   Registro de medidas antropométricas (perímetros, dobras cutâneas).
*   Cálculo automático de percentual de gordura (Protocolo Pollock 3 e 7 Dobras).
*   Classificação de risco (IMC, RCQ).
*   Geração de relatórios comparativos em PDF para acompanhar a evolução.

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
*   **Agenda:** Marcação de aulas e avaliações, com visualização clara dos compromissos.

### 5. **Perfil Profissional e Branding**
*   Personalização do sistema com a marca do Personal Trainer (Logo, Nome, Contato).
*   Esses dados aparecem automaticamente nos cabeçalhos dos relatórios PDF gerados.

### 6. **Administração e Segurança**
*   **Login Seguro:** Autenticação com senha criptografada.
*   **Níveis de Acesso:**
    *   **Administrador:** Acesso total, incluindo gestão de outros usuários.
    *   **Personal:** Acesso às funcionalidades de gestão de alunos e treinos.
*   **Usuário Trial:** Possibilidade de criar usuários com acesso temporário de 30 dias para demonstração.
*   **Backup:** Ferramentas integradas para backup e restauração do banco de dados SQLite.

### 7. **Interface Moderna e Responsiva**
*   Desenvolvido com **CustomTkinter** para uma aparência moderna (Dark/Light mode).
*   Menu lateral retrátil (Collapsible Sidebar) com ícones e tooltips.
*   Responsividade para diferentes tamanhos de janela.

### 8. **Atualização Automática**
*   Sistema integrado de verificação de atualizações via GitHub.
*   Notificação visual quando uma nova versão está disponível.
*   Atualização "One-Click" que baixa e aplica as novidades automaticamente.

---

## 🛠️ Tecnologias Utilizadas

*   **Linguagem:** Python 3.10+
*   **Interface Gráfica:** CustomTkinter (Baseado em Tkinter)
*   **Banco de Dados:** SQLite 3
*   **Relatórios:** FPDF2
*   **Gráficos:** Matplotlib
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

---

## 📂 Estrutura de Arquivos

*   `main.py`: Ponto de entrada da aplicação.
*   `database.py`: Gerenciamento do banco de dados e migrações.
*   `gui/`: Telas e componentes da interface gráfica.
*   `reports/`: Lógica de geração de PDFs.
*   `utils/`: Utilitários (atualizador, tooltips, formatação).
*   `data/`: Armazenamento local (banco de dados, configurações, backups).

---

## 📝 Licença

Este projeto é proprietário e desenvolvido por RJE Tecnologia.
Todos os direitos reservados © 2026.
