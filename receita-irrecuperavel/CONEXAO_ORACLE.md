# Sistema local com Oracle

O painel agora tem duas fontes: importação Excel/CSV e consulta direta por API Python. A API executa somente a consulta fixa em `backend/consulta.sql`, com parâmetros de data. Nenhum SQL enviado pelo navegador é executado. O arquivo SQL avulso continua disponível para execução manual.

## Instalação

Na pasta do projeto, crie um ambiente Python 3.12 e instale:

```sh
python -m venv .venv
# Linux/macOS:
.venv/bin/python -m pip install -r requirements.txt
# Windows:
.venv\Scripts\python -m pip install -r requirements.txt
```

Preencha o arquivo `config_local.py` na raiz, no padrão:

```python
db_host = "aaaaaa"
db_port = "aaaaaa"
db_service_name = "aaaaaa"
db_user = "aaaaaa"
db_password = "aaaaaa"
```

Substitua os placeholders pelos dados reais na sua máquina. A porta pode ser string ou inteiro; normalmente é 1521. Esse arquivo é ignorado pelo Git e não é servido pela API. Não o compartilhe após preencher. `config_local.example.py` é o modelo sem credenciais. Reinicie o servidor após editar.

Opcionalmente, use variáveis do ambiente; elas têm prioridade sobre o arquivo:

| Nome | Uso |
| --- | --- |
| ORACLE_HOST | Host do banco |
| ORACLE_PORT | Porta, padrão 1521 |
| ORACLE_SERVICE_NAME | Nome do serviço Oracle |
| ORACLE_USER | Usuário com SELECT nas seis tabelas AJURI da consulta |
| ORACLE_PASSWORD | Senha, definida no ambiente do processo |

O sistema não carrega `.env` automaticamente. Não envie senha no chat nem a salve em planilhas. Use configuração de ambiente do sistema ou entrada local protegida para definir a senha. A senha não aparece no endpoint de status. Não registre o arquivo de configuração preenchido em controle de versão. O driver usa modo Thin; SID, wallet, TCPS e modo Thick precisam de configuração adicional conforme a infraestrutura e ainda não foram implementados.

Execute a partir da pasta do projeto:

```sh
# Linux/macOS:
.venv/bin/python painel/app.py
# Windows:
.venv\Scripts\python painel\app.py
```

Use o navegador no endereço local de loopback, porta 8001. Se o servidor antigo estiver nessa porta, encerre somente aquele processo e reinicie esta versão. Abrir apenas o HTML mantém a importação de arquivos, mas não habilita a API.

## Operação

Selecione mês inicial e final em Consultar Oracle e clique em Consultar período. Somente meses encerrados são aceitos. A configuração pode ser verificada sem estabelecer conexão. Uma consulta concluída é o teste de acesso efetivo.

Por enquanto, consultas são manuais: não há agendamento, cache nem histórico persistido. Cada consulta recalcula os fechamentos com a informação atual disponível no banco. O período máximo por requisição é 120 meses; resultados acima de 100 mil linhas são rejeitados integralmente. Consultas são serializadas para evitar sobrecarga local. Há tempo limite de conexão de 10 segundos e de 120 segundos por chamada Oracle (não é um limite total da consulta). As fórmulas de negócio são as mesmas do SQL fornecido, que ainda precisa ser validado no Oracle de destino.

É aberta uma transação somente leitura. Recomenda-se usuário do banco com permissões somente SELECT. O servidor fica limitado ao loopback; este protótipo não possui autenticação para publicação e não deve ser exposto na rede sem uma etapa específica de implantação. Acesso de rede/VPN deve existir na máquina que executa o Python.

O arquivo local contém apenas os placeholders solicitados; credenciais reais não foram configuradas. Conectividade, compatibilidade com a versão do Oracle, privilégios e desempenho real permanecem pendentes de validação.
