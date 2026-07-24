# Painel Takai

Painel estático (`index.html`) com dois blocos:

- **Agenda** — próximos compromissos da agenda `takai@somostakai.com.br` (Google
  Calendar), com destaque para reuniões com convidados externos. Blocos de
  rotina (almoço, café, creative/focus day) ficam ocultos por padrão.
- **Tarefas — Karol** — tarefas abertas atribuídas à Karol no ClickUp (espaço
  `takai`), com filtros por prazo (atrasadas / próximos 7 dias / sem prazo),
  busca e filtro por lista.

Sem servidor: os dados ficam embutidos no HTML no momento da geração. Abra
`index.html` no navegador para ver o painel.

## Como atualizar

O painel não busca dados sozinho — é preciso pedir a atualização. No chat com
o Claude, basta pedir algo como **"atualiza o painel"**. Isso faz Claude:

1. Buscar os eventos mais recentes no Google Calendar e as tarefas da Karol no
   ClickUp.
2. Regravar `data/events_raw.json` e `data/tasks_karol.json`.
3. Rodar `python3 scripts/build_dashboard.py` para regerar `index.html`.
4. Commitar e enviar o resultado.

### Rodando manualmente

```bash
python3 scripts/merge_tasks.py     # só se houver data/tasks_page*.json paginados para mesclar
python3 scripts/build_dashboard.py # gera index.html a partir de data/*.json
```

## Estrutura

```
data/events_raw.json    # export bruto dos eventos do Google Calendar
data/tasks_karol.json   # tarefas da Karol já mescladas/deduplicadas
scripts/build_dashboard.py  # gera index.html a partir dos dados acima
scripts/merge_tasks.py      # mescla páginas de tarefas do ClickUp (deduplicação por id)
scripts/template.html       # template do painel (HTML/CSS/JS)
index.html               # painel gerado — abra este arquivo
```
