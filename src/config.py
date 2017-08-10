#!/usr/bin/python3
"""
grblCommander - config
========================
grblCommander configuration loader
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

try:
  from .cfg.user import cfg as user
  cfg = user
  loadedCfg = 'cfg.user'
except:
  from .cfg.default import cfg as default
  cfg = default
  loadedCfg = 'cfg.default'
