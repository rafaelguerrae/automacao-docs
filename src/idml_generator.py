import json
import os
from typing import Dict, List, Any, Tuple
import tempfile
import shutil
import zipfile
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

        # Text frame configuration (based on fixed version analysis)
        self.frame_width = 523.275590551
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
        if os.path.exists("../build"):
            build_dir = "../build"
        elif os.path.exists("build"):
            build_dir = "build"
        else:
            if os.path.exists("src"):
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
            "template.idml",
        ]

        for template_path in template_paths:
            if os.path.exists(template_path):
                return os.path.abspath(template_path)

        raise FileNotFoundError("Arquivo IDML de template não encontrado.")

    """
        Calculate X,Y coordinates for any page number based on template.
        Uses exact coordinates from the template structure.
    """

    def _calculate_page_position(self, page_number: int) -> Tuple[float, float]:
        """Calculate page position for ItemTransform based on fixed structure analysis."""
        
        # Base Y position for all pages
        base_y = -420.944881889
        
        if page_number == 1:
            # Page 1: single page spread
            return 0, base_y
        elif page_number == 2:
            # Page 2: left side of spread
            return -595.275590551, base_y
        elif page_number == 3:
            # Page 3: right side of spread
            return 0, base_y
        else:
            # For additional pages, calculate spread and position
            spread_number = math.ceil((page_number - 1) / 2)  # Which spread (0-based)
            
            if page_number % 2 == 0:  # Even pages (left side)
                x_pos = -595.275590551
            else:  # Odd pages (right side)
                x_pos = 0
            
            # Add vertical offset for additional spreads
            y_offset = spread_number * 1021.8897637780001  # From ItemTransform analysis
            
            return x_pos, base_y + y_offset

    def _get_required_spreads(self, total_pages: int) -> int:
        """Calculate how many spreads are needed based on fixed structure analysis."""
        if total_pages <= 1:
            return 1
        else:
            # First spread has 1 page, remaining spreads have 2 pages each
            return 1 + math.ceil((total_pages - 1) / 2)

    def _create_spread_xml(
        self, spread_id: str, spread_index: int, pages_in_spread: List[int]
    ) -> str:
        """
        Create proper XML for a new spread based on fixed structure analysis.
        """
        # Calculate spread ItemTransform based on spread index
        if spread_index == 0:
            # First spread (page 1 only)
            item_transform = "1 0 0 1 0 0"
            binding_location = 0
        else:
            # Additional spreads
            y_offset = spread_index * 1021.8897637780001
            item_transform = f"1 0 0 1 0 {y_offset}"
            binding_location = 1

        spread_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="20.4">
\t<Spread Self="{spread_id}" FlattenerOverride="Default" SpreadHidden="false" AllowPageShuffle="true" ItemTransform="{item_transform}" ShowMasterItems="true" PageCount="{len(pages_in_spread)}" BindingLocation="{binding_location}" PageTransitionType="None" PageTransitionDirection="NotApplicable" PageTransitionDuration="Medium">
\t\t<FlattenerPreference LineArtAndTextResolution="300" GradientAndMeshResolution="150" ClipComplexRegions="false" ConvertAllStrokesToOutlines="false" ConvertAllTextToOutlines="false">
\t\t\t<Properties>
\t\t\t\t<RasterVectorBalance type="double">50</RasterVectorBalance>
\t\t\t</Properties>
\t\t</FlattenerPreference>"""

        # Add each page to the spread
        for page_num in pages_in_spread:
            x_pos, y_pos = self._calculate_page_position(page_num)
            page_id = self._generate_page_id()
            self.page_counter += 1

            # Use calculated positions for ItemTransform
            page_transform = f"1 0 0 1 {x_pos} {y_pos}"

            # Determine layout rule and applied master
            if page_num == 1:
                layout_rule = "Off"  # Based on fixed structure
                applied_master = "ubb"  # Based on fixed structure
            else:
                layout_rule = "UseMaster" if page_num == 2 else "Off"
                applied_master = "ubb"

            page_xml = f"""
\t\t<Page Self="{page_id}" AppliedAlternateLayout="ub4" LayoutRule="{layout_rule}" SnapshotBlendingMode="IgnoreLayoutSnapshots" OptionalPage="false" GeometricBounds="0 0 {self.page_height} {self.page_width}" ItemTransform="{page_transform}" Name="{page_num}" AppliedTrapPreset="TrapPreset/$ID/kDefaultTrapStyleName" OverrideList="" AppliedMaster="{applied_master}" MasterPageTransform="1 0 0 1 0 0" TabOrder="" GridStartingPoint="TopOutside" UseMasterGrid="true">
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
\t\t</Page>"""
            spread_xml += page_xml

        spread_xml += """
\t</Spread>
</idPkg:Spread>"""

        return spread_xml

    """Update designmap.xml to replace all spread references with new ones."""

    def _update_designmap_for_new_spreads(
        self, extract_dir: str, new_spreads: List[str]
    ) -> bool:

        try:
            designmap_path = os.path.join(extract_dir, "designmap.xml")

            if not os.path.exists(designmap_path):
                print("⚠️  designmap.xml não encontrado")
                return False

            # Read current designmap
            with open(designmap_path, "r", encoding="utf-8") as f:
                designmap_content = f.read()

            # Remove all existing spread references
            spread_pattern = r'\s*<idPkg:Spread[^>]*src="Spreads/[^"]*"[^>]*/?>\s*'
            designmap_content = re.sub(spread_pattern, "", designmap_content)

            # Add new spread entries
            new_spread_entries = []
            for spread_file in new_spreads:
                spread_entry = f'\n\t<idPkg:Spread src="Spreads/{spread_file}" />'
                new_spread_entries.append(spread_entry)

            # Insert new entries before the closing tag
            if "</Document>" in designmap_content:
                insert_point = designmap_content.rfind("</Document>")
                new_content = (
                    designmap_content[:insert_point]
                    + "".join(new_spread_entries)
                    + "\n"
                    + designmap_content[insert_point:]
                )

                with open(designmap_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

                # print(f"✅ Updated designmap.xml with {len(new_spreads)} dynamic spread references")
                return True

            return False

        except Exception as e:
            print(f"❌ Error updating designmap: {e}")
            return False

    """Create stories from JSON pages - one story per SECTION, not per page."""

    def _create_stories_from_pages(
        self, json_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        stories = []

        if "pages" in json_data:
            for page_num, page in enumerate(json_data["pages"], 1):
                if "sections" in page:
                    # Create one story for EACH section
                    for section_idx, section in enumerate(page["sections"]):
                        story_id = self._generate_story_id()
                        # print(f"🔍 Creating story {len(stories)+1}: {story_id} (counter={self.story_counter})")
                        self.story_counter += 1

                        title = section.get("title", "").strip()
                        text = section.get("text", "").strip()
                        
                        # Skip sections that have neither title nor text
                        if not title and not text:
                            continue
                            
                        # Create combined content text for display purposes
                        content_parts = []
                        if title:
                            content_parts.append(title)
                        if text:
                            content_parts.append(text)
                        content_text = "  ".join(content_parts)

                        story_xml = self._create_story_with_content(
                            story_id, title, text
                        )

                        stories.append(
                            {
                                "story_id": story_id,
                                "content_text": content_text,
                                "story_xml": story_xml,
                                "page_number": page_num,
                                "section_index": section_idx,
                                "title": title,
                                "text": text,
                            }
                        )

        # print(f"📊 Total stories created: {len(stories)}")
        return stories

    def _create_story_with_content(self, story_id: str, title: str, text: str) -> str:
        """Create Story XML with separated title and text content with proper formatting."""
        escaped_title = self._escape_xml_content(title) if title else ""
        escaped_text = self._escape_xml_content(text) if text else ""

        # Create story with title (bold, larger) and text (normal) in separate paragraph styles
        story_content = []
        
        # Add title with bold formatting if it exists
        if escaped_title:
            story_content.append(f"""
\t\t<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/$ID/NormalParagraphStyle">
\t\t\t<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" FontStyle="Bold" PointSize="14">
\t\t\t\t<Content>{escaped_title}</Content>
\t\t\t</CharacterStyleRange>
\t\t</ParagraphStyleRange>""")
        
        # Add text with normal formatting if it exists
        if escaped_text:
            story_content.append(f"""
\t\t<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/$ID/NormalParagraphStyle">
\t\t\t<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" PointSize="12">
\t\t\t\t<Content>{escaped_text}</Content>
\t\t\t</CharacterStyleRange>
\t\t</ParagraphStyleRange>""")

        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="20.4">
\t<Story Self="{story_id}" AppliedTOCStyle="n" UserText="true" IsEndnoteStory="false" TrackChanges="false" StoryTitle="$ID/" AppliedNamedGrid="n">
\t\t<StoryPreference OpticalMarginAlignment="false" OpticalMarginSize="12" FrameType="TextFrameType" StoryOrientation="Horizontal" StoryDirection="LeftToRightDirection" />
\t\t<InCopyExportOption IncludeGraphicProxies="true" IncludeAllResources="false" />{''.join(story_content)}
\t</Story>
</idPkg:Story>"""

    def _escape_xml_content(self, text: str) -> str:
        """Escape XML special characters."""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&apos;")
        return "".join(char for char in text if ord(char) >= 32 or char in "\n\r\t")

    """Create a TextFrame XML element for a story"""

    def _create_textframe_for_story(
        self,
        story_id: str,
        frame_id: str,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> str:

        # Use the exact structure from fixed version analysis
        anchor_height = height / 2
        
        # Fixed version uses specific anchor values for wider frames
        if width == 523.275590551:  # Fixed version width
            left_anchor = -254.12598425187792
            right_anchor = 269.1496062991221
        else:
            # Fallback to original calculation
            left_anchor = -width / 2
            right_anchor = width / 2

        return f"""<TextFrame Self="{frame_id}" ParentStory="{story_id}" PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" ParentInterfaceChangeCount="" TargetInterfaceChangeCount="" LastUpdatedInterfaceChangeCount="" OverriddenPageItemProps="" HorizontalLayoutConstraints="FlexibleDimension FixedDimension FlexibleDimension" VerticalLayoutConstraints="FlexibleDimension FixedDimension FlexibleDimension" GradientFillStart="0 0" GradientFillLength="0" GradientFillAngle="0" GradientStrokeStart="0 0" GradientStrokeLength="0" GradientStrokeAngle="0" ItemLayer="uba" Locked="false" LocalDisplaySetting="Default" GradientFillHiliteLength="0" GradientFillHiliteAngle="0" GradientStrokeHiliteLength="0" GradientStrokeHiliteAngle="0" AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" Visible="true" Name="$ID/" ItemTransform="1 0 0 1 {x} {y}">
\t\t\t<Properties>
\t\t\t\t<PathGeometry>
\t\t\t\t\t<GeometryPathType PathOpen="false">
\t\t\t\t\t\t<PathPointArray>
\t\t\t\t\t\t\t<PathPointType Anchor="{left_anchor} -{anchor_height}" LeftDirection="{left_anchor} -{anchor_height}" RightDirection="{left_anchor} -{anchor_height}" />
\t\t\t\t\t\t\t<PathPointType Anchor="{left_anchor} {anchor_height}" LeftDirection="{left_anchor} {anchor_height}" RightDirection="{left_anchor} {anchor_height}" />
\t\t\t\t\t\t\t<PathPointType Anchor="{right_anchor} {anchor_height}" LeftDirection="{right_anchor} {anchor_height}" RightDirection="{right_anchor} {anchor_height}" />
\t\t\t\t\t\t\t<PathPointType Anchor="{right_anchor} -{anchor_height}" LeftDirection="{right_anchor} -{anchor_height}" RightDirection="{right_anchor} -{anchor_height}" />
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
\t\t</TextFrame>"""

    """Main function to inject stories and create necessary spreads."""

    def _inject_stories_and_create_spreads(
        self, idml_path: str, stories: List[Dict[str, str]]
    ) -> bool:

        try:
            # Extract IDML
            extract_dir = tempfile.mkdtemp()

            with zipfile.ZipFile(idml_path, "r") as zip_file:
                zip_file.extractall(extract_dir)

            # print(f"✓ IDML extraído para: {extract_dir}")

            # Analyze requirements
            max_page = int(max(story["page_number"] for story in stories))
            required_spreads = self._get_required_spreads(max_page)

            # Check existing spreads directory
            spreads_dir = os.path.join(extract_dir, "Spreads")
            existing_spreads = [
                f for f in os.listdir(spreads_dir) if f.endswith(".xml")
            ]

            # print(f"📊 Analysis: {max_page} pages need {required_spreads} spreads, found {len(existing_spreads)} existing")

            # Clear existing spreads and create new ones dynamically
            # print("🧹 Clearing existing spreads for dynamic generation...")
            for spread_file in existing_spreads:
                spread_path = os.path.join(spreads_dir, spread_file)
                os.remove(spread_path)
                # print(f"✓ Removed template spread: {spread_file}")

            # Create ALL spreads dynamically based on fixed structure analysis
            new_spreads = []
            for spread_idx in range(required_spreads):
                spread_id = self._generate_spread_id()
                self.spread_counter += 1
                spread_filename = f"Spread_{spread_id}.xml"
                spread_path = os.path.join(spreads_dir, spread_filename)

                # Determine pages for this spread based on fixed structure
                if spread_idx == 0:
                    # First spread: page 1 only
                    pages_in_spread = [1]
                else:
                    # Additional spreads: calculate pages
                    first_page = (spread_idx * 2)
                    second_page = first_page + 1 if first_page + 1 <= max_page else None
                    
                    pages_in_spread = [first_page]
                    if second_page:
                        pages_in_spread.append(second_page)

                # Create spread XML
                spread_xml = self._create_spread_xml(
                    spread_id, spread_idx, pages_in_spread
                )

                with open(spread_path, "w", encoding="utf-8") as f:
                    f.write(spread_xml)

                new_spreads.append(spread_filename)
                # print(f"✅ Created spread: {spread_filename} (pages {pages_in_spread})")

            # Update designmap for all new spreads
            self._update_designmap_for_new_spreads(extract_dir, new_spreads)

            # Create and inject stories
            self._inject_stories_to_extracted_idml(extract_dir, stories)

            # Add TextFrames to spreads
            self._add_textframes_to_spreads(extract_dir, stories)

            # Repackage IDML
            with zipfile.ZipFile(idml_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
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

    def _inject_stories_to_extracted_idml(
        self, extract_dir: str, stories: List[Dict[str, str]]
    ) -> bool:
        """Inject story files into extracted IDML."""
        try:
            stories_dir = os.path.join(extract_dir, "Stories")
            os.makedirs(stories_dir, exist_ok=True)

            # Create story files
            for story_data in stories:
                story_filename = f"Story_{story_data['story_id']}.xml"
                story_path = os.path.join(stories_dir, story_filename)

                with open(story_path, "w", encoding="utf-8") as f:
                    f.write(story_data["story_xml"])

                # print(f"✓ Story created: {story_filename}")

            # Update designmap for stories
            self._update_designmap_for_stories(extract_dir, stories)

            return True

        except Exception as e:
            print(f"❌ Erro ao injetar stories: {e}")
            return False

    def _update_designmap_for_stories(
        self, extract_dir: str, stories: List[Dict[str, str]]
    ) -> bool:
        """Update designmap.xml with story references."""
        try:
            designmap_path = os.path.join(extract_dir, "designmap.xml")

            with open(designmap_path, "r", encoding="utf-8") as f:
                designmap_content = f.read()

            # Add story entries
            story_entries = []
            for story_data in stories:
                story_filename = f"Story_{story_data['story_id']}.xml"
                story_entry = f'\n\t<idPkg:Story src="Stories/{story_filename}" />'
                story_entries.append(story_entry)

            # Insert before closing tag
            if "</Document>" in designmap_content:
                insert_point = designmap_content.rfind("</Document>")
                new_content = (
                    designmap_content[:insert_point]
                    + "".join(story_entries)
                    + "\n"
                    + designmap_content[insert_point:]
                )

                with open(designmap_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

                # print(f"✅ Updated designmap.xml with {len(stories)} story references")
                return True

            return False

        except Exception as e:
            print(f"❌ Error updating designmap for stories: {e}")
            return False

    """Add TextFrames to the appropriate created spreads."""

    def _add_textframes_to_spreads(
        self, extract_dir: str, stories: List[Dict[str, str]]
    ) -> bool:
        try:
            spreads_dir = os.path.join(extract_dir, "Spreads")

            # Organize stories by page
            pages_stories = {}
            for story_data in stories:
                page_num = story_data["page_number"]
                if page_num not in pages_stories:
                    pages_stories[page_num] = []
                pages_stories[page_num].append(story_data)

            # Calculate required spreads for this content
            max_page = int(max(story["page_number"] for story in stories))
            required_spreads = self._get_required_spreads(max_page)
            
            # Get all dynamically created spread files in creation order
            spread_files = []
            for spread_idx in range(required_spreads):
                # Recreate the spread filename based on the same logic used in creation
                if spread_idx == 0:
                    spread_id = "ucf"  # First spread ID
                elif spread_idx == 1:
                    spread_id = "u109"  # Second spread ID  
                else:
                    spread_id = f"u{100 + spread_idx + 1:03d}"  # Additional spreads
                
                spread_filename = f"Spread_{spread_id}.xml"
                spread_files.append(spread_filename)

            # print(f"📄 Distributing TextFrames across {len(spread_files)} dynamic spreads")

            # Add TextFrames to each page
            for page_num, page_stories in pages_stories.items():
                # Calculate which spread this page belongs to based on actual spread structure
                # Spread 0: Page 1 only, Spread 1: Page 2-3, Spread 2: Pages 4-5, etc.
                if page_num == 1:
                    spread_index = 0
                elif page_num == 2:
                    spread_index = 1
                else:
                    # For pages 3+, they go to spread 1 (pages 2-3 together)
                    spread_index = 1

                if spread_index < len(spread_files):
                    spread_file = spread_files[spread_index]
                    spread_path = os.path.join(spreads_dir, spread_file)

                    # Calculate TextFrame X position based on fixed structure analysis
                    if page_num == 1:
                        frame_x = 290.1259842518779  # Page 1: center/right position
                    elif page_num == 2:
                        frame_x = -297.6377952754999  # Page 2: left side of spread
                    elif page_num == 3:
                        frame_x = 290.1259842518779   # Page 3: right side of spread (same as page 1)
                    else:
                        # For additional pages, alternate based on page position
                        if page_num % 2 == 0:  # Even pages (left side)
                            frame_x = -297.6377952754999
                        else:  # Odd pages (right side)
                            frame_x = 290.1259842518779

                    # Read spread
                    with open(spread_path, "r", encoding="utf-8") as f:
                        spread_content = f.read()

                    # Create TextFrames - one per story with vertical spacing
                    textframes = []
                    for story_idx, story_data in enumerate(page_stories):
                        story_id = story_data["story_id"]
                        frame_id = self._generate_textframe_id()

                        # Calculate Y position based on story index and page
                        frame_y = self._calculate_textframe_y_position(
                            page_num, story_idx
                        )

                        # Use frame dimensions from template
                        textframe_xml = self._create_textframe_for_story(
                            story_id,
                            frame_id,
                            frame_x,
                            frame_y,
                            self.frame_width,
                            self.frame_height,
                        )
                        textframes.append(textframe_xml)

                    # Insert TextFrames into spread
                    if "</Spread>" in spread_content:
                        insert_point = spread_content.rfind("</Spread>")
                        new_content = (
                            spread_content[:insert_point]
                            + "\n\t\t"
                            + "\n\t\t".join(textframes)
                            + "\n\t"
                            + spread_content[insert_point:]
                        )

                        with open(spread_path, "w", encoding="utf-8") as f:
                            f.write(new_content)

                    print(
                        f"  - Adicionou {len(textframes)} caixas de texto à página {page_num}"
                    )
                else:
                    print(f"⚠️  Não há spread disponível para a página {page_num}")

            return True

        except Exception as e:
            print(f"❌ Erro ao adicionar TextFrames: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _calculate_textframe_y_position(self, page_num: int, story_index: int) -> float:
        """Calculate Y position for TextFrame based on fixed structure analysis."""
        # Use CONSISTENT Y positions for ALL pages - this was the main issue!
        # The Y positions should be the same regardless of page number
        base_positions = [
            -326.83464566890945,
            -210.61417322872836,
            -94.39370078854728,
            21.826771651633806,
            138.0472440918149,
            254.26771653199575,  # Extra positions for more sections
        ]

        # Return the position for this story index, or calculate if beyond predefined
        if story_index < len(base_positions):
            return base_positions[story_index]
        else:
            # If more stories than predefined positions, continue the pattern
            last_pos = base_positions[-1]
            additional_spacing = 140
            return last_pos + (
                additional_spacing * (story_index - len(base_positions) + 1)
            )

    """
    Main function to generate enhanced IDML with exact number of pages from JSON.
    """

    def generate_file(
        self, json_data: Dict[str, Any], base_name: str = "enhanced"
    ) -> bool:

        try:
            # Get output path
            output_path = self._get_next_output_filename(base_name)

            # Analyze input - Generate exactly the number of pages in JSON
            total_pages = len(json_data.get("pages", []))

            # Validate JSON structure
            if total_pages == 0:
                print("❌ Não foi possível encontrar páginas no JSON")
                return False

            # Copy new template
            base_template = self._find_base_template()
            shutil.copy2(base_template, output_path)
            # print(f"✓ Template copiado (template.idml)")

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
    import sys
    
    print("🚀 Gerando documento .IDML")

    # Parse command line arguments
    test_type = "one"  # default
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["-one", "-two", "-three", "-four"]:
            test_type = arg[1:]  # remove the dash
        else:
            print(f"❌ Argumento inválido: {arg}")
            print("Use: python idml_generator.py [-one|-two|-three|-four]")
            return 1

    # Map test types to JSON files
    json_files = {
        "one": "onePage.json",
        "two": "twoPages.json", 
        "three": "threePages.json",
        "four": "fourPages.json"
    }
    
    # Load test JSON from examples directory
    json_filename = json_files[test_type]
    json_paths = [
        f"examples/{json_filename}",
        f"../examples/{json_filename}",
        f"src/examples/{json_filename}"
    ]
    
    json_file = None
    for path in json_paths:
        if os.path.exists(path):
            json_file = path
            break

    if not json_file:
        print(f"❌ Não foi possível encontrar o arquivo JSON: {json_filename}")
        print(f"Procurado em: {json_paths}")
        return 1

    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    print(f"✅ Arquivo JSON carregado: {json_file}")
    print(f"📄 Tipo de teste: {test_type} ({len(json_data.get('pages', []))} páginas)")

    # Generate enhanced IDML
    generator = EnhancedIDMLGenerator()
    success = generator.generate_file(json_data, f"document-{test_type}")

    if success:
        return 0
    else:
        print("❌ Não foi possível gerar o documento .IDML")
        return 1


if __name__ == "__main__":
    exit(main())