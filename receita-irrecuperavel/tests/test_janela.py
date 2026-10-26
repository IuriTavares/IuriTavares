import re
import unittest
from pathlib import Path
from datetime import date

ROOT=Path(__file__).resolve().parents[1]

def shift(year,month,offset):
    number=year*12+month-1+offset
    return date(number//12,number%12+1,1)

class WindowTests(unittest.TestCase):
    def test_both_sql_files_use_correct_window(self):
        for name in ('inadimplencia_historica.sql','backend/consulta.sql'):
            with self.subTest(name=name):
                text=(ROOT/name).read_text()
                match=re.search(r"SELECT '49_60M', (\d+), (\d+)",text)
                self.assertIsNotNone(match)
                minimum,maximum=map(int,match.groups())
                self.assertEqual(maximum-minimum+1,12)
                self.assertEqual(shift(2025,1,-maximum),date(2020,1,1))
                self.assertEqual(shift(2025,1,1-minimum),date(2021,1,1))
                self.assertNotIn("'50_61M'",text)
                self.assertIn('b.dt_pagamento < j.corte_exclusivo',text)

if __name__=='__main__':unittest.main()
