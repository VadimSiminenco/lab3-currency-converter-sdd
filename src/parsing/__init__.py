"""XML parsing package for BNM official exchange rates feed."""
from src.parsing.xml_parser import parse_bnm_xml, XmlParsingError

__all__ = ["parse_bnm_xml", "XmlParsingError"]
