# Suporte e diagnóstico — ERP Geral

Ao receber um problema, registre versão do produto, horário, rota afetada,
passos para reproduzir e a saída sanitizada de `scripts/diagnostic.ps1`. Nunca
solicite ou compartilhe `.env`, senhas, tokens, dumps com dados reais ou logs
contendo informações pessoais.

Triagem mínima:

1. verifique o navegador e a URL pública;
2. consulte `/api/health`;
3. confirme `database` e `schema`;
4. compare `current_migration` com `expected_migration`;
5. consulte logs do processo (`journalctl` no Linux ou o terminal do serviço no
   Windows);
6. reproduza uma leitura simples antes de tentar uma mutação;
7. faça backup antes de qualquer restore ou atualização.

Quando a API estiver offline, o problema é de processo, proxy ou rede; quando
`database=offline`, investigue PostgreSQL e `DATABASE_URL`; quando
`schema=outdated`, aplique as migrations da versão com o procedimento de
update. Não resolva esses estados desativando autenticação.
