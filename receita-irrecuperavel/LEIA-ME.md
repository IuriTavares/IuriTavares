# Receita irrecuperável — janela de 49 a 60 meses

## Regra vigente

A receita irrecuperável é o saldo pendente de faturas com vencimento do **49º ao 60º mês anterior** ao mês de fechamento, dividido pelo faturamento dessa mesma janela de 12 meses. Em janeiro/2025, os vencimentos são de **janeiro a dezembro/2020**, e o corte inclui pagamentos até o final de 31/01/2025. A janela anterior (50–61) foi substituída; não renomeie resultados antigos para reutilizá-los.

As demais visões são pontuais: 1M, 3M, 6M, 12M e 60M. Todas usam a data efetiva de quitação integral para reconstruir o saldo no fechamento. A implementação segue a regra de negócio informada; a referência regulatória não foi fornecida.

## Arquivos

- `inadimplencia_historica.sql`: SQL completo para rodar manualmente no Oracle. Edite as duas datas do CTE `entrada`.
- `backend/consulta.sql`: mesma regra, com parâmetros enviados pelo sistema.
- `painel/index.html`: painel independente, com leitor de Excel incorporado. Pode ser aberto sozinho para importar Excel/CSV e exportar relatórios Excel.
- `painel/app.py` e `backend/oracle.py`: servidor local e conexão Oracle.
- `config_local.example.py`: modelo dos cinco parâmetros `db_host`, `db_port`, `db_service_name`, `db_user`, `db_password`.
- `iniciar_windows.cmd`: preparação e inicialização no Windows.
- `CONEXAO_ORACLE.md`: detalhes da conexão e limites atuais.

## Windows

Extraia o pacote inteiro em uma pasta. Instale Python 3.12 ou superior, se necessário. Dê dois cliques em `iniciar_windows.cmd`; na primeira execução é necessário acesso à internet para instalar o driver. Mantenha a janela aberta e abra o navegador no endereço local de loopback na porta 8001. A importação de Excel/CSV funciona sem credenciais. Para consultar Oracle, preencha `config_local.py` na sua máquina e reinicie o servidor.

O arquivo de configuração contém apenas placeholders na distribuição e é ignorado pelo Git. Não compartilhe a cópia preenchida. Este sistema ainda é local, sem autenticação para publicação na rede.

## Relatório

A visão inicial é **49–60M**. O painel mostra explicitamente fechamento e janela de vencimentos. A ausência de registros é diferente de saldo zero. O botão **Exportar relatório Excel** cria cinco abas: parâmetros, resumo das seis visões no fechamento escolhido, evolução de todos os fechamentos carregados, detalhamento da visão escolhida e base com os recortes aplicados. A planilha exportada é uma fotografia, sem conexão externa embutida.

A amostra fornecida pelo usuário era apenas de teste e usava a janela antiga. Ela não foi incluída como dado de produção nem convertida por troca de rótulo. Execute o SQL corrigido para obter uma nova extração.

## Validação e pendências

A lógica de limites de janela, a validação de parâmetros da API e os fluxos de importação e exportação são testados localmente. O SQL não foi executado no Oracle de destino. São pendentes conectividade, permissões, compatibilidade, desempenho e conferência com dados reais. O inicializador Windows foi preparado, mas não executado no Windows neste ambiente Linux. SID, wallet e TCPS exigem adaptação conforme a infraestrutura.
