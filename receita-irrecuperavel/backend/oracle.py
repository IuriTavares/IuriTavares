import os
import importlib.util
import re
import threading
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

QUERY = Path(__file__).with_name('consulta.sql').read_text().strip().rstrip(';')
REQUIRED = ('ORACLE_HOST', 'ORACLE_SERVICE_NAME', 'ORACLE_USER', 'ORACLE_PASSWORD')
BUSY = threading.Lock()

class QueryError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status

def configuration():
    config_path = Path(__file__).resolve().parent.parent / 'config_local.py'
    local = None
    if config_path.is_file():
        spec = importlib.util.spec_from_file_location('oracle_local_config', config_path)
        local = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(local)
    names = {'ORACLE_HOST':'db_host', 'ORACLE_PORT':'db_port',
             'ORACLE_SERVICE_NAME':'db_service_name', 'ORACLE_USER':'db_user',
             'ORACLE_PASSWORD':'db_password'}
    result = {}
    for env_name, local_name in names.items():
        value = os.environ.get(env_name)
        if value is None:
            value = getattr(local, local_name, '1521' if env_name=='ORACLE_PORT' else '')
        result[env_name] = str(value) if value is not None else ''
    return result

def configuration_status():
    config = configuration()
    missing = [key for key in REQUIRED if not config[key] or config[key]=='aaaaaa']
    try:
        valid_port = 1 <= int(config['ORACLE_PORT']) <= 65535
    except ValueError:
        valid_port = False
    if not valid_port:
        missing.append('ORACLE_PORT')
    return {'configured': not missing, 'missing': missing, 'connected': False,
            'message': 'Configuração não comprova conectividade.'}

def month(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}', value):
        raise QueryError('Informe os meses no formato AAAA-MM.')
    try:
        return datetime.strptime(value, '%Y-%m')
    except ValueError:
        raise QueryError('Mês inválido.') from None

def validate_period(payload):
    if not isinstance(payload, dict) or set(payload) != {'mes_inicial', 'mes_final'}:
        raise QueryError('Informe somente mes_inicial e mes_final.')
    start, end = month(payload['mes_inicial']), month(payload['mes_final'])
    if start > end:
        raise QueryError('O mês inicial deve preceder ou coincidir com o final.')
    if end.date() >= date.today().replace(day=1):
        raise QueryError('Selecione somente meses já encerrados.')
    if (end.year-start.year)*12+end.month-start.month >= 120:
        raise QueryError('Consulte até 120 fechamentos por vez.')
    return start, end

def json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value

def query(payload):
    start, end = validate_period(payload)
    if not configuration_status()['configured']:
        raise QueryError('Preencha config_local.py ou as variáveis Oracle no servidor antes de consultar.', 503)
    config = configuration()
    if not BUSY.acquire(blocking=False):
        raise QueryError('Já existe uma consulta em execução. Aguarde.', 409)
    try:
        try:
            import oracledb
        except ImportError:
            raise QueryError('Instale as dependências do servidor.', 503) from None
        try:
            port = int(config['ORACLE_PORT'])
            if not 1 <= port <= 65535:
                raise ValueError()
        except ValueError:
            raise QueryError('ORACLE_PORT deve ser uma porta válida.', 503) from None
        try:
            with oracledb.connect(user=config['ORACLE_USER'], password=config['ORACLE_PASSWORD'],
                                  host=config['ORACLE_HOST'], port=port,
                                  service_name=config['ORACLE_SERVICE_NAME'], tcp_connect_timeout=10) as connection:
                connection.call_timeout = 120000
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION READ ONLY')
                    cursor.arraysize = 1000
                    cursor.execute(QUERY, mes_inicial=start, mes_final=end)
                    columns = [c[0] for c in cursor.description]
                    output = []
                    while True:
                        batch = cursor.fetchmany(1000)
                        if not batch:
                            break
                        if len(output)+len(batch) > 100000:
                            raise QueryError('Resultado excede 100 mil linhas. Reduza o período; nenhum resultado parcial foi carregado.', 422)
                        output.extend([[json_value(v) for v in row] for row in batch])
                connection.rollback()
            return {'columns': columns, 'rows': output, 'row_count': len(output),
                    'mes_inicial': payload['mes_inicial'], 'mes_final': payload['mes_final']}
        except oracledb.Error:
            raise QueryError('Não foi possível concluir a consulta Oracle. Confira rede, credenciais, permissões e tempo de execução.', 502) from None
    finally:
        BUSY.release()
