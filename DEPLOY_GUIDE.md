# Guia de Atualização e Deploy (DEV)

Este guia descreve o processo para gerar uma nova versão do **RJE Avaliações** e disponibilizá-la para atualização automática nos clientes.

---

## 1. Preparar a Nova Versão

1.  **Atualizar Versão:**
    *   Abra o arquivo `version.py`.
    *   Incremente a variável `__version__` (ex: de `"1.0.0"` para `"1.0.1"`).

2.  **Testar:**
    *   Rode o sistema localmente (`python main.py`) para garantir que tudo está funcionando.

---

## 2. Gerar o Executável, o ZIP de atualização e o Instalador 

Em um único comando (cria a `.venv` se necessário):

```powershell
powershell -ExecutionPolicy Bypass -File .\build_release.ps1
```

Resultados em `output\`:
*   `RJE_Avaliacoes_Setup.exe` — instalador para novos computadores (ou atualização manual).
*   `RJE_Avaliacoes_vX.Y.Z.zip` — pacote para o **atualizador automático** (anexar na Release do GitHub).

> Antes de gerar, atualize a versão em `version.py` **e** em `installer.iss` (`#define AppVersion`) e `file_version_info.txt`.

---

## 3. Publicar no GitHub (Release) — repositório PÚBLICO, sem token

A partir da v1.1.0 o aplicativo **não usa mais token**: ele consulta releases públicas,
na ordem definida em `UPDATE_REPOS` (`version.py`):

1. `RenatoNogueira/rje_avaliacoes_releases` — **recomendado**: repositório público contendo só as releases (o código continua privado).
2. `RenatoNogueira/rje_avaliacoes_personal_trainer` — usado se o repositório do código for público.

### Configuração única (recomendada)
1.  No GitHub: **New repository** → nome `rje_avaliacoes_releases` → **Public** → marque "Add a README" → Create.
2.  Pronto. Não é preciso enviar código para ele; ele serve só para hospedar os `.zip`.

### A cada versão
1.  No repositório de releases: **Releases** → **Draft a new release**.
2.  **Tag:** `v1.1.0` (mesma versão do `version.py`, com "v").
3.  **Title / Description:** título e lista de mudanças.
4.  **Anexe** `output\RJE_Avaliacoes_vX.Y.Z.zip` (**obrigatório**: o atualizador procura um `.zip` nos assets).
5.  **Publish release**.

---

## 4. Como o Cliente Recebe a Atualização

1.  Ao iniciar, o sistema consulta a última release pública.
2.  Se a tag for maior que a versão instalada, aparece o botão **▲ Atualizar** no menu lateral.
3.  Ao clicar, o `.zip` é baixado (com barra de progresso), o programa fecha, os arquivos são substituídos e ele reabre.
4.  Os dados ficam em `C:\ProgramData\RJE Avaliacoes` e não são afetados.

---

## 5. Segurança: token antigo (AÇÃO NECESSÁRIA)

As versões até a 1.0.33 distribuíam um `.env` com `GITHUB_TOKEN` dentro do instalador e do zip,
e o `.env` também estava versionado no git. **Considere esse token vazado.**

1.  **Publique a v1.1.0** (passo 3). Clientes na 1.0.33 ainda usam o token antigo para achar a atualização
    **no repositório do código** — então, para migrá-los automaticamente, publique também a release `v1.1.0`
    (com o mesmo `.zip`) no repositório `rje_avaliacoes_personal_trainer`.
2.  Aguarde os clientes atualizarem (a v1.1.0 apaga o `.env` antigo da pasta do programa).
3.  **Revogue o token**: GitHub → Settings → Developer settings → Personal access tokens → *Delete/Revoke*.
    Clientes que não atualizaram até lá recebem o instalador novo manualmente.
4.  Tire o `.env` do git: `git rm --cached .env` e faça commit (ele já está no `.gitignore`).
    O token continua no histórico antigo — por isso a revogação é indispensável.

---

## 6. Assinatura digital

Veja **ASSINATURA_DIGITAL.md**. Com o certificado configurado, `build_release.ps1` assina o executável,
o instalador e o desinstalador automaticamente.

---

## Dicas e Solução de Problemas

*   **"Nenhuma release pública encontrada":** a release não foi publicada, está como rascunho, ou o repositório é privado.
*   **Release sem `.zip`:** o botão de atualizar não aparece; anexe o zip na release.
*   **Limite do GitHub (403):** sem token, a API permite 60 consultas/hora por IP — mais que suficiente; tente mais tarde.
*   **Loop de atualização:** confirme que `version.py` foi incrementado ANTES de compilar.
*   **Logs:** `C:\ProgramData\RJE Avaliacoes\logs\updater.log`.
