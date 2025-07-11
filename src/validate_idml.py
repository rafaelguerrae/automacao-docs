#!/usr/bin/env python3
"""
Script para validar e examinar o conteúdo de arquivos IDML.
"""
import zipfile
import os
import sys
from pathlib import Path


def validate_idml(arquivo_idml: str):
    """
    Valida um arquivo IDML e exibe sua estrutura.
    
    Args:
        arquivo_idml: Caminho para o arquivo IDML
    """
    if not os.path.exists(arquivo_idml):
        print(f"❌ Arquivo não encontrado: {arquivo_idml}")
        return False
    
    print(f"🔍 Validando arquivo IDML: {arquivo_idml}")
    print(f"📏 Tamanho: {os.path.getsize(arquivo_idml)} bytes")
    
    try:
        with zipfile.ZipFile(arquivo_idml, 'r') as zipf:
            # Listar conteúdo
            files = zipf.namelist()
            print(f"📁 Arquivos encontrados: {len(files)}")
            
            # Verificar estrutura básica
            required_files = [
                'mimetype',
                'META-INF/container.xml',
                'designmap.xml'
            ]
            
            print("\n✅ Estrutura básica:")
            for req_file in required_files:
                if req_file in files:
                    print(f"   ✓ {req_file}")
                else:
                    print(f"   ✗ {req_file} (AUSENTE)")
            
            # Verificar mimetype
            print("\n🔍 Validando mimetype:")
            try:
                mimetype_info = zipf.getinfo('mimetype')
                mimetype_content = zipf.read('mimetype').decode('utf-8')
                expected_mimetype = 'application/vnd.adobe.indesign-idml-package'
                
                print(f"   Conteúdo: '{mimetype_content}'")
                print(f"   Compressão: {mimetype_info.compress_type} (0=STORED, 8=DEFLATED)")
                
                if mimetype_content == expected_mimetype:
                    print("   ✓ Mimetype correto")
                else:
                    print(f"   ✗ Mimetype incorreto (esperado: {expected_mimetype})")
                    
                if mimetype_info.compress_type == 0:  # ZIP_STORED
                    print("   ✓ Mimetype sem compressão (correto)")
                else:
                    print("   ⚠️  Mimetype comprimido (pode causar problemas)")
                    
            except KeyError:
                print("   ✗ Arquivo mimetype não encontrado")
            
            # Examinar estrutura de diretórios
            print("\n📂 Estrutura de diretórios:")
            dirs = set()
            for file in files:
                if '/' in file:
                    dir_path = file.rsplit('/', 1)[0]
                    dirs.add(dir_path)
            
            for dir_name in sorted(dirs):
                print(f"   📁 {dir_name}/")
                dir_files = [f for f in files if f.startswith(dir_name + '/') and f.count('/') == dir_name.count('/') + 1]
                for file in sorted(dir_files):
                    size = zipf.getinfo(file).file_size
                    print(f"      📄 {os.path.basename(file)} ({size} bytes)")
            
            # Arquivos na raiz
            root_files = [f for f in files if '/' not in f]
            if root_files:
                print(f"   📁 / (raiz)")
                for file in sorted(root_files):
                    size = zipf.getinfo(file).file_size
                    print(f"      📄 {file} ({size} bytes)")
            
        print("\n✅ Validação concluída!")
        return True
        
    except zipfile.BadZipFile:
        print("❌ Arquivo não é um ZIP válido")
        return False
    except Exception as e:
        print(f"❌ Erro ao validar: {e}")
        return False


def extrair_idml(arquivo_idml: str, diretorio_saida: str = None):
    """
    Extrai o conteúdo de um arquivo IDML.
    
    Args:
        arquivo_idml: Caminho para o arquivo IDML
        diretorio_saida: Diretório onde extrair (opcional)
    """
    if not diretorio_saida:
        base_name = Path(arquivo_idml).stem
        diretorio_saida = f"{base_name}_extraido"
    
    print(f"📤 Extraindo {arquivo_idml} para {diretorio_saida}")
    
    try:
        os.makedirs(diretorio_saida, exist_ok=True)
        
        with zipfile.ZipFile(arquivo_idml, 'r') as zipf:
            zipf.extractall(diretorio_saida)
        
        print(f"✅ Conteúdo extraído em: {diretorio_saida}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao extrair: {e}")
        return False


def main():
    """Função principal."""
    if len(sys.argv) < 2:
        print("Uso: python validar_idml.py <arquivo.idml> [--extrair]")
        print("Exemplo: python validar_idml.py examples/documento_produto.idml")
        return 1
    
    arquivo_idml = sys.argv[1]
    extrair = '--extrair' in sys.argv
    
    # Validar arquivo
    if not validar_idml(arquivo_idml):
        return 1
    
    # Extrair se solicitado
    if extrair:
        print()
        extrair_idml(arquivo_idml)
    
    return 0


if __name__ == "__main__":
    exit(main()) 