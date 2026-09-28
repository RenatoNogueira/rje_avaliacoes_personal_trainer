# Assinatura digital do RJE Avaliações

## Por que o Windows mostra "O Windows protegeu o computador"

O **SmartScreen** avisa ao abrir programas **sem assinatura digital** ou de editores ainda sem
"reputação". Não é possível eliminar o aviso só com código: é necessário um **certificado de
assinatura de código** emitido por uma autoridade reconhecida pela Microsoft.
(Certificado autoassinado **não** resolve — o Windows continua bloqueando.)

## Opções de certificado

| Opção | Custo aproximado | Observações |
|---|---|---|
| **Azure Artifact Signing** (antigo *Trusted Signing*) | ~US$ 10/mês | Mais barato e sem token USB. Exige validação de identidade; confira se a sua região (Brasil) e o tipo de cadastro (CNPJ ou pessoa física) já são aceitos. Usa o `signtool` + plugin da Microsoft. |
| Certificado **OV** (Certum, Sectigo, SSL.com...) | ~US$ 200–400/ano | Chave em token USB/nuvem (exigência desde 2023). Reputação no SmartScreen cresce com o número de instalações. |
| Certificado **EV** | ~US$ 300–600/ano | Validação mais rigorosa; token USB. |

> Até a reputação ser construída, o usuário ainda pode ver o aviso algumas vezes, mas ele passa a exibir
> o **nome do editor** (ex.: "RJE Tecnologia") em vez de "Editor desconhecido".

## Como assinar (já automatizado nos scripts)

1. Instale o **Windows SDK** com o componente *Signing Tools* (fornece o `signtool.exe`).
2. Instale o certificado (ou conecte o token USB) e anote a **impressão digital** (thumbprint):
   `certmgr.msc` → Pessoal → Certificados → duplo clique → Detalhes → Impressão digital.
3. No PowerShell, antes do build:

```powershell
$env:RJE_SIGN_THUMBPRINT = "COLE_AQUI_A_IMPRESSAO_DIGITAL"
# ou, com arquivo .pfx:
# $env:RJE_SIGN_PFX = "C:\certificados\rje.pfx"; $env:RJE_SIGN_PASSWORD = "senha"
powershell -ExecutionPolicy Bypass -File .\build_release.ps1
```

O script assina `RJE_Avaliacoes.exe` (inclusive o que vai no `.zip` de atualização), o
`RJE_Avaliacoes_Setup.exe` e o desinstalador, com carimbo de tempo (a assinatura continua
válida mesmo após o certificado expirar). Sem as variáveis, o build funciona normalmente, sem assinar.

Para conferir: botão direito no `.exe` → Propriedades → aba **Assinaturas Digitais**.

## Enquanto não houver certificado

* Oriente o cliente: no aviso, clicar em **Mais informações → Executar assim mesmo**.
* Se algum antivírus bloquear, envie o arquivo para análise de falso positivo:
  https://www.microsoft.com/wdsi/filesubmission (Windows Defender).
* O build já evita práticas que aumentam falsos positivos (UPX desativado, informações de versão preenchidas).
