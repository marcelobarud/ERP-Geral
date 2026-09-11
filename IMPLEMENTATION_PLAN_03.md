# CRM Geral — IMPLEMENTATION_PLAN_03

> Este documento foi produzido quando o projeto ainda se chamava CRM Geral.
> O produto foi posteriormente reposicionado como ERP Geral.

## Objetivo

Este plano representa o terceiro ciclo de evolução do CRM Geral.

O foco é melhorar a consistência visual e iniciar a transformação do CRM em uma aplicação mais adaptável a diferentes negócios, através de:

1. revisão visual;
2. personalização de identidade/interface;
3. campos personalizados nos principais cadastros.

Este plano deve permanecer curto e controlado.

Funcionalidades adicionais serão avaliadas posteriormente em outro ciclo de planejamento.

---

# Estado inicial

O projeto parte do estado estabilizado após o `IMPLEMENTATION_PLAN_02.md`.

Os planos anteriores estão concluídos e congelados:

```text
IMPLEMENTATION_PLAN.md
IMPLEMENTATION_PLAN_02.md
```

Não alterar o conteúdo histórico desses arquivos.

`AI_CONTEXT.md` representa o estado arquitetural corrente.

---

# Princípios deste ciclo

Preservar:

- FastAPI;
- PostgreSQL;
- SQLAlchemy;
- Alembic;
- React;
- TypeScript;
- Vite;
- regras históricas de Vendas;
- separação entre banco de desenvolvimento e banco de teste;
- frontend responsivo;
- APIs explícitas;
- migrations controladas.

Evitar:

- engines excessivamente genéricas;
- SQL dinâmico inseguro;
- alterações físicas de schema disparadas diretamente pelo usuário;
- armazenamento de segredos no repositório;
- refatorações fora do escopo;
- novas funcionalidades não previstas.

---

# Fase 1 — Revisão visual e consistência de layout

## Objetivo

Realizar uma auditoria visual das telas existentes e corrigir problemas de:

- alinhamento;
- espaçamento;
- botões colados;
- inconsistência entre ações;
- distância entre toolbar e conteúdo;
- alinhamento entre inputs e botões;
- margens inconsistentes;
- problemas responsivos.

Esta fase NÃO é um redesign.

A identidade visual atual deve ser preservada.

---

## Escopo

Revisar pelo menos:

- Dashboard;
- Clientes;
- Produtos;
- Funcionários;
- Fornecedores;
- Vendas;
- Nova Venda;
- telas de detalhe;
- modais;
- toolbars;
- filtros;
- formulários;
- tabelas.

---

## Botões e ações

Padronizar:

- espaçamento entre botões;
- alinhamento vertical;
- altura quando aparecem junto de inputs;
- ações primárias;
- ações secundárias;
- ações destrutivas;
- grupos de ações.

Evitar correções isoladas como:

```css
margin-left: 7px;
```

quando um container com `gap` resolve corretamente o layout.

---

## Espaçamento

Consolidar padrões reutilizáveis quando houver benefício real.

Exemplo conceitual:

```css
--space-xs
--space-sm
--space-md
--space-lg
--space-xl
```

Não é obrigatório usar esses nomes exatos.

O objetivo é reduzir valores arbitrários espalhados pelo CSS.

---

## Responsividade

Validar:

```text
1440 × 900
1024 × 768
390 × 844
```

Confirmar:

- ausência de overflow horizontal da página;
- botões acessíveis;
- toolbars utilizáveis;
- campos sem compressão excessiva;
- ações sem sobreposição;
- espaçamento coerente em mobile.

---

## Restrições

Não:

- alterar regras de negócio;
- criar migration;
- mudar identidade visual;
- introduzir nova biblioteca de UI;
- reescrever frontend;
- criar sistema de temas nesta fase.

---

## Validação

Executar:

### Frontend

- lint;
- typecheck;
- testes;
- build.

### Manual

Percorrer todas as telas principais nos três viewports definidos.

---

## Encerramento

Após aprovação:

1. atualizar `AI_CONTEXT.md` somente se novos padrões estruturais relevantes tiverem sido definidos;
2. revisar `git status`;
3. revisar `git diff`;
4. executar `git diff --check`;
5. criar commit separado em PT-BR.

Commit sugerido:

```text
style: padroniza alinhamentos e espaçamentos da interface
```

Descrição sugerida:

```text
Revisa layouts, toolbars, botões, formulários e tabelas para melhorar
alinhamento, espaçamento e responsividade sem alterar a identidade visual.
```

---

# Fase 2 — Aparência, identidade e nomenclaturas

## Objetivo

Criar uma área:

```text
Configurações
└── Aparência
```

capaz de personalizar a identidade visual e algumas nomenclaturas do CRM sem editar código.

As alterações devem possuir preview em tempo real antes de serem salvas.

---

# 2.1 Aparência

Permitir controlar inicialmente:

- nome exibido do sistema;
- logo;
- cor primária;
- cor secundária;
- cor de destaque;
- cores estruturais realmente necessárias;
- arredondamento configurável, se compatível com o design atual.

Não transformar cada propriedade CSS em configuração.

---

# 2.2 CSS variables

Consolidar elementos configuráveis através de CSS variables.

Exemplo conceitual:

```css
--color-primary
--color-secondary
--color-accent
--color-background
--color-surface
--color-text
--radius-control
--radius-card
```

Os nomes finais devem seguir a arquitetura real do projeto.

Não tornar espaçamentos estruturais livremente configuráveis pelo usuário.

---

# 2.3 Preview em tempo real

Fluxo esperado:

```text
usuário altera configuração
↓
estado React
↓
CSS variables/interface
↓
preview imediato
```

Salvar somente mediante ação explícita:

```text
Salvar alterações
```

Também fornecer:

```text
Restaurar padrão
```

Alterações ainda não salvas não devem ser confundidas com configuração persistida.

---

# 2.4 Nomenclaturas de interface

Permitir alterar somente nomenclaturas funcionais relevantes.

Exemplos:

```text
Dashboard
Clientes
Produtos
Funcionários
Fornecedores
Vendas
Nova Venda
```

Possibilidades:

```text
Clientes → Consumidores
Funcionários → Equipe
Vendas → Pedidos
Dashboard → Visão Geral
```

A aplicação deve utilizar essas nomenclaturas de maneira consistente nas áreas principais da interface.

---

# 2.5 Textos que NÃO são configuráveis

Não permitir alterar:

- mensagens internas de erro;
- mensagens de validação;
- textos técnicos;
- erros de API;
- mensagens de segurança;
- mensagens de banco;
- contratos OpenAPI;
- regras de negócio.

O sistema de nomenclaturas é destinado à interface e identidade do produto.

Não é um CMS.

---

# 2.6 Persistência

Criar estrutura de persistência adequada para a configuração visual.

Evitar:

- valores espalhados em várias tabelas sem necessidade;
- JSON completamente livre e sem validação;
- configuração arbitrária de CSS.

Utilizar contrato tipado e validado.

---

# 2.7 Logo

Permitir trocar a imagem da logo.

A implementação deve separar conceitualmente:

```text
configuração da identidade
```

de:

```text
armazenamento físico do arquivo
```

A solução inicial pode utilizar armazenamento local se isso for adequado ao ambiente atual, mas não deve acoplar toda a UI a uma estratégia específica de storage.

Preparar a arquitetura para futura troca por storage externo sem implementar integração cloud neste plano.

Validar:

- tipo de arquivo;
- tamanho;
- substituição;
- fallback para logo padrão;
- comportamento quando arquivo não existe.

Não permitir upload arbitrário executável.

---

# 2.8 Segurança

Nunca armazenar credenciais junto das configurações de aparência.

A tabela/configuração de branding não deve servir como armazenamento genérico de configurações técnicas.

---

# 2.9 Responsividade

A tela Configurações → Aparência deve funcionar em:

```text
1440 × 900
1024 × 768
390 × 844
```

---

# 2.10 Testes

Backend:

- leitura da configuração;
- atualização;
- validação de cores/valores;
- restauração quando aplicável;
- logo;
- entradas inválidas.

Frontend:

- carregar configuração;
- preview;
- salvar;
- restaurar padrão;
- alterar nomenclatura;
- alterar cores;
- logo;
- loading;
- erro.

Executar:

- Ruff;
- Pytest;
- PostgreSQL real;
- lint;
- typecheck;
- testes frontend;
- build.

---

# Encerramento da Fase 2

Atualizar `AI_CONTEXT.md` com a arquitetura efetivamente implementada.

Criar commit separado em PT-BR.

Sugestão:

```text
feat: adiciona personalização visual e identidade do CRM
```

Descrição sugerida:

```text
Adiciona configurações de aparência, logo, cores e nomenclaturas de
interface com preview em tempo real e persistência no backend.
```

---

# Fase 3 — Campos personalizados por módulo

## Objetivo

Permitir que o usuário crie novas informações nos principais cadastros sem precisar alterar manualmente o código ou criar novas colunas físicas no PostgreSQL.

Exemplo:

```text
Clientes
→ adicionar campo "Profissão"
```

Depois disso:

```text
Novo Cliente
Editar Cliente
Detalhe Cliente
```

passam a reconhecer o campo personalizado.

Registros anteriores permanecem sem valor até serem preenchidos.

---

# 3.1 Módulos iniciais

Implementar para:

```text
Clientes
Produtos
Funcionários
Fornecedores
```

Não implementar campos personalizados em Vendas neste plano.

---

# 3.2 Decisão arquitetural obrigatória

NÃO criar coluna física no PostgreSQL para cada campo criado pelo usuário.

Não executar:

```sql
ALTER TABLE clientes ADD COLUMN ...
```

em runtime como funcionalidade do CRM.

Também NÃO utilizar uma única estrutura universal:

```text
custom_fields
custom_field_values
entity_type
```

para todos os módulos.

---

# 3.3 Estruturas separadas por domínio

Criar estruturas específicas:

```text
customer_custom_fields
customer_custom_field_values

product_custom_fields
product_custom_field_values

employee_custom_fields
employee_custom_field_values

supplier_custom_fields
supplier_custom_field_values
```

Os nomes finais podem seguir a convenção existente do projeto, desde que a separação por domínio seja preservada.

---

# 3.4 Definição de campo

Cada definição deve possuir, no mínimo, conceitos equivalentes a:

```text
id
nome
tipo
obrigatório
ativo
ordem de exibição
```

Adicionar apenas metadados realmente necessários.

---

# 3.5 Valores

Cada tabela de valores deve relacionar:

```text
registro da entidade
campo personalizado
valor
```

Não criar registros vazios para todos os objetos existentes ao criar um novo campo.

Exemplo:

Se existem:

```text
1000 Clientes
```

e é criado:

```text
Profissão
```

não criar 1000 linhas vazias.

Ausência de valor representa campo não preenchido.

---

# 3.6 Tipos iniciais

Suportar inicialmente um conjunto controlado.

Preferência:

```text
Texto
Número inteiro
Número decimal
Data
Sim/Não
Lista de opções
```

Não criar sistema de plugins de tipos.

---

# 3.7 Validação

Cada tipo deve possuir validação correspondente no backend.

Exemplos:

```text
Número decimal
→ Decimal

Data
→ date

Sim/Não
→ boolean

Lista
→ valor deve pertencer às opções permitidas
```

Não confiar apenas no frontend.

---

# 3.8 Interface administrativa

Criar área:

```text
Configurações
└── Campos personalizados
```

organizada por módulo.

Exemplo:

```text
Clientes
├── Profissão
├── Tipo de cliente
└── Limite de crédito

Produtos
└── Marca
```

Permitir:

- criar;
- editar propriedades permitidas;
- alterar ordem;
- ativar;
- desativar.

---

# 3.9 Criação dentro do cadastro

Se for simples e coerente com a UX, pode existir atalho:

```text
+ Adicionar campo
```

dentro do formulário de uma entidade.

Esse atalho deve utilizar a mesma infraestrutura administrativa.

Não criar dois sistemas diferentes.

---

# 3.10 Desativação

Ao desativar um campo:

```text
ativo = false
```

o campo deixa de aparecer para preenchimento normal.

Os valores existentes permanecem armazenados.

Não apagar dados automaticamente.

---

# 3.11 Exclusão permanente

Não implementar exclusão física automática como comportamento normal.

Se houver exclusão permanente nesta versão, ela deve:

- ser explicitamente administrativa;
- possuir confirmação clara;
- informar perda dos valores;
- excluir definição e valores de forma transacional.

Se isso aumentar demasiadamente o escopo, deixar exclusão permanente fora desta fase e utilizar somente desativação.

---

# 3.12 Obrigatoriedade

Um campo personalizado pode ser marcado como obrigatório.

Importante:

Registros antigos não devem se tornar inválidos imediatamente apenas porque um novo campo foi criado como obrigatório.

A obrigatoriedade deve ser aplicada quando o registro for criado ou atualizado dentro do fluxo definido.

Documentar claramente a regra efetivamente implementada.

---

# 3.13 Formulários

Novo/Editar devem renderizar campos ativos dinamicamente.

A renderização deve respeitar:

- tipo;
- ordem;
- obrigatório;
- opções;
- valor existente.

Não substituir os campos oficiais do domínio.

Campos personalizados são complementares.

---

# 3.14 Detalhes

Detalhes de:

- Cliente;
- Produto;
- Funcionário;
- Fornecedor

devem apresentar os campos personalizados preenchidos de forma organizada.

Evitar poluir a tela quando nenhum campo personalizado existir.

---

# 3.15 Campos oficiais

Não permitir ao usuário:

- excluir;
- renomear estruturalmente;
- mudar tipo;
- transformar em opcional;

campos oficiais do banco através desse sistema.

A personalização de nomenclaturas da Fase 2 é apenas visual.

Ela não altera schema ou contratos do domínio.

---

# 3.16 Código compartilhado

Embora as tabelas sejam separadas, lógica comum pode ser reutilizada para:

- tipos;
- validação;
- renderização frontend;
- componentes;
- serialização;
- comportamento visual.

Evitar duplicar quatro implementações completas.

Ao mesmo tempo, evitar abstração excessiva baseada em `entity_type`.

A separação do domínio no banco deve permanecer explícita.

---

# 3.17 Campos personalizados e filtros

Não integrar automaticamente campos personalizados aos filtros existentes neste plano.

Exemplo:

Criar:

```text
Cliente → Profissão
```

não significa automaticamente adicionar:

```text
Filtro por Profissão
```

na tela Clientes.

Essa evolução poderá ser estudada posteriormente.

---

# 3.18 Histórico de Vendas

Campos personalizados não devem alterar:

- `VendaItem.preco_unitario`;
- `VendaItem.fornecedor_id`;
- histórico de vendas;
- totais;
- regras de exclusão.

---

# 3.19 Migrations

Criar migrations controladas para as novas tabelas estruturais.

Validar no `crm_geral_test`:

```text
upgrade
downgrade
upgrade
```

Não executar downgrade no banco de desenvolvimento.

---

# 3.20 Testes mínimos

Por módulo:

- criar definição;
- preencher valor;
- atualizar valor;
- ausência de valor;
- registro anterior sem valor;
- campo ativo;
- campo inativo;
- obrigatório;
- tipo inválido;
- Decimal;
- Data;
- Boolean;
- Lista;
- isolamento entre módulos.

Cenário obrigatório:

```text
Campo "Profissão" de Cliente
```

não pode aparecer ou ser aceito em:

```text
Produto
Funcionário
Fornecedor
```

---

# 3.21 Frontend

Validar:

- Configurações;
- criação de campo;
- edição;
- ativação/desativação;
- ordenação;
- Novo registro;
- Editar registro;
- Detalhe;
- estados sem campos personalizados;
- erro;
- loading.

---

# 3.22 Responsividade

Validar:

```text
1440 × 900
1024 × 768
390 × 844
```

A criação de campos não pode tornar os formulários existentes inutilizáveis em mobile.

---

# 3.23 Qualidade

Executar:

Backend:

- Ruff;
- Pytest;
- PostgreSQL real;
- migrations.

Frontend:

- lint;
- typecheck;
- testes;
- build.

---

# Encerramento da Fase 3

Atualizar `AI_CONTEXT.md` com:

- estruturas separadas por módulo;
- tipos suportados;
- regras de obrigatoriedade;
- desativação;
- ausência de valor;
- renderização dinâmica;
- ausência de integração automática com filtros.

Marcar `IMPLEMENTATION_PLAN_03.md` como concluído somente após validação completa.

Criar commit separado em PT-BR.

Sugestão:

```text
feat: adiciona campos personalizados aos cadastros
```

Descrição sugerida:

```text
Permite criar e utilizar campos personalizados em Clientes, Produtos,
Funcionários e Fornecedores com estruturas independentes por domínio,
validação tipada e preservação dos dados ao desativar campos.
```

---

# Critério final do Plano 03

O plano somente está concluído quando:

```text
Fase 1 ✅
Fase 2 ✅
Fase 3 ✅
```

e:

- backend aprovado;
- PostgreSQL aprovado;
- migrations aprovadas;
- frontend aprovado;
- responsividade aprovada;
- nenhum segredo versionado;
- documentação atualizada;
- três commits separados realizados;
- nenhum push automático realizado.

---

# Fora do escopo

Não implementar neste plano:

- campos personalizados em Vendas;
- campos personalizados automaticamente como filtros;
- relatórios dinâmicos;
- BI;
- engine universal de schema;
- criação de tabelas pelo usuário;
- criação direta de colunas PostgreSQL pelo usuário;
- permissões;
- autenticação;
- multi-tenant;
- integrações cloud de storage;
- Plano 04.

Possíveis evoluções devem aguardar novo planejamento.

---

# Estado final

Ao concluir:

```text
IMPLEMENTATION_PLAN.md
→ congelado

IMPLEMENTATION_PLAN_02.md
→ congelado

IMPLEMENTATION_PLAN_03.md
→ concluído
```

Encerrar o ciclo.

Não iniciar novas funcionalidades até novo planejamento.

## Registro de conclusão

Data: 2026-08-23

- Fase 1 concluída e registrada no commit local `f42edcc`.
- Fase 2 concluída e registrada no commit local `2e37dd8`.
- Fase 3 concluída e registrada em commit local separado nesta entrega.
- Backend, PostgreSQL de testes, migrations, frontend, responsividade e
  documentação foram validados.
- `IMPLEMENTATION_PLAN.md` e `IMPLEMENTATION_PLAN_02.md` permaneceram
  congelados.
- Nenhum push foi realizado e o Plano 04 não foi iniciado.
