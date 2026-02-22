# Guia para Corrigir a Busca de Atualizações

Para que o sistema consiga buscar atualizações em um repositório **privado** no GitHub, dois requisitos precisam ser atendidos:

## 1. Token com Permissões Corretas
O token configurado no `.env` atualmente parece não ter a permissão (scope) `repo`.
- Vá em: [GitHub Settings > Tokens (Classic)](https://github.com/settings/tokens)
- Gere um novo token ou edite o existente.
- Certifique-se de marcar a opção **`repo`** (Full control of private repositories).
- Atualize o `GITHUB_TOKEN` no seu arquivo `.env` na raiz do projeto.

## 2. Criar uma Release no GitHub
O sistema busca por **Releases** oficiais, não apenas Tags.
- No GitHub, vá na página do seu repositório: `RenatoNogueira/rje_avaliacoes_personal_trainer`
- Clique em **Releases** na barra lateral direita.
- Clique em **Create a new release**.
- Selecione uma tag existente (ex: `v1.0.18`) ou crie uma nova (ex: `v1.0.19`).
- Dê um título e uma descrição.
- **Importante**: Se você deseja que o Updater baixe o executável (EXE) atualizado, anexe o arquivo `.zip` gerado pelo `build_release.ps1` na seção **Assets** da Release.

## Testando após as mudanças
Após realizar esses passos, você pode rodar o teste que criei para verificar a conexão real:
```powershell
python test_updater.py
```
Se tudo estiver correto, ele retornará "Update available: True" (se a versão na release for maior que a local).
