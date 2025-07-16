import json
import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Tuple
import tempfile
import shutil
import zipfile
from datetime import datetime
import math
import re


class EnhancedIDMLGenerator:
    
    def __init__(self):
        self.temp_dir = None
        self.base_idml_path = None
        self.output_counter = 1
        
        # Layout configuration
        self.page_width = 595.2755905509999
        self.page_height = 841.889763778
        self.margin = 36
        
        # Text frame configuration
        self.frame_width = 508.25196850375585
        self.frame_height = 116.22047244018108
        self.frame_spacing_y = 140
        
        # Page positioning
        self.page1_x = 297.63779527549997
        self.page2_x = -297.63779527549997
        self.page1_y = -291.9685039373898
        self.page2_y = -306.14173228231886
        
        # ID generation counters
        self.spread_counter = 1
        self.story_counter = 1
        self.page_counter = 1
        
    def _generate_spread_id(self) -> str:
        if self.spread_counter == 1:
            return "ucf"
        elif self.spread_counter == 2:
            return "u109"
        else:
            # For additional spreads, generate similar IDs
            return f"u{100 + self.spread_counter:03d}"
    
    def _generate_story_id(self) -> str:
        if self.story_counter == 1:
            story_id = "ue5"
        elif self.story_counter == 2:
            story_id = "u112"
        else:
            story_id = f"u{100 + self.story_counter:03d}"
        
        return story_id
    
    def _generate_page_id(self) -> str:
        if self.page_counter == 1:
            return "ud4"
        elif self.page_counter == 2:
            return "u10e"
        else:
            # For additional pages, generate similar IDs
            return f"u{200 + self.page_counter:03d}"
    
    def _generate_textframe_id(self) -> str:
        if self.page_counter == 1:
            return "uf7"
        elif self.page_counter == 2:
            return "u10f"
        else:
            # For additional textframes, generate similar IDs
            return f"u{300 + self.page_counter:03d}"
    
    def _get_next_output_filename(self, base_name: str = "enhanced") -> str:
        """Get the next available output filename."""
        # Use the same logic as the original generator
        if os.path.exists('../build'):
            build_dir = "../build"
        elif os.path.exists('build'):
            build_dir = "build"
        else:
            if os.path.exists('src'):
                build_dir = "build"
            else:
                build_dir = "../build"
        
        os.makedirs(build_dir, exist_ok=True)
        
        while True:
            filename = f"{base_name}-{self.output_counter}.idml"
            file_path = os.path.join(build_dir, filename)
            
            if not os.path.exists(file_path):
                self.output_counter += 1
                return file_path
            
            self.output_counter += 1
    
    def _find_base_template(self) -> str:
        """Find the base template IDML file"""
        template_paths = [
            "../template/template.idml",
            "template/template.idml",
            "template.idml"
        ]
        
        for template_path in template_paths:
            if os.path.exists(template_path):
                return os.path.abspath(template_path)
        
        raise FileNotFoundError(
            "Arquivo IDML de template não encontrado."
        )

    """
        Calculate X,Y coordinates for any page number based on template.
        Uses exact coordinates from the template structure.
    """
    def _calculate_page_position(self, page_number: int) -> Tuple[float, float]:
        
        if page_number == 1:
            return self.page1_x, self.page1_y
        elif page_number == 2:
            return self.page2_x, self.page2_y
        else:
            # Calculate which spread this page belongs to
            spread_number = math.ceil(page_number / 2) - 1
            
            # Base positions for spreads beyond the template
            if page_number % 2 == 1:  # Odd page (right side)
                base_x = self.page1_x
                base_y = self.page1_y
            else:  # Even page (left side)
                base_x = self.page2_x
                base_y = self.page2_y
            
            # Add spread offset for additional spreads
            spread_offset_x = spread_number * (self.page_width + 50)  # 50pt gap
            spread_offset_y = spread_number * (self.page_height + 50)  # 50pt gap
            
            return base_x + spread_offset_x, base_y + spread_offset_y
    
    def _get_required_spreads(self, total_pages: int) -> int:
        """Calculate how many spreads are needed for the exact number of pages."""
        return math.ceil(total_pages / 2)
    
    def _create_spread_xml(self, spread_id: str, spread_index: int, pages_in_spread: List[int]) -> str:
        """
        Create proper XML for a new spread based on template structure.
        """
        # Use the template ItemTransform values for the spread
        if spread_index == 0:
            # First spread (like ucf)
            item_transform = "1 0 0 1 0 0"
        elif spread_index == 1:
            # Second spread (like u109)
            item_transform = "1 0 0 1 0 1021.8897637780001"
        else:
            # Additional spreads
            item_transform = f"1 0 0 1 0 {1021.8897637780001 * spread_index}"
        
        spread_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="20.4">
\t<Spread Self="{spread_id}" FlattenerOverride="Default" SpreadHidden="false" AllowPageShuffle="true" ItemTransform="{item_transform}" ShowMasterItems="true" PageCount="{len(pages_in_spread)}" BindingLocation="{0 if spread_index == 0 else 1}" PageTransitionType="None" PageTransitionDirection="NotApplicable" PageTransitionDuration="Medium">
\t\t<FlattenerPreference LineArtAndTextResolution="300" GradientAndMeshResolution="150" ClipComplexRegions="false" ConvertAllStrokesToOutlines="false" ConvertAllTextToOutlines="false">
\t\t\t<Properties>
\t\t\t\t<RasterVectorBalance type="double">50</RasterVectorBalance>
\t\t\t</Properties>
\t\t</FlattenerPreference>'''
        
        # Add each page to the spread
        for page_num in pages_in_spread:
            x_pos, y_pos = self._calculate_page_position(page_num)
            page_id = self._generate_page_id()
            self.page_counter += 1
            
            # Calculate ItemTransform for the page
            if page_num == 1:
                page_transform = "1 0 0 1 0 -420.944881889"
            elif page_num == 2:
                page_transform = "1 0 0 1 -595.2755905509999 -420.944881889"
            else:
                # For additional pages, use calculated positions
                page_transform = f"1 0 0 1 {x_pos} {y_pos}"
            
            page_xml = f'''
\t\t<Page Self="{page_id}" AppliedAlternateLayout="ud5" LayoutRule="{'UseMaster' if page_num == 1 else 'Off'}" SnapshotBlendingMode="IgnoreLayoutSnapshots" OptionalPage="false" GeometricBounds="0 0 {self.page_height} {self.page_width}" ItemTransform="{page_transform}" Name="{page_num}" AppliedTrapPreset="TrapPreset/$ID/kDefaultTrapStyleName" OverrideList="" AppliedMaster="ud6" MasterPageTransform="1 0 0 1 0 0" TabOrder="" GridStartingPoint="TopOutside" UseMasterGrid="true">
\t\t\t<Properties>
\t\t\t\t<Descriptor type="list">
\t\t\t\t\t<ListItem type="string"></ListItem>
\t\t\t\t\t<ListItem type="enumeration">Arabic</ListItem>
\t\t\t\t\t<ListItem type="boolean">true</ListItem>
\t\t\t\t\t<ListItem type="boolean">false</ListItem>
\t\t\t\t\t<ListItem type="long">{page_num}</ListItem>
\t\t\t\t\t<ListItem type="long">{page_num}</ListItem>
\t\t\t\t\t<ListItem type="string"></ListItem>
\t\t\t\t</Descriptor>
\t\t\t\t<PageColor type="enumeration">UseMasterColor</PageColor>
\t\t\t</Properties>
\t\t\t<MarginPreference ColumnCount="1" ColumnGutter="12" Top="36" Bottom="36" Left="36" Right="36" ColumnDirection="Horizontal" ColumnsPositions="0 523.275590551" />
\t\t\t<GridDataInformation FontStyle="Regular" PointSize="12" CharacterAki="0" LineAki="9" HorizontalScale="100" VerticalScale="100" LineAlignment="LeftOrTopLineJustify" GridAlignment="AlignEmCenter" CharacterAlignment="AlignEmCenter">
\t\t\t\t<Properties>
\t\t\t\t\t<AppliedFont type="string">Minion Pro</AppliedFont>
\t\t\t\t</Properties>
\t\t\t</GridDataInformation>
\t\t</Page>'''
            spread_xml += page_xml
        
        spread_xml += '''
\t</Spread>
</idPkg:Spread>'''
        
        return spread_xml
    """Update designmap.xml to replace all spread references with new ones."""
    def _update_designmap_for_new_spreads(self, extract_dir: str, new_spreads: List[str]) -> bool:
        
        try:
            designmap_path = os.path.join(extract_dir, "designmap.xml")
            
            if not os.path.exists(designmap_path):
                print("⚠️  designmap.xml não encontrado")
                return False
            
            # Read current designmap
            with open(designmap_path, 'r', encoding='utf-8') as f:
                designmap_content = f.read()
            
            # Remove all existing spread references
            spread_pattern = r'\s*<idPkg:Spread[^>]*src="Spreads/[^"]*"[^>]*/?>\s*'
            designmap_content = re.sub(spread_pattern, '', designmap_content)
            
            # Add new spread entries
            new_spread_entries = []
            for spread_file in new_spreads:
                spread_entry = f'\n\t<idPkg:Spread src="Spreads/{spread_file}" />'
                new_spread_entries.append(spread_entry)
            
            # Insert new entries before the closing tag
            if '</Document>' in designmap_content:
                insert_point = designmap_content.rfind('</Document>')
                new_content = (designmap_content[:insert_point] + 
                             ''.join(new_spread_entries) + '\n' +
                             designmap_content[insert_point:])
                
                with open(designmap_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                #print(f"✅ Updated designmap.xml with {len(new_spreads)} dynamic spread references")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error updating designmap: {e}")
            return False
    
    """Create stories from JSON pages - one story per SECTION, not per page."""
    def _create_stories_from_pages(self, json_data: Dict[str, Any]) -> List[Dict[str, str]]:
        stories = []
        
        if 'pages' in json_data:
            for page_num, page in enumerate(json_data['pages'], 1):
                if 'sections' in page:
                    # Create one story for EACH section
                    for section_idx, section in enumerate(page['sections']):
                        story_id = self._generate_story_id()
                        #print(f"🔍 Creating story {len(stories)+1}: {story_id} (counter={self.story_counter})")
                        self.story_counter += 1
                        
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
                            'page_number': page_num,
                            'section_index': section_idx,
                            'title': title,
                            'text': text
                        })
        
        #print(f"📊 Total stories created: {len(stories)}")
        return stories
    
    def _create_story_with_content(self, story_id: str, content_text: str) -> str:
        """Create Story XML with content based on template structure."""
        escaped_content = self._escape_xml_content(content_text)
        
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="20.4">
\t<Story Self="{story_id}" AppliedTOCStyle="n" UserText="true" IsEndnoteStory="false" TrackChanges="false" StoryTitle="$ID/" AppliedNamedGrid="n">
\t\t<StoryPreference OpticalMarginAlignment="false" OpticalMarginSize="12" FrameType="TextFrameType" StoryOrientation="Horizontal" StoryDirection="LeftToRightDirection" />
\t\t<InCopyExportOption IncludeGraphicProxies="true" IncludeAllResources="false" />
\t\t<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/$ID/NormalParagraphStyle">
\t\t\t<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">
\t\t\t\t<Content>{escaped_content}</Content>
\t\t\t</CharacterStyleRange>
\t\t</ParagraphStyleRange>
\t</Story>
</idPkg:Story>'''
    
    def _escape_xml_content(self, text: str) -> str:
        """Escape XML special characters."""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')


    """Create a TextFrame XML element for a story"""
    def _create_textframe_for_story(self, story_id: str, frame_id: str, x: float, y: float, width: float, height: float) -> str:
        
        # Use the exact structure from template
        anchor_width = width / 2
        anchor_height = height / 2
        
        return f'''<TextFrame Self="{frame_id}" ParentStory="{story_id}" PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" ParentInterfaceChangeCount="" TargetInterfaceChangeCount="" LastUpdatedInterfaceChangeCount="" OverriddenPageItemProps="" HorizontalLayoutConstraints="FlexibleDimension FixedDimension FlexibleDimension" VerticalLayoutConstraints="FlexibleDimension FixedDimension FlexibleDimension" GradientFillStart="0 0" GradientFillLength="0" GradientFillAngle="0" GradientStrokeStart="0 0" GradientStrokeLength="0" GradientStrokeAngle="0" ItemLayer="ucc" Locked="false" LocalDisplaySetting="Default" GradientFillHiliteLength="0" GradientFillHiliteAngle="0" GradientStrokeHiliteLength="0" GradientStrokeHiliteAngle="0" AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" Visible="true" Name="$ID/" ItemTransform="1 0 0 1 {x} {y}">
\t\t\t<Properties>
\t\t\t\t<PathGeometry>
\t\t\t\t\t<GeometryPathType PathOpen="false">
\t\t\t\t\t\t<PathPointArray>
\t\t\t\t\t\t\t<PathPointType Anchor="-{anchor_width} -{anchor_height}" LeftDirection="-{anchor_width} -{anchor_height}" RightDirection="-{anchor_width} -{anchor_height}" />
\t\t\t\t\t\t\t<PathPointType Anchor="-{anchor_width} {anchor_height}" LeftDirection="-{anchor_width} {anchor_height}" RightDirection="-{anchor_width} {anchor_height}" />
\t\t\t\t\t\t\t<PathPointType Anchor="{anchor_width} {anchor_height}" LeftDirection="{anchor_width} {anchor_height}" RightDirection="{anchor_width} {anchor_height}" />
\t\t\t\t\t\t\t<PathPointType Anchor="{anchor_width} -{anchor_height}" LeftDirection="{anchor_width} -{anchor_height}" RightDirection="{anchor_width} -{anchor_height}" />
\t\t\t\t\t\t</PathPointArray>
\t\t\t\t\t</GeometryPathType>
\t\t\t\t</PathGeometry>
\t\t\t</Properties>
\t\t\t<TextFramePreference TextColumnCount="1" TextColumnFixedWidth="{width}" TextColumnMaxWidth="0">
\t\t\t\t<Properties>
\t\t\t\t\t<InsetSpacing type="list">
\t\t\t\t\t\t<ListItem type="unit">0</ListItem>
\t\t\t\t\t\t<ListItem type="unit">0</ListItem>
\t\t\t\t\t\t<ListItem type="unit">0</ListItem>
\t\t\t\t\t\t<ListItem type="unit">0</ListItem>
\t\t\t\t\t</InsetSpacing>
\t\t\t\t</Properties>
\t\t\t</TextFramePreference>
\t\t\t<TextWrapPreference Inverse="false" ApplyToMasterPageOnly="false" TextWrapSide="BothSides" TextWrapMode="None">
\t\t\t\t<Properties>
\t\t\t\t\t<TextWrapOffset Top="0" Left="0" Bottom="0" Right="0" />
\t\t\t\t</Properties>
\t\t\t</TextWrapPreference>
\t\t\t<ObjectExportOption EpubType="$ID/" SizeType="DefaultSize" CustomSize="$ID/" PreserveAppearanceFromLayout="PreserveAppearanceDefault" AltTextSourceType="SourceXMLStructure" ActualTextSourceType="SourceXMLStructure" CustomAltText="$ID/" CustomActualText="$ID/" ApplyTagType="TagFromStructure" ImageConversionType="JPEG" ImageExportResolution="Ppi300" GIFOptionsPalette="AdaptivePalette" GIFOptionsInterlaced="true" JPEGOptionsQuality="High" JPEGOptionsFormat="BaselineEncoding" ImageAlignment="AlignLeft" ImageSpaceBefore="0" ImageSpaceAfter="0" UseImagePageBreak="false" ImagePageBreak="PageBreakBefore" CustomImageAlignment="false" SpaceUnit="CssPixel" CustomLayout="false" CustomLayoutType="AlignmentAndSpacing">
\t\t\t\t<Properties>
\t\t\t\t\t<AltMetadataProperty NamespacePrefix="$ID/" PropertyPath="$ID/" />
\t\t\t\t\t<ActualMetadataProperty NamespacePrefix="$ID/" PropertyPath="$ID/" />
\t\t\t\t</Properties>
\t\t\t</ObjectExportOption>
\t\t</TextFrame>'''
    
    """Main function to inject stories and create necessary spreads."""
    def _inject_stories_and_create_spreads(self, idml_path: str, stories: List[Dict[str, str]]) -> bool:
        
        try:
            # Extract IDML
            extract_dir = tempfile.mkdtemp()
            
            with zipfile.ZipFile(idml_path, 'r') as zip_file:
                zip_file.extractall(extract_dir)
            
            #print(f"✓ IDML extraído para: {extract_dir}")
            
            # Analyze requirements
            max_page = int(max(story['page_number'] for story in stories))
            required_spreads = self._get_required_spreads(max_page)
            
            # Check existing spreads directory
            spreads_dir = os.path.join(extract_dir, "Spreads")
            existing_spreads = [f for f in os.listdir(spreads_dir) if f.endswith('.xml')]
            
            #print(f"📊 Analysis: {max_page} pages need {required_spreads} spreads, found {len(existing_spreads)} existing")
            
            # Clear existing spreads and create new ones dynamically
            #print("🧹 Clearing existing spreads for dynamic generation...")
            for spread_file in existing_spreads:
                spread_path = os.path.join(spreads_dir, spread_file)
                os.remove(spread_path)
                #print(f"✓ Removed template spread: {spread_file}")
            
            # Create ALL spreads dynamically
            new_spreads = []
            for spread_idx in range(required_spreads):
                spread_id = self._generate_spread_id()
                self.spread_counter += 1
                spread_filename = f"Spread_{spread_id}.xml"
                spread_path = os.path.join(spreads_dir, spread_filename)
                
                # Determine pages for this spread
                first_page = (spread_idx * 2) + 1
                second_page = first_page + 1 if first_page + 1 <= max_page else None
                
                pages_in_spread = [first_page]
                if second_page:
                    pages_in_spread.append(second_page)
                
                # Create spread XML
                spread_xml = self._create_spread_xml(
                    spread_id,
                    spread_idx,
                    pages_in_spread
                )
                
                with open(spread_path, 'w', encoding='utf-8') as f:
                    f.write(spread_xml)
                
                new_spreads.append(spread_filename)
                #print(f"✅ Created spread: {spread_filename} (pages {pages_in_spread})")
            
            # Update designmap for all new spreads
            self._update_designmap_for_new_spreads(extract_dir, new_spreads)
            
            # Create and inject stories
            self._inject_stories_to_extracted_idml(extract_dir, stories)
            
            # Add TextFrames to spreads
            self._add_textframes_to_spreads(extract_dir, stories)
            
            # Repackage IDML
            with zipfile.ZipFile(idml_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, extract_dir)
                        zip_file.write(file_path, arc_name)
            
            # Cleanup
            shutil.rmtree(extract_dir)
            print("✅ IDML gerado")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na geração dinâmica: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _inject_stories_to_extracted_idml(self, extract_dir: str, stories: List[Dict[str, str]]) -> bool:
        """Inject story files into extracted IDML."""
        try:
            stories_dir = os.path.join(extract_dir, "Stories")
            os.makedirs(stories_dir, exist_ok=True)
            
            # Create story files
            for story_data in stories:
                story_filename = f"Story_{story_data['story_id']}.xml"
                story_path = os.path.join(stories_dir, story_filename)
                
                with open(story_path, 'w', encoding='utf-8') as f:
                    f.write(story_data['story_xml'])
                
                #print(f"✓ Story created: {story_filename}")
            
            # Update designmap for stories
            self._update_designmap_for_stories(extract_dir, stories)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao injetar stories: {e}")
            return False
    
    def _update_designmap_for_stories(self, extract_dir: str, stories: List[Dict[str, str]]) -> bool:
        """Update designmap.xml with story references."""
        try:
            designmap_path = os.path.join(extract_dir, "designmap.xml")
            
            with open(designmap_path, 'r', encoding='utf-8') as f:
                designmap_content = f.read()
            
            # Add story entries
            story_entries = []
            for story_data in stories:
                story_filename = f"Story_{story_data['story_id']}.xml"
                story_entry = f'\n\t<idPkg:Story src="Stories/{story_filename}" />'
                story_entries.append(story_entry)
            
            # Insert before closing tag
            if '</Document>' in designmap_content:
                insert_point = designmap_content.rfind('</Document>')
                new_content = (designmap_content[:insert_point] + 
                             ''.join(story_entries) + '\n' +
                             designmap_content[insert_point:])
                
                with open(designmap_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                #print(f"✅ Updated designmap.xml with {len(stories)} story references")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error updating designmap for stories: {e}")
            return False
    
    """Add TextFrames to the appropriate created spreads."""
    def _add_textframes_to_spreads(self, extract_dir: str, stories: List[Dict[str, str]]) -> bool:
        try:
            spreads_dir = os.path.join(extract_dir, "Spreads")
            
            # Organize stories by page
            pages_stories = {}
            for story_data in stories:
                page_num = story_data['page_number']
                if page_num not in pages_stories:
                    pages_stories[page_num] = []
                pages_stories[page_num].append(story_data)
            
            # Get all dynamically created spread files
            spread_files = sorted([f for f in os.listdir(spreads_dir) if f.endswith('.xml')])
            
            #print(f"📄 Distributing TextFrames across {len(spread_files)} dynamic spreads")
            
            # Add TextFrames to each page
            for page_num, page_stories in pages_stories.items():
                # Calculate which spread this page belongs to (1-indexed pages)
                spread_index = (page_num - 1) // 2  # Pages 1-2 → spread 0, Pages 3-4 → spread 1, etc.
                
                if spread_index < len(spread_files):
                    spread_file = spread_files[spread_index]
                    spread_path = os.path.join(spreads_dir, spread_file)
                    
                    # Get page position from template
                    x_pos, y_pos = self._calculate_page_position(page_num)
                    
                    # Read spread
                    with open(spread_path, 'r', encoding='utf-8') as f:
                        spread_content = f.read()
                    
                    # Create TextFrames - one per story with vertical spacing
                    textframes = []
                    for story_idx, story_data in enumerate(page_stories):
                        story_id = story_data['story_id']
                        frame_id = self._generate_textframe_id()
                        
                        # Calculate Y position based on story index and page
                        frame_y = self._calculate_textframe_y_position(page_num, story_idx)
                        
                        # Use frame dimensions from template
                        textframe_xml = self._create_textframe_for_story(
                            story_id, frame_id, x_pos, frame_y, self.frame_width, self.frame_height
                        )
                        textframes.append(textframe_xml)
                        
                       # print(f"✓ TextFrame {story_idx+1}: {story_id} at Y={frame_y:.1f}")
                    
                    # Insert TextFrames into spread
                    if '</Spread>' in spread_content:
                        insert_point = spread_content.rfind('</Spread>')
                        new_content = (spread_content[:insert_point] + 
                                      '\n\t\t' + '\n\t\t'.join(textframes) + '\n\t' +
                                      spread_content[insert_point:])
                        
                        with open(spread_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                    
                    print(f"  - Adicionou {len(textframes)} caixas de texto à página {page_num}")
                else:
                    print(f"⚠️  Não há spread disponível para a página {page_num}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao adicionar TextFrames: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _calculate_textframe_y_position(self, page_num: int, story_index: int) -> float:
        """Calculate Y position for TextFrame based on page number and story index."""
        # Base Y positions and spacing patterns from manually corrected version
        if page_num == 1:
            # Page 1 TextFrame Y positions (5 sections)
            base_positions = [
                -326.83464566890945,
                -204.1299212598425,
                -70.86614173113776,
                58.11023622009054,
                197.64566929095668,
                326.83464566890905  # Extra position for more sections
            ]
        elif page_num == 2:
            # Page 2 TextFrame Y positions (6 sections)
            base_positions = [
                -186.8346456689095,
                -46.834645668909474,
                93.16535433109041,
                233.16535433109052,
                373.16535433109052,  # Calculated continuation
                513.16535433109052   # Calculated continuation
            ]
        elif page_num == 3:
            # Page 3 TextFrame Y positions (6 sections)
            base_positions = [
                -94.39370078854725,
                21.826771651633607,
                138.0472440918147,
                254.26771653199575,
                370.48819097217675,  # Calculated continuation
                486.70866541235775   # Calculated continuation
            ]
        else:
            # For additional pages, use a generic pattern
            base_y = -300
            spacing = 140
            base_positions = [base_y + (i * spacing) for i in range(10)]
        
        # Return the position for this story index, or calculate if beyond predefined
        if story_index < len(base_positions):
            return base_positions[story_index]
        else:
            # If more stories than predefined positions, continue the pattern
            last_pos = base_positions[-1]
            additional_spacing = 140
            return last_pos + (additional_spacing * (story_index - len(base_positions) + 1))
    
    """
    Main function to generate enhanced IDML with exact number of pages from JSON.
    """
    def generate_file(self, json_data: Dict[str, Any], base_name: str = "enhanced") -> bool:
        
        try:            
            # Get output path
            output_path = self._get_next_output_filename(base_name)
            
            # Analyze input - Generate exactly the number of pages in JSON
            total_pages = len(json_data.get('pages', []))
            total_sections = sum(len(page.get('sections', [])) for page in json_data.get('pages', []))
            required_spreads = self._get_required_spreads(total_pages)
            
            '''print(f"📊 Analysis:")
            print(f"   📄 Páginas no JSON: {total_pages}")
            print(f"   📝 Total de seções: {total_sections}")
            print(f"   📖 Spreads necessários: {required_spreads}")
            print(f"   📁 Saída: {output_path}")'''
            
            # Validate JSON structure
            if total_pages == 0:
                print("❌ Não foi possível encontrar páginas no JSON")
                return False
            
            # Copy new template
            base_template = self._find_base_template()
            shutil.copy2(base_template, output_path)
            #print(f"✓ Template copiado (template.idml)")
            
            # Create stories - one per page (first section only for now)
            stories = self._create_stories_from_pages(json_data)
            print(f"✅ Criou {len(stories)} stories em {total_pages} páginas")
            
            # Enhanced generation with exact page count
            success = self._inject_stories_and_create_spreads(output_path, stories)
            
            if success:
                print(f" - Documento .IDML gerado: {output_path}")
                print(f" - Gerou {total_pages} páginas")
                return True
            else:
                print("❌ Não foi possível gerar o documento .IDML")
                return False
                
        except Exception as e:
            print(f"❌ Error in enhanced generation: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    print("🚀 Gerando documento .IDML")
    
    # Load test JSON
    json_paths = ["example.json", "src/example.json", "../src/example.json"]
    json_file = None
    
    for path in json_paths:
        if os.path.exists(path):
            json_file = path
            break
    
    if not json_file:
        print("❌ Não foi possível encontrar o arquivo JSON")
        return 1
    
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    print(f"✅ Arquivo JSON carregado: {json_file}")
    
    # Generate enhanced IDML
    generator = EnhancedIDMLGenerator()
    success = generator.generate_file(json_data, "document")
    
    if success:
        return 0
    else:
        print("❌ Não foi possível gerar o documento .IDML")
        return 1


if __name__ == "__main__":
    exit(main()) 