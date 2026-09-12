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

## Padrões compartilhados

- `PageHeader` para títulos e descrições de páginas;
- `button`, `button-primary`, `button-secondary` e `button-danger` para ações;
- `filter-toolbar` para filtros de cadastros;
- `report-toolbar` e `report-filter-bar` para relatórios;
- `data-card`, `data-table`, `table-actions` e `table-action` para listas;
- `Modal` para detalhes e formulários sobrepostos;
- `LoadingState`, `EmptyState`, `ErrorState` e `FeedbackBanner` para estados;
- `sr-only` e labels visíveis/associados para conteúdo acessível.

## Regras de composição

Cada tela deve ter uma ação primária clara, uma hierarquia de título única,
espaçamento consistente e um estado explícito para carregamento, erro e vazio.
Ações de linha devem permanecer agrupadas e alcançáveis por teclado. Tabelas
podem rolar horizontalmente em telas estreitas; o conteúdo não deve ser cortado.

Nos breakpoints de 900px e 560px, grids passam para duas e uma coluna quando
necessário, toolbars empilham e ações de formulário ocupam a largura disponível.
