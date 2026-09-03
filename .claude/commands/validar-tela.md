---
description: "Valida uma rota do LV Jiu Jitsu em desktop e mobile, nos dois temas, com screenshots e, quando aplicável, evidência de rede."
argument-hint: "<rota>"
---

# /validar-tela $ARGUMENTS

Valida `http://localhost:8000/$ARGUMENTS` no navegador interno, seguindo o
contrato de `obsidian/projetos/lvjiujitsu/contrato-ui-lvjiujitsu.md` e o checklist
de `.agents/skills/lvjiujitsu-visual-auditor/references/checklist-visual.md`.
Não declarar sucesso sem screenshot registrado.

## Pré-condição

Garantir o servidor na porta canônica:

```powershell
.\.venv\Scripts\python.exe manage.py runserver localhost:8000
```

Rota interna exige sessão. Validar com a conta do papel que a rota realmente
atende, não com a primeira disponível; as superfícies e seus papéis estão em
`CLAUDE.md`.

## Passos

1. Abrir `http://localhost:8000/$ARGUMENTS` no navegador interno.
2. Validar o caminho feliz.
3. Validar ao menos um edge case relevante à rota.
4. Validar desktop e mobile, redimensionando a viewport.
5. Validar tema claro e escuro.
6. Inspecionar console e terminal.
7. Verificar permissões e estados: vazio, erro, `disabled` e `loading`.
8. Em regra de privacidade, inspecionar e salvar registro sanitizado da
   resposta de rede.
9. Auditar a renderização conforme `.agents/skills/lvjiujitsu-visual-auditor/references/checklist-visual.md`
   — screenshot é material a auditar, não carimbo de aprovação.
10. Capturar screenshot desktop e mobile e registrar os caminhos.

## Saída

```text
Rota: http://localhost:8000/$ARGUMENTS
Papel usado: <papel autenticado | anônimo>
Caminho feliz: <ok | falha>
Edge case (<qual>): <ok | falha>
Desktop: <ok | falha> — <screenshot>
Mobile: <ok | falha> — <screenshot>
Tema claro/escuro: <ok | falha>
Console/terminal: <limpo | erros>
Permissões/estados: <ok | observação>
Rede/privacidade: <não se aplica | resultado e caminho>
Auditoria de renderização: <sem achado | lista>
Status: <validada | incompleta | falhou>
```

## Parar quando

- Navegador interno bloqueado ou indisponível: registrar **incompleta** e a
  limitação real; não declarar validação visual.
- Faltar screenshot desktop ou mobile: registrar **incompleta**.
- Erro crítico no console, no terminal ou na rede: registrar **falhou**.
- Achado de renderização confirmado por medição: registrar **falhou** e
  corrigir; não deixar para o operador encontrar.
- Evidências completas e sem achado: registrar **validada**.
