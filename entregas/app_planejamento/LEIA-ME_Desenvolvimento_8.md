# App Planejamento de Turmas | Desenvolvimento_8

Gerado em 19/11/2026 a partir do Desenvolvimento_7 (script `patch_v8.py`). Alterações em 19 propriedades de 4 telas. O restante do pacote é idêntico ao Desenvolvimento_7.

## 1. Status automático pelas datas

**Regra aplicada**, nesta ordem:

| Condição | Status |
| --- | --- |
| A turma está Cancelada | Continua Cancelada. O cancelamento é sempre manual |
| Hoje é depois do fim previsto | **Concluída** |
| Hoje está entre o início e o fim previstos | **Em execução** |
| A turma ainda não começou, mas está marcada como Em execução ou Concluída | Volta para **Planejada** |
| Qualquer outro caso | Mantém o status escolhido (Rascunho, Em planejamento, Planejada ou Confirmada) |

| Tela / controle | Mudança |
| --- | --- |
| scrCadastroTurma › `btnSalvarTurma.OnSelect` | Grava o status calculado pela regra |
| scrCadastroTurma › `DataCardKey53.Text` | O rótulo avisa que Em execução e Concluída são definidos pelas datas |
| scrTurmas › `HtmlText12` (cartão da turma) | Mostra o status calculado, mesmo que o gravado esteja desatualizado |

As turmas que ninguém abre são atualizadas pelo fluxo diário descrito em `Fluxo_Status_Turmas.md`.

> **Antes de publicar:** confira se a coluna Escolha `Status_Turma` tem a opção **"Concluída"**, escrita exatamente assim. Nenhuma turma usa esse valor hoje. Se a opção não existir, o salvamento falha.

## 2. Filtro de datas da lista de turmas

**Limite de 2.000 turmas.** A galeria `Gallery1` passa a filtrar primeiro por unidade e turma ativa, e esse filtro roda no SharePoint. Os filtros escolhidos na tela rodam depois, sobre as turmas da unidade. Antes, o app lia só as primeiras 2.000 turmas da lista inteira, que já tem 1.993.

**Lógica dos filtros de data:**

| Filtro | Turmas que aparecem |
| --- | --- |
| Período de início | Início previsto entre De e Até, com as duas datas incluídas |
| Período de fim | Fim previsto entre De e Até, com as duas datas incluídas |
| **Período de execução** (novo) | Turmas em execução em algum dia do intervalo: início ≤ Até e fim ≥ De. É a mesma regra da produção por competência |

- Qualquer filtro de data aceita só "De" ou só "Até".
- Filtros de campos diferentes se combinam (E). Filtros do mesmo campo são alternativas (OU).
- **Controles ajustados:** `cmbCampoBuscaTurma`, `txtPesquisarTurma`, `dpBuscaDataDe`, `dpBuscaDataAte`, `Label2`, `Label2_1`, `Label11`, `btnAdicionarFiltroTurma` e `btnEtiquetaFiltroTurma`.

## 3. Calendário com mais de uma modalidade

`scrCalendarioEP` › `Button8.OnSelect`. O combo de modalidade já aceitava várias escolhas, mas só uma era gravada. Agora:

- a primeira modalidade é gravada no evento aberto;
- cada modalidade adicional cria um evento com a mesma unidade, as mesmas datas e a mesma descrição.

O cálculo de H/A e o BI continuam lendo uma modalidade por evento, sem alteração.

## 4. Almoço na turma integral

`scrHorarioTurma` › `Button7.OnSelect` (cadastro), `Carga_Horaria_Dia_DataCard1.Update` (edição) e `DataCardValue20.Default` (prévia).

- Quando o turno da turma é **Integral**, a carga do dia desconta 60 minutos. Exemplo: 08:00–17:00 passa a valer 8h.
- **Proteção:** o desconto só vale para horários com mais de 4h. Um horário curto de turma integral, como um sábado das 08:00 às 12:00, não perde a hora. Para descontar sempre, remova a condição `> 240`.
- O rótulo da carga indica o desconto quando o turno é Integral.
- **Horários já gravados não mudam sozinhos.** Para recalcular, abra e salve cada horário das turmas integrais (43 turmas ativas) ou corrija a lista `Turma_Horarios` com a regra acima.

## Como testar

1. Importe o `.msapp` como cópia de desenvolvimento, sem sobrescrever o app publicado.
2. **Status:**
   - salve uma turma com início no passado e fim no futuro: deve ficar Em execução;
   - salve uma turma com fim no passado: deve ficar Concluída;
   - uma turma Cancelada não muda.
3. **Filtros:**
   - "Período de execução" de 01/01/2027 a 31/12/2027 deve trazer as turmas que começaram em 2026 e terminam em 2027;
   - compare com "Período de início" no mesmo intervalo.
4. **Calendário:** um feriado com 3 modalidades gera 3 eventos.
5. **Horário:** numa turma Integral, 08:00–17:00 mostra 8h; numa turma Manhã, 08:00–12:00 mostra 4h.
