"""Logging setup for {{cookiecutter.driver_name}}"""
import logging
from logging.handlers import RotatingFileHandler
import sys

log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
log_file = './{{cookiecutter.driver_name}}.log'
my_handler = RotatingFileHandler(log_file, mode='a', maxBytes=500*1024,
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)
filelogger = logging.getLogger('{{cookiecutter.driver_name}}')
filelogger.setLevel(logging.INFO)
filelogger.addHandler(my_handler)

console_out = logging.StreamHandler(sys.stdout)
console_out.setFormatter(log_formatter)
filelogger.addHandler(console_out)
