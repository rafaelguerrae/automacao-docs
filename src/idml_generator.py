"""
Gerador de Documentos IDML usando SimpleIDML
Versão 2.1 - Atualizado para nova estrutura de páginas

Este módulo utiliza a biblioteca SimpleIDML para criar documentos Adobe InDesign
de forma mais robusta e confiável, focando na lógica de negócio em vez da 
estrutura técnica do IDML.

Mudanças na v2.1:
- Suporte para estrutura 'pages' com 'sections' 
- Saída simplificada: apenas arquivos .idml enumerados na pasta build/
- Cada página do JSON corresponde a uma página no InDesign
"""

import json
import os
from typing import Dict, List, Any
from simple_idml import idml
import tempfile
import shutil
import zipfile
from datetime import datetime


class IDMLGenerator:
    """
    Gerador de documentos IDML usando SimpleIDML como base.
    Foca na conversão de JSON com páginas para conteúdo InDesign.
    """
    
    def __init__(self):
        self.temp_dir = None
        self.base_idml_path = None
        self.output_counter = 1
    
    def _get_next_output_filename(self, base_name: str = "document") -> str:
        """
        Retorna o próximo nome de arquivo numerado para saída (document-1.idml, document-2.idml, etc.)
        """
        # Determine the build directory relative to project root
        if os.path.exists('../build'):
            build_dir = "../build"  # Running from src/
        elif os.path.exists('build'):
            build_dir = "build"     # Running from project root
        else:
            # Create build directory at project root level
            if os.path.exists('src'):  # We're at project root
                build_dir = "build"
            else:  # We're in src/
                build_dir = "../build"
        
        # Ensure build directory exists
        os.makedirs(build_dir, exist_ok=True)
        print(f"📁 Usando diretório build: {os.path.abspath(build_dir)}")
        
        while True:
            filename = f"{base_name}-{self.output_counter}.idml"
            file_path = os.path.join(build_dir, filename)
            
            if not os.path.exists(file_path):
                print(f"📄 Próximo arquivo: {file_path}")
                self.output_counter += 1
                return file_path
            
            self.output_counter += 1
    
    def _find_base_template(self) -> str:
        """
        Encontra o arquivo IDML base para usar como template.
        """
        # Procurar o arquivo template.idml no diretório template
        template_paths = [
            "../template/template.idml",  # De dentro do src/
            "template/template.idml",     # Da raiz do projeto
            "template.idml"               # Diretório atual
        ]
        
        for template_path in template_paths:
            if os.path.exists(template_path):
                print(f"✓ Usando template: {template_path}")
                return os.path.abspath(template_path)
        
        # Se não encontrar, listar onde procurou
        print("❌ Arquivo template.idml não encontrado em:")
        for path in template_paths:
            abs_path = os.path.abspath(path)
            exists = "✓" if os.path.exists(abs_path) else "✗"
            print(f"   {exists} {abs_path}")
        
        raise FileNotFoundError(
            "Para usar SimpleIDML, precisamos de um arquivo IDML base. "
            "Crie um arquivo vazio no InDesign e salve como template/template.idml"
        )
    
    def _process_pages_to_content(self, json_data: Dict[str, Any]) -> str:
        """
        Converte dados JSON com páginas em texto formatado simples para InDesign.
        Nova estrutura: pages -> sections com title e text.
        """
        content_parts = []
        
        if 'pages' in json_data:
            for page_num, page in enumerate(json_data['pages'], 1):
                content_parts.append(f"=== PÁGINA {page_num} ===\n\n")
                
                # Processar sections da página
                if 'sections' in page:
                    for i, section in enumerate(page['sections']):
                        # Adicionar título da seção
                        title = section.get('title', '')
                        if title:
                            content_parts.append(f"{title}\n\n")
                        
                        # Adicionar texto da seção
                        text = section.get('text', '')
                        if text:
                            content_parts.append(f"{text}\n\n")
                        
                        # Separador entre seções (exceto na última)
                        if i < len(page['sections']) - 1:
                            content_parts.append("---\n\n")
                
                # Separador entre páginas (exceto na última)
                if page_num < len(json_data['pages']):
                    content_parts.append("\n" + "="*50 + "\n\n")
        
        # Fallback para estrutura antiga (compatibilidade)
        elif 'sections' in json_data:
            for i, section in enumerate(json_data['sections']):
                title = section.get('title', '')
                if title:
                    content_parts.append(f"{title}\n\n")
                
                text = section.get('text', '')
                if text:
                    content_parts.append(f"{text}\n\n")
                
                if i < len(json_data['sections']) - 1:
                    content_parts.append("---\n\n")
        
        return "".join(content_parts)
    
    def _escape_xml_content(self, text: str) -> str:
        """
        Escapa caracteres especiais para XML, preservando encoding UTF-8.
        """
        # Não usar html.escape para preservar caracteres especiais portugueses
        # Apenas escapar os caracteres XML obrigatórios
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        
        # Remover caracteres de controle que podem causar problemas no XML
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        return text
    
    def _create_story_with_content(self, story_id: str, content_text: str, dom_version: str = "20.4") -> str:
        """
        Cria uma Story XML com conteúdo real que aparece no InDesign.
        """
        # Escapar o conteúdo para XML
        escaped_content = self._escape_xml_content(content_text)
        
        story_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="{dom_version}">
	<Story Self="{story_id}" AppliedTOCStyle="n" UserText="true" IsEndnoteStory="false" TrackChanges="false" StoryTitle="$ID/" AppliedNamedGrid="n">
		<StoryPreference OpticalMarginAlignment="false" OpticalMarginSize="12" FrameType="TextFrameType" StoryOrientation="Horizontal" StoryDirection="LeftToRightDirection" />
		<InCopyExportOption IncludeGraphicProxies="true" IncludeAllResources="false" />
		<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/$ID/NormalParagraphStyle">
			<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">
				<Content>{escaped_content}</Content>
			</CharacterStyleRange>
		</ParagraphStyleRange>
	</Story>
</idPkg:Story>'''
        
        return story_xml
    
    def _create_stories_from_pages(self, json_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Cria Stories a partir do JSON com estrutura de páginas.
        Cada página pode ter múltiplas seções, cada seção vira uma story.
        Retorna lista de dicionários com story_id, content_text, story_xml e metadados.
        """
        stories = []
        story_counter = 1
        
        if 'pages' in json_data:
            for page_num, page in enumerate(json_data['pages'], 1):
                if 'sections' in page:
                    for section_num, section in enumerate(page['sections'], 1):
                        # Gerar ID único para a story
                        story_id = f"story_p{page_num:02d}s{section_num:02d}"
                        
                        # Combinar título e texto
                        content_parts = []
                        title = section.get('title', '')
                        if title:
                            content_parts.append(title)
                        
                        text = section.get('text', '')
                        if text:
                            content_parts.append(text)
                        
                        content_text = '\n\n'.join(content_parts)
                        
                        # Criar XML da story
                        story_xml = self._create_story_with_content(story_id, content_text)
                        
                        stories.append({
                            'story_id': story_id,
                            'content_text': content_text,
                            'story_xml': story_xml,
                            'page_number': page_num,
                            'section_index': section_num - 1,
                            'title': title,
                            'text': text
                        })
                        
                        story_counter += 1
        
        # Fallback para estrutura antiga (compatibilidade)
        elif 'sections' in json_data:
            for i, section in enumerate(json_data['sections']):
                story_id = f"story_{i+1:03d}"
                
                content_parts = []
                title = section.get('title', '')
                if title:
                    content_parts.append(title)
                
                text = section.get('text', '')
                if text:
                    content_parts.append(text)
                
                content_text = '\n\n'.join(content_parts)
                story_xml = self._create_story_with_content(story_id, content_text)
                
                stories.append({
                    'story_id': story_id,
                    'content_text': content_text,
                    'story_xml': story_xml,
                    'page_number': 1,
                    'section_index': i,
                    'title': title,
                    'text': text
                })
        
        return stories
    
    def _inject_stories_directly(self, idml_path: str, stories: List[Dict[str, str]]) -> bool:
        """
        Injeta Stories diretamente no arquivo IDML manipulando o ZIP.
        Esta é a abordagem mais direta para garantir conteúdo visível.
        """
        try:
            import tempfile
            import shutil
            
            # Criar cópia temporária do IDML
            temp_dir = tempfile.mkdtemp()
            temp_idml_path = os.path.join(temp_dir, "temp.idml")
            shutil.copy2(idml_path, temp_idml_path)
            
            # Extrair o IDML
            extract_dir = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(temp_idml_path, 'r') as zipf:
                zipf.extractall(extract_dir)
            
            # Criar diretório Stories se não existir
            stories_dir = os.path.join(extract_dir, "Stories")
            os.makedirs(stories_dir, exist_ok=True)
            
            # Adicionar as stories
            for story_data in stories:
                story_id = story_data['story_id']
                story_xml = story_data['story_xml']
                
                story_filename = f"Story_{story_id}.xml"
                story_path = os.path.join(stories_dir, story_filename)
                
                with open(story_path, 'w', encoding='utf-8') as f:
                    f.write(story_xml)
                
                print(f"✓ Story criada: {story_filename}")
            
            # Atualizar o designmap.xml para registrar as novas stories
            if self._update_designmap_for_stories(extract_dir, stories):
                print("✓ designmap.xml atualizado com referências às stories")
            else:
                print("⚠️  Falha ao atualizar designmap.xml")
            
            # Atualizar spreads com TextFrames para exibir as stories
            if self._update_spreads_with_textframes(extract_dir, stories):
                print("✓ Spreads atualizados com TextFrames")
            else:
                print("⚠️  Falha ao atualizar spreads")
            
            # Recriar o arquivo IDML
            with zipfile.ZipFile(idml_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Adicionar mimetype sem compressão (obrigatório para IDML)
                mimetype_path = os.path.join(extract_dir, "mimetype")
                if os.path.exists(mimetype_path):
                    zipf.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
                
                # Adicionar todos os outros arquivos
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if file != "mimetype":  # Já adicionamos o mimetype
                            file_path = os.path.join(root, file)
                            arc_path = os.path.relpath(file_path, extract_dir)
                            zipf.write(file_path, arc_path)
            
            # Limpar arquivos temporários
            shutil.rmtree(temp_dir)
            
            print(f"✅ IDML atualizado com {len(stories)} stories")
            return True
            
        except Exception as e:
            print(f"❌ Erro na injeção direta: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _update_designmap_for_stories(self, extract_dir: str, stories: List[Dict[str, str]]) -> bool:
        """
        Atualiza o designmap.xml para incluir as novas stories.
        """
        try:
            designmap_path = os.path.join(extract_dir, "designmap.xml")
            if not os.path.exists(designmap_path):
                print("⚠️  designmap.xml não encontrado")
                return False
            
            # Ler o designmap atual
            with open(designmap_path, 'r', encoding='utf-8') as f:
                designmap_content = f.read()
            
            # Inserir referências às novas stories antes do fechamento do document
            story_refs = []
            for story_data in stories:
                story_id = story_data['story_id']
                story_filename = f"Story_{story_id}.xml"
                story_ref = f'\t\t<idPkg:Story src="Stories/{story_filename}" />'
                story_refs.append(story_ref)
            
            # Inserir as referências antes de </Document>
            if '</Document>' in designmap_content:
                insert_point = designmap_content.find('</Document>')
                new_content = (designmap_content[:insert_point] + 
                              '\n' + '\n'.join(story_refs) + '\n\t' +
                              designmap_content[insert_point:])
                
                with open(designmap_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("✓ designmap.xml atualizado")
                return True
            else:
                print("⚠️  Estrutura do designmap.xml não reconhecida")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao atualizar designmap: {e}")
            return False
    
    def _create_textframe_for_story(self, story_id: str, frame_id: str, x: float, y: float, width: float, height: float) -> str:
        """
        Cria um TextFrame XML que referencia uma Story específica com geometria correta.
        Baseado na análise do document-29-fixed.
        """
        # Calcular anchors baseados na largura real (para width=452, anchors=±226, mas vimos ±238 no fixed)
        # Usar os valores exatos do document-29-fixed para consistência
        anchor_width = 238  # Valor observado no document-29-fixed
        anchor_height = height / 2
        
        textframe_xml = f'''<TextFrame Self="{frame_id}" ParentStory="{story_id}" PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" ParentInterfaceChangeCount="" TargetInterfaceChangeCount="" LastUpdatedInterfaceChangeCount="" OverriddenPageItemProps="" HorizontalLayoutConstraints="FlexibleDimension FixedDimension FlexibleDimension" VerticalLayoutConstraints="FlexibleDimension FixedDimension FlexibleDimension" StrokeWeight="1" GradientFillStart="0 0" GradientFillLength="0" GradientFillAngle="0" GradientStrokeStart="0 0" GradientStrokeLength="0" GradientStrokeAngle="0" ItemLayer="uba" Locked="false" LocalDisplaySetting="Default" GradientFillHiliteLength="0" GradientFillHiliteAngle="0" GradientStrokeHiliteLength="0" GradientStrokeHiliteAngle="0" AppliedObjectStyle="ObjectStyle/$ID/[None]" Visible="true" Name="$ID/" ItemTransform="1 0 0 1 {x} {y}">
			<Properties>
				<PathGeometry>
					<GeometryPathType PathOpen="false">
						<PathPointArray>
							<PathPointType Anchor="-{anchor_width} -{anchor_height}" LeftDirection="-{anchor_width} -{anchor_height}" RightDirection="-{anchor_width} -{anchor_height}" />
							<PathPointType Anchor="-{anchor_width} {anchor_height}" LeftDirection="-{anchor_width} {anchor_height}" RightDirection="-{anchor_width} {anchor_height}" />
							<PathPointType Anchor="{anchor_width} {anchor_height}" LeftDirection="{anchor_width} {anchor_height}" RightDirection="{anchor_width} {anchor_height}" />
							<PathPointType Anchor="{anchor_width} -{anchor_height}" LeftDirection="{anchor_width} -{anchor_height}" RightDirection="{anchor_width} -{anchor_height}" />
						</PathPointArray>
					</GeometryPathType>
				</PathGeometry>
			</Properties>
			<TextFramePreference TextColumnCount="1" TextColumnFixedWidth="{width}" TextColumnMaxWidth="0">
				<Properties>
					<InsetSpacing type="list">
						<ListItem type="unit">12</ListItem>
						<ListItem type="unit">12</ListItem>
						<ListItem type="unit">12</ListItem>
						<ListItem type="unit">12</ListItem>
					</InsetSpacing>
				</Properties>
			</TextFramePreference>
			<TextWrapPreference Inverse="false" ApplyToMasterPageOnly="false" TextWrapSide="BothSides" TextWrapMode="None">
				<Properties>
					<TextWrapOffset Top="0" Left="0" Bottom="0" Right="0" />
				</Properties>
			</TextWrapPreference>
			<ObjectExportOption EpubType="$ID/" SizeType="DefaultSize" CustomSize="$ID/" PreserveAppearanceFromLayout="PreserveAppearanceDefault" AltTextSourceType="SourceXMLStructure" ActualTextSourceType="SourceXMLStructure" CustomAltText="$ID/" CustomActualText="$ID/" ApplyTagType="TagFromStructure" ImageConversionType="JPEG" ImageExportResolution="Ppi300" GIFOptionsPalette="AdaptivePalette" GIFOptionsInterlaced="true" JPEGOptionsQuality="High" JPEGOptionsFormat="BaselineEncoding" ImageAlignment="AlignLeft" ImageSpaceBefore="0" ImageSpaceAfter="0" UseImagePageBreak="false" ImagePageBreak="PageBreakBefore" CustomImageAlignment="false" SpaceUnit="CssPixel" CustomLayout="false" CustomLayoutType="AlignmentAndSpacing">
				<Properties>
					<AltMetadataProperty NamespacePrefix="$ID/" PropertyPath="$ID/" />
					<ActualMetadataProperty NamespacePrefix="$ID/" PropertyPath="$ID/" />
				</Properties>
			</ObjectExportOption>
		</TextFrame>'''
        
        return textframe_xml
    
    def _update_spreads_with_textframes(self, extract_dir: str, stories: List[Dict[str, str]]) -> bool:
        """
        Atualiza os spreads para incluir TextFrames distribuídos por páginas conforme JSON.
        """
        try:
            spreads_dir = os.path.join(extract_dir, "Spreads")
            if not os.path.exists(spreads_dir):
                print("⚠️  Diretório Spreads não encontrado")
                return False
            
            # Encontrar arquivos de spread
            spread_files = [f for f in os.listdir(spreads_dir) if f.endswith('.xml')]
            if not spread_files:
                print("⚠️  Nenhum arquivo de spread encontrado")
                return False
            
            # Organizar stories por página
            pages_stories = {}
            for story_data in stories:
                page_num = story_data['page_number']
                if page_num not in pages_stories:
                    pages_stories[page_num] = []
                pages_stories[page_num].append(story_data)
            
            print(f"📄 Distribuindo stories por {len(pages_stories)} páginas:")
            for page_num, page_stories in pages_stories.items():
                print(f"   Página {page_num}: {len(page_stories)} seções")
            
            # Configuração dos TextFrames (baseada na análise do document-29-fixed)
            frame_width = 452   # Largura correta (confirmada na versão fixed)
            frame_height = 120  # Altura adequada para o texto
            spacing_y = 140     # Espaçamento vertical entre frames
            
            # Coordenadas de referência baseadas na análise do document-29-fixed:
            # Page 1 (Name="1") fica à DIREITA: X = +297.6377952755
            # Page 2 (Name="2") fica à ESQUERDA: X = -297.6
            page1_x = 297.6377952755  # Página 1 fica à direita (spread Name="1")
            page2_x = -297.6          # Página 2 fica à esquerda (spread Name="2")  
            start_y = -320            # Posição Y inicial
            
            # Processar cada página usando o spread correto
            # IMPORTANTE: Mapeamento correto baseado na análise do document-29-fixed:
            # JSON Página 1 (5 seções) → InDesign Page Name="1" → Spread que contém Name="1"  
            # JSON Página 2 (1 seção) → InDesign Page Name="2" → Spread que contém Name="2"
            
            for page_num, page_stories in pages_stories.items():
                # Mapear JSON page para InDesign page name
                if page_num == 1:
                    # JSON página 1 deve ir para InDesign page Name="1"
                    target_page_name = "1"
                elif page_num == 2:
                    # JSON página 2 deve ir para InDesign page Name="2" 
                    target_page_name = "2"
                else:
                    # Para páginas adicionais, usar ordem sequencial
                    target_page_name = str(page_num)
                
                # Por simplicidade, mapear por ordem dos spreads (assumindo template de 2 páginas)
                if page_num == 1:
                    # JSON página 1 → spread[1] (segundo arquivo, contém Name="1")
                    spread_index = 1 if len(spread_files) > 1 else 0
                else:
                    # JSON página 2 → spread[0] (primeiro arquivo, contém Name="2")
                    spread_index = 0
                
                if spread_index >= len(spread_files):
                    print(f"⚠️  Não há spread suficiente para página {page_num}, usando último spread disponível")
                    spread_index = len(spread_files) - 1
                
                spread_file = spread_files[spread_index]
                spread_path = os.path.join(spreads_dir, spread_file)
                
                print(f"📄 JSON Página {page_num} → {spread_file} (InDesign Name=\"{target_page_name}\")")
                
                # Ler o spread atual
                with open(spread_path, 'r', encoding='utf-8') as f:
                    spread_content = f.read()
                
                # Criar TextFrames para as stories desta página
                textframes = []
                
                for i, story_data in enumerate(page_stories):
                    story_id = story_data['story_id']
                    frame_id = f"frame_{story_id}"
                    
                    # Posicionamento correto baseado na página JSON:
                    # JSON página 1 → InDesign página 1 (Name="1") → X positivo (direita)
                    # JSON página 2 → InDesign página 2 (Name="2") → X negativo (esquerda)
                    if page_num == 1:
                        transform_x = page1_x  # Página 1 fica à direita
                    else:
                        transform_x = page2_x  # Página 2 fica à esquerda
                    
                    transform_y = start_y + (i * spacing_y)
                    
                    # Ajustar altura do frame baseado no tamanho do conteúdo
                    content_length = len(story_data['content_text'])
                    if content_length > 200:
                        dynamic_height = min(200, frame_height + (content_length // 10))
                    else:
                        dynamic_height = frame_height
                    
                    textframe_xml = self._create_textframe_for_story(
                        story_id, frame_id, transform_x, transform_y, frame_width, dynamic_height
                    )
                    textframes.append(textframe_xml)
                    
                    print(f"✓ TextFrame criado para {story_id} (JSON Página {page_num}) em X={transform_x:.1f}, Y={transform_y:.1f}, H={dynamic_height}")
                
                # Inserir os TextFrames antes do fechamento do Spread
                if '</Spread>' in spread_content:
                    insert_point = spread_content.rfind('</Spread>')
                    new_content = (spread_content[:insert_point] + 
                                  '\n\t\t' + '\n\t\t'.join(textframes) + '\n\t' +
                                  spread_content[insert_point:])
                    
                    with open(spread_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                
                print(f"✅ {len(textframes)} TextFrames adicionados para página {page_num} no spread {spread_file}")
            
            total_frames = sum(len(page_stories) for page_stories in pages_stories.values())
            print(f"✅ Total: {total_frames} TextFrames distribuídos por páginas")
            return True
                
        except Exception as e:
            print(f"❌ Erro ao atualizar spreads: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def gerar_idml(self, json_data: Dict[str, Any], output_path: str) -> bool:
        """
        Gera um arquivo IDML a partir dos dados JSON usando SimpleIDML.
        
        Args:
            json_data: Dados do produto em formato JSON
            output_path: Caminho onde salvar o arquivo IDML gerado
            
        Returns:
            bool: True se gerado com sucesso, False caso contrário
        """
        try:
            # Encontrar template base
            base_template = self._find_base_template()
            
            # Use the output path directly since _get_next_output_filename already handles the correct path
            final_output_path = output_path
            
            # Ensure the output directory exists
            output_dir = os.path.dirname(os.path.abspath(final_output_path))
            os.makedirs(output_dir, exist_ok=True)
            print(f"📁 Diretório de saída: {output_dir}")
            print(f"📄 Arquivo final: {os.path.abspath(final_output_path)}")
            
            # Processar JSON para stories com conteúdo real
            stories = self._create_stories_from_pages(json_data)
            print(f"✓ Criadas {len(stories)} stories com conteúdo:")
            for story in stories:
                title_preview = story['title'][:30] + "..." if len(story['title']) > 30 else story['title']
                print(f"  Story: {story['story_id']} (Página {story['page_number']}) - {title_preview}")
            
            # Copiar o template diretamente (bypass SimpleIDML prefix que causa problemas)
            final_abs_path = os.path.abspath(final_output_path)
            final_dir = os.path.dirname(final_abs_path)
            os.makedirs(final_dir, exist_ok=True)
            
            # Copiar template diretamente
            shutil.copy2(base_template, final_abs_path)
            print(f"✓ Template copiado para: {final_abs_path}")
            
            # Injetar as stories com conteúdo real
            print("📝 Injetando stories com conteúdo visível...")
            if self._inject_stories_directly(final_abs_path, stories):
                print("✅ Stories injetadas com sucesso!")
            else:
                print("⚠️  Falha na injeção de stories, mas arquivo base criado")
            
            # Atualizar final_output_path para o caminho absoluto usado
            final_output_path = final_abs_path
            
            # Verificar se o arquivo foi criado
            if os.path.exists(final_output_path):
                file_size = os.path.getsize(final_output_path)
                print(f"✅ IDML gerado com sucesso: {final_output_path} ({file_size} bytes)")
                return True
            else:
                print(f"❌ Arquivo não foi criado: {final_output_path}")
                return False
            
        except FileNotFoundError as e:
            print(f"❌ Erro: {e}")
            return False
        except Exception as e:
            print(f"❌ Erro ao gerar IDML: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def gerar_idml_completo(self, json_data: Dict[str, Any], base_name: str = "document") -> bool:
        """
        Gera um arquivo IDML simples com nome enumerado na pasta build/.
        
        Args:
            json_data: Dados JSON das páginas e seções
            base_name: Nome base para o arquivo (document-1.idml, document-2.idml, etc.)
            
        Returns:
            bool: True se gerado com sucesso, False caso contrário
        """
        try:
            # 1. Obter próximo nome de arquivo numerado
            output_path = self._get_next_output_filename(base_name)
            
            # 2. Gerar o IDML
            print(f"🚀 Gerando IDML: {output_path}")
            success = self.gerar_idml(json_data, output_path)
            
            if not success:
                print("❌ Falha na geração do IDML")
                return False
            
            # Verificar se o arquivo foi realmente criado
            if not os.path.exists(output_path):
                print(f"❌ Arquivo IDML não foi criado: {output_path}")
                return False
            
            file_size = os.path.getsize(output_path)
            print(f"✅ IDML criado com sucesso: {file_size} bytes")
            print(f"📂 Localização: {os.path.abspath(output_path)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na geração: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def explorar_idml_existente(self, idml_path: str) -> Dict[str, Any]:
        """
        Explora a estrutura de um arquivo IDML existente para entender sua composição.
        Útil para depuração e aprendizado.
        """
        try:
            package = idml.IDMLPackage(idml_path)
            
            with package as p:
                info = {
                    'spreads': p.spreads if hasattr(p, 'spreads') else [],
                    'stories': p.stories if hasattr(p, 'stories') else [],
                    'pages': getattr(p, 'pages', []),
                    'font_families': [e.get("Name") for e in p.font_families] if hasattr(p, 'font_families') else [],
                    'xml_structure': p.xml_structure_pretty() if hasattr(p, 'xml_structure_pretty') else "N/A",
                    'export_xml': p.export_xml()[:200] + "..." if hasattr(p, 'export_xml') else "N/A"
                }
            
            return info
            
        except Exception as e:
            return {'error': str(e)}


def main():
    """Função principal para gerar IDML de exemplo com nova estrutura de páginas."""
    print("🚀 Iniciando geração de IDML com SimpleIDML...")
    print("📋 Nova estrutura: pages -> sections com title e text")
    
    # Verificar se arquivo JSON existe (procurar em vários locais)
    json_paths = ["example.json", "src/example.json", "../src/example.json"]
    json_file = None
    
    for path in json_paths:
        if os.path.exists(path):
            json_file = path
            break
    
    if not json_file:
        print(f"❌ Arquivo example.json não encontrado em:")
        for path in json_paths:
            print(f"   - {path}")
        return 1
    
    print(f"✓ Arquivo encontrado: {json_file}")
    
    # Carregar dados JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar JSON: {e}")
        return 1
    
    # Validar estrutura JSON
    if 'pages' not in json_data:
        print("❌ JSON deve conter uma chave 'pages'")
        return 1
    
    pages = json_data['pages']
    print(f"📊 Processando {len(pages)} páginas")
    
    # Contar total de seções
    total_sections = 0
    for page in pages:
        if 'sections' in page:
            total_sections += len(page['sections'])
    
    print(f"📄 Total de seções: {total_sections}")
    
    # Mostrar preview do conteúdo
    generator = IDMLGenerator()
    content_preview = generator._process_pages_to_content(json_data)
    print(f"📄 Preview do conteúdo ({len(content_preview)} caracteres):")
    print("=" * 50)
    print(content_preview[:300] + "..." if len(content_preview) > 300 else content_preview)
    print("=" * 50)
    
    # Gerar IDML usando o novo método simplificado
    print(f"\n🎯 Gerando IDML...")
    success = generator.gerar_idml_completo(json_data, "document")
    
    if success:
        print("\n✅ IDML gerado com sucesso!")
        print("📂 Arquivo criado na pasta build/")
        return 0
    else:
        print("❌ Falha ao gerar IDML")
        return 1


if __name__ == "__main__":
    exit(main()) 