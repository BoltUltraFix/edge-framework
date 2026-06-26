"""
EdgeFramework CLI
Uso: python -m edge_framework.cli start --config mi_config.yaml
"""

import argparse
import sys
import logging


def main():
    parser = argparse.ArgumentParser(
        description='EdgeFramework — Infraestructura de trading algorítmico'
    )
    subparsers = parser.add_subparsers(dest='command')

    # Comando start
    start_parser = subparsers.add_parser('start', help='Arrancar el framework')
    start_parser.add_argument('--config', default='config.yaml', help='Ruta al config YAML')
    start_parser.add_argument('--strategy', help='Módulo de estrategia (opcional)')

    # Comando status
    subparsers.add_parser('status', help='Ver estado del framework')

    # Comando version
    subparsers.add_parser('version', help='Ver versión')

    args = parser.parse_args()

    if args.command == 'version':
        from edge_framework import __version__
        print(f'EdgeFramework v{__version__}')

    elif args.command == 'status':
        print('EdgeFramework — Estado: OK')
        print('Usa --config para especificar tu configuración')

    elif args.command == 'start':
        from edge_framework import ExecutionEngine
        logging.basicConfig(level=logging.INFO)
        engine = ExecutionEngine(config=args.config)
        if args.strategy:
            import importlib
            mod = importlib.import_module(args.strategy)
            if hasattr(mod, 'strategy'):
                engine.add_strategy(mod.strategy)
        engine.start_from_config()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()