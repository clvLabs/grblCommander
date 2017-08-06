#!/usr/bin/python3
"""
grblCommander - config
========================
grblCommander configuration loader
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

try:
  from src.config_default import cfg as default
  cfg = default
except:
  from src.config_user import cfg as user
  cfg = user
