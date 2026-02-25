# Guia: Resolvendo o Alerta de Antivírus (Falso Positivo)

O Windows Defender detectou o arquivo `RJE_Avaliacoes.exe` como uma ameaça. Isso é um **Falso Positivo**.

### Por que isso aconteceu?
O programa é escrito em Python e "empacotado" em um único arquivo `.exe`. Muitos antivírus usam Inteligência Artificial (Heurística) para detectar padrões. Como o seu programa é novo e não tem uma "assinatura digital" paga (que custa caro), o antivírus desconfia dele.

### Como resolver agora:
1.  Abra a **Segurança do Windows**.
2.  Vá em **Proteção contra vírus e ameaças** > **Histórico de proteção**.
3.  Encontre a entrada do `RJE_Avaliacoes.exe`.
4.  Clique em **Ações** e selecione **Restaurar**.

### Como evitar que aconteça de novo:
Para garantir que o Windows pare de bloquear seu trabalho, adicione a pasta do projeto às exclusões:
1.  Vá em **Configurações de proteção contra vírus e ameaças** > **Gerenciar configurações**.
2.  Role até o final e clique em **Adicionar ou remover exclusões**.
3.  Clique em **Adicionar uma exclusão** > **Pasta**.
4.  Selecione a pasta `C:\RJE_Avaliacoes` (ou onde você costuma salvar o programa).

---
**Observação:** Eu também atualizei o processo de build do projeto para torná-lo menos "suspeito", desativando compressões agressivas que costumam disparar esses alertas.
