# Primeiro acesso — ERP Geral

## Caminho oficial

1. Preencha o `.env` com o PostgreSQL e um `AUTH_BOOTSTRAP_TOKEN` exclusivo.
2. Execute as migrations e suba o backend.
3. Abra o frontend e acesse `/setup`.
4. Crie o primeiro administrador usando uma senha com pelo menos 12
   caracteres e o token do `.env`.
5. No Dashboard, siga os atalhos **Configurar aparência** e **Revisar
   módulos**.
6. Confira o depósito principal, unidades de medida, condições de pagamento e
   categorias antes da primeira venda ou compra.
7. Cadastre cliente, fornecedor e produto; então execute uma operação pequena
   de venda ou compra como smoke test.

O endpoint de status `GET /api/auth/bootstrap-status` informa somente se ainda
não existe usuário. Ele não revela token, e-mail, senha ou dados de configuração.
Depois que o primeiro usuário é criado, o bootstrap retorna conflito e não pode
ser repetido.

## Instalação vazia

As migrations criam os cadastros de apoio da operação, como unidades de medida,
contas financeiras, módulos e depósito padrão, quando essa referência faz parte
do baseline. O operador deve revisar os valores na interface antes de usá-los
como padrão do cliente.

Se a instalação não puder acessar o backend, a tela deve informar a
indisponibilidade; corrija `/api/health` antes de repetir a configuração. Não
desative autenticação para contornar o bootstrap em produção.
