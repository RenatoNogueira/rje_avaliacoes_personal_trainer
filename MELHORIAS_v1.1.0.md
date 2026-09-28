# RJE Avaliações — v1.1.0 (melhorias de UI/UX, correções e build desktop)

## Correções de bugs (encontrados na análise do código)

| Módulo | Problema | Correção |
|---|---|---|
| Agenda | Havia **dois** `on_excluir`; o segundo sobrescrevia o primeiro e **excluía sem pedir confirmação** | Método duplicado removido: sempre confirma |
| Agenda (PDF) | O PDF da agenda **falhava** (`sqlite3.Row` não tem `.get`) e, quando funcionava, o campo "Data" mostrava o JSON de configurações (variável sobrescrita) | Linhas convertidas para `dict` e variável renomeada |
| Treinos | Novo treino obtinha o id com `last_insert_rowid()` em **outra conexão** (retornava 0) → adicionar exercício num treino novo quebrava | Novo `db.insert()` retorna o id na mesma conexão |
| Alunos / Avaliações / Agenda | Salvar duas vezes um registro novo **duplicava** o registro | O formulário passa a ficar vinculado ao registro recém-criado |
| Avaliações | Caixas Diabetes/Hipertensão/etc. não voltavam marcadas ao abrir e o prefixo "Condições:" **se repetia** a cada salvamento | Prefixo separado do texto e caixas restauradas |
| Avaliações (PDF) | Fotos não apareciam no PDF do executável (caminho relativo resolvido na pasta errada) | Caminhos resolvidos pela pasta de dados |
| Notificações | O "toast" usava uma cor inexistente e **nunca aparecia** | Corrigido; agora substitui as caixas "salvo com sucesso" que travavam o fluxo |
| Dashboard | Cada visita criava um novo timer de atualização que **nunca parava** (consumo crescente de CPU/rede) | Um timer por tela, cancelado ao sair |
| Dashboard | "Avaliações no mês" somava o mesmo mês de **todos os anos**; média de idade ignorava dia/mês | Filtro por ano-mês e idade exata |
| Configurações | Título "Aparência" sobreposto ao botão "Detectar Automaticamente" | Linhas ajustadas |
| Menu lateral | Tooltips eram recriadas a cada recolher/expandir (acumulando e aparecendo no modo expandido) | Criadas uma vez e ativadas/desativadas |
| Logo padrão | `assets/logo_rje.png` era um **arquivo de texto** (URL), não uma imagem | Substituído pela imagem real do ícone |
| Auto-instalador | Copiava só o `.exe` (build onedir precisa de `_internal`) e perguntava "instalar?" a cada abertura se instalado fora de `C:\RJE_Avaliacoes` | Copia a pasta inteira e reconhece instalação feita pelo Setup |
| Relatórios | Caracteres especiais (emoji, travessão colado do WhatsApp etc.) derrubavam a geração do PDF | Substituição segura de caracteres |

## Melhorias de usabilidade (UI/UX)

- **Atalhos de teclado** (F1 mostra a lista): `Ctrl+1..7` navega entre módulos, `Ctrl+N` novo, `Ctrl+S` salvar, `Ctrl+P` PDF, `Ctrl+F` busca, `F5` atualizar, `Ctrl+B` recolhe o menu, `Esc` limpa a busca.
- **Busca enquanto digita** (com atraso inteligente) em Alunos, Agenda, Avaliações, Treinos e Usuários; Alunos também busca por **CPF e telefone**.
- **Item selecionado destacado** nas listas e **contador** de resultados.
- **Feedback não bloqueante** (toasts verdes/vermelhos) no lugar de janelas "OK" após salvar/excluir.
- **Agenda**: novo agendamento já vem com data do filtro/hoje, próxima hora cheia, tipo "Treino" e status "Pendente"; **aviso de conflito de horário**; botões "Hoje"/"Todas"; contador de pendentes.
- **Treinos**: botão **Duplicar treino** (com exercícios, podendo trocar o aluno); ao adicionar exercício o formulário fica pronto para o próximo (mantém séries/reps/divisão); Enter em "Obs" adiciona; catálogo com busca mais leve, `Esc` fecha e "Selecionar" respeita o item marcado.
- **Avaliações**: data de hoje preenchida por padrão; validação de faixas (ex.: altura digitada em cm).
- **Dashboard**: cards e agendamentos **clicáveis** levam ao módulo correspondente.
- **Login**: lembra o último usuário, botão **mostrar/ocultar senha**, aviso de **Caps Lock**, janela centralizada, bloqueio temporário após 5 tentativas.
- **Campos de data**: calendário abre com **duplo clique / F4** (antes abria a cada clique, atrapalhando a digitação) e aparece junto ao campo; máscaras não jogam mais o cursor para o fim.
- **PDFs**: salvos por padrão em `Documentos\RJE Avaliacoes`, com nome de arquivo seguro, e o sistema **oferece abrir o arquivo**; mensagem clara se o PDF estiver aberto em outro programa.
- **Logo** exibida sem distorção (proporção mantida) no login, Sobre e Profissional.
- Menu lateral mostra **quem está logado** e o papel; janela com tamanho mínimo para não quebrar o layout.

## Segurança e confiabilidade (boas práticas)

- **Senhas com PBKDF2-SHA256 + salt** (antes SHA-256 sem salt). Migração transparente no próximo login.
- Aviso para **trocar a senha padrão** `admin/admin` e nova seção **"Alterar minha senha"**.
- Mensagem de login única ("usuário ou senha inválidos"); impede remover/desativar o **último administrador**; senha mínima de 6 caracteres; nome de usuário duplicado com mensagem clara.
- **Dados fora da pasta do programa**: `C:\ProgramData\RJE Avaliacoes` (banco, fotos, backups, logs). Atualizações/reinstalações não tocam nos dados. **Migração automática** dos dados da versão anterior (`_internal\data` e `_internal\media`) na primeira execução — nada é apagado da origem.
- **Backup completo em .zip** (banco + fotos + configurações), **restauração validada** com cópia de segurança automática antes, e **backup automático diário** (mantém os 10 últimos).
- **Log de erros** em arquivo e tratamento global de exceções com mensagem amigável (antes, no .exe sem console, erros sumiam silenciosamente).
- **Instância única**: impede abrir o sistema duas vezes (evita conflito no banco).
- **Atualizador sem token**: consulta releases públicas (`UPDATE_REPOS` em `version.py`) e baixa pela URL pública. O `.env` com `GITHUB_TOKEN` **não é mais distribuído**, e a v1.1.0 apaga o `.env` deixado pelas versões antigas. Download em segundo plano **com barra de progresso**.
- **Assinatura digital** automatizada nos scripts de build (ver `ASSINATURA_DIGITAL.md`).

## Build / instalador

- `rje_avaliacoes.spec` versionado; build **sem matplotlib/numpy** (não eram usados): pasta do app de ~208 MB → **~56 MB**; instalador de 38,8 MB → **~21 MB**. UPX desativado (reduz falso positivo de antivírus).
- Instalador Inno Setup revisado: mesmo AppId (atualiza a instalação existente), atalho na área de trabalho marcado por padrão, fecha o sistema se estiver aberto, permissões para o atualizador automático, limpeza das bibliotecas antigas sem tocar nos dados, informações de versão em português.
- `build_release.ps1` gera tudo (exe, zip de atualização e instalador, assinando se houver certificado) em um comando.
