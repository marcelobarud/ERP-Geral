# AI_CONTEXT.md

Este arquivo é a referência do contexto atual do ERP Geral. Ele documenta o
produto, o escopo da V1 e as decisões arquiteturais que devem orientar agentes
e implementações futuras.

AGENTS.md continua sendo a fonte das regras de trabalho do repositório.

## 1. Visão geral

### Reposicionamento oficial — 2026-09-11

O projeto anteriormente chamado CRM Geral foi oficialmente reposicionado e
renomeado para ERP Geral. Seu foco é uma plataforma genérica e configurável de
gestão administrativa e operacional, com evolução futura para funcionalidades
típicas de ERP, incluindo estoque, compras e financeiro. CRM será tratado como
um produto separado e não deve ser confundido com este projeto.

Produto: ERP genérico, configurável e adaptável, inicialmente voltado à gestão
administrativa e operacional de negócios em geral.

Objetivo da V1: oferecer um sistema administrativo simples para cadastro de
entidades básicas e registro de vendas. A arquitetura deve permitir evolução,
mas a V1 não deve implementar antecipadamente funcionalidades de versões
futuras.

Estado atual: a V1 foi implementada e validada nas Fases 1 a 10, e a Fase 11
foi concluída. A implementação da Fase 12 adicionou o status operacional de
funcionários, o filtro de funcionários ativos em Nova Venda e a proteção
backend contra vendas iniciadas por funcionários inativos. A migration da
Fase 12 utiliza `revision = "20260820_0001"`, com `down_revision =
"20260818_0001"`, respeitando o limite padrão de 32 caracteres da tabela
`alembic_version`. A Fase 13 foi concluída com o snapshot histórico do
fornecedor em `VendaItem`, incluindo migration, model, serviço, contratos e
testes. A Fase 14 foi implementada para melhorar a listagem e o detalhamento
de Vendas: a listagem prioriza Produto, Valor Total, Cliente e Funcionário;
vendas com múltiplos itens exibem a contagem de produtos; e o detalhe
apresenta preço, subtotal e fornecedor histórico. A validação PostgreSQL da
Fase 14 foi confirmada pelo usuário com `63 passed`. A Fase 15 foi concluída
com detalhes relacionais derivados para Clientes e Fornecedores, sem
persistência duplicada. A Fase 16 foi concluída com infraestrutura implementada
e um piloto na tela de
Funcionários, incluindo busca textual no backend, filtro de ativos, combinação
AND, limpar filtros e estados de loading, erro e zero resultados. A validação
PostgreSQL real da Fase 16 foi confirmada pelo usuário. A Fase 17 foi concluída
com busca global backend-driven e filtros detalhados nas cinco telas
operacionais. A Fase 18 concluiu a auditoria e estabilização das Fases 11 a 17,
com validação estática, frontend, UI responsiva, OpenAPI, segurança e
PostgreSQL real. A execução PostgreSQL final foi realizada externamente e
confirmada como aprovada pelo usuário em 2026-08-22. O Plano 03 foi concluído
com três commits locais separados. A Fase 0 do Plano 04 foi concluída em
2026-09-11 com a migration `20260911_0002`: vendas agora possuem ciclo de
vida concluída/cancelada, observação, cancelamento não destrutivo e timestamps
operacionais; as cinco listagens principais usam paginação backend-driven; o
dashboard usa agregação no backend; e leituras de aparência não criam mais
configuração persistida como efeito colateral. O frontend foi validado com 74
testes e build aprovado. A suíte PostgreSQL não foi executada nesta máquina
porque `TEST_DATABASE_URL` não estava configurada.
A Fase 1 do Plano 04 também foi concluída em 2026-09-11 com a migration
`20260911_0003`: autenticação por sessão revogável, usuários, papéis,
permissões centralizadas e logs de auditoria foram adicionados. Em produção,
`AUTH_SECRET` e `AUTH_BOOTSTRAP_TOKEN` são obrigatórios; o frontend oferece
login e logout quando `auth_required` está ativo. A Fase 2 do Plano 04 foi
concluída em 2026-09-11 com a migration
`20260911_0004`: o catálogo de produtos agora possui SKU, código de barras,
unidade de medida, categoria estruturada, ativo/inativo e estoque mínimo;
produtos legados foram preservados e receberam SKU compatível. A relação
produto-fornecedor suporta múltiplos fornecedores com fornecedor preferencial
único, e há histórico de custos separado do snapshot de `VendaItem`. Produtos
inativos não entram em novas vendas. A validação local passou com 41 testes e
60 testes PostgreSQL ignorados por ausência de `TEST_DATABASE_URL`; Ruff e a
validação frontend também passaram. A Fase 3 do Plano 04 foi concluída em
2026-09-11 com a migration
`20260911_0005`: condições de pagamento, orçamentos, pedidos de venda,
snapshots comerciais, transições controladas, conversões idempotentes para
pedido/venda e impressão HTML foram adicionados. Os documentos não movimentam
estoque definitivamente nesta fase. A validação local passou com 43 testes e
61 testes PostgreSQL ignorados por ausência de `TEST_DATABASE_URL`.
A Fase 4 do Plano 04 foi concluída em 2026-09-11 com a migration
`20260911_0006`: depósito padrão, configuração explícita de saldo negativo,
movimentações append-oriented, reversões com origem e inventário com
confirmação foram adicionados. O saldo é calculado pelos eventos e a consulta
usa o estoque mínimo do catálogo. A validação local passou com 45 testes e 62
testes PostgreSQL ignorados por ausência de `TEST_DATABASE_URL`.
A Fase 5 do Plano 04 foi concluída em 2026-09-11 com a migration
`20260911_0007`: pedidos de compra, recebimentos parciais/totais, entradas
idempotentes no estoque e atualização do histórico de custos foram adicionados.
A validação local passou com 47 testes e 63 testes PostgreSQL ignorados por
ausência de `TEST_DATABASE_URL`.
A Fase 6 do Plano 04 foi concluída em 2026-09-11 com a migration
`20260911_0008`: postagem idempotente de vendas no estoque, reversão
compensatória no cancelamento e devoluções parciais/totais aprovadas foram
adicionadas. A validação local passou com 49 testes e 64 testes PostgreSQL
ignorados por ausência de `TEST_DATABASE_URL`.
A Fase 9 do Plano 04 foi concluída em 2026-09-11 com a migration
`20260911_0010`: configuração central de módulos ativos para Comercial,
Compras, Estoque, Financeiro e Relatórios foi adicionada. A visibilidade não
substitui a autorização backend. A validação local passou com 53 testes e 65
testes PostgreSQL ignorados por ausência de `TEST_DATABASE_URL`.
A Fase 7 do Plano 04 foi concluída em 2026-09-11 com a migration
`20260911_0009`: categorias financeiras, contas/caixas, títulos a receber e
pagar, parcelamento, liquidações reversíveis e fluxo previsto versus realizado
foram adicionados. A validação local passou com 51 testes e 65 testes
PostgreSQL ignorados por ausência de `TEST_DATABASE_URL`.
A Fase 8 do Plano 04 foi concluída em 2026-09-11: relatórios agregados de
comercial, compras, estoque e financeiro e um dashboard ERP foram adicionados
com cálculo no backend. A validação local permaneceu em 51 testes aprovados e
65 testes PostgreSQL ignorados por ausência de `TEST_DATABASE_URL`.

Princípio central: privilegiar simplicidade sobre abrangência. Não tratar um
ERP genérico como autorização para construir uma plataforma completa antes de
existir necessidade concreta.

## 2. Stack definida

### Frontend

- React
- TypeScript
- Vite
- Interface web administrativa responsiva

### Backend

- Python
- FastAPI
- Pydantic para validação de dados e contratos da API

### Persistência

- PostgreSQL
- SQLAlchemy como ORM
- Alembic para migrations

### Versionamento

- Git
- GitHub

## 3. Organização preferencial

O projeto deve seguir uma organização monorepo:

    erp-geral/
    ├── frontend/
    ├── backend/
    ├── AGENTS.md
    ├── AI_CONTEXT.md
    ├── .env.example
    ├── .gitignore
    └── README.md

A estrutura interna deve permanecer modular e fácil de alterar. Conforme o
projeto crescer, o frontend pode ser organizado por funcionalidade, por
exemplo customers/, suppliers/, employees/, products/ e sales/.

## 4. Arquitetura

Fluxo principal:

    React + TypeScript
            ↓ HTTP/JSON
    FastAPI + Pydantic
            ↓ regras de negócio e acesso aos dados
    SQLAlchemy
            ↓
    PostgreSQL

Regras de organização:

- O frontend nunca acessa o PostgreSQL diretamente.
- Toda regra de negócio, validação persistente e acesso aos dados passa pelo
  backend.
- APIs devem ser explícitas, previsíveis e orientadas às entidades da V1.
- Evitar criar uma abstração genérica de CRUD antes de existir uma necessidade
  concreta.
- Alterações de schema devem ser feitas por migrations Alembic, nunca por
  alterações manuais não versionadas no banco.
- A separação entre cadastro mestre e transações deve ser preservada.

## 5. Modelo de domínio da V1

Os nomes abaixo representam o modelo conceitual. A implementação deverá
definir tipos, nulabilidade, índices e nomes físicos das colunas de forma
consistente com este contexto. IDs são gerados pelo sistema e não são
informados manualmente pelo usuário.

### Clientes

Campos obrigatórios:

- ID
- Nome
- Cidade
- Estado
- Rua
- Número

Campo opcional:

- Complemento

### Fornecedores

Campos obrigatórios:

- ID
- Nome
- Cidade
- Estado
- Rua
- Número
- CNPJ

Campo opcional:

- Complemento

### Funcionários

Campos obrigatórios:

- ID
- Nome completo
- Cidade
- Estado
- Rua
- Número
- CPF
- Data de nascimento

Campos opcionais:

- Complemento
- RG
- Status operacional (`ativo`), com padrão `true` para novos registros e
  registros existentes após a migration da Fase 12.

### Produtos

Campos obrigatórios:

- ID
- Nome do produto
- Categoria
- Preço de custo
- Preço de venda
- ID do fornecedor

### Vendas

Campos obrigatórios:

- ID
- ID do cliente
- ID do funcionário
- Data da venda

Vendas são criadas como `CONCLUIDA` e podem ser marcadas como `CANCELADA`.
O cancelamento registra data e motivo opcional e preserva a Venda, os
VendaItens e os cadastros raiz referenciados. A API pública não oferece mais
exclusão física de vendas consolidadas.

### Itens da venda

Campos obrigatórios:

- ID
- ID da venda
- ID do produto
- Quantidade
- Preço unitário
- ID do fornecedor no momento da venda (`fornecedor_id`)

VendaItem não possui exclusão independente pela interface e não deve existir
sem uma Venda. `venda_id` permanece obrigatório; não utilizar `SET NULL` nem
criar itens órfãos.

Uma venda deve ser separada de seus itens. Assim, uma venda pode conter
múltiplos produtos sem repetir ou conflitar o ID da venda.

Relacionamentos mínimos:

    vendas.cliente_id      → clientes.id
    vendas.funcionario_id  → funcionarios.id
    venda_itens.venda_id   → vendas.id
    venda_itens.produto_id → produtos.id
    venda_itens.fornecedor_id → fornecedores.id
    produtos.fornecedor_id → fornecedores.id

O nome do produto não deve ser armazenado como informação redundante em
venda_itens; deve ser obtido pela relação com produtos. O preço aplicado na
venda deve ser preservado em venda_itens.preco_unitario, sem depender do preço
atual cadastrado em produtos. Snapshot histórico do nome do produto fica fora
da V1.

## 6. Interface administrativa

A aplicação deve possuir uma interface web administrativa com as seguintes
áreas:

- Dashboard simples
- Clientes
- Produtos
- Fornecedores
- Funcionários
- Nova venda
- Lista de vendas

Para os cadastros, considerar inicialmente as operações:

- listar;
- criar;
- visualizar;
- editar;
- excluir.

As listagens de clientes, fornecedores, funcionários, produtos e vendas são
paginadas no backend e retornam `items`, `page`, `page_size`, `total` e
`total_pages`, preservando os filtros existentes.

O design deve ser:

- genérico e adaptável a lojas em geral;
- clean e acolhedor;
- baseado em cores frias;
- composto por cards e componentes com formas arredondadas;
- responsivo;
- visualmente consistente.

## 7. Regras de domínio e dados

- IDs principais devem ser únicos e gerados pelo sistema.
- Campos obrigatórios devem possuir constraints de nulabilidade coerentes no
  banco e não aceitar NULL.
- Campos opcionais devem aceitar NULL quando a ausência da informação for
  apropriada.
- Não criar valores padrão artificiais apenas para evitar NULL.
- Não substituir ausência de informação por strings vazias sem necessidade.
- Complemento permanece opcional em clientes, fornecedores e funcionários.
- RG permanece opcional em funcionários e não é obrigatório na V1.
- Relacionamentos devem utilizar foreign keys com constraints explícitas no
  PostgreSQL.
- Utilizar outras constraints e índices do PostgreSQL quando aplicável.
- CNPJ de fornecedores deve possuir restrição de unicidade.
- CPF de funcionários deve possuir restrição de unicidade.
- CPF e CNPJ devem ser tratados como strings, nunca como números.
- RG deve ser tratado como string.
- Estado deve ser armazenado como texto curto.
- Número do endereço deve utilizar representação que permita valores como 10A,
  S/N ou equivalentes no futuro.
- quantidade deve ser maior que zero e pode admitir valores fracionários,
  persistidos com representação decimal adequada; unidade de medida permanece
  fora da V1.
- preco_custo, preco_venda e preco_unitario não podem ser negativos.
- Valores monetários devem utilizar tipo decimal apropriado, nunca ponto
  flutuante binário.
- data_nascimento deve utilizar tipo de data apropriado.
- data_venda deve utilizar tipo apropriado para data e hora da operação.
- No fluxo de inclusão de um item, o backend deve consultar o preco_venda
  atual do produto e persistir esse valor como preco_unitario.
- Vendas novas devem iniciar com status `CONCLUIDA`; cancelamento não deve
  apagar a venda nem seus itens.
- Entidades operacionais principais devem manter `created_at` e `updated_at`.
- A leitura de configurações de aparência não deve persistir defaults como
  efeito colateral.
- O total de cada item deve ser derivado de quantidade multiplicada por
  preco_unitario.
- O total da venda deve ser derivado da soma dos itens.
- Não persistir valor_total na venda nem nos itens na V1.
- Não permitir que o histórico de preço de uma venda dependa do preço atual do
  produto.
- `venda_itens.fornecedor_id` deve preservar o fornecedor associado ao Produto
  no momento da venda e não pode ser nulo.
- Alterações posteriores em `produtos.fornecedor_id` não podem modificar o
  snapshot histórico já persistido em `venda_itens`.
- A validação de CPF, RG e CNPJ permanece limitada a tipos, unicidade e regras
  básicas; não adicionar bibliotecas externas de validação documental na V1.
- Campos, tabelas e relacionamentos devem ser adicionados ou alterados por
  migrations.

## 8. Segurança

Segurança deve ser considerada desde o início:

- Nunca versionar secrets.
- Manter arquivos .env fora do Git.
- Fornecer .env.example sem valores secretos.
- Não armazenar senhas em texto puro caso autenticação seja adicionada.
- Validar entradas no backend.
- Utilizar SQLAlchemy e queries parametrizadas.
- Aplicar o princípio de menor privilégio.
- Tratar CPF, RG e CNPJ como dados sensíveis e evitar exposição desnecessária.
- Não registrar informações sensíveis em logs sem necessidade.
- Manter .gitignore adequado.
- Não adicionar credenciais, chaves, certificados ou dumps de banco ao
  repositório.
- Usuários possuem papéis `ADMIN`, `MANAGER` e `OPERATOR`; autorização é
  aplicada no backend por uma matriz central de permissões.
- Senhas usam hash PBKDF2 com salt; sessões usam tokens assinados, expiração e
  revogação persistida.
- A trilha de auditoria não armazena senha, token ou segredo.

## 9. Fora do escopo da V1

Não implementar sem solicitação explícita:

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
- importação ou exportação;
- campos personalizados;
- schema configurável pela interface;
- integrações externas;
- telefone e e-mail adicionais;
- CEP;
- cargos;
- data de admissão;
- múltiplos fornecedores por produto.

A arquitetura pode permitir essas evoluções posteriormente, mas não deve
carregar agora a complexidade necessária para implementá-las.

## 10. Decisões arquiteturais

### V1 pequena sobre uma fundação evolutiva

Decisão: manter o escopo operacional reduzido, usando PostgreSQL, foreign
keys, constraints, migrations, validação no backend e módulos separados.

Motivo: permitir evolução estrutural sem transformar a V1 em uma plataforma
complexa ou em um banco completamente dinâmico.

Consequência: novas colunas e tabelas devem ser introduzidas de forma
explícita, com alteração coordenada de migration, modelo, schema, API e
interface quando necessário.

### Venda e itens de venda separados

Decisão: uma venda possui seus próprios dados e uma coleção de itens.

Motivo: uma única venda pode conter vários produtos.

Consequência: o produto é relacionado por produto_id; não duplicar o nome do
produto em cada item.

### Categoria como texto simples

Decisão: categoria permanece como campo de texto em produtos na V1.

Motivo: manter o cadastro simples sem introduzir uma entidade de categorias ou
um fluxo de categorias cadastráveis.

Consequência: categorias normalizadas ou administráveis ficam fora da V1.

### Funcionário responsável pela venda

Decisão: vendas possui funcionario_id, referenciando funcionarios.id.

Motivo: registrar qual funcionário realizou a venda sem introduzir comissões,
cargos ou regras adicionais.

### Preço histórico do item

Decisão: venda_itens.preco_unitario armazena o preço de venda efetivamente
aplicado no momento da inclusão do item.

Motivo: preservar o histórico de preço mesmo quando produtos.preco_venda for
alterado posteriormente.

Consequência: o backend deve buscar o preço atual do produto no momento da
operação e persistir uma cópia no item. O nome do produto continua sendo lido
pela relação com produtos; snapshots de nome ou outros atributos ficam para
versões futuras.

### Fornecedor histórico do item

Decisão: `venda_itens.fornecedor_id` armazena o fornecedor associado ao Produto
no momento da criação da venda, com `NOT NULL` e foreign key para
`fornecedores.id`.

Motivo: preservar a referência histórica mesmo que o fornecedor atual do
Produto seja alterado posteriormente.

Consequência: o frontend não informa o fornecedor histórico; o backend captura
`Produto.fornecedor_id` de um Produto persistido. A migration da Fase 13 faz
backfill dos itens existentes usando o fornecedor atual do Produto no momento
da migration, que é a única informação disponível para registros anteriores.

### Totais derivados

Decisão: não persistir valor_total em vendas nem em venda_itens na V1.

Motivo: evitar dados redundantes enquanto não existir necessidade concreta de
persistência adicional.

Consequência: o total do item é quantidade multiplicada por preco_unitario e o
total da venda é a soma dos totais derivados de seus itens.

### Exclusão física com integridade referencial

Decisão: exclusões podem ser físicas na V1, desde que não removam
silenciosamente dados relacionados. Cadastros raiz referenciados permanecem
protegidos contra exclusão quando possuem dependências.

Motivo: manter a V1 simples e preservar a integridade e o histórico das
vendas.

Consequência: quando um registro estiver referenciado e sua remoção
comprometer a integridade ou o histórico, o backend deve impedir a exclusão e
retornar uma resposta clara para a interface. A Venda pode ser excluída
explicitamente pelo usuário; nessa operação, o backend exclui primeiro e na
mesma transação exclusivamente os VendaItens daquela venda e depois a Venda.
Não utilizar cascatas destrutivas a partir de Cliente, Funcionário, Produto ou
Fornecedor. VendaItem continua com `venda_id` obrigatório, sem `SET NULL`, e
itens órfãos não são permitidos. Soft delete, arquivamento e auditoria de
exclusões ficam fora da V1. O campo `ativo` foi introduzido posteriormente
na Fase 12 do `IMPLEMENTATION_PLAN_02.md` como status operacional de
Funcionários; ele não representa soft delete.

### Tipos e regras mínimas de dados

Decisão: IDs são gerados pelo sistema; documentos são strings; valores
monetários utilizam decimal; datas utilizam tipos próprios; e foreign keys
possuem constraints explícitas no PostgreSQL.

Motivo: garantir consistência de persistência sem adicionar validações
específicas ou regras de negócio desnecessárias.

### Backend como fronteira de dados

Decisão: toda comunicação com o banco e toda regra de negócio passa pelo
FastAPI.

Motivo: centralizar segurança, validação, consistência e regras de domínio.

Consequência: o React consome contratos HTTP/JSON e não conhece as credenciais
ou a conexão do PostgreSQL.

### Status operacional de Funcionários

Decisão: Funcionários possuem `ativo`, um booleano não nulo com padrão `true`.

Motivo: permitir retirar um funcionário da operação de novas vendas sem
remover seu cadastro ou quebrar o histórico já registrado.

Consequências:

- novos funcionários nascem ativos;
- funcionários existentes permanecem ativos após a migration;
- `GET /api/employees` sem filtro continua incluindo ativos e inativos;
- `GET /api/employees?active=true` é o filtro mínimo usado por Nova Venda;
- o backend rejeita novas vendas com funcionário inativo;
- vendas históricas continuam exibindo o funcionário inativo;
- a proteção de exclusão de funcionário referenciado permanece inalterada;
- o PATCH existente permite ativar e inativar o funcionário.

### Listagem e detalhamento de Vendas

Decisão: a leitura operacional de Vendas prioriza Produto, Valor Total,
Cliente e Funcionário, nessa ordem.

Consequências:

- uma Venda com um único item exibe o nome do Produto;
- uma Venda com dois ou mais Produtos exibe `<n> produtos`, contando IDs de
  Produtos distintos;
- o total continua derivado dos `VendaItens` e de seus preços históricos;
- o detalhamento exibe quantidade, preço unitário histórico, subtotal e o
  fornecedor histórico de `VendaItem`;
- a leitura do fornecedor histórico utiliza `venda_itens.fornecedor_id`, sem
  reconstruí-lo a partir do fornecedor atual do Produto;
- o backend carrega Produto e Fornecedor histórico com eager loading para
  evitar consultas individuais por item;
- filtros e detalhes relacionais de Cliente ou Fornecedor permanecem fora da
  Fase 14.

## 11. Pontos ainda não especificados

As ambiguidades arquiteturais relevantes da V1 estão resolvidas neste
documento. A obrigatoriedade, a opcionalidade e a nulabilidade dos campos
foram formalizadas no modelo de domínio e nas regras de dados.

Detalhes de implementação, como comprimentos exatos de strings e formatos de
contratos da API, podem ser definidos durante a implementação sem alterar as
decisões arquiteturais registradas aqui.

## 12. Estado de implementação e backlog orientativo

- [x] Bootstrap do monorepo, frontend e backend executáveis.
- [x] Contratos iniciais da API, migrations e modelos da V1.
- [x] Validações, endpoints, testes principais, telas administrativas,
  vendas e dashboard simples.
- [x] Reexecutar duas vezes a suíte PostgreSQL após a correção do rollback de
  exclusão de venda.
- [x] Fase 11: correções de UI e consistência visual.
- [x] Implementação da Fase 12: status de Funcionários, filtro em Nova Venda,
  bloqueio backend e testes associados.
- [x] Validação PostgreSQL final da Fase 12 após a correção do identificador
  da migration.
- [x] Fase 13 concluída: snapshot histórico de fornecedor em `VendaItem`,
  integridade referencial, serviço e testes.
- [x] Fase 14 concluída: listagem e detalhamento de Vendas com valores
  históricos, fornecedor histórico e validação PostgreSQL (`63 passed`).
- [x] Fase 15 concluída: detalhes relacionais derivados de Clientes e
  Fornecedores, com validação funcional e responsiva.
- [x] Fase 16 concluída: infraestrutura de filtros, piloto de Funcionários e
  validação PostgreSQL real confirmada pelo usuário.
- [x] Fase 17 concluída: busca global e filtros detalhados por módulo.
- [x] Fase 18 concluída: auditoria, correções de regressão, validação final e
  documentação atualizada; PostgreSQL real aprovado externamente pelo usuário.
- [x] Plano 03 — Fase 1: auditoria visual e responsiva concluída sem redesign
  ou alteração de regras de negócio.
- [x] Plano 03 — Fase 2: aparência, identidade, nomenclaturas, logo e prévia
  em tempo real implementadas e validadas.
- [x] Plano 03 — Fase 3: campos personalizados isolados por cadastro,
  validação tipada, formulários dinâmicos e detalhes concluídos.
- [x] Plano 04 — Fase 0: fundação transacional, cancelamento não destrutivo,
  timestamps, paginação backend-driven, dashboard agregado e observação em
  vendas.
- [x] Plano 04 — Fase 1: autenticação, usuários, papéis, autorização
  backend-first, sessões revogáveis e auditoria operacional.
- [ ] Funcionalidades fora da V1 permanecem no backlog futuro.

## 13. Comandos

Os comandos principais estão documentados em `README.md`. No backend, use os
executáveis da `.venv` sem ativar a virtualenv:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes PostgreSQL exigem `TEST_DATABASE_URL` fornecida externamente e
apontando para um banco dedicado com sufixo `_test`.

## 14. Última atualização

Data: 2026-09-11

- Ambiguidades do modelo resolvidas: categoria, funcionário responsável,
  histórico de preço, totais, exclusões e tipos mínimos de dados.
- Regra transacional atualizada na Fase 0: o fluxo público cancela vendas e
  preserva a Venda e seus VendaItens; a exclusão física de venda não é mais
  oferecida.
- Obrigatoriedade, opcionalidade e nulabilidade dos campos da V1 formalizadas;
  RG permanece opcional.
- Modelo de Vendas, relacionamentos e regras de domínio atualizados para
  refletir as decisões aprovadas.
- Fases 1 a 10 implementadas e validadas; a suíte PostgreSQL passou duas vezes
  consecutivas com `57 passed` em cada execução.
- Fase 11 concluída com correções de overflow/alinhamento dos itens de Nova
  Venda e hierarquia visual do Dashboard.
- Fase 12 implementada com `funcionarios.ativo`, migration reversível,
  `GET /api/employees?active=true`, PATCH de status, bloqueio de vendas por
  funcionário inativo e indicação visual no frontend.
- O identificador inicial da migration excedia `VARCHAR(32)` em
  `alembic_version`; foi corrigido para `20260820_0001` sem criar migration
  adicional. A validação PostgreSQL pós-correção foi executada e confirmada
  pelo usuário.
- Fase 13 concluída com `venda_itens.fornecedor_id` obrigatório, FK para
  `fornecedores.id`, backfill da migration `20260820_0002`, captura do snapshot
  pelo serviço de vendas e proteção de fornecedor historicamente referenciado.
- Fase 14 implementada com resumo do fornecedor histórico no contrato de
  leitura, eager loading sem N+1, listagem na ordem Produto/Valor Total/
  Cliente/Funcionário, contagem de múltiplos produtos e detalhe completo dos
  itens.
- Fase 0 do Plano 04 implementada com a migration `20260911_0002`, timestamps,
  cancelamento não destrutivo, observação em vendas, paginação backend-driven,
  dashboard agregado e leitura de aparência sem persistência implícita.
- Fase 1 do Plano 04 implementada com a migration `20260911_0003`, usuários,
  sessões revogáveis, papéis, autorização backend-first e logs de auditoria;
  autenticação no frontend e CORS para `Authorization` foram integrados.
- A validação local da Fase 14 ficou em `27 passed, 36 skipped, 1 warning` no
  backend e `34 passed` no frontend; os skips ocorreram porque
  `TEST_DATABASE_URL` não estava definida. Ruff, lint, typecheck e build
  passaram.
- A validação manual confirmou desktop, notebook e mobile próximo de
  `390 × 844`, sem overflow horizontal; o detalhe foi verificado com 1 e 3
  itens e a listagem com 1, 2 e 3 produtos.
- A validação PostgreSQL da Fase 14 foi confirmada pelo usuário com `63 passed`.
- A Fase 15 adicionou detalhes relacionais sem persistência duplicada: o detalhe
  de Fornecedor deriva Produtos por `Produto.fornecedor_id`, e o detalhe de
  Cliente deriva Produtos comprados por `Cliente → Vendas → VendaItens → Produto`.
- Produtos comprados são consolidados por `produto_id` em query agregada, com
  soma Decimal de `VendaItem.quantidade`; Produtos com o mesmo nome e IDs
  diferentes permanecem registros distintos.
- O detalhe de Fornecedor usa `selectinload(Fornecedor.produtos)` para evitar
  N+1; o detalhe de Cliente usa uma query `GROUP BY`/`SUM`, sem cascata N+1.
- A implementação local da Fase 15 passou Ruff, backend `27 passed, 38 skipped,
  1 warning`, frontend lint, typecheck, `38 passed` e build naquele checkpoint.
  A validação final posterior confirmou os detalhes relacionais em desktop,
  notebook e mobile; a Fase 15 está concluída.
- A Fase 16 foi implementada como infraestrutura mínima e reutilizável: o
  `SearchInput` é compartilhado, enquanto o piloto de Funcionários mantém
  estado de edição e estado aplicado para busca e `ativo`, com aplicação
  explícita e limpeza dos filtros.
- O endpoint `GET /api/employees` aceita `search` e `active`; `search` é
  normalizado por trim e aplicado apenas aos campos visíveis da listagem
  (`nome_completo`, `cpf`, `cidade` e `estado`). Os parâmetros são combinados
  com AND e enviados por query string HTTP, sem introduzir estado na URL da
  aplicação.
- A Fase 16 não adicionou filtros relacionais invisíveis, engine universal,
  migration ou funcionalidade de módulos posteriores. A validação local passou
  com Ruff, backend `27 passed, 39 skipped, 1 warning`, frontend lint,
  typecheck, `44 passed` e build; os skips ocorreram porque
  `TEST_DATABASE_URL` não estava definida neste processo. A revisão manual
  confirmou busca, combinação com ativos, limpeza, zero resultados e o layout
  em 1440×900, 1024×768 e 390×844. A validação PostgreSQL real foi concluída
  e confirmada pelo usuário.
- A Fase 17 aplicou o padrão de busca e filtros a Clientes, Produtos,
  Funcionários, Fornecedores e Vendas. A busca usa debounce de 300 ms; filtros
  detalhados ficam em painel suspenso, usam opções reais quando aplicável e
  preservam combinação AND e aplicação explícita.
- A Fase 18 corrigiu três regressões confirmadas: ordem de imports da migration
  da Fase 12, acionamento duplicado ao limpar o `SearchInput` e contribuição das
  tabelas para a rolagem horizontal da página no mobile.
- Validação final da Fase 18: Ruff, lint, typecheck e build aprovados; frontend
  com `58 passed`; suíte backend atual com `71 tests collected`; UI aprovada em
  `1440 × 900`, `1024 × 768` e `390 × 844`; console sem erros; OpenAPI e
  auditoria de secrets aprovados. A execução PostgreSQL real foi realizada
  externamente e confirmada como aprovada pelo usuário; a contagem e os warnings
  dessa execução externa não foram transcritos nesta atualização.
- O Plano 03 — Fase 1 foi auditado nos viewports `1440 × 900`, `1024 × 768`
  e `390 × 844`; não foram encontrados overflow, corte ou desalinhamento que
  justificassem alteração de layout. A validação técnica passou Ruff, pytest
  PostgreSQL (`71 passed` no checkpoint), lint, typecheck, testes frontend e
  build. O registro foi feito no commit local `f42edcc`.
- O Plano 03 — Fase 2 adicionou a tabela singleton explícita
  `configuracoes_aparencia` e a migration `20260823_0001`, mantendo a cadeia
  Alembic linear e o head único `20260823_0001`:
  `20260818_0001 → 20260820_0001 → 20260820_0002 → 20260823_0001`.
- A aparência é lida e atualizada por `GET/PATCH /api/settings/appearance`,
  pode ser restaurada por `POST /api/settings/appearance/reset` e aceita logo
  PNG, JPEG ou WEBP de até 2 MB em `PUT /api/settings/appearance/logo`. Cores,
  raios e nomenclaturas possuem contratos tipados e validação; não há CSS
  livre nem credenciais persistidas. Logos ficam em armazenamento local de
  branding e são servidas pelo caminho `/uploads/branding/`.
- A tela Configurações → Aparência usa CSS variables, preview em tempo real,
  nomenclaturas aplicadas à navegação, logo com fallback e layout responsivo.
  A validação de migration downgrade/upgrade, Ruff e PostgreSQL passou com
  `74 passed, 16 warnings`; frontend passou lint, typecheck, `60 passed` e
  build. A checagem manual confirmou a tela em `1440 × 900`, `1024 × 768` e
  `390 × 844`, sem overflow.
- O Plano 03 — Fase 3 adicionou estruturas independentes de definição e valor
  para Clientes, Produtos, Funcionários e Fornecedores, sem `entity_type`
  universal e sem colunas dinâmicas nas tabelas raiz. A migration
  `20260823_0002` mantém a cadeia linear e cria oito tabelas específicas.
- Os tipos suportados são texto, inteiro, decimal, data, booleano e select.
  O backend valida cada tipo, opções permitidas, campos obrigatórios e
  isolamento por módulo; valores ausentes não geram linhas vazias. Campos
  desativados deixam de aparecer nos formulários, mas valores existentes são
  preservados. Campos personalizados não foram adicionados a Vendas nem aos
  filtros.
- A área Configurações → Campos personalizados permite criar, editar, ordenar,
  ativar e desativar definições por cadastro. Os formulários de criação/edição
  renderizam campos ativos por tipo e os detalhes exibem apenas valores
  preenchidos.
- A validação da Fase 3 passou downgrade/upgrade no banco de testes, Ruff,
  backend PostgreSQL com `75 passed, 17 warnings`, frontend lint, typecheck,
  `62 passed` e build. A checagem responsiva confirmou a administração de
  campos em `1440 × 900`, `1024 × 768` e `390 × 844`, sem overflow.
- Warnings conhecidos de Starlette/httpx e de teardown transacional permanecem
  como dívida técnica não bloqueante; dependências não foram atualizadas apenas
  para removê-los.

## Atualização posterior — personalização visual controlada

- A área Configurações → Aparência foi simplificada para manter o branding
  global sempre disponível e oferecer o botão `Ativar modo de personalização
  visual`; não há mais edição de overrides de página exposta nessa tela.
- Foi adicionada a migration reversível `20260823_0004`, criando
  `configuracoes_aparencia_elementos` para overrides tipados e independentes
  das tabelas comerciais. A cadeia Alembic permanece linear, com head
  `20260823_0004`.
- O backend expõe `GET/PUT/DELETE /api/settings/appearance/overrides` por
  chave estável, valida o tipo (`TEXT`, `SURFACE`, `BUTTON`, `INPUT`, `TABLE`,
  `PAGE`) e aceita somente propriedades permitidas, sem CSS livre, expressões,
  seletores ou regras arbitrárias de layout.
- O frontend usa `data-customization-key` e metadados de tipo/grupo/página em
  componentes reutilizáveis. O editor suporta hover, seleção por clique,
  navegação normal, preview imediato em draft, salvar, cancelar, desfazer e
  restaurar o elemento; a resolução segue elemento específico → herança
  disponível → branding global → default.
- Foram instrumentados Dashboard, Clientes, Produtos, Funcionários,
  Fornecedores, Vendas e Nova venda com elementos `PAGE`, `TEXT`, `SURFACE`,
  `BUTTON`, `INPUT` e `TABLE`. A edição permanece limitada a cor, peso/tamanho
  controlados, superfície, borda, raio e tokens de tabela conforme o tipo.
- Campos Personalizados não foram alterados e não foram incorporados ao
  editor visual. Nenhuma migration ou tabela comercial foi criada para essa
  funcionalidade; o Plano 04 não foi iniciado.
- A validação deste checkpoint passou com backend PostgreSQL em duas execuções
  consecutivas: `80 passed, 17 warnings` em cada uma. Frontend: `67 passed`,
  typecheck, lint e build aprovados. A validação manual confirmou desktop,
  notebook e mobile em `1440 × 900`, `1024 × 768` e `390 × 844`, sem overflow;
  o console permaneceu sem erros.
- Permanecem apenas os warnings conhecidos de Starlette/httpx e do teardown
  transacional SQLAlchemy. Nenhuma dependência foi alterada para ocultá-los.

## Atualização posterior — descoberta visual automática e editor híbrido

- O editor visual agora resolve elementos apresentados no DOM mesmo quando eles
  não possuem `data-customization-key` explícito. A resolução considera tag,
  role, texto próprio, atributos semânticos, classes estáveis e
  `getComputedStyle`, ignorando wrappers sem apresentação visual e qualquer
  subtree marcado com `data-customization-ignore`.
- Foram cobertas as categorias semânticas `TEXT`, `ICON`, `BUTTON`, `INPUT`,
  `SELECT`, `TEXTAREA`, `SURFACE`, `BORDERED_SURFACE`, `CARD`, `TABLE`,
  `TABLE_HEADER`, `TABLE_CELL`, `LINK`, `BADGE` e `PAGE`. A persistência mantém
  o contrato backend existente, mapeando essas categorias para os tipos
  canônicos já autorizados (`TEXT`, `SURFACE`, `BUTTON`, `INPUT`, `TABLE` e
  `PAGE`), sem CSS arbitrário ou novo schema.
- A identidade híbrida prioriza metadado explícito, depois uma chave estrutural
  estável por página/região/semântica e, por último, um fallback somente para
  prévia. Não são persistidos `nth-child`, posição, XPath, seletor bruto ou
  classe gerada. Elementos sem identidade estável mostram aviso e o salvamento
  é bloqueado, sem esconder a prévia.
- A tabela usa a chave estável da tabela mais a coluna identificada pelo
  cabeçalho; linhas repetidas da mesma coluna compartilham a identidade sem
  depender da posição da linha. A seleção expõe a hierarquia visual de
  ancestrais, permitindo subir de texto/célula para card, superfície ou página.
- O modo `Selecionar` intercepta clique, hover e seleção com overlay fixo,
  enquanto `Navegar` preserva links, botões e o comportamento normal do ERP.
  Eventos são delegados no `document`, portanto conteúdos dinâmicos,
  dropdowns, modais e portais também podem ser inspecionados. Toolbar, painel,
  overlay e estilos do editor ficam fora da descoberta.
- Componentes compartilhados receberam identidade visual controlada quando
  apropriado (Sidebar, Modal, FeedbackBanner, EmptyState, ErrorState e
  LoadingState). Isso não alterou a lógica de Campos Personalizados nem os
  fluxos comerciais.
- Preview e drafts são aplicados imediatamente. Overrides automáticos usam uma
  folha de estilos controlada por atributos estáveis, além da aplicação direta
  durante a inspeção, para sobreviver a rerenders e troca de rota. Cancelar,
  desfazer, restaurar elemento, salvar e reset continuam disponíveis.
- A cobertura frontend do editor inclui texto e superfície sem instrumentação,
  categorias semânticas, tabela repetida, hierarquia, conteúdo modal/portal,
  modos Selecionar/Navegar e exclusão da UI do próprio editor. O frontend
  terminou com `72 passed` em 16 arquivos, lint, typecheck e build aprovados.
- A validação manual passou nas telas Dashboard, Clientes, Produtos,
  Funcionários, Fornecedores e Vendas, incluindo navegação normal e seleção
  visual automática. Em `1440 × 900`, `1024 × 768` e `390 × 844`, toolbar,
  painel, controles e overlay permaneceram contidos, sem overflow horizontal;
  no mobile o painel foi dimensionado dentro da largura disponível.
- A migration head continuou em `20260823_0004`; nenhuma migration, model,
  endpoint ou regra backend foi criada ou alterada nesta etapa. Ruff passou e
  a suíte PostgreSQL real passou duas vezes consecutivas com `80 passed,
  17 warnings` em cada execução.
- Os warnings restantes são os já conhecidos de Starlette/httpx e
  `SAWarning: transaction already deassociated from connection` no teardown.
  Não foram atualizadas dependências para suprimi-los. Credenciais não foram
  persistidas em arquivos ou código; o Plano 04/Fase 18 não foi iniciado e
  nenhum commit ou push foi realizado.

## Atualização posterior — correção do upload e exibição da logo

- A causa raiz da imagem quebrada foi confirmada no fluxo real: o backend
  persistia `/uploads/branding/<uuid>.png` e servia corretamente esse recurso
  em `http://127.0.0.1:8000`, mas o frontend usava o caminho relativo
  diretamente no `<img>`. O navegador então buscava a URL no Vite
  (`5173/uploads/...`), que respondia o `index.html` com `200 text/html` em
  vez da imagem.
- O contrato de upload foi explicitado como `multipart/form-data`, com campo
  `file`, e o OpenAPI passou a descrevê-lo. O frontend usa `FormData` e não
  fixa manualmente o header multipart/boundary. MIME ausente ou genérico pode
  ser inferido apenas como auxílio, mas o backend confirma o formato real com
  Pillow; extensão sozinha nunca autoriza o arquivo.
- Foi adicionada a resolução centralizada `resolveBackendAssetUrl` para
  transformar referências relativas da API em URLs do backend usando
  `VITE_API_BASE_URL`/`API_BASE_URL`. A Sidebar recebe a URL resolvida e não
  contém host hardcoded. A API continua persistindo referência pública
  relativa, separada do caminho físico local.
- PNG, JPEG e WEBP são os únicos formatos aceitos. O limite bruto permanece
  em 2 MB. O conteúdo é aberto e verificado antes de ser persistido; arquivos
  corrompidos, MIME/formato incompatível e payloads acima do limite retornam
  erro controlado, preservando a logo anterior.
- Logos rasterizadas são normalizadas sem upscale, com limite de 1024 px por
  lado, preservando proporção e usando `contain` no container existente da
  Sidebar. PNG/WebP preservam transparência; JPEG é convertido para RGB quando
  necessário; orientação EXIF de JPEG é normalizada. Há limite adicional de
  25 milhões de pixels para proteção contra decompression bombs, com resposta
  controlada. Nomes físicos continuam sendo UUIDs e a extensão corresponde ao
  formato salvo.
- A troca segue a ordem validar/processar/salvar arquivo novo/atualizar
  configuração/confirmar/remover arquivo anterior. Restaurar padrão remove a
  referência customizada e retorna ao fallback. Não há bytes de imagem na
  tabela de aparência, base64 persistido ou migration nova.
- Os testes backend cobrem upload PNG, dimensões 3000×3000, horizontal,
  vertical, imagem pequena sem upscale, transparência, EXIF, MIME genérico,
  corrupção, MIME/formato inválido, excesso de bytes, URL pública, troca,
  restauração e OpenAPI multipart. A suíte PostgreSQL sequencial passou duas
  vezes com `83 passed, 17 warnings` em cada execução.
- A validação manual confirmou upload pela interface, preview/feedback de
  sucesso, URL no backend, `GET` da imagem com `200 image/png`, persistência
  após reload, substituição e restauração. A URL resolveu para o backend em
  `1440 × 900`, `1024 × 768` e `390 × 844`; o console não apresentou erros.
- A validação frontend passou lint, typecheck, `74 passed` e build. Ruff
  passou. A dependência explícita adicionada foi Pillow para validação e
  normalização raster, além de `python-multipart` para o contrato de upload.
  Campos Personalizados e o Editor Visual não foram alterados além da
  continuação da exibição correta da logo; nenhum commit ou push foi feito.

## Atualização — Plano 05, Fase 0 concluída em 2026-09-11

A Fase 0 foi estabilizada antes do início da Fase 1. A migration
`20260911_0006` foi corrigida preservando `revision` e `down_revision`: o seed
do depósito agora usa `INSERT` SQL com `CURRENT_TIMESTAMP`, inclui timestamps
obrigatórios e define um único depósito padrão por índice parcial PostgreSQL.

O recebimento de compras agora acumula somente a quantidade efetivamente
recebida em cada confirmação. Foram cobertos recebimento parcial, excesso,
recebimento final e confirmação idempotente. A lógica operacional de compras,
vendas, devoluções e relatórios resolve o depósito padrão por serviço; não há
dependência crítica de `deposito_id = 1`.

A fixture PostgreSQL foi ajustada para usar savepoints por teste e repor os
dados de referência das migrations após a limpeza. Isso mantém unidades,
conta de caixa, módulos, depósito padrão e configuração de estoque disponíveis
sem contaminar o banco de desenvolvimento.

Validações realizadas:

- PostgreSQL existente em revisão anterior: upgrade até `20260911_0010`;
- PostgreSQL vazio descartável: upgrade completo até `head`;
- PostgreSQL descartável: downgrade até `base` e re-upgrade completo;
- backend PostgreSQL: `118 passed`;
- backend sem `TEST_DATABASE_URL`: `53 passed`, `65 skipped` por ausência
  intencional da conexão;
- Ruff: aprovado;
- frontend: `75 passed`, lint, typecheck e build aprovados;
- `git diff --check`: aprovado.

Os bancos descartáveis foram removidos após a validação. Nenhuma credencial
foi persistida em arquivo, código ou documentação. A Fase 1 do Plano 05 foi
executada na sequência.

## Atualização — Plano 05, Fase 1 concluída em 2026-09-11

A Fase 1 transformou o backend comercial em uma fatia vertical operável. A
navegação agora expõe Orçamentos, Pedidos, Vendas comerciais e Devoluções, e
Configurações expõe as condições de pagamento com listagem, criação, edição e
ativação/inativação.

Orçamentos e pedidos possuem telas para listagem, busca, filtro, criação,
edição em rascunho, detalhes, transições controladas, conversão e impressão
HTML. Devoluções permitem quantidades totais ou parciais, motivo e aprovação
com entrada no estoque. A venda exibe origem do pedido, condição de pagamento,
observações e status/cancelamento.

A migration `20260911_0011` adiciona `vendas.pedido_venda_id` e
`vendas.condicao_pagamento_id`, com foreign keys e índice único para manter a
origem sem duplicação. A API recebeu atualização de condições, documentos,
filtros comerciais e listagem de devoluções. As conversões continuam
idempotentes e os snapshots comerciais permanecem preservados.

Validação: PostgreSQL `118 passed`; frontend `77 passed`, lint, typecheck e
build aprovados; Ruff e `git diff --check` aprovados. A Fase 2 foi executada
na sequência.

## Atualização — Plano 05, Fase 2 concluída em 2026-09-11

A interface de Compras agora expõe Pedidos e Recebimentos. Pedidos podem ser
listados, pesquisados, filtrados, criados, editados em rascunho, emitidos,
cancelados e acompanhados por quantidades solicitadas, recebidas e pendentes.
Recebimentos suportam quantidade real parcial ou total, custo efetivo,
rascunho, confirmação e histórico por pedido.

A confirmação usa o depósito padrão resolvido pelo serviço, preserva a
idempotência da entrada no estoque e registra o histórico de custos. O backend
recebeu busca por número/fornecedor e edição protegida de pedidos sem
recebimentos. Não houve migration nova na fase.

Validação da fase: PostgreSQL específico de compras `1 passed`; suíte backend
`118 passed`; frontend `77 passed`, lint, typecheck e build aprovados; Ruff e
`git diff --check` aprovados. A Fase 3 foi executada na sequência.

## Atualização — Plano 05, Fase 3 concluída em 2026-09-11

A interface de Estoque agora expõe Saldos, Movimentações, Ajustes, Inventários
e Depósitos. Saldos possuem filtros de depósito, produto, categoria e baixo
estoque. Movimentações exibem metadados operacionais. Ajustes exigem motivo e
usam os tipos append-oriented existentes. Inventários permitem contar vários
produtos, calcular diferenças e confirmar ajustes. Depósitos podem ser
criados, editados, ativados/inativados e definidos como padrão.

O backend recebeu edição de depósitos e listagem de inventários, sem migration
nova. O saldo continua calculado a partir dos eventos; a confirmação de
inventário permanece idempotente. Transferência entre depósitos ficou fora da
fase por ausência de contrato atual e foi registrada para evolução posterior.

Validação da fase: PostgreSQL específico de estoque `1 passed`; suíte backend
`118 passed`; frontend `77 passed`, lint, typecheck e build aprovados; Ruff e
`git diff --check` aprovados. A Fase 4 foi executada na sequência.

## Atualização — Plano 05, Fase 4 concluída em 2026-09-11

A navegação de Financeiro agora expõe Contas a receber, Contas a pagar e
Caixa e fluxo de caixa. Vendas comuns e vendas convertidas de pedidos geram
títulos a receber automaticamente; recebimentos confirmados de compras geram
títulos a pagar. Os links `origem_tipo`/`origem_id` preservam a origem e a
criação é idempotente.

Títulos podem ser filtrados por tipo e status, consultados com suas parcelas,
liquidados parcial ou totalmente e revertidos. O fluxo de caixa separa
previsto de realizado, e a interface permite cadastrar contas/caixas. A
fundação da migration `20260911_0009` foi reutilizada sem migration nova.

Validação da fase: suíte backend PostgreSQL `118 passed`; frontend `77
passed`, lint, typecheck e build aprovados; Ruff e `git diff --check`
aprovados. A Fase 5 será executada na sequência.

## Atualização — Plano 05, Fase 5 concluída em 2026-09-11

A área de Relatórios agora expõe Dashboard ERP, Comercial, Compras, Estoque e
Financeiro. O dashboard apresenta clientes, produtos ativos, vendas
concluídas, baixo estoque, valores em aberto e valores realizados. Os
relatórios reutilizam as agregações backend existentes e oferecem filtro de
período no comercial e exportação CSV dos dados carregados.

Também foram expostos indicadores de pedidos e recebimentos pendentes,
saldos e movimentações, títulos vencidos e fluxo previsto versus realizado.
Não foi necessária migration nova nesta fase.

Validação da fase: suíte backend PostgreSQL `118 passed`; frontend `77
passed`, lint, typecheck e build aprovados; Ruff e `git diff --check`
aprovados. A Fase 6 será executada na sequência.

## Atualização — Plano 05, Fase 6 concluída em 2026-09-11

Foi criada a tela Configurações → Módulos para listar e ativar/desativar
Comercial, Compras, Estoque, Financeiro e Relatórios pela API existente. A
barra lateral agora reflete os módulos ativos e uma rota acessada diretamente
quando seu módulo está desativado apresenta estado explícito de indisponibilidade.

A autenticação e as permissões da API continuam sendo a proteção efetiva; a
ocultação do menu não é usada como segurança. Não houve migration nova.

Validação da fase: frontend `77 passed`, lint, typecheck e build aprovados;
Ruff e `git diff --check` aprovados. A Fase 7 será executada na sequência.

## Atualização — Plano 05, Fase 7 concluída em 2026-09-11

O backend passou a emitir headers de segurança contra MIME sniffing, framing,
referrer excessivo e acesso desnecessário a câmera, microfone e
geolocalização. Login, bootstrap e upload da logo receberam limites de
tentativa por IP com resposta `429` e `Retry-After`.

Sessões continuam com expiração, revogação no logout e bloqueio de usuários
inativos. O upload mantém validação de conteúdo, tipo, tamanho e dimensões,
normalização e remoção do arquivo anterior. A auditoria agora cobre também
compras, recebimentos, estoque, inventários e operações financeiras, além de
autenticação, usuários, aparência, módulos e vendas. A revisão de índices não
encontrou necessidade de migration adicional. Em múltiplas instâncias, o rate
limiting deve ser aplicado também no proxy/gateway compartilhado.

Validação da fase: suíte backend PostgreSQL `118 passed`; frontend `77
passed`, lint, typecheck e build aprovados; Ruff e `git diff --check`
aprovados. Os testes direcionados de auditoria passaram (`3 passed`). O Plano
05 foi concluído.

## Atualização — Plano 06, Fase 0 concluída em 2026-09-11

O ambiente principal local foi alinhado ao estado atual do código. O banco
`erp_geral` foi respaldado logicamente antes da alteração e atualizado de
`20260911_0001` até `20260911_0011` pelas migrations Alembic, sem uso de
`stamp` e sem remoção de dados. O backend atual foi reiniciado em
`127.0.0.1:8000`; o frontend continua em `127.0.0.1:5173`.

O endpoint `/api/health` agora diferencia processo, banco e schema, retornando
`degraded` quando o PostgreSQL está indisponível ou quando a revisão aplicada
não corresponde ao head do código. Os endpoints principais de módulos,
dashboard, relatórios, cadastros, compras, estoque e financeiro foram
validados após a migração.

Validação da fase: suíte backend PostgreSQL `118 passed`; frontend `77
passed`, typecheck e lint aprovados; `ruff check app` aprovado. O comando
abrangente `ruff check .` ainda aponta 53 linhas longas preexistentes em
migrations históricas e não foi usado como justificativa para reformatá-las.
O Plano 06 prossegue pela Fase 1, com foco nos smoke tests ponta a ponta.

## Atualização — Plano 06, Fase 1 concluída em 2026-09-11

A Fase 1 foi executada no ambiente principal local com dados artificiais
identificáveis. Foram validados os fluxos de orçamento → pedido → venda →
estoque → contas a receber → liquidação; pedido de compra → recebimentos
parcial e final → estoque → contas a pagar; devolução parcial e inventário
com ajuste de saldo. A desativação temporária de Relatórios bloqueou a rota
direta na interface e o módulo foi reativado ao final.

Foi corrigida a regra financeira de compras: `create_receipt` não cria mais
obrigação; `confirm_receipt` cria o título a pagar na mesma transação da
entrada de estoque, com confirmação repetida idempotente. Nenhum dado
existente foi removido; os registros artificiais de validação permanecem
identificados no banco principal.

Validação da fase: backend PostgreSQL `118 passed`; frontend `77 passed`,
lint, typecheck e build aprovados; `ruff check app` e `git diff --check`
aprovados. O Plano 06 prossegue pela Fase 2, voltada a erros, autenticação e
permissões na experiência do usuário.

## Atualização — Plano 06, Fase 2 concluída em 2026-09-11

A Fase 2 alinhou a experiência do frontend às regras de autenticação e
autorização. O cliente HTTP agora diferencia indisponibilidade, 401, 403,
404, 409, 422 e 5xx, limpa token e sinaliza a sessão expirada, preservando
mensagens de domínio e substituindo detalhes técnicos por mensagens seguras.

Foi adicionada a área Configurações → Usuários, baseada nas APIs existentes,
com listagem, criação, edição de papel, vínculo com funcionário e ativação ou
inativação. A navegação oculta essa área para papéis que não podem administrar
usuários quando a autenticação está ativa; a autorização final continua no
backend.

Validação da fase: frontend `79 passed`, typecheck e build aprovados; lint
aprovado com os avisos preexistentes de efeitos React. O Plano 06 prossegue
pela Fase 3, voltada à consistência de produto e navegação.

## Atualização — Plano 06, Fase 3 concluída em 2026-09-11

A navegação foi consolidada para apresentar uma única área Comercial, com
Nova venda, Vendas, Orçamentos, Pedidos e Devoluções. A entrada duplicada de
Vendas comerciais foi removida do menu, sem retirar a rota direta existente.

As listas de Comercial e Compras agora resolvem e exibem nomes de clientes e
fornecedores, mantendo identificadores técnicos apenas como fallback. A
organização atual de filtros, cabeçalhos, tabelas, ações e estados vazios foi
mantida coerente entre telas equivalentes.

Validação da fase: frontend `79 passed`, typecheck e build aprovados. O Plano
06 prossegue pela Fase 4, voltada a relatórios, responsividade e
acessibilidade.

## Atualização — Plano 06, Fase 4 concluída em 2026-09-11

Os relatórios deixaram de compartilhar o identificador visual `dashboard`.
Dashboard ERP, Comercial, Compras, Estoque e Financeiro agora possuem
identificadores próprios, suportados pela migration `20260911_0012` e pelo
contrato de aparência do backend.

O layout dos relatórios passou a distinguir carregamento de estado vazio,
mantendo filtros de período, totalizadores e exportação CSV. Os controles
continuam rotulados e a estrutura responsiva existente cobre sidebar/drawer,
filtros, tabelas, formulários e modais nos breakpoints previstos.

Validação da fase: backend PostgreSQL `120 passed`; frontend `79 passed`,
typecheck e build aprovados; Ruff e `git diff --check` aprovados. O Plano 06
prossegue pela Fase 5, o gate final de maturidade V1.

## Marco V1 — Plano 06 concluído em 2026-09-11

O gate final confirmou os fluxos principais do ERP Geral no ambiente local:
venda com estoque e contas a receber, compra com recebimentos parcial e final
e contas a pagar no momento correto, devolução parcial, inventário com ajuste,
permissões por papel e ativação ou desativação de módulos.

Ambiente final: frontend em `127.0.0.1:5173`, backend em `127.0.0.1:8000`,
banco `erp_geral`, health `ok` e Alembic em `20260911_0012`. As suítes finais
passaram com backend PostgreSQL `120 passed` e frontend `79 passed`; lint,
`ruff check app`, typecheck, build e `git diff --check` também foram
aprovados. O `ruff check .` ainda aponta 53 linhas longas preexistentes em
migrations históricas.

Classificação do marco: **SIM, COM AJUSTES**. Fiscal, NF-e, SPED,
contabilidade, folha, CRM, BI avançado e integrações bancárias automáticas
continuam fora do escopo e são evoluções futuras, não bloqueadores da V1
operacional.

## Atualização — Plano 07, Fase 0 em 2026-09-12

O Plano 07 passou a ter um caminho oficial de instalação reproduzível. A
configuração `.env` é resolvida pela raiz do monorepo, o exemplo assume
produção protegida e a instalação técnica está documentada em
`docs/INSTALLATION.md`. Foi adicionado o script `scripts/install.ps1`.

Validação: scripts PowerShell parseados; backend `ruff check app` e testes
focados `13 passed` aprovados; `git diff --check` aprovado.

A validação online de uma instalação nova com PostgreSQL descartável não foi
executada neste ambiente porque as ferramentas de administração PostgreSQL não
estão disponíveis e não se deve tocar no banco principal. O runbook deixa essa
prova operacional explícita para o primeiro ambiente isolado do cliente.

## Atualização — Plano 07, Fase 1 em 2026-09-12

O ERP agora tem execução web de produção documentada em
`docs/PRODUCTION.md`. Foram adicionados `scripts/start-backend.ps1` para
Uvicorn sem reload, `scripts/serve-frontend.ps1` e
`scripts/static_server.py`, que serve o build Vite com fallback de SPA. Também
foram incluídos modelos de unidade systemd e reverse proxy Nginx em `deploy/`.

O cliente HTTP usa `VITE_API_BASE_URL` quando configurado; no build sem esse
override, usa a origem atual, permitindo frontend e API sob o mesmo domínio.
O link de impressão comercial passou a usar o mesmo resolvedor de origem.
Validação: frontend `79 passed`, typecheck e build aprovados; refresh de
`/customers` respondeu `200`; scripts PowerShell parseados.

## Atualização — Plano 07, Fase 2 em 2026-09-12

Foram adicionados `scripts/backup.ps1`, `scripts/restore.ps1` e
`scripts/update.ps1`, além do runbook `docs/BACKUP.md`. O backup inclui dump
custom do PostgreSQL e `backend/storage` em arquivo separado; o restore exige
`-ConfirmRestore` e destino explícito; o update segue backup → migrations →
build, deixando stop/start sob controle do operador. Nenhum script destrutivo
foi executado contra o banco principal.

Validação: os três scripts PowerShell foram parseados sem erros e
`git diff --check` foi executado. O ensaio real de restore permanece pendente
de um PostgreSQL isolado, por segurança e pela ausência dos clientes
administrativos PostgreSQL neste ambiente.

## Atualização — Plano 07, Fase 3 em 2026-09-12

O primeiro acesso agora possui status explícito em
`GET /api/auth/bootstrap-status` e uma tela `/setup` que cria o primeiro
administrador usando o token configurado, grava a sessão e encaminha a pessoa
para o ERP. O bootstrap continua protegido no backend, limitado por taxa e
irrepetível depois da criação do primeiro usuário.

O Dashboard passou a oferecer atalhos de configuração de aparência e módulos.
O caminho completo está descrito em `docs/ONBOARDING.md`, incluindo revisão de
depósito, unidades, condições de pagamento e categorias antes da primeira
operação. Validação: frontend `79 passed`, typecheck e build aprovados.

## Atualização — Plano 07, Fase 4 em 2026-09-12

Os defaults de distribuição foram reforçados. CORS agora é configurável por
`CORS_ORIGINS`, documentação OpenAPI pode ser desligada por
`API_DOCS_ENABLED` e fica desativada por padrão em produção, e `STORAGE_DIR`
permite apontar branding/uploads para armazenamento persistente fora do código.
Foi criado `docs/SECURITY.md` com o checklist de secrets, HTTPS, PostgreSQL,
permissões, uploads, rate limiting e backups. A validação da configuração de
produção continua rejeitando secrets ausentes, curtos ou com marcadores de
exemplo.

Validação: backend `ruff check app` aprovado; testes focados `16 passed, 9
skipped`; frontend permanece com `79 passed`, typecheck e build aprovados.

## Atualização — Plano 07, Fase 5 em 2026-09-12

Foi criada a fonte de versão em `backend/app/core/version.py`, o
`CHANGELOG.md`, os runbooks `docs/RELEASE.md` e `docs/SUPPORT.md`, e o script
sanitizado `scripts/diagnostic.ps1`. `/api/health` informa a versão junto dos
estados de processo, banco e schema; `/api/system-info` exige autenticação e
retorna somente versão, ambiente e estado de migrations.

Validação: backend `ruff check app` aprovado; testes focados `15 passed`; script
de diagnóstico parseado; frontend permanece com `79 passed`, typecheck e build
aprovados. O fluxo não lê nem exibe o `.env`.

## Atualização — Plano 07, Fase 6 em 2026-09-12

O sistema visual foi formalizado em `docs/DESIGN_SYSTEM.md`, com tokens de
espaçamento, altura de controle e foco visível no `frontend/src/index.css`.
Relatórios agora usam `report-toolbar`, `report-filter-bar` e
`report-metrics-grid`, evitando a toolbar sem estilo e a grade quebrada em
telas intermediárias. Ações de tabela receberam alvo mínimo de teclado e os
breakpoints de 900px/560px foram alinhados para filtros e métricas.

Validação: a suíte frontend permanece `79 passed`, typecheck e build aprovados;
Ruff do backend segue aprovado.

## Atualização — Plano 07, Fase 7 em 2026-09-12

Foi corrigida a causa da tela quebrada de Devoluções: as rotas estáticas
`/api/sales/returns` e `/api/sales/returns/{return_id}` agora precedem a rota
dinâmica `/{sale_id}`. Um teste protege essa ordem. Nos relatórios, a toolbar
foi separada em filtros e ações, as métricas ganharam grade própria e as ações
de tabela receberam área mínima de interação. A base visual foi preservada;
não há skill Impeccable instalada neste ambiente.

Validação: backend `ruff check app` e `16 passed`; frontend `79 passed`,
typecheck e build aprovados.

## Atualização — Plano 07, Fase 8 em 2026-09-12

A navegação diferencia agora **Pedidos de venda** e **Pedidos de compra**.
Modais passaram a focar o botão de fechamento ao abrir e a associar descrição
com `aria-describedby`; links, botões e ações de tabela têm foco visível. Os
relatórios foram verificados visualmente no navegador com API online, métricas
carregadas, filtros separados e navegação sem rótulos ambíguos. Os breakpoints
existentes de 900px e 560px empilham filtros, ações e métricas sem corte.

Validação: frontend `79 passed`, typecheck e build aprovados; backend
`ruff check app` e `16 passed` aprovados.
