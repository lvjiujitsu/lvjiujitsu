#!/usr/bin/env python
"""
Script temporário para substituir register.html com register_clean.html
"""
import shutil
from pathlib import Path

# Paths
templates_dir = Path(__file__).parent / 'templates' / 'login'
old_file = templates_dir / 'register.html'
new_file = templates_dir / 'register_clean.html'
backup_file = templates_dir / 'register_old_backup.html'

# Backup do arquivo original
if old_file.exists():
    shutil.copy2(old_file, backup_file)
    print(f'✓ Backup criado: {backup_file.name}')

# Substituir
if new_file.exists():
    shutil.copy2(new_file, old_file)
    print(f'✓ Arquivo substituído: {old_file.name}')
    print(f'✓ Novo template aplicado com sucesso!')
else:
    print(f'✗ Erro: {new_file.name} não encontrado')
    exit(1)

print('\n📝 Próximos passos:')
print('1. Atualize o navegador e teste o formulário de cadastro')
print('2. Verifique todos os fluxos: Aluno sem dependente, Aluno com dependente, Responsável, Outro')
print('3. Teste o botão "Descartar" para verificar se limpa tudo e volta ao step 1')
