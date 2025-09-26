#!/usr/bin/env python3
"""
SSML (Speech Synthesis Markup Language) is a subset of XML specifically
designed for controlling synthesis. You can see examples of how the SSML
should be parsed in the unit tests below.
"""

#
# DO NOT USE CHATGPT, COPILOT, OR ANY AI CODING ASSISTANTS.
# Conventional auto-complete and Intellisense are allowed.
#
# DO NOT USE ANY PRE-EXISTING XML PARSERS FOR THIS TASK - lxml, ElementTree, etc.
# You may use online references to understand the SSML specification, but DO NOT read
# online references for implementing an XML/SSML parser.
#


from typing import List, Union, Dict

SSMLNode = Union["SSMLText", "SSMLTag"]


class SSMLTag:
    def __init__(self, name: str, attributes: Dict[str, str] = None, children: List[SSMLNode] = None):
        self.name = name
        self.attributes = attributes or {}
        self.children = children or []
        
    def __eq__(self, other):
        if not isinstance(other, SSMLTag):
            return False
        return (self.name == other.name and 
                self.attributes == other.attributes and 
                self.children == other.children)


class SSMLText:
    def __init__(self, text: str):
        self.text = text
        
    def __eq__(self, other):
        if not isinstance(other, SSMLText):
            return False
        return self.text == other.text


def parse_attributes(attr_string: str) -> Dict[str, str]:
    import re
    attrs = {}
    i = 0
    n = len(attr_string)
    
    while i < n:
        # Skip whitespace
        while i < n and attr_string[i].isspace():
            i += 1
        if i >= n:
            break
            
        # Find attribute name
        name_start = i
        while i < n and (attr_string[i].isalnum() or attr_string[i] in '-_.:'):
            i += 1
        if i == name_start:
            # No valid attribute name found
            raise Exception(f"Invalid attribute at position {i}")
            
        name = attr_string[name_start:i]
        
        # Skip whitespace before =
        while i < n and attr_string[i].isspace():
            i += 1
            
        # Expect = after attribute name
        if i >= n or attr_string[i] != '=':
            raise Exception(f"Expected '=' after attribute name '{name}'")
        i += 1
        
        # Skip whitespace after =
        while i < n and attr_string[i].isspace():
            i += 1
            
        # Get attribute value
        if i >= n:
            raise Exception(f"Expected attribute value after '=' for attribute '{name}'")
            
        quote = attr_string[i]
        if quote not in ('"', "'"):
            # Unquoted attribute value (not allowed in strict XML, but we'll handle it)
            value_start = i
            while i < n and not attr_string[i].isspace() and attr_string[i] != '>':
                i += 1
            value = attr_string[value_start:i]
        else:
            # Quoted attribute value
            i += 1  # Skip opening quote
            value_start = i
            while i < n and attr_string[i] != quote:
                if attr_string[i] == '&':
                    # Handle XML entities (simplified)
                    i += 1
                    while i < n and attr_string[i] != ';':
                        i += 1
                    if i >= n:
                        break
                i += 1
                
            if i >= n or attr_string[i] != quote:
                raise Exception(f"Unclosed quote in attribute value for '{name}'")
                
            value = attr_string[value_start:i]
            i += 1  # Skip closing quote
        
        attrs[name] = value
    
    return attrs


def parseSSML(ssml: str) -> SSMLNode:
    def parse_node(s: str, pos: int, expected_closing_tag: str = None) -> tuple[list[SSMLNode], int]:
        nodes = []
        i = pos
        text_buffer = []
        
        while i < len(s):
            if s[i] == '<':
                # Handle text content before the tag
                if text_buffer:
                    text = ''.join(text_buffer)
                    if text.strip():
                        nodes.append(SSMLText(unescapeXMLChars(text)))
                    text_buffer = []
                
                # Handle closing tag
                if s.startswith('</', i):
                    end_tag = s.find('>', i)
                    if end_tag == -1:
                        raise Exception("Unclosed tag")
                    
                    # Extract tag name from closing tag (handle whitespace)
                    tag_content = s[i+2:end_tag].strip()
                    closing_tag = tag_content.strip().lower()
                    
                    # Validate closing tag matches expected
                    if expected_closing_tag and closing_tag != expected_closing_tag:
                        raise Exception(f"Mismatched tags: expected </{expected_closing_tag}>, got </{closing_tag}>")
                    
                    return nodes, end_tag + 1
                
                # Handle opening tag
                tag_end = s.find('>', i)
                if tag_end == -1:
                    raise Exception("Unclosed tag")
                
                # Parse tag content (handle whitespace)
                tag_content = s[i+1:tag_end].strip()
                is_self_closing = tag_content.endswith('/')
                if is_self_closing:
                    tag_content = tag_content[:-1].strip()
                
                # Split tag name and attributes (handle whitespace)
                parts = tag_content.strip().split(None, 1)
                if not parts:
                    raise Exception("Empty tag")
                    
                tag_name = parts[0].lower()
                attr_str = parts[1] if len(parts) > 1 else ""
                
                # Parse attributes
                attributes = {}
                if attr_str:
                    try:
                        attributes = parse_attributes(attr_str)
                    except Exception as e:
                        raise Exception(f"Invalid attributes in tag <{tag_name}>: {str(e)}")
                
                # Handle self-closing tag
                if is_self_closing:
                    nodes.append(SSMLTag(tag_name, attributes, []))
                    i = tag_end + 1
                    continue
                
                # Parse children recursively
                children, new_pos = parse_node(s, tag_end + 1, tag_name)
                nodes.append(SSMLTag(tag_name, attributes, children))
                i = new_pos
                
            else:
                text_buffer.append(s[i])
                i += 1
        
        # Add any remaining text
        if text_buffer:
            text = ''.join(text_buffer)
            if text.strip():
                nodes.append(SSMLText(unescapeXMLChars(text)))
        
        # If we were expecting a closing tag but didn't find it
        if expected_closing_tag:
            raise Exception(f"Missing closing tag </{expected_closing_tag}>")
            
        return nodes, i
    
    # Remove any leading/trailing whitespace
    ssml = ssml.strip()
    
    # Check for root <speak> tag (case insensitive and with whitespace)
    ssml_lower = ssml.lower()
    if not (ssml_lower.lstrip().startswith('<speak') and '</speak>' in ssml_lower):
        raise Exception("SSML must be wrapped in a <speak> tag")
    
    try:
        # Find the actual end of the opening speak tag
        speak_start = ssml_lower.find('<speak')
        speak_end = ssml.find('>', speak_start)
        if speak_end == -1:
            raise Exception("Invalid SSML: unclosed <speak> tag")
        
        # Parse the content between <speak> and </speak>
        content_start = speak_end + 1
        content_end = ssml_lower.rfind('</speak>')
        if content_end == -1:
            raise Exception("Invalid SSML: missing closing </speak> tag")
        
        # Extract the content and parse it
        content = ssml[content_start:content_end].strip()
        nodes, _ = parse_node(content, 0)
        
        # Create the root speak tag with the parsed content
        speak_attrs = {}
        if ' ' in ssml[speak_start:speak_end]:
            # Extract attributes from the speak tag
            attr_str = ssml[speak_start + 6:speak_end].strip()
            speak_attrs = parse_attributes(attr_str) if attr_str else {}
        
        return SSMLTag('speak', speak_attrs, nodes)
        
    except Exception as e:
        raise Exception(f"Error parsing SSML: {str(e)}")

def ssmlNodeToText(node: SSMLNode) -> str:
    if isinstance(node, SSMLText):
        return escapeXMLChars(node.text)
    elif isinstance(node, SSMLTag):
        # Build attributes string
        attrs = ""
        if node.attributes:
            attrs = " " + " ".join(f'{k}="{escapeXMLChars(str(v))}"' for k, v in node.attributes.items())
        
        # Handle self-closing tags (no children and no text content)
        if not node.children:
            return f"<{node.name}{attrs} />"
        
        # Handle elements with children
        children = "".join(ssmlNodeToText(child) for child in node.children)
        
        # If children is empty after processing, make it self-closing
        if not children.strip():
            return f"<{node.name}{attrs} />"
            
        return f"<{node.name}{attrs}>{children}</{node.name}>"
    return ""


def unescapeXMLChars(text: str) -> str:
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def escapeXMLChars(text: str) -> str:
    return text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

# Example usage:
# ssml_string = '<speak>Hello, <break time="500ms"/>world!</speak>'
# parsed_ssml = parseSSML(ssml_string)
# text = ssmlNodeToText(parsed_ssml)
# print(text)