# Plano técnico da V1 — CRM Geral

> Este documento foi produzido quando o projeto ainda se chamava CRM Geral.
> O produto foi posteriormente reposicionado como ERP Geral.

O plano abaixo segue exclusivamente as decisões de AI_CONTEXT.md e as regras de AGENTS.md. A implementação deve ocorrer de forma incremental, com commits pequenos e validação ao final de cada fase.

## Fase 1 — Bootstrap do monorepo

**Objetivo:** criar a base mínima do projeto sem adicionar funcionalidades de negócio.

**Áreas prováveis:**
- frontend/
- backend/
- .gitignore
- .env.example
- Configurações de qualidade e testes.

**Tarefas:**
1. Criar a estrutura frontend/ e backend/.
2. Inicializar o frontend com React, TypeScript e Vite.
3. Inicializar o backend Python com estrutura mínima do FastAPI.
4. Criar configurações separadas para desenvolvimento e testes.
5. Definir variáveis esperadas no .env.example, sem secrets.
6. Configurar lint, typecheck e formatação conforme as ferramentas escolhidas.
7. Criar a estrutura básica de testes backend e frontend.
8. Garantir que configurações locais, banco, secrets e artefatos de build estejam no .gitignore.

**Dependências:** nenhuma.

**Critérios de conclusão:**
- Frontend e backend possuem inicialização independente.
- Nenhum código de domínio ou acesso ao banco foi criado ainda.
- O projeto possui verificações mínimas de qualidade.
- Não há secrets versionados.

**Verificações:**
- Typecheck inicial do frontend.
- Verificação de importação/inicialização do backend.
- Execução de um teste mínimo em cada lado.
- Revisão do .gitignore e .env.example.

**Riscos:**
- Adicionar dependências ou abstrações sem necessidade.
- Acoplar o frontend ao banco.
- Criar configuração obrigatória de Docker, Redis ou filas.

**Checkpoint sugerido:** commit de bootstrap do monorepo.

## Fase 2 — Fundação do backend

**Objetivo:** estabelecer a base executável do FastAPI, configuração e conexão futura com PostgreSQL.

**Áreas prováveis:**
- backend/app/
- backend/tests/
- backend/alembic.ini
- Configuração de ambiente do backend.

**Tarefas:**
1. Organizar módulos básicos de configuração, aplicação e API.
2. Implementar leitura de configuração por variáveis de ambiente.
3. Definir a URL de conexão do PostgreSQL sem expor credenciais.
4. Configurar SQLAlchemy e o engine.
5. Configurar criação e encerramento de sessões de banco.
6. Configurar Alembic para usar a mesma configuração do banco.
7. Criar tratamento básico e consistente de erros HTTP.
8. Criar endpoint de health check sem regra de negócio.
9. Definir a fronteira entre rotas, schemas, serviços e persistência.
10. Evitar criar um repositório genérico antes de existir necessidade concreta.

**Dependências:** Fase 1.

**Critérios de conclusão:**
- FastAPI inicia com configuração externa.
- O health check responde corretamente.
- A conexão com PostgreSQL pode ser configurada sem alterar código.
- Alembic reconhece a configuração do projeto.
- Erros básicos possuem respostas previsíveis.

**Verificações:**
- Teste do health check.
- Teste de configuração inválida.
- Teste de abertura e encerramento de sessão.
- Verificação de que secrets não aparecem em logs.

**Riscos:**
- Misturar configuração de teste com configuração de produção.
- Criar camadas excessivas antes do primeiro fluxo real.
- Permitir que erros de banco vazem detalhes sensíveis.

**Checkpoint sugerido:** commit da fundação do backend.

## Fase 3 — Modelo de dados

**Objetivo:** criar o modelo relacional mínimo da V1 com integridade, nulabilidade e histórico de preço corretos.

**Ordem segura de criação:**
1. clientes
2. fornecedores
3. funcionarios
4. produtos
5. vendas
6. venda_itens

**Tarefas:**
1. Criar os modelos SQLAlchemy das seis entidades.
2. Usar IDs gerados pelo sistema.
3. Marcar como não nulos todos os campos obrigatórios.
4. Permitir NULL apenas em:
   - clientes.complemento;
   - fornecedores.complemento;
   - funcionarios.complemento;
   - funcionarios.rg.
5. Definir CPF e CNPJ como strings com unicidade.
6. Definir RG como string opcional.
7. Definir estado como texto curto.
8. Definir número do endereço de forma compatível com valores como 10A e S/N.
9. Usar tipos decimais apropriados para preços.
10. Usar tipo de data para nascimento.
11. Usar tipo apropriado de data e hora para data_venda.
12. Aplicar foreign keys explícitas:
    - produtos.fornecedor_id;
    - vendas.cliente_id;
    - vendas.funcionario_id;
    - venda_itens.venda_id;
    - venda_itens.produto_id.
13. Criar constraints para quantidade maior que zero.
14. Criar constraints para preços não negativos.
15. Não usar ON DELETE CASCADE para Cliente, Funcionário, Produto ou Fornecedor; a exclusão de Venda será explícita e restrita aos seus próprios itens.
16. Criar migrations em ordem dependente, preferencialmente por blocos revisáveis:
    - tabelas de cadastros;
    - produtos;
    - vendas e itens.

**Dependências:** Fase 2.

**Critérios de conclusão:**
- O banco representa exatamente as entidades da V1.
- Todas as foreign keys e constraints estão explícitas.
- Vendas podem conter múltiplos itens.
- O nome do produto não é duplicado em venda_itens.
- O preço histórico é armazenado somente em venda_itens.preco_unitario.
- Não existem valor_total persistidos na V1.

**Verificações:**
- Aplicação das migrations em banco vazio.
- Inspeção das constraints e índices.
- Tentativa de inserir campos obrigatórios como NULL.
- Tentativa de inserir CPF ou CNPJ duplicado.
- Tentativa de inserir preço negativo ou quantidade inválida.
- Tentativa de excluir registros referenciados.

**Riscos:**
- Escolher float para valores monetários.
- Tornar RG obrigatório por engano.
- Usar cascatas destrutivas.
- Criar campos adicionais não aprovados.
- Fazer a venda depender do preço atual do produto após sua criação.

**Checkpoint sugerido:** commit das migrations e modelos da V1.

**Revisão Architect/Reviewer recomendada:** antes de aplicar a primeira migration em ambiente compartilhado.

## Fase 4 — Contratos e CRUD do backend

**Objetivo:** disponibilizar os cadastros básicos com contratos explícitos e regras de integridade.

**Entidades:**
- Clientes.
- Fornecedores.
- Funcionários.
- Produtos.

**Tarefas:**
1. Criar schemas Pydantic de criação, atualização e leitura.
2. Representar corretamente campos obrigatórios e opcionais.
3. Criar endpoints de listar, criar, visualizar, editar e excluir.
4. Organizar rotas por recurso, por exemplo:
   - /api/customers;
   - /api/suppliers;
   - /api/employees;
   - /api/products.
5. Garantir validação de preços, documentos e campos obrigatórios.
6. Garantir que IDs não sejam aceitos como entrada manual na criação.
7. Retornar 404 para registros inexistentes.
8. Retornar conflito claro quando exclusão violar integridade referencial.
9. Não excluir silenciosamente vendas a partir de cadastros raiz; a Venda somente é removida por ação explícita do usuário.
10. Manter respostas e erros consistentes entre os recursos.
11. Adicionar testes de unidade e integração por recurso.

**Dependências:** Fases 2 e 3.

**Critérios de conclusão:**
- Cada cadastro possui CRUD funcional.
- Os schemas não permitem violar as regras do modelo.
- Exclusões respeitam as foreign keys.
- O backend não expõe detalhes internos de SQLAlchemy ou PostgreSQL.
- A documentação automática da API reflete os contratos implementados.

**Verificações:**
- Testes de criação válida e inválida.
- Testes de atualização.
- Testes de consulta individual e listagem.
- Testes de registro inexistente.
- Testes de CPF/CNPJ duplicados.
- Testes de exclusão de registros referenciados.

**Riscos:**
- Criar CRUD genérico difícil de adaptar.
- Permitir alteração indevida de IDs.
- Aceitar preço histórico pelo cliente.
- Retornar 500 para conflitos que deveriam ser respostas controladas.

**Checkpoint sugerido:** um commit por grupo de cadastro ou um commit único de CRUD, se a revisão permanecer simples.

## Fase 5 — Fluxo de vendas

**Objetivo:** implementar o fluxo transacional de criação e consulta de vendas com múltiplos itens.

**Tarefas:**
1. Definir o contrato de criação de venda com cliente, funcionário, data da venda e lista de itens.
2. Representar cada item com produto e quantidade.
3. Não aceitar preco_unitario como preço confiável enviado pelo frontend.
4. Validar cliente e funcionário antes de criar a venda.
5. Validar cada produto informado.
6. Consultar o preco_venda atual de cada produto no backend.
7. Persistir esse valor em venda_itens.preco_unitario.
8. Criar a venda e seus itens dentro de uma única transação.
9. Permitir múltiplos produtos na mesma venda.
10. Calcular o subtotal de cada item de forma derivada.
11. Calcular o total da venda pela soma dos itens.
12. Não persistir valor_total na venda ou nos itens.
13. Criar consulta detalhada e listagem de vendas.
14. Retornar os dados necessários para exibir produto, preço unitário, quantidade e totais derivados.
15. Tratar falhas de validação sem deixar venda parcialmente gravada.
16. Definir comportamento claro para exclusão de produtos, clientes ou funcionários referenciados.
17. Permitir exclusão física explícita de uma venda por endpoint próprio, removendo na mesma transação somente seus VendaItens e a Venda.

**Dependências:** Fases 2, 3 e 4.

**Critérios de conclusão:**
- Uma venda possui cliente e funcionário.
- Uma venda pode conter vários produtos.
- O preço histórico é capturado exclusivamente pelo backend.
- Alterar o preço do produto não altera vendas existentes.
- Totais são calculados sem colunas redundantes.
- Falhas durante a operação fazem rollback completo.
- A exclusão explícita de uma Venda remove seus VendaItens e a própria Venda sem remover Cliente, Funcionário, Produto ou Fornecedor.
- `venda_id` permanece obrigatório e não existem VendaItens órfãos.

**Verificações:**
- Venda com um item.
- Venda com vários itens.
- Quantidade inválida.
- Produto inexistente.
- Cliente ou funcionário inexistente.
- Tentativa de manipular o preço enviado pelo cliente.
- Alteração posterior do preço do produto.
- Falha no meio da transação.
- Consulta dos totais derivados.
- Exclusão de uma venda com múltiplos itens e preservação dos cadastros raiz.
- Exclusão de uma venda inexistente retornando 404.

**Riscos:**
- Confiar no preço enviado pelo frontend.
- Gravar venda sem todos os itens.
- Persistir totais redundantes.
- Criar endpoint de desconto, pagamento ou estoque, que estão fora da V1.
- Permitir inconsistência em caso de erro transacional.

**Checkpoint sugerido:** commit do fluxo de vendas do backend.

**Revisão Architect/Reviewer recomendada:** antes de liberar o contrato de criação de venda para o frontend.

## Fase 6 — Fundação do frontend

**Objetivo:** estabelecer a base visual e de navegação sem implementar telas completas de negócio.

**Áreas prováveis:**
- frontend/src/
- Layout, navegação, cliente HTTP e componentes compartilhados.

**Tarefas:**
1. Organizar o frontend por features.
2. Criar estrutura inicial para customers, suppliers, employees, products e sales.
3. Criar layout administrativo.
4. Criar navegação para as áreas da V1.
5. Criar cliente HTTP usando a solução mínima necessária.
6. Centralizar tratamento de loading, erro e resposta HTTP.
7. Definir tipos TypeScript alinhados aos contratos da API.
8. Criar componentes compartilhados somente quando houver reutilização clara.
9. Definir tokens visuais para cores frias, espaçamento, cards e bordas arredondadas.
10. Garantir comportamento responsivo básico.
11. Não introduzir Redux, design system complexo ou abstrações globais prematuras.

**Dependências:** Fase 1 e contratos estáveis das Fases 4 e 5.

**Critérios de conclusão:**
- A aplicação possui layout e navegação funcional.
- As features estão separadas de forma compreensível.
- O cliente HTTP trata estados básicos.
- O frontend não possui acesso ao banco.
- O visual inicial segue as diretrizes aprovadas.

**Verificações:**
- Typecheck.
- Lint.
- Navegação entre áreas.
- Teste de loading, erro de API e resposta vazia.
- Verificação em larguras de tela principais.

**Riscos:**
- Criar componentes genéricos antes de conhecer os casos reais.
- Duplicar tipos ou contratos entre frontend e backend.
- Introduzir bibliotecas de UI ou gerenciamento de estado sem necessidade.

**Checkpoint sugerido:** commit da fundação visual e de navegação.

## Fase 7 — Telas de cadastro

**Objetivo:** implementar as operações administrativas dos quatro cadastros da V1.

**Tarefas comuns por módulo:**
1. Criar listagem.
2. Criar formulário de inclusão.
3. Criar visualização individual.
4. Criar edição.
5. Criar exclusão com confirmação.
6. Exibir mensagens de sucesso e erro.
7. Respeitar campos obrigatórios e opcionais.
8. Exibir conflitos de integridade de forma compreensível.

**Clientes:**
- Campos de endereço.
- Complemento opcional.
- Sem CPF, telefone, e-mail ou CEP.

**Fornecedores:**
- Campos de endereço.
- CNPJ obrigatório.
- Complemento opcional.
- Exibição de conflito de CNPJ duplicado.

**Funcionários:**
- CPF obrigatório.
- Data de nascimento obrigatória.
- RG opcional.
- Complemento opcional.
- Sem cargo ou data de admissão.

**Produtos:**
- Categoria como texto.
- Preço de custo e preço de venda.
- Seleção de fornecedor existente.
- Sem cadastro separado de categorias.
- Sem múltiplos fornecedores.

**Dependências:** Fases 4 e 6.

**Critérios de conclusão:**
- Cada módulo executa o CRUD previsto.
- Formulários impedem ausência de campos obrigatórios.
- Campos opcionais não são preenchidos artificialmente.
- Exclusões respeitam erros de integridade retornados pelo backend.
- Não aparecem campos fora do escopo.

**Verificações:**
- Testes de formulário.
- Testes de submissão válida e inválida.
- Testes de edição e exclusão.
- Testes de loading e erro.
- Testes responsivos básicos.
- Verificação de que RG e complemento podem permanecer ausentes.

**Riscos:**
- Transformar ausência em string vazia sem necessidade.
- Permitir alteração de identificadores.
- Criar tela de categorias cadastráveis.
- Esconder erros de unicidade ou integridade.

**Checkpoint sugerido:** um commit independente por módulo ou por grupo pequeno de módulos.

## Fase 8 — Interface de vendas

**Objetivo:** fornecer a criação e consulta operacional de vendas.

**Tarefas:**
1. Criar tela de Nova venda.
2. Permitir seleção de cliente.
3. Permitir seleção de funcionário.
4. Permitir inclusão de múltiplos produtos.
5. Permitir remoção de itens antes do envio.
6. Permitir ajuste de quantidade.
7. Exibir preço unitário retornado pelo backend.
8. Exibir subtotal e total derivados para o usuário.
9. Enviar apenas dados permitidos pelo contrato; o frontend não deve controlar o preço histórico.
10. Exibir erros de produto, cliente, funcionário e transação.
11. Criar Lista de vendas.
12. Exibir dados básicos da venda e seus itens.
13. Permitir consulta detalhada sem criar recursos de relatório avançado.
14. Permitir exclusão explícita de uma venda com confirmação clara, removendo também seus itens associados.

**Dependências:** Fases 5, 6 e 7.

**Critérios de conclusão:**
- É possível criar uma venda com um ou vários produtos.
- Cliente e funcionário são obrigatórios.
- Quantidade é validada.
- O preço persistido é sempre definido pelo backend.
- O total apresentado corresponde à soma dos itens.
- A lista de vendas mostra o histórico sem depender do preço atual do produto.
- É possível excluir uma venda com confirmação; seus itens são removidos e os cadastros raiz permanecem.

**Verificações:**
- Venda com um item.
- Venda com múltiplos itens.
- Inclusão e remoção de itens.
- Alteração de quantidade.
- Erro de API durante o envio.
- Tentativa de manipulação do preço no payload.
- Conferência do histórico após alteração de preço do produto.
- Confirmação, cancelamento e exclusão de venda com atualização imediata da lista.

**Riscos:**
- Recalcular ou substituir o preço histórico no frontend.
- Criar descontos, pagamentos, estoque ou caixa.
- Permitir submissão sem itens.
- Divergência entre totais exibidos e dados retornados pelo backend.

**Checkpoint sugerido:** commit da interface de vendas.

**Revisão Architect/Reviewer recomendada:** validação do fluxo ponta a ponta e da autoridade do backend sobre o preço.

## Fase 9 — Dashboard simples

**Objetivo:** oferecer uma visão inicial operacional sem transformar o dashboard em módulo analítico.

**Tarefas:**
1. Criar uma página inicial administrativa.
2. Exibir atalhos para Clientes, Produtos, Fornecedores, Funcionários e Vendas.
3. Exibir apenas informações básicas úteis para navegação e operação.
4. Caso sejam exibidas contagens, obtê-las de forma simples e consistente.
5. Evitar gráficos, tendências, metas, indicadores financeiros ou relatórios.
6. Garantir que a tela não crie novas entidades nem altere o escopo da V1.
7. Manter o mesmo padrão visual das demais telas.

**Dependências:** Fases 6, 7 e 8.

**Critérios de conclusão:**
- Dashboard serve como ponto de entrada da aplicação.
- Não possui funcionalidades analíticas avançadas.
- Não adiciona novas regras de domínio.
- Navegação para as áreas principais funciona.

**Verificações:**
- Renderização com banco vazio.
- Renderização com dados existentes.
- Estados de carregamento e erro.
- Teste de navegação.

**Riscos:**
- Evoluir para BI, relatórios ou dashboards analíticos.
- Criar endpoints complexos apenas para alimentar cards.
- Duplicar regras de consulta existentes.

**Checkpoint sugerido:** commit do dashboard básico.

## Fase 10 — Validação final da V1

**Status atual:** concluída.

A validação PostgreSQL final foi executada em banco dedicado com migration
aplicada e duas execuções consecutivas da suíte. Ambas terminaram com `57
passed` e `16 warnings`, sem falhas ou skips.

**Objetivo:** verificar que a aplicação está funcional, segura e coerente com o contexto aprovado.

**Tarefas:**
1. Executar testes backend unitários e de integração.
2. Executar testes frontend relevantes.
3. Executar lint.
4. Executar typecheck.
5. Executar build do frontend e validação de inicialização do backend.
6. Aplicar migrations em PostgreSQL limpo.
7. Validar constraints, índices e foreign keys.
8. Testar os CRUDs principais.
9. Executar o fluxo completo: criar cliente, funcionário, fornecedor, produto e venda com múltiplos itens, e consultar a venda.
10. Alterar o preço do produto e confirmar que a venda histórica permanece igual.
11. Testar exclusões de registros referenciados.
12. Revisar secrets, .env.example e .gitignore.
13. Verificar que CPF, RG e CNPJ não aparecem desnecessariamente em logs ou respostas.
14. Revisar que não existem funcionalidades fora do escopo.
15. Revisar o diff final e a documentação do estado implementado.

**Dependências:** Fases 1 a 9.

**Critérios de conclusão:**
- Testes principais passam, incluindo duas execuções consecutivas da suíte
  PostgreSQL após a última correção.
- Lint, typecheck e build passam.
- Migrations funcionam em banco limpo.
- Fluxo de venda funciona de ponta a ponta.
- Integridade referencial é preservada.
- Preço histórico é preservado.
- Nenhuma funcionalidade fora da V1 foi introduzida.
- O contexto/documentação reflete o estado real do código.

**Verificações:**
- Suíte backend.
- Suíte frontend.
- Testes manuais de fluxo.
- Revisão de segurança.
- Revisão independente do Reviewer.

**Riscos:**
- Validar apenas o caminho feliz.
- Ignorar falhas de transação.
- Aceitar divergência entre documentação e código.
- Liberar secrets ou dados sensíveis em logs.
- Deixar funcionalidades futuras entrarem por conveniência.

**Checkpoint sugerido:** commit de estabilização da V1, sem publicar ou fazer deploy automaticamente.

# Ordem recomendada

1. Bootstrap do monorepo.
2. Fundação do backend.
3. Modelos e migrations.
4. CRUD dos cadastros no backend.
5. Fluxo de vendas no backend.
6. Fundação do frontend.
7. Telas dos cadastros.
8. Interface de vendas.
9. Dashboard simples.
10. Validação final.

A ordem prioriza primeiro persistência e regras de negócio, depois contratos de API e, por fim, interface. Isso reduz o risco de construir telas sobre contratos instáveis.

# Pontos para revisão Architect/Reviewer

- Após a Fase 1: decisões de dependências, estrutura e configuração.
- Antes da primeira migration: tipos, nulabilidade, constraints, unicidade e foreign keys.
- Antes do CRUD: contratos HTTP/JSON, códigos de erro e comportamento de exclusão.
- Antes da interface de vendas: autoridade do backend sobre preco_unitario e atomicidade da transação.
- Antes da validação final: segurança, integridade referencial e ausência de funcionalidades fora da V1.

# Checkpoints de commits

Sugestão de commits independentes:

1. Bootstrap do monorepo.
2. Fundação do backend e health check.
3. Modelos e migrations dos cadastros.
4. Modelos e migrations de vendas.
5. CRUD de clientes e fornecedores.
6. CRUD de funcionários e produtos.
7. Fluxo de vendas do backend.
8. Fundação do frontend.
9. Telas de cadastros.
10. Interface de vendas.
11. Dashboard simples.
12. Testes e estabilização da V1.

Os commits são checkpoints sugeridos para revisão; não devem ser criados automaticamente sem solicitação explícita.

# Escopo preservado

Nenhuma funcionalidade fora da V1 foi adicionada ao plano. Permanecem fora do escopo:

- estoque;
- pagamentos;
- caixa;
- categorias cadastráveis;
- serviços;
- agenda;
- ordens de serviço;
- comissões;
- relatórios avançados;
- dashboards analíticos;
- importação/exportação;
- campos personalizados;
- schema configurável;
- integrações externas;
- telefone, e-mail e CEP;
- cargos e data de admissão;
- múltiplos fornecedores por produto.

Estado atual da implementação: as Fases 1 a 9 foram implementadas e a Fase 10
foi concluída após a validação PostgreSQL final. A V1 pode ser considerada
concluída dentro do escopo aprovado.
