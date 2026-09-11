# IMPLEMENTATION_PLAN_02.md

# Plano técnico de evolução — CRM Geral

> Este documento foi produzido quando o projeto ainda se chamava CRM Geral.
> O produto foi posteriormente reposicionado como ERP Geral.

Este plano é a continuação direta do `IMPLEMENTATION_PLAN.md`, cuja V1 foi concluída e validada.

O objetivo desta segunda etapa é evoluir o CRM Geral sem perder a simplicidade, a integridade referencial e a organização consolidada na V1.

As mudanças desta etapa estão agrupadas em três frentes:

- correções e estabilização;
- expansão do modelo de dados;
- novas funcionalidades operacionais.

O `IMPLEMENTATION_PLAN.md` permanece congelado como registro histórico da V1 concluída.

As decisões arquiteturais consolidadas neste plano também devem ser refletidas em `AI_CONTEXT.md` quando forem implementadas e aprovadas.

---

# 1. Estado herdado da V1

A V1 foi concluída com:

- frontend React + TypeScript + Vite;
- backend FastAPI + Pydantic;
- SQLAlchemy;
- PostgreSQL;
- Alembic;
- CRUD de Clientes;
- CRUD de Fornecedores;
- CRUD de Funcionários;
- CRUD de Produtos;
- criação de vendas com múltiplos itens;
- quantidade fracionária;
- preço histórico por item;
- listagem e detalhamento de vendas;
- exclusão de vendas com remoção dos seus `VendaItens`;
- proteção dos cadastros raiz referenciados;
- Dashboard administrativo simples;
- layout responsivo;
- auditoria de secrets;
- validação final com PostgreSQL real;
- suíte PostgreSQL validada em execuções consecutivas.

A evolução desta etapa deve preservar integralmente essas garantias.

---

# 2. Princípios desta etapa

## 2.1. Evolução incremental

As mudanças devem continuar sendo implementadas em fases pequenas e revisáveis.

Cada fase deve possuir:

- objetivo claro;
- dependências explícitas;
- critérios de conclusão;
- testes;
- validação manual;
- revisão de diff;
- checkpoint de commit sugerido.

---

## 2.2. Banco como fonte de integridade

Alterações estruturais devem continuar utilizando:

- models SQLAlchemy;
- migrations Alembic;
- constraints PostgreSQL;
- schemas Pydantic;
- contratos HTTP explícitos.

Nenhuma alteração manual de schema deve ser considerada solução definitiva.

---

## 2.3. Backend como autoridade

O frontend continua sem acesso direto ao banco.

Regras persistentes, filtros que dependam dos dados, snapshots históricos e validações de domínio devem passar pelo backend.

---

## 2.4. Histórico transacional

Informações históricas de uma venda não devem depender de alterações futuras nos cadastros raiz.

Já existe snapshot histórico de:

```text
venda_itens.preco_unitario
```

Nesta etapa será criado também snapshot histórico de:

```text
venda_itens.fornecedor_id
```

O fornecedor armazenado em `VendaItem` representa o fornecedor do produto no momento da venda.

---

## 2.5. Filtros previsíveis

Os filtros devem obedecer à seguinte regra:

> Os filtros globais e detalhados de cada tela devem utilizar somente informações que fazem parte daquela própria tela/visualização.

Não criar filtros baseados em informações indiretas ou ocultas de outras tabelas apenas porque existe relacionamento no banco.

Exemplo:

Na tela de Produtos, podem existir filtros para:

- nome;
- categoria;
- preço;
- fornecedor;

caso esses dados sejam exibidos na própria tela.

Não devem existir filtros para:

- cidade do fornecedor;
- estado do fornecedor;
- endereço do fornecedor;

se essas informações não fizerem parte da visualização de Produtos.

Relacionamentos exibidos apenas em telas de detalhe não se tornam filtros automaticamente.

---

# 3. Novas decisões de domínio

## 3.1. Status do Funcionário

Funcionário passa a possuir status operacional:

```text
ativo: boolean
```

Regra inicial:

```text
ativo = true
```

para novos funcionários e registros existentes após migration.

Funcionário inativo:

- permanece no banco;
- permanece visível em vendas históricas;
- pode ser consultado e editado;
- não deve ser disponibilizado para seleção em uma nova venda.

Inativar funcionário não exclui nem altera vendas anteriores.

---

## 3.2. Fornecedor histórico em VendaItem

Adicionar:

```text
venda_itens.fornecedor_id
```

A coluna deve representar o fornecedor do produto no momento da venda.

Fluxo conceitual:

```text
Produto no momento da venda

preco_venda
   ↓
venda_itens.preco_unitario

fornecedor_id
   ↓
venda_itens.fornecedor_id
```

Se posteriormente o produto mudar de fornecedor:

- vendas novas utilizam o novo fornecedor;
- vendas antigas mantêm o fornecedor histórico original.

`fornecedor_id` em `VendaItem` não é apenas um atalho para `Produto.fornecedor_id`; é um snapshot histórico deliberado.

---

## 3.3. Produtos na listagem de Vendas

A listagem de vendas deve apresentar, nesta ordem:

```text
Produto
Valor Total
Cliente
Funcionário
```

Regra para a coluna Produto:

### Um único produto

Exibir o nome do produto.

Exemplo:

```text
Notebook
```

### Dois ou mais produtos

Exibir:

```text
<quantidade> produtos
```

Exemplos:

```text
2 produtos
3 produtos
7 produtos
```

No detalhamento da venda devem continuar aparecendo todos os produtos individualmente, com seus respectivos:

- nomes;
- quantidades;
- preços unitários históricos;
- subtotais.

---

# 4. Fase 11 — Correções de UI e consistência visual

**Status atual:** concluída.

## Objetivo

Corrigir problemas visuais já identificados e melhorar a hierarquia do Dashboard sem alterar regras de domínio.

## Tarefas

### Nova Venda

Corrigir o overflow dos itens da venda.

Atualmente o bloco:

```text
Produto | Quantidade | Preço unitário | Subtotal | Remover
```

pode ultrapassar o limite visual do card de composição.

A correção deve:

- manter todo o conteúdo dentro do card;
- adaptar corretamente as colunas;
- evitar larguras fixas excessivas;
- preservar legibilidade;
- funcionar com um ou vários itens;
- funcionar em desktop, notebook e mobile;
- reorganizar os campos em telas menores quando necessário.

Não resolver apenas com:

```css
overflow: hidden;
```

caso isso apenas esconda o conteúdo.

A estrutura deve realmente se adaptar ao espaço disponível.

### Dashboard

Alterar a ordem visual para:

```text
Dashboard
↓
Atalhos
↓
Big Numbers / Resumo
```

Os atalhos devem aparecer antes dos cards de contagem.

## Dependências

V1 concluída.

## Critérios de conclusão

- nenhum item da venda ultrapassa o card;
- nenhum overflow horizontal relevante;
- vários itens permanecem utilizáveis;
- mobile continua funcional;
- atalhos aparecem acima dos big numbers;
- nenhuma regra de negócio foi alterada.

## Resultado da validação

- Nova Venda validada com um item e com suporte a múltiplos itens pelos testes
  existentes;
- composição validada em viewport amplo, notebook e `390 × 844`;
- nenhum overflow horizontal relevante observado;
- Dashboard validado com Atalhos antes do Resumo operacional;
- console do navegador sem erros ou avisos durante a validação;
- frontend: `29 passed`, lint, typecheck e build aprovados.

## Verificações

- Nova Venda com 1 item;
- Nova Venda com vários itens;
- viewport amplo;
- notebook;
- `390 × 844`;
- Dashboard com dados;
- Dashboard vazio;
- console do navegador.

## Checkpoint sugerido

`fix: corrige layout de vendas e hierarquia do dashboard`

---

# 5. Fase 12 — Status ativo/inativo de Funcionários

**Status atual:** concluída.

## Objetivo

Adicionar controle operacional de ativação e desativação de funcionários.

## Banco

Adicionar campo:

```text
funcionarios.ativo
```

Tipo:

```text
boolean
```

Regra:

```text
NOT NULL
default true
```

A migration deve garantir que funcionários existentes permaneçam ativos.

## Backend

Atualizar:

- model;
- migration;
- schemas;
- leitura;
- atualização;
- contratos OpenAPI;
- testes.

Não é necessário criar endpoint específico de ativação se o PATCH existente puder atualizar o status com clareza.

## Frontend

Na edição do funcionário, adicionar controle para:

```text
Ativo
Inativo
```

Pode ser:

- toggle;
- checkbox;
- select;

desde que seja claro e acessível.

A listagem deve indicar o status quando isso fizer parte da visualização final aprovada.

## Nova Venda

Funcionários inativos não devem aparecer como opção selecionável em uma nova venda.

Entretanto:

- funcionário inativo continua aparecendo em vendas históricas;
- seu nome histórico continua acessível através do relacionamento existente.

## Exclusão

A nova regra de status não substitui a proteção referencial.

Funcionário utilizado em venda continua protegido contra exclusão física.

## Critérios de conclusão

- funcionário novo nasce ativo;
- funcionário existente permanece ativo após migration;
- edição permite ativar/inativar;
- inativo não aparece em Nova Venda;
- vendas antigas continuam exibindo o funcionário;
- exclusões referenciadas continuam retornando conflito.

## Testes

- migration;
- criação padrão ativa;
- PATCH para inativo;
- PATCH para reativação;
- funcionário inativo ausente na seleção de Nova Venda;
- funcionário inativo presente em venda histórica;
- regressão de CRUD.

## Resultado da implementação e validação

- migration criada sem alterar a migration original da V1;
- `funcionarios.ativo` persistido como booleano não nulo com padrão `true`;
- migration final utiliza `revision = "20260820_0001"` e
  `down_revision = "20260818_0001"`;
- o identificador foi corrigido para respeitar o limite de 32 caracteres da
  tabela `alembic_version`;
- criação, atualização, leitura, filtro de funcionários ativos e bloqueio de
  vendas para funcionários inativos implementados;
- frontend permite ativar/inativar, indica o status e oculta inativos em Nova
  Venda;
- validação PostgreSQL real confirmada pelo usuário após a correção, incluindo
  upgrade, downgrade/upgrade e duas execuções consecutivas da suíte;
- naquele checkpoint, a Fase 13 ainda não havia sido iniciada; seu estado atual
  está registrado na seção da Fase 13 abaixo.

## Checkpoint sugerido

`feat: adiciona status operacional de funcionários`

---

# 6. Fase 13 — Snapshot histórico de Fornecedor em VendaItem

**Status atual:** concluída.

## Objetivo

Preservar qual fornecedor estava associado ao produto no momento da venda.

## Banco

Adicionar:

```text
venda_itens.fornecedor_id
```

com foreign key para:

```text
fornecedores.id
```

O campo passa a representar histórico transacional.

## Regra de criação da venda

Ao criar um item:

```text
Produto.preco_venda
→ VendaItem.preco_unitario

Produto.fornecedor_id
→ VendaItem.fornecedor_id
```

O frontend não deve informar `fornecedor_id` como autoridade.

O backend deve obtê-lo a partir do Produto selecionado.

## Histórico

Exemplo:

```text
Produto A
Fornecedor atual: X
```

Venda criada:

```text
VendaItem.fornecedor_id = X
```

Depois:

```text
Produto A
Fornecedor atual alterado para Y
```

Resultado:

```text
Venda antiga → fornecedor X
Venda nova   → fornecedor Y
```

## Dados existentes

A migration deve definir estratégia clara para preencher registros antigos.

Como a V1 não possuía snapshot histórico de fornecedor, para vendas já existentes a única informação disponível é o fornecedor atualmente associado ao Produto naquele momento da migration.

Essa limitação deve ser documentada.

Não inventar histórico que o sistema não armazenava anteriormente.

## Exclusão de Fornecedor

A política de integridade deve ser revisada considerando a nova FK histórica.

Fornecedor referenciado por:

- Produto;
- VendaItem histórico;

não deve ser excluído fisicamente se isso quebrar o histórico.

A API deve retornar conflito claro.

## Exclusão de Venda

Excluir Venda continua removendo:

```text
Venda
+
seus VendaItens
```

e não remove o Fornecedor.

## Critérios de conclusão

- `fornecedor_id` persistido em VendaItem;
- backend define snapshot;
- frontend não controla fornecedor histórico;
- mudança de fornecedor do Produto não altera vendas antigas;
- venda nova usa fornecedor atual;
- VendaItem continua sem órfãos;
- fornecedor histórico permanece íntegro.

## Testes

- migration;
- criação com fornecedor;
- alteração posterior do fornecedor do produto;
- venda antiga preserva fornecedor;
- venda nova usa fornecedor novo;
- tentativa de excluir fornecedor historicamente referenciado;
- exclusão de Venda preserva Fornecedor;
- rollback transacional.

## Estado da implementação e validação

- migration `20260820_0002` adiciona `venda_itens.fornecedor_id`, executa o
  backfill dos registros existentes, aplica `NOT NULL`, FK e índice;
- o model mantém `VendaItem.fornecedor_id` obrigatório, com FK para
  `fornecedores.id`;
- o serviço de criação de vendas captura `Produto.fornecedor_id` persistido e
  não aceita o fornecedor histórico como autoridade do frontend;
- contratos, OpenAPI, proteção de exclusão de Fornecedor e testes da Fase 13
  foram atualizados;
- os testes de persistência usam `session.add_all(...)` e `session.flush()`
  antes de capturar o snapshot, incluindo os testes residuais de proteção de
  Produto e Cliente referenciados;
- a correção desta pendência alterou somente
  `backend/tests/test_persistence.py`; nenhum model, migration, serviço,
  schema ou frontend foi alterado;
- validação local após a correção: `27 passed, 36 skipped, 1 warning`. Os
  skips ocorreram porque `TEST_DATABASE_URL` não estava definida;
- a Fase 13 foi considerada concluída após a validação PostgreSQL registrada
  no projeto;
- a Fase 14 está documentada abaixo e permanece restrita à listagem e ao
  detalhamento de Vendas.

## Checkpoint sugerido

`feat: preserva fornecedor histórico nos itens de venda`

---

# 7. Fase 14 — Evolução da listagem e detalhamento de Vendas

**Status atual:** concluída.

## Objetivo

Melhorar a leitura operacional da tela de Vendas.

## Listagem

Exibir nesta ordem:

```text
Produto
Valor Total
Cliente
Funcionário
```

Outras informações já existentes podem permanecer apenas se forem necessárias e não comprometerem a ordem principal aprovada.

## Produto

### Venda com um produto

Exibir:

```text
Nome do produto
```

### Venda com dois ou mais produtos

Exibir:

```text
2 produtos
3 produtos
4 produtos
...
```

A contagem representa número de itens/produtos distintos registrados na venda.

## Valor Total

Continuar utilizando o total derivado dos itens.

Não criar coluna persistida de total.

## Detalhamento

Exibir todos os itens da venda com:

- produto;
- quantidade;
- preço unitário histórico;
- subtotal;
- fornecedor histórico quando a Fase 13 já estiver concluída e fizer parte da apresentação aprovada.

O preço exibido deve continuar vindo de:

```text
venda_itens.preco_unitario
```

Nunca reconstruir venda histórica usando `produtos.preco_venda`.

## Critérios de conclusão

- ordem correta da listagem;
- uma venda com um produto mostra o nome;
- dois ou mais mostram `<n> produtos`;
- detalhe mostra todos os produtos;
- valores históricos continuam corretos;
- total continua derivado.

## Testes

- venda com 1 produto;
- venda com 2 produtos;
- venda com 3 produtos;
- preço atual diferente do histórico;
- detalhe com todos os itens;
- formatação PT-BR;
- responsividade.

## Estado da implementação e validação

- o contrato de leitura de `VendaItem` fornece resumo mínimo do fornecedor
  histórico (`id` e `nome`) além de `fornecedor_id`;
- o model possui relacionamento somente de leitura para o fornecedor apontado
  pelo snapshot histórico, e `sale_query()` carrega Produto e Fornecedor
  histórico com `selectinload`, evitando N+1;
- a listagem exibe, nesta ordem, Produto, Valor Total, Cliente e Funcionário;
- uma venda com um item exibe o nome do Produto; com dois ou mais exibe
  `<n> produtos`, contando Produtos distintos;
- o detalhe exibe individualmente Produto, Quantidade, Preço unitário
  histórico, Subtotal e Fornecedor histórico;
- nenhuma migration, coluna persistida de total/contagem ou regra transacional
  foi criada nesta fase;
- testes backend foram ajustados para o contrato histórico e testes frontend
  cobrem 1, 2 e 3 produtos, total, detalhe, preço histórico, fornecedor
  histórico, loading, vazio, erro e exclusão;
- validação local: Ruff passou; backend `27 passed, 36 skipped, 1 warning`;
  frontend `34 passed`, lint, typecheck e build passaram. Os skips ocorreram
  porque `TEST_DATABASE_URL` não estava definida;
- validação manual confirmou listagem e detalhe em desktop, notebook e
  `390 × 844`, incluindo vendas com 1, 2 e 3 produtos, sem overflow horizontal;
- a validação PostgreSQL da Fase 14 foi confirmada pelo usuário com
  `63 passed`;
- a Fase 15, filtros e detalhes relacionais não foram iniciados.

## Checkpoint sugerido

`feat: aprimora listagem e detalhe de vendas`

---

# 8. Fase 15 — Detalhes relacionais de Clientes e Fornecedores

**Status atual:** concluída. Implementação, relacionamentos derivados, estados
vazios e responsividade foram revalidados na Fase 18.

## Objetivo

Enriquecer os detalhes dos cadastros sem duplicar dados.

---

## 8.1. Fornecedor → Produtos fornecidos

### Estado da implementação

- `GET /api/suppliers/{id}` retorna um schema de detalhe com Produtos derivados
  de `Produto.fornecedor_id`.
- O carregamento usa `selectinload(Fornecedor.produtos)`, sem persistir uma
  lista duplicada e sem N+1.
- A tela de Fornecedores carrega o detalhe sob demanda, exibe os nomes dos
  Produtos e possui estado vazio, loading e erro.

No detalhamento do Fornecedor, adicionar seção:

```text
Produtos fornecidos
```

Os produtos devem ser obtidos através de:

```text
produtos.fornecedor_id
```

Não duplicar lista de produtos dentro de Fornecedor.

Informações mínimas:

- nome do produto.

Podem ser exibidas outras informações já presentes na tela de Produtos quando fizer sentido e não transformar o detalhe em relatório.

---

## 8.2. Cliente → Produtos comprados

### Estado da implementação

- `GET /api/customers/{id}` retorna um schema de detalhe com Produtos derivados
  de `Cliente → Vendas → VendaItens → Produto`.
- A consolidação ocorre no banco por `produto_id`, com `SUM(VendaItem.quantidade)`
  preservando `Decimal`; nomes iguais com IDs diferentes permanecem separados.
- A tela de Clientes carrega o detalhe sob demanda, exibe quantidade fracionária
  e possui estado vazio, loading e erro.

No detalhamento do Cliente, adicionar seção:

```text
Produtos comprados
```

Origem:

```text
Cliente
↓
Vendas
↓
VendaItens
↓
Produto
```

A visão deve ser derivada do histórico real.

Informações recomendadas:

```text
Produto
Quantidade adquirida
```

Pode consolidar o mesmo produto comprado em várias vendas quando isso puder ser feito de forma simples e previsível.

Não transformar esta seção em módulo analítico.

Não adicionar:

- ranking;
- gasto médio;
- recomendação;
- frequência;
- tendências;
- gráficos.

## Histórico

Quando for necessário mostrar preço dentro do contexto de uma venda específica, utilizar o preço histórico de `VendaItem`.

Para uma visão consolidada de produtos comprados, não inventar um “preço atual” como se fosse histórico.

## Critérios de conclusão

- detalhe do fornecedor mostra seus produtos;
- detalhe do cliente mostra produtos comprados;
- dados são derivados de relacionamentos reais;
- nenhuma duplicação estrutural;
- banco vazio funciona;
- cliente sem compras mostra estado vazio;
- fornecedor sem produtos mostra estado vazio.

## Testes

- fornecedor com produtos;
- fornecedor sem produtos;
- cliente com múltiplas vendas;
- cliente sem vendas;
- produtos repetidos;
- quantidade fracionária;
- estado vazio;
- responsividade.

## Checkpoint sugerido

`feat: adiciona detalhes relacionais de clientes e fornecedores`

## Validação final

- Os checkpoints locais anteriores permaneceram preservados como histórico.
- A Fase 18 revalidou detalhes com e sem relações, consolidação por
  `produto_id`, quantidade Decimal, eager loading e ausência de persistência
  duplicada.
- A revisão manual confirmou os detalhes em desktop, notebook e mobile.
- A validação PostgreSQL final foi executada externamente e confirmada como
  aprovada pelo usuário em 2026-08-22.
- Fase 15 concluída.

---

# 9. Fase 16 — Infraestrutura de filtros

**Status atual:** concluída, com infraestrutura implementada, piloto em
Funcionários e validação PostgreSQL real confirmada pelo usuário.

## Objetivo

Criar um padrão consistente para filtros globais e detalhados antes de aplicá-los a todas as telas.

## Regra central

Filtros devem utilizar somente informações pertencentes à própria tela.

Não atravessar relacionamentos apenas para oferecer atributos que o usuário não vê naquela visualização.

---

## 9.1. Filtro global

Cada tela principal deve possuir busca global simples.

Exemplo:

```text
Pesquisar...
```

A busca deve atuar apenas sobre campos textuais relevantes daquela visualização.

Não é uma pesquisa global do banco inteiro.

---

## 9.2. Filtros detalhados

Devem utilizar apenas atributos visíveis e relevantes naquela tela.

Os filtros devem ser definidos por feature, não por uma engine genérica universal.

---

## 9.3. Backend

Preferir query parameters nas APIs.

Exemplos conceituais:

```text
GET /api/products?search=...
GET /api/products?supplier_id=...
GET /api/employees?active=true
GET /api/sales?customer_id=...
```

Os nomes finais devem seguir os contratos reais do projeto.

Não carregar toda a base no navegador como estratégia principal quando o filtro puder ser resolvido adequadamente pelo backend.

---

## 9.4. Frontend

Criar componentes compartilhados somente quando existir reutilização real.

Pode existir algo simples como:

```text
SearchInput
FilterPanel
```

mas evitar:

```text
GenericFilterEngine
DynamicQueryBuilder
UniversalDataExplorer
```

## Estado da URL

Quando apropriado, filtros podem ser representados por query string para permitir navegação previsível.

Isso deve ser adotado apenas se for simples dentro do sistema de roteamento atual.

Não introduzir nova biblioteca pesada apenas para isso.

## 9.5. Implementação atual

- `SearchInput` foi criado como componente compartilhado simples, com label
  acessível, input controlado e limpeza explícita.
- Funcionários é o único piloto: a tela combina busca textual e `Somente
  ativos` por meio de um botão `Aplicar filtros`, preservando separação entre
  valores editados e filtros aplicados.
- A busca é normalizada com `trim`; valor vazio ou apenas espaços equivale à
  ausência do parâmetro. A combinação de `search` e `active` usa AND no
  backend.
- O backend filtra apenas campos textuais visíveis na própria listagem de
  Funcionários: nome, CPF, cidade e estado. Não foram adicionados filtros
  relacionais invisíveis, engine universal, estado de filtros na URL ou
  debounce obrigatório.
- Estados de loading, erro recuperável, lista vazia e zero resultados foram
  preservados. O layout do toolbar se adapta a desktop, notebook e mobile;
  tabelas continuam usando seu wrapper de rolagem interna sem criar rolagem
  horizontal da página.

## 9.6. Validação atual

- Ruff: aprovado.
- Backend local: `27 passed, 39 skipped, 1 warning`; os skips são testes
  PostgreSQL sem `TEST_DATABASE_URL` neste processo.
- Frontend: lint, typecheck, `44 passed` e build aprovados.
- Validação manual: busca com texto normalizado, combinação com ativos,
  limpeza, zero resultados e layout verificados em `1440×900`, `1024×768` e
  `390×844`; o menu móvel também foi confirmado. O retry de erro foi coberto
  pelo teste do piloto.
- PostgreSQL real: validado pelo usuário após a execução da suíte com o banco
  de testes configurado externamente. Não foram usadas credenciais de
  `.env.example`.

A Fase 16 está concluída. As Fases 17 e 18 também foram concluídas e estão
registradas nas seções seguintes.

## Critérios de conclusão

- padrão global definido;
- filtros detalhados definidos;
- contratos backend consistentes;
- loading/erro/vazio preservados;
- limpar filtros funciona;
- filtros combinados funcionam;
- nenhuma informação invisível é introduzida como filtro.

## Checkpoint sugerido

`feat: cria infraestrutura de filtros operacionais`

---

# 10. Fase 17 — Filtros por módulo

**Status atual:** concluída. Busca global e filtros detalhados foram aplicados
às cinco telas operacionais e estabilizados na Fase 18.

## Objetivo

Aplicar o padrão da Fase 16 às telas principais.

---

## 10.1. Clientes

Filtro global:

- campos textuais relevantes exibidos na tela.

Filtros detalhados podem incluir, conforme visualização final:

- Cidade;
- Estado.

Não criar filtros por produtos comprados apenas porque essa informação existe no detalhamento.

---

## 10.2. Produtos

Filtro global:

- nome;
- categoria;
- fornecedor, caso exibido na tela.

Filtros detalhados:

- Categoria;
- Fornecedor;
- Preço de custo;
- Preço de venda;

quando esses campos fizerem parte da visualização.

Não utilizar:

- cidade do fornecedor;
- estado do fornecedor;
- endereço do fornecedor;
- outros atributos ocultos da tabela de Fornecedores.

---

## 10.3. Funcionários

Filtro global:

- campos relevantes exibidos.

Filtros detalhados recomendados:

- Cidade;
- Estado;
- Status Ativo/Inativo.

Não criar filtros analíticos de vendas.

---

## 10.4. Fornecedores

Filtro global:

- nome;
- CNPJ;
- outros campos textuais efetivamente exibidos.

Filtros detalhados podem incluir:

- Cidade;
- Estado.

Produtos fornecidos, quando exibidos somente no detalhamento, não se tornam filtro automaticamente.

---

## 10.5. Vendas

A tela principal passa a apresentar:

```text
Produto
Valor Total
Cliente
Funcionário
```

Portanto os filtros podem atuar sobre essas informações e demais campos efetivamente exibidos, como data, caso permaneça visível na interface.

Filtros detalhados recomendados:

- Produto;
- Cliente;
- Funcionário;
- Data/período;
- Valor Total, se for mantido como informação de filtro aprovada.

O valor total continua sendo derivado; filtros por total não devem exigir coluna persistida apenas para facilitar consulta.

## Combinação de filtros

Filtros detalhados devem poder ser combinados de forma previsível.

Exemplo:

```text
Funcionário = João
+
Produto = Produto A
+
Período = agosto/2026
```

Não criar linguagem de consulta avançada.

## Critérios de conclusão

- cinco telas com filtro global;
- filtros detalhados coerentes;
- limpar filtros;
- combinar filtros;
- estados vazios claros;
- responsividade;
- contratos backend documentados;
- nenhuma relação oculta usada indevidamente.

## Testes

Por módulo:

- filtro isolado;
- busca global;
- combinação;
- limpar;
- zero resultados;
- erro da API;
- valores especiais;
- regressão do CRUD;
- regressão da paginação, se existir;
- mobile.

## Validação final

- Clientes: busca, Cidade e Estado.
- Produtos: busca, Categoria, Fornecedor e intervalos Decimal de custo e venda.
- Funcionários: busca, Cidade, Estado e status Todos/Ativos/Inativos.
- Fornecedores: busca, Cidade e Estado.
- Vendas: busca, Produto, Cliente, Funcionário, período e Valor Total.
- Busca backend-driven com trim, vazio tratado como ausência e debounce de
  `300 ms` no frontend.
- Filtros detalhados combinados com AND, aplicação explícita, limpeza, estados
  vazios e zero resultados revalidados.
- Painéis utilizam opções reais, indicação de filtros ativos e fechamento por
  toggle, clique externo e Escape.
- Layout aprovado em `1440 × 900`, `1024 × 768` e `390 × 844`, sem rolagem
  horizontal da página.
- Fase 17 concluída sem adicionar migration ou filtro fora do escopo aprovado.

## Checkpoint sugerido

`feat: adiciona filtros às telas operacionais`

---

# 11. Fase 18 — Validação e estabilização do IMPLEMENTATION_PLAN_02

**Status atual:** concluída em 2026-08-22.

## Objetivo

Executar revisão final das mudanças introduzidas neste plano.

## Validar

### Correções

- Nova Venda sem overflow;
- Dashboard com Atalhos acima dos Big Numbers.

### Funcionários

- ativo/inativo;
- histórico preservado;
- inativo indisponível em nova venda.

### VendaItem

- preço histórico;
- fornecedor histórico;
- nenhuma dependência de fornecedor atual para reconstruir venda antiga.

### Vendas

- listagem na ordem:
  - Produto;
  - Valor Total;
  - Cliente;
  - Funcionário;
- contagem de múltiplos produtos;
- detalhe completo.

### Clientes

- produtos comprados no detalhe.

### Fornecedores

- produtos fornecidos no detalhe.

### Filtros

- global;
- detalhados;
- somente dados pertencentes à tela;
- combinações;
- limpeza;
- zero resultados.

### Integridade

- cadastros raiz protegidos;
- Venda exclui seus VendaItens;
- Fornecedor histórico protegido;
- nenhum VendaItem órfão;
- migrations consistentes.

## Qualidade

Executar:

### Backend

- Ruff;
- testes completos;
- PostgreSQL real;
- migrations;
- upgrade/downgrade seguro em banco de teste quando aplicável.

### Frontend

- lint;
- typecheck;
- testes;
- build;
- validação manual;
- console.

### UI

- desktop;
- notebook;
- mobile próximo de `390 × 844`.

## Segurança

Verificação regressiva:

- `.env` fora do Git;
- `.env.example` apenas placeholders;
- nenhum secret;
- nenhum dump;
- nenhum dado pessoal desnecessário em logs.

## Documentação

Atualizar:

- `AI_CONTEXT.md`;
- este `IMPLEMENTATION_PLAN_02.md`;
- README apenas se necessário.

## Critérios de conclusão

- todas as fases deste plano implementadas;
- testes aplicáveis passam;
- PostgreSQL real validado;
- migrations consistentes;
- nenhuma regressão relevante;
- documentação alinhada ao código;
- nenhum recurso futuro introduzido sem decisão explícita.

## Resultado final

- Ruff: aprovado, sem erros.
- Backend: `71 tests collected`; a execução PostgreSQL real foi realizada
  externamente e confirmada como aprovada pelo usuário. A contagem e os warnings
  do relatório externo não foram fornecidos nesta atualização.
- Frontend: lint e typecheck aprovados; `58 passed`; build Vite concluído.
- Alembic: cadeia linear
  `20260818_0001 → 20260820_0001 → 20260820_0002`, com head único
  `20260820_0002`; validação externa no banco de teste confirmada pelo usuário.
- UI manual: Dashboard, cadastros, Nova Venda, Vendas, detalhes, modais e filtros
  aprovados em `1440 × 900`, `1024 × 768` e `390 × 844`.
- Nova Venda: um e três itens, quantidade fracionária, preços, subtotais, total,
  Remover e ausência de overflow revalidados sem persistir dados de
  demonstração adicionais.
- Filtros: opções reais, aplicação, limpeza, indicador ativo, debounce e zero
  resultados validados nas cinco telas.
- Console: nenhum erro ou warning novo da aplicação durante os fluxos manuais.
- Segurança: nenhum `.env` real, certificado, dump ou secret de alta confiança
  encontrado no Git; exemplos permanecem apenas com placeholders.
- Regressões corrigidas: import da migration para Ruff, callback duplicado no
  limpar do `SearchInput` e overflow horizontal da página causado pela área
  rolável das tabelas no mobile.
- Dívida técnica não bloqueante: warnings conhecidos de Starlette/httpx e de
  teardown transacional; nenhuma atualização ampla de dependências foi feita.
- Nenhuma funcionalidade fora das Fases 11 a 18 foi adicionada.
- Fase 18 concluída; não foi criada Fase 19.

## Checkpoint sugerido

`feat: conclui evolução do IMPLEMENTATION_PLAN_02`

---

# 12. Ordem recomendada

```text
Fase 11
Correções de UI
        ↓
Fase 12
Funcionários ativos/inativos
        ↓
Fase 13
Fornecedor histórico em VendaItem
        ↓
Fase 14
Listagem e detalhe de Vendas
        ↓
Fase 15
Detalhes relacionais
        ↓
Fase 16
Infraestrutura de filtros
        ↓
Fase 17
Filtros por módulo
        ↓
Fase 18
Validação final
```

A ordem prioriza:

1. correções visuais pequenas;
2. alterações estruturais do banco;
3. contratos e histórico;
4. apresentação;
5. consultas relacionais;
6. filtros;
7. estabilização.

---

# 13. Checkpoints Architect/Reviewer

Revisão recomendada:

## Antes da Fase 12

Confirmar:

- migration do campo `ativo`;
- regra de funcionário inativo;
- impacto em Nova Venda.

## Antes da Fase 13

Confirmar:

- semântica histórica de `fornecedor_id`;
- estratégia para registros existentes;
- integridade referencial;
- política de exclusão de Fornecedor.

## Antes da Fase 16

Confirmar:

- quais campos realmente fazem parte de cada visualização;
- quais filtros pertencem a cada tela;
- contratos de query parameters;
- evitar filtros baseados em dados ocultos.

## Antes da Fase 18

Revisar:

- migrations;
- integridade;
- histórico;
- regressões;
- segurança;
- documentação.

---

# 14. Bugs e dívida técnica conhecidos

Este plano deve permanecer aberto a bugs encontrados durante sua execução.

Novos bugs devem ser classificados em:

```text
bloqueante
alta prioridade
média prioridade
baixa prioridade
```

Bugs bloqueantes ou regressões relacionadas às fases em execução podem ser corrigidos imediatamente.

Melhorias opcionais devem ser registradas para avaliação antes de entrarem no escopo.

Warnings técnicos já conhecidos não devem motivar atualizações amplas de dependências sem necessidade concreta.

---

# 15. Fora do escopo atual

Continuam fora deste plano, salvo decisão explícita posterior:

- estoque;
- pagamentos;
- caixa;
- categorias cadastráveis;
- serviços;
- agenda;
- ordens de serviço;
- comissões;
- dashboards analíticos avançados;
- relatórios avançados;
- importação/exportação;
- campos personalizados;
- schema configurável;
- integrações externas;
- múltiplos fornecedores simultâneos por produto;
- autenticação;
- autorização;
- soft delete;
- auditoria avançada;
- recomendação de produtos;
- BI.

Esses itens podem ser considerados em planos futuros.

---

# 16. Backlog aberto

O `IMPLEMENTATION_PLAN_02.md` não precisa representar o encerramento definitivo das evoluções desta etapa.

Novas necessidades identificadas durante o desenvolvimento podem ser adicionadas posteriormente, desde que:

1. sejam avaliadas antes da implementação;
2. não quebrem decisões já consolidadas sem revisão;
3. sejam posicionadas na fase correta ou em nova fase;
4. tenham impacto em banco/API/frontend documentado;
5. possuam critérios de validação.

O objetivo é permitir evolução controlada sem transformar o plano em escopo ilimitado.

---

# 17. Estado atual

```text
IMPLEMENTATION_PLAN.md
→ V1 concluída e congelada

IMPLEMENTATION_PLAN_02.md
→ planejamento aprovado
→ Fase 11 concluída
→ Fase 12 concluída
→ Fase 13 concluída
→ Fase 14 concluída; PostgreSQL validado com `63 passed`
→ Fase 15 concluída; detalhes relacionais validados
→ Fase 16 concluída; piloto em Funcionários e PostgreSQL validados
→ Fase 17 concluída; filtros por módulo validados
→ Fase 18 concluída; evolução auditada e estabilizada
```

Fases previstas:

- Fase 11 — Correções de UI e consistência visual;
- Fase 12 — Status ativo/inativo de Funcionários;
- Fase 13 — Snapshot histórico de Fornecedor em VendaItem;
- Fase 14 — Evolução da listagem e detalhamento de Vendas;
- Fase 15 — Detalhes relacionais de Clientes e Fornecedores;
- Fase 16 — Infraestrutura de filtros;
- Fase 17 — Filtros por módulo;
- Fase 18 — Validação e estabilização.
