import os
import sys
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from backend import oracle

class OracleTests(unittest.TestCase):
    def test_dates(self):
        a,b=oracle.validate_period({'mes_inicial':'2025-01','mes_final':'2025-02'})
        self.assertEqual(a,datetime(2025,1,1))
        for payload in [None,{}, {'mes_inicial':'2025-02','mes_final':'2025-01'},
                        {'mes_inicial':'2025-13','mes_final':'2025-13'},
                        {'mes_inicial':'2025-01','mes_final':'2999-01'},
                        {'mes_inicial':'2000-01','mes_final':'2025-01'},
                        {'mes_inicial':'2025-01','mes_final':'2025-01','sql':'DELETE'}]:
            with self.subTest(payload=payload),self.assertRaises(oracle.QueryError):
                oracle.validate_period(payload)

    def test_local_config_and_env_priority(self):
        from types import SimpleNamespace
        local=SimpleNamespace(db_host='test-host',db_port=1521,db_service_name='test-service',db_user='test-user',db_password='test-password')
        with patch.dict(os.environ,{},clear=True),patch('backend.oracle.Path.is_file',return_value=True),patch('backend.oracle.importlib.util.module_from_spec',return_value=local),patch('importlib.machinery.SourceFileLoader.exec_module'):
            self.assertEqual(oracle.configuration()['ORACLE_HOST'],'test-host')
            self.assertTrue(oracle.configuration_status()['configured'])
            with patch.dict(os.environ,{'ORACLE_HOST':'env-host'}):
                self.assertEqual(oracle.configuration()['ORACLE_HOST'],'env-host')

    def test_missing_configuration(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertFalse(oracle.configuration_status()['configured'])
            with self.assertRaises(oracle.QueryError) as e:
                oracle.query({'mes_inicial':'2025-01','mes_final':'2025-01'})
            self.assertEqual(e.exception.status,503)

    def test_fixed_readonly_query_and_serialization(self):
        driver=MagicMock();driver.Error=type('DriverError',(Exception,),{})
        connection=driver.connect.return_value.__enter__.return_value
        cursor=connection.cursor.return_value.__enter__.return_value
        cursor.description=[('DATA',),('VALOR',)]
        cursor.fetchmany.side_effect=[[(datetime(2025,1,1),Decimal('1043.76'))],[]]
        env={k:'test-value' for k in oracle.REQUIRED};env['ORACLE_PORT']='1521'
        with patch.dict(os.environ,env,clear=True),patch.dict(sys.modules,{'oracledb':driver}):
            result=oracle.query({'mes_inicial':'2025-01','mes_final':'2025-01'})
        self.assertEqual(result['rows'],[['2025-01-01T00:00:00','1043.76']])
        self.assertEqual(cursor.execute.call_args_list[0].args,('SET TRANSACTION READ ONLY',))
        self.assertEqual(cursor.execute.call_args_list[1].args,(oracle.QUERY,))
        self.assertEqual(cursor.execute.call_args_list[1].kwargs['mes_inicial'],datetime(2025,1,1))
        connection.rollback.assert_called_once()
        self.assertFalse(oracle.BUSY.locked())

    def test_driver_error_does_not_expose_credentials(self):
        driver=MagicMock();driver.Error=type('DriverError',(Exception,),{})
        driver.connect.side_effect=driver.Error('secret-password')
        with patch.dict(os.environ,{**{k:'test-value' for k in oracle.REQUIRED},'ORACLE_PORT':'1521'},clear=True),patch.dict(sys.modules,{'oracledb':driver}):
            with self.assertRaises(oracle.QueryError) as e:
                oracle.query({'mes_inicial':'2025-01','mes_final':'2025-01'})
            self.assertEqual(e.exception.status,502)
            self.assertNotIn('secret-password',str(e.exception))
        self.assertFalse(oracle.BUSY.locked())

if __name__=='__main__': unittest.main()
