# App Planejamento de Turmas | Desenvolvimento_6

Gerado em 19/11/2026 a partir de `App_Planejamento_Turmas_Desenvolvimento_5.msapp`, aplicando os ajustes descritos em `Documentacao_Migracao/Planejamento_Unico/Formulas_Ajustes_App_v5.txt`.

## O que mudou

São 11 propriedades em 2 telas. O restante do pacote é idêntico byte a byte ao Desenvolvimento_5.

| Tela | Controle | Propriedade | Mudança |
| --- | --- | --- | --- |
| scrCadastroTurma | cmbPeriodoLetivo | Items | Filtra pelo ID da unidade e mostra cada período uma só vez (menor ID, ou o já vinculado à turma) |
| scrCadastroTurma | cmbPeriodoLetivo | DisplayFields / SearchFields | `["Periodo_Letivo"]` no lugar de `["ComplianceAssetId"]` |
| scrCadastroTurma | cmbPeriodoLetivo | OnChange | `Reset(txtAnoReferencia)` |
| scrCadastroTurma | txtAnoReferencia | Default / DisplayMode | O ano vem do período letivo, e o campo fica só leitura quando há período selecionado |
| scrCadastroTurma | Ano_Referencia_DataCard1 | Update | Grava o ano do período letivo |
| scrCadastroTurma | DataCardKey4 | Text | O rótulo passa a ser "Ano de referência" |
| scrPlanejamentos | Title2 | Text | Mostra o nome do planejamento |
| scrPlanejamentos | Subtitle2 | Text / Color | Alerta quando a unidade tem mais de um planejamento ativo |

As alterações foram feitas em `Controls/*.json`, que é o que o Studio carrega, e espelhadas em `Src/*.pa.yaml`. O script `patch_msapp.py` reproduz a geração.

## Como testar

1. No Power Apps, abra uma cópia de desenvolvimento: **Abrir → Procurar arquivos**, selecione o `.msapp` e salve com outro nome. Não sobrescreva o app publicado.
2. **Verificador do aplicativo:** confira se as propriedades alteradas não apresentam erro de fórmula.
   - Se `GroupBy` acusar erro, use as colunas entre aspas: `GroupBy(_periodos, "Periodo_Letivo", "Registros")`.
3. **Cadastro de turma de Niterói:**
   - o combo de período mostra 2027, 2027.1 e 2027.2 uma vez cada;
   - ao escolher o período, o ano é preenchido e bloqueado;
   - a turma grava.
4. **Edição de turma existente:**
   - o período continua selecionado;
   - o ano mostra o ano do período;
   - salvar não gera erro.
5. **Tela de planejamentos:**
   - Niterói mostra "Planejamento único da unidade";
   - unidades com mais de um planejamento ativo mostram o alerta em laranja.
