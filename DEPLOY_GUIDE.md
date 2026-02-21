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

## 2. Gerar o Executável (Build)

Para que a atualização funcione nos clientes que usam o `.exe`, você precisa compilar a nova versão.

1.  **Ativar ambiente virtual:**
    ```powershell
    .venv\Scripts\activate
    ```

2.  **Rodar o PyInstaller:**
    ```powershell
    pyinstaller --noconfirm --clean rje_avaliacoes.spec
    ```
    *Isso vai gerar uma nova pasta `dist/RJE_Avaliacoes` com o executável atualizado.*

3.  **Compactar para Distribuição:**
    *   Vá até a pasta `dist/`.
    *   Entre na pasta `RJE_Avaliacoes` e selecione **todos os arquivos e pastas** dentro dela.
    *   Clique com botão direito -> Enviar para -> Pasta compactada (ZIP).
    *   **Importante:** O zip deve conter os arquivos soltos na raiz (RJE_Avaliacoes.exe, pastas gui, utils, etc), ou conter uma única pasta raiz com tudo dentro. O atualizador suporta ambos, mas prefira zipar o conteúdo da pasta `RJE_Avaliacoes`.
    *   Nomeie o arquivo como `RJE_Avaliacoes_v1.0.1.zip` (ou a versão correspondente).

---

## 3. Publicar no GitHub (Release)

1.  Acesse seu repositório no GitHub.
2.  Vá na aba **Releases** (lado direito) -> **Draft a new release**.
3.  **Choose a tag:** Crie uma nova tag correspondente à versão (ex: `v1.0.1`).
4.  **Title:** Coloque o título da versão (ex: `Versão 1.0.1 - Correções de Bugs`).
5.  **Description:** Liste as mudanças (Changelog). Isso aparecerá para o usuário se implementarmos visualização de notas.
6.  **Attach binaries (IMPORTANTE):**
    *   Arraste e solte o arquivo `.zip` que você criou no Passo 2.
    *   **O atualizador do EXE só funciona se houver um arquivo `.zip` nos assets da release.**
7.  Clique em **Publish release**.

---

## 4. Como o Cliente Recebe a Atualização

1.  O sistema do cliente verifica automaticamente a API do GitHub ao iniciar.
2.  Ele detecta que a tag `v1.0.1` é maior que a versão local.
3.  Um botão de download (⬇️) aparece na barra lateral.
4.  Ao clicar, o sistema baixa o seu `.zip`, extrai, fecha o programa, substitui os arquivos e reabre automaticamente.

---

## Dicas e Solução de Problemas

*   **Repositório Privado:** Certifique-se de que o cliente tem o `GITHUB_TOKEN` configurado no arquivo `.env` para conseguir baixar os assets.
*   **Erro 404:** Significa que não há release publicada ou o token está inválido/sem permissão.
*   **Loop de Atualização:** Se o cliente atualizar mas continuar na versão antiga, verifique se você realmente incrementou o `version.py` ANTES de compilar o executável.
