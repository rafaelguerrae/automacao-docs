# Automação de Documentos InDesign (IDML)

Este projeto permite gerar automaticamente documentos InDesign no formato IDML a partir de dados JSON estruturados, criando **conteúdo visível** que aparece corretamente quando aberto no Adobe InDesign.

## Funcionalidades

- **Geração de conteúdo visível** - Texto aparece no InDesign
- **Sistema de posicionamento corrigido** - TextFrames posicionados corretamente
- **Estrutura JSON simplificada** - Foco em páginas/seções com title/texto
- **Manipulação direta de IDML** - Stories injetadas corretamente
- **CLI com múltiplos exemplos** - Teste com 1, 2 ou 3 páginas
- **Posicionamento dinâmico** - Baseado em análise de estrutura fixa

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

### Estrutura JSON Atualizada (Versão Atual)

```json
{
    "pages": [
        {
            "sections": [
                {
                    "title": "CARACTERÍSTICAS TÉCNICAS",
                    "text": "O ET3200 é um multímetro digital de alta precisão..."
                },
                {
                    "title": "ESPECIFICAÇÕES",
                    "text": "Tensão: 24V DC ±10%, Corrente: 0-10A, Precisão: ±0.1%"
                }
            ]
        }
    ]
}
```

### Uso Básico

```python
from src.idml_generator import EnhancedIDMLGenerator
import json

# Carregar dados JSON
with open('examples/onePage.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)

# Gerar IDML
generator = EnhancedIDMLGenerator()
generator.generate_file(dados, "meu-documento")
```

### Executar Exemplos

```bash
cd src

# Gerar documento com 1 página
python idml_generator.py -one

# Gerar documento com 2 páginas  
python idml_generator.py -two

# Gerar documento com 3 páginas
python idml_generator.py -three
```

### Exemplos Disponíveis

- **onePage.json** - Documento com 1 página e 5 seções
- **twoPages.json** - Documento com 2 páginas (5 + 6 seções)
- **threePages.json** - Documento com 3 páginas (5 + 6 + 6 seções)

## 🎯 Como Funciona (Técnico)

### 1. Processamento JSON → Stories
```python
# Converte cada seção em uma Story com conteúdo real
story_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
    <Story Self="{story_id}">
        <StoryPreference OpticalMarginAlignment="false"/>
        <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/$ID/NormalParagraphStyle">
            <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">
                <Content>{escaped_text}</Content>
            </CharacterStyleRange>
        </ParagraphStyleRange>
    </Story>
</idPkg:Story>'''
```

### 2. Geração Dinâmica de Spreads
- **Spread 1**: Página 1 apenas (página única)
- **Spread 2+**: Páginas 2-3, 4-5, etc. (páginas duplas)
- Cálculo automático de posições baseado em estrutura fixa
- Registra spreads no `designmap.xml`

### 3. Sistema de Posicionamento Baseado em Análise Fixa
```python
# Posições X por página (baseado em análise de estrutura fixa)
if page_num == 1:
    frame_x = 297.6377952754998
elif page_num == 2:
    frame_x = -297.6377952754999  # Página esquerda
elif page_num == 3:
    frame_x = 290.125984251878   # Página direita

# Posições Y específicas por página e seção
page_1_positions = [-274.99, -158.77, -42.55, 73.66, 189.88]
```

## 🔍 Arquitetura da Solução

### Problemas Resolvidos
1. **❌ Problema Original**: Posicionamento incorreto de TextFrames
   - **✅ Solução**: Análise de estrutura fixa para posicionamento exato

2. **❌ Geração de Spreads**: Spreads não seguiam padrão correto
   - **✅ Solução**: Spread 1 = página única, Spread 2+ = páginas duplas

3. **❌ Caracteres Portugueses**: Acentos e símbolos não funcionavam
   - **✅ Solução**: Escape XML adequado + encoding UTF-8

4. **❌ CLI Limitado**: Apenas um exemplo de teste
   - **✅ Solução**: CLI com -one, -two, -three para diferentes cenários

### Fluxo de Processamento
```
JSON Input → Stories Creation → Dynamic Spreads → TextFrame Positioning
     ↓              ↓                ↓                    ↓      
  Parsing      Content Tags     Spread Generation    Fixed Coordinates   
```

## 🚀 Próximos Passos Possíveis

### Imediato
- 🎨 **Estilos personalizados** por tipo de seção
- 📏 **Ajuste automático** de altura baseado no conteúdo
- 🖼️ **Suporte a imagens** nas seções
- 📄 **Mais exemplos** com 4+ páginas
- 🔧 **Configuração de layout** via JSON (margens, espaçamento)

### Recursos Avançados
- 📊 **Templates múltiplos** para diferentes tipos de documento
- 🎯 **Posicionamento automático** baseado em conteúdo
- 📱 **Geração responsiva** para diferentes tamanhos de página