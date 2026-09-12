# Release e atualização — ERP Geral

## Fonte da versão

A versão do produto está em `backend/app/core/version.py` e deve ser atualizada
junto da seção correspondente em `CHANGELOG.md`. O endpoint público `/api/health`
expõe somente a versão e o estado técnico; `/api/system-info` exige a sessão do
usuário e retorna também ambiente e migrations aplicadas.

## Checklist de release

- [ ] atualizar versão e `CHANGELOG.md`;
- [ ] revisar migrations e baseline, quando houver alteração de schema;
- [ ] executar backend: typecheck equivalente, Ruff e pytest relevante;
- [ ] executar frontend: testes, typecheck e build;
- [ ] executar backup e confirmar que o arquivo pode ser lido;
- [ ] testar upgrade em instalação isolada;
- [ ] publicar o build e reiniciar o processo controladamente;
- [ ] validar `/api/health`, login e smoke de cliente, produto e operação;
- [ ] registrar riscos, incompatibilidades e procedimento de rollback;
- [ ] somente depois promover a versão ao cliente.

Não use o endpoint de diagnóstico para coletar secrets. O script
`scripts/diagnostic.ps1` imprime somente versões, migration e estados técnicos.
