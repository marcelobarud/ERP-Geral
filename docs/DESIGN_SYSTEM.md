# Design system — ERP Geral

## Fundamentos

Os tokens globais ficam em `frontend/src/index.css`. A aparência configurável
continua sendo aplicada por variáveis `--appearance-*`; os tokens de layout
complementam essa camada sem substituir o branding do cliente.

- cor de ação: azul primário/secundário;
- sucesso: verde; erro: vermelho; aviso: âmbar;
- superfícies: fundo claro, superfície branca e superfície suave;
- raio de controle e raio de card vêm da configuração de aparência;
- foco visível usa `--focus-ring`;
- espaçamento de página e seção usa `--space-page` e `--space-section`.

### Fundação semântica

Os papéis semânticos da fundação visual ficam em `frontend/src/index.css`. A
calibragem atual usa uma escala tipográfica mais administrativa, radius
moderado para superfícies, `elevation-0` em cards comuns e elevação reservada
para camadas flutuantes. A camada inclui `--color-canvas`,
`--color-surface-muted`, `--color-surface-elevated`, os papéis de borda,
estado, foco, tipografia, spacing, radius, elevation, motion e z-index.

Aliases legados como `--line`, `--surface-soft`, `--blue`, `--green` e `--red`
permanecem por compatibilidade e apontam para os papéis semânticos. Valores
locais continuam permitidos quando representam uma exceção contextual real.

A precedência de aparência é obrigatória:

```text
override do elemento → tema da página → aparência global → token/fallback
```

Tokens globais são a fundação e não devem substituir overrides inline,
customização persistida ou temas específicos de página.

## Padrões compartilhados

- `PageHeader` para títulos e descrições de páginas;
- `button`, `button-primary`, `button-secondary` e `button-danger` para ações;
- `filter-toolbar` para filtros de cadastros;
- `report-toolbar` e `report-filter-bar` para relatórios;
- `data-card`, `data-table`, `table-actions` e `table-action` para listas;
- `Modal` para detalhes e formulários sobrepostos;
- `LoadingState`, `EmptyState`, `ErrorState` e `FeedbackBanner` para estados;
- `sr-only` e labels visíveis/associados para conteúdo acessível.

### Interações e leitura operacional

O Primary usa cor e contraste para indicar a ação dominante, sem elevação
decorativa. Secondary usa borda e superfície; Danger permanece explícito, mas
discreto, com cor e superfície de risco. Ações leves continuam em padrões
link-like/textuais e ações de linha não devem parecer três botões primários:
`Ver` e `Editar` são ações leves, enquanto `Excluir` usa o tratamento
destrutivo contido.

Inputs, selects, textareas, busca e filtros compartilham borda, superfície,
radius e foco visível. Placeholder, disabled e erro mantêm contraste útil; um
erro pode usar `aria-invalid` e não depende apenas da cor.

Tabelas preservam a densidade compacta e a semântica atual. O container usa
elevação zero e borda clara, o cabeçalho tem contraste e tracking contidos e o
hover da linha é sutil. Overrides de tabela continuam prevalecendo sobre os
valores de fallback da fundação.

## Regras de composição

Cada tela deve ter uma ação primária clara, uma hierarquia de título única,
espaçamento consistente e um estado explícito para carregamento, erro e vazio.
Ações de linha devem permanecer agrupadas e alcançáveis por teclado. Tabelas
podem rolar horizontalmente em telas estreitas; o conteúdo não deve ser cortado.

Nos breakpoints de 900px e 560px, grids passam para duas e uma coluna quando
necessário, toolbars empilham e ações de formulário ocupam a largura disponível.

Filtros operacionais simples usam uma barra aberta, sem superfície própria. Um
`FilterMenu` pode concentrar muitos parâmetros e o `report-filter-bar` mantém
período e escopo analítico juntos. A escolha depende da tarefa; uma grande
superfície não deve existir apenas para envolver controles.

### Shell e iconografia

O Shell usa `@tabler/icons-react` como biblioteca única de ícones funcionais.
O mapeamento compartilhado fica em `frontend/src/app/iconography.tsx`: a
navegação usa ícones de 18px, ações usam 17px e estados usam 16px, todos com
`currentColor` e traço consistente. Ícones não recebem cor própria nem
substituem labels, nomes acessíveis ou texto de status.

Sidebar e Topbar mantêm contraste por superfície, borda e cor de estado. A
navegação ativa usa uma única ênfase de tema, enquanto hover e chevrons são
tratamentos discretos. No mobile, os controles de menu e fechamento preservam
alvos de toque e o texto de saúde fica resumido visualmente, mantendo o estado
disponível para tecnologias assistivas.

## Data visualization

O Dashboard usa MUI X Charts Community (`@mui/x-charts`) somente para
visualizações analíticas; a biblioteca não substitui o Design System do ERP.
Use `LineChart` para tendências contínuas e `BarChart` para comparações ou
rankings claros. Cada gráfico deve responder a uma pergunta operacional real,
usar dados agregados no backend e manter título, período, unidade e contexto
textual compreensíveis.

Charts devem consumir as variáveis semânticas da aparência, usar superfície,
borda e `elevation-0`, evitar a paleta rainbow e permanecer responsivos dentro
do container. A navegação por teclado e o comportamento de
`prefers-reduced-motion` da biblioteca devem ser preservados. Não criar gráfico
vazio sem explicar o estado nem adicionar Sparkline, Gauge ou PieChart apenas
por ornamentação.

No Dashboard, séries esparsas preservam todos os buckets e valores retornados
pela API; apenas a exibição dos labels do eixo pode ser espaçada com
`tickLabelInterval`. A interface não cria pontos sintéticos no frontend. O
visual principal usa uma geometria maior, enquanto análises auxiliares e
estados vazios usam variantes compactas próprias.

No Relatório Comercial, a mesma fundação pode combinar uma série temporal para
responder quando o resultado aconteceu, rankings horizontais Top N para
responder o que ou quem mais contribuiu e tabelas compactas como evidência
detalhada. A granularidade deve vir da agregação do backend, os rankings devem
se adaptar ao tamanho real do dataset e estados sem dados devem explicar a
ausência em vez de renderizar eixos vazios.

No Relatório Financeiro, séries monetárias comparáveis podem compartilhar um
`BarChart` agrupado quando usam a mesma base temporal e a mesma unidade, como
valores a receber e a pagar ainda em aberto por vencimento. O seletor de período
deve declarar quais blocos ele altera; métricas acumuladas permanecem rotuladas
como posição histórica. Saldos vencidos quitados não alimentam estados de
atenção, e a ausência de pendências deve ser comunicada como estado positivo.
