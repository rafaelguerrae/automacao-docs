# Automação de Documentos InDesign (IDML)

Este projeto permite gerar automaticamente documentos InDesign no formato IDML a partir de dados JSON estruturados, criando **conteúdo visível** que aparece corretamente quando aberto no Adobe InDesign.

## Projeto


- **Geração de conteúdo visível** - Texto aparece no InDesign
- **Sistema de posicionamento corrigido** - TextFrames centralizados
- **Estrutura JSON simplificada** - Foco em title/texto
- **Manipulação direta de IDML** - Stories injetadas corretamente
- **Numeração automática** - Diretórios test-1, test-2, etc.

## Características Principais

- **Conteúdo Visível**: Gera arquivos IDML com texto que aparece no InDesign
- **Stories Reais**: Cria elementos `<Content>` com texto formatado
- **TextFrames Conectados**: Liga Stories a TextFrames para exibição
- **Posicionamento Inteligente**: Sistema de coordenadas corrigido
- **JSON Simplificado**: Estrutura intuitiva com seções title/texto
- **Análise Integrada**: Extrai IDML automaticamente para verificação

## Instalação

```bash
pip install -r src/requirements.txt
```

### Estrutura JSON Simplificada (Versão Atual)

```json
{
    "secoes": [
        {
            "title": "CARACTERÍSTICAS TÉCNICAS",
            "texto": "O ET3200 é um multímetro digital de alta precisão..."
        },
        {
            "title": "ESPECIFICAÇÕES",
            "texto": "Tensão: 24V DC ±10%, Corrente: 0-10A, Precisão: ±0.1%"
        }
    ]
}
```

### Uso Básico

```python
from src.idml_generator import IDMLGenerator
import json

# Carregar dados JSON
with open('src/example.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)

# Gerar IDML com análise automática
generator = IDMLGenerator()
generator.gerar_idml_completo(dados, base_name="meu-documento")
```

### Executar Exemplo Rápido

```bash
cd src
python idml_generator.py
```

## 🎯 Como Funciona (Técnico)

### 1. Processamento JSON → Stories
```python
# Converte cada seção em uma Story com conteúdo real
story_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
    <Story Self="{story_id}">
        <StoryPreference OpticalMarginAlignment="false"/>
        <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/$ID/[No paragraph style]">
            <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">
                <Content>{escaped_text}</Content>
            </CharacterStyleRange>
        </ParagraphStyleRange>
    </Story>
</idPkg:Story>'''
```

### 2. Injeção Direta no IDML
- Manipula arquivo ZIP diretamente
- Cria diretório `Stories/` se não existir
- Registra Stories no `designmap.xml`
- Atualiza spreads com TextFrames

### 3. Sistema de Posicionamento Corrigido
```python
center_x = -297.6  # Centro horizontal na spread
start_y = -350     # Posição inicial Y
transform_y = start_y + (i * 70)  # Distribuição vertical

# ItemTransform formato: "1 0 0 1 X Y"
textframe_xml = f'<TextFrame ItemTransform="1 0 0 1 {center_x} {transform_y}" ...>'
```

## 🔍 Arquitetura da Solução

### Problemas Resolvidos
1. **❌ Problema Original**: SimpleIDML `import_xml()` não criava conteúdo visível
   - **✅ Solução**: Manipulação direta de arquivos Story com tags `<Content>`

2. **❌ Posicionamento Incorreto**: TextFrames não apareciam centralizados
   - **✅ Solução**: Sistema de coordenadas baseado em exemplos funcionais

3. **❌ Caracteres Portugueses**: Acentos e símbolos não funcionavam
   - **✅ Solução**: Escape XML adequado + encoding UTF-8

4. **❌ Estrutura Complexa**: JSON original muito complexo
   - **✅ Solução**: JSON simplificado com title/texto

### Fluxo de Processamento
```
JSON Input → Stories Creation → IDML Injection → TextFrame Positioning
     ↓              ↓                ↓                    ↓      
  Parsing      Content Tags     ZIP Manipulation    Coordinate System   
```

## 🚀 Próximos Passos Possíveis

### Imediato
- 🎨 **Estilos personalizados** por tipo de seção
- 📏 **Ajuste automático** de altura baseado no conteúdo
- 🖼️ **Suporte a imagens** nas seções